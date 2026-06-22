# Terms-of-Service review — can we publish this?

**Date:** 2026-06-22. **Purpose:** decide whether/how to make the repo + report public without
violating the data providers' terms. **Bottom line:** publish the **code + derived analysis**
(non-commercial, attributed), **never the raw provider payloads**, and be ready to take down on
request. The strict reading is that scraping SofaScore/FotMob at all is disallowed by their terms —
so this is a calculated, low-profile, non-commercial research posture, not a "fully compliant" one.

## What each source allows

### SofaScore — restrictive (primary momentum source)
Their Terms & Conditions state the site and its contents are owned by SofaScore and "may not be
copied, modified, reproduced, downloaded or distributed in any way without express prior written
permission." They also note they cannot expose official API endpoints due to upstream data-provider
agreements. → **Scraping is against their terms; redistributing raw payloads is clearly out.**

### FotMob — restrictive (cross-check + commentary)
Their ToS (`fotmob.com/tos.txt`) is explicit:
- "Use of the data, content, or any information displayed on FotMob for any purpose, including but
  not limited to scraping, reproduction, redistribution, or commercial purposes, without the express
  written consent of FotMob is strictly prohibited."
- "The use of automatic services (robots, spiders, indexing, etc.) … is expressly forbidden."
- Grants only a "personal … non-commercial use" license to the app itself.
→ **Scraping + redistribution disallowed; personal non-commercial app use is fine.**

### StatsBomb Open Data — permissive (historical baseline)
Free for research and analytics with **attribution**: state the source as StatsBomb and use their
logo when you publish research/insights derived from the data. → **Safe to use and to publish derived
analysis, with attribution + logo.** This is the only source we can lean on without tension.

## Our posture (what reduces risk)

1. **Derived-data-only** — enforced in `.gitignore` (`data/raw/`, `data/interim/` never committed).
   We publish the aggregated stoppage table + snapshots, not provider payloads. ✅ already in place.
2. **Non-commercial** — portfolio/research only; no ads, no paywall, no resale. Keep it that way.
3. **Attribution** — credit SofaScore/FotMob as momentum sources and StatsBomb (with logo) for the
   historical baseline, in the README and the report footer.
4. **No bulk republication / takedown-on-request** — add a short data-use note inviting providers to
   request removal; comply immediately if asked.
5. **Polite scraping** — low rate, only matches we analyze, cached so we never re-fetch.

## Residual risk (be honest)
- SofaScore/FotMob terms prohibit scraping itself, regardless of what we redistribute. Publishing the
  *scraper code* advertises that we do it. Risk is low for a small non-commercial project but nonzero
  (worst realistic case: a takedown/cease-and-desist, not damages).
- Mitigations if you want to lower it further: (a) keep the SofaScore/FotMob scraper modules in the
  repo but lead the README with the StatsBomb-based historical analysis, (b) or make the repo public
  but the scraper a documented-but-not-headlined component, (c) or keep raw scraping local and publish
  only the StatsBomb + derived WC2026 numbers.

## Recommendation
Proceed to publish **public, non-commercial, derived-only, attributed, takedown-friendly**. Add the
attribution + data-use note (README footer already has a derived-data line — extend it). This is the
common posture for football-analytics hobby projects and is a reasonable risk for a portfolio piece.

## Decision (user)
- [ ] Go public with the posture above
- [ ] Go public but de-emphasize the live scraper (lead with StatsBomb/derived results)
- [ ] Keep private for now

*(Action only happens at item #3 "commit → push → enable Pages" — this doc is the input to that call.)*
