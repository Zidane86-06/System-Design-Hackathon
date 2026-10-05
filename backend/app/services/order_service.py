import json
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models import Order, OrderItem, IdempotencyRecord, Product
from app.services.inventory_service import inventory_service
from app.services.outbox_service import outbox_service
from app.config import settings

VALID_STATE_TRANSITIONS = {
    "CREATED": ["RESERVATION_PENDING", "CANCELLED"],
    "RESERVATION_PENDING": ["RESERVED", "CANCELLED"],
    "RESERVED": ["PAYMENT_PENDING", "CANCELLED"],
    "PAYMENT_PENDING": ["CONFIRMED", "PAYMENT_FAILED", "CANCELLED"],
    "CONFIRMED": [],
    "PAYMENT_FAILED": ["CANCELLED"],
    "CANCELLED": []
}

class OrderService:
    async def create_order(
        self,
        db: AsyncSession,
        user_id: str,
        product_id: str,
        quantity: int,
        idempotency_key: str = None
    ) -> tuple[Order, str]:
        """
        Creates an order with idempotency check, inventory reservation gate, 
        and initial state machine transition.
        """
        # 1. Idempotency Key Validation & Check
        if idempotency_key:
            stmt = select(IdempotencyRecord).where(IdempotencyRecord.idempotency_key == idempotency_key)
            res = await db.execute(stmt)
            existing_rec = res.scalar_one_or_none()
            if existing_rec:
                if existing_rec.order_id:
                    ord_stmt = select(Order).where(Order.order_id == existing_rec.order_id)
                    ord_res = await db.execute(ord_stmt)
                    existing_order = ord_res.scalar_one_or_none()
                    if existing_order:
                        # Return existing order for duplicate idempotency key
                        return existing_order, "DUPLICATE"
                # If record exists without order, return response from record
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key already processed."
                )

        # 2. Get Product Info
        prod_stmt = select(Product).where(Product.product_id == product_id)
        prod_res = await db.execute(prod_stmt)
        product = prod_res.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found."
            )

        order_id = str(uuid.uuid4())
        total_amount = product.price * quantity

        # 3. Create initial order in CREATED state
        order = Order(
            order_id=order_id,
            user_id=user_id,
            status="CREATED",
            total_amount=total_amount,
            idempotency_key=idempotency_key,
            created_at=datetime.now(timezone.utc)
        )
        db.add(order)

        order_item = OrderItem(
            order_item_id=str(uuid.uuid4()),
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=product.price,
            subtotal=total_amount
        )
        db.add(order_item)

        # Record Idempotency key if provided
        if idempotency_key:
            idem_rec = IdempotencyRecord(
                idempotency_id=str(uuid.uuid4()),
                idempotency_key=idempotency_key,
                user_id=user_id,
                order_id=order_id,
                response_status=201
            )
            db.add(idem_rec)

        # Transition -> RESERVATION_PENDING
        order.status = "RESERVATION_PENDING"

        # 4. Reserve Inventory (Redis Gate + Conditional Postgres Update)
        reservation = await inventory_service.reserve_stock(
            db=db,
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            order_id=order_id
        )

        # Transition -> RESERVED -> PAYMENT_PENDING
        order.status = "PAYMENT_PENDING"

        # Outbox event
        await outbox_service.create_event(
            db=db,
            aggregate_type="Order",
            aggregate_id=order_id,
            event_type="OrderCreated",
            payload={
                "order_id": order_id,
                "user_id": user_id,
                "product_id": product_id,
                "quantity": quantity,
                "total_amount": total_amount,
                "reservation_id": reservation.reservation_id,
                "idempotency_key": idempotency_key
            }
        )

        await db.commit()
        await outbox_service.publish_pending_events(db)
        
        return order, reservation.reservation_id

    async def update_order_status(self, db: AsyncSession, order_id: str, new_status: str):
        stmt = select(Order).where(Order.order_id == order_id)
        res = await db.execute(stmt)
        order = res.scalar_one_or_none()
        if not order:
            return None
        
        current = order.status
        allowed = VALID_STATE_TRANSITIONS.get(current, [])
        if new_status not in allowed and new_status != current:
            print(f"Warning: Invalid state transition from {current} to {new_status}")

        order.status = new_status
        order.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return order

order_service = OrderService()
