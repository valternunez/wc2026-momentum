"""Acclimatization study: is the momentum drop bigger when teams are far from home heat?

Builds, for every stoppage-team row across the tournaments, an `accl_gap` =
(match-day venue WBGT) − (squad's recent home-stadium WBGT). A team flying from a cool home
into US summer heat has a large positive gap; a host-region team ~0. We then ask whether the
on-top momentum drop deepens with `accl_gap`.

What this can and cannot show (see the plan): the §05 headline is identified WITHIN 2026
(same teams, break vs quiet minute), where acclimatization is differenced out — so this does
NOT threaten the −25. It probes the cross-tournament heterogeneity, esp. the CWC −23 outlier
("clubs regress more" vs "European clubs in US heat"). `accl_gap` is also collinear with
continent/league/style, so a gap↔drop link is suggestive, not proof.

Squad home:
  - national teams (WC2026 / Copa24 / Euro24): mean home-WBGT over the starting XI's CLUBS
    (FotMob `primaryTeamId`, present in those payloads);
  - clubs (CWC25): the club's own home (the team id) — no lineup needed.
  - WC2022 is excluded: those payloads carry no club affiliation.

LOCAL run only (scrapes club home coords + climate); writes data/processed/acclimatization.parquet.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import polars as pl

from src.analysis.descriptive import cluster_bootstrap_ci, on_top_rows
from src.analysis.heat_interaction import _slope_cluster_ci
from src.enrich.clubs import club_home_wbgt, pre_tournament_window
from src.enrich.weather import geocode_city, get_weather
from src.features.momentum_features import _date_from_ts
from src.paths import PROCESSED, RAW, RAW_FOTMOB
from src.scrape import fotmob


@dataclass(frozen=True)
class Tournament:
    name: str
    parquet: str
    raw_dir: Path
    start: date
    is_clubs: bool


TOURNAMENTS: list[Tournament] = [
    Tournament("WC2026", "stoppages.parquet", RAW_FOTMOB, date(2026, 6, 11), False),
    Tournament("Copa2024", "copa2024_placebo.parquet", RAW / "fotmob_copa2024", date(2024, 6, 20), False),
    Tournament("Euro2024", "euro2024_placebo.parquet", RAW / "fotmob_euro2024", date(2024, 6, 14), False),
    Tournament("CWC2025", "cwc2025_placebo.parquet", RAW / "fotmob_cwc2025", date(2025, 6, 14), True),
    # WC2022 excluded: payloads carry no club affiliation (squad->club impossible).
]

OUT = PROCESSED / "acclimatization.parquet"


def _read_raw(raw_dir: Path, mid: str) -> dict[str, Any]:
    p = raw_dir / f"{mid}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _venue_wbgt(meta: dict, existing: float | None, *, client=None) -> float | None:
    """Match-day venue WBGT: reuse the parquet value (WC2026) else geocode the city + fetch."""
    if existing is not None:
        return float(existing)
    city = meta.get("venue_city") or meta.get("venue_stadium")
    coords = geocode_city(city, client=client) if city else None
    if not coords:
        return None
    d = _date_from_ts(meta.get("start_timestamp"))
    if not d:
        return None
    try:
        return get_weather(coords[0], coords[1], d, client=client)["wbgt"]
    except Exception:
        return None


def _squad_home_wbgt(
    meta: dict, raw: dict, is_home: bool, tour: Tournament, window: tuple[str, str], cache: dict
) -> float | None:
    """Recent home WBGT for one team-side: the club itself (CWC) or the XI's clubs (nations)."""
    def home_for(cid):  # memoized per (club_id, window)
        if cid is None:
            return None
        k = (cid, window)
        if k not in cache:
            cache[k] = club_home_wbgt(cid, window)
        return cache[k]

    if tour.is_clubs:
        tid = meta.get("home_team_id") if is_home else meta.get("away_team_id")
        return home_for(tid)
    side = "home" if is_home else "away"
    clubs = [p["club_id"] for p in fotmob.parse_lineup(raw)
             if p["side"] == side and p["is_starter"] and p.get("club_id") is not None]
    vals = [w for w in (home_for(c) for c in clubs) if w is not None]
    return (sum(vals) / len(vals)) if vals else None


def build_acclimatization_table(tournaments: list[Tournament] = TOURNAMENTS, *, verbose: bool = True) -> pl.DataFrame:
    """Augment each tournament's stoppage rows with venue/home WBGT + accl_gap; concat all."""
    cache: dict = {}                 # (club_id, window) -> home WBGT (dedupes scraping)
    frames: list[pl.DataFrame] = []
    for tour in tournaments:
        path = PROCESSED / tour.parquet
        if not path.exists():
            if verbose:
                print(f"[accl] skip {tour.name}: {tour.parquet} missing")
            continue
        df = pl.read_parquet(path).with_columns(pl.col("match_id").cast(pl.Utf8))
        window = pre_tournament_window(tour.start)
        # one accl row per (match_id, is_home); join back to all stoppage rows of that match-side
        keys = df.select(["match_id", "is_home"]).unique().to_dicts()
        recs: list[dict] = []
        wclient = None
        for k in keys:
            mid, is_home = k["match_id"], k["is_home"]
            raw = _read_raw(tour.raw_dir, mid)
            if not raw:
                continue
            meta = fotmob.parse_match_meta(raw)
            existing = (df.filter((pl.col("match_id") == mid) & (pl.col("is_home") == is_home))
                          ["wbgt"].drop_nulls().to_list())
            venue = _venue_wbgt(meta, existing[0] if existing else None, client=wclient)
            home = _squad_home_wbgt(meta, raw, is_home, tour, window, cache)
            gap = (venue - home) if (venue is not None and home is not None) else None
            recs.append({"match_id": mid, "is_home": is_home,
                         "venue_wbgt": venue, "squad_home_wbgt": home, "accl_gap": gap})
        if not recs:
            continue
        accl = pl.DataFrame(recs)
        merged = df.join(accl, on=["match_id", "is_home"], how="left").with_columns(
            pl.lit(tour.name).alias("tournament"))
        frames.append(merged)
        if verbose:
            ng = accl["accl_gap"].drop_nulls()
            print(f"[accl] {tour.name}: {accl.height} match-sides, accl_gap n={ng.len()} "
                  f"mean={ng.mean():.1f}" if ng.len() else f"[accl] {tour.name}: no accl_gap resolved")
    if not frames:
        return pl.DataFrame()
    cols = list(frames[0].columns)
    return pl.concat([f.select(cols) for f in frames], how="vertical")


# --- analysis ---------------------------------------------------------------
def _gap_drop(df: pl.DataFrame, **bk) -> dict[str, Any]:
    """On-top rows with a resolved gap: slope of momentum_delta on accl_gap + low/high-gap means."""
    top = on_top_rows(df).drop_nulls(["accl_gap"])
    if top.height < 6:
        return {"n": top.height, "note": "too few rows"}
    med = float(top["accl_gap"].median())
    lo = top.filter(pl.col("accl_gap") <= med)
    hi = top.filter(pl.col("accl_gap") > med)
    s, slo, shi = _slope_cluster_ci(top, "accl_gap", **bk)
    lm, llo, lhi = cluster_bootstrap_ci(lo, **bk)
    hm, hlo, hhi = cluster_bootstrap_ci(hi, **bk)
    return {
        "n": top.height, "n_matches": top["match_id"].n_unique(), "gap_median": med,
        "slope_per_C": {"slope": s, "ci_lo": slo, "ci_hi": shi},
        "low_gap": {"n": lo.height, "mean": lm, "ci_lo": llo, "ci_hi": lhi},
        "high_gap": {"n": hi.height, "mean": hm, "ci_lo": hlo, "ci_hi": hhi},
    }


def summarize_acclimatization(df: pl.DataFrame, **bk) -> dict[str, Any]:
    """CWC-clubs test, nations-pooled test, and the per-tournament gap means."""
    out: dict[str, Any] = {"per_tournament": {}}
    for t in sorted(df["tournament"].unique().to_list()):
        sub = on_top_rows(df.filter(pl.col("tournament") == t)).drop_nulls(["accl_gap"])
        if sub.height:
            out["per_tournament"][t] = {
                "n": sub.height, "gap_mean": float(sub["accl_gap"].mean()),
                "drop_mean": float(sub["momentum_delta"].mean())}
    clubs = df.filter(pl.col("tournament") == "CWC2025")
    nations = df.filter(pl.col("tournament").is_in(["WC2026", "Copa2024", "Euro2024"]))
    out["cwc_clubs_test"] = _gap_drop(clubs, **bk)
    out["nations_test"] = _gap_drop(nations, **bk)
    return out


def _fmt_cell(c: dict | None) -> str:
    if not c or c.get("mean") is None or c["mean"] != c["mean"]:
        return "n/a"
    return f"{c['mean']:+.1f} [{c['ci_lo']:+.1f},{c['ci_hi']:+.1f}] n={c['n']}"


def print_summary(res: dict[str, Any]) -> None:
    print("\n=== Acclimatization: home-vs-venue heat gap ===")
    print("  per-tournament (on-top): gap C  drop")
    for t, v in res["per_tournament"].items():
        print(f"    {t:9s} gap {v['gap_mean']:+5.1f}   drop {v['drop_mean']:+6.1f}   (n={v['n']})")
    for label, key in (("CWC clubs", "cwc_clubs_test"), ("Nations pooled", "nations_test")):
        r = res[key]
        print(f"\n  {label}:")
        if "slope_per_C" not in r:
            print(f"    {r}")
            continue
        sl = r["slope_per_C"]
        print(f"    slope/C   {sl['slope']:+.2f} [{sl['ci_lo']:+.2f},{sl['ci_hi']:+.2f}]  "
              "(<0 => drop deepens as teams get further from home heat)")
        print(f"    low-gap   {_fmt_cell(r['low_gap'])}")
        print(f"    high-gap  {_fmt_cell(r['high_gap'])}   (split at gap={r['gap_median']:+.1f}C)")


if __name__ == "__main__":
    t = build_acclimatization_table()
    if not t.is_empty():
        print_summary(summarize_acclimatization(t))
