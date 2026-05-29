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
