import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';

export interface Run {
  run_id: string;
  model: string;
  model_full: string;
  judge: string;
  timestamp: string;
  n_tasks: number;
  composite_ct: number;
  composite_ac: number;
}

export interface TaskRow {
  run_id: string;
  model: string;
  task_id: string;
  dimension: string;
  ac: number;
  ct: number;
  ni: number;
  refusal: boolean;
}

export interface ItemRow {
  run_id: string;
  model: string;
  task_id: string;
  item_id: string;
  dimension: 'fork' | 'guardian';
  execution_score: number | null;
  complete: boolean | null;
  correct: boolean;
  credit: number;
  value_i: number;
  capable: number;
  volunteered: number;
  rationale: string;
  severity: string | null;
  blocking: boolean | null;
}

export interface NoiseRow {
  run_id: string;
  model: string;
  task_id: string;
  description: string;
  noise_class: string;
  weight: number;
}

export interface ControlRow {
  run_id: string;
  model: string;
  task_id: string;
  control_prompt_id: string;
  success: boolean;
  rationale: string;
}

export interface TaskDef {
  task_id: string;
  prompt: string;
  gold_atomic_items: any[];
}

export interface DashboardData {
  runs: Run[];
  tasks: TaskRow[];
  items: ItemRow[];
  noise: NoiseRow[];
  controls: ControlRow[];
  taskDefs: Record<string, TaskDef>;
}

const RESULTS_DIR = path.join(process.cwd(), '..', 'results');
const TASKS_DIR = path.join(process.cwd(), '..', 'tasks');

function shortModelName(fullName: string): string {
  if (fullName.includes('/')) {
    const parts = fullName.split('/');
    return parts[parts.length - 1];
  }
  return fullName;
}

function loadAllTasks(dirPath: string): TaskDef[] {
  const tasks: TaskDef[] = [];
  if (!fs.existsSync(dirPath)) return tasks;

  function walk(currentPath: string) {
    const entries = fs.readdirSync(currentPath, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(currentPath, entry.name);
      if (entry.isDirectory()) {
        walk(fullPath);
      } else if (entry.isFile() && fullPath.endsWith('.yaml')) {
        const content = fs.readFileSync(fullPath, 'utf-8');
        try {
          const parsed = yaml.load(content) as TaskDef;
          if (parsed && parsed.task_id) {
            tasks.push(parsed);
          }
        } catch (e) {
          console.error(`Failed to parse task yaml: ${fullPath}`, e);
        }
      }
    }
  }

  walk(dirPath);
  return tasks;
}

// In-memory cache for fast subsequent reads during dev (hot reloads)
let cachedData: DashboardData | null = null;

export function loadDashboardData(useCache = true): DashboardData {
  if (useCache && cachedData) {
    return cachedData;
  }

  const taskDefsList = loadAllTasks(TASKS_DIR);
  const taskDefs: Record<string, TaskDef> = {};
  const itemMeta: Record<string, { value_i: number; severity: string | null; blocking: boolean | null }> = {};

  for (const task of taskDefsList) {
    taskDefs[task.task_id] = task;
    if (Array.isArray(task.gold_atomic_items)) {
      for (const item of task.gold_atomic_items) {
        if (!item.item_id) continue;
        const meta = {
          value_i: item.value_i !== undefined ? item.value_i : 1.0,
          blocking: item.blocking !== undefined ? item.blocking : null,
          severity: item.severity !== undefined ? item.severity : null,
        };
        itemMeta[item.item_id] = meta;
      }
    }
  }

  const runs: Run[] = [];
  const tasks: TaskRow[] = [];
  const items: ItemRow[] = [];
  const noise: NoiseRow[] = [];
  const controls: ControlRow[] = [];

  if (fs.existsSync(RESULTS_DIR)) {
    const runDirs = fs.readdirSync(RESULTS_DIR, { withFileTypes: true });

    for (const entry of runDirs) {
      if (!entry.isDirectory()) continue;
      const runDirPath = path.join(RESULTS_DIR, entry.name);
      const metaPath = path.join(runDirPath, 'run_meta.json');

      if (!fs.existsSync(metaPath)) continue;

      const metaStr = fs.readFileSync(metaPath, 'utf-8');
      const meta = JSON.parse(metaStr);

      const runId = meta.run_id;
      const modelFull = meta.model_under_test;
      const modelShort = shortModelName(modelFull);

      runs.push({
        run_id: runId,
        model: modelShort,
        model_full: modelFull,
        judge: meta.judge_model || '',
        timestamp: meta.timestamp,
        n_tasks: (meta.tasks_evaluated || []).length,
        composite_ct: meta.composite_ct ?? 0,
        composite_ac: meta.composite_ac ?? 0,
      });

      const resultFiles = fs.readdirSync(runDirPath).filter(f => f.endsWith('_result.json'));
      for (const resFile of resultFiles) {
        const resPath = path.join(runDirPath, resFile);
        const resStr = fs.readFileSync(resPath, 'utf-8');
        const res = JSON.parse(resStr);
        const taskId = res.task_id;

        tasks.push({
          run_id: runId,
          model: modelShort,
          task_id: taskId,
          dimension: res.dimension_alias || '',
          ac: res.absolute_coverage ?? 0,
          ct: res.conditional_thoroughness ?? 0,
          ni: res.noise_index ?? 0,
          refusal: res.refusal || false,
        });

        const judgs = res.judgments || {};
        const capMap = res.capability_map || {};

        if (Array.isArray(judgs.fork_verdicts)) {
          for (const v of judgs.fork_verdicts) {
            const im = itemMeta[v.item_id] || { value_i: 1.0, blocking: null, severity: null };
            const credit = im.value_i * (v.execution_score || 0) * (v.correct ? 1 : 0);
            items.push({
              run_id: runId,
              model: modelShort,
              task_id: taskId,
              item_id: v.item_id,
              dimension: 'fork',
              execution_score: v.execution_score ?? 0,
              complete: null,
              correct: v.correct || false,
              credit,
              value_i: im.value_i,
              capable: capMap[v.item_id] ? 1 : 0,
              volunteered: credit > 0 ? 1 : 0,
              rationale: v.rationale || '',
              severity: null,
              blocking: im.blocking,
            });
          }
        }

        if (Array.isArray(judgs.guardian_verdicts)) {
          for (const v of judgs.guardian_verdicts) {
            const im = itemMeta[v.item_id] || { value_i: 1.0, severity: null, blocking: null };
            const credit = im.value_i * (v.complete ? 1 : 0) * (v.correct ? 1 : 0);
            items.push({
              run_id: runId,
              model: modelShort,
              task_id: taskId,
              item_id: v.item_id,
              dimension: 'guardian',
              execution_score: null,
              complete: v.complete || false,
              correct: v.correct || false,
              credit,
              value_i: im.value_i,
              capable: capMap[v.item_id] ? 1 : 0,
              volunteered: credit > 0 ? 1 : 0,
              rationale: v.rationale || '',
              severity: im.severity,
              blocking: null,
            });
          }
        }

        if (Array.isArray(judgs.noise_instances)) {
          for (const n of judgs.noise_instances) {
            noise.push({
              run_id: runId,
              model: modelShort,
              task_id: taskId,
              description: n.description || '',
              noise_class: n.noise_class || '',
              weight: n.weight || 0,
            });
          }
        }

        if (Array.isArray(judgs.control_verdicts)) {
          for (const c of judgs.control_verdicts) {
            controls.push({
              run_id: runId,
              model: modelShort,
              task_id: taskId,
              control_prompt_id: c.control_prompt_id || '',
              success: c.success || false,
              rationale: c.rationale || '',
            });
          }
        }
      }
    }
  }

  const data: DashboardData = {
    runs,
    tasks,
    items,
    noise,
    controls,
    taskDefs,
  };
  cachedData = data;
  return data;
}

export function getLatestRuns(runs: Run[]): string[] {
  if (!runs || runs.length === 0) return [];
  const latestByModel: Record<string, Run> = {};
  for (const run of runs) {
    if (!latestByModel[run.model]) {
      latestByModel[run.model] = run;
    } else {
      if (new Date(run.timestamp) > new Date(latestByModel[run.model].timestamp)) {
        latestByModel[run.model] = run;
      }
    }
  }
  return Object.values(latestByModel).map(r => r.run_id);
}
