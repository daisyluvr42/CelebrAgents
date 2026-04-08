from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic

from .. import config
from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self):
        self.client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

    async def stream_chat(
        self, system_prompt: str, messages: list[dict], model: str | None = None
    ) -> AsyncIterator[str]:
        model = model or config.ANTHROPIC_MODEL
        async with self.client.messages.stream(
            model=model,
            max_tokens=8192,
            system=system_prompt,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text
