import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import fitz
import tempfile
from convert import render_page_to_png, png_to_mp4, concatenate_videos, convert_pdf

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


class TestPngToMp4:
    def test_calls_ffmpeg_with_correct_args(self):
        with patch("convert.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            png = Path("/tmp/page.png")
            mp4 = Path("/tmp/page.mp4")
            png_to_mp4(png, mp4)
            args = mock_run.call_args[0][0]
            assert args[0] == "ffmpeg"
            assert "-loop" in args
            assert "1" in args
            assert "-t" in args
            assert "2" in args
            assert "-crf" in args
            assert "18" in args
            assert str(png) in args
            assert str(mp4) in args

    def test_raises_on_ffmpeg_failure(self):
        with patch("convert.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "ffmpeg")
            with pytest.raises(subprocess.CalledProcessError):
                png_to_mp4(Path("/tmp/p.png"), Path("/tmp/p.mp4"))


class TestConcatenateVideos:
    def test_calls_ffmpeg_concat(self):
        mp4s = [Path("/tmp/p1.mp4"), Path("/tmp/p2.mp4"), Path("/tmp/p3.mp4")]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "completo.mp4"
            with patch("convert.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                concatenate_videos(mp4s, out)
            args = mock_run.call_args[0][0]
            assert args[0] == "ffmpeg"
            assert "-f" in args
            assert "concat" in args
            assert str(out) in args

    def test_raises_on_empty_list(self):
        with pytest.raises(ValueError, match="No hay videos"):
            concatenate_videos([], Path("/tmp/out.mp4"))


class TestConvertPdf:
    def test_creates_one_mp4_per_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "output"
            convert_pdf(SAMPLE_PDF, out_dir, concat=False)
            doc = fitz.open(str(SAMPLE_PDF))
            page_count = doc.page_count
            doc.close()
            mp4s = sorted(out_dir.glob("pagina_*.mp4"))
            assert len(mp4s) == page_count
            assert mp4s[0].name == "pagina_001.mp4"

    def test_concat_creates_combined_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "output"
            convert_pdf(SAMPLE_PDF, out_dir, concat=True)
            assert (out_dir / "video_completo.mp4").exists()

    def test_output_dir_created_automatically(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "nuevo" / "output"
            assert not out_dir.exists()
            convert_pdf(SAMPLE_PDF, out_dir, concat=False)
            assert out_dir.exists()
