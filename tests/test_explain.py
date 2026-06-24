"""The per-match modal blurb must not call a faint, fading edge "dominating".

`_match_explanation` describes the 5-minute *average before* each hydration break, which can be a
marginal bottom-decile lead (e.g. Mexico's +4.6 vs South Africa that had already faded by the
whistle). The wording is graded to |pre|, so a marginal lead reads "roughly even" rather than
"on top"/"dominaba". These pin that grading in both languages.
"""

from __future__ import annotations

import polars as pl

from src.report.build_site import _match_explanation
from src.report.i18n import FRAG, TYPES


def _df(pre: float, delta: float, minute: float = 25.0) -> pl.DataFrame:
    return pl.DataFrame(
        [{
            "match_id": "1", "is_home": True, "clock_minute": minute,
            "stoppage_type": "hydration",
            "momentum_pre_5min_mean": pre, "momentum_delta": delta,
        }]
    )


def test_marginal_lead_is_not_called_on_top():
    out = _match_explanation(_df(4.0, 1.0), "1", "Mexico", "South Africa", FRAG["en"], TYPES["en"])
    assert "roughly even" in out
    assert "on top" not in out   # a +4 bottom-decile edge must not read as dominance
    assert "Mexico" in out


def test_strong_lead_reads_well_on_top():
    out = _match_explanation(_df(50.0, 3.0), "1", "Mexico", "South Africa", FRAG["en"], TYPES["en"])
    assert "well on top" in out


def test_zero_delta_holds_steady():
    out = _match_explanation(_df(10.0, 0.2), "1", "Mexico", "South Africa", FRAG["en"], TYPES["en"])
    assert "held roughly steady" in out


def test_spanish_marginal_drops_dominaba():
    out = _match_explanation(_df(4.0, 1.0), "1", "México", "Sudáfrica", FRAG["es"], TYPES["es"])
    assert "parejo" in out
    assert "dominaba" not in out   # the Mexico-South Africa overclaim, fixed
