"""UEFA Euro 2024 same-units placebo (delegates to fotmob_placebo).

Euro 2024 (Germany, 14 Jun – 14 Jul 2024) is European national teams in the same recent era as
WC2026, on the same FotMob momentum scale, with no mandated 22'/67' break. Together with Copa
América 2024 (South American national teams) it tests whether the no-break regression baseline
depends on WHO is playing — and it lands right with the other national-team baselines (~−16).
Raw cached in a SEPARATE dir so the WC2026 daily build never ingests these matches.
"""

from __future__ import annotations

from datetime import date

import polars as pl

from src.analysis.fotmob_placebo import build_fotmob_placebo, summarize_placebo
from src.paths import RAW

EURO_2024_PRIMARY_ID = 50  # FotMob primaryId for the UEFA European Championship (2024 finals window)
RAW_EURO = RAW / "fotmob_euro2024"


def build_euro_placebo_table(match_ids: list[str] | None = None) -> pl.DataFrame:
    return build_fotmob_placebo(
        EURO_2024_PRIMARY_ID, date(2024, 6, 14), date(2024, 7, 14), RAW_EURO, match_ids=match_ids
    )


def summarize_euro_placebo(df: pl.DataFrame, **boot_kw) -> dict:
    return summarize_placebo(df, **boot_kw)
