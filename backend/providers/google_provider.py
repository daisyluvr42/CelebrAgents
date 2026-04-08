from collections.abc import AsyncIterator

from google import genai
from google.genai import types

from .. import config
from .base import LLMProvider


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

        response = self.client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
