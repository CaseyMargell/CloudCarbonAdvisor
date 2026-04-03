# Cloud Carbon Advisor — Technical Specification

## Project Summary

A web application where users upload their cloud provider bill (PDF or CSV) and receive immediate, actionable recommendations for reducing the carbon footprint of their cloud infrastructure. No accounts, no auth, no stored data. Upload a file, get results, done.

The backend uses an LLM (Claude API) to extract structured data from uploaded bills and generate prioritized carbon reduction recommendations. A weekly background job maintains a current reference dataset of carbon intensity by cloud region and instance family.

## Design Philosophy

- **Stupid simple for the user.** One page. Upload a file. Get results. Nothing else.
- **Stupid simple for the developer.** One language (Python). One service. No build step. No JavaScript framework. No node_modules. HTML goes in template files. Script tags go in the head. Dependencies stay minimal and stable.
- **Zero data retention.** Bills are processed in memory and discarded. No database for user data. No cookies, no tracking beyond basic anonymous request counts logged to stdout.
- **LLM-native architecture.** Don't build a rule engine. Don't build a bill parser per provider. Let the LLM extract structured data from whatever format the user provides, and let it reason about recommendations using the reference dataset as context.
- **Low cost to operate.** Target < $50/month at moderate traffic (100-500 analyses/month). Single Railway service on a personal account.

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Single Railway Service                  │
│                                                      │
│   FastAPI (Python)                                   │
│   ├── Serves HTML pages via Jinja2 templates         │
│   ├── Serves static files (CSS, icons)               │
│   ├── POST /api/analyze (file upload + SSE stream)   │
│   ├── GET /api/health                                │
│   └── Reads carbon-reference.json from disk          │
│                                                      │
│   Frontend: HTML + HTMX (CDN) + Tailwind (CDN)      │
│   No build step. No npm. No node_modules.            │
└─────────────────────┬───────────────────────────────┘
                      │
        ┌─────────────▼──────────┐
        │    Claude API           │
        │    (claude-sonnet-4-20250514)    │
        │    Streaming response   │
        └────────────────────────┘

┌─────────────────────────────────────────────────────┐
│           Weekly Reference Data Job                  │
│   - Pulls carbon intensity per cloud region          │
│   - Pulls instance family energy profiles            │
│   - Writes carbon-reference.json                     │
│   - Runs via GitHub Actions cron (free)              │
│   - Commits updated JSON to repo                     │
└─────────────────────────────────────────────────────┘
```

## Tech Stack

- **Python 3.12+**
- **FastAPI** — web framework, serves both HTML pages and API endpoints
- **Jinja2** — HTML templating (included with FastAPI)
- **HTMX** — handles file upload via AJAX and SSE streaming into the page (loaded from CDN, one script tag)
- **Tailwind CSS** — styling (loaded from CDN, no build step)
- **Anthropic Python SDK** — Claude API with streaming
- **pdfplumber** — PDF text extraction
- **openpyxl** — XLSX reading (if needed)
- **uvicorn** — ASGI server

That's it. No JavaScript framework. No bundler. No transpiler. No package.json.

## Frontend Specification

The frontend is server-rendered HTML with HTMX for interactivity. All pages are Jinja2 templates served by FastAPI.

### Page States

The single page has three visual states, managed by HTMX swapping content in and out of a main container div.

**State 1: Upload (default)**
- Clean, centered layout
- Headline: "Upload your cloud bill. Get carbon reduction recommendations in 60 seconds."
- Brief subtext explaining what this does (one sentence)
- Large drag-and-drop zone that also works as a click-to-upload button
- Accepted formats noted below the zone: "AWS, Azure, or GCP bills — PDF or CSV"
- Below the upload zone: a brief "How it works" section (3 short items, not a wall of text)
- Privacy note: "Your data is never stored. Bills are analyzed in memory and immediately discarded."
- Link to a sample analysis so people can see what they'll get before uploading

**State 2: Processing**
- The upload zone is replaced (via HTMX swap) with a processing indicator
- Brief "Analyzing your bill..." message with a CSS-only animation (no JS needed)
- As the SSE stream begins, the processing indicator transitions to the results area
- Results render progressively as the stream arrives

**State 3: Results**
- Full rendered analysis streamed into a results div
- The LLM response is markdown — convert to HTML server-side as each SSE chunk arrives, OR use a lightweight markdown-to-HTML library client-side (see HTMX SSE section below)
- A "Download as PDF" button (using the browser's window.print() with a print stylesheet — simplest possible approach, no library needed)
- A "Start over" link that reloads the page
- At the bottom: tip jar CTA and consulting mention

### HTMX Integration

**File upload:** Use `hx-post="/api/analyze"` with `hx-encoding="multipart/form-data"` on the form. This submits the file via AJAX without a page reload.

**SSE streaming:** HTMX has a built-in SSE extension. Use `hx-ext="sse"` with `sse-connect="/api/analyze"` to consume the streaming response. Each SSE event contains a chunk of HTML (the backend converts markdown chunks to HTML before sending). HTMX appends each chunk into the results container.

**Important:** The SSE extension needs to be loaded separately:
```html
<script src="https://unpkg.com/htmx.org@2.0.4"></script>
<script src="https://unpkg.com/htmx-ext-sse@2.3.0/sse.js"></script>
```

**Markdown rendering approach:** The simplest path is to have the backend accumulate the streamed markdown response, convert completed sections to HTML (using Python's `markdown` library), and send HTML fragments via SSE. This keeps all rendering server-side and means the browser just appends HTML. No client-side markdown library needed.

### Drag-and-Drop File Upload

This is the one place where a small inline script is needed. HTMX handles form submission, but the drag-and-drop visual feedback (highlighting the drop zone, reading the dropped file into the form's file input) requires a few lines of vanilla JavaScript:

```html
<script>
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    fileInput.files = e.dataTransfer.files;
    // Trigger the HTMX form submission
    htmx.trigger(document.getElementById('upload-form'), 'submit');
  });
</script>
```

This is the extent of the custom JavaScript in the entire application.

### Tip Jar / CTA Section

At the bottom of results and in a subtle footer on the upload page:
- "This tool is free and open source. If it saved you time or helped you reduce your carbon footprint:"
- Buy Me a Coffee button/link (simple href, no embed script)
- "Need hands-on help optimizing your cloud infrastructure? [Get in touch]" — link is configurable via env var (CONTACT_URL)
- GitHub repo link

### Design Direction
- Clean, professional, slightly opinionated
- White/light background, good typography, generous whitespace
- Accent color: sophisticated teal or forest green (not neon)
- Mobile-responsive but desktop is the primary use case
- No dark mode for v1
- The CSS will be minimal since Tailwind utility classes handle most styling inline
- Add a print stylesheet that hides the upload form, footer, and buttons so window.print() produces a clean report

### Sample Analysis Page

Create a `/sample` route that serves a pre-generated analysis result as a static HTML page. This lets potential users see the quality and depth of the output before uploading their own bill. Generate this once from a synthetic AWS bill and save it as a template.

## Backend Specification

### API Endpoints

**`GET /`** — Serves the main page (upload form)

**`GET /sample`** — Serves the pre-generated sample analysis

**`POST /api/analyze`**
- Accepts: `multipart/form-data` with a single file field
- Returns: `text/event-stream` (Server-Sent Events)
- Process:
  1. Validate file type and size
  2. If PDF: extract text using pdfplumber. If text extraction yields < 200 chars, fall back to sending the PDF as base64 to Claude's document/vision capability
  3. If CSV/TSV: read into text representation. If > 5000 rows, group by region/service/instance family and summarize
  4. If XLSX: convert to CSV-like text using openpyxl, then same summarization logic
  5. Load carbon reference data from memory cache
  6. Construct the analysis prompt (system prompt + reference data + extracted bill text)
  7. Call Claude API with streaming enabled
  8. As each text chunk arrives from Claude, accumulate it and convert completed markdown sections to HTML fragments
  9. Send each HTML fragment as an SSE event
  10. After the response completes, discard all file data from memory
- Error handling: return SSE events with error messages for unsupported formats, files too large, API failures, and rate limits. The frontend should display these in the results area.

**`GET /api/health`**
- Returns `200 OK` with `{"status": "ok", "reference_data_updated": "<date>"}`

### File Processing Details

**PDF handling:**
- Use pdfplumber to extract text from all pages
- Don't try to be clever about parsing — extract the raw text and let the LLM make sense of it
- For very large PDFs (> 50 pages), truncate to the first 50 pages and note this in the prompt
- If text extraction yields very little text (< 200 chars), the PDF is likely image-based. Fall back to sending it as a base64 document to Claude's vision capability. This costs more per analysis — log it so we can track frequency.

**CSV/TSV handling:**
- Read into a pandas DataFrame
- If > 5000 rows, summarize: group by region, service type, and instance family, summing usage hours and cost
- Convert the structured summary to a clean text representation for the prompt

**XLSX handling:**
- Use openpyxl to read, convert to DataFrame, then same logic as CSV

### Rate Limiting
- Simple in-memory rate limiting: max 10 analyses per IP per hour
- Python dict with timestamps, cleaned up periodically
- No Redis or external state needed at this traffic volume
- Return a 429 with a friendly message rendered in the results area via SSE

### Reference Data Caching
- Load `carbon-reference.json` into memory at startup
- Reload from disk every hour (simple background task using FastAPI's lifespan or a periodic check)
- The file is small (< 100KB) — memory is fine

### Cost Management
- Use `claude-sonnet-4-20250514` for all analyses
- Set `max_tokens` to 4096 for the response
- Log input/output token counts per request to stdout for cost tracking
- Estimated cost per analysis: $0.05-0.30 depending on bill size
- At 500 analyses/month with average $0.15 each = ~$75/month in API costs

### Security
- No stored data: files exist only in memory during processing
- CORS: not needed since frontend and backend are the same origin
- File validation: check file extension and size on upload. Reject anything not PDF/CSV/TSV/XLSX
- Max file size: 20MB, enforced server-side
- Rate limiting: prevents API cost abuse
- No secrets exposed to the client
- Set appropriate Content-Security-Policy headers

## System Prompt

This is the core intellectual property of the tool. Iterate on it based on real analysis quality.

Store this in `prompts/analysis_system_prompt.txt` so it can be edited without changing code.

```
You are Cloud Carbon Advisor, an expert in cloud infrastructure sustainability.
You analyze cloud provider bills and produce specific, actionable recommendations
for reducing carbon emissions.

## Your Task
Analyze the cloud bill data provided below. Extract the key usage information
(services, instance types, regions, usage volumes, costs) and produce a carbon
impact assessment with prioritized recommendations.

## Reference Data
The following JSON contains current carbon intensity data by cloud region and
energy efficiency data by instance family. Use this as your primary reference
for recommendations.

<carbon_reference_data>
{reference_data}
</carbon_reference_data>

## Analysis Instructions

1. **Extract and summarize** the bill contents: which provider(s), which regions,
   which services, which instance types, approximate monthly spend, and usage
   patterns you can identify.

2. **Estimate carbon footprint** using the reference data. Be transparent about
   what is estimated vs. known. Use the formula:
   Carbon = Energy (kWh) × Grid Carbon Intensity (gCO2/kWh) × PUE
   Where energy is derived from instance type power draw × usage hours.
   Express the total in kg CO2e/month and provide a relatable comparison
   (e.g., "equivalent to X miles driven" or "X trees needed to offset annually").

3. **Produce prioritized recommendations** in these categories, ordered by
   estimated carbon reduction impact (largest first):

   **Region Migration**: Identify workloads that appear non-latency-sensitive
   (batch jobs, dev/test, CI/CD, analytics, backups, data warehousing) and
   recommend specific lower-carbon regions. Include the estimated carbon
   reduction AND any cost delta (increase or decrease). Name the specific
   source and destination regions.

   **Instance Optimization**: Recommend ARM-based alternatives (AWS Graviton,
   Azure Ampere, GCP Tau T2A) where applicable. These typically use 40-60%
   less energy for comparable workloads. Name the specific current and
   recommended instance types.

   **Right-sizing**: If usage patterns suggest over-provisioning (e.g., large
   instance types with low implied utilization based on cost patterns),
   recommend specific downsizing. Note: you are working from billing data,
   not utilization metrics, so be appropriately cautious and flag that
   utilization monitoring would give more precise recommendations.

   **Idle Resource Cleanup**: Flag any line items that suggest unused or
   underutilized resources (detached storage volumes, idle load balancers,
   minimal-traffic services with fixed costs).

   **Workload Scheduling**: For batch-style workloads, recommend time-shifting
   to periods of lower grid carbon intensity where the reference data supports
   this (some grids are significantly cleaner at night or on weekends).

4. **For each recommendation**, provide:
   - What to change (specific and concrete)
   - Estimated monthly carbon reduction (kg CO2e)
   - Estimated monthly cost impact (savings or increase, in USD)
   - Implementation effort: "Quick win" (< 1 hour), "Moderate" (1-5 hours),
     or "Significant" (requires architecture changes)
   - Any risks or caveats

5. **Summary section** at the end with:
   - Total estimated current monthly carbon footprint
   - Total estimated reduction if all recommendations implemented
   - Percentage reduction
   - Top 3 "do this first" actions

## Output Format
Use clean, readable markdown. Use tables for comparisons where appropriate.
Use headers to organize sections. Bold the key numbers. Be direct and
specific — avoid vague advice like "consider using more efficient instances."
Instead say "Migrate your 3x m5.2xlarge instances in us-east-1 to m7g.2xlarge
(Graviton) in us-west-2 (Oregon), reducing carbon by approximately X kg
CO2e/month."

## Tone
Professional but approachable. Like a knowledgeable colleague who has done
this analysis many times. Do not hedge excessively — make clear recommendations
while noting where estimates are uncertain. No marketing language, no
greenwashing, no guilt-tripping. Just useful, honest analysis.

## Important Caveats to Include
- Note that all carbon estimates are approximate and based on publicly
  available data about grid carbon intensity and typical hardware power draw
- Note that billing data alone cannot determine actual CPU/memory utilization —
  recommendations based on right-sizing should be validated with monitoring data
- Include a brief note about methodology: carbon intensity sourced from
  Electricity Maps, energy estimation based on SPECpower database and
  provider documentation
```

## Carbon Reference Data

### File: `data/carbon-reference.json`

This file is the sole source of truth for carbon intensity and instance energy data. Updated weekly by GitHub Actions and committed to the repo. The backend loads it into memory.

### Schema

```json
{
  "last_updated": "2026-04-01T00:00:00Z",
  "data_sources": {
    "carbon_intensity": "Electricity Maps (https://app.electricitymaps.com)",
    "instance_energy": "SPECpower database + cloud provider documentation",
    "pue": "Cloud provider sustainability reports"
  },
  "providers": {
    "aws": {
      "pue": 1.135,
      "regions": {
        "us-east-1": {
          "name": "N. Virginia",
          "grid_carbon_intensity_gco2_kwh": 383.2,
          "renewable_percentage": 35,
          "notes": "One of the highest-carbon AWS regions due to Virginia grid mix"
        },
        "us-west-2": {
          "name": "Oregon",
          "grid_carbon_intensity_gco2_kwh": 78.4,
          "renewable_percentage": 85,
          "notes": "Predominantly hydroelectric, one of the lowest-carbon AWS regions"
        }
      }
    },
    "azure": {
      "pue": 1.185,
      "regions": {}
    },
    "gcp": {
      "pue": 1.10,
      "regions": {}
    }
  },
  "instance_families": {
    "aws": {
      "m5": {
        "architecture": "x86 (Intel Xeon Platinum)",
        "typical_tdp_watts": 150,
        "arm_equivalent": "m7g",
        "energy_savings_with_arm": "40-50%"
      },
      "m7g": {
        "architecture": "ARM (Graviton3)",
        "typical_tdp_watts": 85,
        "arm_equivalent": null,
        "notes": "ARM-based, significantly lower power draw"
      }
    }
  }
}
```

**NOTE:** This is a skeleton. For the initial build, populate it with the top 20-30 regions across all three providers and the top 30 instance families by popularity. This covers 90%+ of real-world bills. The automated weekly update job can be built after launch.

### Weekly Update Job (GitHub Actions)

```yaml
# .github/workflows/update-carbon-data.yml
name: Update Carbon Reference Data
on:
  schedule:
    - cron: '0 6 * * 1'  # Every Monday at 6am UTC
  workflow_dispatch:  # Allow manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install requests
      - run: python scripts/update_carbon_data.py
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: update carbon reference data [automated]"
          file_pattern: data/carbon-reference.json
```

The `update_carbon_data.py` script should:
1. Pull latest grid carbon intensity per region from Electricity Maps free API (or fall back to a curated static dataset if the API is unavailable)
2. Pull latest instance family data from cloud provider pricing APIs to keep the instance catalog current
3. Validate the output JSON against the schema
4. Write to `data/carbon-reference.json`

**For the initial build, manually curate the reference data JSON. The automated update job is a Phase 4 task. Do not let it block launch.**

## Project Structure

```
cloud-carbon-advisor/
├── README.md
├── LICENSE (MIT)
├── .github/
│   └── workflows/
│       └── update-carbon-data.yml
├── main.py                          # FastAPI app entry point
├── config.py                        # Environment variables and settings
├── requirements.txt                 # Python dependencies (keep this small)
├── Dockerfile                       # For Railway deployment
├── railway.toml                     # Railway config (optional)
├── services/
│   ├── file_processor.py            # PDF/CSV/XLSX text extraction
│   ├── llm_service.py               # Claude API interaction + streaming
│   └── reference_data.py            # Load and cache carbon-reference.json
├── rate_limiter.py                  # Simple in-memory rate limiter
├── prompts/
│   └── analysis_system_prompt.txt   # The system prompt (editable without code changes)
├── data/
│   └── carbon-reference.json        # Carbon intensity reference data
├── templates/
│   ├── base.html                    # Base template (head, scripts, footer)
│   ├── index.html                   # Main page with upload form
│   ├── sample.html                  # Pre-generated sample analysis
│   └── partials/
│       ├── results.html             # Results container (swapped in by HTMX)
│       ├── processing.html          # Processing indicator
│       └── error.html               # Error display
├── static/
│   ├── style.css                    # Any custom CSS beyond Tailwind utilities
│   ├── favicon.svg                  # Simple leaf or cloud icon
│   └── og-image.png                 # Social sharing image
└── scripts/
    └── update_carbon_data.py        # Weekly data update script
```

### Dependencies (requirements.txt)

```
fastapi>=0.115.0
uvicorn>=0.34.0
python-multipart>=0.0.18
jinja2>=3.1.4
anthropic>=0.42.0
pdfplumber>=0.11.0
openpyxl>=3.1.5
pandas>=2.2.0
markdown>=3.7
```

That's 9 dependencies. All stable, well-maintained libraries. No JavaScript dependencies.

## Deployment

### Railway Setup

Single service, deployed from the GitHub repo.

**Railway configuration:**
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment variables:
  - `ANTHROPIC_API_KEY` — Claude API key
  - `CONTACT_URL` — Link for the consulting CTA (e.g., LinkedIn profile or email)
  - `BMAC_URL` — Buy Me a Coffee / Ko-fi link
  - `GITHUB_URL` — Repo link
  - `MAX_FILE_SIZE_MB` — Default 20
  - `RATE_LIMIT_PER_HOUR` — Default 10

**Domain:** Configure in Railway's settings. Either a custom domain (subdomain of caseymargell.com or a standalone domain) or use the free Railway-provided URL for initial testing.

**Dockerfile (optional but recommended for consistent builds):**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### DNS / Domain Options

Option A (recommended): `carbon.caseymargell.com` — subdomain of personal site
Option B: Standalone domain like `cloudcarboncheck.com`

Either way, point DNS to Railway. Railway handles TLS automatically.

## Development Priorities / Build Order

Each phase should be independently deployable and testable.

### Phase 1: Backend Core (Day 1-2)
1. FastAPI app skeleton with health endpoint and static file serving
2. Jinja2 template setup with base template (HTMX + Tailwind CDN links in head)
3. File upload endpoint that accepts PDF/CSV and extracts text via pdfplumber/pandas
4. System prompt loaded from text file, assembled with hardcoded reference data
5. Claude API integration with streaming
6. SSE streaming — convert markdown chunks to HTML server-side, send as SSE events
7. Simple rate limiter
8. Test with a sample AWS bill

### Phase 2: Frontend Templates (Day 2-3)
1. Index page with upload form and drag-and-drop zone
2. HTMX wiring: form submission via AJAX, SSE consumption for streaming results
3. Processing indicator (CSS animation, no JS)
4. Results rendering (streamed HTML appended to results div)
5. "Start over" and "Download as PDF" (window.print with print stylesheet)
6. Footer with tip jar, consulting CTA, GitHub link
7. Basic responsive layout with Tailwind utilities
8. Print stylesheet for clean PDF output

### Phase 3: Polish and Deploy (Day 3-4)
1. Error handling rendered in the UI (bad file types, rate limits, API failures)
2. Sample analysis page at /sample
3. Populate carbon-reference.json with real data for top 20-30 regions and 30 instance families
4. README with description and screenshots
5. Deploy to Railway
6. Configure domain
7. End-to-end test with real bills from each provider

### Phase 4: Reference Data Automation (Follow-up week)
1. Write `update_carbon_data.py` with real data sources
2. Set up GitHub Actions cron job
3. Verify automated commits work

### Phase 5: Iteration Based on Usage (Ongoing)
1. Improve system prompt based on real analysis quality
2. Add support for additional bill formats as users report issues
3. Expand reference data coverage
4. Optional: simple anonymous feedback mechanism ("Was this helpful? Yes/No") that logs to stdout

## Testing Strategy

- **Unit tests**: Test file processing (PDF text extraction, CSV parsing, summarization) with sample files
- **Integration test**: Full upload → Claude API → SSE stream flow. Can use a mock Claude response for CI.
- **Sample bills**: Create 3-4 realistic synthetic bills (AWS CUR CSV, AWS PDF, GCP billing export, Azure cost export) for testing. These should be committed to the repo in a `tests/fixtures/` directory.
- **Manual end-to-end**: Upload each sample bill through the UI and verify the full flow works. This is sufficient for v1 given the application's simplicity.

## What This Is NOT

To keep scope contained, this is explicitly NOT:
- An account-connected monitoring tool (no AWS/Azure/GCP API keys from users)
- A real-time dashboard (one-shot analysis only)
- A multi-tenant SaaS (no users, no accounts, no auth)
- A carbon offset marketplace
- A compliance reporting tool (no CSRD/CDP/GRI templates)
- A FinOps tool (carbon is the focus, cost context is secondary)
- A JavaScript application (it is a Python application that serves HTML)

## Open Questions for Development

1. **PDF vision fallback**: For image-heavy PDFs where text extraction fails, sending the PDF as base64 to Claude's vision capability works but costs more. **Recommendation**: Try text extraction first. If < 200 chars extracted, fall back to vision automatically. Log occurrences to track frequency.

2. **Model selection**: Start with Claude Sonnet 4. If analysis quality on complex multi-service bills is insufficient, consider Opus for those cases. But start with Sonnet across the board.

3. **Markdown-to-HTML streaming**: The backend needs to convert markdown to HTML incrementally as the stream arrives. The Python `markdown` library works on complete text. **Recommendation**: Accumulate the full streamed response, converting to HTML periodically (e.g., every 500 chars or on paragraph boundaries) and sending the delta as SSE events. Alternatively, send raw markdown via SSE and use a tiny client-side markdown renderer (marked.js is 8KB gzipped, loaded from CDN — this is acceptable even with the "no framework" philosophy since it is a single utility script, not a framework). **Let the developer decide based on what is simpler to implement.**

4. **Sample analysis**: Generate one high-quality analysis from a synthetic AWS bill with diverse services and regions. Save the rendered HTML as the sample page. This should be done during Phase 3 after the analysis pipeline is working.
