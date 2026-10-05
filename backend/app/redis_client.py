import asyncio
import time
from typing import Optional, Dict, Tuple
from app.config import settings

# Redis Lua Script for Atomic Inventory Reservation
LUA_RESERVE_SCRIPT = """
local stock_key = KEYS[1]
local reservation_key = KEYS[2]
local qty = tonumber(ARGV[1])
local ttl = tonumber(ARGV[2])

local current_stock = tonumber(redis.call('get', stock_key) or "0")

if current_stock >= qty then
    redis.call('decrby', stock_key, qty)
    redis.call('setex', reservation_key, ttl, qty)
    return 1
else
    return 0
end
"""

LUA_RELEASE_SCRIPT = """
local stock_key = KEYS[1]
local reservation_key = KEYS[2]

local reserved_qty = redis.call('get', reservation_key)
if reserved_qty then
    redis.call('incrby', stock_key, tonumber(reserved_qty))
    redis.call('del', reservation_key)
    return 1
else
    return 0
end
"""

class FastInMemoryRedisGate:
    """High-concurrency thread-safe in-memory Redis gate simulation fallback."""
    def __init__(self):
        self._stocks: Dict[str, int] = {"salestorm-prod-001": 100}
        self._reservations: Dict[str, Tuple[int, float]] = {} # res_id -> (qty, expire_at)
        self._lock = asyncio.Lock()

    async def initialize_stock(self, product_id: str, stock: int):
        async with self._lock:
            self._stocks[product_id] = stock
            self._reservations.clear()

    async def reserve(self, product_id: str, reservation_id: str, qty: int, ttl: int) -> bool:
        async with self._lock:
            current = self._stocks.get(product_id, 0)
            if current >= qty:
                self._stocks[product_id] = current - qty
                self._reservations[reservation_id] = (qty, time.time() + ttl)
                return True
            return False

    async def release(self, product_id: str, reservation_id: str) -> bool:
        async with self._lock:
            if reservation_id in self._reservations:
                qty, _ = self._reservations.pop(reservation_id)
                self._stocks[product_id] = self._stocks.get(product_id, 0) + qty
                return True
            return False

    async def get_available_stock(self, product_id: str) -> int:
        async with self._lock:
            return self._stocks.get(product_id, 0)

class RedisGateClient:
    def __init__(self):
        self.redis = None
        self.memory_gate = FastInMemoryRedisGate()
        self._reserve_sha = None
        self._release_sha = None

    async def connect(self):
        if settings.USE_REDIS:
            try:
                import redis.asyncio as aioredis
                self.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                await self.redis.ping()
                self._reserve_sha = await self.redis.script_load(LUA_RESERVE_SCRIPT)
                self._release_sha = await self.redis.script_load(LUA_RELEASE_SCRIPT)
                await self.redis.setnx("product:salestorm-prod-001:stock", 100)
                print("Connected to Redis successfully.")
            except Exception as e:
                print(f"Redis connection failed ({e}). Falling back to fast thread-safe in-memory Gate.")
                self.redis = None

    async def reserve(self, product_id: str, reservation_id: str, qty: int = 1, ttl: int = 30) -> bool:
        if self.redis:
            try:
                stock_key = f"product:{product_id}:stock"
                res_key = f"reservation:{reservation_id}"
                res = await self.redis.evalsha(self._reserve_sha, 2, stock_key, res_key, qty, ttl)
                return bool(res == 1)
            except Exception:
                return await self.memory_gate.reserve(product_id, reservation_id, qty, ttl)
        return await self.memory_gate.reserve(product_id, reservation_id, qty, ttl)

    async def release(self, product_id: str, reservation_id: str) -> bool:
        if self.redis:
            try:
                stock_key = f"product:{product_id}:stock"
                res_key = f"reservation:{reservation_id}"
                res = await self.redis.evalsha(self._release_sha, 2, stock_key, res_key)
                return bool(res == 1)
            except Exception:
                return await self.memory_gate.release(product_id, reservation_id)
        return await self.memory_gate.release(product_id, reservation_id)

    async def get_available(self, product_id: str) -> int:
        if self.redis:
            try:
                val = await self.redis.get(f"product:{product_id}:stock")
                return int(val) if val is not None else 0
            except Exception:
                return await self.memory_gate.get_available_stock(product_id)
        return await self.memory_gate.get_available_stock(product_id)

    async def reset_stock(self, product_id: str, stock: int = 100):
        await self.memory_gate.initialize_stock(product_id, stock)
        if self.redis:
            try:
                await self.redis.set(f"product:{product_id}:stock", stock)
            except Exception:
                pass

redis_gate = RedisGateClient()
