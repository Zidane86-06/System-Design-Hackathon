export interface Product {
  product_id: string;
  name: string;
  price: number;
  created_at: string;
}

export interface Inventory {
  inventory_id: string;
  product_id: string;
  total_quantity: number;
  available_quantity: number;
  reserved_quantity: number;
  version: number;
  updated_at: string;
}

export interface Order {
  order_id: string;
  user_id: string;
  status: string;
  total_amount: number;
  idempotency_key?: string;
  created_at: string;
  updated_at: string;
  reservation_id?: string;
}

export interface Payment {
  payment_id: string;
  order_id: string;
  amount: number;
  status: string;
  transaction_id?: string;
  created_at: string;
}

export interface SystemStatus {
  inventory: {
    total_units: number;
    available_units: number;
    reserved_units: number;
    successful_sales: number;
    cancelled_orders: number;
    oversold_units: number;
  };
  system_health: {
    inventory_service: string;
    order_service: string;
    payment_service: string;
    database: string;
    payment_gateway: string;
    kafka: string;
    redis: string;
  };
  flags: {
    order_service_outage: boolean;
    db_down: boolean;
    payment_gateway_down: boolean;
  };
  load_test_progress: {
    total_requests: number;
    completed_requests: number;
    successful_purchases: number;
    rejected_out_of_stock: number;
    oversold_units: number;
    duplicate_orders: number;
    duration_ms: number;
    rps: number;
    avg_latency_ms: number;
    status: string;
    result_status: string;
  };
}

export interface OutboxEvent {
  event_id: string;
  event_type: string;
  aggregate_id: string;
  payload: any;
  timestamp: string;
}
