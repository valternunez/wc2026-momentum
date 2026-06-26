"""CONCACAF Gold Cup 2025 same-units placebo (delegates to fotmob_placebo).

The Gold Cup 2025 (US/Canada, 14 Jun – 6 Jul 2025) is the closest no-break analog to
WC2026: CONCACAF NATIONAL teams in the same host region and June/July summer heat, many
of them (Mexico, USA, Canada, Panama, Costa Rica…) also WC2026 sides, on the same FotMob
momentum scale. Windowing at 22'/67' (no mandated break there) gives a
regression-to-the-mean baseline directly comparable to the 2026 hydration effect. Raw
cached in a SEPARATE dir so the WC2026 daily build never ingests these matches.

Note: the 2023 edition is intentionally excluded — FotMob carries no per-minute momentum
series for it (0/33 matches), so there is nothing to window.
"""

from __future__ import annotations

from datetime import date

import polars as pl

from src.analysis.fotmob_placebo import build_fotmob_placebo, summarize_placebo
from src.paths import RAW

GOLDCUP_PRIMARY_ID = 298  # FotMob primaryId for the CONCACAF Gold Cup
RAW_GOLDCUP_2025 = RAW / "fotmob_goldcup2025"


def build_goldcup_placebo_table(match_ids: list[str] | None = None) -> pl.DataFrame:
    return build_fotmob_placebo(
        GOLDCUP_PRIMARY_ID, date(2025, 6, 14), date(2025, 7, 6), RAW_GOLDCUP_2025, match_ids=match_ids
    )


def summarize_goldcup_placebo(df: pl.DataFrame, **boot_kw) -> dict:
    return summarize_placebo(df, **boot_kw)
