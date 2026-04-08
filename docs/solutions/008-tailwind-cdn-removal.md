---
tags: [frontend, performance, css, tailwind]
category: frontend
module: static
symptoms: ["300KB JS loaded on every page", "slow first paint", "CDN dependency"]
---

# Removing Tailwind CDN Without a Build Step

## Problem
The Tailwind CDN script (~300KB JS) was loaded on every page but no Tailwind utility classes were actually used — a design-iterator agent had already rewritten everything to semantic CSS in style.css.

## Solution
Just remove the `<script src="https://cdn.tailwindcss.com">` tag. No build step needed because there's nothing to compile.

## How We Got Here
1. Initial build used Tailwind CDN per the spec
2. A design-iterator agent rewrote all templates to use semantic class names (`.hero-headline`, `.drop-zone`, etc.) with custom CSS in style.css
3. The Tailwind CDN script remained but was dead weight — no utility classes in any template
4. Verified by grepping all templates: zero Tailwind utility classes found
5. Removed the script tag and cdn.tailwindcss.com from CSP allowlist

## Key Insight
If you use a design agent that rewrites your markup, check whether your CSS framework is still actually being used before keeping it. A 300KB runtime compiler doing nothing is easy to miss.
