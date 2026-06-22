"""Editorial report template + prose (editable copy, separated from data).

The full page is a `{{TOKEN}}`-templated HTML string based on the supplied design
(`WC2026 Momentum Editorial Design`). `build_site.py` computes the token values from
the live committed data and substitutes them (plain str.replace, so the CSS braces in
the <style> block are safe).

Editorial integrity:
- All three pundit quotes are real and sourced (links inline).
- Claims are kept to what the stats support: the *descriptive* ordering is real; the
  causal "huddle" reading is flagged as suggestive, not yet significant.
- Source of truth: FotMob per-minute momentum + ESPN commentary (not SofaScore).
"""

from __future__ import annotations

TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Do hydration breaks really kill momentum? — WC2026 Stoppage Momentum</title>
<meta name="description" content="Do FIFA's mandatory hydration breaks shift in-match momentum at the 2026 World Cup? A living, data-driven analysis.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#EFEBDF}
  a{color:inherit}
  ::selection{background:#E5482E;color:#FCFAF3}
  @keyframes livepulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.78)}}
  .mb-card{transition:transform .14s ease, box-shadow .14s ease}
  .mb-card:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(26,24,19,.10)}
  .src{font-family:'IBM Plex Mono',monospace;color:#E5482E;text-decoration:none;border-bottom:1px solid rgba(229,72,46,.4)}
</style></head>
<body>
<article style="background:#EFEBDF;color:#1A1813;font-family:'IBM Plex Sans',sans-serif;width:100%;min-height:100vh;overflow-x:hidden">

  <!-- MASTHEAD -->
  <header style="max-width:840px;margin:0 auto;padding:22px 40px 0;display:flex;justify-content:space-between;align-items:center;gap:24px;flex-wrap:wrap">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.22em;text-transform:uppercase;color:#1A1813;font-weight:600">WC2026 · Stoppage Momentum Study</div>
    <div style="display:flex;align-items:center;gap:9px;font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.08em;color:#6B6557">
      <span style="width:8px;height:8px;border-radius:50%;background:#E5482E;display:inline-block;animation:livepulse 1.8s ease-in-out infinite"></span>
      LIVE · UPDATED {{UPDATED_DATE}}
    </div>
  </header>
  <div style="max-width:840px;margin:14px auto 0;padding:0 40px"><div style="height:2px;background:#1A1813"></div></div>

  <!-- HERO -->
  <section style="max-width:840px;margin:0 auto;padding:56px 40px 30px">
    <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:26px">The Hydration-Break Experiment</div>
    <h1 style="font-family:'Newsreader',serif;font-weight:500;font-size:clamp(46px,7.4vw,104px);line-height:.95;letter-spacing:-.015em;max-width:15ch;text-wrap:balance">Do hydration breaks really kill momentum?</h1>
    <p style="font-family:'Newsreader',serif;font-size:clamp(20px,2.4vw,28px);line-height:1.45;max-width:760px;margin-top:30px;color:#332F26;text-wrap:pretty">FIFA made in-match hydration breaks mandatory at the 2026 World Cup. Coaches and pundits call them momentum killers. With {{N_MATCHES}} matches in, the data is starting to agree — though maybe not for the reason you'd think.</p>
    <div style="display:flex;gap:28px;flex-wrap:wrap;margin-top:34px;font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.08em;color:#6B6557">
      <span>BY THE WC2026 MOMENTUM PROJECT</span>
      <span>{{N_MATCHES}} MATCHES · {{N_STOPPAGES}} STOPPAGES · LIVING ANALYSIS</span>
    </div>
  </section>

  <!-- HEADLINE STAT BAND -->
  <section style="background:#1A1813;color:#EFEBDF;margin-top:30px">
    <div style="max-width:840px;margin:0 auto;padding:54px 40px;display:flex;gap:48px;align-items:center;flex-wrap:wrap">
      <div style="flex:0 0 auto;display:flex;align-items:flex-start;gap:6px">
        <span style="font-family:'Newsreader',serif;font-weight:500;font-size:clamp(34px,6vw,72px);color:#E5482E;line-height:1;align-self:flex-start;margin-top:.18em">−</span>
        <span style="font-family:'Newsreader',serif;font-weight:500;font-size:clamp(96px,17vw,210px);line-height:.82;color:#E5482E;letter-spacing:-.02em">{{HERO_DELTA}}</span>
      </div>
      <div style="flex:1 1 320px;min-width:280px">
        <p style="font-family:'Newsreader',serif;font-size:clamp(21px,2.3vw,29px);line-height:1.4;color:#EFEBDF;max-width:34ch">momentum points — the average swing <em style="font-style:italic;color:#E5C9A0">away</em> from the team on top in the five minutes after a hydration break.</p>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.07em;color:#948D7C;margin-top:18px;line-height:1.75">
          <div>MEAN OF {{HYD_N}} BREAKS WHERE A TEAM HELD THE EDGE</div>
          <div>FOTMOB PER-MINUTE MOMENTUM SCALE</div>
        </div>
      </div>
    </div>
  </section>

  <!-- 01 — THE CLAIM -->
  <section style="max-width:840px;margin:0 auto;padding:64px 40px 18px">
    <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:22px">01 — The claim on TV</h2>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820;margin-bottom:20px">Every match it's the same beat. The referee blows for the mandated break midway through each half, both sides jog to the touchline for three minutes of water and instructions — and not everyone is convinced it belongs there.</p>
    <blockquote style="font-family:'Newsreader',serif;font-style:italic;font-size:clamp(24px,2.9vw,33px);line-height:1.34;color:#1A1813;border-left:3px solid #E5482E;padding:6px 0 6px 28px;margin:34px 0 16px">"Hydration breaks are a bit interesting … every time going to a commercial is a bit — not really that I like it. If it's really hot it would be good to put them in. But you have to look at it in every game, separately."</blockquote>
    <div style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.13em;color:#6B6557;text-transform:uppercase;padding-left:28px;margin-bottom:34px">Virgil van Dijk · Netherlands captain, after the 2–2 draw with Japan · <a class="src" href="https://www.espn.com/soccer/story/_/id/49071612/virgil-van-dijk-criticises-world-cup-hydration-breaks">ESPN</a></div>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820">Van Dijk's gripe is flow and ad breaks. The sharper charge is tactical — and the booth even has a name for it. ITV's Emma Hayes calls them <em style="font-style:italic">momentum breaks</em>: <span style="color:#1A1813">"advantageous for the team losing momentum … when you're on top, you don't want it; when you're losing, you do."</span> <a class="src" href="https://www.espn.com/soccer/story/_/id/48945011/why-there-drinks-breaks-2026-world-cup-fifa-criticised">[ESPN]</a> A free reset for the team under pressure. The question is whether it survives contact with the data.</p>
  </section>

  <!-- 02 — MONEY CHART -->
  <section style="max-width:840px;margin:0 auto;padding:50px 40px 30px">
    <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:10px">02 — What every stoppage does</h2>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.58;color:#2B2820;margin-bottom:40px">For the team on top before a break, here's how much momentum it loses in the next five minutes — by what kind of stoppage interrupted it. Every bar points the same way. The hydration break points furthest.</p>

    <div style="border-top:2px solid #1A1813;padding-top:30px">
      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:26px;gap:16px;flex-wrap:wrap">
        <span style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.14em;color:#6B6557">MEAN MOMENTUM CHANGE FOR THE TEAM ON TOP</span>
        <span style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.1em;color:#6B6557">{{CI_CAPTION}}</span>
      </div>
      <div style="position:relative">
        <div style="position:absolute;inset:0;pointer-events:none">
          <div style="position:absolute;top:0;bottom:34px;right:0;width:1px;background:#1A1813"></div>
          <div style="position:absolute;top:0;bottom:34px;right:31.25%;width:1px;background:rgba(26,24,19,.14)"></div>
          <div style="position:absolute;top:0;bottom:34px;right:62.5%;width:1px;background:rgba(26,24,19,.14)"></div>
          <div style="position:absolute;top:0;bottom:34px;right:93.75%;width:1px;background:rgba(26,24,19,.14)"></div>
        </div>
        {{MONEY_ROWS}}
        <div style="position:relative;height:30px;margin-top:6px">
          <span style="position:absolute;right:0;transform:translateX(50%);font-family:'IBM Plex Mono',monospace;font-size:12px;color:#1A1813;font-weight:600">0</span>
          <span style="position:absolute;right:31.25%;transform:translateX(50%);font-family:'IBM Plex Mono',monospace;font-size:12px;color:#6B6557">−10</span>
          <span style="position:absolute;right:62.5%;transform:translateX(50%);font-family:'IBM Plex Mono',monospace;font-size:12px;color:#6B6557">−20</span>
          <span style="position:absolute;right:93.75%;transform:translateX(50%);font-family:'IBM Plex Mono',monospace;font-size:12px;color:#6B6557">−30</span>
        </div>
      </div>
      <p style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.04em;color:#948D7C;margin-top:14px;line-height:1.6">{{INTERVAL_NOTE}}</p>
    </div>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820;margin-top:34px">{{COMPARE_SENTENCE}}</p>
  </section>

  <!-- 03 — MATCH BY MATCH -->
  <section style="border-top:1px solid #DDD6C5;background:#EAE5D6;margin-top:30px">
    <div style="max-width:840px;margin:0 auto;padding:60px 40px 56px">
      <div style="margin-bottom:34px">
        <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:18px">03 — Match by match</h2>
        <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.55;color:#2B2820;text-wrap:pretty">The aggregate is built from these. Every match in the set so far, with its minute-by-minute momentum — the wave rises when the <strong style="font-weight:600">home</strong> side is on top, drops when the <strong style="font-weight:600">away</strong> side takes over, and dashed lines mark detected stoppages.</p>
      </div>
      <div style="display:flex;gap:26px;flex-wrap:wrap;align-items:center;margin-bottom:28px;font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.06em;color:#5A5547">
        <span style="display:flex;align-items:center;gap:8px"><span style="width:18px;height:10px;background:#9CC4E0;display:inline-block;border-radius:1px"></span>HOME ON TOP</span>
        <span style="display:flex;align-items:center;gap:8px"><span style="width:18px;height:10px;background:#EBC09A;display:inline-block;border-radius:1px"></span>AWAY ON TOP</span>
        <span style="display:flex;align-items:center;gap:8px"><span style="width:0;height:14px;border-left:2px dashed #3E88C7;display:inline-block"></span>HYDRATION</span>
        <span style="display:flex;align-items:center;gap:8px"><span style="width:0;height:14px;border-left:2px dashed #2E8B57;display:inline-block"></span>VAR</span>
        <span style="display:flex;align-items:center;gap:8px"><span style="width:0;height:14px;border-left:2px dashed #E08A4B;display:inline-block"></span>INJURY</span>
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px">
        {{MATCH_CARDS}}
      </div>
      <p style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.04em;color:#948D7C;margin-top:24px;line-height:1.6">Per-minute momentum rendered from FotMob (derived analysis only — raw payloads not redistributed). One panel per scraped match; stoppage markers from the reconciled FotMob + ESPN commentary feed.</p>
    </div>
  </section>

  <!-- 04 — MECHANISM -->
  <section style="background:#1A1813;color:#EFEBDF">
    <div style="max-width:840px;margin:0 auto;padding:62px 40px">
      <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:18px">04 — Is it the huddle, not the water?</h2>
      <p style="font-family:'Newsreader',serif;font-size:clamp(22px,2.6vw,30px);line-height:1.42;color:#EFEBDF;margin-bottom:42px;text-wrap:pretty">Line the stoppages up by how much of a coaching window they create, and the momentum swing roughly tracks them. The more a break looks like a timeout, the harder the leading team tends to fall.</p>
      <div style="display:grid;grid-template-columns:1fr 1fr;border-top:1px solid rgba(255,255,255,.22)">
        <div style="padding:26px 30px 26px 0;border-right:1px solid rgba(255,255,255,.14)">
          <div style="font-family:'Newsreader',serif;font-size:48px;font-weight:500;color:#E5482E;line-height:1">{{MECH_HYD}}</div>
          <div style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:15px;margin-top:8px;color:#EFEBDF">Hydration break</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:13.5px;line-height:1.5;color:#A9A290;margin-top:6px">Three scheduled minutes. Full organised huddle, water, tactical reset.</p>
        </div>
        <div style="padding:26px 0 26px 30px">
          <div style="font-family:'Newsreader',serif;font-size:48px;font-weight:500;color:#E5C9A0;line-height:1">{{MECH_VAR}}</div>
          <div style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:15px;margin-top:8px;color:#EFEBDF">VAR review</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:13.5px;line-height:1.5;color:#A9A290;margin-top:6px">A long pause, players idle — but no formal touchline instruction.</p>
        </div>
        <div style="padding:26px 30px 26px 0;border-right:1px solid rgba(255,255,255,.14);border-top:1px solid rgba(255,255,255,.14)">
          <div style="font-family:'Newsreader',serif;font-size:48px;font-weight:500;color:#E5C9A0;line-height:1">{{MECH_IH}}</div>
          <div style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:15px;margin-top:8px;color:#EFEBDF">Injury · with huddle</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:13.5px;line-height:1.5;color:#A9A290;margin-top:6px">Unscheduled, but long enough for a coach to gather the side.</p>
        </div>
        <div style="padding:26px 0 26px 30px;border-top:1px solid rgba(255,255,255,.14)">
          <div style="font-family:'Newsreader',serif;font-size:48px;font-weight:500;color:#E5C9A0;line-height:1">{{MECH_INH}}</div>
          <div style="font-family:'IBM Plex Sans',sans-serif;font-weight:600;font-size:15px;margin-top:8px;color:#EFEBDF">Injury · no huddle</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:13.5px;line-height:1.5;color:#A9A290;margin-top:6px">Quick stoppage, play resumes before anyone regroups.</p>
        </div>
      </div>
      <p style="font-family:'Newsreader',serif;font-size:20px;line-height:1.6;color:#D8D2C2;margin-top:34px">If a water break were only about <em style="font-style:italic">rest</em>, an equally long VAR pause should match it. So far it doesn't quite — which points at the <strong style="font-weight:600;color:#EFEBDF">coaching window</strong> a break creates. Belgium's Rudi Garcia put it plainly: <span style="color:#EFEBDF">"for me, it's a coaching break more than a cooling break."</span> <a class="src" href="https://www.aljazeera.com/sports/2026/6/20/hydration-break-boos-how-fifa-united-players-fans-coaches-at-world-cup">[Al Jazeera]</a> But read it carefully: once we control for pre-break momentum and pit hydration against a duration-matched VAR, the gap is <strong style="font-weight:600;color:#EFEBDF">not yet statistically distinguishable</strong>. The ordering is suggestive — not a verdict.</p>
    </div>
  </section>

  <!-- 05 — THE CATCH -->
  <section style="max-width:840px;margin:0 auto;padding:64px 40px 18px">
    <h2 style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:22px">05 — The catch worth stating out loud</h2>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820;margin-bottom:20px">A team that just had a blazing five minutes tends to cool off <em style="font-style:italic">anyway</em> — break or no break. That's regression to the mean, and it's the single biggest threat to reading too much into the bars above.</p>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820;margin-bottom:20px">So the same test was run on the 2022 World Cup, which had no mandated breaks at all, at the fake 22′ and 67′ marks. The team on top still slipped — a small, non-zero amount whose confidence interval excludes zero. Some of the 2026 effect is gravity, not the water bottle.</p>
    <div style="background:#1A1813;color:#EFEBDF;padding:30px 32px;margin:30px 0;border-radius:2px">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.16em;color:#E5C9A0;margin-bottom:14px">2022 PLACEBO · NO BREAKS EXISTED</div>
      <div style="display:flex;gap:36px;flex-wrap:wrap;align-items:baseline">
        <div><span style="font-family:'Newsreader',serif;font-size:44px;font-weight:500;color:#EFEBDF">{{PLACEBO_MEAN}}</span><span style="font-family:'IBM Plex Mono',monospace;font-size:12px;color:#948D7C;margin-left:10px">xT units</span></div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;color:#C9C3B2;line-height:1.6">{{PLACEBO_CI}}<br>{{PLACEBO_N}}</div>
      </div>
    </div>
    <p style="font-family:'Newsreader',serif;font-size:21px;line-height:1.62;color:#2B2820">Which is exactly why the model controls for pre-break momentum, clusters its errors by match, and won't print a causal headline until the live sample is big enough. The interaction regression-to-the-mean <em style="font-style:italic">can't</em> explain — a break hitting harder precisely when a team is on top — is the part still being watched.</p>
  </section>

  <!-- LIVING / TREND -->
  {{TREND}}

  <!-- BOTTOM LINE -->
  <section style="max-width:840px;margin:0 auto;padding:46px 40px 20px">
    <div style="border-top:2px solid #1A1813;border-bottom:2px solid #1A1813;padding:44px 0">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#E5482E;font-weight:600;margin-bottom:24px">The bottom line — so far</div>
      <p style="font-family:'Newsreader',serif;font-weight:500;font-size:clamp(26px,3.6vw,46px);line-height:1.22;letter-spacing:-.01em;max-width:24ch">The momentum killer looks real — and it might be a coaching timeout in disguise. But the sample is young, the intervals are wide, and the verdict stays open until the final.</p>
    </div>
  </section>

  <!-- METHOD / FOOTER -->
  <footer style="background:#1A1813;color:#C9C3B2;margin-top:30px">
    <div style="max-width:840px;margin:0 auto;padding:56px 40px 60px">
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:32px 40px">
        <div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;color:#E5C9A0;margin-bottom:12px">OUTCOME</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:14px;line-height:1.62">FotMob per-minute momentum (home-positive), reframed per team, aggregated to 5-minute pre/post windows around each stoppage.</p>
        </div>
        <div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;color:#E5C9A0;margin-bottom:12px">IDENTIFICATION</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:14px;line-height:1.62">Duration-matched comparison of hydration vs VAR vs injury stoppages. Stoppages detected from ESPN commentary, not a hardcoded clock.</p>
        </div>
        <div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;color:#E5C9A0;margin-bottom:12px">CAVEATS HANDLED</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:14px;line-height:1.62">Regression to the mean (2022 historical placebo), score-state asymmetry, substitutions at the break, match-clustered confidence intervals.</p>
        </div>
        <div>
          <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;color:#E5C9A0;margin-bottom:12px">REPRODUCE</div>
          <p style="font-family:'IBM Plex Sans',sans-serif;font-size:14px;line-height:1.62">Daily-updating dataset and live report regenerate from the committed parquet through the July 19 final.</p>
          <a href="{{PAGES_URL}}" class="src" style="font-size:13px;display:inline-block;margin-top:12px">github.com/valternunez/wc2026-momentum ↗</a>
        </div>
      </div>
      <div style="height:1px;background:rgba(255,255,255,.14);margin:40px 0 24px"></div>
      <div style="display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.1em;color:#7E776A">
        <span>WC2026 STOPPAGE MOMENTUM STUDY · SNAPSHOT {{SNAPSHOT_DATE}}</span>
        <span>LIVING ANALYSIS · NUMBERS COMPUTED FROM THE COMMITTED DATASET</span>
      </div>
    </div>
  </footer>
</article>
</body></html>
"""
