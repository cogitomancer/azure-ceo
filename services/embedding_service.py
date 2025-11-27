from __future__ import annotations
from typing import List
from openai import AsyncOpenAI


class EmbeddingService:
    """
    Wrapper to generate embeddings using Azure OpenAI or OpenAI.
    """

    def __init__(self, client: AsyncOpenAI, model: str):
        self.client = client
        self.model = model

    async def embed_text(self, text: str) -> List[float]:
        """
        Returns a dense embedding vector for the given text.
        """
        resp = await self.client.embeddings.create(
            input=text,
            model=self.model,
        )
        return resp.data[0].embedding
