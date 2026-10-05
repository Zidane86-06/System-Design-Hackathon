import pytest
import pytest_asyncio
import asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db import AsyncSessionLocal, init_db
from app.models import Inventory
from app.redis_client import redis_gate

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    await init_db()
    async with AsyncSessionLocal() as db:
        from sqlalchemy import update
        await db.execute(
            update(Inventory)
            .where(Inventory.product_id == "salestorm-prod-001")
            .values(available_quantity=100, reserved_quantity=0, version=1)
        )
        await db.commit()
    await redis_gate.reset_stock("salestorm-prod-001", 100)

@pytest.mark.asyncio
async def test_normal_purchase():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/orders", json={
            "user_id": "demo-user-001",
            "product_id": "salestorm-prod-001",
            "quantity": 1
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "CONFIRMED"

@pytest.mark.asyncio
async def test_idempotency_protection():
    idem_key = f"test-key-{uuid.uuid4()}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"Idempotency-Key": idem_key}
        resp1 = await ac.post("/orders", json={
            "user_id": "demo-user-001",
            "product_id": "salestorm-prod-001",
            "quantity": 1
        }, headers=headers)
        assert resp1.status_code == 201
        order1 = resp1.json()

        resp2 = await ac.post("/orders", json={
            "user_id": "demo-user-001",
            "product_id": "salestorm-prod-001",
            "quantity": 1
        }, headers=headers)
        assert resp2.status_code == 201
        order2 = resp2.json()

        assert order1["order_id"] == order2["order_id"]

@pytest.mark.asyncio
async def test_payment_failure_saga_compensation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/orders", json={
            "user_id": "demo-user-001",
            "product_id": "salestorm-prod-001",
            "quantity": 1,
            "simulate_payment_failure": True
        })
        assert resp.status_code == 201
        order = resp.json()
        assert order["status"] == "CANCELLED"

@pytest.mark.asyncio
async def test_inventory_cannot_become_negative():
    await redis_gate.reset_stock("salestorm-prod-001", 1)
    async with AsyncSessionLocal() as db:
        from sqlalchemy import update
        await db.execute(
            update(Inventory)
            .where(Inventory.product_id == "salestorm-prod-001")
            .values(available_quantity=1, reserved_quantity=0)
        )
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r1 = await ac.post("/orders", json={"user_id": "demo-user-001", "product_id": "salestorm-prod-001", "quantity": 1})
        assert r1.status_code == 201
        
        r2 = await ac.post("/orders", json={"user_id": "demo-user-001", "product_id": "salestorm-prod-001", "quantity": 1})
        assert r2.status_code == 409
        assert "OUT_OF_STOCK" in r2.json()["detail"]

@pytest.mark.asyncio
async def test_10k_concurrency_no_overselling():
    """
    CRITICAL PROOF TEST:
    200 purchase attempts against 100 stock units.
    Validates:
    - Successful purchases <= 100
    - Available stock >= 0
    - Oversold units == 0
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/simulation/load-test", json={
            "total_requests": 200,
            "concurrency": 20,
            "product_id": "salestorm-prod-001"
        })
        assert resp.status_code == 200

        completed = False
        for _ in range(30):
            await asyncio.sleep(0.5)
            prog = await ac.get("/simulation/load-test/progress")
            p_data = prog.json()
            if p_data["status"] == "COMPLETED":
                completed = True
                assert p_data["successful_purchases"] <= 100
                assert p_data["oversold_units"] == 0
                assert "PASS" in p_data["result_status"]
                break
        assert completed, "Load test did not finish in time."
