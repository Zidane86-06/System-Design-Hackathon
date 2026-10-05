from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.models import Order
from app.schemas import CreateOrderRequest, OrderOut
from app.services.order_service import order_service
from app.services.payment_service import payment_service

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    req: CreateOrderRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db)
):
    order, res_id_or_status = await order_service.create_order(
        db=db,
        user_id=req.user_id,
        product_id=req.product_id,
        quantity=req.quantity,
        idempotency_key=idempotency_key
    )

    if res_id_or_status != "DUPLICATE":
        # Process payment automatically unless requested to simulate failure
        payment = await payment_service.process_payment(
            db=db,
            order_id=order.order_id,
            amount=order.total_amount,
            reservation_id=res_id_or_status,
            simulate_failure=req.simulate_payment_failure or False
        )
        
    out = OrderOut.model_validate(order)
    if res_id_or_status != "DUPLICATE":
        out.reservation_id = res_id_or_status
    return out

@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Order).where(Order.order_id == order_id)
    res = await db.execute(stmt)
    ord_obj = res.scalar_one_or_none()
    if not ord_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return ord_obj

@router.post("/{order_id}/cancel", response_model=OrderOut)
async def cancel_order(order_id: str, db: AsyncSession = Depends(get_db)):
    ord_obj = await order_service.update_order_status(db, order_id, "CANCELLED")
    if not ord_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return ord_obj
