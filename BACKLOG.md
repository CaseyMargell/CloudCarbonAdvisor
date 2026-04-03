# Cloud Carbon Advisor — Backlog

## Active

(None currently)

## Recently Merged (needs follow-up)

- [x] MVP implementation (PR #1) — needs manual testing with real bills

## Up Next

- [ ] End-to-end test with Casey's real AWS bills (output/)
- [ ] Generate sample analysis page content via pipeline
- [ ] Populate PRODUCT.md with actual product context
- [ ] XLSX support (add openpyxl when a user requests it)
- [ ] PDF vision fallback for scanned/image-heavy PDFs
- [ ] Phase 4: Reference data automation (GitHub Actions cron)

## Known Defects

(None yet — needs manual testing)

## Ideas (not yet planned)

- Anonymous feedback mechanism ("Was this helpful? Yes/No")
- OG image and favicon for social sharing
- Structured JSON logging (when traffic justifies it)
- Concurrency semaphore (when traffic justifies it)
- Dark mode
- Azure/GCP bill-specific test fixtures

## Done (recent)

- [x] PR #1: Cloud Carbon Advisor MVP — FastAPI backend, SSE streaming, frontend, 34 tests, 47 regions, 31 instance families
