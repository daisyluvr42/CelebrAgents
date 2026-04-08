from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from .. import config
from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

    async def stream_chat(
        self, system_prompt: str, messages: list[dict], model: str | None = None
    ) -> AsyncIterator[str]:
        model = model or config.OPENAI_MODEL
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        stream = await self.client.chat.completions.create(
            model=model,
            messages=full_messages,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
