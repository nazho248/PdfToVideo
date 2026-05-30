import fitz
import subprocess
import argparse
import tempfile
from pathlib import Path

DPI = 300  # resolución de render — calidad de impresión, texto perfectamente nítido


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


def concatenate_videos(mp4_paths: list[Path], output_path: Path) -> None:
    """Une una lista de MP4s en un único video usando FFmpeg concat demuxer."""
    if not mp4_paths:
        raise ValueError("No hay videos para concatenar")

    concat_list = output_path.parent / "_concat_list.txt"
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


def convert_pdf(pdf_path: Path, output_path: Path) -> None:
    """Convierte un PDF completo en un único MP4 (2 segundos por página)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf_path))

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        mp4_paths: list[Path] = []

        for i, page in enumerate(doc, start=1):
            png_path = tmp / f"page_{i:03d}.png"
            mp4_path = tmp / f"page_{i:03d}.mp4"

            print(f"  Página {i}/{doc.page_count}: renderizando...")
            render_page_to_png(page, png_path)

            print(f"  Página {i}/{doc.page_count}: convirtiendo a MP4...")
            png_to_mp4(png_path, mp4_path)

            mp4_paths.append(mp4_path)

        page_count = doc.page_count
        doc.close()

        print(f"  Uniendo {len(mp4_paths)} páginas en un video...")
        concatenate_videos(mp4_paths, output_path)

    print(f"\nListo. Video de {page_count} páginas guardado en: {output_path}")


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
