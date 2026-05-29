# PDF to Video

Convierte cada página de un PDF en un video MP4 de 2 segundos. Opcionalmente genera un video completo con todas las páginas en orden.

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
# Un MP4 por página (output/pagina_001.mp4, pagina_002.mp4, ...)
python convert.py documento.pdf

# Un MP4 por página + video completo (output/video_completo.mp4)
python convert.py documento.pdf --concat

# Carpeta de salida personalizada
python convert.py documento.pdf -o mi_carpeta --concat
```

## Salida

```
output/
├── pagina_001.mp4
├── pagina_002.mp4
├── ...
└── video_completo.mp4   # solo con --concat
```

- Resolución: nativa del PDF (300 DPI — ~2550×3300px para A4)
- Formato: MP4 H.264 CRF 18
- Duración por página: 2 segundos

## Tests

```bash
pytest tests/ -v
```
