import os
from dataclasses import dataclass


@dataclass
class Config:
    api_key: str
    workers: int
    db_path: str
    host: str
    port: int


def get_config() -> Config:
    """Lee la configuración desde variables de entorno."""
    api_key = os.environ.get("PDFVIDEO_API_KEY")
    if not api_key:
        raise RuntimeError("Falta la variable de entorno PDFVIDEO_API_KEY")
    return Config(
        api_key=api_key,
        workers=int(os.environ.get("PDFVIDEO_WORKERS", "2")),
        db_path=os.environ.get("PDFVIDEO_DB", "jobs.db"),
        host=os.environ.get("PDFVIDEO_HOST", "127.0.0.1"),
        port=int(os.environ.get("PDFVIDEO_PORT", "8001")),
    )
