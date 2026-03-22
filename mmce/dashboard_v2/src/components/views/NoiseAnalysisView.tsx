'use client';

import { useMemo, useState } from 'react';
import { DashboardData, NoiseRow } from '@/lib/data-loader';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import DataTable, { Column } from '../ui/DataTable';

interface NoiseAnalysisViewProps {
  data: DashboardData;
}

const NOISE_COLORS: Record<string, string> = {
  "false_uncertainty": "#C27A71", // terracotta
  "performative_hedging": "#D4A373", // muted gold
  "unnecessary_clarification": "#7E91A3", // dusty blue
  "hallucinated_risk": "#6D6875", // dark olive
  "redundant_restatement": "#A09D8B", // olive gray
  "audit_theater": "#B5838D", // dusty rose
};

const ALL_CLASSES = Object.keys(NOISE_COLORS);

export default function NoiseAnalysisView({ data }: NoiseAnalysisViewProps) {
  const [modelFilter, setModelFilter] = useState<string>('All');
  const [classFilter, setClassFilter] = useState<string>('All');

  const models = useMemo(() => Array.from(new Set(data.runs.map(r => r.model))).sort(), [data.runs]);

  // Breakdown Data
  const noiseBreakdownData = useMemo(() => {
    return models.map(model => {
      const modelNoise = data.noise.filter(n => n.model === model);
      const row: any = { model };
      
      for (const cls of ALL_CLASSES) {
        row[cls] = modelNoise.filter(n => n.noise_class === cls).reduce((sum, n) => sum + n.weight, 0);
      }
      return row;
    });
  }, [data.noise, models]);

  // Filtered Table Data
  const tableData = useMemo(() => {
    return data.noise.filter(n => {
      const matchModel = modelFilter === 'All' || n.model === modelFilter;
      const matchClass = classFilter === 'All' || n.noise_class === classFilter;
      return matchModel && matchClass;
    });
  }, [data.noise, modelFilter, classFilter]);

  const noiseColumns: Column<NoiseRow>[] = [
    { key: 'model', label: 'Model', className: 'align-top w-32' },
    { key: 'task_id', label: 'Task', className: 'align-top w-48 truncate max-w-[12rem]' },
    { 
      key: 'noise_class', 
      label: 'Class', 
      className: 'align-top w-40',
      render: (r) => (
        <span style={{ color: NOISE_COLORS[r.noise_class] }}>
          {r.noise_class.replace(/_/g, ' ')}
        </span>
      )
    },
    { key: 'weight', label: 'Weight', className: 'align-top text-right w-16' },
    { 
      key: 'description', 
      label: 'Description', 
      className: 'text-ink-light break-words leading-relaxed whitespace-normal',
      sortable: false 
    },
  ];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-paper border border-faint p-3 font-mono text-xs shadow-lg">
          <p className="font-bold text-ink mb-2">{label}</p>
          {payload.map((entry: any, index: number) => {
            if (entry.value > 0) {
              return (
                <p key={index} style={{ color: entry.color }}>
                  {entry.name.replace(/_/g, ' ')}: {entry.value.toFixed(1)}
                </p>
              );
            }
            return null;
          })}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="flex flex-col gap-12">
      <div>
        <h2 className="font-serif text-2xl font-semibold mb-2">Noise Analysis</h2>
        <p className="text-sm text-ink-light">
          Noise penalizes false, alarmist, or irrelevant warnings. Lower is better. 
          Six classes: false uncertainty, performative hedging, unnecessary clarification, 
          hallucinated risk, redundant restatement, audit theater.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8">
        {/* Noise Breakdown Chart */}
        <div className="border border-faint bg-white p-6">
          <h3 className="font-serif text-lg font-semibold mb-6">Noise Class Breakdown by Model</h3>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={noiseBreakdownData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E2DA" vertical={false} />
                <XAxis dataKey="model" tick={{ fontSize: 11, fontFamily: 'var(--font-mono)' }} interval={0} angle={-15} textAnchor="end" height={60} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  iconType="circle" 
                  wrapperStyle={{ fontSize: '11px', fontFamily: 'var(--font-mono)' }} 
                  formatter={(value) => value.replace(/_/g, ' ')}
                />
                {ALL_CLASSES.map(cls => (
                  <Bar key={cls} dataKey={cls} stackId="a" fill={NOISE_COLORS[cls]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Noise Instance Table */}
        <div className="flex flex-col h-[600px]">
          <div className="flex justify-between items-baseline mb-4">
            <h3 className="font-serif text-lg font-semibold">Noise Instance Details</h3>
            <div className="flex gap-4 font-mono text-xs">
              <label className="flex items-center gap-2">
                Model:
                <select 
                  value={modelFilter} 
                  onChange={e => setModelFilter(e.target.value)}
                  className="p-1 border border-faint bg-white focus:outline-none"
                >
                  <option value="All">All</option>
                  {models.map(m => <option key={m} value={m}>{m}</option>)}
                </select>
              </label>
              <label className="flex items-center gap-2">
                Class:
                <select 
                  value={classFilter} 
                  onChange={e => setClassFilter(e.target.value)}
                  className="p-1 border border-faint bg-white focus:outline-none"
                >
                  <option value="All">All</option>
                  {ALL_CLASSES.map(cls => <option key={cls} value={cls}>{cls.replace(/_/g, ' ')}</option>)}
                </select>
              </label>
            </div>
          </div>

          <DataTable<NoiseRow>
            data={tableData}
            columns={noiseColumns}
            getRowKey={(r, idx) => `${r.run_id}-${r.task_id}-${idx}`}
            maxHeight="500px"
          />
        </div>
      </div>
    </div>
  );
}
