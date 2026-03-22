'use client';

import { useState, useMemo } from 'react';
import { DashboardData } from '@/lib/data-loader';
import DataTable, { Column } from '../ui/DataTable';

interface LeaderboardViewProps {
  data: DashboardData;
}

interface LeaderboardRow {
  model: string;
  overallScore: number;
  compositeCt: number;
  compositeAc: number;
  gap: number;
  forkCt: number;
  guardianCt: number;
  avgNi: number;
  tasks: number;
}

interface TaskDetailRow {
  task: string;
  dimension: string;
  ac: number;
  ct: number;
  ni: number;
}

export default function LeaderboardView({ data }: LeaderboardViewProps) {
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  const leaderboardData = useMemo(() => {
    if (!data.runs.length) return [];

    return data.runs.map(run => {
      const modelTasks = data.tasks.filter(t => t.run_id === run.run_id);

      const forkTasks = modelTasks.filter(t => t.dimension === 'fork');
      const guardianTasks = modelTasks.filter(t => t.dimension === 'guardian');

      const forkCt = forkTasks.length ? forkTasks.reduce((acc, t) => acc + t.ct, 0) / forkTasks.length : 0;
      const guardianCt = guardianTasks.length ? guardianTasks.reduce((acc, t) => acc + t.ct, 0) / guardianTasks.length : 0;

      const avgNi = modelTasks.length ? modelTasks.reduce((acc, t) => acc + t.ni, 0) / modelTasks.length : 0;

      return {
        model: run.model,
        overallScore: run.composite_ct,
        compositeCt: run.composite_ct,
        compositeAc: run.composite_ac,
        gap: run.composite_ct - run.composite_ac,
        forkCt,
        guardianCt,
        avgNi,
        tasks: run.n_tasks,
      };
    });
  }, [data]);

  const taskDetailsData = useMemo(() => {
    if (!selectedModel) return [];
    return data.tasks.filter(t => t.model === selectedModel).map(t => ({
      task: t.task_id,
      dimension: t.dimension,
      ac: t.ac,
      ct: t.ct,
      ni: t.ni,
    }));
  }, [data, selectedModel]);

  const renderBar = (val: number, max: number, colorClass: string) => {
    const pct = Math.max(0, Math.min(100, (val / max) * 100));
    return (
      <div className="w-full h-1 bg-faint overflow-hidden mt-1">
        <div className={`h-full ${colorClass}`} style={{ width: `${pct}%` }} />
      </div>
    );
  };

  const leaderboardColumns: Column<LeaderboardRow>[] = [
    { key: 'model', label: 'Model', className: 'font-semibold text-ink' },
    {
      key: 'overallScore',
      label: 'Overall Score',
      className: 'font-bold',
      render: (r) => (
        <div>
          <span className="text-base font-bold">{r.overallScore.toFixed(3)}</span>
          {renderBar(r.overallScore, 1, 'bg-green-600')}
        </div>
      )
    },
    {
      key: 'compositeCt',
      label: 'Composite CT',
      render: (r) => (
        <div>
          {r.compositeCt.toFixed(3)}
          {renderBar(r.compositeCt, 1, 'bg-sage')}
        </div>
      )
    },
    {
      key: 'compositeAc',
      label: 'Composite AC',
      render: (r) => (
        <div>
          {r.compositeAc.toFixed(3)}
          {renderBar(r.compositeAc, 1, 'bg-dustyblue')}
        </div>
      )
    },
    { key: 'gap', label: 'Thoroughness Gap', render: (r) => r.gap.toFixed(3) },
    {
      key: 'forkCt',
      label: 'Fork CT',
      render: (r) => (
        <div>
          {r.forkCt.toFixed(3)}
          {renderBar(r.forkCt, 1, 'bg-sage')}
        </div>
      )
    },
    {
      key: 'guardianCt',
      label: 'Guardian CT',
      render: (r) => (
        <div>
          {r.guardianCt.toFixed(3)}
          {renderBar(r.guardianCt, 1, 'bg-sage')}
        </div>
      )
    },
    {
      key: 'avgNi',
      label: 'Avg NI',
      render: (r) => (
        <div>
          {r.avgNi.toFixed(3)}
          {renderBar(r.avgNi, 1, 'bg-terracotta')}
        </div>
      )
    },
    { key: 'tasks', label: 'Tasks' },
  ];

  const taskColumns: Column<TaskDetailRow>[] = [
    { key: 'task', label: 'Task' },
    { key: 'dimension', label: 'Dimension', className: 'uppercase text-[10px]' },
    { key: 'ac', label: 'AC', render: (r) => r.ac.toFixed(3) },
    { key: 'ct', label: 'CT', render: (r) => r.ct.toFixed(3) },
    { key: 'ni', label: 'NI', render: (r) => r.ni.toFixed(3) },
  ];

  if (!leaderboardData.length) {
    return <div className="p-8 text-ink-light font-serif">No results found for selected runs.</div>;
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h2 className="font-serif text-2xl font-semibold mb-2">Model Leaderboard</h2>
        <p className="text-sm text-ink-light">
          Ranked by Overall Score (= Composite CT). Thoroughness Gap = CT − AC. Positive means unrealized capability.
        </p>
      </div>

      <DataTable<LeaderboardRow>
        data={leaderboardData}
        columns={leaderboardColumns}
        getRowKey={(r, idx) => r.model}
        initialSort={{ key: 'overallScore', direction: 'desc' }}
        onRowClick={(r) => setSelectedModel(r.model === selectedModel ? null : r.model)}
        selectedRowKey={selectedModel || undefined}
      />

      {selectedModel && (
        <div className="border border-faint bg-white p-6 mt-4">
          <h3 className="font-serif text-lg font-semibold mb-4">Per-Task Scores: {selectedModel}</h3>
          <DataTable<TaskDetailRow>
            data={taskDetailsData}
            columns={taskColumns}
            getRowKey={(r, idx) => r.task}
            maxHeight="400px"
          />
        </div>
      )}
    </div>
  );
}
