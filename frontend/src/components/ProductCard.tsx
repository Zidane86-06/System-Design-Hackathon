import React from 'react';
import { ShoppingBag, Zap, Tag, ShieldCheck } from 'lucide-react';
import { Product, Inventory } from '../types';

interface ProductCardProps {
  product: Product | null;
  inventory: Inventory | null;
  onOpenBuyModal: () => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product, inventory, onOpenBuyModal }) => {
  const available = inventory ? inventory.available_quantity : 100;
  const reserved = inventory ? inventory.reserved_quantity : 0;
  const total = inventory ? inventory.total_quantity : 100;
  const isOutOfStock = available <= 0;

  return (
    <div className="glass-panel p-6 rounded-2xl border border-white/10 relative overflow-hidden group">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-16 h-16 rounded-xl bg-gradient-to-tr from-cyan-500 to-purple-600 flex items-center justify-center text-slate-900 shadow-lg shadow-cyan-500/20 group-hover:scale-105 transition-transform">
            <ShoppingBag className="w-8 h-8 text-slate-950 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-xl font-bold text-white">{product?.name || "SALESTORM Limited Edition Product"}</h3>
              <span className="text-[10px] font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2 py-0.5 rounded">
                LIMITED FLASH SALE
              </span>
            </div>
            <p className="text-sm text-slate-400 font-mono mt-0.5">High-demand flash event item • 100 Units Max Batch</p>
          </div>
        </div>

        <div className="flex items-center space-x-6 w-full sm:w-auto justify-between sm:justify-end">
          <div className="text-right">
            <p className="text-xs text-slate-400 font-mono">PRICE PER UNIT</p>
            <p className="text-2xl font-black text-white font-mono">₹{product?.price || 999}</p>
          </div>

          <button
            onClick={onOpenBuyModal}
            disabled={isOutOfStock}
            className={`px-6 py-3 rounded-xl font-bold font-mono text-sm shadow-xl flex items-center space-x-2 transition ${
              isOutOfStock
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                : 'bg-gradient-to-r from-cyan-400 to-cyan-500 hover:from-cyan-300 hover:to-cyan-400 text-slate-950 shadow-cyan-500/25 active:scale-95'
            }`}
          >
            <Zap className="w-4 h-4 fill-current" />
            <span>{isOutOfStock ? 'OUT OF STOCK' : 'BUY NOW'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
