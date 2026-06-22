import json
from pathlib import Path

import pytest

from src.scrape import commentary as comm
from src.scrape import sofascore

FIX = Path(__file__).parent / "fixtures" / "synthetic_match"


def _read(name: str) -> dict | list:
    return json.loads((FIX / name).read_text(encoding="utf-8"))


@pytest.fixture
def match_inputs() -> dict:
    """Parsed synthetic-match inputs, via the real parsers (offline)."""
    return {
        "meta": sofascore.parse_match_meta(_read("event.json")),
        "momentum": sofascore.parse_momentum(_read("graph.json")),
        "incidents": sofascore.parse_incidents(_read("incidents.json")),
        "commentary": comm.normalize_lines(_read("commentary.json")),
    }
