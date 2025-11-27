"""
Retrieval-Augmented Generation plugin using Azure AI Search.
Provides grounded product information and citation metadata.
"""

from __future__ import annotations

from typing import Dict, Any, List

from azure.search.documents.aio import SearchClient
from azure.identity.aio import DefaultAzureCredential

from plugins.base_plugin import BasePlugin


class RAGPlugin(BasePlugin):
    """
    Retrieval-Augmented Generation plugin for grounded product lookup.

    Exposes two functions:
    - retrieve_product_info(query)
    - extract_citations(items)
    """

    def __init__(self, config: dict):
        self.config = config

        # Credentials (async)
        self.credential = DefaultAzureCredential()

        # Azure AI Search client
        self.search_client = SearchClient(
            endpoint=config["azure_search"]["endpoint"],
            index_name=config["azure_search"]["index_name"],
            credential=self.credential
        )

    # ---------------------------------------------------------------------
    # REQUIRED BY BasePlugin
    # ---------------------------------------------------------------------
    def get_functions(self) -> Dict[str, Any]:
        return {
            "retrieve_product_info": self.retrieve_product_info,
            "extract_citations": self.extract_citations,
        }

    # ---------------------------------------------------------------------
    # SEARCH FUNCTION (async)
    # ---------------------------------------------------------------------
    async def retrieve_product_info(self, query: str) -> Dict[str, Any]:
        """
        Retrieve grounded product information from Azure AI Search.

        Returns structured results:
        {
            "items": [
                {
                    "content": "...",
                    "title": "...",
                    "citation": "[Source: ..., Page X]",
                    "score": float
                }
            ]
        }
        """

        try:
            results = await self.search_client.search(
                search_text=query,
                top=5,
                select=["content", "title", "source_file", "page_number"],
                query_type="semantic",
                semantic_configuration_name="default"
            )
        except Exception as e:
            return {
                "items": [],
                "error": f"Search error: {str(e)}",
                "query": query
            }

        retrieved_items: List[Dict[str, Any]] = []

        async for result in results:
            citation = f"[Source: {result['title']}, Page {result.get('page_number', '?')}]"

            retrieved_items.append({
                "content": result.get("content", ""),
                "title": result.get("title", "Unknown Source"),
                "citation": citation,
                "score": result.get("@search.score", 0.0)
            })

        return {
            "items": retrieved_items,
            "query": query
        }

    # ---------------------------------------------------------------------
    # CITATION PROCESSOR
    # ---------------------------------------------------------------------
    async def extract_citations(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Takes the items returned by retrieve_product_info() and returns
        a clean list of citation strings.

        Returns:
        {
            "citations": ["[Source: manual, Page 3]", ...]
        }
        """
        citations = [
            item.get("citation", "")
            for item in items
            if isinstance(item, dict) and "citation" in item
        ]

        return {"citations": citations}
