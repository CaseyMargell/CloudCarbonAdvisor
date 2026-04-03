import json
import logging
from collections.abc import AsyncGenerator
from pathlib import Path

import anthropic
from fastapi import Request

import config

logger = logging.getLogger("cloud-carbon-advisor")

_system_prompt_template: str | None = None
_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def _get_system_prompt_template() -> str:
    global _system_prompt_template
    if _system_prompt_template is None:
        prompt_path = Path(__file__).parent.parent / "prompts" / "analysis_system_prompt.txt"
        _system_prompt_template = prompt_path.read_text()
    return _system_prompt_template


def _build_system_prompt(reference_data: dict) -> str:
    """Build system prompt with reference data injected. Returns a new string each time."""
    template = _get_system_prompt_template()
    ref_json = json.dumps(reference_data, indent=2) if reference_data else "{}"
    return template.replace("{reference_data}", ref_json)


async def analyze_bill(
    bill_text: str,
    reference_data: dict,
    request: Request,
) -> AsyncGenerator[str, None]:
    """Stream analysis of a cloud bill using Claude API.

    Yields markdown text chunks. Checks for client disconnect between chunks
    and cancels the API call if the client has gone away.
    """
    system_prompt = _build_system_prompt(reference_data)
    client = _get_client()

    user_message = f"Here is the cloud bill to analyze:\n\n{bill_text}"

    input_tokens = 0
    output_tokens = 0

    try:
        async with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            async for text in stream.text_stream:
                if await request.is_disconnected():
                    logger.info("Client disconnected, cancelling stream")
                    break

                yield text

            # Only get final message if stream completed normally (not cancelled)
            if not await request.is_disconnected():
                try:
                    message = await stream.get_final_message()
                    input_tokens = message.usage.input_tokens
                    output_tokens = message.usage.output_tokens
                except Exception:
                    pass  # Stream was cancelled, token counts unavailable

    except anthropic.APIStatusError as e:
        logger.error("Claude API error: %s %s", e.status_code, e.message)
        raise
    except anthropic.APIConnectionError as e:
        logger.error("Claude API connection error: %s", e)
        raise
    finally:
        if input_tokens or output_tokens:
            logger.info(
                "Token usage: input=%d output=%d estimated_cost=$%.4f",
                input_tokens,
                output_tokens,
                (input_tokens * 3.0 / 1_000_000) + (output_tokens * 15.0 / 1_000_000),
            )
