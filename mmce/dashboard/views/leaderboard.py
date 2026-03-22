"""Tab 1: Leaderboard — ranked table of models by Overall Score."""

from __future__ import annotations

import panel as pn
import pandas as pd

from mmce.dashboard.data_loader import DashboardData

# Color scales for conditional formatting
_GREEN = "linear-gradient(90deg, #22c55e88 {pct}%, transparent {pct}%)"
_RED = "linear-gradient(90deg, #ef444488 {pct}%, transparent {pct}%)"
_AMBER = "linear-gradient(90deg, #f59e0b88 {pct}%, transparent {pct}%)"


def _pct(val: float, max_val: float) -> float:
    if max_val == 0:
        return 0
    return min(val / max_val * 100, 100)


def _build_leaderboard_df(data: DashboardData) -> pd.DataFrame:
    """Build the leaderboard summary DataFrame."""
    runs = data.runs_df.copy()
    tasks = data.tasks_df.copy()

    if runs.empty or tasks.empty:
        return pd.DataFrame()

    # Per-dimension CT/AC
    dim_stats = (
        tasks.groupby(["run_id", "model", "dimension"])
        .agg({"ct": "mean", "ac": "mean", "ni": "mean"})
        .reset_index()
    )

    fork_stats = dim_stats[dim_stats["dimension"] == "fork"][
        ["run_id", "model", "ct", "ac"]
    ].rename(columns={"ct": "fork_ct", "ac": "fork_ac"})

    guardian_stats = dim_stats[dim_stats["dimension"] == "guardian"][
        ["run_id", "model", "ct", "ac"]
    ].rename(columns={"ct": "guardian_ct", "ac": "guardian_ac"})

    # Average NI across all tasks
    avg_ni = tasks.groupby(["run_id", "model"])["ni"].mean().reset_index()
    avg_ni.columns = ["run_id", "model", "avg_ni"]

    # Merge
    lb = runs[["run_id", "model", "n_tasks", "composite_ct", "composite_ac"]].copy()
    lb = lb.merge(fork_stats, on=["run_id", "model"], how="left")
    lb = lb.merge(guardian_stats, on=["run_id", "model"], how="left")
    lb = lb.merge(avg_ni, on=["run_id", "model"], how="left")

    # Overall Score = Composite CT (the primary ranking metric)
    lb["overall_score"] = lb["composite_ct"]
    lb["gap"] = lb["composite_ct"] - lb["composite_ac"]
    lb = lb.sort_values("overall_score", ascending=False).reset_index(drop=True)

    # Round for display
    float_cols = [
        "overall_score", "composite_ct", "composite_ac", "gap",
        "fork_ct", "fork_ac", "guardian_ct", "guardian_ac", "avg_ni",
    ]
    for col in float_cols:
        if col in lb.columns:
            lb[col] = lb[col].round(3)

    lb = lb.rename(columns={
        "model": "Model",
        "overall_score": "Overall Score",
        "composite_ct": "Composite CT",
        "composite_ac": "Composite AC",
        "gap": "Thoroughness Gap",
        "fork_ct": "Fork CT",
        "guardian_ct": "Guardian CT",
        "avg_ni": "Avg NI",
        "n_tasks": "Tasks",
    })

    return lb[
        ["Model", "Overall Score", "Composite CT", "Composite AC", "Thoroughness Gap",
         "Fork CT", "Guardian CT", "Avg NI", "Tasks"]
    ]


def _build_task_detail_df(data: DashboardData, model: str) -> pd.DataFrame:
    """Build per-task detail for a selected model."""
    tasks = data.tasks_df[data.tasks_df["model"] == model].copy()
    if tasks.empty:
        return pd.DataFrame()

    tasks = tasks[["task_id", "dimension", "ac", "ct", "ni"]].copy()
    for col in ["ac", "ct", "ni"]:
        tasks[col] = tasks[col].round(3)

    return tasks.rename(columns={
        "task_id": "Task",
        "dimension": "Dimension",
        "ac": "AC",
        "ct": "CT",
        "ni": "NI",
    }).reset_index(drop=True)


def build(data: DashboardData) -> pn.Column:
    """Build the leaderboard tab."""
    lb_df = _build_leaderboard_df(data)

    if lb_df.empty:
        return pn.Column(pn.pane.Markdown("## No results found"))

    # Color formatters for Tabulator
    bokeh_formatters = {
        "Overall Score": {"type": "progress", "max": 1.0, "color": "#16a34a"},
        "Composite CT": {"type": "progress", "max": 1.0, "color": "#22c55e"},
        "Composite AC": {"type": "progress", "max": 1.0, "color": "#3b82f6"},
        "Fork CT": {"type": "progress", "max": 1.0, "color": "#22c55e"},
        "Guardian CT": {"type": "progress", "max": 1.0, "color": "#22c55e"},
        "Avg NI": {"type": "progress", "max": 1.0, "color": "#ef4444"},
    }

    table = pn.widgets.Tabulator(
        lb_df,
        layout="fit_data_stretch",
        height=250,
        show_index=False,
        selectable="row",
        formatters=bokeh_formatters,
        frozen_columns=["Model"],
        widths={"Model": 200, "Overall Score": 150},
    )

    # Detail panel updates on row selection
    detail_title = pn.pane.Markdown("### Select a model row to see per-task breakdown")
    detail_table = pn.widgets.Tabulator(
        pd.DataFrame(),
        layout="fit_columns",
        height=250,
        show_index=False,
        visible=False,
    )

    def on_row_select(event):
        if not event.new:
            return
        row_idx = event.new[0]
        model_name = lb_df.iloc[row_idx]["Model"]
        detail = _build_task_detail_df(data, model_name)
        detail_table.value = detail
        detail_table.visible = True
        detail_title.object = f"### Per-Task Scores: {model_name}"

    table.param.watch(on_row_select, "selection")

    return pn.Column(
        pn.pane.Markdown("## Model Leaderboard"),
        pn.pane.Markdown(
            "*Ranked by Overall Score (= Composite CT). "
            "Thoroughness Gap = CT − AC: positive means unrealized capability.*"
        ),
        table,
        pn.layout.Divider(),
        detail_title,
        detail_table,
    )
