# Cloud Carbon Advisor -- Backlog

## Active

(None currently)

## Up Next

- [ ] End-to-end test with Azure bills (Casey has AWS only so far)
- [ ] XLSX support (add openpyxl when a user requests it)
- [ ] PDF vision fallback for scanned/image-heavy PDFs
- [ ] Phase 4: Reference data automation (GitHub Actions cron)
- [ ] Expand reference data: IBM Cloud, Hetzner, OVHcloud (feasible -- published PUE + known grid zones)
- [ ] Anonymous feedback mechanism ("Was this helpful? Yes/No")

## Known Defects

(None reported)

## Ideas (not yet planned)

- OG image and favicon for social sharing
- Structured JSON logging (when traffic justifies it)
- Concurrency semaphore (when traffic justifies it)
- Dark mode
- Move inline JS to static file + remove CSP unsafe-inline
- Tailwind CDN -> static CSS build (performance)

## Done (recent)

- [x] PR #1: Cloud Carbon Advisor MVP
- [x] PR #2: Code review fixes (SSE deltas, DOMPurify, disconnect guard, HSTS, Dockerfile)
- [x] Sample analysis page from real AWS bill
- [x] FAQ page with data sources, methodology, privacy
- [x] Two-pass analysis (summary + on-demand details) -- ~50% token savings
- [x] Progressive section-by-section streaming with earth icon progress
- [x] Unicode character sanitization
- [x] Impact CTA (tree planting via chatGPTree + buy me a coffee)
- [x] PII protection in system prompt
- [x] ROOT_PATH support for reverse proxy deployment
- [x] Live deployment on Railway at /cloud-carbon-advisor/
