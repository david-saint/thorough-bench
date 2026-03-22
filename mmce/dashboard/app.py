"""MMCE Thoroughness Dashboard — Panel servable entry point."""

from __future__ import annotations

import panel as pn

from mmce.dashboard.data_loader import DashboardData, get_latest_per_model, load_all_runs
from mmce.dashboard.views import (
    dimension_analysis,
    leaderboard,
    model_comparison,
    noise_analysis,
    task_drilldown,
)

pn.extension("tabulator")


def build_dashboard() -> pn.template.MaterialTemplate:
    """Build the full dashboard template."""
    # Load all data
    full_data = load_all_runs()

    if full_data.runs_df.empty:
        template = pn.template.MaterialTemplate(title="MMCE Dashboard")
        template.main.append(pn.pane.Markdown("## No benchmark results found in mmce/results/"))
        return template

    # Run selector: default to latest per model
    all_run_ids = full_data.runs_df["run_id"].tolist()
    default_runs = get_latest_per_model(full_data.runs_df)

    # Build labels: "model (timestamp, N tasks)"
    run_labels = {}
    for _, row in full_data.runs_df.iterrows():
        label = f"{row['model']} ({row['timestamp']}, {row['n_tasks']} tasks)"
        run_labels[row["run_id"]] = label

    run_selector = pn.widgets.MultiChoice(
        name="Runs",
        options=run_labels,
        value=default_runs,
        width=280,
    )

    # Content area
    content_area = pn.Column()

    def rebuild(event=None):
        selected = run_selector.value or default_runs
        data = full_data.filter_runs(selected)

        content_area.clear()
        content_area.append(
            pn.Tabs(
                ("Leaderboard", leaderboard.build(data)),
                ("Model Comparison", model_comparison.build(data)),
                ("Task Deep Dive", task_drilldown.build(data)),
                ("Dimension Analysis", dimension_analysis.build(data)),
                ("Noise Analysis", noise_analysis.build(data)),
                dynamic=False,
            )
        )

    run_selector.param.watch(rebuild, "value")
    rebuild()  # Initial build

    template = pn.template.MaterialTemplate(
        title="MMCE Thoroughness Dashboard",
        sidebar=[
            pn.pane.Markdown("### Settings"),
            run_selector,
            pn.pane.Markdown(
                "---\n"
                "*Select benchmark runs to include. "
                "Default: latest run per model.*"
            ),
        ],
        main=[content_area],
    )

    return template


# Panel servable entry point
dashboard = build_dashboard()
dashboard.servable()
