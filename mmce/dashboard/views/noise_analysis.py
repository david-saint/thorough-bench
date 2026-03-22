"""Tab 5: Noise Analysis — class breakdown + instance table."""

from __future__ import annotations

import panel as pn
import pandas as pd
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure

from mmce.dashboard.data_loader import DashboardData

_NOISE_COLORS = {
    "false_uncertainty": "#ef4444",
    "performative_hedging": "#f59e0b",
    "unnecessary_clarification": "#3b82f6",
    "hallucinated_risk": "#8b5cf6",
    "redundant_restatement": "#6b7280",
    "audit_theater": "#ec4899",
}

_ALL_CLASSES = list(_NOISE_COLORS.keys())


def _noise_class_breakdown(data: DashboardData) -> pn.pane.Bokeh:
    """Stacked bar: noise weight by class per model."""
    noise = data.noise_df.copy()
    if noise.empty:
        return pn.pane.Markdown("*No noise instances recorded*")

    agg = (
        noise.groupby(["model", "noise_class"])["weight"]
        .sum()
        .unstack(fill_value=0)
    )

    # Ensure all classes present
    for cls in _ALL_CLASSES:
        if cls not in agg.columns:
            agg[cls] = 0.0

    models = list(agg.index)

    # Precompute cumulative bottom/top columns for stacking
    source_data: dict[str, list] = {"models": models}
    cumulative = [0.0] * len(models)
    for cls in _ALL_CLASSES:
        vals = agg[cls].tolist()
        source_data[f"{cls}_bottom"] = list(cumulative)
        cumulative = [b + v for b, v in zip(cumulative, vals)]
        source_data[f"{cls}_top"] = list(cumulative)
        source_data[cls] = vals

    source = ColumnDataSource(source_data)

    p = figure(
        title="Noise Class Breakdown by Model",
        x_range=models,
        y_axis_label="Total Noise Weight",
        width=600, height=350,
        tools="hover,reset",
        tooltips="$name: @$name{0.0}",
    )

    for cls in _ALL_CLASSES:
        p.vbar(
            x="models",
            top=f"{cls}_top",
            bottom=f"{cls}_bottom",
            source=source,
            width=0.7,
            color=_NOISE_COLORS[cls],
            alpha=0.85,
            legend_label=cls.replace("_", " "),
            name=cls,
        )

    p.y_range.start = 0
    p.legend.location = "top_right"
    p.legend.label_text_font_size = "8pt"

    return pn.pane.Bokeh(p)


def _noise_instance_table(data: DashboardData) -> pn.Column:
    """Filterable table of all noise instances."""
    noise = data.noise_df.copy()
    if noise.empty:
        return pn.pane.Markdown("*No noise instances recorded*")

    display = noise[["model", "task_id", "noise_class", "description", "weight"]].copy()
    display = display.rename(columns={
        "model": "Model",
        "task_id": "Task",
        "noise_class": "Class",
        "description": "Description",
        "weight": "Weight",
    })

    # Filters
    model_filter = pn.widgets.MultiChoice(
        name="Filter by Model",
        options=sorted(noise["model"].unique().tolist()),
        value=[],
    )
    class_filter = pn.widgets.MultiChoice(
        name="Filter by Noise Class",
        options=sorted(noise["noise_class"].unique().tolist()),
        value=[],
    )

    table = pn.widgets.Tabulator(
        display,
        layout="fit_data_stretch",
        height=350,
        show_index=False,
        header_filters={
            "Model": {"type": "list", "valuesLookup": True},
            "Class": {"type": "list", "valuesLookup": True},
        },
        widths={"Description": 400},
    )

    return pn.Column(
        pn.pane.Markdown("### Noise Instance Details"),
        table,
    )


def build(data: DashboardData) -> pn.Column:
    """Build the noise analysis tab."""
    return pn.Column(
        pn.pane.Markdown("## Noise Analysis"),
        pn.pane.Markdown(
            "*Noise penalizes false, alarmist, or irrelevant warnings. "
            "Lower is better. Six classes: false uncertainty, performative hedging, "
            "unnecessary clarification, hallucinated risk, redundant restatement, audit theater.*"
        ),
        _noise_class_breakdown(data),
        pn.layout.Divider(),
        _noise_instance_table(data),
    )
