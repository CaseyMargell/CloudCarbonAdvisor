---
tags: [llm, claude-api, cost-optimization, streaming]
category: architecture
module: services
symptoms: ["high API costs", "slow analysis", "unnecessary token usage"]
---

# Two-Pass Analysis for Token Cost Optimization

## Problem
Generating a full carbon analysis (summary + detailed recommendations + methodology + CTA) in a single LLM call uses ~4096 tokens of output. Many users only need the summary. Detailed breakdowns, methodology notes, and CTAs are often not read.

## Solution
Split into two passes:

1. **Summary pass** (~2048 max_tokens): Bill Summary, Recommendation Summary table, Top Actions, Implementation Roadmap. Fast, focused, always generated.
2. **Details pass** (~4096 max_tokens, on-demand): Detailed expandable recommendation breakdowns. Only generated when user clicks "Get detailed recommendations" or "Download PDF Report".

Static content (methodology notes, tree planting CTA) is appended as HTML -- never LLM-generated since it's the same every time.

## Key Details
- Bill text is sent to the browser via an SSE `context` event so the details call doesn't require re-uploading
- The `loadDetails()` JS function guards against double-loading with `detailsLoaded`/`detailsLoading` flags
- "Download PDF Report" auto-triggers details generation if not already loaded, then prints
- Estimated savings: ~50% token cost for users who only need the summary
- Both passes use the same `_stream_claude()` helper on the backend
