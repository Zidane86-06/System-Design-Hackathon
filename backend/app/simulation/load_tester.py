import asyncio
import time
import uuid
from typing import Dict, Any
from app.db import AsyncSessionLocal
from app.services.order_service import order_service
from app.services.payment_service import payment_service
from app.redis_client import redis_gate
from app.models import Inventory

class LoadTestRunner:
    def __init__(self):
        self.is_running = False
        self.progress = {
            "total_requests": 10000,
            "completed_requests": 0,
            "successful_purchases": 0,
            "rejected_out_of_stock": 0,
            "oversold_units": 0,
            "duplicate_orders": 0,
            "duration_ms": 0,
            "rps": 0,
            "avg_latency_ms": 0,
            "status": "IDLE",
            "result_status": "NONE"
        }

    async def run_test(
        self,
        total_requests: int = 10000,
        concurrency: int = 200,
        product_id: str = "salestorm-prod-001"
    ) -> Dict[str, Any]:
        if self.is_running:
            return self.progress

        self.is_running = True
        self.progress.update({
            "total_requests": total_requests,
            "completed_requests": 0,
            "successful_purchases": 0,
            "rejected_out_of_stock": 0,
            "oversold_units": 0,
            "duplicate_orders": 0,
            "duration_ms": 0,
            "rps": 0,
            "avg_latency_ms": 0,
            "status": "RUNNING",
            "result_status": "TESTING"
        })

        # Reset stock to exactly 100 for benchmark
        async with AsyncSessionLocal() as db:
            from sqlalchemy import update
            inv_stmt = (
                update(Inventory)
                .where(Inventory.product_id == product_id)
                .values(available_quantity=100, reserved_quantity=0, version=1)
            )
            await db.execute(inv_stmt)
            await db.commit()
            await redis_gate.reset_stock(product_id, 100)

        semaphore = asyncio.Semaphore(concurrency)
        latencies = []
        start_time = time.time()

        async def worker(request_idx: int):
            async with semaphore:
                req_start = time.time()
                user_id = f"sim-user-{(request_idx % 500) + 1:03d}"
                idem_key = f"loadtest-key-{request_idx}"
                
                success = False
                out_of_stock = False
                
                try:
                    async with AsyncSessionLocal() as db:
                        order, res_id_or_status = await order_service.create_order(
                            db=db,
                            user_id=user_id,
                            product_id=product_id,
                            quantity=1,
                            idempotency_key=idem_key
                        )
                        if res_id_or_status == "DUPLICATE":
                            self.progress["duplicate_orders"] += 1
                            success = True
                        else:
                            payment = await payment_service.process_payment(
                                db=db,
                                order_id=order.order_id,
                                amount=order.total_amount,
                                reservation_id=res_id_or_status
                            )
                            if payment.status == "SUCCESS":
                                success = True
                except Exception as e:
                    err_msg = str(e)
                    out_of_stock = True

                req_duration = (time.time() - req_start) * 1000
                latencies.append(req_duration)

                self.progress["completed_requests"] += 1
                if success:
                    self.progress["successful_purchases"] += 1
                else:
                    self.progress["rejected_out_of_stock"] += 1

        batch_size = 200
        for i in range(0, total_requests, batch_size):
            tasks = [worker(j) for j in range(i, min(i + batch_size, total_requests))]
            await asyncio.gather(*tasks)

        end_time = time.time()
        elapsed = end_time - start_time
        
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            res = await db.execute(select(Inventory).filter_by(product_id=product_id))
            inv = res.scalar_one()
            
            sold = self.progress["successful_purchases"]
            oversold = max(0, sold - 100)
            if inv.available_quantity < 0:
                oversold += abs(inv.available_quantity)
                
            self.progress["oversold_units"] = oversold

        avg_lat = sum(latencies) / len(latencies) if latencies else 0
        rps = total_requests / elapsed if elapsed > 0 else 0

        self.progress.update({
            "duration_ms": round(elapsed * 1000, 2),
            "rps": round(rps, 2),
            "avg_latency_ms": round(avg_lat, 2),
            "status": "COMPLETED",
            "result_status": "PASS — No Overselling" if oversold == 0 and sold <= 100 else "FAIL — Overselling Detected"
        })

        self.is_running = False
        return self.progress

load_test_runner = LoadTestRunner()
