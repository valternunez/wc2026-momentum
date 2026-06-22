"""Club World Cup 2025 same-units placebo (delegates to fotmob_placebo).

CWC 2025 (US, 14 Jun – 13 Jul 2025) ran in the same summer heat as WC2026 on the same
FotMob momentum scale, so windowing at 22'/67' (no mandated break there) gives a
regression-to-the-mean baseline directly comparable to the 2026 hydration effect.
Raw cached in a SEPARATE dir so the WC2026 daily build never ingests these matches.
"""

from __future__ import annotations

from datetime import date

import polars as pl

from src.analysis.fotmob_placebo import build_fotmob_placebo, summarize_placebo
from src.paths import RAW

CWC_2025_PRIMARY_ID = 78
RAW_CWC = RAW / "fotmob_cwc2025"


def build_cwc_placebo_table(match_ids: list[str] | None = None) -> pl.DataFrame:
    return build_fotmob_placebo(
        CWC_2025_PRIMARY_ID, date(2025, 6, 14), date(2025, 7, 13), RAW_CWC, match_ids=match_ids
    )


def summarize_cwc_placebo(df: pl.DataFrame, **boot_kw) -> dict:
    return summarize_placebo(df, **boot_kw)
