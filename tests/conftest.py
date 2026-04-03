import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Set required env var before importing app modules
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-for-testing")


@pytest.fixture
def app():
    """Create a fresh app instance for testing."""
    import main
    ref_path = Path(__file__).parent.parent / "data" / "carbon-reference.json"
    main.reference_data = json.loads(ref_path.read_text())
    return main.app


@pytest.fixture
def client(app):
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def synthetic_csv_path():
    return Path(__file__).parent / "fixtures" / "synthetic_aws_bill.csv"


@pytest.fixture
def synthetic_csv_bytes(synthetic_csv_path):
    return synthetic_csv_path.read_bytes()
