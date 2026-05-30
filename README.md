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

## Microservicio HTTP (para Laravel)

Expone la conversión como API local asíncrona. Ver diseño completo en

### Arranque

```bash
export PDFVIDEO_API_KEY="una-clave-larga-y-secreta"
export PDFVIDEO_WORKERS=2          # conversiones simultáneas (opcional)
.venv/bin/uvicorn api:app --host 127.0.0.1 --port 8001
```

El servicio solo escucha en `127.0.0.1` (no acepta tráfico externo) y exige el
header `X-API-Key` en todas las rutas.

### Endpoints

- `POST /jobs` → encola una conversión, responde `{job_id, status}` al instante
- `GET /jobs/{job_id}` → estado actual (`queued`/`processing`/`done`/`failed`)
- Al terminar, hace `POST` al `webhook_url` indicado con el resultado

### Ejemplo desde Laravel

```php
$res = Http::withHeaders(['X-API-Key' => config('services.pdfvideo.key')])
    ->post('http://127.0.0.1:8001/jobs', [
        'pdf_path'    => storage_path('app/pdfs/doc.pdf'),
        'output_path' => storage_path('app/videos/doc.mp4'),
        'webhook_url' => route('video.listo'),
    ]);
$jobId = $res->json('job_id');
```
