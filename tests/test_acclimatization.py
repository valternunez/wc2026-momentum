"""Offline tests for the acclimatization study's pure logic.

Network bits (FotMob team endpoint, Open-Meteo climate/geocode) are exercised by the local
build; here we test the deterministic glue: lineup parsing, the run-in window, and the
squad -> mean-home-WBGT aggregation (with the per-club lookup stubbed)."""

from __future__ import annotations

from datetime import date

from src.analysis import acclimatization as A
from src.scrape.fotmob import parse_lineup


def test_parse_lineup_sides_starters_and_clubs():
    raw = {"content": {"lineup": {
        "homeTeam": {
            "starters": [{"id": 1, "name": "A", "primaryTeamId": 10, "primaryTeamName": "Cph"},
                         {"id": 2, "name": "B", "primaryTeamId": 11, "primaryTeamName": "Rio"}],
            "subs": [{"id": 3, "name": "C", "primaryTeamId": 10, "primaryTeamName": "Cph"}],
        },
        "awayTeam": {
            "starters": [{"id": 4, "name": "D"}],   # no club affiliation (older payloads)
            "subs": [],
        },
    }}}
    rows = parse_lineup(raw)
    assert len(rows) == 4
    home_start = [r for r in rows if r["side"] == "home" and r["is_starter"]]
    assert {r["club_id"] for r in home_start} == {10, 11}
    sub = next(r for r in rows if not r["is_starter"])
    assert sub["side"] == "home" and sub["club_id"] == 10
    away = next(r for r in rows if r["side"] == "away")
    assert away["club_id"] is None      # tolerated, not an error


def test_parse_lineup_empty():
    assert parse_lineup({}) == []
    assert parse_lineup({"content": {"lineup": {}}}) == []


def test_pre_tournament_window_is_pre_and_bounded():
    start, end = A.pre_tournament_window(date(2026, 6, 11))   # WC2026
    assert end == "2026-06-04"          # ends a week before kickoff
    assert start == "2026-04-16"        # ~7 weeks earlier
    assert start < end < "2026-06-11"   # strictly before the tournament


def test_squad_home_wbgt_nations_means_over_starting_xi(monkeypatch):
    # stub the per-club lookup: clubs 10 and 11 sit at 20°C and 30°C
    homes = {10: 20.0, 11: 30.0}
    monkeypatch.setattr(A, "club_home_wbgt", lambda cid, win, **k: homes.get(cid))
    raw = {"content": {"lineup": {"homeTeam": {"starters": [
        {"id": 1, "primaryTeamId": 10}, {"id": 2, "primaryTeamId": 10}, {"id": 3, "primaryTeamId": 11},
    ], "subs": [{"id": 9, "primaryTeamId": 11}]}, "awayTeam": {"starters": [], "subs": []}}}}
    tour = A.Tournament("X", "x.parquet", A.RAW_FOTMOB, date(2026, 6, 11), is_clubs=False)
    val = A._squad_home_wbgt({}, raw, True, tour, ("2026-04-16", "2026-06-04"), {})
    assert abs(val - (20.0 + 20.0 + 30.0) / 3) < 1e-9   # starters only (sub excluded)


def test_squad_home_wbgt_clubs_uses_team_id(monkeypatch):
    monkeypatch.setattr(A, "club_home_wbgt", lambda cid, win, **k: {555: 26.0}.get(cid))
    tour = A.Tournament("CWC", "c.parquet", A.RAW_FOTMOB, date(2025, 6, 14), is_clubs=True)
    meta = {"home_team_id": 555, "away_team_id": 999}
    assert A._squad_home_wbgt(meta, {}, True, tour, ("a", "b"), {}) == 26.0
    assert A._squad_home_wbgt(meta, {}, False, tour, ("a", "b"), {}) is None  # 999 unknown
