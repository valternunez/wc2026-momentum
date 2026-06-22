"""Tests for the confounder/context enrichment lane (venue + weather)."""

from __future__ import annotations

import polars as pl
import pytest

from src.enrich import enrich_stoppages
from src.enrich.venues import lookup_venue
from src.enrich.weather import get_weather, wbgt


# --------------------------------------------------------------------------- #
# lookup_venue
# --------------------------------------------------------------------------- #
def test_lookup_canonical_name():
    v = lookup_venue("Mercedes-Benz Stadium")
    assert v is not None
    assert v["name"] == "Mercedes-Benz Stadium"
    assert v["city"] == "Atlanta"
    assert v["dome"] is True


def test_lookup_open_air_final_venue():
    v = lookup_venue("MetLife Stadium")
    assert v is not None
    assert v["dome"] is False
    assert v["country"] == "USA"


def test_lookup_by_city():
    v = lookup_venue("Vancouver")
    assert v is not None
    assert v["name"] == "BC Place"
    assert v["dome"] is True


def test_lookup_alias_and_case_insensitive():
    # "dallas" is an alias for AT&T Stadium (city is Arlington).
    v = lookup_venue("dallas")
    assert v is not None and v["name"] == "AT&T Stadium" and v["dome"] is True
    # Case / punctuation tolerance.
    assert lookup_venue("estadio azteca")["name"] == "Estadio Azteca"


def test_lookup_unknown_returns_none():
    assert lookup_venue("Wembley Stadium") is None
    assert lookup_venue("") is None
    assert lookup_venue(None) is None  # type: ignore[arg-type]


def test_venue_table_has_16_with_5_domes():
    from src.enrich.venues import VENUES

    assert len(VENUES) == 16
    domes = [n for n, a in VENUES.items() if a["dome"]]
    # Atlanta, Dallas, Houston, LA SoFi, Vancouver
    assert len(domes) == 5
    assert set(domes) == {
        "Mercedes-Benz Stadium",
        "AT&T Stadium",
        "NRG Stadium",
        "SoFi Stadium",
        "BC Place",
    }


# --------------------------------------------------------------------------- #
# wbgt
# --------------------------------------------------------------------------- #
def test_wbgt_hot_humid_high():
    # 35C / 70% RH is dangerous heat -> high WBGT (well above 30).
    assert wbgt(35.0, 70.0) > 30.0


def test_wbgt_mild_lower():
    # 18C / 50% RH is mild -> low WBGT.
    assert wbgt(18.0, 50.0) < 20.0


def test_wbgt_monotonic_in_temp_and_humidity():
    # Increasing either temperature or humidity should not lower WBGT.
    assert wbgt(30.0, 60.0) > wbgt(20.0, 60.0)
    assert wbgt(30.0, 80.0) > wbgt(30.0, 40.0)


# --------------------------------------------------------------------------- #
# get_weather (network) — skips cleanly offline
# --------------------------------------------------------------------------- #
def test_get_weather_real_fetch():
    # Atlanta, a safely-archived past date. Network test: skip on any failure.
    try:
        w = get_weather(33.7554, -84.4008, "2022-07-15", hour=18)
    except Exception as e:  # offline / API down
        pytest.skip(f"Open-Meteo unreachable: {e}")
    if w["temp_c"] is None or w["humidity"] is None:
        pytest.skip("Open-Meteo returned no hourly data for the test date")
    assert -40.0 < w["temp_c"] < 60.0
    assert 0.0 <= w["humidity"] <= 100.0
    assert w["wbgt"] == pytest.approx(wbgt(w["temp_c"], w["humidity"]))


# --------------------------------------------------------------------------- #
# enrich_stoppages
# --------------------------------------------------------------------------- #
def test_enrich_stoppages_known_and_unknown(monkeypatch):
    # Stub the network so the test is deterministic and offline-safe.
    import src.enrich as enrich_mod

    def fake_get_weather(lat, lon, date, hour=18, *, client=None):
        return {"temp_c": 28.0, "humidity": 65.0, "wbgt": wbgt(28.0, 65.0)}

    monkeypatch.setattr(enrich_mod, "get_weather", fake_get_weather)

    df = pl.DataFrame(
        {
            "venue": ["Mercedes-Benz Stadium", "Wembley Stadium"],
            "match_date": ["2026-06-15", "2026-06-16"],
            "dome": [None, None],
            "temp_c": [None, None],
            "humidity": [None, None],
            "wbgt": [None, None],
        }
    )

    out = enrich_stoppages(df, kickoff_hour=18)
    assert out.height == 2

    known = out.filter(pl.col("venue") == "Mercedes-Benz Stadium").row(0, named=True)
    assert known["dome"] is True
    assert known["temp_c"] == 28.0
    assert known["humidity"] == 65.0
    assert known["wbgt"] == pytest.approx(wbgt(28.0, 65.0))

    unknown = out.filter(pl.col("venue") == "Wembley Stadium").row(0, named=True)
    assert unknown["dome"] is None
    assert unknown["temp_c"] is None
    assert unknown["humidity"] is None
    assert unknown["wbgt"] is None


def test_enrich_stoppages_weather_failure_keeps_dome(monkeypatch):
    import src.enrich as enrich_mod

    def boom(*a, **k):
        raise RuntimeError("api down")

    monkeypatch.setattr(enrich_mod, "get_weather", boom)

    df = pl.DataFrame(
        {
            "venue": ["BC Place"],
            "match_date": ["2026-06-15"],
            "dome": [None],
            "temp_c": [None],
            "humidity": [None],
            "wbgt": [None],
        }
    )
    out = enrich_stoppages(df)
    row = out.row(0, named=True)
    assert row["dome"] is True  # dome kept even when weather fails
    assert row["temp_c"] is None and row["wbgt"] is None


def test_enrich_stoppages_empty_df_no_raise():
    df = pl.DataFrame(
        schema={
            "venue": pl.Utf8,
            "match_date": pl.Utf8,
            "dome": pl.Boolean,
            "temp_c": pl.Float64,
            "humidity": pl.Float64,
            "wbgt": pl.Float64,
        }
    )
    out = enrich_stoppages(df)
    assert out.height == 0
