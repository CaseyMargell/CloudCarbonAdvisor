---
tags: [fastapi, starlette, jinja2, templates]
category: gotcha
module: frontend
symptoms: ["TypeError: unhashable type: 'dict'", "TemplateResponse context error"]
---

# FastAPI TemplateResponse API Change

## Problem
Newer versions of Starlette/FastAPI changed the `TemplateResponse` constructor. The old positional form:

```python
templates.TemplateResponse("index.html", {"request": request, "key": "value"})
```

Throws `TypeError: unhashable type: 'dict'` because it tries to use the context dict as a dict key.

## Solution
Use the keyword argument form:

```python
templates.TemplateResponse(
    request=request,
    name="index.html",
    context={"key": "value"},
)
```

Note: `request` is passed separately, not inside `context`.

## When This Applies
Any FastAPI project using Jinja2 templates with `fastapi >= 0.115` / `starlette >= 1.0`.
