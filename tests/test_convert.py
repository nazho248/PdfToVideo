import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import fitz
import tempfile
from convert import render_page_to_png

SAMPLE_PDF = Path(__file__).parent.parent / "sample.pdf"


class TestRenderPageToPng:
    def test_creates_png_file(self):
        doc = fitz.open(str(SAMPLE_PDF))
        page = doc[0]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "page.png"
            render_page_to_png(page, out)
            assert out.exists()
        doc.close()

    def test_png_has_correct_dimensions(self):
        """El PNG debe tener dimensiones proporcionales al tamaño del PDF."""
        doc = fitz.open(str(SAMPLE_PDF))
        page = doc[0]
        expected_w = round(page.rect.width * 150 / 72)
        expected_h = round(page.rect.height * 150 / 72)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "page.png"
            render_page_to_png(page, out)
            pix = fitz.Pixmap(str(out))
            assert abs(pix.width - expected_w) <= 2
            assert abs(pix.height - expected_h) <= 2
        doc.close()
