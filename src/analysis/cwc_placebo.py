"""Club World Cup 2025 placebo — a same-units regression-to-mean baseline.

CWC 2025 (US, 14 Jun – 13 Jul 2025) ran in the same summer heat as WC2026 and its
momentum comes from the SAME FotMob scale, so windowing at the nominal 22'/67' marks
— where no *mandated* break existed — gives a regression-to-the-mean baseline that is
DIRECTLY comparable to the 2026 hydration effect (unlike the 2022 StatsBomb xT-proxy
placebo, which is in different units). CWC 2025 cooling breaks were sparse and
heat-triggered (typically ~30'/75'), so the 22'/67' marks are dominated by no-break
cases — a clean placebo.

Raw is cached in a SEPARATE dir (data/raw/fotmob_cwc2025/) so the WC2026 daily build
never ingests these matches. Occasional build via `pipeline --cwc-placebo`.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import polars as pl

from src.analysis.descriptive import cluster_bootstrap_ci, on_top_rows
from src.analysis.placebo import _placebo_stoppage
from src.features.momentum_features import COLUMNS, WINDOW_MIN, expand_stoppage_rows
from src.paths import RAW
from src.scrape import fotmob

CWC_2025_PRIMARY_ID = 78
PLACEBO_MINUTES = (22.0, 67.0)
RAW_CWC = RAW / "fotmob_cwc2025"
_START, _END = date(2025, 6, 14), date(2025, 7, 13)


def discover_cwc2025_ids(client=None) -> list[str]:
    client = client or fotmob.make_client()
    ids: set[str] = set()
    d = _START
    while d <= _END:
        for e in fotmob.list_competition_events(d.strftime("%Y%m%d"), CWC_2025_PRIMARY_ID, client=client):
            if e.get("id"):
                ids.add(str(e["id"]))
        d += timedelta(days=1)
    return sorted(ids)


def build_cwc_placebo_table(match_ids: list[str] | None = None, minutes=PLACEBO_MINUTES) -> pl.DataFrame:
    client = fotmob.make_client()
    ids = match_ids if match_ids is not None else discover_cwc2025_ids(client)
    rows: list[dict[str, Any]] = []
    for mid in ids:
        details = fotmob.fetch_match_details(mid, client=client, dest_dir=RAW_CWC)
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


def summarize_cwc_placebo(df: pl.DataFrame, **boot_kw) -> dict[str, Any]:
    top = on_top_rows(df)
    if top.is_empty():
        return {"mean": None, "ci_lo": None, "ci_hi": None, "n": 0, "n_matches": 0}
    mean, lo, hi = cluster_bootstrap_ci(top, **boot_kw)
    return {"mean": mean, "ci_lo": lo, "ci_hi": hi, "n": top.height, "n_matches": top["match_id"].n_unique()}
