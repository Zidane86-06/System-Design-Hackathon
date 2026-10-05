import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models import Payment, Order, Reservation
from app.services.inventory_service import inventory_service
from app.services.order_service import order_service
from app.services.outbox_service import outbox_service
from app.config import settings

class PaymentService:
    async def process_payment(
        self,
        db: AsyncSession,
        order_id: str,
        amount: float,
        reservation_id: str = None,
        simulate_failure: bool = False
    ) -> Payment:
        # Check Payment Gateway Chaos flag
        if settings.PAYMENT_GATEWAY_DOWN:
            simulate_failure = True

        stmt = select(Order).where(Order.order_id == order_id)
        res = await db.execute(stmt)
        order = res.scalar_one_or_none()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order '{order_id}' not found."
            )

        payment_id = str(uuid.uuid4())
        txn_id = f"txn_{str(uuid.uuid4())[:8]}"

        # Mock External Payment Gateway Logic
        is_success = not simulate_failure

        payment = Payment(
            payment_id=payment_id,
            order_id=order_id,
            amount=amount,
            status="SUCCESS" if is_success else "FAILED",
            transaction_id=txn_id if is_success else None,
            created_at=datetime.now(timezone.utc)
        )
        db.add(payment)

        # Get associated reservation
        res_stmt = select(Reservation).where(Reservation.order_id == order_id, Reservation.status == "ACTIVE")
        res_out = await db.execute(res_stmt)
        reservation = res_out.scalar_one_or_none()
        r_id = reservation.reservation_id if reservation else reservation_id

        if is_success:
            # Payment Success Path
            await outbox_service.create_event(
                db=db,
                aggregate_type="Payment",
                aggregate_id=payment_id,
                event_type="PaymentSuccess",
                payload={
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "amount": amount,
                    "transaction_id": txn_id,
                    "reservation_id": r_id
                }
            )
            
            # Check if Order Service is simulating outage
            if settings.ORDER_SERVICE_OUTAGE:
                # Do NOT update order state to CONFIRMED yet. Event is safely stored in Outbox/Kafka!
                print(f"Order Service OUTAGE simulated. Payment {payment_id} succeeded, order {order_id} pending recovery.")
                await db.commit()
            else:
                # Confirm Order & Reservation
                await order_service.update_order_status(db, order_id, "CONFIRMED")
                if r_id:
                    await inventory_service.confirm_reservation(db, r_id)
                await outbox_service.create_event(
                    db=db,
                    aggregate_type="Order",
                    aggregate_id=order_id,
                    event_type="OrderConfirmed",
                    payload={"order_id": order_id, "status": "CONFIRMED"}
                )
                await db.commit()
        else:
            # Payment Failure Path -> Saga Compensation Flow
            await outbox_service.create_event(
                db=db,
                aggregate_type="Payment",
                aggregate_id=payment_id,
                event_type="PaymentFailed",
                payload={
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "amount": amount,
                    "reason": "SIMULATED_PAYMENT_FAILURE",
                    "reservation_id": r_id
                }
            )

            # Trigger Saga Compensation: Cancel Order & Release Reservation
            await order_service.update_order_status(db, order_id, "CANCELLED")
            if r_id:
                await inventory_service.release_reservation(db, r_id, reason="RELEASED")

            await outbox_service.create_event(
                db=db,
                aggregate_type="Order",
                aggregate_id=order_id,
                event_type="OrderCancelled",
                payload={
                    "order_id": order_id,
                    "status": "CANCELLED",
                    "reason": "PAYMENT_FAILED"
                }
            )
            await db.commit()

        await outbox_service.publish_pending_events(db)
        return payment

payment_service = PaymentService()
