"""Static (matplotlib/mplsoccer) publication counterparts to the plotly charts.

These mirror `src/viz/charts.py` (the interactive web figures) but render PNGs
suitable for a LinkedIn/portfolio post or a PDF appendix. Colours and framing are
kept in sync with the plotly versions for a consistent look across the report.

Entry point: `save_static_charts(df, out_dir=None) -> list[str]` renders the PNGs
and returns their paths. It degrades gracefully on small-N / empty input
(renders a labelled placeholder rather than crashing), so it is safe to call
early in the tournament when the dataset is thin.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: never try to open a window (CI / Task Scheduler)
import matplotlib.pyplot as plt  # noqa: E402
import polars as pl  # noqa: E402

from src.analysis.descriptive import effect_by_type, on_top_rows  # noqa: E402
from src.paths import SITE  # noqa: E402

# Same colour map as src/viz/charts.py so static and interactive figures match.
COLORS = {
    "hydration": "#0072B2",
    "var": "#E69F00",
    "injury_huddle": "#009E73",
    "injury_no_huddle": "#56B4E9",
    "other": "#999999",
}
_FALLBACK = "#999999"
_ZERO_LINE = "#555555"

DPI = 150


def _color(stype: str) -> str:
    return COLORS.get(stype, _FALLBACK)


def _placeholder(ax: plt.Axes, message: str) -> None:
    """Render an empty axes with a centred caveat message (small/empty-N case)."""
    ax.text(
        0.5,
        0.5,
        message,
        ha="center",
        va="center",
        wrap=True,
        fontsize=12,
        color="#555555",
        transform=ax.transAxes,
    )
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def effect_chart(effects: list[dict], ax: plt.Axes | None = None) -> plt.Figure:
    """Mean momentum delta (team that was on top) by stoppage type, with 95% CIs.

    Static counterpart to `charts.effect_chart`. Bars whose CI crosses zero are
    not distinguishable from "no effect".
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.5, 4.6))
    else:
        fig = ax.figure

    effects = [e for e in effects if e.get("n", 0) > 0 and e.get("mean_delta") == e.get("mean_delta")]
    if not effects:
        _placeholder(ax, "No on-top stoppages yet —\nnothing to estimate.")
        ax.set_title("Momentum change after a stoppage — for the team that was on top")
        return fig

    labels = [e["stoppage_type"] for e in effects]
    means = [e["mean_delta"] for e in effects]
    err_lo = [max(0.0, e["mean_delta"] - e["ci_lo"]) for e in effects]
    err_hi = [max(0.0, e["ci_hi"] - e["mean_delta"]) for e in effects]
    colors = [_color(t) for t in labels]

    x = range(len(labels))
    ax.bar(x, means, color=colors, width=0.6, zorder=2)
    ax.errorbar(
        x,
        means,
        yerr=[err_lo, err_hi],
        fmt="none",
        ecolor="#333333",
        elinewidth=1.4,
        capsize=5,
        zorder=3,
    )
    ax.axhline(0, linestyle=":", color=_ZERO_LINE, linewidth=1, zorder=1)

    # annotate n above/below each bar depending on sign
    for xi, e in zip(x, effects):
        top = e["ci_hi"] if e["mean_delta"] >= 0 else e["mean_delta"]
        ax.annotate(
            f"n={e['n']}",
            (xi, top),
            textcoords="offset points",
            xytext=(0, 4),
            ha="center",
            fontsize=9,
            color="#444444",
        )

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylabel("Mean momentum delta (post − pre, 5-min windows)")
    ax.set_xlabel("Stoppage type")
    ax.set_title("Momentum change after a stoppage — for the team that was on top")
    ax.margins(y=0.18)
    fig.tight_layout()
    return fig


def distribution_chart(df: pl.DataFrame, ax: plt.Axes | None = None) -> plt.Figure:
    """Distribution (box + strip) of on-top momentum delta by stoppage type.

    Static counterpart to `charts.distribution_chart`. The spread matters, not
    just the point estimate — a few extreme matches can move an average.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.5, 4.6))
    else:
        fig = ax.figure

    top = on_top_rows(df) if df is not None and df.height else pl.DataFrame()
    types = sorted(top["stoppage_type"].unique().to_list()) if top.height else []
    series = {t: top.filter(pl.col("stoppage_type") == t)["momentum_delta"].to_list() for t in types}
    series = {t: v for t, v in series.items() if v}

    if not series:
        _placeholder(ax, "No on-top stoppages yet —\nno distribution to show.")
        ax.set_title("Distribution of momentum delta by stoppage type (team on top)")
        return fig

    labels = list(series.keys())
    data = [series[t] for t in labels]
    positions = range(1, len(labels) + 1)

    bp = ax.boxplot(
        data,
        positions=list(positions),
        widths=0.55,
        patch_artist=True,
        showfliers=False,
        medianprops=dict(color="#222222", linewidth=1.4),
        whiskerprops=dict(color="#666666"),
        capprops=dict(color="#666666"),
    )
    for patch, t in zip(bp["boxes"], labels):
        patch.set_facecolor(_color(t))
        patch.set_alpha(0.35)
        patch.set_edgecolor(_color(t))

    # overlay all points (boxpoints="all" equivalent), jittered
    import numpy as np

    rng = np.random.default_rng(7)
    for pos, t in zip(positions, labels):
        vals = series[t]
        jitter = rng.uniform(-0.12, 0.12, size=len(vals))
        ax.scatter(
            [pos + j for j in jitter],
            vals,
            color=_color(t),
            edgecolors="white",
            linewidths=0.4,
            s=28,
            alpha=0.9,
            zorder=3,
        )

    ax.axhline(0, linestyle=":", color=_ZERO_LINE, linewidth=1, zorder=1)
    ax.set_xticks(list(positions))
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylabel("Momentum delta")
    ax.set_title("Distribution of momentum delta by stoppage type (team on top)")
    fig.tight_layout()
    return fig


def momentum_timeline_chart(df: pl.DataFrame, ax: plt.Axes | None = None) -> plt.Figure:
    """Optional strip: per-stoppage pre vs post on-top momentum, ordered by clock.

    A compact "before/after" view — each on-top stoppage is a vertical segment
    from its pre-window mean to its post-window mean, coloured by type. Adds value
    by making the *direction* of each individual shift visible (not just the
    aggregate), which the bar/box charts hide.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.5, 4.2))
    else:
        fig = ax.figure

    top = on_top_rows(df) if df is not None and df.height else pl.DataFrame()
    needed = {"clock_minute", "momentum_pre_5min_mean", "momentum_post_5min_mean", "stoppage_type"}
    if not top.height or not needed.issubset(set(top.columns)):
        _placeholder(ax, "No on-top stoppages yet —\nno timeline to show.")
        ax.set_title("Per-stoppage momentum shift (team on top)")
        return fig

    rows = (
        top.select(["clock_minute", "momentum_pre_5min_mean", "momentum_post_5min_mean", "stoppage_type"])
        .drop_nulls()
        .sort("clock_minute")
    )
    if not rows.height:
        _placeholder(ax, "No on-top stoppages yet —\nno timeline to show.")
        ax.set_title("Per-stoppage momentum shift (team on top)")
        return fig

    seen: set[str] = set()
    for r in rows.iter_rows(named=True):
        x = r["clock_minute"]
        pre = r["momentum_pre_5min_mean"]
        post = r["momentum_post_5min_mean"]
        t = r["stoppage_type"]
        label = t if t not in seen else None
        seen.add(t)
        ax.plot([x, x], [pre, post], color=_color(t), linewidth=2, alpha=0.8, zorder=2)
        ax.scatter([x], [pre], color="white", edgecolors=_color(t), linewidths=1.4, s=30, zorder=3)
        ax.scatter([x], [post], color=_color(t), s=42, zorder=3, label=label)

    ax.axhline(0, linestyle=":", color=_ZERO_LINE, linewidth=1, zorder=1)
    ax.set_xlabel("Clock minute of stoppage")
    ax.set_ylabel("Momentum (open = pre, filled = post)")
    ax.set_title("Per-stoppage momentum shift (team on top)")
    ax.legend(title="Stoppage type", fontsize=8, loc="best", framealpha=0.9)
    fig.tight_layout()
    return fig


def save_static_charts(df: pl.DataFrame, out_dir: str | Path | None = None) -> list[str]:
    """Render the static publication PNGs and return their paths.

    Renders into `out_dir` (default `SITE / "figures"`, gitignored). Never raises
    on small-N / empty input — each chart falls back to a labelled placeholder.

    Returns the list of written PNG paths (as strings) in a stable order:
        [effect_by_type.png, distribution.png, momentum_timeline.png]
    """
    out = Path(out_dir) if out_dir is not None else (SITE / "figures")
    out.mkdir(parents=True, exist_ok=True)

    if df is None:
        df = pl.DataFrame()

    try:
        effects = effect_by_type(df) if df.height else []
    except Exception:
        effects = []

    paths: list[str] = []
    builders = [
        ("effect_by_type.png", lambda: effect_chart(effects)),
        ("distribution.png", lambda: distribution_chart(df)),
        ("momentum_timeline.png", lambda: momentum_timeline_chart(df)),
    ]
    for name, build in builders:
        fig = build()
        dest = out / name
        fig.savefig(dest, dpi=DPI, bbox_inches="tight")
        plt.close(fig)
        paths.append(str(dest))

    return paths
