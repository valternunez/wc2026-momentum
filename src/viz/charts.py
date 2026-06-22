"""Plotly chart builders for the report site.

Each function returns a plotly Figure; `src/report/build_site.py` embeds them.
Keep these presentation-only — all numbers come from src/analysis.
"""

from __future__ import annotations

import plotly.graph_objects as go
import polars as pl

# colour the treatment (hydration) distinctly from the comparison stoppages
_COLORS = {
    "hydration": "#0072B2",
    "var": "#E69F00",
    "injury_huddle": "#009E73",
    "injury_no_huddle": "#56B4E9",
    "other": "#999999",
}


def effect_chart(effects: list[dict]) -> go.Figure:
    """Mean momentum delta (team that was on top) by stoppage type, with 95% CIs."""
    effects = [e for e in effects if e["n"] > 0]
    x = [e["stoppage_type"] for e in effects]
    y = [e["mean_delta"] for e in effects]
    err_plus = [e["ci_hi"] - e["mean_delta"] for e in effects]
    err_minus = [e["mean_delta"] - e["ci_lo"] for e in effects]
    fig = go.Figure(
        go.Bar(
            x=x,
            y=y,
            marker_color=[_COLORS.get(t, "#999") for t in x],
            error_y=dict(type="data", symmetric=False, array=err_plus, arrayminus=err_minus),
            text=[f"n={e['n']}" for e in effects],
            textposition="outside",
        )
    )
    fig.add_hline(y=0, line_dash="dot", line_color="#555")
    fig.update_layout(
        title="Momentum change after a stoppage — for the team that was on top",
        yaxis_title="Mean momentum delta (post − pre, 5-min windows)",
        xaxis_title="Stoppage type",
        template="plotly_white",
        height=440,
    )
    return fig


def distribution_chart(df: pl.DataFrame) -> go.Figure:
    """Distribution (not just the point estimate) of on-top momentum delta by type."""
    from src.analysis.descriptive import on_top_rows

    top = on_top_rows(df)
    fig = go.Figure()
    for stype in sorted(top["stoppage_type"].unique().to_list()):
        vals = top.filter(pl.col("stoppage_type") == stype)["momentum_delta"].to_list()
        fig.add_trace(go.Box(y=vals, name=stype, marker_color=_COLORS.get(stype, "#999"), boxpoints="all"))
    fig.add_hline(y=0, line_dash="dot", line_color="#555")
    fig.update_layout(
        title="Distribution of momentum delta by stoppage type (team on top)",
        yaxis_title="Momentum delta",
        template="plotly_white",
        height=440,
        showlegend=False,
    )
    return fig


def trend_chart(snapshots: list[dict], stoppage_type: str = "hydration") -> go.Figure:
    """How the hydration estimate has evolved as N grew (the snapshot time series)."""
    dates, means, ns = [], [], []
    for s in snapshots:
        bt = (s.get("by_type") or {}).get(stoppage_type)
        if bt and bt.get("on_top_mean_delta") is not None:
            dates.append(s.get("date"))
            means.append(bt["on_top_mean_delta"])
            ns.append(bt.get("n_on_top"))
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates, y=means, mode="lines+markers",
            text=[f"n={n}" for n in ns], line_color=_COLORS["hydration"],
        )
    )
    fig.add_hline(y=0, line_dash="dot", line_color="#555")
    fig.update_layout(
        title=f"{stoppage_type.title()} effect estimate over the tournament",
        yaxis_title="On-top mean momentum delta",
        xaxis_title="Snapshot date",
        template="plotly_white",
        height=380,
    )
    return fig
