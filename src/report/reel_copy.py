"""Reel/TikTok page template (reel.html + reel.es.html) — a ~15s kinetic myth-buster cut.

A standalone, full-bleed 1080x1920 page that auto-plays a fast timeline on load: hook → the
"-N after a break" proof → the twist (the no-break control next to it) → honest verdict → CTA.
Built to be screen-recorded into a Reel/TikTok (src/viz/social.build_reel_video). All copy lives
in i18n.STRINGS as REEL_* tokens and every number resolves through the shared {{TOKEN}} pass in
build_site.build_reel_pages(), so it traces to data/processed/* like the rest of the site.

NOTE: non-raw string — never use backslash-escaped double-quotes (\\") inside; Python would
collapse them and break the inline JS. Single-quoted JS/CSS/attr values throughout.
"""

from __future__ import annotations

TEMPLATE = """<!DOCTYPE html>
<html lang="{{LANG}}"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{{REEL_META_TITLE}}</title>
<meta name="robots" content="noindex">
<meta name="theme-color" content="#14110D">
<meta name="color-scheme" content="light">
<meta name="darkreader-lock">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=IBM+Plex+Sans:wght@500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{color-scheme:light}
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{height:100%}
  body{background:#14110D;font-family:'IBM Plex Sans',sans-serif;overflow:hidden}
  .stage{position:fixed;inset:0;display:grid;place-items:center}
  .frame{position:relative;width:min(100vw, calc(100vh * 9 / 16));height:min(100vh, calc(100vw * 16 / 9));
         background:#EFEBDF;color:#1A1813;overflow:hidden;container-type:size}
  /* progress ticks (subtle) */
  .ticks{position:absolute;top:5cqw;left:8cqw;right:8cqw;display:flex;gap:1.4cqw;z-index:7}
  .tick{flex:1;height:0.8cqw;min-height:3px;border-radius:3px;background:rgba(26,24,19,.14)}
  .tick.on{background:#1A1813}
  /* scenes (centered safe band, clear of platform UI top/bottom) */
  .scene{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;
         padding:18cqw 9cqw;opacity:0;visibility:hidden}
  .scene.show{opacity:1;visibility:visible}
  .kicker{font-family:'IBM Plex Mono',monospace;font-weight:600;letter-spacing:.2em;text-transform:uppercase;
          font-size:3.3cqw;color:#C03A22}
  .hookline{font-family:'Newsreader',serif;font-weight:500;font-size:13cqw;line-height:1.0;letter-spacing:-.02em;margin-top:5cqw}
  .hookline span{display:block}
  .kill{color:#C03A22;font-style:italic}
  .tag{font-family:'IBM Plex Mono',monospace;font-size:3.6cqw;letter-spacing:.04em;color:#6B6557;margin-top:6cqw}
  .bignum{font-family:'Newsreader',serif;font-weight:500;font-size:40cqw;line-height:1;letter-spacing:-.02em;margin:2cqw 0}
  .bignum.red{color:#C03A22}.bignum.ink{color:#1A1813}
  .numlabel{font-family:'IBM Plex Mono',monospace;font-size:4cqw;letter-spacing:.04em;color:#5A5547;margin-top:3cqw}
  .wave{width:100%;height:auto;margin-bottom:5cqw;overflow:visible}
  .wave-zero{stroke:#B8B19E;stroke-width:1}
  .wave-band{fill:#78716220}
  .wave-path{fill:none;stroke:#C03A22;stroke-width:3.4;stroke-linecap:round;stroke-linejoin:round;
             stroke-dasharray:100;stroke-dashoffset:100}
  /* twist split */
  .twist-kicker{font-family:'Newsreader',serif;font-style:italic;font-size:8cqw;color:#C03A22;margin-bottom:3cqw}
  .vs{display:flex;align-items:flex-end;gap:9cqw;margin-top:1cqw}
  .vcol{display:flex;flex-direction:column}
  .vnum{font-family:'Newsreader',serif;font-weight:500;font-size:17cqw;line-height:.85;letter-spacing:-.02em}
  .vnum.ink{color:#1A1813}.vcol.dim .vnum{color:#C9C0A8}
  .vlabel{font-family:'IBM Plex Mono',monospace;font-size:3cqw;letter-spacing:.03em;color:#5A5547;margin-top:2cqw}
  .vcol.dim .vlabel{color:#B3AB95}
  .twistline{font-family:'Newsreader',serif;font-size:6.4cqw;line-height:1.2;color:#1A1813;margin-top:7cqw;max-width:22ch}
  .flash{position:absolute;inset:0;background:#C03A22;opacity:0;pointer-events:none;z-index:6}
  /* verdict */
  .vk{font-family:'IBM Plex Mono',monospace;font-weight:600;letter-spacing:.2em;text-transform:uppercase;font-size:3.4cqw;color:#6B6557}
  .ci{font-family:'IBM Plex Mono',monospace;font-size:3.6cqw;color:#6B6557;margin-top:2cqw}
  .verdict-line{font-family:'Newsreader',serif;font-size:6cqw;line-height:1.25;color:#1A1813;margin-top:5cqw;max-width:20ch}
  /* cta */
  .cta-line{font-family:'Newsreader',serif;font-weight:500;font-size:9cqw;line-height:1.05;margin-top:5cqw}
  .cta-url{font-family:'IBM Plex Mono',monospace;font-size:4cqw;letter-spacing:.02em;color:#C03A22;margin-top:5cqw}
  /* motion */
  @keyframes slamIn{0%{opacity:0;transform:scale(1.5)}62%{opacity:1;transform:scale(.94)}100%{opacity:1;transform:scale(1)}}
  @keyframes riseIn{0%{opacity:0;transform:translateY(4cqw)}100%{opacity:1;transform:translateY(0)}}
  @keyframes wipeIn{0%{clip-path:inset(0 100% 0 0);opacity:.25}100%{clip-path:inset(0 0 0 0);opacity:1}}
  @keyframes slideInR{0%{opacity:0;transform:translateX(14cqw)}100%{opacity:1;transform:translateX(0)}}
  @keyframes flashRed{0%{opacity:0}28%{opacity:.4}100%{opacity:0}}
  @keyframes drawWave{to{stroke-dashoffset:0}}
  .a-rise,.a-slam,.a-wipe,.a-slide{opacity:0}
  .scene.show .a-rise{animation:riseIn .5s cubic-bezier(.2,.7,.2,1) both}
  .scene.show .a-slam{animation:slamIn .62s cubic-bezier(.2,.7,.2,1) both}
  .scene.show .a-wipe{animation:wipeIn .6s ease both}
  .scene.show .a-slide{animation:slideInR .55s cubic-bezier(.2,.7,.2,1) both}
  .scene.show .a-draw{animation:drawWave 1.0s ease both}
  .scene.show .a-flash{animation:flashRed .55s ease both}
  .d1{animation-delay:.10s}.d2{animation-delay:.22s}.d3{animation-delay:.36s}.d4{animation-delay:.52s}
  @media (prefers-reduced-motion: reduce){
    .a-rise,.a-slam,.a-wipe,.a-slide{opacity:1}
    .scene.show .a-rise,.scene.show .a-slam,.scene.show .a-wipe,.scene.show .a-slide{animation:none}
    .wave-path{stroke-dashoffset:0}
  }
</style></head>
<body>
<div class="stage"><div class="frame">

  <div class="ticks"><span class="tick"></span><span class="tick"></span><span class="tick"></span><span class="tick"></span><span class="tick"></span></div>

  <!-- 1 — hook -->
  <section class="scene" data-scene="hook">
    <div class="kicker a-rise d1">{{REEL_KICKER}}</div>
    <h1 class="hookline">
      <span class="a-rise d2">{{REEL_HOOK1}}</span>
      <span class="kill a-rise d3">{{REEL_HOOK_KILL}}</span>
      <span class="a-rise d4">{{REEL_HOOK2}}</span>
    </h1>
    <div class="tag a-rise d4">{{REEL_HOOK_TAG}}</div>
  </section>

  <!-- 2 — the 'proof' -->
  <section class="scene" data-scene="proof">
    <svg class="wave a-rise d1" viewBox="0 0 320 130" role="presentation">
      <rect class="wave-band" x="150" y="6" width="34" height="118"></rect>
      <line class="wave-zero" x1="8" y1="74" x2="312" y2="74"></line>
      <path class="wave-path a-draw" pathLength="100" data-len="100"
            d="M8,74 C44,40 74,30 104,44 C124,53 138,34 150,36 L184,36 C202,66 220,98 252,90 C278,84 296,78 312,80"></path>
    </svg>
    <div class="bignum red a-slam d2">&#8722;{{HERO_DELTA}}</div>
    <div class="numlabel a-rise d3">{{REEL_PROOF_LABEL}}</div>
    <div class="tag a-rise d4">{{REEL_PROOF_TAG}}</div>
  </section>

  <!-- 3 — the twist -->
  <section class="scene" data-scene="twist">
    <div class="flash a-flash"></div>
    <div class="twist-kicker a-rise d1">{{REEL_TWIST_KICKER}}</div>
    <div class="vs">
      <div class="vcol dim a-rise d2"><div class="vnum">&#8722;{{HERO_DELTA}}</div><div class="vlabel">{{REEL_PROOF_LABEL}}</div></div>
      <div class="vcol a-slide d3"><div class="vnum ink">&#8722;{{P26_DELTA}}</div><div class="vlabel">{{REEL_TWIST_LABEL}}</div></div>
    </div>
    <div class="twistline a-wipe d4">{{REEL_TWIST_LINE}}</div>
  </section>

  <!-- 4 — verdict -->
  <section class="scene" data-scene="verdict">
    <div class="vk a-rise d1">{{REEL_VERDICT_KICKER}}</div>
    <div class="bignum red a-slam d2">{{GAP}}</div>
    <div class="ci a-rise d3">95% CI {{GAP_LO}} &middot;&middot;&middot; {{GAP_HI}}</div>
    <div class="verdict-line a-wipe d4">{{REEL_VERDICT}}</div>
  </section>

  <!-- 5 — cta -->
  <section class="scene" data-scene="cta">
    <div class="kicker a-rise d1">{{REEL_KICKER}}</div>
    <div class="cta-line a-rise d2">{{REEL_CTA}}</div>
    <div class="cta-url a-rise d3">{{REEL_CTA_URL}}</div>
  </section>

</div></div>
<script>
(function(){
  var order=['hook','proof','twist','verdict','cta'], scenes={};
  [].forEach.call(document.querySelectorAll('.scene'), function(s){ scenes[s.getAttribute('data-scene')]=s; });
  var ticks=[].slice.call(document.querySelectorAll('.tick'));
  var schedule=[[0,'hook'],[3000,'proof'],[7000,'twist'],[11000,'verdict'],[14000,'cta']];
  var rm=window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function show(name){
    var i=order.indexOf(name);
    order.forEach(function(n,j){ scenes[n].classList.toggle('show', j===i); });
    ticks.forEach(function(t,j){ t.classList.toggle('on', j<=i); });
  }
  function play(){ if(rm){ show('cta'); return; } schedule.forEach(function(e){ setTimeout(function(){ show(e[1]); }, e[0]); }); }
  // The recorder loads with ?rec and calls __play() to start the timeline at a known instant (so the
  // captured window aligns exactly); a direct browser visit just auto-plays.
  window.__play=play;
  if(location.search.indexOf('rec')===-1){ play(); }
})();
</script>
</body>
</html>"""
