import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

SAMPLE_PDF = Path(__file__).parent.parent / "sample.pdf"


@pytest.fixture
def client(tmp_path):
    env = {"PDFVIDEO_API_KEY": "testkey", "PDFVIDEO_DB": str(tmp_path / "jobs.db")}
    with patch.dict(os.environ, env, clear=False):
        import importlib
        import api as api_module
        importlib.reload(api_module)
        with patch.object(api_module.worker, "submit") as mock_submit:
            yield TestClient(api_module.app), api_module, mock_submit


class TestApi:
    def test_post_jobs_requires_api_key(self, client):
        c, _, _ = client
        r = c.post("/jobs", json={"pdf_path": str(SAMPLE_PDF), "output_path": "/tmp/o.mp4"})
        assert r.status_code == 401

    def test_post_jobs_rejects_wrong_key(self, client):
        c, _, _ = client
        r = c.post("/jobs", json={"pdf_path": str(SAMPLE_PDF), "output_path": "/tmp/o.mp4"},
                   headers={"X-API-Key": "malo"})
        assert r.status_code == 401

    def test_post_jobs_creates_job(self, client):
        c, _, mock_submit = client
        r = c.post("/jobs",
                   json={"pdf_path": str(SAMPLE_PDF), "output_path": "/tmp/o.mp4", "webhook_url": "https://x.test/h"},
                   headers={"X-API-Key": "testkey"})
        assert r.status_code == 202
        body = r.json()
        assert "job_id" in body
        assert body["status"] == "queued"
        assert mock_submit.called

    def test_post_jobs_missing_pdf_returns_400(self, client):
        c, _, _ = client
        r = c.post("/jobs",
                   json={"pdf_path": "/no/existe.pdf", "output_path": "/tmp/o.mp4"},
                   headers={"X-API-Key": "testkey"})
        assert r.status_code == 400

    def test_get_job_status(self, client):
        c, _, _ = client
        post = c.post("/jobs",
                      json={"pdf_path": str(SAMPLE_PDF), "output_path": "/tmp/o.mp4"},
                      headers={"X-API-Key": "testkey"})
        job_id = post.json()["job_id"]
        r = c.get(f"/jobs/{job_id}", headers={"X-API-Key": "testkey"})
        assert r.status_code == 200
        assert r.json()["job_id"] == job_id
        assert r.json()["status"] == "queued"

    def test_get_job_requires_api_key(self, client):
        c, _, _ = client
        r = c.get("/jobs/cualquiera")
        assert r.status_code == 401

    def test_get_missing_job_404(self, client):
        c, _, _ = client
        r = c.get("/jobs/no-existe", headers={"X-API-Key": "testkey"})
        assert r.status_code == 404
