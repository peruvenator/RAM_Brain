"""Refresh the FINTRX session token into 1Password.

1. Run start-fintrx-chrome.cmd and make sure platform.fintrx.com is logged in.
2. Run:  %USERPROFILE%/.venvs/fintrx/Scripts/python capture_token.py
3. Confirms with a health check. Nothing secret is printed.
"""
import sys

from fintrx_sdk import FintrxClient, FintrxAuthError, auth_bridge_capture

try:
    auth_bridge_capture()
except FintrxAuthError as e:
    print("CAPTURE FAILED:", e)
    sys.exit(1)

hc = FintrxClient().health_check()
if hc.get("is_logged_in"):
    print("health_check OK: is_logged_in = true")
else:
    print("health_check returned", hc)
    sys.exit(1)
