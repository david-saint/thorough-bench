"""Tab 2: Model Comparison — AC/CT scatter, CT/NI quadrant, gap bars."""

from __future__ import annotations

import panel as pn
import pandas as pd
from bokeh.models import ColumnDataSource, HoverTool, Label, Slope, Span
from bokeh.palettes import Category10_10
from bokeh.plotting import figure

from mmce.dashboard.data_loader import DashboardData

# Consistent model -> color mapping
_PALETTE = Category10_10


def _model_colors(models: list[str]) -> dict[str, str]:
    return {m: _PALETTE[i % len(_PALETTE)] for i, m in enumerate(sorted(models))}


def _ac_ct_scatter(data: DashboardData) -> pn.pane.Bokeh:
    """Chart A: Composite AC vs Composite CT scatter."""
    df = data.runs_df.copy()
    if df.empty:
        return pn.pane.Markdown("No data")

    # Add refusal rate if available in tasks_df
    tasks = data.tasks_df.copy()
    if not tasks.empty and "refusal" in tasks.columns:
        ref_rates = tasks.groupby("model")["refusal"].mean().reset_index(name="ref_rate")
        df = df.merge(ref_rates, on="model", how="left")
        df["ref_rate"] = df["ref_rate"].fillna(0)
    else:
        df["ref_rate"] = 0.0

    colors = _model_colors(df["model"].tolist())
    df["color"] = df["model"].map(colors)
    df["gap"] = (df["composite_ct"] - df["composite_ac"]).round(3)

    source = ColumnDataSource(df)

    p = figure(
        title="AC vs CT — Capability Profile",
        x_axis_label="Composite AC (capability × thoroughness)",
        y_axis_label="Composite CT (pure thoroughness)",
        width=500, height=400,
        tools="pan,wheel_zoom,reset",
        x_range=(-0.05, 1.05), y_range=(-0.05, 1.05),
    )

    # Diagonal reference line: y = x
    p.add_layout(Slope(gradient=1, y_intercept=0,
                       line_color="gray", line_dash="dashed", line_alpha=0.5))

    p.scatter(
        "composite_ac", "composite_ct",
        source=source,
        size=14,
        color="color",
        alpha=0.8,
        legend_field="model",
    )

    p.add_tools(HoverTool(tooltips=[
        ("Model", "@model"),
        ("AC", "@composite_ac{0.000}"),
        ("CT", "@composite_ct{0.000}"),
        ("Gap", "@gap{0.000}"),
        ("Refusals", "@ref_rate{0.0%}"),
    ]))

    p.legend.location = "top_left"
    p.legend.label_text_font_size = "9pt"

    # Annotation
    p.add_layout(Label(
        x=0.6, y=0.15,
        text="On diagonal = all controls pass",
        text_font_size="9pt", text_color="gray",
    ))
    p.add_layout(Label(
        x=0.05, y=0.85,
        text="Above = capability gaps inflate CT",
        text_font_size="9pt", text_color="gray",
    ))

    return pn.pane.Bokeh(p)


def _ct_ni_quadrant(data: DashboardData) -> pn.pane.Bokeh:
    """Chart B: CT vs NI quadrant chart."""
    runs = data.runs_df.copy()
    tasks = data.tasks_df.copy()

    if runs.empty or tasks.empty:
        return pn.pane.Markdown("No data")

    # Compute average NI per model run
    avg_ni = tasks.groupby(["run_id", "model"])["ni"].mean().reset_index()
    avg_ni.columns = ["run_id", "model", "avg_ni"]
    df = runs.merge(avg_ni, on=["run_id", "model"])

    colors = _model_colors(df["model"].tolist())
    df["color"] = df["model"].map(colors)

    source = ColumnDataSource(df)

    max_ni = max(df["avg_ni"].max() * 1.2, 0.5)

    p = figure(
        title="CT vs NI — Thoroughness Quality",
        x_axis_label="Average Noise Index (lower = better)",
        y_axis_label="Composite CT (higher = better)",
        width=500, height=400,
        tools="pan,wheel_zoom,reset",
        x_range=(-0.02, max_ni), y_range=(-0.05, 1.05),
    )

    # Quadrant dividers at medians
    med_ct = df["composite_ct"].median()
    med_ni = df["avg_ni"].median()

    p.add_layout(Span(location=med_ct, dimension="width",
                       line_color="gray", line_dash="dotted", line_alpha=0.5))
    p.add_layout(Span(location=med_ni, dimension="height",
                       line_color="gray", line_dash="dotted", line_alpha=0.5))

    p.scatter(
        "avg_ni", "composite_ct",
        source=source,
        size=14,
        color="color",
        alpha=0.8,
        legend_field="model",
    )

    p.add_tools(HoverTool(tooltips=[
        ("Model", "@model"),
        ("CT", "@composite_ct{0.000}"),
        ("Avg NI", "@avg_ni{0.000}"),
    ]))

    # Quadrant labels
    p.add_layout(Label(x=0.01, y=0.95, text="Thorough + Quiet",
                        text_font_size="10pt", text_color="#22c55e", text_font_style="bold"))
    p.add_layout(Label(x=max_ni * 0.55, y=0.95, text="Thorough but Noisy",
                        text_font_size="10pt", text_color="#f59e0b", text_font_style="bold"))
    p.add_layout(Label(x=0.01, y=0.02, text="Lazy + Quiet",
                        text_font_size="10pt", text_color="#6b7280"))
    p.add_layout(Label(x=max_ni * 0.55, y=0.02, text="Noisy + Lazy",
                        text_font_size="10pt", text_color="#ef4444", text_font_style="bold"))

    p.legend.location = "top_right"
    p.legend.label_text_font_size = "9pt"

    return pn.pane.Bokeh(p)


def _ac_cap_scatter(data: DashboardData) -> pn.pane.Bokeh:
    """Chart C: AC vs Base Capability scatter."""
    df = data.runs_df.copy()
    if df.empty:
        return pn.pane.Markdown("No data")

    colors = _model_colors(df["model"].tolist())
    df["color"] = df["model"].map(colors)
    # cap = AC / CT
    df["cap"] = df.apply(lambda r: r["composite_ac"] / r["composite_ct"] if r["composite_ct"] > 0 else 0, axis=1)

    source = ColumnDataSource(df)

    p = figure(
        title="Complex Score vs Base Capability",
        x_axis_label="Base Capability (AC / CT)",
        y_axis_label="Absolute Coverage (AC)",
        width=500, height=400,
        tools="pan,wheel_zoom,reset",
        x_range=(-0.05, 1.05), y_range=(-0.05, 1.05),
    )

    # Median line
    med_cap = df["cap"].median()
    p.add_layout(Span(location=med_cap, dimension="height",
                       line_color="gray", line_dash="dashed", line_alpha=0.5))

    p.scatter(
        "cap", "composite_ac",
        source=source,
        size=14,
        color="color",
        alpha=0.8,
        legend_field="model",
    )

    p.add_tools(HoverTool(tooltips=[
        ("Model", "@model"),
        ("AC", "@composite_ac{0.000}"),
        ("Capability", "@cap{0.000}"),
    ]))

    p.legend.location = "top_left"
    p.legend.label_text_font_size = "9pt"

    return pn.pane.Bokeh(p)


def _capability_bars(data: DashboardData) -> pn.pane.Bokeh:
    """Chart D: Base Capability (AC/CT) horizontal bars."""
    df = data.runs_df.copy()
    if df.empty:
        return pn.pane.Markdown("No data")

    df["cap"] = df.apply(lambda r: r["composite_ac"] / r["composite_ct"] if r["composite_ct"] > 0 else 0, axis=1)
    df = df.sort_values("cap", ascending=False).reset_index(drop=True)

    colors = _model_colors(df["model"].tolist())
    df["color"] = df["model"].map(colors)

    source = ColumnDataSource(df)

    p = figure(
        title="Base Capability Ranking (AC / CT)",
        x_axis_label="Capability Score (1.0 = handles all concepts in isolation)",
        y_range=df["model"].tolist()[::-1],  # Reverse for descending order
        width=1000, height=400,
        tools="pan,wheel_zoom,reset",
        x_range=(-0.02, 1.05),
    )

    p.hbar(
        y="model", right="cap",
        source=source,
        height=0.6,
        color="color",
        alpha=0.8,
    )

    p.add_tools(HoverTool(tooltips=[
        ("Model", "@model"),
        ("Capability", "@cap{0.000}"),
        ("AC", "@composite_ac{0.000}"),
        ("CT", "@composite_ct{0.000}"),
    ]))

    return pn.pane.Bokeh(p)


def _gap_bars(data: DashboardData) -> pn.pane.Bokeh:
    """Chart E: Thoroughness Gap horizontal bars."""
    df = data.runs_df.copy()
    if df.empty:
        return pn.pane.Markdown("No data")

    df["gap"] = df["composite_ct"] - df["composite_ac"]
    df = df.sort_values("gap", ascending=True).reset_index(drop=True)

    colors = _model_colors(df["model"].tolist())
    df["color"] = df["model"].map(colors)

    source = ColumnDataSource(df)

    p = figure(
        title="Thoroughness Gap (CT − AC)",
        x_axis_label="Gap (positive = unrealized capability)",
        y_range=df["model"].tolist(),
        width=500, height=300,
        tools="pan,wheel_zoom,reset",
    )

    p.hbar(
        y="model", right="gap",
        source=source,
        height=0.6,
        color="color",
        alpha=0.8,
    )

    p.add_tools(HoverTool(tooltips=[
        ("Model", "@model"),
        ("Gap", "@gap{0.000}"),
        ("CT", "@composite_ct{0.000}"),
        ("AC", "@composite_ac{0.000}"),
    ]))

    # Zero reference line
    p.add_layout(Span(location=0, dimension="height",
                       line_color="gray", line_dash="dashed", line_alpha=0.5))

    return pn.pane.Bokeh(p)


def _strategy_bias_bars(data: DashboardData) -> pn.pane.Bokeh:
    """Chart F: Strategy Bias Profile (Steamrolling) for Fork tasks."""
    df = data.items_df.copy()
    if df.empty or "dimension" not in df.columns:
        return pn.pane.Markdown("No data")

    fork_df = df[df["dimension"] == "fork"].copy()
    if fork_df.empty:
        return pn.pane.Markdown("No fork data")

    # group by model and execution_score to get counts
    counts = fork_df.groupby(["model", "execution_score"]).size().unstack(fill_value=0)
    
    # Calculate percentages
    totals = counts.sum(axis=1)
    # Handle possible missing score columns safely
    asked = counts.get(1.0, 0) / totals * 100
    wasteful = counts.get(0.5, 0) / totals * 100
    steamrolled = counts.get(0.0, 0) / totals * 100
    
    plot_df = pd.DataFrame({
        "model": counts.index,
        "Asked": asked,
        "Wasteful": wasteful,
        "Steamrolled": steamrolled,
    }).reset_index(drop=True)

    source = ColumnDataSource(plot_df)
    categories = ["Asked", "Wasteful", "Steamrolled"]
    colors = ["#22c55e", "#f59e0b", "#ef4444"]

    p = figure(
        title="Strategy Bias Profile: Disambiguation",
        x_axis_label="Percentage of Fork Items (%)",
        y_range=plot_df["model"].tolist()[::-1],
        width=1000, height=400,
        tools="pan,wheel_zoom,reset",
        x_range=(-0.5, 100.5),
    )

    p.hbar_stack(
        categories, y="model", height=0.6, color=colors, source=source,
        legend_label=["Asked (Safe)", "Wasteful Friction", "Steamrolled (Assumption)"]
    )

    p.add_tools(HoverTool(tooltips=[
        ("Model", "@model"),
        ("Asked", "@Asked{0.1f}%"),
        ("Wasteful", "@Wasteful{0.1f}%"),
        ("Steamrolled", "@Steamrolled{0.1f}%"),
    ]))

    p.legend.location = "top_right"
    p.legend.orientation = "horizontal"

    return pn.pane.Bokeh(p)


def build(data: DashboardData) -> pn.Column:
    """Build the model comparison tab."""
    return pn.Column(
        pn.pane.Markdown("## Model Comparison"),
        pn.Row(
            _ac_ct_scatter(data),
            _ac_cap_scatter(data),
        ),
        pn.Row(
            _ct_ni_quadrant(data),
            _gap_bars(data),
        ),
        _capability_bars(data),
        _strategy_bias_bars(data),
    )
