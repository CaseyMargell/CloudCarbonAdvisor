import pytest
from pathlib import Path

from services.file_processor import validate_file, extract_text, _extract_csv_text


class FakeUploadFile:
    def __init__(self, filename):
        self.filename = filename


class TestValidateFile:
    def test_valid_pdf(self):
        assert validate_file(FakeUploadFile("bill.pdf")) is None

    def test_valid_csv(self):
        assert validate_file(FakeUploadFile("export.csv")) is None

    def test_valid_tsv(self):
        assert validate_file(FakeUploadFile("data.tsv")) is None

    def test_invalid_extension(self):
        error = validate_file(FakeUploadFile("malware.exe"))
        assert error is not None
        assert "Unsupported" in error

    def test_xlsx_rejected_in_v1(self):
        error = validate_file(FakeUploadFile("sheet.xlsx"))
        assert error is not None

    def test_no_filename(self):
        error = validate_file(FakeUploadFile(None))
        assert error is not None

    def test_case_insensitive_extension(self):
        assert validate_file(FakeUploadFile("BILL.PDF")) is None
        assert validate_file(FakeUploadFile("data.CSV")) is None


class TestExtractCSV:
    def test_basic_csv(self, synthetic_csv_bytes):
        result = _extract_csv_text(synthetic_csv_bytes, ",")
        assert "m5.2xlarge" in result
        assert "us-east-1" in result
        assert len(result) > 100

    def test_empty_csv(self):
        with pytest.raises(Exception):
            _extract_csv_text(b"", ",")

    def test_truncation(self):
        # Create a large CSV
        rows = ["col1,col2,col3"]
        for i in range(3000):
            rows.append(f"val{i},val{i},val{i}")
        large_csv = "\n".join(rows).encode("utf-8")
        result = _extract_csv_text(large_csv, ",")
        assert "truncated" in result.lower()

    def test_latin1_encoding(self):
        content = "name,cost\nFrankfürt,100\n".encode("latin-1")
        result = _extract_csv_text(content, ",")
        assert "100" in result


@pytest.mark.asyncio
class TestExtractText:
    async def test_csv_extraction(self, synthetic_csv_path):
        file_bytes = synthetic_csv_path.read_bytes()
        result = await extract_text("bill.csv", file_bytes)
        assert "m5.2xlarge" in result

    async def test_unsupported_extension(self):
        with pytest.raises(ValueError, match="Unsupported"):
            await extract_text("file.xlsx", b"data")
