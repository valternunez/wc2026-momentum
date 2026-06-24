"""Match-time weather via the free Open-Meteo API (no API key) + WBGT.

We need hourly temperature_2m + relative_humidity_2m at a venue on the match
date, at an assumed local kickoff hour (no kickoff time exists in the data — see
`enrich.__init__.enrich_stoppages`, the hour is a parameter).

Endpoints (Open-Meteo, free for non-commercial use, no key):
  - archive  : https://archive-api.open-meteo.com/v1/archive   (ERA5 reanalysis,
               past dates; ~5-day lag before "today")
  - forecast : https://api.open-meteo.com/v1/forecast          (recent + future)

We pick archive for dates older than ~5 days, else forecast. Raw JSON responses
are persisted under data/raw/weather/ (gitignored) as an idempotent cache keyed
by lat/lon/date — never re-fetch a cached (lat,lon,date). CLAUDE.md: persist raw
before use.
"""

from __future__ import annotations

import json
import math
from datetime import date as _date
from datetime import datetime, timedelta, timezone

import httpx

from src.paths import RAW

WEATHER_RAW = RAW / "weather"

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
GEOCODE_RAW = RAW / "geocode"

# Archive (ERA5) typically lags ~5 days. Use forecast for anything more recent.
_ARCHIVE_LAG_DAYS = 6


def wbgt(temp_c: float, humidity: float) -> float:
    """WBGT (Wet Bulb Globe Temperature) approximation, degrees C.

    Australian Bureau of Meteorology simplified formula (shade / no direct solar
    radiation term), which estimates WBGT from dry-bulb temperature and water
    vapour pressure:

        e    = (RH/100) * 6.105 * exp(17.27*T / (237.7+T))   # vapour pressure, hPa
        WBGT = 0.567*T + 0.393*e + 3.94

    Source: Australian BoM, "Thermal Comfort observations / Approximation of WBGT"
    (http://www.bom.gov.au/info/thermal_stress/#approximation). Widely used as a
    practical heat-stress proxy when full WBGT instrumentation is unavailable.
    Note: this is a shade estimate; true on-pitch WBGT under sun runs higher.

    Args:
        temp_c: dry-bulb air temperature, degrees Celsius.
        humidity: relative humidity, percent (0-100).
    Returns:
        WBGT estimate in degrees Celsius.
    """
    t = float(temp_c)
    rh = float(humidity)
    e = (rh / 100.0) * 6.105 * math.exp(17.27 * t / (237.7 + t))
    return 0.567 * t + 0.393 * e + 3.94


def _cache_path(lat: float, lon: float, date: str) -> "object":
    key = f"{round(float(lat), 3)}_{round(float(lon), 3)}_{date}.json"
    return WEATHER_RAW / key


def _choose_endpoint(date: str) -> str:
    try:
        d = _date.fromisoformat(date)
    except ValueError:
        return FORECAST_URL
    cutoff = datetime.now(timezone.utc).date() - timedelta(days=_ARCHIVE_LAG_DAYS)
    return ARCHIVE_URL if d <= cutoff else FORECAST_URL


def _fetch_raw(lat: float, lon: float, date: str, *, client: httpx.Client | None = None) -> dict:
    """Fetch hourly temp+humidity for one day from Open-Meteo. Tries the chosen
    endpoint, then falls back to the other (archive<->forecast) on failure."""
    primary = _choose_endpoint(date)
    fallback = FORECAST_URL if primary == ARCHIVE_URL else ARCHIVE_URL
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date,
        "end_date": date,
        "hourly": "temperature_2m,relative_humidity_2m",
        "timezone": "auto",  # hourly timestamps in venue-local time
    }
    own = client is None
    cl = client or httpx.Client(timeout=30)
    try:
        last_exc: Exception | None = None
        for url in (primary, fallback):
            try:
                resp = cl.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                if data.get("hourly", {}).get("time"):
                    return data
                last_exc = RuntimeError(f"empty hourly from {url}")
            except Exception as e:  # try the fallback endpoint
                last_exc = e
        raise RuntimeError(f"open-meteo fetch failed for {lat},{lon},{date}: {last_exc}")
    finally:
        if own:
            cl.close()


def _load_or_fetch(lat: float, lon: float, date: str, *, client=None) -> dict:
    """Idempotent cache: read persisted raw if present, else fetch + persist."""
    path = _cache_path(lat, lon, date)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    data = _fetch_raw(lat, lon, date, client=client)
    WEATHER_RAW.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return data


def _extract_hour(raw: dict, hour: int) -> tuple[float | None, float | None]:
    """Pull (temp_c, humidity) at the requested local hour from a raw response.

    Open-Meteo hourly `time` entries look like "2026-06-22T18:00" (local, because
    we requested timezone=auto). We match on the hour; if absent, use the closest
    available hour.
    """
    hourly = raw.get("hourly", {})
    times = hourly.get("time") or []
    temps = hourly.get("temperature_2m") or []
    hums = hourly.get("relative_humidity_2m") or []
    if not times:
        return None, None

    target = int(hour)
    best_i = 0
    best_diff = 24
    for i, t in enumerate(times):
        try:
            h = int(t[11:13])
        except (ValueError, IndexError):
            continue
        diff = abs(h - target)
        if diff < best_diff:
            best_diff, best_i = diff, i
            if diff == 0:
                break
    temp = temps[best_i] if best_i < len(temps) else None
    hum = hums[best_i] if best_i < len(hums) else None
    return (
        float(temp) if temp is not None else None,
        float(hum) if hum is not None else None,
    )


def get_weather(lat: float, lon: float, date: str, hour: int = 18, *, client=None) -> dict:
    """Return {temp_c, humidity, wbgt} for a venue on `date` at local `hour`.

    Uses the persisted raw cache under data/raw/weather/ (fetch once per
    lat/lon/date). `date` is an ISO date string ("YYYY-MM-DD"). Raises on a
    genuine fetch failure (caller in enrich_stoppages catches and keeps None).
    """
    raw = _load_or_fetch(lat, lon, date, client=client)
    temp_c, humidity = _extract_hour(raw, hour)
    w = None if (temp_c is None or humidity is None) else wbgt(temp_c, humidity)
    return {"temp_c": temp_c, "humidity": humidity, "wbgt": w}


# --- climate normals (one ranged call) -------------------------------------
def _climate_cache_path(lat: float, lon: float, start: str, end: str, hour: int):
    key = f"clim_{round(float(lat), 3)}_{round(float(lon), 3)}_{start}_{end}_{hour}.json"
    return WEATHER_RAW / key


def climate_mean_wbgt(
    lat: float, lon: float, start_date: str, end_date: str, hour: int = 18, *, client=None
) -> float | None:
    """Mean daily WBGT at local `hour` over [start_date, end_date] — ONE Open-Meteo call.

    Used for a club's recent home thermal load (the pre-tournament run-in), which is the
    acclimatization reference. Persists the raw ranged response under data/raw/weather/ and
    is idempotent (re-runs hit disk). Returns None if no usable hours came back.
    """
    path = _climate_cache_path(lat, lon, start_date, end_date, hour)
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
    else:
        params_date = (start_date, end_date)
        raw = _fetch_range(lat, lon, *params_date, client=client)
        WEATHER_RAW.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(raw), encoding="utf-8")
    hourly = raw.get("hourly", {})
    times = hourly.get("time") or []
    temps = hourly.get("temperature_2m") or []
    hums = hourly.get("relative_humidity_2m") or []
    vals: list[float] = []
    for t, tc, rh in zip(times, temps, hums):
        try:
            if int(t[11:13]) == int(hour) and tc is not None and rh is not None:
                vals.append(wbgt(float(tc), float(rh)))
        except (ValueError, IndexError):
            continue
    return (sum(vals) / len(vals)) if vals else None


def geocode_city(name: str, *, client=None) -> tuple[float, float] | None:
    """(lat, lon) for a city/venue name via Open-Meteo geocoding. None if not found.

    Cached raw under data/raw/geocode/ (idempotent per name). Used to place non-WC tournament
    venues (Copa/Euro/CWC) for match-day WBGT; WC2026 venues already carry coords in venues.py.
    """
    if not name or not str(name).strip():
        return None
    key = "_".join(str(name).lower().split())
    path = GEOCODE_RAW / f"{key}.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        # Open-Meteo matches a single place name, so "Miami Gardens, Florida" fails — try the
        # full string, then the pre-comma token ("Miami Gardens"), then the last comma segment.
        head = str(name).split(",")[0].strip()
        tail = str(name).split(",")[-1].strip()
        candidates = [c for c in dict.fromkeys([str(name).strip(), head, tail]) if c]
        own = client is None
        cl = client or httpx.Client(timeout=30)
        data = {}
        got_response = False  # did ANY request actually come back (vs all raising)?
        try:
            for cand in candidates:
                try:
                    resp = cl.get(GEOCODE_URL, params={"name": cand, "count": 1, "language": "en"})
                    resp.raise_for_status()
                    got_response = True
                    d = resp.json()
                    if d.get("results"):
                        data = d
                        break
                except Exception:
                    continue
        finally:
            if own:
                cl.close()
        # Only cache a real answer — a successful response, including a legitimate empty "no results".
        # If EVERY request raised (a transient network/Cloudflare blip), do not poison the cache with
        # {} (which would make the venue permanently "not found"); leave it absent so the next run retries.
        if got_response:
            GEOCODE_RAW.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data), encoding="utf-8")
    results = data.get("results") or []
    if not results:
        return None
    r = results[0]
    try:
        return float(r["latitude"]), float(r["longitude"])
    except (KeyError, TypeError, ValueError):
        return None


def _fetch_range(lat: float, lon: float, start: str, end: str, *, client=None) -> dict:
    """Fetch hourly temp+humidity for a DATE RANGE (archive first, forecast fallback)."""
    primary = _choose_endpoint(start)  # window start governs which endpoint has the data
    fallback = FORECAST_URL if primary == ARCHIVE_URL else ARCHIVE_URL
    params = {
        "latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
        "hourly": "temperature_2m,relative_humidity_2m", "timezone": "auto",
    }
    own = client is None
    cl = client or httpx.Client(timeout=60)
    try:
        last_exc: Exception | None = None
        for url in (primary, fallback):
            try:
                resp = cl.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                if data.get("hourly", {}).get("time"):
                    return data
                last_exc = RuntimeError(f"empty hourly from {url}")
            except Exception as e:
                last_exc = e
        raise RuntimeError(f"open-meteo range fetch failed for {lat},{lon},{start}..{end}: {last_exc}")
    finally:
        if own:
            cl.close()
