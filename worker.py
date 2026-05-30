import logging
from concurrent.futures import ThreadPoolExecutor, Future
from pathlib import Path

import httpx

from convert import convert_pdf
from jobs import JobStore

logger = logging.getLogger(__name__)


class Worker:
    """Ejecuta conversiones en un pool de threads y notifica vía webhook."""

    def __init__(self, store: JobStore, workers: int, api_key: str):
        self.store = store
        self.api_key = api_key
        self.executor = ThreadPoolExecutor(max_workers=workers)

    def submit(self, job_id: str) -> Future:
        """Encola un job en el pool. Devuelve el Future."""
        return self.executor.submit(self.run_job, job_id)

    def run_job(self, job_id: str) -> None:
        """Procesa un job de inicio a fin, actualizando estado y disparando webhook."""
        job = self.store.get(job_id)
        if job is None:
            return

        try:
            self.store.update(job_id, status="processing")

            def on_progress(done: int, total: int) -> None:
                self.store.update(job_id, progress=f"{done}/{total}")

            convert_pdf(Path(job["pdf_path"]), Path(job["output_path"]), progress_callback=on_progress)
            self.store.update(job_id, status="done")
            self._notify(job, status="done", output_path=job["output_path"], error=None)
        except Exception as exc:  # noqa: BLE001 — queremos capturar cualquier fallo del job
            self.store.update(job_id, status="failed", error=str(exc))
            self._notify(job, status="failed", output_path=None, error=str(exc))

    def _notify(self, job: dict, status: str, output_path: str | None, error: str | None) -> None:
        webhook_url = job.get("webhook_url")
        if not webhook_url:
            return
        payload = {
            "job_id": job["id"],
            "status": status,
            "output_path": output_path,
            "error": error,
        }
        try:
            httpx.post(webhook_url, json=payload, headers={"X-API-Key": self.api_key}, timeout=10)
        except Exception as exc:  # noqa: BLE001 — un webhook fallido no debe romper el worker
            # No reintentamos: Laravel puede consultar GET /jobs/{id} como respaldo.
            logger.warning("Webhook falló para job %s (%s): %s", job["id"], webhook_url, exc)

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False)
