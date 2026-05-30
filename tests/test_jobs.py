import tempfile
from pathlib import Path
from jobs import JobStore


class TestJobStore:
    def _store(self, tmp):
        return JobStore(str(Path(tmp) / "jobs.db"))

    def test_create_and_get(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            job_id = store.create(pdf_path="/a/doc.pdf", output_path="/a/doc.mp4", webhook_url="https://x.test/hook")
            job = store.get(job_id)
            assert job["id"] == job_id
            assert job["status"] == "queued"
            assert job["pdf_path"] == "/a/doc.pdf"
            assert job["output_path"] == "/a/doc.mp4"
            assert job["webhook_url"] == "https://x.test/hook"
            assert job["progress"] is None
            assert job["error"] is None

    def test_get_missing_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            assert store.get("no-existe") is None

    def test_update_status_and_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            job_id = store.create(pdf_path="/a.pdf", output_path="/a.mp4", webhook_url=None)
            store.update(job_id, status="processing", progress="3/10")
            job = store.get(job_id)
            assert job["status"] == "processing"
            assert job["progress"] == "3/10"

    def test_update_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            job_id = store.create(pdf_path="/a.pdf", output_path="/a.mp4", webhook_url=None)
            store.update(job_id, status="failed", error="boom")
            job = store.get(job_id)
            assert job["status"] == "failed"
            assert job["error"] == "boom"

    def test_ids_are_unique(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            a = store.create(pdf_path="/a.pdf", output_path="/a.mp4", webhook_url=None)
            b = store.create(pdf_path="/b.pdf", output_path="/b.mp4", webhook_url=None)
            assert a != b
