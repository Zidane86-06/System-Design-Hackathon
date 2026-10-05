# AI Usage Note — SALESTORM Flash-Sale Platform

This document outlines the usage of AI assistance in developing the **SALESTORM** high-concurrency flash-sale platform prototype for hackathon submission.

---

## 1. AI Tools Utilized

- **Google Antigravity AI Assistant** (Powered by Gemini 3.6 Flash)

---

## 2. Scope of AI Assistance

1. **Architecture & Schema Design**:
   - Assisting with SQLAlchemy 2.0 async database model definitions for 9 core tables (`users`, `products`, `inventory`, `reservations`, `orders`, `order_items`, `payments`, `idempotency_records`, `outbox_events`).
   - Designing the Redis Reservation Gate Lua script and PostgreSQL conditional SQL update strategy (`WHERE product_id = ? AND available_quantity >= ?`).

2. **Backend Microservice Implementation**:
   - Boilerplate code generation for FastAPI routers, Outbox pattern publisher, Order state machine, and Payment Saga compensation flows.
   - High-concurrency load testing module (`LoadTestRunner`) utilizing Python `asyncio` task pools.

3. **Frontend Dashboard Design**:
   - Creating glassmorphism React components in TypeScript and Tailwind CSS (`JuryDashboard`, `OrderTimeline`, `ServiceStatusPanel`, `EventLogViewer`).

---

## 3. Human Review & Verification

- **Manual Code Review**: All generated Python and TypeScript files were manually audited to enforce SRP/SOLID principles and guard against state race conditions.
- **Empirical Execution & Benchmarking**: Verified via automated `pytest` suite and live async benchmark load tests confirming:
  - Total requests: 10,000
  - Initial inventory: 100
  - Maximum successful purchases: 100
  - Oversold units: 0
