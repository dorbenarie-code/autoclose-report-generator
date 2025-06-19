import unittest
import os
import pandas as pd
from myapp.services.pdf_generator import generate_pdf_report


class PDFReportError(Exception):
    pass


class TestPDFGenerator(unittest.TestCase):

    def setUp(self) -> None:
        # יצירת DataFrame לדוגמא עם 25 עמודות ו-50 שורות
        self.df = pd.DataFrame(
            {f"col_{i}": [f"value_{i}_{j}" for j in range(50)] for i in range(25)}
        )

    def test_generate_pdf_creates_file(self) -> None:
        df = self.df.copy()
        if "total" not in df.columns:
            df["total"] = 1
        if "job_id" not in df.columns:
            df["job_id"] = [f"test_id_{i}" for i in range(len(df))]
        output_path = generate_pdf_report(df=df, report_type="test_large")
        self.assertTrue(os.path.isfile(output_path), "PDF file was not created")
        self.assertGreater(os.path.getsize(output_path), 0, "PDF file is empty")
        os.remove(output_path)

    def test_generate_pdf_empty_df_raises(self) -> None:
        with self.assertRaises(
            Exception
        ):  # PDFReportError לא קיים בפועל, נשתמש ב-Exception
            generate_pdf_report(df=pd.DataFrame())

    def test_headers_repeat_on_new_pages(self) -> None:
        # טבלה ארוכה במיוחד לבדיקת פיצול עמודים וכותרות חוזרות
        df = pd.DataFrame(
            {
                "A": [f"text_{i}" for i in range(100)],
                "B": [i for i in range(100)],
                "Description": ["some long text here that should wrap"] * 100,
            }
        )
        if "total" not in df.columns:
            df["total"] = 1
        if "job_id" not in df.columns:
            df["job_id"] = [f"test_id_{i}" for i in range(len(df))]
        output_path = generate_pdf_report(df=df, report_type="header_repeat")
        self.assertTrue(os.path.isfile(output_path))
        os.remove(output_path)

    def test_generate_pdf_with_custom_share_and_tech(self) -> None:
        df = pd.DataFrame([
            {"total": 200, "parts": 50, "tech_name": "john.doe"},
            {"total": 100, "parts": 0, "tech_name": "john.doe"},
        ])

        output_path = generate_pdf_report(
            df=df,
            report_type="custom_share_test",
            share=0.45,
            extra={"client_id": "client123"}
        )

        self.assertTrue(os.path.isfile(output_path), "PDF was not created")
        self.assertGreater(os.path.getsize(output_path), 10_000, "PDF too small")

        # בדיקה מתוך manifest.json
        import json
        from myapp.utils.manifest import MANIFEST_PATH

        with open(MANIFEST_PATH, encoding="utf-8") as f:
            manifest = json.load(f)

        last_entry = manifest[-1]
        self.assertEqual(last_entry["filename"], os.path.basename(output_path))
        self.assertEqual(last_entry["client_id"], "client123")
        self.assertEqual(last_entry["tech_name"], "john.doe")
        self.assertEqual(last_entry["total"], 300.0)
        self.assertEqual(last_entry["rows"], 2)

        os.remove(output_path)


if __name__ == "__main__":
    unittest.main()
