"""
Retrieval-Augmented Generation plugin using Azure AI Search.
Provides grounded product information and citation metadata.

Uses company-specific Azure Search indexes:
- Hudson Street Bakery: hudson-street-products
- Microsoft: microsoft-azure-products

Data indexed from tables/ folder into Azure AI Search.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List

from azure.search.documents.aio import SearchClient
from azure.identity.aio import DefaultAzureCredential

from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class RAGPlugin(BasePlugin):
    """
    Retrieval-Augmented Generation plugin for grounded product lookup.

    Exposes two functions:
    - retrieve_product_info(query)
    - extract_citations(items)
    
    Uses company-specific Azure Search indexes based on COMPANY_ID.
    """

    def __init__(self, config: dict):
        super().__init__(config=config, name="RAGPlugin")
        
        # Get company-specific Azure Search configuration
        self.company_search_config = self._get_company_search_config()
        
        # Credentials (async)
        self.credential = DefaultAzureCredential()

        # Azure AI Search client with company-specific index
        index_name = self.company_search_config.get("index_name", config["azure_search"]["index_name"])
        semantic_config = self.company_search_config.get("semantic_config", "default")
        
        self.search_client = SearchClient(
            endpoint=config["azure_search"]["endpoint"],
            index_name=index_name,
            credential=self.credential
        )
        self.semantic_config = semantic_config
        self.company_name = self.company_search_config.get("company_name", "Unknown")
        
        logger.info(f"RAGPlugin initialized for {self.company_name} using index: {index_name}")

    def _get_company_search_config(self) -> Dict[str, Any]:
        """Get company-specific Azure Search configuration."""
        try:
            from services.company_data_service import CompanyDataService
            service = CompanyDataService()
            search_config = service.get_azure_search_config()
            search_config["company_name"] = service.get_company_info()["name"]
            return search_config
        except Exception as e:
            logger.warning(f"Could not load company search config: {e}")
            return {"index_name": "product-docs", "semantic_config": "default", "company_name": "Unknown"}

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
        
        Use this tool to search for product details, features, pricing, and descriptions.
        Always use this tool when you need factual information about products, services, or company offerings.
        
        Args:
            query: Search query describing what product information you need (e.g., "almond croissant", "best-selling items", "seasonal products")
        
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

        logger.info(f"RAG search for {self.company_name}: {query[:50]}...")
        
        try:
            results = await self.search_client.search(
                search_text=query,
                top=5,
                select=["content", "title", "source_file", "page_number", "product_name", "category"],
                query_type="semantic",
                semantic_configuration_name=self.semantic_config
            )
        except Exception as e:
            logger.error(f"Azure Search error for {self.company_name}: {e}")
            return {
                "items": [],
                "error": f"Search error: {str(e)}",
                "query": query,
                "company": self.company_name
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
        Extract citation strings from retrieved product information items.
        
        Use this tool to format citations for use in marketing content.
        Call this after retrieve_product_info() to get properly formatted citations.
        
        Args:
            items: List of items returned by retrieve_product_info()
        
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
