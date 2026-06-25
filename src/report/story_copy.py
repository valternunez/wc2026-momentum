"""Story-mode page template (story.html + story.es.html).

A vertical 9:16, swipe-through "Instagram story" of the overall finding — built to be flipped
through on a phone and screen-recorded into a real IG-Story video, or saved slide-by-slide as a
1080x1920 PNG (rendered locally via Playwright with ?still=N, like the OG cards). All slide copy
lives in i18n.STRINGS as STORY_* tokens; every number resolves through the shared {{TOKEN}} pass
in build_site.build_story_pages(), so it traces to data/processed/* exactly like the main page.

NOTE: non-raw string — never use backslash-escaped double-quotes (\\") inside; Python would
collapse them and break the inline JS/markup. Use single-quoted JS/CSS/attr values throughout.
"""

from __future__ import annotations

TEMPLATE = """<!DOCTYPE html>
<html lang="{{LANG}}"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{{STORY_META_TITLE}}</title>
<meta name="description" content="{{STORY_META_DESC}}">
<link rel="canonical" href="{{STORY_CANONICAL}}">
<meta name="theme-color" content="#14110D">
<meta name="color-scheme" content="light">
<meta name="darkreader-lock">
<meta property="og:type" content="article">
<meta property="og:title" content="{{STORY_META_TITLE}}">
<meta property="og:description" content="{{STORY_META_DESC}}">
<meta property="og:url" content="{{STORY_CANONICAL}}">
<meta property="og:image" content="{{OG_IMAGE}}">
<meta name="twitter:card" content="summary_large_image">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='15' fill='%231A1813'/><circle cx='16' cy='16' r='6' fill='%23E5482E'/></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{color-scheme:light}
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{height:100%}
  body{background:#14110D;font-family:'IBM Plex Sans',sans-serif;overflow:hidden}
  a{color:inherit}
  ::selection{background:#E5482E;color:#FCFAF3}
  :focus-visible{outline:2px solid #E5482E;outline-offset:2px;border-radius:2px}
  .stage{position:fixed;inset:0;display:grid;place-items:center;padding:0}
  @media (min-width:520px){ .stage{padding:18px} }
  .frame{position:relative;width:min(100vw, calc(100vh * 9 / 16));height:min(100vh, calc(100vw * 16 / 9));
         background:#EFEBDF;color:#1A1813;overflow:hidden;container-type:size;cursor:pointer;
         -webkit-user-select:none;user-select:none;touch-action:pan-y}
  @media (min-width:520px){ .frame{border-radius:16px;box-shadow:0 24px 80px rgba(0,0,0,.55)} }
  /* progress bars */
  .progress{position:absolute;top:0;left:0;right:0;display:flex;gap:1.4cqw;padding:3.2cqw 5cqw 0;z-index:6}
  .seg{flex:1;height:0.9cqw;min-height:3px;border-radius:3px;background:rgba(26,24,19,.16)}
  .seg.on{background:#1A1813}
  /* slides */
  .slide{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;
         padding:15cqw 8.5cqw 19cqw;opacity:0;visibility:hidden;z-index:1}
  .slide.active{opacity:1;visibility:visible;z-index:2}
  .kick,.label{font-family:'IBM Plex Mono',monospace;font-weight:600;letter-spacing:.2em;text-transform:uppercase}
  .kick{font-size:3.3cqw;color:#C03A22}
  .label{font-size:3.4cqw;color:#6B6557;margin-bottom:5cqw}
  .hook{font-family:'Newsreader',serif;font-weight:500;font-size:8.4cqw;line-height:1.04;letter-spacing:-.012em;margin-top:3cqw}
  .big{display:block;font-family:'Newsreader',serif;font-weight:500;font-size:40cqw;line-height:.82;letter-spacing:-.02em}
  .big.red{color:#C03A22}.big.ink{color:#1A1813}
  .unit{font-family:'IBM Plex Mono',monospace;font-size:3.5cqw;letter-spacing:.04em;color:#5A5547;margin-top:3.5cqw}
  .ci{font-family:'IBM Plex Mono',monospace;font-size:3.4cqw;color:#6B6557;margin-top:2cqw}
  .sub{font-family:'Newsreader',serif;font-size:4.5cqw;line-height:1.42;color:#2B2820;margin-top:5.5cqw;max-width:30ch}
  .cta-url{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:3.9cqw;letter-spacing:.02em;
           color:#C03A22;text-decoration:none;border-bottom:1px solid rgba(192,58,34,.5);margin-top:5cqw}
  /* schematic wave (decorative — no axis numbers) */
  .wave{width:100%;height:auto;margin-top:6cqw;overflow:visible}
  .wave-zero{stroke:#B8B19E;stroke-width:1}
  .wave-band{fill:#78716220;opacity:0}
  .slide.active .wave-band{opacity:1;transition:opacity .8s ease .5s}
  .wave-path{fill:none;stroke:#C03A22;stroke-width:3;stroke-linecap:round;stroke-linejoin:round;
             stroke-dasharray:100;stroke-dashoffset:100}
  /* entrance animation */
  .anim{opacity:0;transform:translateY(12px)}
  .slide.active .anim{opacity:1;transform:none;transition:opacity .55s ease, transform .55s ease}
  .slide.active .d1{transition-delay:.04s}.slide.active .d2{transition-delay:.16s}.slide.active .d3{transition-delay:.30s}
  /* close (back to the analysis) */
  .close{position:absolute;top:5.5cqw;right:4cqw;z-index:7;display:flex;align-items:center;justify-content:center;
         min-width:9cqw;min-height:9cqw;font-family:'IBM Plex Mono',monospace;font-size:4.4cqw;line-height:1;
         color:#6B6557;text-decoration:none;background:none;border:0;cursor:pointer}
  .close:hover{color:#C03A22}
  /* chrome */
  .chrome{position:absolute;left:0;right:0;bottom:0;z-index:6;padding:0 6cqw 5cqw;
          display:flex;flex-direction:column;gap:2.4cqw}
  .hint{font-family:'IBM Plex Mono',monospace;font-size:2.4cqw;letter-spacing:.08em;color:#9A927E;pointer-events:none}
  .crow{display:flex;align-items:center;justify-content:space-between;gap:3cqw;flex-wrap:wrap}
  .ctrls{display:flex;gap:3.6cqw;align-items:center;flex-wrap:wrap}
  .cbtn{font-family:'IBM Plex Mono',monospace;font-size:2.6cqw;letter-spacing:.05em;color:#46412F;
        text-decoration:none;border-bottom:1px solid rgba(70,65,47,.35);background:none;border-top:0;border-left:0;border-right:0;cursor:pointer;padding:0 0 1px}
  .counter{font-family:'IBM Plex Mono',monospace;font-size:2.6cqw;letter-spacing:.08em;color:#8A8268;white-space:nowrap}
  .navchev{position:absolute;top:50%;transform:translateY(-50%);z-index:5;background:none;border:0;cursor:pointer;
           font-size:6cqw;color:rgba(26,24,19,.28);padding:4cqw;display:none}
  @media (hover:hover) and (min-width:520px){ .navchev{display:block} }
  .navchev.prev{left:0}.navchev.next{right:0}
  /* share bar */
  .sharebar{display:flex;align-items:center;flex-wrap:wrap;gap:2.6cqw;margin-top:6cqw}
  .sharebar-label{font-family:'IBM Plex Mono',monospace;font-size:3cqw;letter-spacing:.14em;text-transform:uppercase;color:#6B6557}
  .sbtn{font-family:'IBM Plex Mono',monospace;font-size:3.2cqw;letter-spacing:.03em;color:#EFEBDF;background:#1A1813;
        text-decoration:none;padding:1.8cqw 3.2cqw;border-radius:4px;border:0;cursor:pointer;line-height:1}
  .sbtn:hover{background:#C03A22}
  .sbtn.ghost{background:none;color:#46412F;border:1px solid rgba(70,65,47,.4)}
  /* reduced motion: show everything, no transitions */
  @media (prefers-reduced-motion: reduce){
    .anim{opacity:1;transform:none}
    .slide.active .anim{transition:none}
    .wave-path{stroke-dashoffset:0}
    .wave-band{opacity:1}
  }
  /* still-capture mode: show one slide, no chrome, no animation (Playwright ?still=N) */
  body.still{overflow:hidden}
  body.still .stage{padding:0}
  body.still .frame{width:100vw;height:100vh;border-radius:0;box-shadow:none;cursor:default}
  body.still .progress,body.still .chrome,body.still .hint,body.still .navchev,body.still .close{display:none}
  body.still .slide{opacity:0;visibility:hidden}
  body.still .slide.show{opacity:1;visibility:visible;z-index:3}
  body.still .anim{opacity:1;transform:none;transition:none}
  body.still .wave-path{stroke-dashoffset:0}
  body.still .wave-band{opacity:1}
  /* autoplay mode: clean full-bleed frame for video capture (Playwright ?autoplay=1) — keep the
     progress bars, hide the interactive chrome */
  body.autoplay{overflow:hidden}
  body.autoplay .stage{padding:0}
  body.autoplay .frame{width:100vw;height:100vh;border-radius:0;box-shadow:none;cursor:default}
  body.autoplay .chrome,body.autoplay .hint,body.autoplay .navchev,body.autoplay .close{display:none}
  body.autoplay .sharebar{display:none!important}  /* no tappable share buttons in a recorded video (beat the inline display:flex) */
</style></head>
<body>
<div class="stage">
  <div class="frame" id="frame">

    <div class="progress" aria-hidden="true">
      <span class="seg"></span><span class="seg"></span><span class="seg"></span>
      <span class="seg"></span><span class="seg"></span><span class="seg"></span>
    </div>

    <a class="close no-nav same-tab" href="{{HOME_HREF}}" aria-label="{{MODAL_CLOSE_ARIA}}"><span aria-hidden="true">&#10005;</span></a>
    <button class="navchev prev no-nav" data-go="prev" aria-label="{{STORY_PREV}}">&#8249;</button>
    <button class="navchev next no-nav" data-go="next" aria-label="{{STORY_NEXT}}">&#8250;</button>

    <!-- 1 — hook -->
    <section class="slide" data-i="1">
      <div class="kick anim d1">{{STORY_KICKER}}</div>
      <h1 class="hook anim d2">{{STORY_HOOK_H}}</h1>
      <p class="sub anim d3">{{STORY_HOOK_SUB}}</p>
    </section>

    <!-- 2 — the claim -->
    <section class="slide" data-i="2">
      <div class="label anim d1">{{STORY_CLAIM_LABEL}}</div>
      <h2 class="hook anim d2">{{STORY_CLAIM_H}}</h2>
      <p class="sub anim d3">{{STORY_CLAIM_SUB}}</p>
    </section>

    <!-- 3 — the drop -->
    <section class="slide" data-i="3">
      <div class="label anim d1">{{STORY_DROP_LABEL}}</div>
      <span class="big red anim d2" data-num="{{HERO_DELTA}}" data-prefix="&#8722;">&#8722;{{HERO_DELTA}}</span>
      <div class="unit anim d2">{{STORY_DROP_UNIT}}</div>
      <svg class="wave anim d3" viewBox="0 0 320 130" role="presentation">
        <rect class="wave-band" x="150" y="6" width="34" height="118"></rect>
        <line class="wave-zero" x1="8" y1="74" x2="312" y2="74"></line>
        <path class="wave-path" pathLength="100" data-len="100"
              d="M8,74 C44,40 74,30 104,44 C124,53 138,34 150,36 L184,36 C202,66 220,98 252,90 C278,84 296,78 312,80"></path>
      </svg>
      <p class="sub anim d3">{{STORY_DROP_SUB}}</p>
    </section>

    <!-- 4 — the catch -->
    <section class="slide" data-i="4">
      <div class="label anim d1">{{STORY_CATCH_LABEL}}</div>
      <span class="big ink anim d2" data-num="{{P26_DELTA}}" data-prefix="&#8722;">&#8722;{{P26_DELTA}}</span>
      <div class="unit anim d2">{{STORY_CATCH_UNIT}}</div>
      <p class="sub anim d3">{{STORY_CATCH_SUB}}</p>
    </section>

    <!-- 5 — the verdict -->
    <section class="slide" data-i="5">
      <div class="label anim d1">{{STORY_VERDICT_LABEL}}</div>
      <span class="big red anim d2" data-num="{{GAP}}" data-prefix="">{{GAP}}</span>
      <div class="unit anim d2">{{STORY_VERDICT_UNIT}}</div>
      <div class="ci anim d2">95% CI {{GAP_LO}} &middot;&middot;&middot; {{GAP_HI}}</div>
      <p class="sub anim d3">{{STORY_VERDICT_SUB}}</p>
    </section>

    <!-- 6 — CTA -->
    <section class="slide" data-i="6">
      <div class="kick anim d1">{{STORY_KICKER}}</div>
      <h2 class="hook anim d2">{{STORY_CTA_H}}</h2>
      <p class="sub anim d2">{{STORY_CTA_SUB}}</p>
      <a class="cta-url no-nav same-tab anim d3" href="{{HOME_HREF}}">{{STORY_CTA_URL}}</a>
      <div class="anim d3">{{SHARE_BAR}}</div>
    </section>

    <div class="chrome">
      <div class="hint" id="hint">{{STORY_HINT}}</div>
      <div class="crow">
        <div class="ctrls">
          <a class="cbtn no-nav" id="save" href="story/{{STORY_DIR}}/slide1.png" download>&#8595; {{STORY_SAVE}}</a>
          <a class="cbtn no-nav" href="{{STORY_VID}}" download>&#8595; {{STORY_VIDEO}}</a>
          {{STORY_LANG}}
        </div>
        <div class="counter" id="counter" data-of="{{STORY_OF}}"></div>
      </div>
    </div>

  </div>
</div>
<script>
(function(){
  var frame=document.getElementById('frame');
  var slides=[].slice.call(frame.querySelectorAll('.slide'));
  var segs=[].slice.call(frame.querySelectorAll('.seg'));
  var counter=document.getElementById('counter');
  var save=document.getElementById('save');
  var N=slides.length, idx=0;
  var rm=window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var of=(counter&&counter.getAttribute('data-of'))||'of';

  function countup(el){
    var raw=el.getAttribute('data-num'), pre=el.getAttribute('data-prefix')||'', n=parseInt(raw,10);
    if(isNaN(n)){ el.textContent=raw; return; }
    if(rm){ el.textContent=pre+n; return; }
    var dur=680, t0=null;
    function step(ts){ if(t0===null)t0=ts; var p=Math.min((ts-t0)/dur,1), e=1-Math.pow(1-p,3);
      el.textContent=pre+Math.round(n*e); if(p<1) requestAnimationFrame(step); else el.textContent=pre+n; }
    el.textContent=pre+'0'; requestAnimationFrame(step);
  }
  function drawWave(sl){
    var w=sl.querySelector('.wave-path'); if(!w) return; var len=w.getAttribute('data-len')||'100';
    w.style.transition='none'; w.style.strokeDashoffset=len; void w.getBoundingClientRect();
    w.style.transition= rm ? 'none' : 'stroke-dashoffset 1.15s ease'; w.style.strokeDashoffset='0';
  }
  function activate(i){
    slides.forEach(function(s,j){ s.classList.toggle('active', j===i); });
    segs.forEach(function(s,j){ s.classList.toggle('on', j<=i); });
    if(counter) counter.textContent=(i+1)+' '+of+' '+N;
    if(save) save.setAttribute('href','story/{{STORY_DIR}}/slide'+(i+1)+'.png');
    var sl=slides[i];
    sl.querySelectorAll('[data-num]').forEach(countup);
    drawWave(sl);
  }
  function go(i){ idx=Math.max(0,Math.min(N-1,i)); activate(idx); }
  function next(){ go(idx+1); } function prev(){ go(idx-1); }

  var params=new URLSearchParams(location.search);

  // still-capture mode (?still=N) — one slide, final state, no animation
  var still=params.get('still');
  if(still!==null){
    var k=Math.max(1,Math.min(N,parseInt(still,10)||1))-1;
    document.body.classList.add('still'); rm=true;
    slides.forEach(function(s,j){ s.classList.toggle('show', j===k); });
    activate(k); return;
  }

  // autoplay mode (?autoplay=1) — used by the video recorder: advance on a timer through every
  // slide (playing each slide's animations), hold on the last. Chrome is hidden via body.autoplay.
  if(params.get('autoplay')!==null){
    document.body.classList.add('autoplay');
    activate(0);
    var per=3200, i=0;
    var timer=setInterval(function(){ i++; if(i>=N){ clearInterval(timer); return; } go(i); }, per);
    return;
  }

  frame.addEventListener('click', function(e){
    if(e.target.closest('a,button,.no-nav,.sharebar')) return;
    var r=frame.getBoundingClientRect();
    if(e.clientX-r.left < r.width*0.32) prev(); else next();
  });
  var sx=null;
  frame.addEventListener('pointerdown', function(e){ sx=e.clientX; });
  frame.addEventListener('pointerup', function(e){ if(sx===null) return; var dx=e.clientX-sx; sx=null;
    if(Math.abs(dx)>45){ if(dx<0) next(); else prev(); } });
  document.addEventListener('keydown', function(e){
    if(e.key==='ArrowRight'||e.key===' '){ e.preventDefault(); next(); }
    else if(e.key==='ArrowLeft'){ e.preventDefault(); prev(); } });
  [].slice.call(frame.querySelectorAll('[data-go]')).forEach(function(b){
    b.addEventListener('click', function(){ var d=b.getAttribute('data-go'); if(d==='next')next(); else if(d==='prev')prev(); }); });

  activate(0);
})();
</script>
</body>
</html>"""
