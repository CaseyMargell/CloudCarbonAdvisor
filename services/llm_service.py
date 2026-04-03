import json
import logging
from collections.abc import AsyncGenerator
from pathlib import Path

import anthropic
from fastapi import Request

import config

logger = logging.getLogger("cloud-carbon-advisor")

_prompts: dict[str, str] = {}
_client: anthropic.AsyncAnthropic | None = None

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def _get_prompt_template(name: str) -> str:
    if name not in _prompts:
        _prompts[name] = (PROMPTS_DIR / name).read_text()
    return _prompts[name]


def _build_prompt(template_name: str, reference_data: dict) -> str:
    """Build a system prompt with reference data and config values injected."""
    template = _get_prompt_template(template_name)
    ref_json = json.dumps(reference_data, indent=2) if reference_data else "{}"
    prompt = template.replace("{reference_data}", ref_json)
    prompt = prompt.replace("{tree_donation_url}", config.TREE_DONATION_URL)
    prompt = prompt.replace("{bmac_url}", config.BMAC_URL)
    return prompt


async def _stream_claude(
    system_prompt: str,
    user_message: str,
    request: Request,
    max_tokens: int = 4096,
    label: str = "analysis",
) -> AsyncGenerator[str, None]:
    """Stream a Claude response. Handles disconnect detection and token logging."""
    client = _get_client()
    input_tokens = 0
    output_tokens = 0

    try:
        async with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            async for text in stream.text_stream:
                if await request.is_disconnected():
                    logger.info("Client disconnected during %s, cancelling", label)
                    break
                yield text

            if not await request.is_disconnected():
                try:
                    message = await stream.get_final_message()
                    input_tokens = message.usage.input_tokens
                    output_tokens = message.usage.output_tokens
                except Exception:
                    pass

    except anthropic.APIStatusError as e:
        logger.error("Claude API error (%s): %s %s", label, e.status_code, e.message)
        raise
    except anthropic.APIConnectionError as e:
        logger.error("Claude API connection error (%s): %s", label, e)
        raise
    finally:
        if input_tokens or output_tokens:
            logger.info(
                "%s token usage: input=%d output=%d estimated_cost=$%.4f",
                label, input_tokens, output_tokens,
                (input_tokens * 3.0 / 1_000_000) + (output_tokens * 15.0 / 1_000_000),
            )


async def analyze_bill(
    bill_text: str,
    reference_data: dict,
    request: Request,
) -> AsyncGenerator[str, None]:
    """Stream concise bill analysis (summary + top actions + roadmap)."""
    system_prompt = _build_prompt("analysis_system_prompt.txt", reference_data)
    user_message = f"Here is the cloud bill to analyze:\n\n{bill_text}"

    async for chunk in _stream_claude(system_prompt, user_message, request,
                                       max_tokens=2048, label="summary"):
        yield chunk


async def analyze_bill_details(
    bill_text: str,
    reference_data: dict,
    request: Request,
) -> AsyncGenerator[str, None]:
    """Stream detailed recommendation breakdowns (expandable sections)."""
    system_prompt = _build_prompt("details_system_prompt.txt", reference_data)
    user_message = f"Here is the cloud bill to produce detailed recommendations for:\n\n{bill_text}"

    async for chunk in _stream_claude(system_prompt, user_message, request,
                                       max_tokens=4096, label="details"):
        yield chunk
