'use client';

import { useState, useMemo } from 'react';
import { DashboardData } from '@/lib/data-loader';
import { Settings2, BarChart2, Activity, Zap, ShieldAlert, ListTree, Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import LeaderboardView from './views/LeaderboardView';
import ModelComparisonView from './views/ModelComparisonView';
import TaskDeepDiveView from './views/TaskDeepDiveView';
import DimensionAnalysisView from './views/DimensionAnalysisView';
import NoiseAnalysisView from './views/NoiseAnalysisView';

interface DashboardClientProps {
  initialData: DashboardData;
  defaultRuns: string[];
}

type TabType = 'leaderboard' | 'comparison' | 'tasks' | 'dimensions' | 'noise';

const TABS: { id: TabType; label: string; icon: React.ReactNode }[] = [
  { id: 'leaderboard', label: 'Leaderboard', icon: <ListTree size={16} /> },
  { id: 'comparison', label: 'Model Comparison', icon: <BarChart2 size={16} /> },
  { id: 'tasks', label: 'Task Deep Dive', icon: <Zap size={16} /> },
  { id: 'dimensions', label: 'Dimension Analysis', icon: <Activity size={16} /> },
  { id: 'noise', label: 'Noise Analysis', icon: <ShieldAlert size={16} /> },
];

export default function DashboardClient({ initialData, defaultRuns }: DashboardClientProps) {
  const [selectedRuns, setSelectedRuns] = useState<Set<string>>(new Set(defaultRuns));
  const [activeTab, setActiveTab] = useState<TabType>('leaderboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Filter data based on selected runs
  const filteredData = useMemo(() => {
    const runsArray = Array.from(selectedRuns);
    return {
      runs: initialData.runs.filter(r => runsArray.includes(r.run_id)),
      tasks: initialData.tasks.filter(t => runsArray.includes(t.run_id)),
      items: initialData.items.filter(i => runsArray.includes(i.run_id)),
      noise: initialData.noise.filter(n => runsArray.includes(n.run_id)),
      controls: initialData.controls.filter(c => runsArray.includes(c.run_id)),
      taskDefs: initialData.taskDefs,
    };
  }, [initialData, selectedRuns]);

  const toggleRun = (runId: string) => {
    setSelectedRuns(prev => {
      const next = new Set(prev);
      if (next.has(runId)) next.delete(runId);
      else next.add(runId);
      return next;
    });
  };

  return (
    <div className="flex h-full w-full relative">
      {/* Mobile Overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-ink/20 z-40 md:hidden" 
          onClick={() => setIsSidebarOpen(false)} 
        />
      )}

      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-72 border-r border-faint bg-white flex flex-col shrink-0 transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="p-4 border-b border-faint flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Settings2 size={18} className="text-sage" />
            <h2 className="font-serif font-semibold text-lg">Settings</h2>
          </div>
          <button 
            className="md:hidden text-ink-light hover:text-ink"
            onClick={() => setIsSidebarOpen(false)}
          >
            <X size={20} />
          </button>
        </div>
        
        <div className="p-4 flex-1 overflow-y-auto">
          <h3 className="text-xs uppercase tracking-widest text-ink-light mb-3 font-semibold">Select Runs</h3>
          <div className="flex flex-col gap-2">
            {initialData.runs.map(run => (
              <label 
                key={run.run_id} 
                className={`flex items-start gap-3 p-2 border cursor-pointer transition-colors duration-200 ${
                  selectedRuns.has(run.run_id) 
                    ? 'border-sage bg-sage/5' 
                    : 'border-faint hover:border-ink-light/30'
                }`}
              >
                <div className="pt-0.5">
                  <input
                    type="checkbox"
                    checked={selectedRuns.has(run.run_id)}
                    onChange={() => toggleRun(run.run_id)}
                    className="accent-sage w-4 h-4 rounded-none border-faint cursor-pointer"
                  />
                </div>
                <div className="flex flex-col">
                  <span className="font-semibold text-sm leading-tight">{run.model}</span>
                  <span className="text-[10px] text-ink-light leading-tight mt-1">{run.timestamp}</span>
                  <span className="text-[10px] text-ink-light leading-tight">{run.n_tasks} tasks</span>
                </div>
              </label>
            ))}
          </div>
          
          <div className="mt-6 pt-4 border-t border-faint">
            <p className="text-xs text-ink-light italic leading-relaxed">
              * Select benchmark runs to include. Default: latest run per model.
            </p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 bg-paper">
        {/* Navigation */}
        <div className="flex items-center border-b border-faint shrink-0 px-4 md:px-8 pt-4 md:pt-6 bg-paper">
          <button 
            className="mr-4 pb-2 md:hidden text-ink-light hover:text-ink flex-shrink-0"
            onClick={() => setIsSidebarOpen(true)}
          >
            <Menu size={20} />
          </button>
          <nav className="flex items-center gap-1 overflow-x-auto whitespace-nowrap no-scrollbar pb-0">
            {TABS.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`relative flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === tab.id ? 'text-ink' : 'text-ink-light hover:text-ink'
                }`}
              >
                {tab.icon}
                {tab.label}
                {activeTab === tab.id && (
                  <motion.div
                    layoutId="activeTabIndicator"
                    className="absolute bottom-0 left-0 right-0 h-[2px] bg-sage"
                    initial={false}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  />
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* View Area */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              {activeTab === 'leaderboard' && <LeaderboardView data={filteredData} />}
              {activeTab === 'comparison' && <ModelComparisonView data={filteredData} />}
              {activeTab === 'tasks' && <TaskDeepDiveView data={filteredData} />}
              {activeTab === 'dimensions' && <DimensionAnalysisView data={filteredData} />}
              {activeTab === 'noise' && <NoiseAnalysisView data={filteredData} />}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
