import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text
from fastapi import HTTPException, status
from app.models import Inventory, Reservation
from app.redis_client import redis_gate
from app.services.outbox_service import outbox_service
from app.config import settings

class InventoryService:
    async def reserve_stock(
        self,
        db: AsyncSession,
        user_id: str,
        product_id: str,
        quantity: int = 1,
        order_id: str = None
    ) -> Reservation:
        if settings.DATABASE_DOWN:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is currently unavailable (Chaos Simulated)"
            )

        reservation_id = str(uuid.uuid4())
        ttl = settings.RESERVATION_TTL_SECONDS
        
        # Step 1: Redis Reservation Gate Check
        gate_success = await redis_gate.reserve(product_id, reservation_id, quantity, ttl)
        if not gate_success:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="OUT_OF_STOCK: Redis reservation gate rejected request - stock exhausted."
            )

        # Step 2: PostgreSQL Conditional Update
        # UPDATE inventory SET available_quantity = available_quantity - qty, reserved_quantity = reserved_quantity + qty
        # WHERE product_id = ? AND available_quantity >= qty;
        stmt = (
            update(Inventory)
            .where(
                Inventory.product_id == product_id,
                Inventory.available_quantity >= quantity
            )
            .values(
                available_quantity=Inventory.available_quantity - quantity,
                reserved_quantity=Inventory.reserved_quantity + quantity,
                version=Inventory.version + 1,
                updated_at=datetime.now(timezone.utc)
            )
        )
        
        result = await db.execute(stmt)
        
        # Check affected rows
        if result.rowcount == 0:
            # Revert Redis reservation gate since DB conditional check failed
            await redis_gate.release(product_id, reservation_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="OUT_OF_STOCK: DB conditional update failed - insufficient stock."
            )

        # Step 3: Create Reservation Record
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        reservation = Reservation(
            reservation_id=reservation_id,
            user_id=user_id,
            product_id=product_id,
            order_id=order_id,
            quantity=quantity,
            status="ACTIVE",
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at
        )
        db.add(reservation)

        # Step 4: Outbox Event
        await outbox_service.create_event(
            db=db,
            aggregate_type="Reservation",
            aggregate_id=reservation_id,
            event_type="ReservationCreated",
            payload={
                "reservation_id": reservation_id,
                "user_id": user_id,
                "product_id": product_id,
                "order_id": order_id,
                "quantity": quantity,
                "expires_at": expires_at.isoformat()
            }
        )

        return reservation

    async def release_reservation(
        self,
        db: AsyncSession,
        reservation_id: str,
        reason: str = "RELEASED" # RELEASED or EXPIRED
    ) -> bool:
        stmt = select(Reservation).where(Reservation.reservation_id == reservation_id)
        res = await db.execute(stmt)
        reservation = res.scalar_one_or_none()
        
        if not reservation or reservation.status not in ("ACTIVE", "RESERVED"):
            return False

        # Conditional DB update to return inventory
        inv_stmt = (
            update(Inventory)
            .where(Inventory.product_id == reservation.product_id)
            .values(
                available_quantity=Inventory.available_quantity + reservation.quantity,
                reserved_quantity=Inventory.reserved_quantity - reservation.quantity,
                version=Inventory.version + 1,
                updated_at=datetime.now(timezone.utc)
            )
        )
        await db.execute(inv_stmt)

        reservation.status = reason

        # Redis release
        await redis_gate.release(reservation.product_id, reservation_id)

        # Outbox event
        event_type = "ReservationExpired" if reason == "EXPIRED" else "ReservationReleased"
        await outbox_service.create_event(
            db=db,
            aggregate_type="Reservation",
            aggregate_id=reservation_id,
            event_type=event_type,
            payload={
                "reservation_id": reservation_id,
                "product_id": reservation.product_id,
                "order_id": reservation.order_id,
                "quantity": reservation.quantity,
                "reason": reason
            }
        )
        
        await db.commit()
        return True

    async def confirm_reservation(self, db: AsyncSession, reservation_id: str):
        stmt = select(Reservation).where(Reservation.reservation_id == reservation_id)
        res = await db.execute(stmt)
        reservation = res.scalar_one_or_none()
        
        if reservation and reservation.status == "ACTIVE":
            reservation.status = "CONFIRMED"
            # Deduct from reserved_quantity (since sale completed)
            inv_stmt = (
                update(Inventory)
                .where(Inventory.product_id == reservation.product_id)
                .values(
                    reserved_quantity=Inventory.reserved_quantity - reservation.quantity,
                    version=Inventory.version + 1,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await db.execute(inv_stmt)
            await db.commit()

inventory_service = InventoryService()
