from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from BuddyCareExcel_logic import load_excel_for_lookup, split_thai_name, to_mysql_date


BASE_DIR = Path(__file__).resolve().parent
TEST_EXCEL_PATH = BASE_DIR / "test-data" / "test.xlsx"


class BuddyCareExcelTestDataTests(unittest.TestCase):
    def test_test_data_file_exists(self) -> None:
        self.assertTrue(TEST_EXCEL_PATH.exists(), f"Missing test data: {TEST_EXCEL_PATH}")

    def test_load_excel_for_lookup_uses_test_data(self) -> None:
        df = load_excel_for_lookup(str(TEST_EXCEL_PATH))

        self.assertEqual(len(df), 108)
        self.assertEqual(df.iloc[0]["ลำดับ"], 1)
        self.assertEqual(df.iloc[0]["วันที่ xls"], "06-03-2026")
        self.assertEqual(df.iloc[0]["คำนำหน้า"], "นาย")
        self.assertEqual(df.iloc[0]["ชื่อ"], "ประจน")
        self.assertEqual(df.iloc[0]["นามสกุล"], "ขวัญอ่างทอง")
        self.assertEqual(df.iloc[0]["สถานะ"], "เข้าเยี่ยมเสร็จสิ้น")
        self.assertIn("Reason", df.columns)
        self.assertTrue(df["Reason"].fillna("").astype(str).str.strip().ne("").any())
        self.assertIn("cid", df.columns)
        self.assertTrue(df["cid"].fillna("").eq("").all())

    def test_load_excel_for_lookup_sorts_by_excel_date_then_original_order(self) -> None:
        df = load_excel_for_lookup(str(TEST_EXCEL_PATH))
        parsed_dates = pd.to_datetime(df["วันที่ xls"], errors="coerce", dayfirst=True)

        self.assertTrue(parsed_dates.is_monotonic_increasing)
        same_date_rows = df[df["วันที่ xls"].eq("25-03-2026")]
        self.assertEqual(same_date_rows.iloc[0]["ชื่อ"], "สายทอง")
        self.assertEqual(same_date_rows.iloc[1]["ชื่อ"], "เอื้อน")
        self.assertEqual(same_date_rows.iloc[2]["ชื่อ"], "เยาวลักษณ์")

    def test_split_thai_name_handles_prefixes_from_test_data(self) -> None:
        self.assertEqual(
            split_thai_name("นางสาวช่อทิพย์ พูพุ่ม"),
            ("นางสาว", "ช่อทิพย์", "พูพุ่ม"),
        )
        self.assertEqual(
            split_thai_name("น.ส.จันทิมา แย้มทัศ"),
            ("น.ส.", "จันทิมา", "แย้มทัศ"),
        )

    def test_to_mysql_date_accepts_test_data_date_format(self) -> None:
        self.assertEqual(to_mysql_date("21-04-2026"), "2026-04-21")


if __name__ == "__main__":
    unittest.main()
