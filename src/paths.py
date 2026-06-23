"""Canonical filesystem paths and a few project-wide constants.

Keep this dependency-free (stdlib only) so every module can import it cheaply.
"""

from __future__ import annotations

from pathlib import Path

# Repo root = parent of src/
ROOT = Path(__file__).resolve().parent.parent

DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"

SNAPSHOTS = ROOT / "snapshots"
REPORTS = ROOT / "reports"
SITE = ROOT / "site"
FIXTURES = ROOT / "tests" / "fixtures"

# Provider-specific raw subtrees
RAW_FOTMOB = RAW / "fotmob"
RAW_COMMENTARY = RAW / "commentary"

# The one analysis-ready table everything in the writeup must be reproducible from.
STOPPAGES_PARQUET = PROCESSED / "stoppages.parquet"

# --- Domain constants -------------------------------------------------------

# Nominal hydration/cooling break marks (minutes). The referee has discretion to
# delay them around other stoppages, so these are SEEDS for detection, not truth.
# Detection is anchored on commentary, not these numbers (see PROJECT_BRIEF.md).
HYDRATION_NOMINAL_MINUTES = (22, 67)

# Pre/post window length (minutes) for momentum aggregation around a stoppage.
WINDOW_MIN = 5

# Canonical stoppage type vocabulary (one of these per stoppage row).
STOPPAGE_TYPES = (
    "hydration",
    "var",
    "injury_huddle",
    "injury_no_huddle",
    "other",
)


def ensure_dirs() -> None:
    """Create the directories the pipeline writes to. Safe to call repeatedly."""
    for d in (RAW_FOTMOB, RAW_COMMENTARY, INTERIM, PROCESSED, SNAPSHOTS, SITE):
        d.mkdir(parents=True, exist_ok=True)
