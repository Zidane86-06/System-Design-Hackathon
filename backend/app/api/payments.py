from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.models import Payment
from app.schemas import PaymentRequest, PaymentOut
from app.services.payment_service import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("", response_model=PaymentOut)
async def make_payment(req: PaymentRequest, db: AsyncSession = Depends(get_db)):
    payment = await payment_service.process_payment(
        db=db,
        order_id=req.order_id,
        amount=req.amount,
        simulate_failure=req.simulate_failure or False
    )
    return payment

@router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Payment).where(Payment.payment_id == payment_id)
    res = await db.execute(stmt)
    pay = res.scalar_one_or_none()
    if not pay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return pay
