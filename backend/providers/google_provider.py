import asyncio
import logging
from collections.abc import AsyncIterator

from google import genai
from google.genai import types

from .. import config
from .base import LLMProvider

logger = logging.getLogger(__name__)


class GoogleProvider(LLMProvider):
    def __init__(self):
        self.client = genai.Client(api_key=config.GOOGLE_API_KEY)

    async def stream_chat(
        self, system_prompt: str, messages: list[dict], model: str | None = None
    ) -> AsyncIterator[str]:
        model = model or config.GOOGLE_MODEL
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

        logger.info("Google API call: model=%s, system_prompt_len=%d, messages=%d", model, len(system_prompt), len(contents))

        def _sync_stream():
            response = self.client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                ),
            )
            chunks = []
            for chunk in response:
                if chunk.text:
                    chunks.append(chunk.text)
            return chunks

        loop = asyncio.get_event_loop()
        chunks = await loop.run_in_executor(None, _sync_stream)
        for chunk in chunks:
            yield chunk
