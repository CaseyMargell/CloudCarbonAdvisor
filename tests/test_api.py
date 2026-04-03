import json
from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "reference_data_updated" in data

    def test_health_includes_reference_date(self, client):
        response = client.get("/api/health")
        data = response.json()
        # Reference data is loaded, should have a date
        assert data["reference_data_updated"] != "none"


class TestIndexPage:
    def test_index_returns_html(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Cloud Carbon Advisor" in response.text

    def test_index_has_upload_form(self, client):
        response = client.get("/")
        assert 'id="drop-zone"' in response.text
        assert 'id="file-input"' in response.text

    def test_index_has_privacy_note(self, client):
        response = client.get("/")
        assert "immediately discarded" in response.text

    def test_index_has_csp_header(self, client):
        response = client.get("/")
        assert "Content-Security-Policy" in response.headers


class TestAnalyzeEndpoint:
    def test_rejects_no_file(self, client):
        response = client.post("/api/analyze")
        assert response.status_code == 422  # FastAPI validation error

    def test_rejects_wrong_extension(self, client):
        response = client.post(
            "/api/analyze",
            files={"file": ("malware.exe", b"evil content", "application/octet-stream")},
        )
        assert response.status_code == 400
        assert "Unsupported" in response.json()["error"]

    def test_rejects_empty_file(self, client):
        response = client.post(
            "/api/analyze",
            files={"file": ("empty.csv", b"", "text/csv")},
        )
        assert response.status_code == 400
        assert "empty" in response.json()["error"].lower()

    def test_rejects_oversized_file(self, client):
        # Create a file just over 20MB
        big_content = b"x" * (21 * 1024 * 1024)
        response = client.post(
            "/api/analyze",
            files={"file": ("big.csv", big_content, "text/csv")},
        )
        assert response.status_code == 413

    def test_rate_limiting(self, client):
        """After hitting the limit, should get 429."""
        # Set rate limit low for testing
        import config
        original_limit = config.RATE_LIMIT_PER_HOUR
        config.RATE_LIMIT_PER_HOUR = 2

        import main
        main.rate_limiter = __import__("rate_limiter").RateLimiter(2)

        csv_content = b"service,cost\nEC2,100\nS3,50\n"

        try:
            with patch("main.analyze_bill") as mock_analyze:
                async def fake_stream(*args, **kwargs):
                    yield "test"
                mock_analyze.return_value = fake_stream()

                # First two should work (they'll fail at Claude but pass rate limit)
                for _ in range(2):
                    client.post(
                        "/api/analyze",
                        files={"file": ("bill.csv", csv_content, "text/csv")},
                    )

                # Third should be rate limited
                response = client.post(
                    "/api/analyze",
                    files={"file": ("bill.csv", csv_content, "text/csv")},
                )
                assert response.status_code == 429
                assert "limit" in response.json()["error"].lower()
        finally:
            config.RATE_LIMIT_PER_HOUR = original_limit
            main.rate_limiter = __import__("rate_limiter").RateLimiter(original_limit)

    def test_csv_triggers_streaming(self, client, synthetic_csv_path):
        """A valid CSV should trigger the streaming response (mocked Claude)."""
        csv_bytes = synthetic_csv_path.read_bytes()

        with patch("main.analyze_bill") as mock_analyze:
            async def fake_stream(*args, **kwargs):
                yield "## Analysis\n\nTest result"

            mock_analyze.return_value = fake_stream()

            response = client.post(
                "/api/analyze",
                files={"file": ("bill.csv", csv_bytes, "text/csv")},
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

            # Check SSE format
            body = response.text
            assert "event: chunk" in body
            assert "event: done" in body


class TestSSEFormat:
    def test_sse_events_are_valid_json(self, client, synthetic_csv_path):
        """SSE data fields should be valid JSON."""
        csv_bytes = synthetic_csv_path.read_bytes()

        with patch("main.analyze_bill") as mock_analyze:
            async def fake_stream(*args, **kwargs):
                yield "Hello "
                yield "world"

            mock_analyze.return_value = fake_stream()

            response = client.post(
                "/api/analyze",
                files={"file": ("bill.csv", csv_bytes, "text/csv")},
            )

            lines = response.text.strip().split("\n")
            for line in lines:
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    assert isinstance(data, dict)

    def test_done_event_sent_after_chunks(self, client, synthetic_csv_path):
        csv_bytes = synthetic_csv_path.read_bytes()

        with patch("main.analyze_bill") as mock_analyze:
            async def fake_stream(*args, **kwargs):
                yield "Result text"

            mock_analyze.return_value = fake_stream()

            response = client.post(
                "/api/analyze",
                files={"file": ("bill.csv", csv_bytes, "text/csv")},
            )

            body = response.text
            chunk_pos = body.find("event: chunk")
            done_pos = body.find("event: done")
            assert chunk_pos < done_pos  # done comes after chunks
