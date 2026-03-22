# Dashboard v2 Implementation Plan

## Background & Motivation
The current Panel/Bokeh-based Python dashboard (`/mmce/dashboard`) is functionally adequate but visually simple and suffers from broken dynamic features. The goal is to build `/mmce/dashboard_v2`—a dynamic, responsive, and visually striking frontend using a modern JavaScript stack. This new dashboard must expose all existing datapoints and sentiments while strictly adhering to the `frontend-design` skill guidelines to avoid generic "AI slop" aesthetics.

## Scope & Impact
- **Location**: A new Next.js project will be created in `/mmce/dashboard_v2`.
- **Functionality**: Complete feature parity with the existing dashboard, including all charts, tables, and data breakdowns.
- **Impact**: Non-destructive. The existing `mmce/dashboard` and evaluation harness will remain unaffected. The Next.js app will simply read the existing JSON artifacts in `/mmce/results/` and `/mmce/tasks/`.

## Proposed Solution

### 1. Architecture: Next.js Fullstack
Using Next.js (App Router), we will leverage Server Components and Server Actions to directly read and parse the local `mmce/results` and `mmce/tasks` directories. This eliminates the need for a separate Python backend API or an intermediate build step to export JSON.

### 2. Aesthetic Direction: Academic / Print
Following the user's choice, the UI will commit to a bold "Academic / Print" editorial style:
- **Color Palette**: High-contrast, clean aesthetic. Off-white/warm-white backgrounds (e.g., `#FAF9F6`) with stark black text.
- **Data Colors**: Refined, pastel-tinted data visualizations (soft sage greens, muted terracottas, dusty blues) replacing generic primary colors.
- **Typography**: A highly distinctive pairing. `Playfair Display` for bold, elegant headings and UI anchors. `Roboto Mono` or `Fira Code` for precise, tabular data and numerical presentation.
- **Layout**: Generous margins, strict grid-based alignment, and clear typographic hierarchy, mimicking a high-end academic journal or editorial publication.
- **Motion**: Subtle, elegant animations using Framer Motion (e.g., soft staggered fade-ins for charts and rows, graceful layout transitions).

### 3. Tech Stack
- **Framework**: Next.js (React)
- **Styling**: Tailwind CSS
- **Data Visualization**: Recharts (for scatter, bar, and composed charts)
- **Tables**: HTML/React tables or TanStack Table for filterable views
- **Motion**: Framer Motion
- **Icons**: Lucide React

### 4. Data Layer Mapping
We will implement a Node.js equivalent of `data_loader.py` in `lib/data-loader.ts`. It will scan the directories, parse the JSON files, and construct identical normalized DataFrames (represented as arrays of objects in JS):
- Runs data
- Tasks data
- Items (Fork & Guardian verdicts)
- Noise instances
- Controls

### 5. Views to Replicate (1:1 Parity)
- **Leaderboard**: Interactive data table ranked by Composite CT, with conditional formatting bars for CT/AC/Gap/NI. Includes expandable row/detail view for per-task scores.
- **Model Comparison**: 
  - Scatter plot (AC vs CT) with diagonal reference.
  - Quadrant Chart (CT vs NI) denoting Thorough/Quiet/Noisy/Lazy quadrants.
  - Horizontal Bar chart (Thoroughness Gap).
- **Task Deep Dive**: 
  - Heatmap (Task × Model).
  - Capability vs Volunteering Matrix (Both, Gap, Neither, Surprise).
  - Verdict Rationale viewer (Prompt, items, controls, noise instances).
- **Dimension Analysis**: 
  - Fork: Stacked bars (Execution Score distribution) and Grouped bars (Blocking vs Non-Blocking).
  - Guardian: Grouped bars (Detection rate by severity) and Per-flag heatmap.
- **Noise Analysis**: 
  - Stacked bar (Noise classes by model).
  - Filterable table of noise instances.

## Alternatives Considered
- **Vite SPA + Python JSON Export**: Rejected. While viable for static hosting, it requires an additional build step. Next.js was selected for seamless, out-of-the-box local filesystem access.

## Phased Implementation Plan
1. **Phase 1: Setup & Data Layer**
   - Initialize Next.js application in `mmce/dashboard_v2`.
   - Install dependencies (`recharts`, `framer-motion`, `tailwind`, fonts).
   - Implement `lib/data-loader.ts` to parse `run_meta.json` and `*_result.json` files and provide normalized data arrays to the app.
2. **Phase 2: Shell & Design System**
   - Configure Tailwind with the "Academic / Print" color scheme and fonts.
   - Build the main application shell (Sidebar for run selection, main content tabs).
3. **Phase 3: View Implementation**
   - Recreate the Leaderboard, Model Comparison, Task Deep Dive, Dimension Analysis, and Noise Analysis views using React components and Recharts.
4. **Phase 4: Polish & Refinement**
   - Apply Framer Motion for staggered component entry.
   - Refine spacing, typography, and visual hierarchy to strictly meet the `frontend-design` aesthetic constraints.
   - Ensure all dynamic interactions (filters, row selections, tab switching) function flawlessly.

## Verification & Testing
- Run `npm run dev` in the new directory.
- Visually verify that all 5 tabs render without errors.
- Cross-reference data points in the new dashboard with the existing Panel dashboard to ensure 100% data accuracy.
- Confirm the design language strongly reflects the intended "Academic / Print" style and avoids generic defaults.
