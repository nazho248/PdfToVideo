import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from jobs import JobStore
from worker import Worker


class TestWorker:
    def _store(self, tmp):
        return JobStore(str(Path(tmp) / "jobs.db"))

    def test_run_job_success_updates_status_and_webhook(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            job_id = store.create(pdf_path="/a.pdf", output_path="/a.mp4", webhook_url="https://x.test/hook")
            worker = Worker(store, workers=1, api_key="k")

            with patch("worker.convert_pdf") as mock_convert, patch("worker.httpx.post") as mock_post:
                def fake_convert(pdf, out, progress_callback=None):
                    if progress_callback:
                        progress_callback(1, 2)
                        progress_callback(2, 2)
                    return 2
                mock_convert.side_effect = fake_convert
                worker.run_job(job_id)

            job = store.get(job_id)
            assert job["status"] == "done"
            assert job["progress"] == "2/2"
            assert job["page_count"] == 2
            assert mock_post.called
            kwargs = mock_post.call_args.kwargs
            assert kwargs["json"]["status"] == "done"
            assert kwargs["json"]["job_id"] == job_id
            assert kwargs["json"]["page_count"] == 2
            assert kwargs["json"]["seconds_per_page"] == 2
            assert kwargs["headers"]["X-API-Key"] == "k"

    def test_run_job_failure_sets_failed_and_webhook(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            job_id = store.create(pdf_path="/a.pdf", output_path="/a.mp4", webhook_url="https://x.test/hook")
            worker = Worker(store, workers=1, api_key="k")

            with patch("worker.convert_pdf", side_effect=RuntimeError("boom")), patch("worker.httpx.post") as mock_post:
                worker.run_job(job_id)

            job = store.get(job_id)
            assert job["status"] == "failed"
            assert "boom" in job["error"]
            assert mock_post.call_args.kwargs["json"]["status"] == "failed"

    def test_no_webhook_when_url_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            job_id = store.create(pdf_path="/a.pdf", output_path="/a.mp4", webhook_url=None)
            worker = Worker(store, workers=1, api_key="k")
            with patch("worker.convert_pdf", return_value=1), patch("worker.httpx.post") as mock_post:
                worker.run_job(job_id)
            assert not mock_post.called

    def test_submit_runs_in_pool(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store(tmp)
            job_id = store.create(pdf_path="/a.pdf", output_path="/a.mp4", webhook_url=None)
            worker = Worker(store, workers=2, api_key="k")
            with patch("worker.convert_pdf", return_value=3):
                future = worker.submit(job_id)
                future.result(timeout=5)
            assert store.get(job_id)["status"] == "done"
