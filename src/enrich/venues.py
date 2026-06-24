"""World Cup 2026 venue table + fuzzy venue lookup.

The 16 host stadiums (USA / Mexico / Canada). For each we record canonical name,
city, country, lat/lon, IANA timezone, and a `dome` flag.

`dome` semantics for THIS analysis (PROJECT_BRIEF.md H3): True when the stadium
has a fixed or *retractable* roof that lets the match be climate-controlled
(closed roof + sometimes A/C), so outdoor WBGT does not reach the players. False
for open-air bowls where players are exposed to ambient temperature/humidity.

Roof status sources (cross-checked against stadium operators / FIFA venue pages,
verified 2024-2025):
  - Atlanta — Mercedes-Benz Stadium: retractable roof.                -> dome=True
  - Dallas/Arlington — AT&T Stadium: retractable roof.                -> dome=True
  - Houston — NRG Stadium: retractable roof.                          -> dome=True
  - Los Angeles — SoFi Stadium: fixed (canopy) roof, open sides but
    covered/climate-buffered playing field; treated as controlled.    -> dome=True
  - Vancouver — BC Place: fixed retractable (cable) roof.             -> dome=True
  - All other 11 venues are open-air bowls.                           -> dome=False

Note: the World Cup final is at MetLife (East Rutherford, NJ) which is OPEN-AIR.
Mexico's three venues (Estadio Azteca, Guadalajara, Monterrey) are open-air.
Coordinates are stadium-centroid decimal degrees; timezones are IANA names.
"""

from __future__ import annotations

# canonical name -> attributes. `aliases` holds SofaScore-style stadium/city
# strings we expect to see upstream (the schema's `venue` may be stadium OR city).
VENUES: dict[str, dict] = {
    # --- United States (11) ---
    "MetLife Stadium": {
        "city": "East Rutherford",
        "country": "USA",
        "lat": 40.8135,
        "lon": -74.0745,
        "tz": "America/New_York",
        "dome": False,
        "aliases": ["new york", "new jersey", "east rutherford", "metlife", "ny/nj"],
    },
    "AT&T Stadium": {
        "city": "Arlington",
        "country": "USA",
        "lat": 32.7473,
        "lon": -97.0945,
        "tz": "America/Chicago",
        "dome": True,
        "aliases": ["dallas", "arlington", "at&t", "att stadium"],
    },
    "NRG Stadium": {
        "city": "Houston",
        "country": "USA",
        "lat": 29.6847,
        "lon": -95.4107,
        "tz": "America/Chicago",
        "dome": True,
        "aliases": ["houston", "nrg"],
    },
    "Mercedes-Benz Stadium": {
        "city": "Atlanta",
        "country": "USA",
        "lat": 33.7554,
        "lon": -84.4008,
        "tz": "America/New_York",
        "dome": True,
        "aliases": ["atlanta", "mercedes-benz", "mercedes benz"],
    },
    "Hard Rock Stadium": {
        "city": "Miami Gardens",
        "country": "USA",
        "lat": 25.9580,
        "lon": -80.2389,
        "tz": "America/New_York",
        "dome": False,  # canopy over stands only; playing field is open-air
        "aliases": ["miami", "miami gardens", "hard rock"],
    },
    "Lincoln Financial Field": {
        "city": "Philadelphia",
        "country": "USA",
        "lat": 39.9008,
        "lon": -75.1675,
        "tz": "America/New_York",
        "dome": False,
        "aliases": ["philadelphia", "philly", "lincoln financial"],
    },
    "Gillette Stadium": {
        "city": "Foxborough",
        "country": "USA",
        "lat": 42.0909,
        "lon": -71.2643,
        "tz": "America/New_York",
        "dome": False,
        "aliases": ["boston", "foxborough", "foxboro", "gillette"],
    },
    "Arrowhead Stadium": {
        "city": "Kansas City",
        "country": "USA",
        "lat": 39.0489,
        "lon": -94.4839,
        "tz": "America/Chicago",
        "dome": False,
        "aliases": ["kansas city", "kc", "arrowhead", "geha field"],
    },
    "Levi's Stadium": {
        "city": "Santa Clara",
        "country": "USA",
        "lat": 37.4030,
        "lon": -121.9700,
        "tz": "America/Los_Angeles",
        "dome": False,
        "aliases": ["san francisco", "bay area", "santa clara", "levi's", "levis"],
    },
    "SoFi Stadium": {
        "city": "Inglewood",
        "country": "USA",
        "lat": 33.9535,
        "lon": -118.3392,
        "tz": "America/Los_Angeles",
        "dome": True,  # fixed canopy roof; field covered/climate-buffered
        "aliases": ["los angeles", "la", "inglewood", "sofi"],
    },
    "Lumen Field": {
        "city": "Seattle",
        "country": "USA",
        "lat": 47.5952,
        "lon": -122.3316,
        "tz": "America/Los_Angeles",
        "dome": False,  # partial roof over seating; field open-air
        "aliases": ["seattle", "lumen"],
    },
    # --- Mexico (3) ---
    "Estadio Azteca": {
        "city": "Mexico City",
        "country": "Mexico",
        "lat": 19.3029,
        "lon": -99.1505,
        "tz": "America/Mexico_City",
        "dome": False,
        "aliases": ["mexico city", "azteca", "estadio banorte", "ciudad de mexico"],
    },
    "Estadio Akron": {
        "city": "Guadalajara",
        "country": "Mexico",
        "lat": 20.6818,
        "lon": -103.4628,
        "tz": "America/Mexico_City",
        "dome": False,
        "aliases": ["guadalajara", "akron", "estadio chivas", "zapopan"],
    },
    "Estadio BBVA": {
        "city": "Monterrey",
        "country": "Mexico",
        "lat": 25.6694,
        "lon": -100.2447,
        "tz": "America/Monterrey",
        "dome": False,
        "aliases": ["monterrey", "bbva", "estadio bbva bancomer", "guadalupe"],
    },
    # --- Canada (2) ---
    "BMO Field": {
        "city": "Toronto",
        "country": "Canada",
        "lat": 43.6332,
        "lon": -79.4185,
        "tz": "America/Toronto",
        "dome": False,
        "aliases": ["toronto", "bmo"],
    },
    "BC Place": {
        "city": "Vancouver",
        "country": "Canada",
        "lat": 49.2768,
        "lon": -123.1119,
        "tz": "America/Vancouver",
        "dome": True,  # retractable cable-supported roof
        "aliases": ["vancouver", "bc place"],
    },
}


def _normalize(s: str) -> str:
    """Lowercase, strip punctuation noise, collapse whitespace for matching."""
    out = []
    for ch in s.lower().strip():
        if ch.isalnum() or ch.isspace():
            out.append(ch)
        elif ch == "&":
            out.append("&")  # keep ampersand (AT&T)
        else:
            out.append(" ")
    return " ".join("".join(out).split())


# Approx stadium elevation (metres). Altitude is a fatigue stressor (thin air), separate from heat;
# Mexico City and Guadalajara are the high-altitude WC2026 venues (> 1,500 m).
ELEV_M: dict[str, int] = {
    "MetLife Stadium": 7, "AT&T Stadium": 180, "NRG Stadium": 15, "Mercedes-Benz Stadium": 320,
    "Hard Rock Stadium": 2, "Lincoln Financial Field": 12, "Gillette Stadium": 90,
    "Arrowhead Stadium": 270, "Levi's Stadium": 9, "SoFi Stadium": 30, "Lumen Field": 5,
    "Estadio Azteca": 2240, "Estadio Akron": 1560, "Estadio BBVA": 540, "BMO Field": 76, "BC Place": 3,
}


def venue_elev_m(venue_or_city: str) -> int | None:
    """Elevation (m) for a venue/city string, via the same alias matching as lookup_venue."""
    v = lookup_venue(venue_or_city)
    return ELEV_M.get(v["name"]) if v and v.get("name") else None


def lookup_venue(venue_or_city: str) -> dict | None:
    """Fuzzy-match a SofaScore-style venue/city string to a WC2026 venue.

    Case-insensitive, punctuation-tolerant, alias-aware, substring-tolerant.
    Returns a dict with name/city/country/lat/lon/tz/dome, or None if no match.

    Matching strategy (first hit wins):
      1. exact normalized match against canonical name, city, or any alias;
      2. substring match (query contains a key token, or a key token contains
         the query) against the same set, preferring the longest key matched.
    """
    if not venue_or_city or not str(venue_or_city).strip():
        return None
    q = _normalize(str(venue_or_city))

    # Build (key_string, canonical_name) candidate index.
    candidates: list[tuple[str, str]] = []
    for name, attrs in VENUES.items():
        candidates.append((_normalize(name), name))
        candidates.append((_normalize(attrs["city"]), name))
        for alias in attrs["aliases"]:
            candidates.append((_normalize(alias), name))

    # 1) exact normalized match
    for key, name in candidates:
        if key == q:
            return _result(name)

    # 2) substring match, prefer the longest matching key (most specific)
    best: tuple[int, str] | None = None
    for key, name in candidates:
        if not key:
            continue
        if key in q or q in key:
            score = len(key)
            if best is None or score > best[0]:
                best = (score, name)
    if best is not None:
        return _result(best[1])
    return None


def _result(name: str) -> dict:
    a = VENUES[name]
    return {
        "name": name,
        "city": a["city"],
        "country": a["country"],
        "lat": a["lat"],
        "lon": a["lon"],
        "tz": a["tz"],
        "dome": a["dome"],
    }
