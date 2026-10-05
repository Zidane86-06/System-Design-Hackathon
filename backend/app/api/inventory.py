from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.models import Inventory
from app.schemas import InventoryOut
from app.services.inventory_service import inventory_service
from app.redis_client import redis_gate

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.get("/{product_id}", response_model=InventoryOut)
async def get_inventory(product_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Inventory).where(Inventory.product_id == product_id)
    res = await db.execute(stmt)
    inv = res.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found")
    
    # Sync with Redis gate for accuracy
    redis_avail = await redis_gate.get_available(product_id)
    inv.available_quantity = min(inv.available_quantity, redis_avail)
    return inv

@router.post("/{product_id}/reserve")
async def reserve_inventory(
    product_id: str,
    user_id: str = "demo-user-001",
    quantity: int = 1,
    db: AsyncSession = Depends(get_db)
):
    reservation = await inventory_service.reserve_stock(
        db=db, user_id=user_id, product_id=product_id, quantity=quantity
    )
    await db.commit()
    return {"status": "SUCCESS", "reservation_id": reservation.reservation_id}

@router.post("/{product_id}/release")
async def release_inventory(
    reservation_id: str,
    db: AsyncSession = Depends(get_db)
):
    success = await inventory_service.release_reservation(db=db, reservation_id=reservation_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not release reservation")
    return {"status": "SUCCESS", "reservation_id": reservation_id}
