import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """Create a fresh app instance for testing."""
    # Import here to avoid module-level side effects
    import main
    # Pre-load reference data
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


@pytest.fixture
def mock_claude_response():
    """Mock a streaming Claude response."""
    chunks = [
        "## Carbon Footprint Analysis\n\n",
        "Your estimated monthly carbon footprint is **42.5 kg CO2e**.\n\n",
        "### Recommendations\n\n",
        "1. **Migrate to Oregon** — Save 15 kg CO2e/month\n",
    ]
    return chunks
