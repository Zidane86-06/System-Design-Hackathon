from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db import get_db
from app.schemas import LoadTestRequest, SimulationStatus
from app.simulation.load_tester import load_test_runner
from app.simulation.chaos_manager import chaos_manager
from app.config import settings
from app.models import Inventory, Order, Reservation, Payment
from app.redis_client import redis_gate
from app.event_bus import event_bus

router = APIRouter(prefix="/simulation", tags=["Simulation"])

@router.post("/load-test")
async def trigger_load_test(req: LoadTestRequest, background_tasks: BackgroundTasks):
    if load_test_runner.is_running:
        return load_test_runner.progress
    
    # Run async test in background
    background_tasks.add_task(
        load_test_runner.run_test,
        total_requests=req.total_requests,
        concurrency=req.concurrency,
        product_id=req.product_id
    )
    return {
        "message": f"Started {req.total_requests} request load test with concurrency {req.concurrency}.",
        "status": "RUNNING"
    }

@router.get("/load-test/progress")
async def get_load_test_progress():
    return load_test_runner.progress

@router.post("/order-service-outage")
async def trigger_order_service_outage(duration: int = 30):
    return await chaos_manager.toggle_order_service_outage(duration)

@router.post("/database-failure")
async def trigger_database_failure(duration: int = 5):
    return await chaos_manager.toggle_database_failure(duration)

@router.post("/payment-gateway-failure")
async def trigger_payment_gateway_failure(duration: int = 10):
    return await chaos_manager.toggle_payment_gateway_failure(duration)

@router.post("/scenarios/{scenario_id}")
async def run_scenario(scenario_id: str):
    if scenario_id == "successful-purchase":
        return await chaos_manager.run_scenario_successful_purchase()
    elif scenario_id == "payment-failure":
        return await chaos_manager.run_scenario_payment_failure()
    elif scenario_id == "duplicate-buy":
        return await chaos_manager.run_scenario_duplicate_buy()
    elif scenario_id == "reset-inventory":
        await redis_gate.reset_stock("salestorm-prod-001", 100)
        from sqlalchemy import update
        async with AsyncSessionLocal() as db:
            inv_stmt = update(Inventory).where(Inventory.product_id == "salestorm-prod-001").values(
                available_quantity=100, reserved_quantity=0, version=1
            )
            await db.execute(inv_stmt)
            await db.commit()
        return {"status": "SUCCESS", "message": "Reset inventory stock to 100"}
    else:
        return {"status": "UNKNOWN_SCENARIO", "scenario_id": scenario_id}

@router.get("/status")
async def get_simulation_status(db: AsyncSession = Depends(get_db)):
    # Calculate live inventory stats
    inv_stmt = select(Inventory).filter_by(product_id="salestorm-prod-001")
    res = await db.execute(inv_stmt)
    inv = res.scalar_one_or_none()
    
    redis_avail = await redis_gate.get_available("salestorm-prod-001")
    
    # Counts
    orders_cnt = await db.execute(select(func.count(Order.order_id)))
    total_orders = orders_cnt.scalar() or 0
    
    succ_cnt = await db.execute(select(func.count(Order.order_id)).where(Order.status == "CONFIRMED"))
    successful_sales = succ_cnt.scalar() or 0

    fail_cnt = await db.execute(select(func.count(Order.order_id)).where(Order.status == "CANCELLED"))
    cancelled_orders = fail_cnt.scalar() or 0

    available_units = inv.available_quantity if inv else 100
    reserved_units = inv.reserved_quantity if inv else 0
    total_units = inv.total_quantity if inv else 100

    return {
        "inventory": {
            "total_units": total_units,
            "available_units": min(available_units, redis_avail),
            "reserved_units": reserved_units,
            "successful_sales": successful_sales,
            "cancelled_orders": cancelled_orders,
            "oversold_units": max(0, successful_sales - 100)
        },
        "system_health": {
            "inventory_service": "HEALTHY" if not settings.DATABASE_DOWN else "DOWN",
            "order_service": "DOWN (SIMULATED)" if settings.ORDER_SERVICE_OUTAGE else "HEALTHY",
            "payment_service": "DOWN (SIMULATED)" if settings.PAYMENT_GATEWAY_DOWN else "HEALTHY",
            "database": "DOWN (SIMULATED)" if settings.DATABASE_DOWN else "HEALTHY",
            "payment_gateway": "DOWN (SIMULATED)" if settings.PAYMENT_GATEWAY_DOWN else "HEALTHY",
            "kafka": "HEALTHY",
            "redis": "HEALTHY"
        },
        "flags": {
            "order_service_outage": settings.ORDER_SERVICE_OUTAGE,
            "db_down": settings.DATABASE_DOWN,
            "payment_gateway_down": settings.PAYMENT_GATEWAY_DOWN
        },
        "load_test_progress": load_test_runner.progress
    }

@router.get("/events")
async def get_simulation_events():
    return event_bus.get_recent_events()
