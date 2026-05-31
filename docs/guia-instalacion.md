# Guía de instalación paso a paso (para principiantes)

Esta guía asume que **nunca** has usado este proyecto y te lleva de la mano desde
cero hasta tener el conversor funcionando, ya sea por línea de comandos o como
microservicio. Sigue los pasos en orden.

> Convención: las líneas que empiezan con `$` son comandos que escribes en la
> terminal (no copies el `$`). Todo lo demás es explicación o salida esperada.

---

## Paso 0 — ¿Qué necesito antes de empezar?

Tres cosas:

1. **Una terminal.** En Linux/Mac ya la tienes. En Windows usa WSL (Ubuntu).
2. **Python 3.10 o superior.**
3. **FFmpeg** (el programa que arma los videos).

No te preocupes si no los tienes: los instalamos en el Paso 1.

---

## Paso 1 — Instalar los programas base

### 1.1 Comprobar si ya tienes Python

```
$ python3 --version
```

Si responde algo como `Python 3.10.x` o superior, ya estás. Si dice "command not
found" o una versión menor a 3.10, instálalo:

- **Ubuntu / WSL:**
  ```
  $ sudo apt update
  $ sudo apt install python3 python3-venv
  ```
- **Mac (con Homebrew):**
  ```
  $ brew install python
  ```

### 1.2 Instalar FFmpeg

Comprueba si lo tienes:

```
$ ffmpeg -version
```

Si dice "command not found", instálalo:

- **Ubuntu / WSL:**
  ```
  $ sudo apt install ffmpeg
  ```
  (te pedirá tu contraseña; al escribirla no se ve nada, es normal)
- **Mac:**
  ```
  $ brew install ffmpeg
  ```

Vuelve a correr `ffmpeg -version`. Si ahora muestra una versión, listo.

---

## Paso 2 — Descargar el proyecto

Elige una carpeta donde quieras guardarlo (por ejemplo tu carpeta de proyectos) y
clónalo:

```
$ git clone git@github.com:nazho248/PdfToVideo.git
$ cd PdfToVideo
```

A partir de aquí, **todos los comandos se ejecutan dentro de esta carpeta**
(`PdfToVideo`). Si cierras la terminal y vuelves, recuerda entrar de nuevo con
`cd ruta/a/PdfToVideo`.

---

## Paso 3 — Crear el entorno virtual

Un "entorno virtual" es una cajita aislada donde se instalan las librerías de
Python de este proyecto, sin ensuciar el resto de tu sistema.

```
$ python3 -m venv .venv
```

Esto crea una carpeta oculta `.venv`. Ahora **actívala**:

```
$ source .venv/bin/activate
```

Sabrás que está activo porque tu terminal ahora muestra `(.venv)` al inicio de la
línea. **Cada vez que abras una terminal nueva para trabajar en el proyecto,
tienes que volver a activarlo** con ese mismo comando.

Para salir del entorno cuando termines: `deactivate`.

---

## Paso 4 — Instalar las librerías del proyecto

Con el entorno activado (`(.venv)` visible):

```
$ pip install -r requirements.txt
```

Esto descarga e instala todo lo que el proyecto necesita (PyMuPDF, FastAPI, etc.).
Tarda un minuto. Si termina sin errores en rojo, ya está todo listo.

---

## Paso 5 — Probarlo por línea de comandos (lo más simple)

El proyecto trae un PDF de ejemplo llamado `sample.pdf`. Conviértelo:

```
$ python convert.py sample.pdf
```

Verás que va imprimiendo el avance página por página. Al terminar tendrás un
archivo `output.mp4` en la carpeta. Ábrelo con cualquier reproductor (VLC, el
visor de tu sistema, etc.): es un video donde cada página dura 2 segundos.

Para convertir tu propio PDF y elegir dónde guardar el resultado:

```
$ python convert.py /ruta/a/mi-documento.pdf -o /ruta/donde/guardar/video.mp4
```

**Con esto ya tienes lo esencial funcionando.** Los pasos siguientes son solo si
quieres usarlo como servicio para conectarlo con otra aplicación.

---

## Paso 6 — Levantar el microservicio (opcional)

Esto solo lo necesitas si otra app (por ejemplo un backend) va a pedir las
conversiones automáticamente. Si solo querías convertir PDFs a mano, puedes
ignorar este paso.

### 6.1 Definir la clave de acceso

El servicio exige una clave secreta para que nadie más lo use. Defínela como
variable de entorno (cámbiala por algo largo y propio):

```
$ export PDFVIDEO_API_KEY="mi-clave-super-secreta-123"
```

> Esa variable solo dura mientras la terminal esté abierta. Si abres otra
> terminal, vuelve a exportarla.

### 6.2 Arrancar el servicio

```
$ python api.py
```

Verás un mensaje como `Uvicorn running on http://127.0.0.1:8001`. **Deja esa
terminal abierta** (el servicio corre ahí). Para detenerlo, presiona `Ctrl + C`.

### 6.3 Ver que está vivo

Abre el navegador en:

```
http://127.0.0.1:8001/docs
```

Verás una página interactiva con los endpoints. Desde ahí puedes probar las
peticiones sin escribir código.

### 6.4 Probarlo desde otra terminal

Abre una **segunda** terminal (la primera está ocupada con el servicio), entra a
la carpeta del proyecto y lanza una conversión de prueba:

```
$ curl -X POST http://127.0.0.1:8001/jobs \
    -H "X-API-Key: mi-clave-super-secreta-123" \
    -H "Content-Type: application/json" \
    -d "{\"pdf_path\":\"$(pwd)/sample.pdf\",\"output_path\":\"/tmp/prueba.mp4\"}"
```

Te responderá algo como:

```json
{"job_id":"a1b2c3...","status":"queued"}
```

Copia ese `job_id` y consulta el estado:

```
$ curl http://127.0.0.1:8001/jobs/PEGA_AQUI_EL_JOB_ID \
    -H "X-API-Key: mi-clave-super-secreta-123"
```

Irá pasando de `queued` → `processing` → `done`. Cuando esté en `done`, el video
estará en `/tmp/prueba.mp4`.

---

## Paso 7 — Dejarlo corriendo en un servidor (opcional, avanzado)

Para producción no se usa `python api.py`, sino Gunicorn detrás de un servicio
systemd que lo mantenga vivo. Todo eso está explicado en
`docs/operaciones.md`.

---

## Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `command not found: python3` | Python no instalado | Paso 1.1 |
| `command not found: ffmpeg` | FFmpeg no instalado | Paso 1.2 |
| `No module named fitz` / `fastapi` | No activaste el entorno o no instalaste deps | `source .venv/bin/activate` y Paso 4 |
| El prompt no muestra `(.venv)` | Entorno sin activar | `source .venv/bin/activate` |
| `RuntimeError: Falta PDFVIDEO_API_KEY` | No exportaste la clave | Paso 6.1 |
| `401` al llamar la API | La clave del header no coincide con `PDFVIDEO_API_KEY` | Usa la misma clave en ambos lados |
| `400` al llamar la API | La ruta del PDF no existe o está mal escrita | Usa rutas absolutas y verifica que el archivo exista |
| El video no se genera | FFmpeg falló | Confirma `ffmpeg -version` y que el PDF no esté dañado |

---

## Resumen ultra rápido

```
$ sudo apt install python3 python3-venv ffmpeg     # una sola vez
$ git clone git@github.com:nazho248/PdfToVideo.git
$ cd PdfToVideo
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
$ python convert.py sample.pdf                      # ¡listo!
```
