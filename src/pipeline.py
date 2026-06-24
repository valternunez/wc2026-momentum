"""One-command pipeline: scrape -> parse -> features -> processed parquet -> snapshot.

Idempotent: matches whose raw JSON already exists are NOT re-scraped; the parquet
is always rebuilt from disk (cheap). Designed to run daily from a residential
machine (scrape) — CI never calls this (publish-only). See scripts/daily.ps1.

Usage:
  uv run python -m src.pipeline --match-ids 12345 12346
  uv run python -m src.pipeline --ids-file data/match_ids.json
  uv run python -m src.pipeline --no-scrape           # rebuild parquet from cached raw
  uv run python -m src.pipeline --ids-file data/match_ids.json --date 2026-06-22
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import polars as pl

from src.features.momentum_features import COLUMNS, expand_stoppage_rows
from src.parse.stoppages import detect_stoppages
from src.paths import DATA, PROCESSED, RAW, RAW_FOTMOB, STOPPAGES_PARQUET, ensure_dirs
from src.scrape import commentary as comm
from src.scrape import espn, fotmob
from src.snapshot import write_snapshot


def _yyyymmdd(ts: int | None) -> str | None:
    """Epoch seconds -> 'YYYYMMDD' (UTC), for the ESPN scoreboard lookup."""
    if not ts:
        return None
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y%m%d")


def assemble_rows(
    meta: dict[str, Any],
    momentum: list[dict[str, float]],
    incidents: list[dict[str, Any]],
    commentary: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Pure: inputs -> stoppage-level rows (2 per detected stoppage). Testable offline."""
    rows: list[dict[str, Any]] = []
    for s in detect_stoppages(meta, incidents, commentary):
        rows.extend(expand_stoppage_rows(meta, s, momentum))
    return rows


def rows_for_match(match_id: int | str) -> list[dict[str, Any]]:
    """Build rows for one match from its persisted FotMob raw (no network)."""
    meta, momentum, incidents, nominal = fotmob.match_inputs(match_id)
    if not meta or not momentum:
        return []
    # ESPN commentary (saved at scrape) gives exact hydration timing + VAR + injury.
    # If it captured hydration breaks, trust it; else keep nominal 22'/67' as a backstop
    # (we still get VAR/injury from the real commentary either way).
    real = comm.normalize_lines(comm.load_commentary(match_id))
    commentary = real if any(c.get("type") == "hydration" for c in real) else real + nominal
    return assemble_rows(meta, momentum, incidents, commentary)


def scrape_match(match_id: int | str, *, client=None, force: bool = False) -> None:
    """Fetch + persist FotMob raw + best-effort ESPN commentary for one match."""
    fotmob.fetch_match_details(match_id, client=client, force=force)
    # Best-effort ESPN commentary (matched by date + team names) for exact
    # hydration timing + VAR/injury. Never fail the scrape if ESPN is missing.
    if not comm.load_commentary(match_id):
        meta = fotmob.parse_match_meta(fotmob.load_raw(match_id))
        date_str = _yyyymmdd(meta.get("start_timestamp"))
        if date_str and meta.get("home_team") and meta.get("away_team"):
            lines = espn.commentary_for_match(date_str, meta["home_team"], meta["away_team"])
            if lines:
                comm.save_commentary(match_id, lines)


def discover_scraped_ids() -> list[str]:
    """Match ids that already have FotMob raw data on disk."""
    return sorted(p.stem for p in RAW_FOTMOB.glob("*.json")) if RAW_FOTMOB.exists() else []


def _guard_rowcount(prev: int, new: int, *, force: bool) -> None:
    """Raise if the rebuilt table lost >50% of rows vs the committed parquet (unless forced)."""
    if not force and prev > 0 and new < max(1, prev // 2):
        raise RuntimeError(
            f"Refusing to overwrite stoppages.parquet: rows {prev} -> {new} (>50% drop). "
            "Likely a source/payload regression — investigate, or re-run with --force to override."
        )


def build_table(match_ids: list[str]) -> pl.DataFrame:
    rows: list[dict[str, Any]] = []
    for mid in match_ids:
        rows.extend(rows_for_match(mid))
    if not rows:
        return pl.DataFrame(schema={c: pl.Utf8 for c in COLUMNS})
    return pl.DataFrame(rows).select(COLUMNS)


def run(
    match_ids: list[str], *, do_scrape: bool, force: bool, date: str | None, do_enrich: bool = True,
) -> pl.DataFrame:
    ensure_dirs()
    if do_scrape and match_ids:
        client = fotmob.make_client()  # plain client + x-mas auth header
        try:
            for mid in match_ids:
                try:
                    scrape_match(mid, client=client, force=force)
                    print(f"[scrape] ok {mid}")
                except Exception as e:  # keep going; a finished match can be retried tomorrow
                    print(f"[scrape] FAIL {mid}: {type(e).__name__}: {e}")
        finally:
            if hasattr(client, "close"):
                client.close()

    all_ids = sorted(set(discover_scraped_ids()) | set(map(str, match_ids)))
    df = build_table(all_ids)

    # coverage: surface matches that produced no rows (pending, missing data, or a payload-shape change)
    covered = set(df["match_id"].unique().to_list()) if not df.is_empty() else set()
    missing = [m for m in all_ids if m not in covered]
    if missing:
        shown = ", ".join(missing[:12]) + (" …" if len(missing) > 12 else "")
        print(f"[build] WARNING: {len(missing)}/{len(all_ids)} matches produced 0 rows ({shown})")

    # Confounder enrichment (venue dome + weather) fills dome/temp_c/humidity/wbgt.
    # Hits Open-Meteo, so it's opt-out via --no-enrich for fast offline rebuilds.
    # enrich_stoppages is resilient (unknown venue / failed fetch -> None, never raises).
    if do_enrich and not df.is_empty():
        from src.enrich import enrich_stoppages

        df = enrich_stoppages(df)
        print("[enrich] venue + weather columns filled")

    # guardrails — never overwrite a good committed parquet with garbage (override with --force)
    if set(df.columns) != set(COLUMNS):
        raise RuntimeError(f"parquet schema drift: {sorted(set(COLUMNS) ^ set(df.columns))}")
    if STOPPAGES_PARQUET.exists():
        _guard_rowcount(pl.read_parquet(STOPPAGES_PARQUET).height, df.height, force=force)

    STOPPAGES_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(STOPPAGES_PARQUET)
    print(f"[build] {df.height} rows from {len(all_ids)} matches "
          f"({len(covered)} with data) -> {STOPPAGES_PARQUET}")

    if date:
        path = write_snapshot(df, date)
        print(f"[snapshot] {path}")

    # Per-match editorial panels + match meta (local only; need FotMob raw). Committed; CI serves them.
    try:
        from src.viz.per_match import build_match_panels

        ids = build_match_panels()
        _write_matches_json(all_ids)
        _write_momentum_json(all_ids, df)
        print(f"[per-match] {len(ids)} panels + matches.json + momentum.json ({len(all_ids)} matches)")
    except Exception as e:
        print(f"[per-match] skipped: {type(e).__name__}: {e}")
    try:  # within-2026 regression-to-the-mean control (committed; CI reads it)
        pdf = build_2026_placebo(all_ids)
        print(f"[placebo2026] {pdf.height} rows ({pdf['match_id'].n_unique()} matches) -> placebo2026.parquet")
    except Exception as e:
        print(f"[placebo2026] skipped: {type(e).__name__}: {e}")
    return df


def _write_momentum_json(match_ids: list[str], df: pl.DataFrame) -> None:
    """Committed per-match momentum series + stoppage markers, for the interactive modal.

    Publishes FotMob's derived momentum index (user-approved, non-commercial + attributed).
    Compact arrays keep it small. CI embeds this; raw stays local.
    """
    out = []
    for mid in match_ids:
        raw = fotmob.load_raw(mid)
        if not raw:
            continue
        series = [[round(p["minute"], 1), round(p["value"], 1)] for p in fotmob.parse_momentum(raw)]
        if not series:
            continue
        m = fotmob.parse_match_meta(raw)
        stoppages = []
        if df is not None and not df.is_empty():
            sub = (df.filter(pl.col("match_id") == str(mid))
                     .select(["clock_minute", "stoppage_type"]).unique()
                     .sort(["clock_minute", "stoppage_type"]))  # tie-break for deterministic output
            stoppages = [[r["clock_minute"], r["stoppage_type"]] for r in sub.to_dicts()]
        tc = (raw.get("general") or {}).get("teamColors") or {}
        colors = None
        if tc.get("lightMode") or tc.get("darkMode"):
            colors = {
                "light": {"home": (tc.get("lightMode") or {}).get("home"),
                          "away": (tc.get("lightMode") or {}).get("away")},
                "dark": {"home": (tc.get("darkMode") or {}).get("home"),
                         "away": (tc.get("darkMode") or {}).get("away")},
            }
        out.append({
            "id": str(mid), "home": m.get("home_team"), "away": m.get("away_team"),
            "hs": m.get("home_score"), "as": m.get("away_score"),
            "ts": m.get("start_timestamp"), "colors": colors,
            "series": series, "stoppages": stoppages, "goals": fotmob.parse_goals(raw),
        })
    (PROCESSED / "momentum.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")


def _write_matches_json(match_ids: list[str]) -> None:
    """Committed per-match meta (home/away/score/date/stage) so the report has fixtures in CI."""
    rows = []
    for mid in match_ids:
        raw = fotmob.load_raw(mid)
        if not raw:
            continue
        m = fotmob.parse_match_meta(raw)
        rows.append({
            "id": str(mid), "home": m.get("home_team"), "away": m.get("away_team"),
            "home_score": m.get("home_score"), "away_score": m.get("away_score"),
            "ts": m.get("start_timestamp"), "stage": m.get("stage"), "league": m.get("tournament"),
        })
    rows.sort(key=lambda r: (r["ts"] or 0, r["id"]))
    (PROCESSED / "matches.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")


def build_historical_placebo(limit: int | None = None) -> pl.DataFrame:
    """Build the 2022-WC historical placebo parquet (StatsBomb xT-flow proxy).

    Separate, occasional run (not part of the daily flow): applies the 22'/67'
    windowing to a tournament with NO mandated breaks, so any effect there is bias.
    Writes data/processed/historical_placebo.parquet.
    """
    from src.analysis.historical_placebo import build_historical_placebo_table, summarize_placebo
    from src.scrape.statsbomb import fetch_matches

    ids = [m["match_id"] for m in fetch_matches()]
    if limit:
        ids = ids[:limit]
    print(f"[hist-placebo] building from {len(ids)} StatsBomb 2022 matches…")
    df = build_historical_placebo_table(ids)
    out = PROCESSED / "historical_placebo.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out)
    print(f"[hist-placebo] {df.height} rows -> {out}")
    print(f"[hist-placebo] summary: {summarize_placebo(df)}")
    return df


MATCH_IDS_FILE = DATA / "match_ids.json"


def discover_finished_wc_ids(days: int, end_date: str | None) -> list[str]:
    """Discover FINISHED WC matches over the last `days` dates and merge into match_ids.json.

    A match is upcoming (skip) if its FotMob status is a future ISO timestamp; anything else on a
    past/today date is finished. Reuses fotmob.list_wc_events. Returns the merged id list (strings).
    """
    end = (
        datetime.strptime(end_date, "%Y-%m-%d").date()
        if end_date
        else datetime.now(timezone.utc).date()
    )
    client = fotmob.make_client()
    found: set[str] = set()
    for i in range(max(days, 1)):
        d = (end - timedelta(days=i)).strftime("%Y%m%d")
        for e in fotmob.list_wc_events(d, client=client):
            if e.get("id") and not re.match(r"^\d{4}-\d\d-\d\dT", str(e.get("status"))):
                found.add(str(e["id"]))

    existing: set[str] = set()
    if MATCH_IDS_FILE.exists():
        existing = {str(x) for x in json.loads(MATCH_IDS_FILE.read_text(encoding="utf-8"))}
    # a bad FotMob day returns 0 — don't clobber the tracked list with an empty discovery
    if not found and existing:
        print(f"[discover] WARNING: 0 matches found over {days}d; keeping existing {len(existing)} (no overwrite)")
        return sorted(existing, key=int)
    merged = sorted(existing | found, key=int)
    tmp = MATCH_IDS_FILE.with_name(MATCH_IDS_FILE.name + ".tmp")  # atomic: write temp then replace
    tmp.write_text(json.dumps(merged), encoding="utf-8")
    tmp.replace(MATCH_IDS_FILE)
    print(f"[discover] {len(found)} finished WC matches over {days}d; tracking {len(merged)} total")
    return merged


def build_cwc_placebo() -> pl.DataFrame:
    """Build the CWC 2025 same-units placebo parquet (occasional run; FotMob momentum)."""
    from src.analysis.cwc_placebo import build_cwc_placebo_table, summarize_cwc_placebo

    print("[cwc-placebo] discovering + scraping CWC 2025 (FotMob)…")
    df = build_cwc_placebo_table()
    out = PROCESSED / "cwc2025_placebo.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out)
    print(f"[cwc-placebo] {df.height} rows ({df['match_id'].n_unique()} matches) -> {out}")
    print(f"[cwc-placebo] summary: {summarize_cwc_placebo(df)}")
    return df


def build_copa_placebo() -> pl.DataFrame:
    """Build the Copa América 2024 same-units placebo parquet (occasional run; FotMob momentum).

    National teams in US summer heat — the closest no-break analog to WC2026.
    """
    from src.analysis.copa_placebo import build_copa_placebo_table, summarize_copa_placebo

    print("[copa-placebo] discovering + scraping Copa América 2024 (FotMob)…")
    df = build_copa_placebo_table()
    out = PROCESSED / "copa2024_placebo.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out)
    print(f"[copa-placebo] {df.height} rows ({df['match_id'].n_unique()} matches) -> {out}")
    print(f"[copa-placebo] summary: {summarize_copa_placebo(df)}")
    return df


def build_euro_placebo() -> pl.DataFrame:
    """Build the Euro 2024 same-units placebo parquet (occasional run; FotMob momentum).

    European national teams — the team-side companion to Copa América for the no-break baseline.
    """
    from src.analysis.euro_placebo import build_euro_placebo_table, summarize_euro_placebo

    print("[euro-placebo] discovering + scraping Euro 2024 (FotMob)…")
    df = build_euro_placebo_table()
    out = PROCESSED / "euro2024_placebo.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out)
    print(f"[euro-placebo] {df.height} rows ({df['match_id'].n_unique()} matches) -> {out}")
    print(f"[euro-placebo] summary: {summarize_euro_placebo(df)}")
    return df


def build_wc2022_placebo() -> pl.DataFrame:
    """Build the 2022-WC same-units placebo parquet via FotMob (occasional run)."""
    from datetime import date

    from src.analysis.fotmob_placebo import build_fotmob_placebo, summarize_placebo
    from src.scrape.fotmob import WORLD_CUP_PRIMARY_ID

    print("[wc2022-placebo] discovering + scraping WC 2022 (FotMob)…")
    df = build_fotmob_placebo(WORLD_CUP_PRIMARY_ID, date(2022, 11, 20), date(2022, 12, 18),
                              RAW / "fotmob_wc2022")
    out = PROCESSED / "wc2022_placebo.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out)
    print(f"[wc2022-placebo] {df.height} rows ({df['match_id'].n_unique()} matches) -> {out}")
    print(f"[wc2022-placebo] summary: {summarize_placebo(df)}")
    return df


# Within-2026 regression-to-the-mean control: the SAME matches windowed at non-break minutes,
# all >=5' clear of the real 22'/67' breaks and the 45' half (so pre/post windows aren't contaminated).
PLACEBO_2026_MINUTES = (10.0, 35.0, 55.0, 80.0)


def build_2026_placebo(match_ids: list[str]) -> pl.DataFrame:
    """Window the 2026 matches at fake non-break minutes -> data/processed/placebo2026.parquet."""
    from datetime import date

    from src.analysis.fotmob_placebo import build_fotmob_placebo
    from src.scrape.fotmob import WORLD_CUP_PRIMARY_ID

    df = build_fotmob_placebo(WORLD_CUP_PRIMARY_ID, date(2026, 6, 1), date(2026, 8, 1), RAW_FOTMOB,
                              minutes=PLACEBO_2026_MINUTES, match_ids=[str(m) for m in match_ids])
    out = PROCESSED / "placebo2026.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out)
    return df


def _parse_ids(args: argparse.Namespace) -> list[str]:
    ids: list[str] = [str(i) for i in (args.match_ids or [])]
    if args.ids_file:
        data = json.loads(open(args.ids_file, encoding="utf-8").read())
        ids += [str(i) for i in data]
    return sorted(set(ids))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--match-ids", nargs="*", type=str, help="FotMob match ids to scrape/build")
    ap.add_argument("--ids-file", type=str, help="JSON file with a list of match ids")
    ap.add_argument("--no-scrape", action="store_true", help="rebuild parquet from cached raw only")
    ap.add_argument("--force", action="store_true", help="re-fetch even if raw exists")
    ap.add_argument("--date", type=str, default=None, help="snapshot date YYYY-MM-DD (writes a snapshot)")
    ap.add_argument("--no-enrich", action="store_true", help="skip venue+weather enrichment (no network)")
    ap.add_argument("--historical-placebo", action="store_true", help="build the 2022-WC placebo parquet and exit")
    ap.add_argument("--hp-limit", type=int, default=None, help="limit StatsBomb matches for --historical-placebo")
    ap.add_argument("--cwc-placebo", action="store_true", help="build the CWC 2025 same-units placebo parquet and exit")
    ap.add_argument("--wc2022-placebo", action="store_true", help="build the 2022-WC FotMob same-units placebo and exit")
    ap.add_argument("--copa-placebo", action="store_true", help="build the Copa América 2024 same-units placebo parquet and exit")
    ap.add_argument("--euro-placebo", action="store_true", help="build the Euro 2024 same-units placebo parquet and exit")
    ap.add_argument("--og-card", action="store_true", help="render the 1200x630 social share card and exit")
    ap.add_argument("--discover-days", type=int, default=None,
                    help="auto-discover finished WC matches over the last N days and merge into match_ids.json")
    args = ap.parse_args()
    if args.historical_placebo:
        build_historical_placebo(limit=args.hp_limit)
        return
    if args.cwc_placebo:
        build_cwc_placebo()
        return
    if args.wc2022_placebo:
        build_wc2022_placebo()
        return
    if args.copa_placebo:
        build_copa_placebo()
        return
    if args.euro_placebo:
        build_euro_placebo()
        return
    if args.og_card:
        from src.viz.social import build_share_card

        print("[og-card]", build_share_card())
        return
    ids = _parse_ids(args)
    if args.discover_days:
        ids = sorted(set(ids) | set(discover_finished_wc_ids(args.discover_days, args.date)), key=int)
    run(
        ids,
        do_scrape=not args.no_scrape,
        force=args.force,
        date=args.date,
        do_enrich=not args.no_enrich,
    )


if __name__ == "__main__":
    main()
