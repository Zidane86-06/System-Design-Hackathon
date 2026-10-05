import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Index, Text, CheckConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class Product(Base):
    __tablename__ = "products"
    
    product_id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    inventory = relationship("Inventory", back_populates="product", uselist=False)

class Inventory(Base):
    __tablename__ = "inventory"
    
    inventory_id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.product_id"), unique=True, nullable=False)
    total_quantity = Column(Integer, nullable=False)
    available_quantity = Column(Integer, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    product = relationship("Product", back_populates="inventory")

    __table_args__ = (
        CheckConstraint("available_quantity >= 0", name="chk_available_qty_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="chk_reserved_qty_non_negative"),
    )

class Reservation(Base):
    __tablename__ = "reservations"
    
    reservation_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.product_id"), nullable=False)
    order_id = Column(String(36), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False, default="ACTIVE") # ACTIVE, CONFIRMED, EXPIRED, RELEASED
    created_at = Column(DateTime(timezone=True), default=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=False)

class Order(Base):
    __tablename__ = "orders"
    
    order_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    status = Column(String(50), nullable=False, default="CREATED")
    # States: CREATED, RESERVATION_PENDING, RESERVED, PAYMENT_PENDING, CONFIRMED, PAYMENT_FAILED, CANCELLED
    total_amount = Column(Float, nullable=False)
    idempotency_key = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

class OrderItem(Base):
    __tablename__ = "order_items"
    
    order_item_id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.order_id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

class Payment(Base):
    __tablename__ = "payments"
    
    payment_id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.order_id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(50), nullable=False) # PENDING, SUCCESS, FAILED
    transaction_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    
    idempotency_id = Column(String(36), primary_key=True, default=generate_uuid)
    idempotency_key = Column(String(100), unique=True, nullable=False)
    user_id = Column(String(36), nullable=False)
    order_id = Column(String(36), nullable=True)
    response_status = Column(Integer, nullable=False, default=200)
    response_body = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=True)

class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    
    event_id = Column(String(36), primary_key=True, default=generate_uuid)
    aggregate_type = Column(String(50), nullable=False)
    aggregate_id = Column(String(36), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False) # JSON encoded
    published = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    published_at = Column(DateTime(timezone=True), nullable=True)
