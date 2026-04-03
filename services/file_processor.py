import asyncio
import csv
import io
import logging
from pathlib import Path

import pdfplumber

import config

logger = logging.getLogger("cloud-carbon-advisor")


def validate_file(file) -> str | None:
    """Validate file extension. Returns error message or None if valid."""
    if not file.filename:
        return "No filename provided."
    ext = Path(file.filename).suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        return f"Unsupported file type '{ext}'. Please upload a PDF, CSV, or TSV file."
    return None


async def extract_text(filename: str, file_bytes: bytes) -> str:
    """Extract text from uploaded file. Runs CPU-bound work in thread pool."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return await asyncio.to_thread(_extract_pdf_text, file_bytes)
    elif ext in (".csv", ".tsv"):
        delimiter = "\t" if ext == ".tsv" else ","
        return await asyncio.to_thread(_extract_csv_text, file_bytes, delimiter)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from PDF using pdfplumber."""
    pages_text = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        total_pages = len(pdf.pages)
        truncated = total_pages > config.MAX_PDF_PAGES
        for page in pdf.pages[:config.MAX_PDF_PAGES]:
            text = page.extract_text()
            if text:
                pages_text.append(text)

    full_text = "\n\n".join(pages_text)

    if len(full_text) < config.MIN_PDF_TEXT_LENGTH:
        raise ValueError(
            "Could not extract sufficient text from this PDF. "
            "It may be a scanned image. Please try a text-based PDF or CSV export."
        )

    if truncated:
        full_text += f"\n\n[NOTE: This PDF has {total_pages} pages. Only the first {config.MAX_PDF_PAGES} were analyzed.]"

    logger.info("PDF extraction: %d pages, %d chars", min(total_pages, config.MAX_PDF_PAGES), len(full_text))
    return full_text


def _extract_csv_text(file_bytes: bytes, delimiter: str = ",") -> str:
    """Extract text from CSV/TSV using built-in csv module."""
    if not file_bytes:
        raise ValueError("Empty file")

    # Try common encodings
    text = None
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            text = file_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if text is None:
        raise ValueError("Unable to decode file. Please ensure it is UTF-8 or Latin-1 encoded.")

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = []
    for i, row in enumerate(reader):
        if i >= config.MAX_CSV_ROWS:
            rows.append(f"[... truncated at {config.MAX_CSV_ROWS} rows. Full file has more data.]")
            break
        rows.append(delimiter.join(row))

    result = "\n".join(rows)
    logger.info("CSV extraction: %d rows, %d chars", len(rows), len(result))
    return result
