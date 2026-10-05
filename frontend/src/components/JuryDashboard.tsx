import React, { useState } from 'react';
import { ShieldCheck, Flame, RefreshCw, AlertTriangle, Cpu, Play, FastForward, CheckCircle2, XCircle } from 'lucide-react';
import { SystemStatus } from '../types';
import {
  triggerLoadTest,
  runScenario,
  triggerOrderOutage,
  triggerDatabaseFailure,
  triggerPaymentGatewayFailure
} from '../services/api';

interface JuryDashboardProps {
  status: SystemStatus | null;
  onRefresh: () => void;
  onSelectOrder: (orderId: string) => void;
}

export const JuryDashboard: React.FC<JuryDashboardProps> = ({ status, onRefresh, onSelectOrder }) => {
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [actionOutput, setActionOutput] = useState<any | null>(null);

  const inv = status?.inventory || {
    total_units: 100,
    available_units: 100,
    reserved_units: 0,
    successful_sales: 0,
    cancelled_orders: 0,
    oversold_units: 0,
  };

  const loadProgress = status?.load_test_progress;

  const handleAction = async (name: string, fn: () => Promise<any>) => {
    setLoadingAction(name);
    try {
      const res = await fn();
      setActionOutput({ action: name, res });
      onRefresh();
    } catch (err: any) {
      setActionOutput({ action: name, error: err.message });
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* SECTION 31 — JURY DEMO HERO BANNER */}
      <div className="glass-panel p-6 rounded-2xl border border-cyan-500/30 relative overflow-hidden bg-gradient-to-r from-cyan-950/40 via-slate-900 to-purple-950/40">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <ShieldCheck className="w-64 h-64 text-cyan-400" />
        </div>

        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="inline-flex items-center space-x-2 bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-mono px-3 py-1 rounded-full mb-3">
              <Flame className="w-3.5 h-3.5 text-cyan-400" />
              <span>HACKATHON VERIFICATION CORE</span>
            </div>
            <h2 className="text-3xl font-black tracking-tight text-white">
              SALESTORM <span className="text-gradient">— Jury Demo</span>
            </h2>
            <p className="text-slate-300 text-sm mt-1 max-w-xl">
              High-concurrency inventory guarantee engine. Atomically handles 10,000 purchase attempts against 100 stock units using Redis Gate + PostgreSQL conditional SQL updates.
            </p>
          </div>

          <div className="flex items-center gap-4 bg-slate-900/90 border border-slate-700/80 p-4 rounded-xl shadow-2xl">
            <div className="text-center px-4 border-r border-slate-700">
              <p className="text-xs font-mono text-slate-400">CONCURRENT USERS</p>
              <p className="text-2xl font-black text-cyan-400 font-mono">10,000</p>
            </div>
            <div className="text-center px-4 border-r border-slate-700">
              <p className="text-xs font-mono text-slate-400">AVAILABLE UNITS</p>
              <p className="text-2xl font-black text-purple-400 font-mono">100</p>
            </div>
            <div className="text-center px-4">
              <p className="text-xs font-mono text-slate-400">OVERSELLING</p>
              <p className={`text-2xl font-black font-mono ${inv.oversold_units === 0 ? 'text-emerald-400' : 'text-rose-500'}`}>
                {inv.oversold_units}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* KPI METRICS GRID */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card p-4 rounded-xl border border-white/5">
          <p className="text-xs text-slate-400 font-mono">Available Stock</p>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-3xl font-extrabold text-cyan-400 font-mono">{inv.available_units}</span>
            <span className="text-xs text-slate-500 font-mono">/ {inv.total_units}</span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
            <div 
              className="bg-cyan-400 h-full transition-all duration-300"
              style={{ width: `${(inv.available_units / inv.total_units) * 100}%` }}
            ></div>
          </div>
        </div>

        <div className="glass-card p-4 rounded-xl border border-white/5">
          <p className="text-xs text-slate-400 font-mono">Reserved Units</p>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-3xl font-extrabold text-purple-400 font-mono">{inv.reserved_units}</span>
            <span className="text-xs text-slate-500 font-mono">ACTIVE TTL</span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
            <div 
              className="bg-purple-400 h-full transition-all duration-300"
              style={{ width: `${(inv.reserved_units / inv.total_units) * 100}%` }}
            ></div>
          </div>
        </div>

        <div className="glass-card p-4 rounded-xl border border-white/5">
          <p className="text-xs text-slate-400 font-mono">Successful Sales</p>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-3xl font-extrabold text-emerald-400 font-mono">{inv.successful_sales}</span>
            <span className="text-xs text-emerald-500/80 font-mono">MAX 100</span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
            <div 
              className="bg-emerald-400 h-full transition-all duration-300"
              style={{ width: `${(inv.successful_sales / inv.total_units) * 100}%` }}
            ></div>
          </div>
        </div>

        <div className="glass-card p-4 rounded-xl border border-white/5">
          <p className="text-xs text-slate-400 font-mono">Oversold Count</p>
          <div className="flex items-baseline justify-between mt-1">
            <span className={`text-3xl font-extrabold font-mono ${inv.oversold_units === 0 ? 'text-slate-300' : 'text-rose-500'}`}>
              {inv.oversold_units}
            </span>
            <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${inv.oversold_units === 0 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}`}>
              {inv.oversold_units === 0 ? 'PASSED' : 'FAILED'}
            </span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
            <div className={`h-full ${inv.oversold_units === 0 ? 'bg-emerald-400' : 'bg-rose-500'}`} style={{ width: '100%' }}></div>
          </div>
        </div>
      </div>

      {/* SECTION 18 & 31 — ONE-CLICK SCENARIOS BOARD */}
      <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-cyan-400" />
            <h3 className="text-lg font-bold text-white">One-Click Demonstration Scenarios</h3>
          </div>
          <button
            onClick={() => handleAction('reset-inventory', () => runScenario('reset-inventory'))}
            className="flex items-center space-x-1.5 text-xs font-mono text-cyan-400 hover:text-cyan-300 bg-cyan-950/60 border border-cyan-800 px-3 py-1.5 rounded-lg transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset Stock to 100</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Scenario 1 */}
          <button
            onClick={() => handleAction('Successful Purchase', () => runScenario('successful-purchase'))}
            disabled={loadingAction !== null}
            className="flex flex-col justify-between p-4 bg-slate-800/60 hover:bg-slate-800 border border-slate-700/70 hover:border-cyan-500/50 rounded-xl transition text-left group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono text-cyan-400 font-bold">SCENARIO 1</span>
              <Play className="w-4 h-4 text-slate-400 group-hover:text-cyan-400" />
            </div>
            <h4 className="font-bold text-white text-sm">Run Successful Purchase</h4>
            <p className="text-xs text-slate-400 mt-1">Reserve -&gt; Order -&gt; Payment -&gt; Confirmed</p>
          </button>

          {/* Scenario 2 */}
          <button
            onClick={() => handleAction('Payment Failure', () => runScenario('payment-failure'))}
            disabled={loadingAction !== null}
            className="flex flex-col justify-between p-4 bg-slate-800/60 hover:bg-slate-800 border border-slate-700/70 hover:border-amber-500/50 rounded-xl transition text-left group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono text-amber-400 font-bold">SCENARIO 2</span>
              <AlertTriangle className="w-4 h-4 text-slate-400 group-hover:text-amber-400" />
            </div>
            <h4 className="font-bold text-white text-sm">Simulate Payment Failure</h4>
            <p className="text-xs text-slate-400 mt-1">Triggers Saga Compensation &amp; Stock Release</p>
          </button>

          {/* Scenario 3 */}
          <button
            onClick={() => handleAction('Duplicate Buy', () => runScenario('duplicate-buy'))}
            disabled={loadingAction !== null}
            className="flex flex-col justify-between p-4 bg-slate-800/60 hover:bg-slate-800 border border-slate-700/70 hover:border-purple-500/50 rounded-xl transition text-left group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono text-purple-400 font-bold">SCENARIO 3</span>
              <RefreshCw className="w-4 h-4 text-slate-400 group-hover:text-purple-400" />
            </div>
            <h4 className="font-bold text-white text-sm">Test Idempotency</h4>
            <p className="text-xs text-slate-400 mt-1">Submits duplicate key; verifies 1 order created</p>
          </button>

          {/* Scenario 4 */}
          <button
            onClick={() => handleAction('30s Order Outage', () => triggerOrderOutage(30))}
            disabled={loadingAction !== null}
            className="flex flex-col justify-between p-4 bg-slate-800/60 hover:bg-slate-800 border border-slate-700/70 hover:border-rose-500/50 rounded-xl transition text-left group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono text-rose-400 font-bold">SCENARIO 4</span>
              <AlertTriangle className="w-4 h-4 text-slate-400 group-hover:text-rose-400" />
            </div>
            <h4 className="font-bold text-white text-sm">30s Order Service Outage</h4>
            <p className="text-xs text-slate-400 mt-1">Outbox pattern preserves state; auto-recovers</p>
          </button>

          {/* Scenario 6 - 10,000 Request Test */}
          <button
            onClick={() => handleAction('10,000 Request Test', () => triggerLoadTest(10000, 200))}
            disabled={loadingAction !== null}
            className="flex flex-col justify-between p-4 bg-gradient-to-tr from-cyan-950 to-purple-950 hover:from-cyan-900 hover:to-purple-900 border border-cyan-500/40 rounded-xl transition text-left group col-span-1 md:col-span-2 shadow-lg"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono text-cyan-300 font-bold flex items-center gap-1">
                <FastForward className="w-3.5 h-3.5 text-cyan-400" /> SCENARIO 6 — PROOF BENCHMARK
              </span>
              <span className="text-[10px] font-mono bg-cyan-400 text-slate-900 px-2 py-0.5 rounded font-bold">HIGH CONCURRENCY</span>
            </div>
            <h4 className="font-extrabold text-white text-base">Run 10,000 Request Test</h4>
            <p className="text-xs text-cyan-200/80 mt-1">
              Simulate 10,000 concurrent purchase attempts against 100 units. Verifies 0 overselling guarantee.
            </p>
          </button>

          {/* Scenario 7 */}
          <button
            onClick={() => handleAction('50x Traffic Scaling', () => triggerLoadTest(5000, 500))}
            disabled={loadingAction !== null}
            className="flex flex-col justify-between p-4 bg-slate-800/60 hover:bg-slate-800 border border-slate-700/70 hover:border-cyan-500/50 rounded-xl transition text-left group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono text-cyan-400 font-bold">SCENARIO 7</span>
              <Cpu className="w-4 h-4 text-slate-400 group-hover:text-cyan-400" />
            </div>
            <h4 className="font-bold text-white text-sm">Simulate 50x Traffic</h4>
            <p className="text-xs text-slate-400 mt-1">Tests worker pool auto-scaling &amp; Redis gate speed</p>
          </button>

          {/* Scenario 8 */}
          <button
            onClick={() => handleAction('Database Failure', () => triggerDatabaseFailure(5))}
            disabled={loadingAction !== null}
            className="flex flex-col justify-between p-4 bg-slate-800/60 hover:bg-slate-800 border border-slate-700/70 hover:border-amber-500/50 rounded-xl transition text-left group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono text-amber-400 font-bold">SCENARIO 8</span>
              <AlertTriangle className="w-4 h-4 text-slate-400 group-hover:text-amber-400" />
            </div>
            <h4 className="font-bold text-white text-sm">Database Failure</h4>
            <p className="text-xs text-slate-400 mt-1">Simulates 5s database outage; zero data corruption</p>
          </button>

          {/* Scenario 9 */}
          <button
            onClick={() => handleAction('Payment Gateway Failure', () => triggerPaymentGatewayFailure(10))}
            disabled={loadingAction !== null}
            className="flex flex-col justify-between p-4 bg-slate-800/60 hover:bg-slate-800 border border-slate-700/70 hover:border-rose-500/50 rounded-xl transition text-left group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono text-rose-400 font-bold">SCENARIO 9</span>
              <AlertTriangle className="w-4 h-4 text-slate-400 group-hover:text-rose-400" />
            </div>
            <h4 className="font-bold text-white text-sm">Gateway Failure</h4>
            <p className="text-xs text-slate-400 mt-1">Fails gracefully; releases inventory stock safely</p>
          </button>
        </div>
      </div>

      {/* REAL-TIME LOAD TEST MONITORING PROGRESS CARD */}
      {loadProgress && loadProgress.status !== 'IDLE' && (
        <div className="glass-panel p-6 rounded-2xl border border-cyan-500/40 bg-slate-900/90 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Flame className="w-5 h-5 text-cyan-400 animate-bounce" />
              <h3 className="text-lg font-bold text-white">10,000 Request Load Test Execution</h3>
            </div>
            <span className={`text-xs font-mono font-bold px-3 py-1 rounded-full ${loadProgress.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-cyan-500/20 text-cyan-300 animate-pulse'}`}>
              STATUS: {loadProgress.status}
            </span>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-xs font-mono text-slate-300">
              <span>Completed: {loadProgress.completed_requests} / {loadProgress.total_requests}</span>
              <span>{Math.round((loadProgress.completed_requests / loadProgress.total_requests) * 100)}%</span>
            </div>
            <div className="w-full bg-slate-800 h-3 rounded-full overflow-hidden p-0.5 border border-slate-700">
              <div 
                className="bg-gradient-to-r from-cyan-400 to-purple-500 h-full rounded-full transition-all duration-200"
                style={{ width: `${(loadProgress.completed_requests / loadProgress.total_requests) * 100}%` }}
              ></div>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 pt-2 text-center font-mono">
            <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700">
              <p className="text-[10px] text-slate-400">SUCCESS PURCHASES</p>
              <p className="text-xl font-bold text-emerald-400">{loadProgress.successful_purchases}</p>
            </div>
            <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700">
              <p className="text-[10px] text-slate-400">REJECTED (OUT OF STOCK)</p>
              <p className="text-xl font-bold text-amber-400">{loadProgress.rejected_out_of_stock}</p>
            </div>
            <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700">
              <p className="text-[10px] text-slate-400">OVERSOLD UNITS</p>
              <p className={`text-xl font-bold ${loadProgress.oversold_units === 0 ? 'text-emerald-400' : 'text-rose-500'}`}>
                {loadProgress.oversold_units}
              </p>
            </div>
            <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700">
              <p className="text-[10px] text-slate-400">THROUGHPUT (RPS)</p>
              <p className="text-xl font-bold text-cyan-400">{loadProgress.rps}</p>
            </div>
            <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700">
              <p className="text-[10px] text-slate-400">RESULT GUARANTEE</p>
              <p className="text-xs font-bold text-emerald-300 mt-1">{loadProgress.result_status}</p>
            </div>
          </div>
        </div>
      )}

      {/* ACTION RESULT FEEDBACK POPUP */}
      {actionOutput && (
        <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl font-mono text-xs text-slate-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-cyan-400 font-bold">ACTION RESULT: {actionOutput.action}</span>
            <button onClick={() => setActionOutput(null)} className="text-slate-400 hover:text-white">✕</button>
          </div>
          <pre className="bg-slate-950 p-3 rounded border border-slate-800 overflow-x-auto text-emerald-400">
            {JSON.stringify(actionOutput.res || actionOutput.error, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
