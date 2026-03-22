'use client';

import { useMemo } from 'react';
import { DashboardData } from '@/lib/data-loader';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';

interface DimensionAnalysisViewProps {
  data: DashboardData;
}

export default function DimensionAnalysisView({ data }: DimensionAnalysisViewProps) {
  const models = useMemo(() => Array.from(new Set(data.runs.map(r => r.model))).sort(), [data.runs]);

  // Fork Execution Score Data
  const forkExecutionData = useMemo(() => {
    return models.map(model => {
      const forkItems = data.items.filter(i => i.model === model && i.dimension === 'fork');
      if (!forkItems.length) return { model, '1.0 (Visible)': 0, '0.5 (Wasteful)': 0, '0.0 (Silent)': 0 };
      
      const v1 = forkItems.filter(i => i.execution_score === 1.0).length;
      const v05 = forkItems.filter(i => i.execution_score === 0.5).length;
      const v0 = forkItems.filter(i => i.execution_score === 0.0).length;
      const total = forkItems.length;

      return {
        model,
        '1.0 (Visible)': v1 / total,
        '0.5 (Wasteful)': v05 / total,
        '0.0 (Silent)': v0 / total,
      };
    });
  }, [data.items, models]);

  // Fork Blocking Data
  const forkBlockingData = useMemo(() => {
    return models.map(model => {
      const forkItems = data.items.filter(i => i.model === model && i.dimension === 'fork');
      const blocking = forkItems.filter(i => i.blocking === true);
      const nonBlocking = forkItems.filter(i => i.blocking === false);
      
      const blockingAvg = blocking.length ? blocking.reduce((a, i) => a + (i.execution_score || 0), 0) / blocking.length : 0;
      const nonBlockingAvg = nonBlocking.length ? nonBlocking.reduce((a, i) => a + (i.execution_score || 0), 0) / nonBlocking.length : 0;

      return {
        model,
        Blocking: blockingAvg,
        'Non-Blocking': nonBlockingAvg,
      };
    });
  }, [data.items, models]);

  // Guardian Severity Data
  const guardianSeverityData = useMemo(() => {
    return models.map(model => {
      const guardianItems = data.items.filter(i => i.model === model && i.dimension === 'guardian');
      const getRate = (sev: string) => {
        const items = guardianItems.filter(i => i.severity === sev);
        if (!items.length) return 0;
        return items.filter(i => i.credit > 0).length / items.length;
      };

      return {
        model,
        Critical: getRate('critical'),
        Important: getRate('important'),
        Optional: getRate('optional'),
      };
    });
  }, [data.items, models]);

  // Guardian Heatmap
  const { flagIds, guardianHeatmap } = useMemo(() => {
    const guardianItems = data.items.filter(i => i.dimension === 'guardian');
    const flags = Array.from(new Set(guardianItems.map(i => i.item_id))).sort();
    
    const map: Record<string, Record<string, number>> = {};
    for (const flag of flags) {
      map[flag] = {};
      for (const m of models) {
        const item = guardianItems.find(i => i.item_id === flag && i.model === m);
        map[flag][m] = item && item.credit > 0 ? 1 : 0;
      }
    }
    return { flagIds: flags, guardianHeatmap: map };
  }, [data.items, models]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-paper border border-faint p-3 font-mono text-xs shadow-lg">
          <p className="font-bold text-ink mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {(entry.value * 100).toFixed(1)}%
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="flex flex-col gap-12">
      <div>
        <h2 className="font-serif text-2xl font-semibold mb-2">Dimension Analysis</h2>
        <p className="text-sm text-ink-light">Detailed breakdown of Fork (Ambiguity) and Guardian (Risk) dimensions.</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {/* Fork Execution */}
        <div className="border border-faint bg-white p-6">
          <h3 className="font-serif text-lg font-semibold mb-1">Fork: Execution Score Distribution</h3>
          <p className="text-xs text-ink-light mb-6">1.0 = Visible, 0.5 = Wasteful, 0.0 = Silent Assumption.</p>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={forkExecutionData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E2DA" vertical={false} />
                <XAxis dataKey="model" tick={{ fontSize: 11, fontFamily: 'var(--font-mono)' }} interval={0} angle={-30} textAnchor="end" height={60} />
                <YAxis tickFormatter={(val) => `${(val * 100).toFixed(0)}%`} tick={{ fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', fontFamily: 'var(--font-mono)' }} />
                <Bar dataKey="0.0 (Silent)" stackId="a" fill="#C27A71" />
                <Bar dataKey="0.5 (Wasteful)" stackId="a" fill="#D4A373" />
                <Bar dataKey="1.0 (Visible)" stackId="a" fill="#9CAF88" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Fork Blocking vs Non-Blocking */}
        <div className="border border-faint bg-white p-6">
          <h3 className="font-serif text-lg font-semibold mb-1">Fork: Blocking vs Non-Blocking</h3>
          <p className="text-xs text-ink-light mb-6">Average execution score.</p>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={forkBlockingData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E2DA" vertical={false} />
                <XAxis dataKey="model" tick={{ fontSize: 11, fontFamily: 'var(--font-mono)' }} interval={0} angle={-30} textAnchor="end" height={60} />
                <YAxis tick={{ fontSize: 11 }} domain={[0, 1]} />
                <Tooltip content={<CustomTooltip />} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', fontFamily: 'var(--font-mono)' }} />
                <Bar dataKey="Blocking" fill="#C27A71" />
                <Bar dataKey="Non-Blocking" fill="#7E91A3" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Guardian Severity */}
        <div className="border border-faint bg-white p-6">
          <h3 className="font-serif text-lg font-semibold mb-1">Guardian: Detection Rate by Severity</h3>
          <p className="text-xs text-ink-light mb-6">Proportion of risks successfully identified per severity.</p>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={guardianSeverityData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E2DA" vertical={false} />
                <XAxis dataKey="model" tick={{ fontSize: 11, fontFamily: 'var(--font-mono)' }} interval={0} angle={-30} textAnchor="end" height={60} />
                <YAxis tickFormatter={(val) => `${(val * 100).toFixed(0)}%`} tick={{ fontSize: 11 }} domain={[0, 1]} />
                <Tooltip content={<CustomTooltip />} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', fontFamily: 'var(--font-mono)' }} />
                <Bar dataKey="Critical" fill="#C27A71" />
                <Bar dataKey="Important" fill="#D4A373" />
                <Bar dataKey="Optional" fill="#A09D8B" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Guardian Heatmap */}
        <div className="border border-faint bg-white p-6 overflow-x-auto">
          <h3 className="font-serif text-lg font-semibold mb-4">Guardian: Per-Flag Detection</h3>
          <div className="inline-block min-w-full">
            <div className="flex">
              <div className="w-32 shrink-0" />
              {models.map(m => (
                <div key={m} className="w-12 px-1 text-[10px] font-semibold text-center truncate -rotate-45 origin-bottom-left pb-2" title={m}>
                  {m}
                </div>
              ))}
            </div>
            {flagIds.map(flag => (
              <div key={flag} className="flex border-t border-faint/50 hover:bg-faint/20">
                <div className="w-32 pr-2 py-1 text-[10px] truncate leading-tight flex items-center" title={flag}>
                  {flag.replace('guardian_', '')}
                </div>
                {models.map(m => {
                  const detected = guardianHeatmap[flag]?.[m];
                  return (
                    <div 
                      key={m} 
                      className="w-12 flex items-center justify-center border-l border-faint/50"
                    >
                      <div className={`w-full h-full p-1 border-2 border-white ${detected ? 'bg-sage' : 'bg-terracotta/80'}`} />
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
