# SALESTORM — High-Concurrency Flash Sale Platform

> **10,000 CONCURRENT USERS | 100 AVAILABLE UNITS | 0 OVERSELLING GUARANTEE**

SALESTORM is an enterprise-grade prototype designed for high-concurrency flash-sale events. It mathematically guarantees that even under extreme traffic bursts (10,000+ concurrent buy requests), the total number of successful purchases never exceeds available inventory (`available_quantity >= 0`).

---

## 🚀 Core Architecture Highlights

- **Fast Inventory Reservation Gate**: Redis atomic Lua script (`evalsha`) decrements inventory tokens in microsecond latency.
- **PostgreSQL Conditional SQL Update**: Ensures strict database consistency using conditional update constraints:
  ```sql
  UPDATE inventory
  SET available_quantity = available_quantity - :qty,
      reserved_quantity = reserved_quantity + :qty,
      version = version + 1
  WHERE product_id = :product_id AND available_quantity >= :qty;
  ```
- **Idempotency Protection**: Enforces `Idempotency-Key` header deduplication via PostgreSQL `idempotency_records` table and fast Redis cache.
- **Saga / Compensating Transactions**: If payment processing fails or times out, the saga automatically cancels the order and releases reserved stock.
- **Transactional Outbox Pattern**: Commits domain events (`ReservationCreated`, `PaymentSuccess`, `OrderConfirmed`, etc.) in the exact same SQL transaction as business updates, publishing asynchronously to Kafka.
- **30-Second Reservation TTL & Recovery**: Expired unpaid reservations automatically trigger stock release workers.
- **Service Outage Resiliency (30s Order Recovery)**: Payments processed during an Order Service outage accumulate in the Outbox/Kafka and reconcile automatically upon service recovery.

---

## 🛠️ Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS (Glassmorphism Jury Dashboard).
- **Backend Services**: Python 3.11+, FastAPI, SQLAlchemy 2.0 (Async Engine), Pydantic v2.
- **Database & Cache**: PostgreSQL / SQLite (Async), Redis.
- **Event Bus & Observability**: Kafka, Prometheus, Grafana.
- **Containers**: Docker & Docker Compose.

---

## 🎯 Quick Start (Standalone Local Execution)

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
Backend API will start at: `http://localhost:8000`  
Swagger API Docs: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Dashboard will open at: `http://localhost:3000`

---

## 🐳 Docker Deployment

To launch full microservices architecture including PostgreSQL, Redis, Kafka, Prometheus & Frontend:

```bash
docker compose up --build
```

---

## 🧪 Automated Testing

Run the automated test suite covering all 12 scenario specs:

```bash
cd backend
python -m pytest tests/test_salestorm.py -v
```

This verifies:
1. Normal Purchase Flow
2. Idempotency Key Reuse
3. Payment Failure Saga Compensation
4. Inventory Non-Negative Constraint
5. **10,000 Request Concurrency Test (0 Oversold Guarantee)**

---

## 📊 One-Click Jury Demo Scenarios

The **SALESTORM — Jury Demo** control panel provides one-click buttons for jury testing:

1. **Successful Purchase**: Full order lifecycle (`CREATED` -> `RESERVED` -> `CONFIRMED`).
2. **Payment Failure**: Triggers saga compensation (`PAYMENT_FAILED` -> `RELEASED` -> `CANCELLED`).
3. **Test Idempotency**: Submits duplicate `Idempotency-Key` headers.
4. **30s Order Service Outage**: Demonstrates zero event loss and auto-reconciliation.
5. **Run 10,000 Request Test**: Fires 10,000 concurrent purchase attempts on 100 stock units.
6. **50x Traffic Scaling**: Tests worker throughput under high traffic.
7. **Database Failure Simulation**: Injects 5s DB outage safely.
8. **Payment Gateway Failure**: Tests graceful fallback and inventory preservation.
