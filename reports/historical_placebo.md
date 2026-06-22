# Historical placebo — how much "effect" is just regression to the mean?

**Source:** StatsBomb open data, 2022 men's World Cup (64 matches). **Built by:**
`python -m src.pipeline --historical-placebo` → `data/processed/historical_placebo.parquet`.

## The test
The 2022 World Cup had **no mandated hydration breaks**. So we apply our *exact* analysis pipeline at
the same nominal break minutes (22′ and 67′) on those matches, using an event-based **xT-flow
momentum proxy** as the outcome (there's no SofaScore momentum series for 2022). Any non-zero "effect"
at these fake break times is **bias** — almost entirely regression to the mean (RTM): a team that was
on top in the preceding 5 minutes tends to cool off whether or not anything happened.

## Result
For the team that was on top of momentum pre-"break":

| metric | value |
|--------|-------|
| mean momentum delta (post − pre) | **−0.0080** |
| 95% CI (cluster-bootstrapped by match) | **−0.0121 … −0.0041** |
| stoppages (on-top rows) | 128 |
| matches | 64 |

## What it means
- **The CI excludes zero** → RTM is real and measurable: even with no break, the team on top loses a
  little momentum on average. This is precisely the confound the brief flags as the single biggest
  threat.
- **Units caveat:** this number is in xT-flow units, *not* the SofaScore momentum scale used for the
  live 2026 analysis, so its *magnitude* is not directly comparable to the live deltas — treat it as a
  **directional baseline**, not a subtractable constant.
- **Design consequence:** the live causal model **must control for pre-break momentum** so the
  hydration estimate isn't just re-measuring RTM. Our signed-off spec does exactly this
  (`momentum_pre_5min_mean` as a continuous control, reported with and without it) — see
  `src/analysis/regression.py`. The interaction `hydration × pre-momentum` is the part RTM cannot
  explain, because RTM applies equally at placebo and real break times.

## Reproduce
```
uv run python -m src.pipeline --historical-placebo     # all 64 matches
uv run python -c "import polars as pl; from src.analysis.historical_placebo import summarize_placebo; \
  print(summarize_placebo(pl.read_parquet('data/processed/historical_placebo.parquet')))"
```
