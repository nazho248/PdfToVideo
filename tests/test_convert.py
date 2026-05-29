import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import fitz

SAMPLE_PDF = Path(__file__).parent.parent / "sample.pdf"
