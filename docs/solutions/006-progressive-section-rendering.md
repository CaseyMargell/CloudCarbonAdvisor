---
tags: [frontend, streaming, sse, markdown, rendering]
category: frontend
module: templates
symptoms: ["page jumping during streaming", "markdown garbled across chunks", "full DOM rebuild on every chunk"]
---

# Progressive Section-by-Section Streaming Render

## Problem
Naively re-rendering the full accumulated markdown on every SSE chunk causes:
1. Page jumping as the DOM is rebuilt
2. Markdown broken across chunk boundaries (e.g., `**bol` + `d**` = garbled)
3. O(n^2) rendering cost

## Solution
Scan the accumulated text for `## ` header boundaries and render each section into its own stable DOM element. Only the current in-progress section re-renders.

```javascript
// Detect section headers in the full accumulated text
var headerPattern = /\n(#{1,2}\s+\S[^\n]*)/g;
// For each new header, finalize the previous section and create a new DOM element
```

Key insight: NEVER split `data.content` by `\n` and reassemble -- this breaks markdown formatting that spans chunk boundaries. Always work on the full accumulated string.

## Progress Indicators
Each section shows a pulsing earth icon with a friendly label (e.g., "Summarizing your bill...") mapped from the header text via a lookup table. The indicator is removed when the next section starts.

## Unicode Cleanup
LLMs output Unicode characters (em dashes, smart quotes, arrows) despite ASCII-only instructions. A `cleanText()` function strips these to ASCII equivalents before rendering to prevent garbled characters like `a-TM`.
