---
tags: [fastapi, sse, streaming, file-upload, htmx]
category: architecture
module: api
symptoms: ["HTMX SSE extension not working with POST", "EventSource GET-only limitation"]
---

# SSE Streaming with File Upload (POST)

## Problem
The spec called for HTMX's SSE extension (`sse-connect`) to consume streaming responses from a file upload endpoint. This doesn't work because `EventSource` (the browser API underlying HTMX SSE) only supports GET requests. You cannot POST a file and receive an SSE stream via EventSource.

## Solution
Use `fetch()` with `ReadableStream` to POST the file as FormData and consume the `text/event-stream` response directly in ~30 lines of vanilla JS.

```javascript
const response = await fetch('/api/analyze', { method: 'POST', body: formData });
const reader = response.body.getReader();
// Parse SSE events from the stream manually
```

## Key Details
- This makes HTMX unnecessary — once fetch() handles both upload and streaming, HTMX has no role
- SSE events must include `Cache-Control: no-cache` and `X-Accel-Buffering: no` headers or reverse proxies (Railway, nginx) will buffer the stream
- The `Connection: keep-alive` header is also needed
- FastAPI's `StreamingResponse` with `media_type="text/event-stream"` works well for this

## Gotchas
- Don't forget proxy headers — streaming works locally but breaks in production without them
- `marked.js` for client-side markdown rendering avoids the pain of incremental server-side markdown→HTML conversion (partial tables, unclosed code blocks)
