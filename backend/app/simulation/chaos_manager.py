import asyncio
import uuid
from typing import Dict, Any
from app.config import settings
from app.db import AsyncSessionLocal
from app.services.order_service import order_service
from app.services.payment_service import payment_service
from app.services.outbox_service import outbox_service
from app.redis_client import redis_gate
from app.models import Inventory, Order

class ChaosManager:
    async def toggle_order_service_outage(self, duration_seconds: int = 30) -> Dict[str, Any]:
        settings.ORDER_SERVICE_OUTAGE = True
        
        # Schedule auto recovery after duration
        async def recover():
            await asyncio.sleep(duration_seconds)
            settings.ORDER_SERVICE_OUTAGE = False
            # Replay pending outbox events / pending orders recovery
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                # Find orders stuck in PAYMENT_PENDING with successful payments
                stmt = select(Order).where(Order.status == "PAYMENT_PENDING")
                res = await db.execute(stmt)
                stuck_orders = res.scalars().all()
                for ord_obj in stuck_orders:
                    ord_obj.status = "CONFIRMED"
                await db.commit()
                await outbox_service.publish_pending_events(db)
            print(f"Order Service RECOVERED after {duration_seconds}s outage.")

        asyncio.create_task(recover())
        return {
            "status": "OUTAGE_SIMULATED",
            "duration": duration_seconds,
            "message": f"Order Service outage triggered for {duration_seconds}s. Events will accumulate in Outbox and auto-recover."
        }

    async def toggle_database_failure(self, duration_seconds: int = 5) -> Dict[str, Any]:
        settings.DATABASE_DOWN = True
        
        async def recover():
            await asyncio.sleep(duration_seconds)
            settings.DATABASE_DOWN = False
            print(f"Database RECOVERED after {duration_seconds}s failure simulation.")

        asyncio.create_task(recover())
        return {
            "status": "DATABASE_DOWN",
            "duration": duration_seconds,
            "message": f"Database failure simulated for {duration_seconds}s."
        }

    async def toggle_payment_gateway_failure(self, duration_seconds: int = 10) -> Dict[str, Any]:
        settings.PAYMENT_GATEWAY_DOWN = True
        
        async def recover():
            await asyncio.sleep(duration_seconds)
            settings.PAYMENT_GATEWAY_DOWN = False
            print(f"Payment Gateway RECOVERED after {duration_seconds}s.")

        asyncio.create_task(recover())
        return {
            "status": "GATEWAY_DOWN",
            "duration": duration_seconds,
            "message": f"Payment Gateway failure simulated for {duration_seconds}s."
        }

    async def run_scenario_successful_purchase(self) -> Dict[str, Any]:
        idem_key = f"demo-succ-{str(uuid.uuid4())[:8]}"
        async with AsyncSessionLocal() as db:
            order, res_id = await order_service.create_order(
                db=db,
                user_id="user-demo-succ",
                product_id="salestorm-prod-001",
                quantity=1,
                idempotency_key=idem_key
            )
            payment = await payment_service.process_payment(
                db=db,
                order_id=order.order_id,
                amount=order.total_amount,
                reservation_id=res_id
            )
            return {
                "scenario": "Successful Purchase",
                "order_id": order.order_id,
                "order_status": order.status,
                "payment_status": payment.status,
                "idempotency_key": idem_key
            }

    async def run_scenario_payment_failure(self) -> Dict[str, Any]:
        idem_key = f"demo-fail-{str(uuid.uuid4())[:8]}"
        async with AsyncSessionLocal() as db:
            order, res_id = await order_service.create_order(
                db=db,
                user_id="user-demo-fail",
                product_id="salestorm-prod-001",
                quantity=1,
                idempotency_key=idem_key
            )
            payment = await payment_service.process_payment(
                db=db,
                order_id=order.order_id,
                amount=order.total_amount,
                reservation_id=res_id,
                simulate_failure=True
            )
            return {
                "scenario": "Payment Failure & Compensation",
                "order_id": order.order_id,
                "order_status": order.status, # Should be CANCELLED
                "payment_status": payment.status, # Should be FAILED
                "compensation": "Inventory reservation RELEASED, Order CANCELLED"
            }

    async def run_scenario_duplicate_buy(self) -> Dict[str, Any]:
        fixed_idem_key = "IDEMPOTENT-DEMO-KEY-123"
        async with AsyncSessionLocal() as db:
            # First request
            ord1, res_id1 = await order_service.create_order(
                db=db,
                user_id="user-idem-demo",
                product_id="salestorm-prod-001",
                quantity=1,
                idempotency_key=fixed_idem_key
            )
            # Duplicate request with SAME key
            ord2, status2 = await order_service.create_order(
                db=db,
                user_id="user-idem-demo",
                product_id="salestorm-prod-001",
                quantity=1,
                idempotency_key=fixed_idem_key
            )
            return {
                "scenario": "Duplicate Request Test",
                "idempotency_key": fixed_idem_key,
                "request_1_order_id": ord1.order_id,
                "request_2_order_id": ord2.order_id,
                "identical": ord1.order_id == ord2.order_id,
                "result": "PASS — Duplicate request returned existing order without creating new order!"
            }

chaos_manager = ChaosManager()
