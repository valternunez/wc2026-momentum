"""Per-match momentum small-multiples grid (static PNG).

One mini chart per scraped match: home-positive momentum over the minutes, with
vertical markers at detected stoppages (hydration emphasised). Generated LOCALLY
because the per-minute momentum series lives only in FotMob raw (gitignored) — we
publish the rendered image, not the underlying values (ToS: derived analysis, not
raw-payload redistribution). Committed to reports/figures/ and embedded by build_site.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import polars as pl  # noqa: E402

from src.paths import RAW_FOTMOB, REPORTS, STOPPAGES_PARQUET  # noqa: E402
from src.scrape import fotmob  # noqa: E402
from src.viz.charts import _COLORS  # noqa: E402

DEFAULT_OUT = REPORTS / "figures" / "per_match_momentum.png"
HOME_COLOR = "#0072B2"
AWAY_COLOR = "#D55E00"
NCOLS = 6

# --- editorial per-match panels (one transparent PNG per match) -------------
MATCHES_DIR = REPORTS / "figures" / "matches"
PANEL_HOME = "#9CC4E0"   # home-on-top fill (blue)
PANEL_AWAY = "#EBC09A"   # away-on-top fill (orange)
MARKER_COLORS = {        # dashed stoppage markers, colour-coded by type
    "hydration": "#3E88C7",
    "var": "#2E8B57",
    "injury_huddle": "#E08A4B",
    "injury_no_huddle": "#E08A4B",
    "other": "#9A927E",
}


def build_match_panels(out_dir: str | Path = MATCHES_DIR, *, match_ids: list[str] | None = None) -> list[str]:
    """Render one transparent editorial momentum panel per match -> <match_id>.png.

    Home-positive momentum filled blue above the zero line / orange below, with
    colour-coded dashed stoppage markers, no axes. Reads FotMob raw + the parquet;
    safe when raw is absent (returns []). Returns the match ids rendered.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ids = match_ids if match_ids is not None else sorted(p.stem for p in RAW_FOTMOB.glob("*.json"))
    df = pl.read_parquet(STOPPAGES_PARQUET) if STOPPAGES_PARQUET.exists() else None

    written: list[str] = []
    for mid in ids:
        raw = fotmob.load_raw(mid)
        if not raw:
            continue
        mom = fotmob.parse_momentum(raw)
        if not mom:
            continue
        xs = [p["minute"] for p in mom]
        ys = [p["value"] for p in mom]

        fig, ax = plt.subplots(figsize=(4.2, 1.45))
        ax.fill_between(xs, ys, 0, where=[y >= 0 for y in ys], color=PANEL_HOME, linewidth=0)
        ax.fill_between(xs, ys, 0, where=[y < 0 for y in ys], color=PANEL_AWAY, linewidth=0)
        ax.axhline(0, color="#1A1813", linewidth=1.1)
        for minute, stype in _markers(df, mid):
            ax.axvline(minute, color=MARKER_COLORS.get(stype, "#9A927E"), linestyle=(0, (4, 3)),
                       linewidth=1.2, alpha=0.95)
        ymax = max((abs(y) for y in ys), default=1) * 1.08
        ax.set_ylim(-ymax, ymax)
        ax.set_xlim(min(xs), max(xs))
        ax.axis("off")
        fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02)
        fig.savefig(out_dir / f"{mid}.png", dpi=150, transparent=True)
        plt.close(fig)
        written.append(mid)
    return written


def _markers(df: pl.DataFrame | None, match_id: str) -> list[tuple[float, str]]:
    if df is None or df.is_empty():
        return []
    sub = df.filter(pl.col("match_id") == match_id).select(["clock_minute", "stoppage_type"]).unique()
    return [(r["clock_minute"], r["stoppage_type"]) for r in sub.to_dicts()]


def build_per_match_grid(out_path: str | Path | None = None, *, match_ids: list[str] | None = None) -> str | None:
    """Render the grid to `out_path`. Returns the path, or None if there's nothing to draw.

    Reads momentum from FotMob raw and stoppage markers from the processed parquet. Safe when raw is
    absent (e.g. in CI) — returns None without raising.
    """
    out_path = Path(out_path or DEFAULT_OUT)
    ids = match_ids if match_ids is not None else sorted(p.stem for p in RAW_FOTMOB.glob("*.json"))
    df = pl.read_parquet(STOPPAGES_PARQUET) if STOPPAGES_PARQUET.exists() else None

    panels = []
    for mid in ids:
        raw = fotmob.load_raw(mid)
        if not raw:
            continue
        mom = fotmob.parse_momentum(raw)
        if not mom:
            continue
        meta = fotmob.parse_match_meta(raw)
        panels.append((mid, meta, mom))
    if not panels:
        return None

    n = len(panels)
    ncols = min(NCOLS, n)
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 2.2, nrows * 1.5), squeeze=False)
    ymax = max(abs(p["value"]) for _, _, mom in panels for p in mom) or 100

    for idx, (mid, meta, mom) in enumerate(panels):
        ax = axes[idx // ncols][idx % ncols]
        xs = [p["minute"] for p in mom]
        ys = [p["value"] for p in mom]
        ax.fill_between(xs, ys, 0, where=[y >= 0 for y in ys], color=HOME_COLOR, alpha=0.5, linewidth=0)
        ax.fill_between(xs, ys, 0, where=[y < 0 for y in ys], color=AWAY_COLOR, alpha=0.5, linewidth=0)
        ax.axhline(0, color="#444", linewidth=0.6)
        for minute, stype in _markers(df, mid):
            ax.axvline(minute, color=_COLORS.get(stype, "#999"), linestyle="--", linewidth=0.9,
                       alpha=0.9 if stype == "hydration" else 0.6)
        ax.set_ylim(-ymax * 1.05, ymax * 1.05)
        ax.set_xlim(0, max(xs))
        title = f"{meta.get('home_team', '?')} v {meta.get('away_team', '?')}"
        ax.set_title(title[:26], fontsize=7)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)

    for j in range(n, nrows * ncols):  # blank unused cells
        axes[j // ncols][j % ncols].axis("off")

    fig.suptitle("Per-match momentum (blue = home on top, orange = away) — dashed lines mark stoppages",
                 fontsize=10, y=0.997)
    fig.tight_layout(rect=(0, 0, 1, 0.99))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return str(out_path)


if __name__ == "__main__":
    print("[per-match]", build_per_match_grid() or "no FotMob raw found — nothing to render")
