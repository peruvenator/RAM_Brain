import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import common


class DomainTests(unittest.TestCase):
    def test_strips_scheme_www_and_path(self):
        self.assertEqual(common.extract_domain("https://www.Intrua.com/about"), "intrua.com")

    def test_blank_and_nan(self):
        self.assertEqual(common.extract_domain(None), "")
        self.assertEqual(common.extract_domain(float("nan")), "")
        self.assertEqual(common.extract_domain("  "), "")

    def test_generic_domain_is_blank(self):
        self.assertEqual(common.extract_domain("gmail.com"), "")

    def test_subdomain_kept(self):
        self.assertEqual(common.extract_domain("advisors.lpl.com"), "advisors.lpl.com")


class PhoneTests(unittest.TestCase):
    def test_last_ten_digits(self):
        self.assertEqual(common.phone_digits("+1 617-720-4500"), "6177204500")
        self.assertEqual(common.phone_digits("12814912800"), "2814912800")
        self.assertEqual(common.phone_digits("(713) 355-9910"), "7133559910")

    def test_short_or_blank(self):
        self.assertEqual(common.phone_digits(None), "")
        self.assertEqual(common.phone_digits("555"), "")


class StateTests(unittest.TestCase):
    def test_upper_two_letter(self):
        self.assertEqual(common.norm_state(" tx "), "TX")
        self.assertEqual(common.norm_state("Texas"), "TX")
        self.assertEqual(common.norm_state(None), "")


if __name__ == "__main__":
    unittest.main()
