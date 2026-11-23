import os
import tempfile

import pytest

# Force mock LLM + a throwaway DB file before any app module is imported.
os.environ["LLM_PROVIDER"] = "mock"
os.environ["SEED_DEMO_DATA"] = "false"
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
