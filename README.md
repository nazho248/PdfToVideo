# PdfToVideo

Convierte un PDF en un video MP4 donde cada página se muestra durante 2 segundos.
Sirve para pasar presentaciones, apuntes o documentos a un formato de video que
luego puedes subir a YouTube, VdoCipher, una plataforma de cursos, etc.

Render a 300 DPI, así que el texto se lee nítido. Se puede usar como script de
línea de comandos o levantarlo como microservicio HTTP para integrarlo con otra
app (por ejemplo un backend Laravel).

## Requisitos

- Python 3.10 o superior
- FFmpeg instalado en el sistema

En Debian/Ubuntu:

```bash
sudo apt update
sudo apt install ffmpeg
```

En macOS:

```bash
brew install ffmpeg
```

## Instalación

¿Primera vez? Hay una guía paso a paso bien detallada en
`docs/guia-instalacion.md`.

Clona el repo y crea un entorno virtual. Si usas `uv`:

```bash
git clone git@github.com:nazho248/PdfToVideo.git
cd PdfToVideo
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Con `pip` normal funciona igual:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso por línea de comandos

Lo más básico, deja el video en `output.mp4`:

```bash
python convert.py documento.pdf
```

Indicando dónde guardarlo:

```bash
python convert.py documento.pdf -o videos/resultado.mp4
```

El video sale en H.264 (CRF 18) a la resolución nativa del PDF. Para un A4 eso
ronda los 2550x3300 px. Un documento de 15 páginas tarda un par de minutos y pesa
unos pocos MB.

## Microservicio HTTP

Si necesitas convertir desde otra aplicación, el servicio expone una API que
encola las conversiones y avisa cuando terminan. No recibe el PDF por la red:
le pasas la ruta del archivo en disco, así que pensado para correr en el mismo
servidor que la app que lo consume.

Configura la clave de acceso copiando la plantilla y editándola:

```bash
cp .env.example .env
# edita .env y pon tu clave en PDFVIDEO_API_KEY
```

Y arranca:

```bash
python api.py
```

El `.env` se carga solo (vía `python-dotenv`), no hace falta exportar nada. Queda
escuchando en `127.0.0.1:8001` (solo localhost) y pide el header `X-API-Key` en
todas las rutas. La documentación interactiva está en
`http://127.0.0.1:8001/docs`.

### Endpoints

`POST /jobs` — encola una conversión y responde al instante:

```json
{
  "pdf_path": "/ruta/absoluta/documento.pdf",
  "output_path": "/ruta/absoluta/video.mp4",
  "webhook_url": "https://tu-app.com/webhook"
}
```

Devuelve `{ "job_id": "...", "status": "queued" }`.

`GET /jobs/{job_id}` — consulta el estado (`queued`, `processing`, `done` o
`failed`) y el progreso por página.

Cuando el job termina, el servicio hace un `POST` al `webhook_url` con el
resultado. Si no pasas `webhook_url`, simplemente consulta el estado tú mismo.

### Configuración

Se lee de variables de entorno:

| Variable | Default | Descripción |
|---|---|---|
| `PDFVIDEO_API_KEY` | — | clave de acceso (obligatoria) |
| `PDFVIDEO_WORKERS` | `2` | conversiones simultáneas |
| `PDFVIDEO_DB` | `jobs.db` | ruta del SQLite con el estado de los jobs |
| `PDFVIDEO_HOST` | `127.0.0.1` | host de escucha |
| `PDFVIDEO_PORT` | `8001` | puerto |
| `PDFVIDEO_DPI` | `300` | resolución de render; más alto = más nítido y pesado |
| `PDFVIDEO_CRF` | `18` | compresión H.264; más bajo = mejor calidad y más peso |

Estas variables también aplican al uso por línea de comandos (se leen del `.env`).

Para desplegarlo en un servidor (gunicorn + systemd) ver `docs/operaciones.md`.

### Ajustar la calidad del video

Dos perillas controlan el equilibrio calidad/peso:

- **`PDFVIDEO_DPI`** — la resolución. Cada página se renderiza a `tamaño × DPI/72`
  píxeles. `150` da archivos ligeros, `300` (default) es calidad de impresión,
  `600` es muy nítido pero pesado.
- **`PDFVIDEO_CRF`** — cuánto comprime FFmpeg. Va de 0 a 51, y **más bajo es mejor
  calidad** (y más peso): `0` sin pérdida, `18` casi perfecto (default), `23`
  normal, `28` ya se nota.

Si los videos pesan demasiado, sube el CRF (p. ej. `23`) o baja el DPI (p. ej.
`200`). Si quieres máxima nitidez, baja el CRF y sube el DPI.

## Tests

```bash
pytest tests/ -v
```

Algunos tests ejecutan FFmpeg de verdad sobre el PDF de ejemplo, así que la
suite completa tarda unos minutos.

## Cómo funciona

El proceso es directo: PyMuPDF renderiza cada página del PDF a una imagen PNG, y
FFmpeg convierte cada imagen en un clip estático de 2 segundos. Al final esos
clips se concatenan en un único MP4. Los archivos intermedios se generan en una
carpeta temporal y se borran solos.

## Licencia

MIT
