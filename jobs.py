import sqlite3
import threading
import uuid
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobStore:
    """Almacén de jobs en SQLite. Seguro para uso concurrente desde varios threads."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    pdf_path TEXT NOT NULL,
                    output_path TEXT NOT NULL,
                    webhook_url TEXT,
                    progress TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, pdf_path: str, output_path: str, webhook_url: str | None) -> str:
        job_id = str(uuid.uuid4())
        now = _now()
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO jobs (id, status, pdf_path, output_path, webhook_url, progress, error, created_at, updated_at) "
                "VALUES (?, 'queued', ?, ?, ?, NULL, NULL, ?, ?)",
                (job_id, pdf_path, output_path, webhook_url, now, now),
            )
        return job_id

    def update(self, job_id: str, status: str | None = None, progress: str | None = None, error: str | None = None) -> None:
        sets = ["updated_at = ?"]
        vals: list = [_now()]
        if status is not None:
            sets.append("status = ?")
            vals.append(status)
        if progress is not None:
            sets.append("progress = ?")
            vals.append(progress)
        if error is not None:
            sets.append("error = ?")
            vals.append(error)
        vals.append(job_id)
        with self._lock, self._connect() as conn:
            conn.execute(f"UPDATE jobs SET {', '.join(sets)} WHERE id = ?", vals)

    def get(self, job_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return dict(row) if row else None
