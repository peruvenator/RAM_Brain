"""Run a pipeline script with a FINTRX token captured live from the debug Chrome profile.

Fallback for when the 1Password write in capture_token.py is refused. The token is held only in
this process's environment and never written anywhere.

Usage:  python scripts/with_chrome_token.py scripts/fetch_details.py [args...]
Requires start-fintrx-chrome.cmd to be running with platform.fintrx.com logged in.
"""
from __future__ import annotations

import os
import runpy
import sys

from fintrx_sdk import auth_bridge_capture


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cred = auth_bridge_capture(verbose=True)
    os.environ["FINTRX_TOKEN"] = cred["token"]
    os.environ["FINTRX_EMAIL"] = cred["email"]
    script, sys.argv = sys.argv[1], sys.argv[1:]
    runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main()
