from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Gauge

router = APIRouter(tags=["Metrics"])

# Prometheus Metrics definitions
REQUEST_COUNTER = Counter("salestorm_http_requests_total", "Total HTTP requests", ["method", "endpoint"])
SUCCESSFUL_SALES_GAUGE = Gauge("salestorm_successful_sales_total", "Total successful purchases")
AVAILABLE_INVENTORY_GAUGE = Gauge("salestorm_available_inventory", "Available inventory stock")
OVERSOLD_UNITS_GAUGE = Gauge("salestorm_oversold_units", "Oversold inventory count")

@router.get("/metrics")
async def prometheus_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
