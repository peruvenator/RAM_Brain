import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import openpyxl
import write_output


class FillTests(unittest.TestCase):
    def test_fills_column_c_and_leaves_rest(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "s.xlsx"; out = Path(d) / "o.xlsx"
            wb = openpyxl.Workbook(); ws = wb.active
            ws.append(["Record ID", "Company name", "Fintrx Firm CRD ID", "Phone Number"])
            ws.append([1, "Intrua", None, "555"]); ws.append([2, "Nobody", None, "666"])
            wb.save(src)
            n = write_output.fill_workbook(src, out, {0: dict(crd_id="281554", matched_name="Intrua Financial",
                                                              methods="exact_normalized", link2="1.9")})
            self.assertEqual(n, 1)
            ws2 = openpyxl.load_workbook(out).active
            self.assertEqual(ws2["C2"].value, 281554)
            self.assertIsNone(ws2["C3"].value)
            self.assertEqual(ws2["D3"].value, "666")
            self.assertEqual(ws2["E1"].value, "fintrx_match_name")
            self.assertEqual(ws2["E2"].value, "Intrua Financial")

    def test_fills_team_block(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "s.xlsx"; out = Path(d) / "o.xlsx"
            wb = openpyxl.Workbook(); ws = wb.active
            ws.append(["Record ID", "Company name", "Fintrx Firm CRD ID"])
            ws.append([1, "Konvergent wealth partners", None])
            wb.save(src)
            write_output.fill_workbook(src, out, {}, {0: dict(team_id="54668", team_name="Konvergent Wealth Partners",
                                                               parent_crd="284656", link="1.8")})
            ws2 = openpyxl.load_workbook(out).active
            self.assertIsNone(ws2["C2"].value)                      # column C untouched for a team match
            self.assertEqual(ws2["G1"].value, "Fintrx_wealth_team_id")
            self.assertEqual(ws2["G2"].value, 54668)
            self.assertEqual(ws2["I2"].value, 284656)


if __name__ == "__main__":
    unittest.main()
