import { Product, Inventory, Order, SystemStatus, OutboxEvent } from '../types';

const API_BASE = '/api';

export async function fetchProducts(): Promise<Product[]> {
  const res = await fetch(`${API_BASE}/products`);
  if (!res.ok) throw new Error('Failed to fetch products');
  return res.json();
}

export async function fetchInventory(productId: string): Promise<Inventory> {
  const res = await fetch(`${API_BASE}/inventory/${productId}`);
  if (!res.ok) throw new Error('Failed to fetch inventory');
  return res.json();
}

export async function createOrder(
  userId: string,
  productId: string,
  quantity: number,
  idempotencyKey?: string,
  simulatePaymentFailure?: boolean
): Promise<Order> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (idempotencyKey) {
    headers['Idempotency-Key'] = idempotencyKey;
  }

  const res = await fetch(`${API_BASE}/orders`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      user_id: userId,
      product_id: productId,
      quantity,
      simulate_payment_failure: simulatePaymentFailure || false,
    }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Order creation failed');
  }
  return res.json();
}

export async function fetchOrder(orderId: string): Promise<Order> {
  const res = await fetch(`${API_BASE}/orders/${orderId}`);
  if (!res.ok) throw new Error('Failed to fetch order');
  return res.json();
}

export async function fetchSimulationStatus(): Promise<SystemStatus> {
  const res = await fetch(`${API_BASE}/simulation/status`);
  if (!res.ok) throw new Error('Failed to fetch status');
  return res.json();
}

export async function fetchRecentEvents(): Promise<OutboxEvent[]> {
  const res = await fetch(`${API_BASE}/simulation/events`);
  if (!res.ok) throw new Error('Failed to fetch events');
  return res.json();
}

export async function triggerLoadTest(totalRequests: number = 10000, concurrency: number = 200) {
  const res = await fetch(`${API_BASE}/simulation/load-test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ total_requests: totalRequests, concurrency, product_id: 'salestorm-prod-001' }),
  });
  return res.json();
}

export async function runScenario(scenarioId: string) {
  const res = await fetch(`${API_BASE}/simulation/scenarios/${scenarioId}`, {
    method: 'POST',
  });
  return res.json();
}

export async function triggerOrderOutage(duration: number = 30) {
  const res = await fetch(`${API_BASE}/simulation/order-service-outage?duration=${duration}`, {
    method: 'POST',
  });
  return res.json();
}

export async function triggerDatabaseFailure(duration: number = 5) {
  const res = await fetch(`${API_BASE}/simulation/database-failure?duration=${duration}`, {
    method: 'POST',
  });
  return res.json();
}

export async function triggerPaymentGatewayFailure(duration: number = 10) {
  const res = await fetch(`${API_BASE}/simulation/payment-gateway-failure?duration=${duration}`, {
    method: 'POST',
  });
  return res.json();
}
