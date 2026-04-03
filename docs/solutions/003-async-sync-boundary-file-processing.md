---
tags: [fastapi, async, pdfplumber, csv, performance]
category: performance
module: services
symptoms: ["event loop blocked during PDF processing", "slow concurrent request handling"]
---

# Async/Sync Boundary for File Processing

## Problem
pdfplumber and Python's csv module are synchronous CPU-bound operations. Calling them directly in an async FastAPI endpoint blocks the event loop, preventing concurrent request handling.

## Solution
Use `asyncio.to_thread()` to run CPU-bound file processing in a thread pool:

```python
async def extract_text(filename: str, file_bytes: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return await asyncio.to_thread(_extract_pdf_text, file_bytes)
    elif ext in (".csv", ".tsv"):
        return await asyncio.to_thread(_extract_csv_text, file_bytes, delimiter)
```

The `_extract_pdf_text` and `_extract_csv_text` functions are regular synchronous functions that do the actual work.

## Key Details
- `asyncio.to_thread()` is simpler than `loop.run_in_executor()` (Python 3.9+)
- The file bytes are already in memory (read via `await file.read()`) before the thread pool call
- Free file_bytes with `del file_bytes` in a `finally` block after extraction to reduce memory pressure
