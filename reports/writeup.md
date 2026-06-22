# Do hydration breaks kill momentum at the 2026 World Cup?

*Auto-generated from the live dataset — updates daily through the final. Numbers below are
computed from the committed parquet, not hand-edited.*

**Headline.** {{HEADLINE}}

FIFA made in-match hydration breaks (~22′ and ~67′) mandatory at the 2026 World Cup. Coaches and
pundits call them "momentum killers" — a free reset for the team under pressure. This project tests
that claim using **per-minute momentum** as the outcome and other stoppages (VAR, injuries) of
similar length as comparisons, to separate the *pause* from the *coaching window* from *physical
recovery*.

## What the data says so far

For the team that was **on top** of momentum in the 5 minutes before a break, the average change in
the next 5 minutes was **{{HYD_MEAN}}** (95% CI {{HYD_CI}}), across **{{HYD_N}}** hydration breaks.
A negative number means the break pushed momentum *away* from the team that had been pressing — the
"momentum killer" pattern. The chart and table below compare hydration breaks against VAR reviews
and injury stoppages.

> This is a living analysis. Early in the tournament N is small and the confidence interval is wide;
> watch the "estimate over the tournament" chart for whether the effect stabilizes or vanishes as
> data accumulates. A null result is a real, reportable finding.

## How to read these charts
- **Effect by type:** point estimate ± 95% CI (cluster-bootstrapped by match). Bars whose CI crosses
  zero are not distinguishable from "no effect."
- **Distribution:** the spread matters, not just the mean — a few extreme matches can move an average.
- **Estimate over the tournament:** the hydration estimate recomputed at each daily snapshot.

## Method (short)
- **Outcome:** SofaScore per-minute momentum (home-positive), reframed per team, aggregated to
  5-minute pre/post windows around each stoppage. FotMob used as a cross-check.
- **Treatment vs comparison:** hydration breaks vs VAR vs injury stoppages, detected from commentary
  + incident feeds (not a hardcoded clock).
- **Conditioning:** we report the effect for the team that was on top pre-break, because pooling both
  team perspectives averages to zero by construction.
- **Caveats handled:** regression to the mean (the biggest threat), score-state asymmetry,
  substitutions at the break, and non-independent stoppages within a match (match-clustered CIs).
  The 2022-WC historical placebo is run (all 64 matches): it shows a small but non-zero on-top
  decline at fake break times, confirming regression to the mean is real — see
  `reports/historical_placebo.md`.
- **Causal model (signed off):** two-way fixed-effects regression on one row per stoppage
  (`momentum_delta ~ C(stoppage_type)*pre_momentum + score_diff_pre + C(match) + C(team)`, match-
  clustered SEs, VAR reference). The momentum-killer test is the `hydration × pre_momentum`
  interaction; pre-momentum is a continuous regression-to-the-mean control reported with and without.

*Causal estimates are gated: no causal claim is published until the live sample is large enough.
See the [repository](https://github.com/) and `PROJECT_BRIEF.md` for the full design and hypotheses.*
