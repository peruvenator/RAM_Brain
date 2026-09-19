"""FINTRX SDK, Windows fork: Python client for the FINTRX platform internal API.

Credentials come from 1Password (op://ReSolve/Fintrix). See auth.py and README.md.
"""

from .client import FintrxClient, FintrxAuthError, FintrxAPIError
from .auth import load_credential, store_credential, auth_bridge_capture

__version__ = "0.2.0"
__all__ = [
    "FintrxClient",
    "FintrxAuthError",
    "FintrxAPIError",
    "load_credential",
    "store_credential",
    "auth_bridge_capture",
]
