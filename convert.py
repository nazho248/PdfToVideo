import fitz
import subprocess
import argparse
import tempfile
from pathlib import Path

DPI = 150  # resolución de render — suficiente para texto nítido en video


def render_page_to_png(page: fitz.Page, output_path: Path) -> None:
    """Renderiza una página PDF a PNG en DPI configurado."""
    scale = DPI / 72
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    pix.save(str(output_path))


def png_to_mp4(png_path: Path, mp4_path: Path, duration: int = 2) -> None:
    """Convierte un PNG a un MP4 estático de `duration` segundos."""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(png_path),
        "-t", str(duration),
        "-c:v", "libx264",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        str(mp4_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
