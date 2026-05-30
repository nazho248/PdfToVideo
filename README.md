# PDF to Video

Convierte un PDF completo en un único video MP4, mostrando cada página 2 segundos en orden.

## Requisitos

- Python 3.x
- FFmpeg (`sudo apt install ffmpeg` en Linux / `brew install ffmpeg` en Mac)

## Instalación

```bash
# Crear entorno virtual e instalar dependencias
uv venv .venv
uv pip install pymupdf pytest

# Activar el entorno
source .venv/bin/activate
```

## Uso

```bash
# Genera output.mp4 en el directorio actual
python convert.py documento.pdf

# Ruta de salida personalizada
python convert.py documento.pdf -o videos/resultado.mp4
```

## Salida

Un único archivo MP4 con todas las páginas del PDF en orden:

- Resolución: nativa del PDF (300 DPI — ~2550×3300px para A4)
- Formato: MP4 H.264 CRF 18
- Duración: 2 segundos por página

## Tests

```bash
pytest tests/ -v
```
