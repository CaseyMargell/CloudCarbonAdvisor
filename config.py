import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "10"))

CONTACT_URL = os.getenv("CONTACT_URL", "")
BMAC_URL = os.getenv("BMAC_URL", "")
GITHUB_URL = os.getenv("GITHUB_URL", "")

ALLOWED_EXTENSIONS = {".pdf", ".csv", ".tsv"}
MAX_PDF_PAGES = 50
MIN_PDF_TEXT_LENGTH = 200
MAX_CSV_ROWS = 2000
