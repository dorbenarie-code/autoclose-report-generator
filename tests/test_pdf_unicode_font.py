import os
import unittest
from fpdf import FPDF
import pytest


class TestPDFUnicodeFont(unittest.TestCase):
    def test_pdf_with_unicode_font(self) -> None:
        pdf = FPDF()
        pdf.add_page()
        font_path = "static/fonts/DejaVuSans.ttf"
        if not os.path.isfile(font_path):
            pytest.skip(f"Font file not found: {font_path}")
        self.assertTrue(os.path.isfile(font_path), f"Font file not found: {font_path}")
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", "", 14)
        pdf.cell(0, 10, "טקסט בעברית - בדיקה", ln=True)
        output_path = "output/test_unicode_font.pdf"
        pdf.output(output_path)
        self.assertTrue(os.path.isfile(output_path))
        os.remove(output_path)


if __name__ == "__main__":
    unittest.main()
