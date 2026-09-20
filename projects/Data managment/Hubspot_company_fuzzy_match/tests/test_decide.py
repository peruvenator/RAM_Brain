import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import decide


class FlagTests(unittest.TestCase):
    def test_domain_phone_state_zip(self):
        src = {"Company Domain Name": "intrua.com", "Phone Number": "12814912800",
               "State/Region (Global)": "TX", "_zip": ""}
        det = {"website_address": "https://www.intrua.com/", "phone": "(281) 491-2800", "state": "TX", "zip": "77098"}
        f = decide.compute_flags(src, det)
        self.assertTrue(f["domain_equal"]); self.assertTrue(f["phone_equal"]); self.assertTrue(f["state_equal"])
        self.assertIsNone(f["zip_equal"])

    def test_missing_state_is_none(self):
        f = decide.compute_flags({"Company Domain Name": "", "Phone Number": "", "State/Region (Global)": None},
                                 {"website_address": "", "phone": "", "state": "TX", "zip": ""})
        self.assertIsNone(f["state_equal"]); self.assertFalse(f["domain_equal"])


class RuleTests(unittest.TestCase):
    F = dict(domain_equal=False, phone_equal=False, state_equal=True, zip_equal=None)

    def test_domain_with_moderate_link_accepts(self):
        self.assertEqual(decide.decide_candidate(1.1, dict(self.F, domain_equal=True)), "accept")
        self.assertEqual(decide.decide_candidate(0.99, dict(self.F, domain_equal=True, state_equal=False)), "accept")

    def test_domain_with_low_link_reviews(self):
        self.assertEqual(decide.decide_candidate(0.6, dict(self.F, domain_equal=True)), "review")

    def test_phone_needs_stronger_link_than_domain(self):
        self.assertEqual(decide.decide_candidate(0.94, dict(self.F, phone_equal=True)), "review")
        self.assertEqual(decide.decide_candidate(1.41, dict(self.F, phone_equal=True)), "accept")

    def test_strong_link_same_state_accepts(self):
        self.assertEqual(decide.decide_candidate(1.7, self.F), "accept")

    def test_strong_link_other_state_reviews(self):
        self.assertEqual(decide.decide_candidate(1.7, dict(self.F, state_equal=False)), "review")

    def test_low_link_rejects(self):
        self.assertEqual(decide.decide_candidate(0.3, self.F), "reject")

    def test_missing_link_reviews(self):
        self.assertEqual(decide.decide_candidate(None, self.F), "review")


class RowTests(unittest.TestCase):
    def test_single_accept_wins(self):
        self.assertEqual(decide.decide_row([{"decision": "accept"}, {"decision": "reject"}]), ("accept", 0, "single_accept"))

    def test_two_accepts_demote(self):
        self.assertEqual(decide.decide_row([{"decision": "accept"}, {"decision": "accept"}])[0], "review")

    def test_only_reviews(self):
        self.assertEqual(decide.decide_row([{"decision": "review"}])[0], "review")

    def test_all_rejects(self):
        self.assertEqual(decide.decide_row([{"decision": "reject"}]), ("no_match", None, "all_rejected"))


if __name__ == "__main__":
    unittest.main()
