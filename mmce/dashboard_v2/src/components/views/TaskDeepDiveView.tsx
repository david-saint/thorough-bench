'use client';

import { useState, useMemo } from 'react';
import { DashboardData } from '@/lib/data-loader';

interface TaskDeepDiveViewProps {
  data: DashboardData;
}

export default function TaskDeepDiveView({ data }: TaskDeepDiveViewProps) {
  const [metric, setMetric] = useState<'ct' | 'ac'>('ct');
  const [selectedTask, setSelectedTask] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  // Heatmap Data
  const { models, tasks, heatmap } = useMemo(() => {
    const mods = Array.from(new Set(data.tasks.map(t => t.model))).sort();
    const tsks = Array.from(new Set(data.tasks.map(t => t.task_id))).sort();
    
    const map: Record<string, Record<string, number>> = {};
    for (const t of data.tasks) {
      if (!map[t.task_id]) map[t.task_id] = {};
      map[t.task_id][t.model] = metric === 'ct' ? t.ct : t.ac;
    }
    
    // Set defaults if null
    if (!selectedTask && tsks.length > 0) setSelectedTask(tsks[0]);
    if (!selectedModel && mods.length > 0) setSelectedModel(mods[0]);

    return { models: mods, tasks: tsks, heatmap: map };
  }, [data.tasks, metric, selectedTask, selectedModel]);

  // Capability Matrix
  const capabilityMatrix = useMemo(() => {
    if (!selectedTask) return null;
    const itemsForTask = data.items.filter(i => i.task_id === selectedTask);
    const itemIds = Array.from(new Set(itemsForTask.map(i => i.item_id))).sort();
    
    const matrix: Record<string, Record<string, 'Both' | 'Gap' | 'Surprise' | 'Neither' | '—'>> = {};
    for (const iId of itemIds) {
      matrix[iId] = {};
      for (const m of models) {
        const item = itemsForTask.find(i => i.item_id === iId && i.model === m);
        if (!item) {
          matrix[iId][m] = '—';
        } else {
          const cap = !!item.capable;
          const vol = !!item.volunteered;
          if (cap && vol) matrix[iId][m] = 'Both';
          else if (cap && !vol) matrix[iId][m] = 'Gap';
          else if (!cap && vol) matrix[iId][m] = 'Surprise';
          else matrix[iId][m] = 'Neither';
        }
      }
    }
    return { itemIds, matrix };
  }, [data.items, selectedTask, models]);

  // Interpolate color from faint (#E5E2DA) to sage (#9CAF88)
  const getColor = (val: number) => {
    if (val === undefined || isNaN(val)) return 'transparent';
    const r1 = 229, g1 = 226, b1 = 218;
    const r2 = 156, g2 = 175, b2 = 136;
    const r = Math.round(r1 + (r2 - r1) * val);
    const g = Math.round(g1 + (g2 - g1) * val);
    const b = Math.round(b1 + (b2 - b1) * val);
    return `rgba(${r}, ${g}, ${b}, ${0.4 + (val * 0.6)})`;
  };

  const statusColors = {
    'Both': 'bg-sage/40',
    'Gap': 'bg-[#D4A373]/40', // Muted gold
    'Neither': 'bg-terracotta/40',
    'Surprise': 'bg-dustyblue/40',
    '—': 'bg-transparent text-ink-light'
  };

  const getRationaleContent = () => {
    if (!selectedTask || !selectedModel) return null;
    const items = data.items.filter(i => i.task_id === selectedTask && i.model === selectedModel);
    const controls = data.controls.filter(c => c.task_id === selectedTask && c.model === selectedModel);
    const noise = data.noise.filter(n => n.task_id === selectedTask && n.model === selectedModel);
    const taskDef = data.taskDefs[selectedTask];

    return { items, controls, noise, taskDef };
  };

  const rationale = getRationaleContent();

  return (
    <div className="flex flex-col gap-10">
      <div>
        <h2 className="font-serif text-2xl font-semibold mb-2">Task Deep Dive</h2>
        <div className="flex gap-4 mb-4">
          <label className="text-sm font-semibold flex items-center gap-2">
            Metric:
            <select 
              value={metric} 
              onChange={e => setMetric(e.target.value as 'ct' | 'ac')}
              className="p-1 border border-faint bg-white font-mono text-xs focus:outline-none"
            >
              <option value="ct">Conditional Thoroughness (CT)</option>
              <option value="ac">Absolute Coverage (AC)</option>
            </select>
          </label>
        </div>
      </div>

      {/* Heatmap */}
      <div className="border border-faint bg-white p-6 overflow-x-auto flex flex-col gap-6">
        <div className="flex justify-between items-baseline">
          <h3 className="font-serif text-lg font-semibold">Task × Model Performance</h3>
          
          {/* Color Scale Legend */}
          <div className="flex items-center gap-3 font-mono text-[10px] text-ink-light">
            <span>0.000</span>
            <div className="w-32 h-2 border border-faint" style={{ background: 'linear-gradient(to right, rgba(229, 226, 218, 0.4), rgba(156, 175, 136, 1.0))' }} />
            <span>1.000</span>
            <span className="ml-2 italic uppercase opacity-60">(Higher is Better)</span>
          </div>
        </div>

        <div className="inline-block min-w-full">
          <div className="flex">
            <div className="w-80 shrink-0" />
            {models.map(m => (
              <div key={m} className="w-40 px-2 text-xs font-semibold text-center break-words leading-tight flex items-end justify-center pb-2" title={m}>
                {m}
              </div>
            ))}
          </div>
          {tasks.map(t => (
            <div key={t} className="flex border-t border-faint/50 hover:bg-faint/20 cursor-pointer" onClick={() => setSelectedTask(t)}>
              <div className={`w-80 pr-4 py-3 text-xs leading-relaxed ${selectedTask === t ? 'font-bold' : ''}`} title={t}>
                {t.replace(/^(fork|guardian)_st_/, '').replace(/_/g, ' ')}
              </div>
              {models.map(m => {
                const val = heatmap[t]?.[m];
                return (
                  <div 
                    key={m} 
                    className="w-40 flex items-center justify-center text-xs font-mono border-l border-faint/50 transition-all hover:ring-2 hover:ring-sage hover:z-10 relative"
                    style={{ backgroundColor: getColor(val || 0) }}
                    onClick={(e) => { e.stopPropagation(); setSelectedTask(t); setSelectedModel(m); }}
                  >
                    {val !== undefined ? val.toFixed(3) : '-'}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-6 p-6 border border-faint bg-white">
        <div className="flex-1">
          <label className="block text-[10px] uppercase tracking-widest text-ink-light font-bold mb-2">Select Task for Analysis</label>
          <select 
            value={selectedTask || ''} 
            onChange={e => setSelectedTask(e.target.value)}
            className="w-full p-2 border border-faint bg-paper font-mono text-sm focus:outline-none focus:ring-1 focus:ring-sage"
          >
            {tasks.map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
        <div className="flex-1">
          <label className="block text-[10px] uppercase tracking-widest text-ink-light font-bold mb-2">Select Model for Rationale</label>
          <select 
            value={selectedModel || ''} 
            onChange={e => setSelectedModel(e.target.value)}
            className="w-full p-2 border border-faint bg-paper font-mono text-sm focus:outline-none focus:ring-1 focus:ring-sage"
          >
            {models.map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {/* Capability Matrix */}
        {capabilityMatrix && (
          <div className="border border-faint bg-white p-6">
            <h3 className="font-serif text-lg font-semibold mb-2">Capability vs Volunteering</h3>
            <p className="text-xs text-ink-light mb-4">Interactive matrix. Click a model header to update the rationale view.</p>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 font-mono text-[10px]">
              <div className="flex flex-col gap-1 p-2 border border-faint bg-paper" title="Model is capable and correctly volunteered the information.">
                <span className="flex items-center gap-1 font-bold"><div className="w-2 h-2 bg-sage/40 border border-faint" /> Both</span>
                <span className="text-ink-light leading-tight">Capable + Volunteered</span>
              </div>
              <div className="flex flex-col gap-1 p-2 border border-faint bg-paper" title="Model is capable but failed to volunteer the information (unrealized capability).">
                <span className="flex items-center gap-1 font-bold"><div className="w-2 h-2 bg-[#D4A373]/40 border border-faint" /> Gap</span>
                <span className="text-ink-light leading-tight">Capable + Silent</span>
              </div>
              <div className="flex flex-col gap-1 p-2 border border-faint bg-paper" title="Model lacks the capability and remained silent.">
                <span className="flex items-center gap-1 font-bold"><div className="w-2 h-2 bg-terracotta/40 border border-faint" /> Neither</span>
                <span className="text-ink-light leading-tight">Incapable + Silent</span>
              </div>
              <div className="flex flex-col gap-1 p-2 border border-faint bg-paper" title="Model volunteered information despite failing the capability control (lucky guess).">
                <span className="flex items-center gap-1 font-bold"><div className="w-2 h-2 bg-dustyblue/40 border border-faint" /> Surprise</span>
                <span className="text-ink-light leading-tight">Incapable + Volunteered</span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs whitespace-nowrap">
                <thead className="bg-paper border-b border-faint">
                  <tr>
                    <th className="px-2 py-2 font-semibold">Item</th>
                    {models.map(m => (
                      <th 
                        key={m} 
                        onClick={() => setSelectedModel(m)}
                        className={`px-2 py-2 font-semibold text-center cursor-pointer transition-all hover:text-sage ${
                          selectedModel === m 
                            ? 'bg-sage/10 text-sage underline underline-offset-4 decoration-sage' 
                            : 'text-ink-light'
                        }`}
                      >
                        {m}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-faint font-mono">
                  {capabilityMatrix.itemIds.map(iId => (
                    <tr key={iId}>
                      <td className="px-2 py-2 truncate max-w-[150px]" title={iId}>{iId}</td>
                      {models.map(m => {
                        const status = capabilityMatrix.matrix[iId][m];
                        const title = status === 'Both' ? 'Capable + Volunteered' : 
                                      status === 'Gap' ? 'Capable but Silent' : 
                                      status === 'Neither' ? 'Incapable and Silent' : 
                                      status === 'Surprise' ? 'Incapable but Volunteered' : '';
                        return (
                          <td key={m} className="p-1" title={title}>
                            <div className={`w-full h-full py-1 text-center border border-transparent ${statusColors[status] || ''}`}>
                              {status}
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Verdict Rationale */}
        {rationale && (
          <div className="border border-faint bg-white p-6 flex flex-col h-[600px]">
            <h3 className="font-serif text-lg font-semibold mb-2">Verdict Rationale</h3>
            <p className="text-xs text-ink-light mb-4">Task: <span className="font-mono bg-faint px-1">{selectedTask}</span> | Model: <span className="font-mono bg-faint px-1">{selectedModel}</span></p>
            
            <div className="overflow-y-auto flex-1 pr-4 custom-scrollbar space-y-6">
              {rationale.taskDef && (
                <div>
                  <h4 className="font-bold text-sm uppercase tracking-widest mb-2 border-b border-faint pb-1">Prompt</h4>
                  <pre className="whitespace-pre-wrap text-xs text-ink-light font-mono bg-paper p-3 border border-faint">
                    {rationale.taskDef.prompt}
                  </pre>
                </div>
              )}

              {rationale.items.map(item => {
                const ctrl = rationale.controls.find(c => {
                  const atom = rationale.taskDef?.gold_atomic_items?.find(a => a.item_id === item.item_id);
                  return atom && atom.control_prompt_id === c.control_prompt_id;
                });

                return (
                  <div key={item.item_id} className="border-l-2 border-sage pl-3">
                    <h5 className="font-bold text-sm font-mono mb-1">{item.item_id}</h5>
                    <div className="flex gap-3 text-xs mb-2 text-ink-light">
                      <span>Dimension: {item.dimension}</span>
                      <span>Score: {item.dimension === 'fork' ? item.execution_score : item.complete} (Correct: {item.correct ? 'Y' : 'N'})</span>
                      <span>Capable: {item.capable ? 'Y' : 'N'}</span>
                      <span>Volunteered: {item.volunteered ? 'Y' : 'N'}</span>
                    </div>
                    <p className="text-sm italic text-ink-light bg-paper p-2 border border-faint">
                      "{item.rationale}"
                    </p>
                    {ctrl && (
                      <div className="mt-2 bg-faint/30 p-2 text-xs border border-faint border-dashed">
                        <span className="font-semibold block mb-1">Control ({ctrl.control_prompt_id}): {ctrl.success ? 'PASS' : 'FAIL'}</span>
                        <p>{ctrl.rationale}</p>
                      </div>
                    )}
                  </div>
                );
              })}

              {rationale.noise.length > 0 && (
                <div>
                  <h4 className="font-bold text-sm uppercase tracking-widest mb-2 border-b border-faint pb-1 text-terracotta">Noise Instances</h4>
                  {rationale.noise.map((n, idx) => (
                    <div key={idx} className="mb-2 text-sm border-l-2 border-terracotta pl-3">
                      <span className="font-semibold">{n.noise_class.replace(/_/g, ' ')}</span> (Wt: {n.weight})
                      <p className="text-ink-light italic text-xs mt-1">"{n.description}"</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
