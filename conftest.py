"""Repository-wide pytest isolation established before test-module imports."""
from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path


TEST_RUN_DIR = Path(tempfile.gettempdir()) / "omni-pytest-tmp" / uuid.uuid4().hex
TEST_RUN_DIR.mkdir(parents=True, exist_ok=True)

# Some legacy backend tests import ``main`` during collection.  Establish the
# throwaway database before any test module can initialize application settings.
os.environ["OMNI_TEST_RUN_DIR"] = str(TEST_RUN_DIR)
os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_RUN_DIR / 'test.db').as_posix()}"
os.environ["UPLOAD_ROOT"] = str(TEST_RUN_DIR / "uploads")
