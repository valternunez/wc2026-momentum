"""Confounder / context enrichment lane: venue + weather.

Fills the schema columns `dome`, `temp_c`, `humidity`, `wbgt` on the
stoppage-level table (`venue` and `match_date` are populated upstream).

Public API:
  - lookup_venue (re-exported from .venues)
  - get_weather, wbgt (re-exported from .weather)
  - enrich_stoppages: the pipeline entry point.

Kickoff-hour approximation
--------------------------
The data has NO kickoff time, only a date. Weather (and thus heat stress) depends
on the hour, so we assume a single representative LOCAL kickoff hour for every
match and make it a parameter, `kickoff_hour` (default 18 = 6pm local). 18:00 is
a reasonable central estimate for WC2026: many matches are scheduled in the
afternoon/evening local time to suit broadcast windows, and Open-Meteo hourly
data is requested in venue-local time (timezone=auto), so `kickoff_hour` is read
directly as a local clock hour. Tune via the parameter for sensitivity checks.
"""

from __future__ import annotations

import polars as pl

from src.enrich.venues import lookup_venue
from src.enrich.weather import get_weather, wbgt

__all__ = ["lookup_venue", "get_weather", "wbgt", "enrich_stoppages"]


def enrich_stoppages(df: pl.DataFrame, *, kickoff_hour: int = 18) -> pl.DataFrame:
    """Fill `dome`, `temp_c`, `humidity`, `wbgt` from venue + weather lookups.

    For each unique (venue, match_date): look up the venue, fetch weather at
    `kickoff_hour` local, and write the enriched values to every matching row.
    Domed venues still record outdoor weather (for transparency) but always get
    dome=True — the analysis conditions on `dome`, not on temp.

    Resilient by design: an unknown venue or a failed weather fetch leaves that
    group's columns as None and is counted; this never raises. Returns a new
    DataFrame with the four columns overwritten (same shape/row order).

    Args:
        df: stoppage-level table with at least `venue` and `match_date` columns.
        kickoff_hour: assumed LOCAL kickoff hour (see module docstring).
    """
    if df.height == 0:
        return df

    # Unique work units. Drop nulls in the keys; those rows stay None.
    pairs = (
        df.select(["venue", "match_date"])
        .unique()
        .drop_nulls()
        .iter_rows()
    )

    # Map (venue, match_date) -> {dome, temp_c, humidity, wbgt}
    enriched: dict[tuple, dict] = {}
    unknown_venue = 0
    failed_weather = 0

    # One HTTP client reused across all fetches.
    import httpx

    client = httpx.Client(timeout=30)
    try:
        for venue, match_date in pairs:
            v = lookup_venue(venue)
            if v is None:
                unknown_venue += 1
                continue
            vals = {"dome": v["dome"], "temp_c": None, "humidity": None, "wbgt": None}
            try:
                w = get_weather(v["lat"], v["lon"], match_date, hour=kickoff_hour, client=client)
                vals["temp_c"] = w["temp_c"]
                vals["humidity"] = w["humidity"]
                vals["wbgt"] = w["wbgt"]
            except Exception as e:  # keep dome, leave weather None
                failed_weather += 1
                print(f"[enrich] weather fetch failed for {venue} {match_date}: {type(e).__name__}: {e}")
            enriched[(venue, match_date)] = vals
    finally:
        client.close()

    if unknown_venue:
        print(f"[enrich] {unknown_venue} unique (venue,date) groups had an unknown venue (left None)")
    if failed_weather:
        print(f"[enrich] {failed_weather} groups had a failed weather fetch (dome kept, weather None)")

    # Build per-row column values from the lookup map.
    def _col(field):
        out = []
        for venue, match_date in zip(df["venue"].to_list(), df["match_date"].to_list()):
            vals = enriched.get((venue, match_date))
            out.append(None if vals is None else vals[field])
        return out

    return df.with_columns(
        pl.Series("dome", _col("dome"), dtype=pl.Boolean),
        pl.Series("temp_c", _col("temp_c"), dtype=pl.Float64),
        pl.Series("humidity", _col("humidity"), dtype=pl.Float64),
        pl.Series("wbgt", _col("wbgt"), dtype=pl.Float64),
    )
