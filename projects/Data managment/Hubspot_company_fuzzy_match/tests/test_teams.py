import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import pull_teams
import match_teams


class LocationTests(unittest.TestCase):
    def test_city_state(self):
        self.assertEqual(pull_teams.parse_location("Gig Harbor, WA"), ("Gig Harbor", "WA"))

    def test_city_only_and_blank(self):
        self.assertEqual(pull_teams.parse_location("Chicago"), ("Chicago", ""))
        self.assertEqual(pull_teams.parse_location(None), ("", ""))

    def test_flatten_reads_parent(self):
        f = pull_teams.flatten({"id": 54668, "name": "Konvergent Wealth Partners", "location": "Gig Harbor, WA",
                                "parent_firm": {"id": 165090, "name": "Integrated Partners", "crd_id": 284656}})
        self.assertEqual((f["team_id"], f["parent_crd"], f["state"]), (54668, 284656, "WA"))


class RuleTests(unittest.TestCase):
    def test_parent_domain_with_moderate_link_accepts(self):
        self.assertEqual(match_teams.decide_candidate(1.1, False, True), "accept")

    def test_strong_link_needs_confirmed_state(self):
        self.assertEqual(match_teams.decide_candidate(1.7, True, False), "accept")
        self.assertEqual(match_teams.decide_candidate(1.7, None, False), "review")
        self.assertEqual(match_teams.decide_candidate(1.7, False, False), "review")

    def test_low_rejects_and_none_reviews(self):
        self.assertEqual(match_teams.decide_candidate(0.3, True, False), "reject")
        self.assertEqual(match_teams.decide_candidate(None, True, False), "review")

    def test_row_rules(self):
        self.assertEqual(match_teams.decide_row([{"decision": "accept"}, {"decision": "reject"}])[0], "accept")
        self.assertEqual(match_teams.decide_row([{"decision": "accept"}, {"decision": "accept"}])[0], "review")


if __name__ == "__main__":
    unittest.main()
