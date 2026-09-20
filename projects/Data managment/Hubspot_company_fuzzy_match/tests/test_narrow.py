import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import narrow


def nrow(sr, item, name, score, state_match, method="fuzzy_token_set"):
    return dict(source_row=str(sr), fintrx_item_id=str(item), matched_name=name, cand_city="X",
                cand_state="TX", score=str(score), method=method, state_match=str(state_match))


def drow(sr, item, name, cnt):
    return dict(source_row=str(sr), fintrx_item_id=str(item) if item else "", matched_name=name,
                rep_count=str(cnt), method="domain_reps" if item else "domain_unmapped")


class MergeTests(unittest.TestCase):
    def test_dedupes_same_item_and_joins_methods(self):
        m = narrow.merge_candidates([nrow(0, 11, "A Co", 100, True, "exact_normalized")], [drow(0, 11, "A Co", 5)])
        self.assertEqual(len(m[0]), 1)
        self.assertEqual(m[0][0]["methods"], "exact_normalized|domain_reps")
        self.assertEqual(m[0][0]["rep_count"], 5)

    def test_unmapped_domain_kept_with_none_id(self):
        m = narrow.merge_candidates([], [drow(3, None, "Mystery LLC", 2)])
        self.assertIsNone(m[3][0]["item_id"])


class AutoKeepTests(unittest.TestCase):
    def test_single_exact_with_state(self):
        m = narrow.merge_candidates([nrow(0, 11, "A", 100, True, "exact_normalized")], [])
        self.assertTrue(narrow.auto_keep(m[0]))

    def test_single_exact_without_state_needs_jev(self):
        m = narrow.merge_candidates([nrow(0, 11, "A", 100, False, "exact_normalized")], [])
        self.assertFalse(narrow.auto_keep(m[0]))

    def test_name_and_domain_agree(self):
        m = narrow.merge_candidates([nrow(0, 11, "A", 88, False)], [drow(0, 11, "A", 3)])
        self.assertTrue(narrow.auto_keep(m[0]))

    def test_two_candidates_needs_jev(self):
        m = narrow.merge_candidates([nrow(0, 11, "A", 100, True, "exact_normalized"), nrow(0, 12, "A2", 90, True)], [])
        self.assertFalse(narrow.auto_keep(m[0]))


class QuestionTests(unittest.TestCase):
    def test_two_questions_per_candidate(self):
        m = narrow.merge_candidates([nrow(0, 11, "A", 90, True), nrow(0, 12, "B", 80, False)], [])
        q = narrow.build_questions(m[0])
        self.assertEqual(set(q), {"link_0", "name_0", "link_1", "name_1"})
        self.assertEqual(q["link_0"]["type"], "score")
        self.assertEqual(len(q["link_0"]["criteria"]), 3)


if __name__ == "__main__":
    unittest.main()
