import os
import fitz
import subprocess
import argparse
import tempfile
from pathlib import Path

from dotenv import load_dotenv

# Carga el .env también cuando se usa convert.py por línea de comandos.
load_dotenv()

# Resolución de render en DPI. Más alto = más resolución y nitidez, pero
# archivos más pesados. 300 = calidad de impresión (default).
DPI = int(os.environ.get("PDFVIDEO_DPI", "300"))

# Calidad de compresión del video (CRF de H.264). MÁS BAJO = MEJOR calidad y más
# peso. Rango útil 0-51: 0 sin pérdida, 18 casi perfecto (default), 23 normal,
# 28 ya se nota la pérdida.
CRF = os.environ.get("PDFVIDEO_CRF", "18")

# Segundos que se muestra cada página en el video.
SECONDS_PER_PAGE = int(os.environ.get("PDFVIDEO_SECONDS_PER_PAGE", "2"))


def render_page_to_png(page: fitz.Page, output_path: Path) -> None:
    """Renderiza una página PDF a PNG en el DPI configurado."""
    scale = DPI / 72
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    pix.save(str(output_path))


def png_to_mp4(png_path: Path, mp4_path: Path, duration: int = SECONDS_PER_PAGE) -> None:
    """Convierte un PNG a un MP4 estático de `duration` segundos."""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(png_path),
        "-t", str(duration),
        "-c:v", "libx264",
        "-crf", str(CRF),
        "-pix_fmt", "yuv420p",
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        str(mp4_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def concatenate_videos(mp4_paths: list[Path], output_path: Path) -> None:
    """Une una lista de MP4s en un único video usando FFmpeg concat demuxer."""
    if not mp4_paths:
        raise ValueError("No hay videos para concatenar")

    # El archivo de lista vive junto a los MP4s de entrada (un dir temporal único
    # por job), no en el directorio de salida — así dos jobs concurrentes que
    # compartan carpeta de salida no se pisan la lista.
    concat_list = mp4_paths[0].parent / "_concat_list.txt"
    lines = "\n".join(f"file '{p.resolve()}'" for p in mp4_paths)
    concat_list.write_text(lines)

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(output_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    finally:
        concat_list.unlink(missing_ok=True)


def convert_pdf(pdf_path: Path, output_path: Path, progress_callback=None) -> int:
    """Convierte un PDF completo en un único MP4 (2 segundos por página).

    progress_callback: callable opcional (done: int, total: int) llamado tras cada página.
    Devuelve el número de páginas del PDF (= número de páginas del video).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf_path))
    total = doc.page_count

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        mp4_paths: list[Path] = []

        for i, page in enumerate(doc, start=1):
            png_path = tmp / f"page_{i:03d}.png"
            mp4_path = tmp / f"page_{i:03d}.mp4"

            print(f"  Página {i}/{total}: renderizando...")
            render_page_to_png(page, png_path)

            print(f"  Página {i}/{total}: convirtiendo a MP4...")
            png_to_mp4(png_path, mp4_path)

            mp4_paths.append(mp4_path)
            if progress_callback is not None:
                progress_callback(i, total)

        doc.close()

        print(f"  Uniendo {len(mp4_paths)} páginas en un video...")
        concatenate_videos(mp4_paths, output_path)

    print(f"\nListo. Video de {total} páginas guardado en: {output_path}")
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Convierte un PDF completo en un video MP4")
    parser.add_argument("pdf", type=Path, help="Ruta al archivo PDF")
    parser.add_argument(
        "--output", "-o", type=Path, default=Path("output.mp4"),
        help="Ruta del video de salida (default: ./output.mp4)"
    )
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"Error: no se encontró el archivo '{args.pdf}'")
        raise SystemExit(1)

    print(f"Convirtiendo '{args.pdf}' -> '{args.output}'...")
    convert_pdf(args.pdf, args.output)


if __name__ == "__main__":
    main()
