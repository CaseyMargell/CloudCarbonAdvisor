---
tags: [deployment, og-image, social-sharing, reverse-proxy]
category: deployment
module: templates
symptoms: ["LinkedIn preview shows no image", "social crawler timeout", "og:image not loading"]
---

# OG Image Behind Reverse Proxy

## Problem
Social crawlers (LinkedIn, X) have short timeouts. When the app is behind a reverse proxy (caseymargell.com -> Railway), the proxy hop + Railway cold start can exceed the crawler's timeout, resulting in "Unable to connect to server" errors.

## Solution
Decouple the OG image URL from the proxy path. Use a separate `OG_BASE_URL` config that points directly at the Railway public URL, bypassing the proxy for crawler requests only.

```html
<meta property="og:image" content="{{ og_base_url }}/static/og-image.png">
```

Where `OG_BASE_URL=https://cloudcarbonadvisor-production.up.railway.app` (no ROOT_PATH prefix, since Railway serves at root).

## Key Details
- `OG_BASE_URL` is separate from `ROOT_PATH` — they serve different purposes
- OG tags are metadata for crawlers, not visible to users — the URL doesn't need to match the user-facing domain
- LinkedIn Post Inspector (`linkedin.com/post-inspector`) shows a `shrink_160` thumbnail that looks blurry — the actual post renders the full-size image
- LinkedIn/X don't support SVG for og:image — must be PNG or JPG
- Recommended size: 1200x630 PNG
