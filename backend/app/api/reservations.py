from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.models import Reservation
from app.schemas import ReservationOut

router = APIRouter(prefix="/reservations", tags=["Reservations"])

@router.get("/{reservation_id}", response_model=ReservationOut)
async def get_reservation(reservation_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Reservation).where(Reservation.reservation_id == reservation_id)
    res = await db.execute(stmt)
    reservation = res.scalar_one_or_none()
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
    return reservation
