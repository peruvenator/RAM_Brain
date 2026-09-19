"""Offline tests for credential resolution. No network, no 1Password calls.

Run from references/fintrx:  python -m unittest tests.test_auth -v
"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fintrx_sdk import auth  # noqa: E402

CLEAN = {k: v for k, v in os.environ.items() if k not in ("FINTRX_TOKEN", "FINTRX_EMAIL")}


class LoadCredential(unittest.TestCase):
    def test_env_wins_when_both_vars_set(self):
        with mock.patch.dict(os.environ, {"FINTRX_TOKEN": "t1", "FINTRX_EMAIL": "e@x.com"}), \
             mock.patch.object(auth, "_op_read", side_effect=AssertionError("must not call op")):
            self.assertEqual(auth.load_credential(), {"token": "t1", "email": "e@x.com"})

    def test_falls_back_to_op_read_when_env_missing(self):
        with mock.patch.dict(os.environ, CLEAN, clear=True), \
             mock.patch.object(auth, "_op_read", side_effect=lambda ref: {
                 auth.TOKEN_REF: "t2", auth.EMAIL_REF: "e2@x.com"}[ref]):
            self.assertEqual(auth.load_credential(), {"token": "t2", "email": "e2@x.com"})

    def test_partial_env_does_not_short_circuit(self):
        env = dict(CLEAN, FINTRX_TOKEN="only-token")
        with mock.patch.dict(os.environ, env, clear=True), \
             mock.patch.object(auth, "_op_read", side_effect=lambda ref: {
                 auth.TOKEN_REF: "t3", auth.EMAIL_REF: "e3@x.com"}[ref]):
            self.assertEqual(auth.load_credential(), {"token": "t3", "email": "e3@x.com"})

    def test_raises_clear_error_when_op_fails(self):
        with mock.patch.dict(os.environ, CLEAN, clear=True), \
             mock.patch.object(auth, "_op_read", side_effect=auth.FintrxAuthError("op read failed")):
            with self.assertRaises(auth.FintrxAuthError):
                auth.load_credential()


class StoreCredential(unittest.TestCase):
    def test_calls_op_item_edit_without_shell(self):
        with mock.patch.object(auth.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=0, stderr="")
            auth.store_credential("tok", "me@x.com")
            args, kwargs = run.call_args
            cmd = args[0]
            self.assertEqual(cmd[:3], ["op", "item", "edit"])
            self.assertIn(auth.ITEM, cmd)
            self.assertTrue(any(a.startswith("credential[") and a.endswith("=tok") for a in cmd))
            self.assertTrue(any(a.startswith("email[") and a.endswith("=me@x.com") for a in cmd))
            self.assertFalse(kwargs.get("shell", False))

    def test_raises_on_nonzero_exit(self):
        with mock.patch.object(auth.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=1, stderr="no write access")
            with self.assertRaises(auth.FintrxAuthError):
                auth.store_credential("tok", "me@x.com")


if __name__ == "__main__":
    unittest.main()
