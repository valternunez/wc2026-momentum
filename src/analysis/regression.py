"""Phase-2 causal spec — SIGNED OFF 2026-06-22 (primary unit + clustering agreed).

Agreed specification (see plan + PROJECT_BRIEF.md §Phase 2):

* **Unit = one row per stoppage, HOME perspective.** Each stoppage produces two
  mirror-image team rows in the stoppage table; fitting both double-counts and
  corrupts SEs. We collapse to the home-perspective row (momentum is home-positive,
  so `momentum_delta` and `score_diff_pre` are already from the home POV).
* **Primary model (two-way FE, match-clustered SEs):**
      momentum_delta ~ C(stoppage_type) * momentum_pre_5min_mean
                       + score_diff_pre + C(match_id) + C(team)
  The "momentum-killer" claim is the interaction
  `C(stoppage_type)[hydration] : momentum_pre_5min_mean` — momentum shifting AWAY
  from whoever was on top. `momentum_pre_5min_mean` is a CONTINUOUS control, which
  is how we defend against regression to the mean; we report WITH and WITHOUT it.
* **Clustering:** cluster-robust SEs at the match level (stoppages within a match
  are not independent).
* **Sample handling:** VAR reviews that change the score (`var_outcome` indicating
  a goal/penalty awarded) can be dropped or analyzed separately — see
  `split_var_by_outcome`. Injuries are reported separately from hydration/VAR; we
  CANNOT drop sub-30s injuries (no per-stoppage durations in the data) — a caveat.

The team-on-top descriptive cut lives in `src/analysis/descriptive.py` (the
SECONDARY, intuitive framing). **Gate:** no causal claim ships in the writeup until
live N is large enough for stable estimates (`MIN_MATCHES` / `MIN_ROWS` guard).
"""

from __future__ import annotations

import polars as pl

MIN_MATCHES = 8
MIN_ROWS = 30

_BASE_COLS = [
    "momentum_delta", "stoppage_type", "momentum_pre_5min_mean",
    "score_diff_pre", "match_id", "team", "is_home", "var_outcome",
]

# var_outcome values that indicate the score/cards changed during the review.
SCORE_CHANGING_VAR = {"goalAwarded", "penaltyAwarded", "redCard", "goalNotAwarded", "penaltyNotAwarded"}


def to_regression_frame(df: pl.DataFrame):
    """Collapse the stoppage table to ONE row per stoppage (home perspective).

    Returns a pandas DataFrame (statsmodels needs pandas). Drops rows missing the
    outcome or key regressors. Asserts the result has one row per stoppage.
    """
    have = [c for c in _BASE_COLS if c in df.columns]
    home = (
        df.filter(pl.col("is_home") == True)  # noqa: E712 (polars expr, not python bool)
        .select(have)
        .drop_nulls(["momentum_delta", "stoppage_type", "momentum_pre_5min_mean", "match_id"])
    )
    pdf = home.to_pandas()
    # one row per stoppage by construction (home POV); guard against accidental dupes
    if "stoppage_id" in df.columns:
        n_stoppages = df.filter(pl.col("is_home") == True)["stoppage_id"].n_unique()  # noqa: E712
        assert len(pdf) <= n_stoppages, "to_regression_frame produced >1 row per stoppage"
    return pdf


def split_var_by_outcome(pdf, *, drop_score_changing: bool = True):
    """Drop (or keep) VAR reviews whose outcome changed the score/cards.

    Brief: VARs typically follow potential goals/red cards, so score state often
    changes during them — confounding the momentum delta. Default drops them.
    """
    if "var_outcome" not in pdf.columns:
        return pdf
    is_var = pdf["stoppage_type"] == "var"
    changed = pdf["var_outcome"].isin(SCORE_CHANGING_VAR)
    mask = is_var & changed
    if drop_score_changing:
        return pdf[~mask].copy()
    return pdf


def run_twfe(
    df: pl.DataFrame,
    *,
    with_interaction: bool = True,
    control_pre_momentum: bool = True,
    drop_score_changing_var: bool = True,
):
    """Fit the signed-off TWFE spec with match-clustered SEs.

    Pass a polars stoppage table (full, both perspectives) — collapsing to the
    home row happens here. Set `control_pre_momentum=False` for the no-RTM-control
    comparison. Returns a fitted statsmodels result.
    """
    import statsmodels.formula.api as smf

    pdf = to_regression_frame(df)
    pdf = split_var_by_outcome(pdf, drop_score_changing=drop_score_changing_var)

    if pdf["match_id"].nunique() < MIN_MATCHES or len(pdf) < MIN_ROWS:
        raise ValueError(
            f"Not enough data for stable estimates yet "
            f"({len(pdf)} rows / {pdf['match_id'].nunique()} matches; "
            f"need >= {MIN_ROWS} / {MIN_MATCHES}). No causal claim until this passes."
        )

    # Use VAR as the reference category so hydration appears as an explicit
    # contrast (hydration-vs-VAR is the mechanism test) and the momentum-killer
    # interaction term [T.hydration]:pre exists. Fall back if VAR is absent.
    types = sorted(pdf["stoppage_type"].unique())
    ref = "var" if "var" in types else types[0]
    cst = f'C(stoppage_type, Treatment(reference="{ref}"))'

    terms = [cst]
    if control_pre_momentum:
        terms.append(f"{cst} * momentum_pre_5min_mean" if with_interaction else "momentum_pre_5min_mean")
    terms += ["score_diff_pre", "C(match_id)", "C(team)"]
    formula = "momentum_delta ~ " + " + ".join(terms)

    return smf.ols(formula, data=pdf).fit(
        cov_type="cluster", cov_kwds={"groups": pdf["match_id"]}
    )


def momentum_killer_estimate(result) -> dict:
    """Pull the hydration × pre-momentum interaction (the momentum-killer test).

    Returns {coef, se, pvalue, ci_lo, ci_hi} for the hydration interaction term, or
    {} if the term isn't in the model (e.g. interaction disabled / type absent).
    """
    name = next(
        (p for p in result.params.index
         if "momentum_pre_5min_mean" in p and "hydration" in p and ":" in p),
        None,
    )
    if name is None:
        return {}
    ci = result.conf_int().loc[name]
    return {
        "term": name,
        "coef": float(result.params[name]),
        "se": float(result.bse[name]),
        "pvalue": float(result.pvalues[name]),
        "ci_lo": float(ci[0]),
        "ci_hi": float(ci[1]),
    }
