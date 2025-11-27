from __future__ import annotations
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
from typing import List, Dict, Any


class VectorStore:
    """
    Handles vector storage + retrieval from Azure AI Search.
    """

    def __init__(self, endpoint: str, index: str, api_key: str):
        self.client = SearchClient(
            endpoint=endpoint,
            index_name=index,
            credential=AzureKeyCredential(api_key),
        )

    async def add_document(self, doc_id: str, embedding: List[float], metadata: Dict[str, Any]):
        await self.client.upload_documents([
            {"id": doc_id, "embedding": embedding, **metadata}
        ])

    async def search(self, embedding: List[float], k: int = 5):
        results = self.client.search(
            search_text=None,
            vectors=[{
                "value": embedding,
                "fields": "embedding",
                "k": k
            }],
            select=["id", "title", "body", "metadata"]
        )
        return [x async for x in results]
