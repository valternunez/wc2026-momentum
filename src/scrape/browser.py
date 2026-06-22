"""Browser-backed fetch for SofaScore — clears Cloudflare's JS managed challenge.

`curl_cffi` (TLS spoofing only) CANNOT pass SofaScore's managed challenge: the
homepage returns 200 but hands out no clearance cookie, and `api.sofascore.com`
returns `403 {"reason":"challenge"}` to every non-browser client — and to datacenter
IPs even from a real headless Chromium. A real browser on a **residential IP** does
pass (it's how a human uses the site), so this runs LOCAL ONLY (never CI).

`BrowserSession` is a drop-in for the curl_cffi session used by `sofascore._get_json`:
it exposes `.get(url) -> _Resp` with `.status_code`, `.text`, `.json()`.

Key design points (learned the hard way):
* **Stay on the www.sofascore.com origin and fetch the API cross-origin**, exactly
  like the real web app. Navigating directly to `api.sofascore.com` makes the request
  carry the wrong Origin/Referer and SofaScore answers `403 "Forbidden"`.
* **No custom request headers** on the in-page fetch — adding e.g. `Accept` turns it
  into a non-simple request and triggers a CORS preflight that gets blocked
  ("Failed to fetch"). A bare `fetch(url, {credentials:'include'})` is a simple
  request the API's CORS allows.
* **Persistent profile** (`data/raw/.browser_profile`, gitignored) so the Cloudflare
  clearance cookie survives between daily runs.
* **Real Chrome if installed** (`channel="chrome"`), falling back to bundled Chromium.
* **Headful by default** — headless is far more likely to be challenged.
"""

from __future__ import annotations

import json
from contextlib import suppress

from src.paths import RAW

PROFILE_DIR = RAW / ".browser_profile"  # under data/raw/ -> gitignored
SITE_ORIGIN = "https://www.sofascore.com/"

# in-page fetch from the www origin: simple cross-origin request (no custom headers
# -> no CORS preflight), cookies included. Returns {s: status, t: text}.
_FETCH_JS = """async (u) => {
  try { const r = await fetch(u, {credentials: 'include'});
        return {s: r.status, t: await r.text()}; }
  catch (e) { return {s: -1, t: 'fetch-error: ' + String(e)}; }
}"""


class _Resp:
    """Minimal curl_cffi-Response lookalike so sofascore._get_json works unchanged."""

    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self._text = text

    @property
    def text(self) -> str:
        return self._text

    def json(self):
        return json.loads(self._text)


class BrowserSession:
    def __init__(self, *, headless: bool = False, warmup: bool = True, timeout: float = 45.0):
        from playwright.sync_api import sync_playwright

        self._timeout_ms = int(timeout * 1000)
        self._warmed = False
        self._pw = sync_playwright().start()
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)

        launch = dict(
            user_data_dir=str(PROFILE_DIR),
            headless=headless,
            locale="en-US",
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:  # prefer the user's real Chrome; fall back to bundled Chromium
            self._ctx = self._pw.chromium.launch_persistent_context(channel="chrome", **launch)
        except Exception:
            self._ctx = self._pw.chromium.launch_persistent_context(**launch)

        self._page = self._ctx.pages[0] if self._ctx.pages else self._ctx.new_page()
        if warmup:
            self._warmup()

    # --- internal ---------------------------------------------------------
    def _warmup(self) -> int | None:
        """Land on www.sofascore.com so the API fetch has the right Origin + cookies."""
        status = None
        with suppress(Exception):
            resp = self._page.goto(SITE_ORIGIN, wait_until="domcontentloaded", timeout=self._timeout_ms)
            status = resp.status if resp else None
            self._page.wait_for_timeout(3500)  # let any challenge auto-solve
        self._warmed = True
        return status

    def _nav_read(self, url: str) -> _Resp:
        """Fallback: navigate to the URL and read the JSON body from the page."""
        status = None
        with suppress(Exception):
            resp = self._page.goto(url, wait_until="domcontentloaded", timeout=self._timeout_ms)
            status = resp.status if resp else None
            body = self._page.evaluate("() => document.body ? document.body.innerText : ''")
            return _Resp(status or -1, body)
        return _Resp(status or -1, "")

    # --- public (curl_cffi-like) -----------------------------------------
    def get(self, url: str, *, timeout: float | None = None, **_ignored) -> _Resp:
        if not self._warmed:
            self._warmup()
        # primary: cross-origin simple fetch from the www origin (mimics the web app)
        res = self._page.evaluate(_FETCH_JS, url)
        resp = _Resp(int(res.get("s", -1)), res.get("t", ""))
        if resp.status_code == 200:
            return resp
        # fallback: direct navigation (handles odd CORS cases; may carry wrong Origin)
        nav = self._nav_read(url)
        return nav if nav.status_code == 200 else resp

    def close(self) -> None:
        with suppress(Exception):
            self._ctx.close()
        with suppress(Exception):
            self._pw.stop()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def probe(headless: bool = False) -> int:
    """Standalone check: can a browser clear Cloudflare and read the API here?

    Run: python -m src.scrape.browser            (headful, recommended)
         python -m src.scrape.browser --headless
    Prints full detail of each strategy so failures are diagnosable in one run.
    """
    test_url = "https://api.sofascore.com/api/v1/event/9576066/graph"
    print(f"[probe] launching browser (headless={headless}) …")
    sess = BrowserSession(headless=headless)
    try:
        hp = sess._warmup()
        print(f"[probe] homepage status: {hp}")

        fres = sess._page.evaluate(_FETCH_JS, test_url)
        ftext = str(fres.get("t", ""))
        print(f"[probe] www-origin fetch: status={fres.get('s')} head={ftext[:90]!r}")

        nav = sess._nav_read(test_url)
        print(f"[probe] nav fallback:     status={nav.status_code} head={nav.text[:90]!r}")

        for label, status, text in (("fetch", fres.get("s"), ftext), ("nav", nav.status_code, nav.text)):
            if status == 200:
                with suppress(Exception):
                    n = len(json.loads(text).get("graphPoints", []))
                    print(f"[probe] SUCCESS via {label} — momentum points: {n}")
                    return 0
        print("[probe] FAIL — neither strategy returned valid JSON (see heads above).")
        return 1
    finally:
        sess.close()


if __name__ == "__main__":
    import sys

    raise SystemExit(probe(headless="--headless" in sys.argv))
