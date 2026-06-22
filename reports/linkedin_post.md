# LinkedIn post — draft

> Fill the bracketed numbers from the live report once N is large enough (aim for ≥ ~40 hydration
> breaks before leading with a strong claim; until then, frame as "early signal"). Lead with the
> finding — including a null. ~600–900 words, 3–4 charts pulled from the report site.

---

**Do FIFA's new hydration breaks actually kill momentum? I tracked every World Cup match to find out.**

Coaches and commentators have a favourite line about the 2026 World Cup's new **mandatory hydration
breaks** (~22′ and ~67′): they "kill the momentum" of whichever team is on top. It sounds obvious.
But is it true — or is it the kind of thing that feels true on TV and evaporates under data?

So I measured it. [N] hydration breaks later, here's what the numbers say.

**The setup.** I used the per-minute *momentum* series that SofaScore computes for every match as the
outcome, and looked at a simple thing: for the team that was on top in the 5 minutes *before* a
break, what happened to their momentum in the 5 minutes *after*? Then I did the same for two
comparison stoppages of similar length — VAR reviews and injury stoppages — so I could separate the
effect of *the pause itself* from *the coaching huddle* a break creates.

**The headline.** [On average, momentum shifted {{by X}} {away from / toward} the team that had been
on top — 95% CI {{lo..hi}}. State plainly whether this is distinguishable from zero.]

**Why this isn't as obvious as it looks.** The single biggest trap here is *regression to the mean*:
a team that just had a hot five minutes tends to cool off anyway, break or no break. So I ran the
identical analysis at **placebo break times** (17′ and 62′, where no break happens) and on **2022
World Cup matches**, which had no mandated breaks at all. [Report what the placebos show — if they
also show an "effect," the naive result is mostly regression to the mean, and say so.]

**The mechanism.** [If hydration breaks move momentum more than equally-long VAR stops, that points
to the coaching window mattering more than the physical pause. If hot open-air venues don't differ
from cool/domed ones, physical recovery probably isn't the driver. Report whichever way it lands.]

**What I'm taking away.** [1–2 sentences. If null: "The 'momentum killer' is mostly a story we tell
ourselves." If real: state the size in plain terms and the most likely mechanism.]

Everything is reproducible: the code, the daily-updating dataset, and a live report that refreshes
as the tournament goes on. Link in the comments. 👇

*Method notes: momentum from SofaScore (FotMob cross-check), stoppages detected from commentary +
incident feeds, effects conditioned on pre-break momentum, confidence intervals clustered by match,
placebo and historical-baseline checks for regression to the mean.*

---

**Charts to attach (export from the report site):**
1. Effect by stoppage type with 95% CIs (the money chart).
2. Distribution of momentum delta for hydration vs comparisons.
3. Estimate-over-the-tournament (shows the CI tightening as N grows — great for credibility).
4. (Optional) placebo vs real side-by-side.
