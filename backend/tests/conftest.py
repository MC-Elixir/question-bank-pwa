from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def standard_docx(fixtures_dir: Path) -> Path:
    return fixtures_dir / "standard_mixed.docx"


@pytest.fixture(scope="session")
def missing_answer_docx(fixtures_dir: Path) -> Path:
    return fixtures_dir / "missing_answer.docx"


@pytest.fixture(scope="session")
def mixed_format_docx(fixtures_dir: Path) -> Path:
    return fixtures_dir / "mixed_format.docx"
