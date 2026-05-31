# Operaciones — Despliegue y Hardening

Guía para correr el microservicio PDF→video en un servidor de producción y
lista de mejoras de seguridad/robustez pendientes.

---

## 1. Despliegue en servidor con Gunicorn

FastAPI es ASGI, así que Gunicorn lo corre con workers de Uvicorn.

### Instalación

```bash
uv pip install gunicorn        # ya tienes uvicorn y fastapi
```

### Comando base

```bash
gunicorn api:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 1 \
  --bind 127.0.0.1:8001 \
  --timeout 0
```

Banderas explicadas:

| Bandera | Valor | Por qué |
|---|---|---|
| `--worker-class` | `uvicorn.workers.UvicornWorker` | Gunicorn no habla ASGI por sí solo; este worker traduce |
| `--workers` | `1` (ver nota abajo) | número de **procesos** Gunicorn |
| `--bind` | `127.0.0.1:8001` | **solo localhost** — no usar `0.0.0.0` |
| `--timeout` | `0` | desactiva el kill por timeout: las conversiones son largas y no deben matar al worker |

> **Importante sobre el bind:** bajo Gunicorn, el bloque `main()` de `api.py` NO se
> ejecuta (Gunicorn importa `api:app` directamente). El enlace a localhost lo
> garantiza `--bind 127.0.0.1:8001`. No omitas esa bandera.

### Cuántos workers de Gunicorn usar

Este servicio tiene **estado en proceso**: cada proceso Gunicorn tiene su propio
`ThreadPoolExecutor` (definido por `PDFVIDEO_WORKERS`). El estado de los jobs vive
en SQLite (archivo compartido en modo WAL), así que cualquier proceso puede
responder `GET /jobs/{id}` aunque otro proceso esté haciendo la conversión.

Consecuencias:

- **Concurrencia real total = `(--workers de Gunicorn) × PDFVIDEO_WORKERS`.**
  Ej: 2 procesos × 2 threads = 4 conversiones simultáneas.
- Un job lanzado vía `POST /jobs` se procesa en el `ThreadPoolExecutor` **del
  proceso que recibió la petición**. El webhook y el estado en SQLite funcionan
  igual sin importar qué proceso lo corrió.
- Más procesos = más contención de escritura en SQLite. Para esta carga (pocos
  jobs, larga duración) la contención es despreciable.

**Recomendación:** empezar con **`--workers 1`** y subir `PDFVIDEO_WORKERS` para
controlar la concurrencia. Es el modelo más simple y predecible. Solo subir los
procesos de Gunicorn si un solo proceso se queda corto de CPU.

### Variables de entorno requeridas

```bash
export PDFVIDEO_API_KEY="clave-larga-y-secreta"   # obligatoria
export PDFVIDEO_WORKERS=2                          # conversiones simultáneas por proceso
export PDFVIDEO_DB="/var/lib/pdfvideo/jobs.db"     # ruta persistente del SQLite
```

---

## 2. Servicio systemd (recomendado para producción)

Para que el servicio reviva si se cae y arranque con el sistema.

Crear `/etc/systemd/system/pdfvideo.service`:

```ini
[Unit]
Description=PDF a Video - microservicio
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/pdfToVideo
Environment="PDFVIDEO_API_KEY=clave-larga-y-secreta"
Environment="PDFVIDEO_WORKERS=2"
Environment="PDFVIDEO_DB=/var/lib/pdfvideo/jobs.db"
ExecStart=/var/www/pdfToVideo/.venv/bin/gunicorn api:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 1 \
  --bind 127.0.0.1:8001 \
  --timeout 0
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Activar:

```bash
sudo mkdir -p /var/lib/pdfvideo            # carpeta de la BD, propietario www-data
sudo chown www-data:www-data /var/lib/pdfvideo
sudo systemctl daemon-reload
sudo systemctl enable --now pdfvideo
sudo systemctl status pdfvideo             # verificar que está corriendo
sudo journalctl -u pdfvideo -f             # ver logs en vivo
```

### Notas de despliegue

- **FFmpeg** debe estar instalado en el servidor (`apt install ffmpeg`).
- El usuario del servicio (`www-data`) debe tener **lectura** sobre la carpeta de
  PDFs de Laravel y **escritura** sobre la carpeta de videos. Lo más simple es que
  ambos (Laravel y este servicio) corran como el mismo usuario o compartan grupo.
- Como el bind es `127.0.0.1`, el puerto 8001 no es accesible desde fuera del
  servidor aunque el firewall no lo bloquee. Aun así, conviene `ufw deny 8001`
  como defensa en profundidad.
- Laravel llama a `http://127.0.0.1:8001` directamente; no hace falta Nginx
  delante del microservicio.

---

## 3. Mejoras de hardening pendientes (decisión del equipo)

Estas salieron del code review. No son bugs — son endurecimientos que dependen de
cómo se quiera operar. Se documentan aquí para decidirlas conscientemente.

### 3.1 Validar rutas contra un directorio base permitido

**Situación actual:** `pdf_path` y `output_path` llegan en el body de `POST /jobs`
y se usan tal cual. Un cliente autenticado podría pedir leer/escribir en cualquier
ruta que el proceso alcance (p. ej. escribir un MP4 en una ruta sensible).

**Riesgo:** bajo, porque es una API interna en localhost y Laravel pasa rutas
confiables de `storage/`. Sube si la API key se filtra o si el bind a localhost
fallara.

**Mitigación propuesta:** agregar `PDFVIDEO_BASE_DIR` y rechazar (`400`) cualquier
`pdf_path`/`output_path` que, tras `Path.resolve()`, no quede dentro de ese
directorio base.

### 3.2 Secreto separado para el webhook

**Situación actual:** la misma `X-API-Key` se usa para autenticar las peticiones
entrantes (Laravel→Python) y se envía en el webhook saliente (Python→Laravel).

**Riesgo:** si Laravel registra los headers de las peticiones entrantes (logging
común), el secreto compartido queda en los logs de Laravel.

**Mitigación propuesta:** introducir `PDFVIDEO_WEBHOOK_SECRET` distinto del
`PDFVIDEO_API_KEY`, de modo que cada lado tenga el mínimo privilegio.

### 3.3 Recuperación de jobs tras reinicio

**Situación actual:** si el servicio se reinicia mientras hay jobs en estado
`processing`, esos jobs quedan colgados en `processing` para siempre (su
`ThreadPoolExecutor` murió con el proceso).

**Riesgo:** medio. Tras un reinicio, Laravel nunca recibe el webhook de esos jobs
y al consultar `GET /jobs/{id}` los ve eternamente "procesando".

**Mitigación propuesta:** un barrido al arrancar que busque jobs en `processing`
(o `queued`) y los reencole en el pool. Requiere agregar a `JobStore` un método
para listar jobs por estado, y llamarlo desde el arranque de `api.py`.

---

## Resumen rápido

| Tema | Estado |
|---|---|
| Correr local (dev) | `uvicorn api:app --host 127.0.0.1 --port 8001` |
| Correr en servidor | Gunicorn + worker Uvicorn, `--bind 127.0.0.1:8001`, `--timeout 0` |
| Mantener vivo | servicio systemd con `Restart=always` |
| Concurrencia | `PDFVIDEO_WORKERS` por proceso; empezar con 1 proceso Gunicorn |
| Hardening pendiente | validar rutas, secreto de webhook aparte, recuperación tras reinicio |
