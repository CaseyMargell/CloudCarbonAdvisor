import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import config
from rate_limiter import RateLimiter
from services.file_processor import validate_file, extract_text
from services.llm_service import analyze_bill

logger = logging.getLogger("cloud-carbon-advisor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

reference_data: dict = {}
rate_limiter = RateLimiter(config.RATE_LIMIT_PER_HOUR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global reference_data
    ref_path = Path(__file__).parent / "data" / "carbon-reference.json"
    if ref_path.exists():
        reference_data = json.loads(ref_path.read_text())
        logger.info("Loaded reference data (last_updated: %s)", reference_data.get("last_updated", "unknown"))
    else:
        logger.warning("No carbon-reference.json found — running without reference data")
        reference_data = {}
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
        "style-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'; "
        "connect-src 'self'; "
        "img-src 'self' data:; "
        "font-src 'self'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "contact_url": config.CONTACT_URL,
            "bmac_url": config.BMAC_URL,
            "github_url": config.GITHUB_URL,
            "max_file_size_mb": config.MAX_FILE_SIZE_MB,
        },
    )


@app.get("/sample", response_class=HTMLResponse)
async def sample(request: Request):
    return templates.TemplateResponse(request=request, name="sample.html")


@app.post("/api/analyze")
async def analyze(request: Request, file: UploadFile = File(...)):
    # Validate file
    error = validate_file(file)
    if error:
        return JSONResponse(status_code=400, content={"error": error})

    # Check rate limit
    client_ip = get_client_ip(request)
    allowed, retry_after = await rate_limiter.check(client_ip)
    if not allowed:
        minutes = retry_after // 60 + 1
        return JSONResponse(
            status_code=429,
            content={"error": f"Analysis limit reached ({config.RATE_LIMIT_PER_HOUR}/hour). Try again in {minutes} minute(s)."},
        )

    # Read file bytes
    file_bytes = await file.read()
    if len(file_bytes) > config.MAX_FILE_SIZE_BYTES:
        return JSONResponse(status_code=413, content={"error": f"File too large. Maximum size is {config.MAX_FILE_SIZE_MB}MB."})
    if len(file_bytes) == 0:
        return JSONResponse(status_code=400, content={"error": "The uploaded file is empty."})

    # Extract text
    try:
        bill_text = await extract_text(file.filename or "unknown", file_bytes)
    except Exception as e:
        logger.error("File extraction failed: %s", e)
        return JSONResponse(status_code=400, content={"error": "Unable to read this file. Try a different format or re-export."})

    if not bill_text or len(bill_text.strip()) < 10:
        return JSONResponse(status_code=400, content={"error": "Could not extract meaningful text from this file. For PDFs, try a text-based export rather than a scanned image."})

    # Stream analysis
    async def event_stream():
        try:
            accumulated = ""
            async for chunk in analyze_bill(bill_text, reference_data, request):
                accumulated += chunk
                yield format_sse("chunk", {"content": accumulated})

            yield format_sse("done", {})
        except Exception as e:
            logger.error("Analysis stream error: %s", e)
            yield format_sse("error", {"message": "Analysis was interrupted. Please try again."})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "reference_data_updated": reference_data.get("last_updated", "none"),
    }
