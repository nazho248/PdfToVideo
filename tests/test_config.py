import os
from unittest.mock import patch
from config import get_config


class TestConfig:
    def test_reads_api_key_from_env(self):
        with patch.dict(os.environ, {"PDFVIDEO_API_KEY": "secreto123"}):
            cfg = get_config()
            assert cfg.api_key == "secreto123"

    def test_defaults(self):
        with patch.dict(os.environ, {"PDFVIDEO_API_KEY": "k"}, clear=True):
            cfg = get_config()
            assert cfg.workers == 2
            assert cfg.db_path == "jobs.db"
            assert cfg.host == "127.0.0.1"
            assert cfg.port == 8001

    def test_custom_values(self):
        env = {
            "PDFVIDEO_API_KEY": "k",
            "PDFVIDEO_WORKERS": "4",
            "PDFVIDEO_DB": "/tmp/x.db",
            "PDFVIDEO_PORT": "9000",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = get_config()
            assert cfg.workers == 4
            assert cfg.db_path == "/tmp/x.db"
            assert cfg.port == 9000

    def test_missing_api_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            import pytest
            with pytest.raises(RuntimeError, match="PDFVIDEO_API_KEY"):
                get_config()
