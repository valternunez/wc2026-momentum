"""Methodology appendix + small-N caveat as HTML fragments for the report site.

These return *fragments* (no <html>/<head> wrapper) so `build_site.py` can drop
them directly into the page body. Substance is pulled from PROJECT_BRIEF.md and
reports/writeup.md; kept concise and readable rather than exhaustive.
"""

from __future__ import annotations

import polars as pl

from src.analysis.descriptive import on_top_rows

# Threshold below which we surface a "small N" caveat on the page.
SMALL_N_THRESHOLD = 40


def build_appendix_html() -> str:
    """Return an HTML fragment for the methodology appendix.

    Covers: momentum operationalization, conditioning on team-on-top, placebo
    tests, the regression-to-the-mean caveat, and an explicit note that the
    causal regression specification is held for methodological review.
    """
    return """\
<section class="methodology">
  <h2>Methodology appendix</h2>

  <h3>Momentum operationalization</h3>
  <p>The outcome is <strong>FotMob's</strong> per-minute in-match <em>momentum</em>
  series &mdash; an expected-threat (xT) model of which side is on top (positive =
  home, negative = away). It is FotMob's own model, distinct from the official
  Opta/Stats&nbsp;Perform momentum on FIFA broadcasts; we read it consistently
  across every tournament here so the choice of model cancels in the comparison.
  (SofaScore was the original source but Cloudflare-blocks datacenter IPs, so the
  pipeline runs on FotMob.) We re-frame the series to each team's perspective per
  row, then aggregate it into two 5-minute windows around every stoppage: a
  <strong>pre</strong> window <code>[t&minus;5, t)</code> and a <strong>post</strong>
  window <code>(t, t+5]</code>, excluding the stoppage minute itself. The primary
  outcome is <code>momentum_delta = post_mean &minus; pre_mean</code>. A shots-only
  reconstruction of the curve recovers only ~20% of its variance
  (Pearson&nbsp;r&nbsp;&asymp;&nbsp;0.46), the rest being the build-up play xT
  rewards &mdash; so it is a genuine threat metric, not noise
  (<code>src/analysis/momentum_recon.py</code>). Stoppages are detected from
  commentary and incident feeds (not a hardcoded clock minute), because the referee
  has discretion to delay the nominal ~22&prime; and ~67&prime; breaks around other
  play stoppages.</p>

  <h3>Conditioning on the team that was on top</h3>
  <p>Because every stoppage contributes two mirrored team-perspective rows, the
  <em>pooled</em> mean delta is ~0 by construction. We therefore report the effect
  for the team that was <strong>on top</strong> of momentum pre-break
  (<code>momentum_pre_5min_mean &gt; 0</code>). The "momentum killer" claim is the
  prediction that hydration breaks push momentum <em>away</em> from that team
  (a negative delta).</p>

  <h3>Comparison conditions (mechanism)</h3>
  <p>Hydration breaks are compared against VAR reviews and injury stoppages
  (split by whether a coaching huddle formed) of similar duration. This is what
  lets us separate the <em>pause</em> from the <em>coaching window</em> from
  <em>physical recovery</em>: a larger effect for hydration breaks than for
  duration-matched VAR would implicate the coaching window rather than the pause.</p>

  <h3>Placebo and robustness tests</h3>
  <ul>
    <li><strong>Placebo break times.</strong> The same windowing is run at the
    17&prime; and 62&prime; marks (5 minutes before the real breaks) in matches
    with no actual stoppage there. An "effect" at placebo times would mean the
    design is broken.</li>
    <li><strong>Historical placebo.</strong> The pipeline is applied to all 64
    2022 World Cup matches at the 22&prime;/67&prime; marks — no breaks were
    mandated then, so any measured "effect" is bias. Result: a small but non-zero
    on-top decline (95% CI excludes zero), confirming regression to the mean is
    real and must be controlled for. See <code>reports/historical_placebo.md</code>.</li>
    <li><strong>Selection on injuries.</strong> Injury results are reported
    separately from hydration/VAR. We <em>cannot</em> drop sub-30-second injuries
    (the data has no reliable per-stoppage durations) &mdash; an acknowledged
    limitation rather than a fix.</li>
    <li><strong>Window length.</strong> The on-top effect is recomputed at 4-, 5-
    and 6-minute windows; it stays negative with every 95% interval below zero
    (about &minus;21 to &minus;25), so it is not an artifact of the 5-minute choice.
    See <code>src/analysis/sensitivity.py</code>.</li>
    <li><strong>Non-independence.</strong> Multiple stoppages within a match are
    not independent, so confidence intervals are bootstrapped by resampling
    <em>matches</em> (cluster bootstrap), not rows. Early in the tournament the
    number of match-clusters is small, so the interval is read as indicative
    rather than as a precise <em>p</em>-value.</li>
  </ul>

  <h3>Regression to the mean (the main threat)</h3>
  <p>A team that just had a hot 5 minutes tends to regress in the next 5 minutes
  whether or not a break occurs. This is the single biggest threat to the naive
  comparison, which will overstate the effect. We address it by conditioning and
  reporting on pre-stoppage momentum explicitly, and the causal stage reports
  estimates both with and without controlling for pre-break momentum so the
  regression-to-the-mean contribution is visible.</p>

  <h3>Causal specification (signed off)</h3>
  <p>The descriptive estimates above are <em>not</em> causal claims. The agreed
  causal model is a two-way (match and team) fixed-effects regression on
  <strong>one row per stoppage</strong> (home perspective &mdash; fitting both
  mirrored rows would double-count):</p>
  <p><code>momentum_delta ~ C(stoppage_type)*momentum_pre_5min_mean
  + score_diff_pre + C(match_id) + C(team)</code>, with cluster-robust standard
  errors at the match level and VAR as the reference category.</p>
  <p>The "momentum-killer" claim is the interaction
  <code>hydration &times; pre-momentum</code> (momentum shifting away from the team
  on top) &mdash; the part regression to the mean cannot explain, since RTM applies
  equally at placebo and real break times. Pre-break momentum enters as a
  <em>continuous control</em>; we report estimates <strong>with and without</strong>
  it. Score-changing VAR reviews are dropped (they confound the delta). See
  <code>src/analysis/regression.py</code>.</p>
  <p><strong>Gate:</strong> no causal claim is published until the live sample is
  large enough for stable estimates. See <code>PROJECT_BRIEF.md</code> for the full
  design.</p>
</section>"""


def small_n_notice(df: pl.DataFrame, threshold: int = SMALL_N_THRESHOLD) -> str:
    """Return an HTML caveat fragment when N is small, else an empty string.

    "N" is the number of on-top hydration breaks driving the headline estimate.
    Below `threshold` (default 40) the confidence interval is wide and the
    estimate unstable, so we surface a visible warning. Returns "" otherwise.
    """
    if df is None or df.height == 0:
        n = 0
    else:
        try:
            top = on_top_rows(df)
            n = top.filter(pl.col("stoppage_type") == "hydration").height
        except Exception:
            n = 0

    if n >= threshold:
        return ""

    return (
        '<aside class="small-n-notice" '
        'style="border-left:4px solid #E69F00;background:#fff8e9;'
        'padding:10px 14px;margin:18px 0;border-radius:4px;color:#5a4500;">'
        f"<strong>Small sample ({n} on-top hydration "
        f"break{'s' if n != 1 else ''}).</strong> "
        "Early in the tournament N is small and the confidence interval is wide. "
        "Treat the point estimate as provisional and watch the estimate-over-the-"
        "tournament chart for whether the effect stabilizes or vanishes as data "
        "accumulates. A null result is itself a reportable finding."
        "</aside>"
    )
