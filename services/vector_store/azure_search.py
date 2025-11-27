# services/vector_store/azure_search.py

from typing import Dict, List, Any, Tuple
import os
import httpx


class AzureCognitiveSearchVectorStore:
    """
    Async wrapper for Azure Cognitive Search vector index.
    Supports upsert + vector search.
    """

    def __init__(self) -> None:
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")    # e.g. "https://<service>.search.windows.net"
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")  # e.g. "azure-ceo-content"
        self.api_key = os.getenv("AZURE_SEARCH_API_KEY")

        if not all([self.endpoint, self.index_name, self.api_key]):
            raise RuntimeError("Missing Azure Cognitive Search environment variables.")

        self._client = httpx.AsyncClient(
            base_url=self.endpoint,
            headers={
                "api-key": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=30.0
        )

    async def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]) -> None:
        """
        Upsert a content item with its vector + metadata.
        Matches ACS @search.action mergeOrUpload semantics.
        """
        document = {
            "@search.action": "mergeOrUpload",
            "id": id,
            "vector": vector,
            **metadata
        }

        url = f"/indexes/{self.index_name}/docs/index?api-version=2024-05-01-preview"

        resp = await self._client.post(url, json={"value": [document]})
        resp.raise_for_status()

    async def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, Dict[str, Any], float]]:
        """
        Vector search interface for ACS.
        Returns list of (document_id, metadata, score).
        """
        url = f"/indexes/{self.index_name}/docs/search?api-version=2024-05-01-preview"

        body = {
            "vectorQueries": [
                {
                    "kind": "vector",
                    "vector": query_vector,
                    "k": top_k,
                    "fields": "vector",
                }
            ]
        }

        resp = await self._client.post(url, json=body)
        resp.raise_for_status()
        payload = resp.json()

        results: List[Tuple[str, Dict[str, Any], float]] = []

        for item in payload.get("value", []):
            doc_id = item.get("id")
            score = item.get("@search.score", 0.0)
            metadata = {k: v for k, v in item.items() if not k.startswith("@")}
            results.append((doc_id, metadata, score))

        return results
