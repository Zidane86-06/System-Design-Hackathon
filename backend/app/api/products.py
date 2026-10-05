from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.models import Product
from app.schemas import ProductOut

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("", response_model=List[ProductOut])
async def list_products(db: AsyncSession = Depends(get_db)):
    stmt = select(Product)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Product).where(Product.product_id == product_id)
    res = await db.execute(stmt)
    prod = res.scalar_one_or_none()
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return prod
