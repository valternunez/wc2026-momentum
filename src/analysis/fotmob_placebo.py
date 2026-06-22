"""Generic FotMob same-units placebo builder.

Apply the 22'/67' windowing to any tournament's FotMob momentum (where no mandated
break existed at those marks) to get a regression-to-the-mean baseline in the SAME
scale as the WC2026 hydration effect. Used for both CWC 2025 and WC 2022 so all
no-break baselines are directly comparable to the live −24. Each competition caches
raw in its OWN dir so the daily WC2026 build never ingests them.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

import polars as pl

from src.analysis.descriptive import cluster_bootstrap_ci, on_top_rows
from src.analysis.placebo import _placebo_stoppage
from src.features.momentum_features import COLUMNS, WINDOW_MIN, expand_stoppage_rows
from src.scrape import fotmob

PLACEBO_MINUTES = (22.0, 67.0)


def discover_ids(primary_id: int, start: date, end: date, *, client=None) -> list[str]:
    client = client or fotmob.make_client()
    ids: set[str] = set()
    d = start
    while d <= end:
        for e in fotmob.list_competition_events(d.strftime("%Y%m%d"), primary_id, client=client):
            if e.get("id"):
                ids.add(str(e["id"]))
        d += timedelta(days=1)
    return sorted(ids)


def build_fotmob_placebo(
    primary_id: int, start: date, end: date, raw_dir: Path,
    *, minutes=PLACEBO_MINUTES, match_ids: list[str] | None = None,
) -> pl.DataFrame:
    client = fotmob.make_client()
    ids = match_ids if match_ids is not None else discover_ids(primary_id, start, end, client=client)
    rows: list[dict[str, Any]] = []
    for mid in ids:
        details = fotmob.fetch_match_details(mid, client=client, dest_dir=raw_dir)
        momentum = fotmob.parse_momentum(details)
        if not momentum:
            continue
        meta = fotmob.parse_match_meta(details)
        max_min = max(p["minute"] for p in momentum)
        for i, minute in enumerate(minutes):
            if max_min < minute + WINDOW_MIN:
                continue
            rows.extend(expand_stoppage_rows(meta, _placebo_stoppage(meta["match_id"], i, minute), momentum))
    if not rows:
        return pl.DataFrame(schema={c: pl.Utf8 for c in COLUMNS})
    return pl.DataFrame(rows).select(COLUMNS)


def summarize_placebo(df: pl.DataFrame, **boot_kw) -> dict[str, Any]:
    top = on_top_rows(df)
    if top.is_empty():
        return {"mean": None, "ci_lo": None, "ci_hi": None, "n": 0, "n_matches": 0}
    mean, lo, hi = cluster_bootstrap_ci(top, **boot_kw)
    return {"mean": mean, "ci_lo": lo, "ci_hi": hi, "n": top.height, "n_matches": top["match_id"].n_unique()}
