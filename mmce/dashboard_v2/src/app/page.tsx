import { loadDashboardData, getLatestRuns } from '@/lib/data-loader';
import DashboardClient from '@/components/DashboardClient';

export default function Home() {
  const data = loadDashboardData(false);
  const defaultRuns = getLatestRuns(data.runs);

  return (
    <main className="flex-1 flex flex-col h-screen overflow-hidden">
      <header className="px-8 py-6 border-b border-faint shrink-0 flex items-baseline justify-between">
        <div>
          <h1 className="font-serif text-3xl tracking-tight text-ink font-semibold">MMCE Thoroughness Dashboard</h1>
          <p className="text-sm text-ink-light mt-1 uppercase tracking-widest font-medium">Evaluation Results & Analytics</p>
        </div>
        <div className="text-xs text-ink-light border border-faint px-3 py-1 bg-white">
          v2.0 // Academic Print
        </div>
      </header>
      
      <div className="flex-1 overflow-hidden flex">
        <DashboardClient initialData={data} defaultRuns={defaultRuns} />
      </div>
    </main>
  );
}
