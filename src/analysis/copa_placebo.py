"""Copa América 2024 same-units placebo (delegates to fotmob_placebo).

Copa América 2024 (US, 20 Jun – 14 Jul 2024) is the closest no-break analog to WC2026:
NATIONAL teams (not clubs) in the same US summer heat, on the same FotMob momentum scale.
Windowing at 22'/67' (no mandated break there) gives a regression-to-the-mean baseline
directly comparable to the 2026 hydration effect. Raw cached in a SEPARATE dir so the
WC2026 daily build never ingests these matches.
"""

from __future__ import annotations

from datetime import date

import polars as pl

from src.analysis.fotmob_placebo import build_fotmob_placebo, summarize_placebo
from src.paths import RAW

COPA_2024_PRIMARY_ID = 44  # FotMob primaryId for CONMEBOL Copa América
RAW_COPA = RAW / "fotmob_copa2024"


def build_copa_placebo_table(match_ids: list[str] | None = None) -> pl.DataFrame:
    return build_fotmob_placebo(
        COPA_2024_PRIMARY_ID, date(2024, 6, 20), date(2024, 7, 14), RAW_COPA, match_ids=match_ids
    )


def summarize_copa_placebo(df: pl.DataFrame, **boot_kw) -> dict:
    return summarize_placebo(df, **boot_kw)
