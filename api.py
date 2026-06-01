from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from config import get_config
from convert import SECONDS_PER_PAGE
from jobs import JobStore
from worker import Worker

config = get_config()
store = JobStore(config.db_path)
worker = Worker(store, workers=config.workers, api_key=config.api_key)

app = FastAPI(title="PDF a Video — microservicio")


def _check_key(x_api_key: str | None) -> None:
    if x_api_key != config.api_key:
        raise HTTPException(status_code=401, detail="API key inválida")


class JobRequest(BaseModel):
    pdf_path: str
    output_path: str
    webhook_url: str | None = None


@app.post("/jobs", status_code=202)
def create_job(req: JobRequest, x_api_key: str | None = Header(default=None)):
    _check_key(x_api_key)
    if not Path(req.pdf_path).exists():
        raise HTTPException(status_code=400, detail=f"No existe el PDF: {req.pdf_path}")
    job_id = store.create(pdf_path=req.pdf_path, output_path=req.output_path, webhook_url=req.webhook_url)
    worker.submit(job_id)
    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str, x_api_key: str | None = Header(default=None)):
    _check_key(x_api_key)
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return {
        "job_id": job["id"],
        "status": job["status"],
        "progress": job["progress"],
        "page_count": job["page_count"],
        "seconds_per_page": SECONDS_PER_PAGE,
        "output_path": job["output_path"],
        "error": job["error"],
    }


def main() -> None:
    """Arranca el servidor enlazado solo al host configurado (127.0.0.1 por defecto)."""
    import uvicorn

    uvicorn.run(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
