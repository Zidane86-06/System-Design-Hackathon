import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from app.db import AsyncSessionLocal
from app.models import Reservation, Order
from app.services.inventory_service import inventory_service
from app.services.order_service import order_service

class ReservationExpiryWorker:
    def __init__(self):
        self._running = False
        self._task = None

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._worker_loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    async def _worker_loop(self):
        while self._running:
            try:
                await self.check_expired_reservations()
            except Exception as e:
                print(f"Error in reservation expiry worker loop: {e}")
            await asyncio.sleep(2)

    async def check_expired_reservations(self):
        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as db:
            stmt = select(Reservation).where(
                Reservation.status == "ACTIVE",
                Reservation.expires_at <= now
            )
            res = await db.execute(stmt)
            expired_list = res.scalars().all()

            for reservation in expired_list:
                print(f"Worker expiring reservation: {reservation.reservation_id}")
                await inventory_service.release_reservation(
                    db=db,
                    reservation_id=reservation.reservation_id,
                    reason="EXPIRED"
                )
                
                # If order exists and is pending payment, cancel it
                if reservation.order_id:
                    ord_stmt = select(Order).where(Order.order_id == reservation.order_id)
                    ord_res = await db.execute(ord_stmt)
                    order = ord_res.scalar_one_or_none()
                    if order and order.status in ("CREATED", "RESERVED", "PAYMENT_PENDING"):
                        await order_service.update_order_status(db, order.order_id, "CANCELLED")

reservation_worker = ReservationExpiryWorker()
