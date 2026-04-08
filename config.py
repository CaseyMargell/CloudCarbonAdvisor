import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY environment variable is required")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "10"))

CONTACT_URL = os.getenv("CONTACT_URL", "")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "cmargell@gmail.com")
BMAC_URL = os.getenv("BMAC_URL", "")
GITHUB_URL = os.getenv("GITHUB_URL", "")
TREE_DONATION_URL = os.getenv("TREE_DONATION_URL", "https://linktr.ee/chatgptree.ai")
SITE_URL = os.getenv("SITE_URL", "https://caseymargell.com")

# Root path for serving behind a reverse proxy (e.g., "/cloud-carbon-advisor")
# Leave empty when serving at the domain root
ROOT_PATH = os.getenv("ROOT_PATH", "").rstrip("/")

ALLOWED_EXTENSIONS = {".pdf", ".csv", ".tsv"}
MAX_PDF_PAGES = 50
MIN_PDF_TEXT_LENGTH = 200
MAX_CSV_ROWS = 2000
