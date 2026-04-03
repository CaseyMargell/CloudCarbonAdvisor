# Cloud Carbon Advisor

Upload your cloud bill. Get carbon reduction recommendations.

A web application that analyzes cloud provider bills (AWS, Azure, GCP) and produces actionable recommendations for reducing your infrastructure's carbon footprint. No accounts, no auth, no stored data.

## How It Works

1. Upload a PDF or CSV cloud bill
2. AI analyzes your services, regions, and instance types against carbon intensity data
3. Get prioritized recommendations with estimated carbon and cost impact

## Quick Start

```bash
# Clone the repo
git clone https://github.com/IndiseaCasey/cloud-carbon-advisor.git
cd cloud-carbon-advisor

# Create .env from example
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Install dependencies
pip install -r requirements.txt

# Run
uvicorn main:app --reload
```

Open http://localhost:8000

## Tech Stack

- **Python 3.12** + **FastAPI** — backend and HTML serving
- **Jinja2** — server-side templates
- **Tailwind CSS** (CDN) — styling
- **marked.js** (CDN) — client-side markdown rendering
- **Anthropic Claude API** — bill analysis with streaming
- **pdfplumber** — PDF text extraction

No JavaScript framework. No build step. No node_modules.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | — | Claude API key |
| `MAX_FILE_SIZE_MB` | No | 20 | Max upload size |
| `RATE_LIMIT_PER_HOUR` | No | 10 | Analyses per IP per hour |
| `CONTACT_URL` | No | — | Consulting CTA link |
| `BMAC_URL` | No | — | Buy Me a Coffee link |
| `GITHUB_URL` | No | — | Repository link |

## Deploy to Railway

```bash
# Using Railway CLI
railway up
```

Or connect the GitHub repo in Railway's dashboard. Set environment variables in Railway's settings.

## Running Tests

```bash
pip install pytest httpx pytest-asyncio
python -m pytest tests/ -v
```

## Project Structure

```
main.py                    FastAPI app, routes, middleware
config.py                  Environment variable config
rate_limiter.py            Fixed-window rate limiter
services/
  file_processor.py        PDF/CSV text extraction
  llm_service.py           Claude API streaming
prompts/
  analysis_system_prompt.txt
data/
  carbon-reference.json    Carbon intensity by region + instance energy data
templates/
  index.html               Single-page app
  sample.html              Pre-generated sample analysis
static/
  style.css                Custom styles
tests/
  test_file_processor.py
  test_rate_limiter.py
  test_api.py
```

## Carbon Reference Data

The `data/carbon-reference.json` file contains carbon intensity data for 47 cloud regions and energy profiles for 31 instance families across AWS, Azure, and GCP.

Sources: EPA eGRID, Electricity Maps, Cloud Carbon Footprint project, SPECpower database, cloud provider sustainability reports.

## Privacy

- Files are processed in memory and immediately discarded
- No database, no cookies, no tracking
- Bill content is sent to Claude API for analysis — Anthropic does not use API data for training

## License

MIT
