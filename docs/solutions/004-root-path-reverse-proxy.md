---
tags: [fastapi, deployment, reverse-proxy, railway]
category: deployment
module: config
symptoms: ["CSS not loading behind proxy", "API calls 404 behind subpath", "links point to wrong path"]
---

# Serving FastAPI Behind a Reverse Proxy at a Subpath

## Problem
When a FastAPI app is served behind a reverse proxy at a subpath (e.g., `/cloud-carbon-advisor/`), all internal URLs (`/static/style.css`, `/api/analyze`, `/sample`) resolve relative to the host root, not the subpath. CSS doesn't load, API calls 404, navigation breaks.

## Solution
Add a `ROOT_PATH` env var (e.g., `/cloud-carbon-advisor`) and prefix all URLs:

- **Templates**: `href="{{ root_path }}/sample"`, `src="{{ root_path }}/static/style.css"`
- **JS fetch**: `fetch(ROOT + '/api/analyze', ...)`  where `var ROOT = '{{ root_path }}';`
- **Config**: `ROOT_PATH = os.getenv("ROOT_PATH", "").rstrip("/")`
- Pass `root_path` via `_base_context()` to all templates

## Key Details
- `ROOT_PATH` defaults to empty string -- app works at domain root with no config
- Strip trailing slash to avoid double slashes (`/cloud-carbon-advisor//static/...`)
- External URLs (CDN scripts, mailto, external links) are unaffected
- FastAPI's built-in `root_path` kwarg does NOT handle static files or template URLs -- you must prefix manually
