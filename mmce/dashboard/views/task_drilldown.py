"""Tab 3: Task Deep Dive — heatmap, capability matrix, verdict rationale viewer."""

from __future__ import annotations

import panel as pn
import pandas as pd
from bokeh.models import (
    BasicTicker,
    ColorBar,
    ColumnDataSource,
    HoverTool,
    LinearColorMapper,
)
from bokeh.palettes import RdYlGn9
from bokeh.plotting import figure

from mmce.dashboard.data_loader import DashboardData


def _task_heatmap(data: DashboardData, metric: str = "ct") -> pn.pane.Bokeh:
    """Panel A: Task × Model heatmap."""
    tasks = data.tasks_df.copy()
    if tasks.empty:
        return pn.pane.Markdown("No data")

    pivot = tasks.pivot_table(
        index="model", columns="task_id", values=metric, aggfunc="first"
    )

    models = list(pivot.index)
    task_ids = list(pivot.columns)

    # Shorten task IDs for display
    short_ids = [t.replace("fork_st_", "F").replace("guardian_st_", "G").replace("_", " ")[:30]
                 for t in task_ids]
    id_map = dict(zip(task_ids, short_ids))

    xs, ys, vals, task_fulls = [], [], [], []
    for m in models:
        for t in task_ids:
            xs.append(id_map[t])
            ys.append(m)
            v = pivot.loc[m, t]
            vals.append(v if pd.notna(v) else 0.0)
            task_fulls.append(t)

    source = ColumnDataSource({
        "x": xs, "y": ys, "value": vals,
        "task_full": task_fulls,
        "display": [f"{v:.3f}" for v in vals],
    })

    mapper = LinearColorMapper(
        palette=list(RdYlGn9), low=0, high=1,
    )

    p = figure(
        title=f"Task × Model: {metric.upper()}",
        x_range=list(dict.fromkeys(xs)),
        y_range=list(dict.fromkeys(ys)),
        width=700, height=300,
        tools="tap,reset",
        toolbar_location="above",
    )

    p.rect(
        x="x", y="y", width=0.95, height=0.95,
        source=source,
        fill_color={"field": "value", "transform": mapper},
        line_color="white", line_width=1,
    )

    p.text(
        x="x", y="y", text="display",
        source=source,
        text_align="center", text_baseline="middle",
        text_font_size="10pt", text_color="black",
    )

    color_bar = ColorBar(
        color_mapper=mapper, ticker=BasicTicker(desired_num_ticks=5),
        label_standoff=8, width=15,
    )
    p.add_layout(color_bar, "right")

    p.xaxis.major_label_orientation = 0.7
    p.add_tools(HoverTool(tooltips=[
        ("Task", "@task_full"),
        ("Model", "@y"),
        (metric.upper(), "@display"),
    ]))

    return pn.pane.Bokeh(p)


def _capability_matrix(data: DashboardData, task_id: str) -> pn.Column:
    """Panel B: Capability vs Volunteering matrix for a selected task."""
    items = data.items_df[data.items_df["task_id"] == task_id].copy()
    if items.empty:
        return pn.pane.Markdown(f"*No item data for {task_id}*")

    # Build matrix: rows=items, cols=models
    models = sorted(items["model"].unique())
    item_ids = sorted(items["item_id"].unique())

    rows = []
    for item_id in item_ids:
        row = {"Item": item_id}
        for model in models:
            match = items[(items["item_id"] == item_id) & (items["model"] == model)]
            if match.empty:
                row[model] = "—"
            else:
                r = match.iloc[0]
                capable = bool(r["capable"])
                volunteered = bool(r["volunteered"])
                if capable and volunteered:
                    row[model] = "Both"
                elif capable and not volunteered:
                    row[model] = "Gap"
                elif not capable and volunteered:
                    row[model] = "Surprise"
                else:
                    row[model] = "Neither"
        rows.append(row)

    df = pd.DataFrame(rows)

    # Color mapping for Tabulator
    text_align = {col: "center" for col in models}
    frozen_columns = ["Item"]

    table = pn.widgets.Tabulator(
        df,
        layout="fit_columns",
        height=250,
        show_index=False,
        text_align=text_align,
        frozen_columns=frozen_columns,
        stylesheets=["""
            .tabulator-cell[data-value="Both"] { background-color: #22c55e44; }
            .tabulator-cell[data-value="Gap"] { background-color: #f59e0b44; }
            .tabulator-cell[data-value="Neither"] { background-color: #ef444444; }
            .tabulator-cell[data-value="Surprise"] { background-color: #3b82f644; }
        """],
    )

    legend = pn.pane.Markdown(
        "**Legend**: "
        '<span style="background:#22c55e44;padding:2px 6px">Both</span> = capable + volunteered  '
        '<span style="background:#f59e0b44;padding:2px 6px">Gap</span> = capable but silent  '
        '<span style="background:#ef444444;padding:2px 6px">Neither</span> = no capability  '
        '<span style="background:#3b82f644;padding:2px 6px">Surprise</span> = volunteered without control pass'
    )

    return pn.Column(
        pn.pane.Markdown(f"### Capability vs Volunteering: {task_id}"),
        legend,
        table,
    )


def _rationale_viewer(data: DashboardData, task_id: str, model: str) -> pn.Column:
    """Panel C: Verdict rationale viewer for a specific task + model."""
    items = data.items_df[
        (data.items_df["task_id"] == task_id) & (data.items_df["model"] == model)
    ]
    controls = data.controls_df[
        (data.controls_df["task_id"] == task_id) & (data.controls_df["model"] == model)
    ]
    noise = data.noise_df[
        (data.noise_df["task_id"] == task_id) & (data.noise_df["model"] == model)
    ]

    sections = []

    # Task prompt
    task_def = data.task_defs.get(task_id)
    if task_def:
        sections.append(pn.pane.Markdown(
            f"**Prompt:**\n\n> {task_def.prompt[:500]}{'...' if len(task_def.prompt) > 500 else ''}"
        ))

    # Item verdicts
    for _, item in items.iterrows():
        dim = item["dimension"]
        if dim == "fork":
            score_label = f"execution_score={item['execution_score']}, correct={item['correct']}"
        else:
            score_label = f"complete={item['complete']}, correct={item['correct']}"

        capable = "Yes" if item["capable"] else "No"
        volunteered = "Yes" if item["volunteered"] else "No"

        # Find matching control
        ctrl_text = ""
        if task_def:
            for atom in task_def.gold_atomic_items:
                if atom.item_id == item["item_id"]:
                    ctrl_match = controls[
                        controls["control_prompt_id"] == atom.control_prompt_id
                    ]
                    if not ctrl_match.empty:
                        c = ctrl_match.iloc[0]
                        ctrl_text = (
                            f"\n\n**Control** (`{atom.control_prompt_id}`): "
                            f"success={c['success']}\n\n"
                            f"> {c['rationale'][:300]}"
                        )
                    break

        sections.append(pn.pane.Markdown(
            f"---\n**{item['item_id']}** — {score_label} | "
            f"Capable: {capable} | Volunteered: {volunteered}\n\n"
            f"> {item['rationale'][:400]}"
            f"{ctrl_text}"
        ))

    # Noise instances
    if not noise.empty:
        sections.append(pn.pane.Markdown("---\n**Noise Instances:**"))
        for _, n in noise.iterrows():
            sections.append(pn.pane.Markdown(
                f"- **{n['noise_class']}** (weight={n['weight']}): {n['description']}"
            ))

    if not sections:
        return pn.pane.Markdown("*No data for this selection*")

    return pn.Column(*sections)


def build(data: DashboardData) -> pn.Column:
    """Build the task drilldown tab."""
    tasks = data.tasks_df
    if tasks.empty:
        return pn.Column(pn.pane.Markdown("## No data"))

    task_ids = sorted(tasks["task_id"].unique())
    models = sorted(tasks["model"].unique())

    # Metric toggle
    metric_select = pn.widgets.RadioButtonGroup(
        name="Metric", options=["ct", "ac"], value="ct",
    )

    # Task and model selectors for detail panels
    task_select = pn.widgets.Select(
        name="Task", options=task_ids, value=task_ids[0],
    )
    model_select = pn.widgets.Select(
        name="Model", options=models, value=models[0],
    )

    # Reactive panels
    heatmap_pane = pn.Column(_task_heatmap(data, "ct"))
    cap_matrix_pane = pn.Column(_capability_matrix(data, task_ids[0]))
    rationale_pane = pn.Column(_rationale_viewer(data, task_ids[0], models[0]))

    def on_metric_change(event):
        heatmap_pane.clear()
        heatmap_pane.append(_task_heatmap(data, event.new))

    def on_task_change(event):
        cap_matrix_pane.clear()
        cap_matrix_pane.append(_capability_matrix(data, event.new))
        rationale_pane.clear()
        rationale_pane.append(_rationale_viewer(data, event.new, model_select.value))

    def on_model_change(event):
        rationale_pane.clear()
        rationale_pane.append(_rationale_viewer(data, task_select.value, event.new))

    metric_select.param.watch(on_metric_change, "value")
    task_select.param.watch(on_task_change, "value")
    model_select.param.watch(on_model_change, "value")

    return pn.Column(
        pn.pane.Markdown("## Task Deep Dive"),
        pn.Row(pn.pane.Markdown("**Heatmap metric:**"), metric_select),
        heatmap_pane,
        pn.layout.Divider(),
        pn.Row(task_select, model_select),
        cap_matrix_pane,
        pn.layout.Divider(),
        pn.pane.Markdown("### Verdict Rationale"),
        rationale_pane,
    )
