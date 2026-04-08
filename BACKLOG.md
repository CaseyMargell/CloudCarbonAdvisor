# Cloud Carbon Advisor -- Backlog

## Active

(None currently)

## Up Next

- [ ] End-to-end test with Azure bills
- [ ] XLSX support (add openpyxl when a user requests it)
- [ ] PDF vision fallback for scanned/image-heavy PDFs
- [ ] Phase 4: Reference data automation (GitHub Actions cron)
- [ ] Expand reference data: IBM Cloud, Hetzner, OVHcloud (feasible -- published PUE + known grid zones)
- [ ] Anonymous feedback mechanism ("Was this helpful? Yes/No")

## Known Defects

(None reported)

## Ideas (not yet planned)

- Dark mode
- Structured JSON logging (when traffic justifies it)
- Concurrency semaphore (when traffic justifies it)

## Done (recent)

- [x] PR #1: Cloud Carbon Advisor MVP
- [x] PR #2: Code review fixes
- [x] Sample analysis page from real AWS bill
- [x] FAQ page with data sources, methodology, privacy
- [x] Two-pass analysis (summary + on-demand details) -- ~50% token savings
- [x] Progressive section-by-section streaming with earth spinner
- [x] Unicode character sanitization (cleanText)
- [x] Impact CTA (tree planting via chatGPTree + buy me a coffee)
- [x] PII protection in system prompt
- [x] Non-bill file detection (hides action buttons, saves tokens)
- [x] ROOT_PATH support for reverse proxy deployment
- [x] Live deployment on Railway behind caseymargell.com proxy
- [x] Extracted inline JS to static/app.js, removed CSP unsafe-inline
- [x] Removed Tailwind CDN (all styles already in style.css, -300KB)
- [x] OG image + meta tags for social sharing (LinkedIn, X)
- [x] Favicon (teal globe SVG)
- [x] Footer: plant trees link, FAQ link, mailto contact
- [x] Carbon data date displayed on homepage
- [x] Carbon reference data refresh (April 8) -- UK, France, Germany updated
- [x] Provider support scoped to AWS/Azure/GCP (verified data only)
