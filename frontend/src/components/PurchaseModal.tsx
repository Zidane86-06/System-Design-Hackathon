import React, { useState, useEffect } from 'react';
import { X, Zap, ShieldCheck, RefreshCw, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { createOrder } from '../services/api';
import { Order } from '../types';

interface PurchaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOrderCreated: (order: Order) => void;
}

export const PurchaseModal: React.FC<PurchaseModalProps> = ({ isOpen, onClose, onOrderCreated }) => {
  const [userId, setUserId] = useState('demo-user-001');
  const [quantity, setQuantity] = useState(1);
  const [idempotencyKey, setIdempotencyKey] = useState('');
  const [simulateFailure, setSimulateFailure] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastOrder, setLastOrder] = useState<Order | null>(null);

  useEffect(() => {
    if (isOpen) {
      generateKey();
      setError(null);
      setLastOrder(null);
    }
  }, [isOpen]);

  const generateKey = () => {
    setIdempotencyKey(`idem-key-${Math.random().toString(36).substring(2, 10)}`);
  };

  const handleBuy = async (isDuplicate = false) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const order = await createOrder(
        userId,
        'salestorm-prod-001',
        quantity,
        idempotencyKey,
        simulateFailure
      );
      setLastOrder(order);
      onOrderCreated(order);
    } catch (err: any) {
      setError(err.message || 'Purchase request failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="glass-panel max-w-lg w-full rounded-2xl border border-white/10 p-6 space-y-5 relative shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center space-x-2">
            <Zap className="w-5 h-5 text-cyan-400" />
            <h3 className="text-lg font-bold text-white">Purchase Flash Item</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4 text-xs font-mono">
          <div>
            <label className="block text-slate-400 mb-1">USER ID</label>
            <input
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-slate-400 mb-1">PRODUCT</label>
            <input
              type="text"
              value="SALESTORM Limited Edition Product (₹999)"
              disabled
              className="w-full bg-slate-900/50 border border-slate-800 rounded-lg px-3 py-2 text-slate-400 cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-slate-400 mb-1">IDEMPOTENCY KEY (HEADER)</label>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={idempotencyKey}
                onChange={(e) => setIdempotencyKey(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-cyan-300 font-bold focus:outline-none focus:border-cyan-500"
              />
              <button
                onClick={generateKey}
                className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 border border-slate-700"
                title="Generate new key"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="flex items-center space-x-2 pt-1">
            <input
              type="checkbox"
              id="sim-fail"
              checked={simulateFailure}
              onChange={(e) => setSimulateFailure(e.target.checked)}
              className="rounded bg-slate-900 border-slate-700 text-rose-500 focus:ring-rose-500"
            />
            <label htmlFor="sim-fail" className="text-amber-400 cursor-pointer select-none">
              Simulate Payment Failure (Triggers Saga Compensation)
            </label>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-xs font-mono flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {lastOrder && (
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-300 text-xs font-mono space-y-1">
            <div className="flex items-center space-x-1 font-bold">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Order Created: {lastOrder.order_id}</span>
            </div>
            <p>Status: <span className="font-bold text-white">{lastOrder.status}</span></p>
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
          <button
            onClick={() => handleBuy(false)}
            disabled={isSubmitting}
            className="w-full py-3 bg-gradient-to-r from-cyan-400 to-cyan-500 hover:from-cyan-300 hover:to-cyan-400 text-slate-950 font-bold font-mono text-sm rounded-xl transition shadow-lg shadow-cyan-500/20"
          >
            {isSubmitting ? 'PROCESSING...' : 'SUBMIT BUY REQUEST'}
          </button>

          <button
            onClick={() => handleBuy(true)}
            disabled={isSubmitting}
            className="w-full py-3 bg-slate-800 hover:bg-slate-700 border border-purple-500/50 text-purple-300 font-bold font-mono text-xs rounded-xl transition"
          >
            SEND DUPLICATE REQUEST
          </button>
        </div>
      </div>
    </div>
  );
};
