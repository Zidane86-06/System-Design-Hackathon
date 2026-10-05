from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class ProductOut(BaseModel):
    product_id: str
    name: str
    price: float
    created_at: datetime

    class Config:
        from_attributes = True

class InventoryOut(BaseModel):
    inventory_id: str
    product_id: str
    total_quantity: int
    available_quantity: int
    reserved_quantity: int
    version: int
    updated_at: datetime

    class Config:
        from_attributes = True

class CreateOrderRequest(BaseModel):
    user_id: str = Field(default="demo-user-001")
    product_id: str = Field(default="salestorm-prod-001")
    quantity: int = Field(default=1, ge=1)
    simulate_payment_failure: Optional[bool] = False

class OrderOut(BaseModel):
    order_id: str
    user_id: str
    status: str
    total_amount: float
    idempotency_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    reservation_id: Optional[str] = None

    class Config:
        from_attributes = True

class ReservationOut(BaseModel):
    reservation_id: str
    user_id: str
    product_id: str
    order_id: Optional[str] = None
    quantity: int
    status: str
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True

class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    simulate_failure: Optional[bool] = False

class PaymentOut(BaseModel):
    payment_id: str
    order_id: str
    amount: float
    status: str
    transaction_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class LoadTestRequest(BaseModel):
    total_requests: int = Field(default=10000, ge=1, le=50000)
    concurrency: int = Field(default=200, ge=1, le=1000)
    product_id: str = Field(default="salestorm-prod-001")

class SimulationStatus(BaseModel):
    inventory_service_status: str
    order_service_status: str
    payment_service_status: str
    database_status: str
    payment_gateway_status: str
    kafka_status: str
    redis_status: str
    order_service_outage: bool
    db_down: bool
    payment_gateway_down: bool
