import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle, XCircle, Shield, AlertCircle, ArrowRight } from 'lucide-react';
import { Order } from '../types';

interface OrderTimelineProps {
  order: Order | null;
}

export const OrderTimeline: React.FC<OrderTimelineProps> = ({ order }) => {
  const [ttlSeconds, setTtlSeconds] = useState<number>(30);

  useEffect(() => {
    if (order && order.status === 'PAYMENT_PENDING') {
      setTtlSeconds(30);
      const timer = setInterval(() => {
        setTtlSeconds((prev) => (prev > 0 ? prev - 1 : 0));
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [order]);

  if (!order) {
    return (
      <div className="glass-panel p-6 rounded-2xl border border-white/10 text-center text-slate-400 font-mono text-xs py-12">
        <Clock className="w-8 h-8 text-slate-600 mx-auto mb-2" />
        <p>No active order selected. Submit a Buy Request or click a scenario to view real-time state machine transitions.</p>
      </div>
    );
  }

  const isConfirmed = order.status === 'CONFIRMED';
  const isCancelled = order.status === 'CANCELLED' || order.status === 'PAYMENT_FAILED';

  const steps = [
    { label: 'Order Created', state: 'CREATED', done: true },
    { label: 'Stock Reserved (Redis)', state: 'RESERVED', done: true },
    { label: 'Payment Processing', state: 'PAYMENT_PENDING', done: isConfirmed || isCancelled },
    {
      label: isCancelled ? 'Saga Compensated (Cancelled)' : 'Order Confirmed',
      state: isCancelled ? 'CANCELLED' : 'CONFIRMED',
      done: isConfirmed || isCancelled,
      error: isCancelled,
    },
  ];

  return (
    <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-base font-bold text-white">Order Real-Time State Machine</h3>
            <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${isConfirmed ? 'bg-emerald-500/20 text-emerald-300' : isCancelled ? 'bg-rose-500/20 text-rose-300' : 'bg-amber-500/20 text-amber-300'}`}>
              {order.status}
            </span>
          </div>
          <p className="text-xs font-mono text-slate-400 mt-1">ID: {order.order_id}</p>
        </div>

        {order.status === 'PAYMENT_PENDING' && (
          <div className="flex items-center space-x-2 bg-amber-500/10 border border-amber-500/30 px-3 py-1.5 rounded-lg font-mono text-xs text-amber-300">
            <Clock className="w-4 h-4 animate-spin text-amber-400" />
            <span>Reservation TTL: {ttlSeconds}s</span>
          </div>
        )}
      </div>

      {/* STATE TRANSITION STEPS VISUALIZER */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 py-2">
        {steps.map((step, idx) => (
          <div
            key={idx}
            className={`p-3 rounded-xl border font-mono text-xs flex flex-col justify-between ${
              step.error
                ? 'bg-rose-950/40 border-rose-500/40 text-rose-300'
                : step.done
                ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300'
                : 'bg-slate-900 border-slate-800 text-slate-500'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] opacity-70">STEP 0{idx + 1}</span>
              {step.error ? (
                <XCircle className="w-4 h-4 text-rose-400" />
              ) : step.done ? (
                <CheckCircle className="w-4 h-4 text-emerald-400" />
              ) : (
                <Clock className="w-4 h-4 text-slate-600" />
              )}
            </div>
            <p className="font-bold">{step.label}</p>
          </div>
        ))}
      </div>

      {order.idempotency_key && (
        <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-xs font-mono text-slate-400 flex items-center justify-between">
          <span>Idempotency Protection Header:</span>
          <span className="text-cyan-300 font-bold">{order.idempotency_key}</span>
        </div>
      )}
    </div>
  );
};
