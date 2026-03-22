'use client';

import { useMemo } from 'react';
import { DashboardData } from '@/lib/data-loader';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
  BarChart, Bar, Cell
} from 'recharts';

interface ModelComparisonViewProps {
  data: DashboardData;
}

const COLORS = [
  '#9CAF88', // sage
  '#C27A71', // terracotta
  '#7E91A3', // dustyblue
  '#D4A373', // muted gold
  '#A09D8B', // olive gray
  '#6D6875', // dark olive
  '#B5838D', // dusty rose
  '#E5989B', // soft pink
];

const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: Record<string, unknown> }> }) => {
  if (active && payload && payload.length) {
    const d = payload[0].payload as { model: string; ac: number; ct: number; cap: number; gap: number; ni: number; refusalRate: number };
    return (
      <div className="bg-paper border border-faint p-3 shadow-lg font-mono text-sm text-ink">
        <p className="font-bold mb-1">{d.model}</p>
        <div className="grid grid-cols-2 gap-x-4">
          <span>AC:</span> <span className="text-right">{d.ac.toFixed(3)}</span>
          <span>CT:</span> <span className="text-right">{d.ct.toFixed(3)}</span>
          <span>Capability:</span> <span className="text-right font-bold">{d.cap.toFixed(3)}</span>
          <span>Gap:</span> <span className="text-right">{d.gap.toFixed(3)}</span>
          <span>NI:</span> <span className="text-right">{d.ni.toFixed(3)}</span>
          <span>Refusals:</span> <span className="text-right text-red-600 font-semibold">{(d.refusalRate * 100).toFixed(1)}%</span>
        </div>
      </div>
    );
  }
  return null;
};

export default function ModelComparisonView({ data }: ModelComparisonViewProps) {
  const modelStats = useMemo(() => {
    if (!data.runs.length) return [];
    
    return data.runs.map((run, idx) => {
      const modelTasks = data.tasks.filter(t => t.run_id === run.run_id);
      const avgNi = modelTasks.length ? modelTasks.reduce((acc, t) => acc + t.ni, 0) / modelTasks.length : 0;
      
      const refusals = modelTasks.filter(t => t.refusal).length;
      const refusalRate = modelTasks.length ? refusals / modelTasks.length : 0;

      const forkItems = data.items.filter(i => i.run_id === run.run_id && i.dimension === 'fork');
      const totalFork = forkItems.length;
      const asked = forkItems.filter(i => i.execution_score === 1.0).length;
      const wasteful = forkItems.filter(i => i.execution_score === 0.5).length;
      const steamrolled = forkItems.filter(i => i.execution_score === 0.0).length;

      return {
        model: run.model,
        ac: run.composite_ac,
        ct: run.composite_ct,
        gap: run.composite_ct - run.composite_ac,
        cap: run.composite_ct > 0 ? run.composite_ac / run.composite_ct : 0,
        ni: avgNi,
        refusalRate,
        forkAskedPct: totalFork ? (asked / totalFork) * 100 : 0,
        forkWastefulPct: totalFork ? (wasteful / totalFork) * 100 : 0,
        forkSteamrollPct: totalFork ? (steamrolled / totalFork) * 100 : 0,
        color: COLORS[idx % COLORS.length]
      };
    }).sort((a, b) => a.gap - b.gap);
  }, [data]);

  const capRankedStats = useMemo(() => {
    return [...modelStats].sort((a, b) => b.cap - a.cap);
  }, [modelStats]);

  if (!modelStats.length) {
    return <div className="p-8 text-ink-light font-serif">No data to compare.</div>;
  }

  const medCt = modelStats.reduce((acc, m) => acc + m.ct, 0) / modelStats.length;
  const medNi = modelStats.reduce((acc, m) => acc + m.ni, 0) / modelStats.length;
  const medCap = modelStats.reduce((acc, m) => acc + m.cap, 0) / modelStats.length;

  return (
    <div className="flex flex-col gap-10">
      <div>
        <h2 className="font-serif text-2xl font-semibold mb-2">Model Comparison</h2>
        <p className="text-sm text-ink-light mb-6">Analyzing capability, thoroughness, and noise efficiency.</p>
        
        {/* Persistent Model Legend */}
        <div className="flex flex-wrap gap-x-6 gap-y-3 p-4 border border-faint bg-white mb-8">
          <span className="text-[10px] uppercase tracking-widest text-ink-light font-bold w-full mb-1">Model Legend</span>
          {modelStats.map((m) => (
            <div key={m.model} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: m.color }} />
              <span className="font-mono text-xs font-semibold">{m.model}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* AC vs CT Scatter */}
        <div className="border border-faint bg-white p-6">
          <h3 className="font-serif text-lg font-semibold mb-1">Capability Profile (AC vs CT)</h3>
          <p className="text-xs text-ink-light mb-6">On diagonal = all controls pass. Above = capability gaps inflate CT.</p>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E2DA" />
                <XAxis type="number" dataKey="ac" name="AC" domain={[0, 1]} label={{ value: 'Absolute Coverage (AC)', position: 'insideBottom', offset: -10, className: 'text-xs fill-ink-light' }} />
                <YAxis type="number" dataKey="ct" name="CT" domain={[0, 1]} label={{ value: 'Conditional Thoroughness (CT)', angle: -90, position: 'insideLeft', className: 'text-xs fill-ink-light' }} />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} content={<CustomTooltip />} />
                <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="#4A4A4A" strokeDasharray="3 3" />
                <Scatter name="Models" data={modelStats}>
                  {modelStats.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* AC vs Capability Scatter */}
        <div className="border border-faint bg-white p-6">
          <h3 className="font-serif text-lg font-semibold mb-1">Complex Score vs Base Capability</h3>
          <p className="text-xs text-ink-light mb-6">Score on full task (AC) vs score on isolated control (AC/CT).</p>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E2DA" />
                <XAxis type="number" dataKey="cap" name="Capability" domain={[0, 1]} label={{ value: 'Base Capability (AC/CT)', position: 'insideBottom', offset: -10, className: 'text-xs fill-ink-light' }} />
                <YAxis type="number" dataKey="ac" name="AC" domain={[0, 1]} label={{ value: 'Absolute Coverage (AC)', angle: -90, position: 'insideLeft', className: 'text-xs fill-ink-light' }} />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} content={<CustomTooltip />} />
                <ReferenceLine x={medCap} stroke="#4A4A4A" strokeDasharray="3 3" />
                <Scatter name="Models" data={modelStats}>
                  {modelStats.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* CT vs NI Quadrant */}
        <div className="border border-faint bg-white p-6">
          <div className="flex justify-between items-baseline mb-1">
            <h3 className="font-serif text-lg font-semibold">Thoroughness Quality (CT vs NI)</h3>
          </div>
          <p className="text-xs text-ink-light mb-6 flex justify-between">
            <span>Left: Quiet, Right: Noisy</span>
            <span>Top: Thorough, Bottom: Lazy</span>
          </p>
          <div className="h-80 w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E2DA" />
                <XAxis type="number" dataKey="ni" name="NI" label={{ value: 'Average Noise Index (NI)', position: 'insideBottom', offset: -10, className: 'text-xs fill-ink-light' }} />
                <YAxis type="number" dataKey="ct" name="CT" domain={[0, 1]} label={{ value: 'Conditional Thoroughness (CT)', angle: -90, position: 'insideLeft', className: 'text-xs fill-ink-light' }} />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} content={<CustomTooltip />} />
                <ReferenceLine x={medNi} stroke="#4A4A4A" strokeDasharray="3 3" />
                <ReferenceLine y={medCt} stroke="#4A4A4A" strokeDasharray="3 3" />
                <Scatter name="Models" data={modelStats}>
                  {modelStats.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Gap Bars */}
        <div className="border border-faint bg-white p-6">
          <h3 className="font-serif text-lg font-semibold mb-1">Thoroughness Gap (CT − AC)</h3>
          <p className="text-xs text-ink-light mb-6">Positive gap means the model has unrealized capability.</p>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={modelStats} margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E2DA" horizontal={false} />
                <XAxis type="number" label={{ value: 'Gap', position: 'insideBottom', offset: -5, className: 'text-xs fill-ink-light' }} />
                <YAxis type="category" dataKey="model" width={150} tick={{ fontSize: 10, fill: '#111111', fontFamily: 'var(--font-mono)' }} />
                <Tooltip content={<CustomTooltip />} cursor={{fill: '#F5F5F5'}} />
                <ReferenceLine x={0} stroke="#4A4A4A" strokeDasharray="3 3" />
                <Bar dataKey="gap" barSize={16}>
                  {modelStats.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Capability Bars */}
        <div className="border border-faint bg-white p-6 lg:col-span-2">
          <h3 className="font-serif text-lg font-semibold mb-1">Base Capability Ranking (AC / CT)</h3>
          <p className="text-xs text-ink-light mb-6">Percentage of concepts successfully handled in isolation (control tests).</p>
          <div className="h-[400px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={capRankedStats} margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E2DA" horizontal={false} />
                <XAxis type="number" domain={[0, 1]} label={{ value: 'Capability Score', position: 'insideBottom', offset: -5, className: 'text-xs fill-ink-light' }} />
                <YAxis type="category" dataKey="model" width={150} tick={{ fontSize: 12, fill: '#111111', fontFamily: 'var(--font-mono)' }} />
                <Tooltip content={<CustomTooltip />} cursor={{fill: '#F5F5F5'}} />
                <Bar dataKey="cap" barSize={24}>
                  {capRankedStats.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Strategy Bias Profile (Steamrolling) */}
        <div className="border border-faint bg-white p-6 lg:col-span-2">
          <h3 className="font-serif text-lg font-semibold mb-1">Strategy Bias Profile: Disambiguation</h3>
          <p className="text-xs text-ink-light mb-6">How models handle ambiguous (Fork) prompts: Asking vs Steamrolling (making silent assumptions).</p>
          <div className="h-[400px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={modelStats} margin={{ top: 5, right: 30, left: 100, bottom: 5 }} stackOffset="expand">
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E2DA" horizontal={false} />
                <XAxis type="number" tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} label={{ value: 'Percentage of Fork Items', position: 'insideBottom', offset: -5, className: 'text-xs fill-ink-light' }} />
                <YAxis type="category" dataKey="model" width={150} tick={{ fontSize: 12, fill: '#111111', fontFamily: 'var(--font-mono)' }} />
                <Tooltip 
                  cursor={{fill: '#F5F5F5'}}
                  formatter={(value: unknown, name: unknown) => {
                    const num = typeof value === 'number' ? value : parseFloat(String(value)) || 0;
                    return [`${num.toFixed(1)}%`, String(name)];
                  }}
                />
                <Bar dataKey="forkAskedPct" name="Asked (Safe)" stackId="a" fill="#22c55e" barSize={24} />
                <Bar dataKey="forkWastefulPct" name="Wasteful Friction" stackId="a" fill="#f59e0b" />
                <Bar dataKey="forkSteamrollPct" name="Steamrolled (Assumption)" stackId="a" fill="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
