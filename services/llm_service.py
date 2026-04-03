import json
import logging
from collections.abc import AsyncGenerator
from pathlib import Path

import anthropic
from fastapi import Request

import config

logger = logging.getLogger("cloud-carbon-advisor")

_system_prompt: str | None = None


def _get_system_prompt() -> str:
    global _system_prompt
    if _system_prompt is None:
        prompt_path = Path(__file__).parent.parent / "prompts" / "analysis_system_prompt.txt"
        _system_prompt = prompt_path.read_text()
    return _system_prompt


async def analyze_bill(
    bill_text: str,
    reference_data: dict,
    request: Request,
) -> AsyncGenerator[str, None]:
    """Stream analysis of a cloud bill using Claude API.

    Yields markdown text chunks. Checks for client disconnect between chunks
    and cancels the API call if the client has gone away.
    """
    system_prompt = _get_system_prompt()

    # Inject reference data into prompt
    ref_json = json.dumps(reference_data, indent=2) if reference_data else "{}"
    system_prompt = system_prompt.replace("{reference_data}", ref_json)

    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

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
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info("Client disconnected, cancelling stream")
                    break

                yield text

            # Get final token counts from the stream
            message = await stream.get_final_message()
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens

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
