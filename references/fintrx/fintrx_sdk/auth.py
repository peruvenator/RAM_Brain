"""1Password-backed auth for the FINTRX SDK (Windows fork of Adam's Keychain design).

FINTRX authenticates every request with two headers, X-User-Token and
X-User-Email. They are a *browser session*, not a login: the platform issues
them after you sign in and there is no known endpoint that trades a username
and password for them. So the pair is captured once from a logged-in debug
Chrome (auth_bridge_capture) and stored on the 1Password item below. When it
expires, capture again.

Resolution order for load_credential():
  1. FINTRX_TOKEN / FINTRX_EMAIL in the environment (you ran under
     `op run --env-file op.env -- ...`)
  2. `op read op://ReSolve/Fintrix/credential` and `.../email`

Values pass through memory only. Nothing here prints, logs or writes a secret.
"""
from __future__ import annotations

import json
import os
import subprocess

VAULT = "ReSolve"
ITEM = "Fintrix"
TOKEN_REF = f"op://{VAULT}/{ITEM}/credential"
EMAIL_REF = f"op://{VAULT}/{ITEM}/email"
ENV_TOKEN = "FINTRX_TOKEN"
ENV_EMAIL = "FINTRX_EMAIL"


class FintrxAuthError(RuntimeError):
    pass


def _op_read(ref: str) -> str:
    try:
        p = subprocess.run(["op", "read", ref], capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        raise FintrxAuthError(
            "1Password CLI (`op`) is not on PATH. See references/sops/1password-credentials.md")
    except subprocess.TimeoutExpired:
        raise FintrxAuthError(
            "`op read` timed out; is OP_SERVICE_ACCOUNT_TOKEN set in this session?")
    if p.returncode != 0 or not p.stdout.strip():
        raise FintrxAuthError(
            f"`op read {ref}` failed: {p.stderr.strip()[:200] or 'empty value'}. "
            "Capture a fresh token with auth_bridge_capture() or fill the field in 1Password.")
    return p.stdout.strip()


def load_credential() -> dict:
    """Return {"token": ..., "email": ...}. Raises FintrxAuthError if unavailable."""
    token = os.environ.get(ENV_TOKEN, "").strip()
    email = os.environ.get(ENV_EMAIL, "").strip()
    if token and email:
        return {"token": token, "email": email}
    return {"token": _op_read(TOKEN_REF), "email": _op_read(EMAIL_REF)}


def store_credential(token: str, email: str) -> None:
    """Upsert the pair onto the 1Password item (fields `credential` and `email`)."""
    cmd = ["op", "item", "edit", ITEM, "--vault", VAULT,
           f"credential[password]={token}", f"email[text]={email}"]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise FintrxAuthError(f"1Password write failed: {p.stderr.strip()[:200]}")


def auth_bridge_capture(debug_port: int = 9222, wait: int = 30, verbose: bool = True) -> dict:
    """Capture a fresh (token, email) from a logged-in debug Chrome and store it in 1Password.

    Requires Chrome started with --remote-debugging-port=9222 on a dedicated
    --user-data-dir (start-fintrx-chrome.cmd does this) and a logged-in
    platform.fintrx.com tab. The function nudges the page (clicks a Next/tab
    control) so the SPA fires an API request, then reads the auth headers off
    that request over the DevTools protocol.
    """
    import time
    import urllib.request

    from websocket import create_connection, WebSocketTimeoutException

    trigger_js = (
        "(function(){"
        " var btns = Array.prototype.slice.call(document.querySelectorAll('button, li, a, div'))"
        ".filter(function(e){ var t = (e.innerText||'').trim();"
        " return e.offsetParent !== null && (t === '\\u203a' || t === '>' || t === 'Next' ||"
        " (e.getAttribute('aria-label')||'').toLowerCase().indexOf('next') !== -1); });"
        " if (btns.length) { btns[0].click(); return 'next'; }"
        " var tabs = Array.prototype.slice.call(document.querySelectorAll('button'))"
        ".filter(function(e){ var t = (e.innerText||'').trim();"
        " return /Firms|Contacts|Investors/.test(t) && t.length < 24 && t.length > 2; });"
        " if (tabs.length) { tabs[0].click(); return 'tab'; }"
        " return 'none'; })()"
    )

    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/json" % debug_port, timeout=5) as r:
            targets = json.load(r)
    except OSError as e:
        raise FintrxAuthError(
            f"No debug Chrome on port {debug_port} ({e}). Run start-fintrx-chrome.cmd first.")
    tab = next((t for t in targets
                if t.get("type") == "page" and "platform.fintrx.com" in (t.get("url") or "")), None)
    if tab is None:
        raise FintrxAuthError("no platform.fintrx.com tab in the debug Chrome; open it and log in")

    ws = create_connection(tab["webSocketDebuggerUrl"], suppress_origin=True)
    ws.settimeout(0.2)
    ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
    time.sleep(0.5)
    try:
        while True:
            ws.recv()
    except Exception:
        pass

    ws.send(json.dumps({"id": 99, "method": "Runtime.evaluate",
                        "params": {"expression": trigger_js, "returnByValue": True}}))

    tok = email = None
    start = time.time()
    end = start + wait
    reloaded = False
    while time.time() < end and not (tok and email):
        # The click nudge only works on list pages. If nothing fired after a
        # few seconds (dashboard, detail page), reload: every page load hits
        # /v1/user/ endpoints and carries the auth headers.
        if not reloaded and time.time() - start > 4:
            ws.send(json.dumps({"id": 100, "method": "Page.reload"}))
            reloaded = True
        try:
            frame = ws.recv()
        except WebSocketTimeoutException:
            continue
        try:
            ev = json.loads(frame)
        except Exception:
            continue
        if ev.get("method") == "Network.requestWillBeSent" and \
                "/v1/user/" in (ev.get("params", {}).get("request") or {}).get("url", ""):
            for k, v in (ev["params"]["request"].get("headers") or {}).items():
                if k.lower() == "x-user-token":
                    tok = str(v)
                elif k.lower() == "x-user-email":
                    email = str(v)
    ws.close()

    if not (tok and email):
        raise FintrxAuthError(
            "no X-User-Token observed within %ds; click around on the FINTRX page and retry" % wait)

    store_credential(tok, email)
    if verbose:
        print("FINTRX credential captured (token len=%d) and stored in 1Password (%s/%s)."
              % (len(tok), VAULT, ITEM))
    return {"token": tok, "email": email}
