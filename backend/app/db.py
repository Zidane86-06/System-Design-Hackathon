import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool, NullPool
from sqlalchemy import select
from app.config import settings
from app.models import Base, Product, Inventory, User, Order, OrderItem, Payment, IdempotencyRecord, OutboxEvent, Reservation

if "sqlite" in settings.DATABASE_URL:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Product).where(Product.product_id == "salestorm-prod-001"))
        prod = res.scalar_one_or_none()
        
        if not prod:
            default_product = Product(
                product_id="salestorm-prod-001",
                name="SALESTORM Limited Edition Product",
                price=999.0
            )
            default_inventory = Inventory(
                inventory_id="salestorm-inv-001",
                product_id="salestorm-prod-001",
                total_quantity=100,
                available_quantity=100,
                reserved_quantity=0,
                version=1
            )
            default_user = User(
                user_id="demo-user-001",
                name="Demo Hacker",
                email="demo@salestorm.io"
            )
            session.add(default_product)
            session.add(default_inventory)
            session.add(default_user)
            await session.commit()
            print("Successfully seeded initial product and 100 stock units!")
