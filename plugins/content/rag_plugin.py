"""
Retrieval-Augmented Generation plugin using Azure AI Search.
"""

from semantic_kernel.functions import kernel_function
from typing import Annotated
from azure.search.documents.aio import SearchClient
from azure.identity.aio import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential


class RAGPlugin:
    """
    Plugin for retrieving grounded product information from Azure AI Search.
    Enables citations and prevents hallucinations.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.credential = DefaultAzureCredential()
        
        self.search_client = SearchClient(
            endpoint=config["azure_search"]["endpoint"],
            index_name=config["azure_search"]["index_name"],
            credential=self.credential
        )
    
    @kernel_function(
        name="retrieve_product_info",
        description="Search product documentation for verified information"
    )
    async def retrieve_product_info(
        self,
        query: Annotated[str, "Product feature or information to look up"]
    ) -> Annotated[str, "Retrieved information with source metadata"]:
        """
        Retrieve grounded product information with citation metadata.
        """
        
        # Perform semantic search
        results = await self.search_client.search(
            search_text=query,
            top=5,
            select=["content", "title", "source_file", "page_number"],
            query_type="semantic",
            semantic_configuration_name="default"
        )
        
        # Format results with citations
        retrieved_content = []
        async for result in results:
            citation = f"[Source: {result['title']}, Page {result['page_number']}]"
            retrieved_content.append({
                "content": result["content"],
                "citation": citation,
                "score": result["@search.score"]
            })
        
        if not retrieved_content:
            return "No relevant product information found. Do not make claims without grounding."
        
        # Format response
        response = "Retrieved product information:\n\n"
        for i, item in enumerate(retrieved_content, 1):
            response += f"{i}. {item['content']}\n   {item['citation']}\n\n"
        
        return response
