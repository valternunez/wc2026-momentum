# World Cup 2026 — Stoppage Momentum Analysis

## Project goal

Quantify how in-match stoppages affect game momentum at the 2026 FIFA World Cup, using FIFA's new mandatory hydration breaks as the primary natural experiment and other stoppage types (VAR, injuries, historical cooling breaks) as comparison conditions to isolate the mechanism.

Output: a reproducible dataset, an analysis notebook, a short writeup with charts suitable for a LinkedIn/portfolio post.

## Research questions

**Primary.** Do FIFA's mandated 3-minute hydration breaks (~22' and ~67') shift in-match momentum, and if so, in whose favor?

**Secondary (mechanism).** Is any observed effect driven by (a) the pause itself, (b) the coaching huddle, or (c) physical recovery? We answer this by comparing hydration breaks to other stoppages of similar duration that vary on those dimensions.

**Tertiary.** What conditions moderate the effect? Score state, pre-stoppage momentum, temperature, substitution at the break, and home/away/neutral status.

## Hypotheses

1. Hydration breaks shift momentum away from the team that was on top pre-break (the "momentum killer" claim from coaches and pundits).
2. The effect is larger for hydration breaks than for VAR reviews of similar duration — implying the coaching window matters more than the pause.
3. Hydration breaks at hot, open-air venues show no larger effect than breaks at domed/cool venues — implying physical recovery is not the main mechanism.
4. Substitutions made during a break amplify the momentum shift.

Each of these is a directional, testable prediction. The interesting outcomes are also the null ones — if 1 fails, "momentum break" narrative is media noise.

## Data sources

### Live momentum series (primary outcome)
- **SofaScore** match pages expose a per-minute momentum series. Scrape via their internal API used by the web app.
- **FotMob** also exposes a momentum series via its mobile API. Use as a cross-check; if the two diverge meaningfully, prefer SofaScore and report the disagreement.
- Scrape for every WC 2026 match as it's played. Persist raw JSON to disk before any transformation.

### Stoppage classification (treatment definition)
- Match commentary feeds from BBC Sport, ESPN, and FotMob have timestamped events including injuries, VAR checks, substitutions, goals, cards. Scrape and reconcile across at least two sources.
- Hydration breaks are deterministic (≈22' and ≈67') but the referee has discretion to delay them around other stoppages. Detect them from the commentary feed, not from a hardcoded clock time.

### Historical / placebo data
- **StatsBomb Open Data** GitHub repo: 2022 men's WC + 2023 women's WC for event-level baselines. Used both as a sanity check on our momentum metric and as a historical baseline for cooling-break behavior.
- **FIFA Club World Cup 2025** had cooling breaks under similar conditions in the US — try to source commentary/momentum data for those matches as a pre-2026 baseline.

### Confounders / context
- Stadium metadata (domed vs open, indoor temp control).
- Match-time weather: temperature, humidity, WBGT if available.
- Lineups, score state at each stoppage, substitutions made during the break.
- FBref for match-level summary stats as sanity checks.

## Stoppage-level data schema

The unit of analysis is a single stoppage. One row per stoppage per match per team-perspective (so two rows per stoppage — one from each team's POV — to make the "in whose favor" analysis trivial). Suggested columns:

```
match_id, match_date, stage, venue, dome, temp_c, humidity, wbgt
team, opponent, is_home
stoppage_id, stoppage_type   # hydration | var | injury_huddle | injury_no_huddle | other
clock_minute, real_duration_seconds
score_team_pre, score_opp_pre, score_diff_pre
red_cards_pre_team, red_cards_pre_opp
sub_made_during_break (bool), subs_count_during_break
momentum_pre_5min_mean, momentum_pre_5min_slope    # team-perspective signed
momentum_post_5min_mean, momentum_post_5min_slope
momentum_delta                                      # post - pre, primary outcome
xt_pre_5min, xt_post_5min
field_tilt_pre_5min, field_tilt_post_5min
shots_pre_5min, shots_post_5min
ppda_pre_5min, ppda_post_5min                       # if computable
```

Compute event-derived columns (xT, field tilt, PPDA) only when event data is available — StatsBomb for 2022/2023, commentary-derived approximations otherwise. The momentum series scraped from SofaScore/FotMob is the always-available outcome.

## Momentum operationalization

**Primary metric.** Signed momentum series from SofaScore (positive = home team, negative = away), reframed to team-perspective per row. Aggregate to 5-minute pre/post windows around each stoppage.

**Secondary metrics from event data** (where available):
- xT per minute (Karun Singh's expected threat model — implementation in `socceraction` Python library).
- Field tilt: rolling share of touches in opponent's final third.
- Shot rate and shot xG.
- PPDA as a pressing proxy.

Build these as a `momentum_features.py` module so the same windowing logic applies to any stoppage.

## Analysis plan

### Phase 1 — descriptive
- Mean momentum delta by stoppage type, with bootstrapped CIs.
- Distribution plots, not just point estimates.
- Sanity check: does the SofaScore momentum series correlate with xT-flow on the 2022 WC matches where we have both? If not, the metric is suspect.

### Phase 2 — causal
- Two-way fixed effects regression: `momentum_delta ~ stoppage_type + pre_momentum + duration + score_diff_pre + (match FE) + (team FE)`.
- The "momentum-killer" claim implies a negative interaction between `stoppage_type=hydration` and `pre_momentum`. Test it.
- Duration-matched comparison: restrict to stoppages 2–4 min long, compare hydration vs VAR vs injury-with-huddle vs injury-without-huddle. This is the mechanism test.
- Heterogeneous effects: by venue type, temperature bin, substitution-at-break.

### Phase 3 — placebo & robustness
- **Placebo break time.** Run the same analysis on the 17' and 62' marks (5 min before real breaks) in matches without actual stoppages there. If we see "effects" at placebo times, the design is broken.
- **Historical placebo.** Apply the same pipeline to 2022 WC matches at the 22'/67' marks — there were no mandated breaks then, so any "effect" is bias.
- **Regression to the mean.** Control for pre-stoppage momentum explicitly, and report results both with and without that control. The naive comparison will overstate the effect.
- **Selection on injuries.** Drop injury stoppages where the player resumes within 30 seconds; report injury-stoppage results separately with caveats.

## Confounders and pitfalls to handle explicitly

- **Regression to the mean** is the single biggest threat. A team that just had a hot 5 minutes is, on average, regressing whether or not a break happens.
- **Selection on injuries** — they correlate with intensity and score state, and sometimes are tactically feigned.
- **VAR reviews** typically follow potential goals or red cards — score state often changes during them. Either drop VARs that result in a goal/card or analyze them split by outcome.
- **Score state asymmetry** — losing teams behave differently. Always condition on `score_diff_pre`.
- **Substitutions at the break** are a real co-treatment. Report results both pooled and split by sub/no-sub.
- **Multiple stoppages per match** are not independent. Cluster standard errors at the match level.
- **Stoppage time accounting** — the clock runs during hydration breaks, so the "67'" stoppage is real-time-shifted from the nominal mark. Use actual commentary timestamps, not clock minutes.

## Tech stack

- **Python 3.12**, `uv` for env management.
- **Data**: `polars` (preferred) or `pandas`, `httpx` for scraping, `selectolax` or `parsel` for HTML where needed. Persist raw responses; never re-scrape during analysis.
- **Football-specific**: `socceraction` for xT, `mplsoccer` for pitch plots.
- **Stats**: `statsmodels` for fixed-effects regression, `linearmodels` if we need proper panel methods, `scipy` for bootstrap.
- **Viz**: `plotly` for interactive (consistent with the Ballon d'Or piece), `matplotlib`/`mplsoccer` for static publication-style charts.
- **Notebook**: `marimo` preferred over Jupyter for reproducibility, but Jupyter is fine if it's faster to ship.

## Project structure

```
wc2026-momentum/
├── CLAUDE.md
├── pyproject.toml
├── data/
│   ├── raw/             # untouched scraped JSON/HTML, gitignored
│   ├── interim/         # parsed but not joined
│   └── processed/       # the stoppage-level table (parquet)
├── src/
│   ├── scrape/          # sofascore.py, fotmob.py, commentary.py
│   ├── parse/           # stoppage detection, momentum extraction
│   ├── features/        # momentum_features.py, xt, field_tilt, ppda
│   ├── analysis/        # regressions, plots
│   └── viz/             # chart functions used in the writeup
├── notebooks/
│   └── 01_explore.py    # marimo
├── reports/
│   └── writeup.md
└── tests/
```

## Suggested phasing — start here

Don't try to build everything before scraping. Get a thin slice working end-to-end on three matches first, then scale.

1. **Day 1.** Scrape one SofaScore match's momentum series + commentary. Get the JSON shape pinned down. Persist raw to disk.
2. **Day 2.** Stoppage detection from commentary — start with hydration breaks (easiest) and VAR (next easiest). Build the row schema for one match.
3. **Day 3.** Scale to all played WC 2026 matches so far. Backfill as new matches happen.
4. **Day 4.** Add 2022 WC StatsBomb data and verify the momentum-feature pipeline on it.
5. **Day 5.** Run Phase 1 descriptives. Decide whether the signal is real enough to invest in Phase 2.
6. **Day 6+.** Causal analysis, placebos, writeup.

Resist the urge to over-engineer the scrapers before you have any data on disk.

## Deliverables

- A reproducible repo with a one-command setup.
- A parquet file of all stoppages across WC 2026 + historical comparison matches.
- An analysis notebook that produces every chart and number in the writeup.
- A 600–900 word LinkedIn-style writeup with 3–4 charts, leading with the headline finding (whatever it is — including a null result).
- A short methodology appendix covering the momentum operationalization, the regression spec, and the placebo tests.

## Out of scope (for v1)

- Player-level fatigue modeling.
- Tracking data (we don't have it).
- Real-time prediction.
- Anything involving betting markets.

## Open questions to flag, don't decide unilaterally

- Whether to include knockout-stage matches if the dataset is still small at writeup time.
- Whether to publish the scraped raw data alongside the repo (check ToS for SofaScore/FotMob).
- Whether to extend to the Women's pre-tournament friendlies or other 2026 international windows as additional comparison data.

Ask before deciding these.

## CLAUDE.md guidance for the agent

Put this in `CLAUDE.md` at the repo root:

- This is a research project, not production code. Prioritize clarity and reproducibility over abstraction. No premature OOP. Functions over classes until a class earns its keep.
- Persist raw scraped data to `data/raw/` before any parsing. Never re-scrape during analysis — read from disk.
- Every analysis result that appears in the writeup must be produced by code in the repo, deterministically, from the parquet in `data/processed/`.
- When in doubt about statistical methodology (FE specification, clustering, bootstrap design), stop and ask rather than guessing — the causal claims are the whole point of the project.
- Prefer `polars` over `pandas` for new code. If extending existing pandas code, don't mix.
- Tests are required for the stoppage-detection logic and the momentum-windowing logic. Other code can ship without tests.
- Commit raw data fixtures (one match) to `tests/fixtures/` so the pipeline can be tested offline.
