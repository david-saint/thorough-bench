"""Tab 4: Dimension Analysis — Fork execution score dist + Guardian severity rates."""

from __future__ import annotations

import panel as pn
import pandas as pd
from bokeh.models import ColumnDataSource, HoverTool, FactorRange
from bokeh.palettes import Category10_4
from bokeh.plotting import figure
from bokeh.transform import dodge

from mmce.dashboard.data_loader import DashboardData


def _fork_execution_score_dist(data: DashboardData) -> pn.pane.Bokeh:
    """Stacked bar: proportion of fork items at each execution_score per model."""
    items = data.items_df[data.items_df["dimension"] == "fork"].copy()
    if items.empty:
        return pn.pane.Markdown("*No fork data*")

    # Count items at each score tier per model
    items["score_tier"] = items["execution_score"].map({
        1.0: "1.0 (Visible)",
        0.5: "0.5 (Wasteful)",
        0.0: "0.0 (Silent)",
    })

    counts = (
        items.groupby(["model", "score_tier"])
        .size()
        .unstack(fill_value=0)
    )

    # Ensure all tiers present
    for tier in ["1.0 (Visible)", "0.5 (Wasteful)", "0.0 (Silent)"]:
        if tier not in counts.columns:
            counts[tier] = 0

    # Convert to proportions
    totals = counts.sum(axis=1)
    props = counts.div(totals, axis=0)

    models = list(props.index)
    tiers = ["1.0 (Visible)", "0.5 (Wasteful)", "0.0 (Silent)"]
    colors = ["#22c55e", "#f59e0b", "#ef4444"]

    # Precompute cumulative bottom/top columns for stacking
    source_data: dict[str, list] = {"models": models}
    cumulative = [0.0] * len(models)
    for tier in tiers:
        vals = props[tier].tolist()
        source_data[f"{tier}_bottom"] = list(cumulative)
        cumulative = [b + v for b, v in zip(cumulative, vals)]
        source_data[f"{tier}_top"] = list(cumulative)
        source_data[tier] = vals

    source = ColumnDataSource(source_data)

    p = figure(
        title="Fork: Execution Score Distribution",
        x_range=models,
        y_axis_label="Proportion of Items",
        width=500, height=350,
        tools="hover,reset",
        tooltips="$name: @$name{0.0%}",
    )

    for tier, color in zip(tiers, colors):
        p.vbar(
            x="models", top=f"{tier}_top",
            bottom=f"{tier}_bottom",
            source=source,
            width=0.7, color=color, alpha=0.85,
            legend_label=tier, name=tier,
        )

    p.y_range.start = 0
    p.y_range.end = 1.05
    p.legend.location = "top_right"
    p.legend.label_text_font_size = "9pt"

    return pn.pane.Bokeh(p)


def _fork_blocking_performance(data: DashboardData) -> pn.pane.Bokeh:
    """Grouped bar: avg execution_score on blocking vs non-blocking axes."""
    items = data.items_df[data.items_df["dimension"] == "fork"].copy()
    if items.empty or "blocking" not in items.columns:
        return pn.pane.Markdown("*No fork blocking data*")

    items["blocking_label"] = items["blocking"].map({True: "Blocking", False: "Non-Blocking"})

    agg = (
        items.groupby(["model", "blocking_label"])["execution_score"]
        .mean()
        .unstack(fill_value=0)
    )

    models = list(agg.index)

    blocking_vals = agg.get("Blocking", pd.Series([0] * len(models), index=models)).tolist()
    non_blocking_vals = agg.get("Non-Blocking", pd.Series([0] * len(models), index=models)).tolist()

    source = ColumnDataSource({
        "models": models,
        "Blocking": blocking_vals,
        "Non-Blocking": non_blocking_vals,
    })

    p = figure(
        title="Fork: Blocking vs Non-Blocking Performance",
        x_range=models,
        y_axis_label="Avg Execution Score",
        width=500, height=350,
        tools="hover,reset",
        tooltips=[("Model", "@models"), ("Blocking", "@Blocking{0.00}"), ("Non-Blocking", "@{Non-Blocking}{0.00}")],
    )

    p.vbar(x=dodge("models", -0.15, range=p.x_range), top="Blocking",
           source=source, width=0.25, color="#ef4444", alpha=0.85, legend_label="Blocking")
    p.vbar(x=dodge("models", 0.15, range=p.x_range), top="Non-Blocking",
           source=source, width=0.25, color="#3b82f6", alpha=0.85, legend_label="Non-Blocking")

    p.y_range.start = 0
    p.y_range.end = 1.1
    p.legend.location = "top_right"
    p.legend.label_text_font_size = "9pt"

    return pn.pane.Bokeh(p)


def _guardian_severity_rates(data: DashboardData) -> pn.pane.Bokeh:
    """Grouped bar: detection rate by severity per model."""
    items = data.items_df[data.items_df["dimension"] == "guardian"].copy()
    if items.empty:
        return pn.pane.Markdown("*No guardian data*")

    items["detected"] = (items["credit"] > 0).astype(int)

    agg = (
        items.groupby(["model", "severity"])["detected"]
        .mean()
        .unstack(fill_value=0)
    )

    models = list(agg.index)
    severities = ["critical", "important", "optional"]
    sev_colors = {"critical": "#ef4444", "important": "#f59e0b", "optional": "#6b7280"}

    source_data = {"models": models}
    for sev in severities:
        source_data[sev] = agg.get(sev, pd.Series([0] * len(models), index=models)).tolist()

    source = ColumnDataSource(source_data)

    p = figure(
        title="Guardian: Detection Rate by Severity",
        x_range=models,
        y_axis_label="Detection Rate",
        width=500, height=350,
        tools="hover,reset",
        tooltips=[("Model", "@models"),
                  ("Critical", "@critical{0.0%}"),
                  ("Important", "@important{0.0%}"),
                  ("Optional", "@optional{0.0%}")],
    )

    offsets = {"critical": -0.22, "important": 0.0, "optional": 0.22}
    for sev in severities:
        p.vbar(
            x=dodge("models", offsets[sev], range=p.x_range),
            top=sev, source=source,
            width=0.2, color=sev_colors[sev], alpha=0.85,
            legend_label=sev.capitalize(),
        )

    p.y_range.start = 0
    p.y_range.end = 1.1
    p.legend.location = "top_right"
    p.legend.label_text_font_size = "9pt"

    return pn.pane.Bokeh(p)


def _guardian_flag_heatmap(data: DashboardData) -> pn.pane.Bokeh:
    """Per-flag detection heatmap: rows=flags, cols=models."""
    items = data.items_df[data.items_df["dimension"] == "guardian"].copy()
    if items.empty:
        return pn.pane.Markdown("*No guardian data*")

    items["detected"] = (items["credit"] > 0).astype(int)

    pivot = items.pivot_table(
        index="item_id", columns="model", values="detected", aggfunc="first",
    ).fillna(0)

    flag_ids = list(pivot.index)
    models = list(pivot.columns)

    xs, ys, vals = [], [], []
    for flag in flag_ids:
        for model in models:
            xs.append(model)
            ys.append(flag)
            vals.append(int(pivot.loc[flag, model]))

    colors = ["#ef4444" if v == 0 else "#22c55e" for v in vals]

    source = ColumnDataSource({
        "x": xs, "y": ys, "value": vals,
        "label": ["Detected" if v else "Missed" for v in vals],
        "color": colors,
    })

    p = figure(
        title="Guardian: Per-Flag Detection",
        x_range=models,
        y_range=list(reversed(flag_ids)),
        width=600, height=max(250, len(flag_ids) * 30),
        tools="hover,reset",
        tooltips=[("Flag", "@y"), ("Model", "@x"), ("Status", "@label")],
    )

    p.rect(
        x="x", y="y", width=0.95, height=0.95,
        source=source,
        fill_color="color", line_color="white", line_width=1,
    )

    p.xaxis.major_label_orientation = 0.5

    return pn.pane.Bokeh(p)


def build(data: DashboardData) -> pn.Column:
    """Build the dimension analysis tab."""
    return pn.Column(
        pn.pane.Markdown("## Dimension Analysis"),
        pn.pane.Markdown("### Fork (Uncertainty Monitoring)"),
        pn.pane.Markdown(
            "*How models handle ambiguity: 1.0=visible resolution, "
            "0.5=wasteful clarification, 0.0=silent assumption*"
        ),
        pn.Row(
            _fork_execution_score_dist(data),
            _fork_blocking_performance(data),
        ),
        pn.layout.Divider(),
        pn.pane.Markdown("### Guardian (Knowledge Boundary Detection)"),
        pn.pane.Markdown("*Do models catch critical risks or just easy ones?*"),
        pn.Row(
            _guardian_severity_rates(data),
            _guardian_flag_heatmap(data),
        ),
    )
