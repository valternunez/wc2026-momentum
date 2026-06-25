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
from src.paths import DATA, PROCESSED, RAW, RAW_FOTMOB, SNAPSHOTS, STOPPAGES_PARQUET, ensure_dirs
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
    existing = comm.load_commentary(match_id)
    # Re-derive when missing, forced, or stored under the OLD schema (no per-line `seconds`) —
    # the latter is a one-time self-healing upgrade so real_duration_seconds can be filled.
    # The ESPN summary itself is cached on disk, so a re-derive only re-runs the light discovery.
    stale = bool(existing) and not any("seconds" in c for c in existing)
    if not existing or force or stale:
        meta = fotmob.parse_match_meta(fotmob.load_raw(match_id))
        date_str = _yyyymmdd(meta.get("start_timestamp"))
        if date_str and meta.get("home_team") and meta.get("away_team"):
            lines = espn.commentary_for_match(date_str, meta["home_team"], meta["away_team"])
            if lines:
                comm.save_commentary(match_id, lines)


def discover_scraped_ids() -> list[str]:
    """Match ids that already have FotMob raw data on disk."""
    return sorted(p.stem for p in RAW_FOTMOB.glob("*.json")) if RAW_FOTMOB.exists() else []


def _is_wc2026(match_id: str) -> bool:
    """True iff this match's cached FotMob raw belongs to the 2026 World Cup (parentLeagueId 77).

    The discriminator that separates real WC2026 group/knockout matches from qualifiers and other
    tournaments that may share the RAW_FOTMOB dir. Missing/unreadable raw -> False (excluded).
    """
    g = fotmob.load_raw(match_id).get("general") or {}
    return g.get("parentLeagueId") == fotmob.WORLD_CUP_PRIMARY_ID


def _guard_rowcount(prev: int, new: int, *, force: bool) -> None:
    """Raise if the rebuilt table changed implausibly vs the committed parquet (unless forced).

    Two directions: a >50% row DROP (a source/payload regression), or a sudden >2.5x INFLATION once
    the table is already sizeable — phantom stoppages or a non-WC competition leak, the documented
    contamination direction. The inflation check is gated on prev>=60 so legitimate early-tournament
    accumulation (small N growing fast) doesn't trip it.
    """
    if force or prev <= 0:
        return
    if new < max(1, prev // 2):
        raise RuntimeError(
            f"Refusing to overwrite stoppages.parquet: rows {prev} -> {new} (>50% drop). "
            "Likely a source/payload regression — investigate, or re-run with --force to override."
        )
    if prev >= 60 and new > prev * 2.5:
        raise RuntimeError(
            f"Refusing to overwrite stoppages.parquet: rows {prev} -> {new} (>2.5x inflation). "
            "Likely phantom stoppages or a non-WC competition leak — investigate, or --force to override."
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
    # Competition gate: only build genuine WC2026 matches (FotMob parentLeagueId 77). Orphan raw from
    # other competitions (WC qualifiers, Euro, Copa) can land in RAW_FOTMOB from ad-hoc fetches; this
    # keeps them out of the parquet, matches.json, momentum.json, panels and the within-2026 placebo.
    wc_ids = [m for m in all_ids if _is_wc2026(m)]
    dropped = [m for m in all_ids if m not in set(wc_ids)]
    if dropped:
        shown = ", ".join(dropped[:12]) + (" …" if len(dropped) > 12 else "")
        print(f"[gate] excluded {len(dropped)} non-WC2026 raw match(es): {shown}")
    all_ids = wc_ids
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
                     .select(["clock_minute", "stoppage_type", "real_duration_seconds"]).unique()
                     .sort(["clock_minute", "stoppage_type"]))  # tie-break for deterministic output
            # [minute, type, duration_seconds|null] — the chart shades each break's measured length
            stoppages = [[r["clock_minute"], r["stoppage_type"], r["real_duration_seconds"]]
                         for r in sub.to_dicts()]
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


def build_acclimatization(date_str: str | None = None) -> "pl.DataFrame":
    """Build the acclimatization table (home-vs-venue heat gap) + summary + snapshot.

    Occasional LOCAL run: scrapes each club's home-stadium coords (FotMob team endpoint) and
    a pre-tournament home-climate window (Open-Meteo), both cached. Writes
    data/processed/acclimatization.parquet and snapshots/<date>/acclimatization.json.
    """
    from src.analysis.acclimatization import (
        OUT, build_acclimatization_table, print_summary, summarize_acclimatization,
    )

    print("[accl] building acclimatization table (scrapes club home coords + climate)…")
    df = build_acclimatization_table()
    if df.is_empty():
        print("[accl] no rows built — nothing written")
        return df
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(OUT)
    print(f"[accl] {df.height} rows ({df['match_id'].n_unique()} matches) -> {OUT}")
    # Persist the clubs-placed count so the (raw-free) CI site build can render it instead of "—".
    _clubs = RAW / "fotmob_clubs"
    _n = len(list(_clubs.glob("*.json"))) if _clubs.exists() else 0
    if _n:
        (PROCESSED / "accl_meta.json").write_text(json.dumps({"clubs_placed": _n}), encoding="utf-8")
        print(f"[accl] meta -> clubs_placed={_n}")
    res = summarize_acclimatization(df)
    print_summary(res)
    d = date_str or datetime.now(timezone.utc).date().isoformat()
    snap = SNAPSHOTS / d / "acclimatization.json"
    snap.parent.mkdir(parents=True, exist_ok=True)
    snap.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[accl] snapshot -> {snap}")
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


# Within-2026 regression-to-the-mean control: the SAME matches windowed at non-break minutes.
# Position-matched to BRACKET the two real break regions (~22-25' and ~67-68') rather than the old
# 10'/80' game-state extremes, while staying >=5' clear of the breaks and the 45' half so the pre/post
# windows aren't contaminated. (The break-vs-placebo gap is additionally pre-level-adjusted downstream,
# so this control nets out regression to the mean on both clock position and starting momentum.)
PLACEBO_2026_MINUTES = (15.0, 35.0, 58.0, 78.0)


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


def build_twfe() -> dict:
    """Fit the signed-off TWFE causal model and persist the momentum-killer interaction to
    data/processed/twfe.json, so the statsmodels-free CI site build can report it honestly.

    Best-effort and SAFE: needs the events/dev extra (statsmodels). If statsmodels isn't installed
    (e.g. a lean Railway run), it logs and leaves any committed twfe.json untouched rather than
    overwriting the local estimate with a blank. Writes {gated: true} when the MIN_MATCHES/MIN_ROWS
    gate isn't met yet.
    """
    out = PROCESSED / "twfe.json"
    try:
        from src.analysis.descriptive import load_processed
        from src.analysis.regression import momentum_killer_estimate, run_twfe

        res = run_twfe(load_processed())
        rec = {"available": True, "gated": False, "n_obs": int(res.nobs),
               **momentum_killer_estimate(res)}
    except ValueError as e:  # data gate (not enough matches/rows yet)
        rec = {"available": True, "gated": True, "reason": str(e)[:160]}
    except Exception as e:  # statsmodels missing, etc. — do NOT clobber a committed estimate
        print(f"[twfe] skipped, leaving twfe.json untouched ({type(e).__name__}: {e})")
        return {}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec), encoding="utf-8")
    print(f"[twfe] -> {out}: p={rec.get('pvalue')}, coef={rec.get('coef')}, gated={rec.get('gated')}")
    return rec


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
    ap.add_argument("--acclimatization", action="store_true", help="build the acclimatization table (home-vs-venue heat gap) and exit")
    ap.add_argument("--twfe", action="store_true", help="fit the signed-off TWFE model and persist twfe.json (needs the dev/events extra) and exit")
    ap.add_argument("--og-card", action="store_true", help="render the 1200x630 social share card and exit")
    ap.add_argument("--story-cards", action="store_true", help="render the 1080x1920 story-slide still PNGs (needs a built site/story.html) and exit")
    ap.add_argument("--story-video", action="store_true", help="render the 1080x1920 story MP4 per language (needs a built site/story.html + ffmpeg) and exit")
    ap.add_argument("--reel-video", action="store_true", help="render the ~15s 1080x1920 kinetic reel MP4 per language (needs a built site/reel.html + ffmpeg) and exit")
    ap.add_argument("--refresh-social", action="store_true", help="regenerate og cards + story stills + story videos IF the headline numbers changed (best-effort) and exit")
    ap.add_argument("--method-pdf", action="store_true", help="render the methodology pages to committed PDFs and exit")
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
    if args.acclimatization:
        build_acclimatization(args.date)
        return
    if args.twfe:
        build_twfe()
        return
    if args.og_card:
        from src.viz.social import build_share_card

        print("[og-card]", build_share_card())
        return
    if args.story_cards:
        from src.viz.social import build_story_cards

        print("[story-cards]", build_story_cards())
        return
    if args.story_video:
        from src.viz.social import build_story_video

        print("[story-video]", build_story_video())
        return
    if args.reel_video:
        from src.viz.social import build_reel_video

        print("[reel-video]", build_reel_video())
        return
    if args.refresh_social:
        from src.viz.social import refresh_social

        refresh_social()
        return
    if args.method_pdf:
        from src.viz.method_pdf import build_methodology_pdf

        for p in build_methodology_pdf():
            print("[method-pdf]", p)
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
