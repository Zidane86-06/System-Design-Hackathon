import React from 'react';
import { Zap, ShieldCheck, Activity, Database, Server } from 'lucide-react';
import { SystemStatus } from '../types';

interface NavbarProps {
  status: SystemStatus | null;
}

export const Navbar: React.FC<NavbarProps> = ({ status }) => {
  const isHealthy = status ? !status.flags.db_down && !status.flags.order_service_outage : true;

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-white/10 px-6 py-4 mb-6">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-gradient-to-tr from-cyan-500 to-purple-600 rounded-xl text-slate-900 shadow-lg shadow-cyan-500/20">
            <Zap className="w-6 h-6 fill-current" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-extrabold tracking-wider text-white">SALESTORM</h1>
              <span className="text-[10px] uppercase tracking-widest font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 px-2 py-0.5 rounded-full">
                Jury Demo v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">High-Concurrency Inventory Reservation Engine</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="hidden sm:flex items-center space-x-3 text-xs font-mono">
            <div className="flex items-center space-x-1.5 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
              <Database className="w-3.5 h-3.5 text-purple-400" />
              <span className="text-slate-300">PostgreSQL</span>
            </div>
            <div className="flex items-center space-x-1.5 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
              <Server className="w-3.5 h-3.5 text-cyan-400" />
              <span className="text-slate-300">Redis Gate</span>
            </div>
          </div>

          <div className="flex items-center space-x-2 bg-slate-900/90 border border-slate-800 px-3 py-1.5 rounded-lg">
            <span className={`w-2.5 h-2.5 rounded-full ${isHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500 animate-ping'}`}></span>
            <span className="text-xs font-mono text-slate-200 font-medium">
              {isHealthy ? 'SYSTEM HEALTHY' : 'CHAOS SIMULATED'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
