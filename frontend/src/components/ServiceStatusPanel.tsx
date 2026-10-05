import React from 'react';
import { Server, Database, Activity, Cpu, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { SystemStatus } from '../types';

interface ServiceStatusPanelProps {
  status: SystemStatus | null;
}

export const ServiceStatusPanel: React.FC<ServiceStatusPanelProps> = ({ status }) => {
  const health = status?.system_health || {
    inventory_service: 'HEALTHY',
    order_service: 'HEALTHY',
    payment_service: 'HEALTHY',
    database: 'HEALTHY',
    payment_gateway: 'HEALTHY',
    kafka: 'HEALTHY',
    redis: 'HEALTHY',
  };

  const services = [
    { name: 'Inventory Service', state: health.inventory_service },
    { name: 'Order Service', state: health.order_service },
    { name: 'Payment Service', state: health.payment_service },
    { name: 'PostgreSQL DB', state: health.database },
    { name: 'Redis Gate', state: health.redis },
    { name: 'Mock Gateway', state: health.payment_gateway },
    { name: 'Kafka Event Bus', state: health.kafka },
  ];

  return (
    <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
      <div className="flex items-center space-x-2 border-b border-white/10 pb-4">
        <Server className="w-5 h-5 text-purple-400" />
        <h3 className="text-base font-bold text-white">Microservices &amp; Infrastructure Matrix</h3>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 font-mono text-xs">
        {services.map((svc, idx) => {
          const isUp = svc.state === 'HEALTHY';
          return (
            <div
              key={idx}
              className={`p-3 rounded-xl border flex flex-col justify-between space-y-2 ${
                isUp
                  ? 'bg-slate-900/80 border-slate-800 text-slate-200'
                  : 'bg-rose-950/40 border-rose-500/50 text-rose-300'
              }`}
            >
              <span className="text-[10px] text-slate-400 truncate">{svc.name}</span>
              <div className="flex items-center space-x-1.5 font-bold">
                <span className={`w-2 h-2 rounded-full ${isUp ? 'bg-emerald-400' : 'bg-rose-500 animate-pulse'}`}></span>
                <span className={isUp ? 'text-emerald-400' : 'text-rose-400 text-[10px]'}>
                  {svc.state}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
