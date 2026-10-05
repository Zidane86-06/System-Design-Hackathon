import React from 'react';
import { Terminal, Activity, Zap } from 'lucide-react';
import { OutboxEvent } from '../types';

interface EventLogViewerProps {
  events: OutboxEvent[];
}

export const EventLogViewer: React.FC<EventLogViewerProps> = ({ events }) => {
  return (
    <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div className="flex items-center space-x-2">
          <Terminal className="w-5 h-5 text-cyan-400" />
          <h3 className="text-base font-bold text-white">Outbox Pattern &amp; Kafka Event Stream</h3>
        </div>
        <span className="text-xs font-mono text-slate-400">{events.length} Recent Events</span>
      </div>

      <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 h-64 overflow-y-auto font-mono text-xs space-y-2 custom-scrollbar">
        {events.length === 0 ? (
          <div className="text-center text-slate-600 py-12">
            No outbox events generated yet. Trigger a scenario or buy request to view transactional messages.
          </div>
        ) : (
          events.map((evt, idx) => {
            const isSuccess = evt.event_type.includes('Success') || evt.event_type.includes('Confirmed') || evt.event_type.includes('Created');
            const isFailure = evt.event_type.includes('Failed') || evt.event_type.includes('Cancelled') || evt.event_type.includes('Expired');

            return (
              <div key={idx} className="p-2.5 bg-slate-900/90 rounded border border-slate-800/80 flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] text-slate-500">[{new Date(evt.timestamp).toLocaleTimeString()}]</span>
                    <span className={`font-bold px-1.5 py-0.5 rounded text-[10px] ${
                      isSuccess ? 'bg-emerald-500/20 text-emerald-300' : isFailure ? 'bg-rose-500/20 text-rose-300' : 'bg-cyan-500/20 text-cyan-300'
                    }`}>
                      {evt.event_type}
                    </span>
                    <span className="text-slate-400">AggID: {evt.aggregate_id.substring(0, 8)}...</span>
                  </div>
                  <pre className="text-[11px] text-slate-300 overflow-x-auto">
                    {JSON.stringify(evt.payload, null, 2)}
                  </pre>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
