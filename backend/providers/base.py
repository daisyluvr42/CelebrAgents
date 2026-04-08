from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class LLMProvider(ABC):
    @abstractmethod
    async def stream_chat(
        self, system_prompt: str, messages: list[dict], model: str | None = None
    ) -> AsyncIterator[str]:
        """Yield text chunks from the LLM."""
        ...
