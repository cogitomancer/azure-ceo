"""
Utility for extracting citations from Semantic Kernel responses.

TODO: Consider refactoring this into a dedicated CitationPlugin for better integration
      with the agent system. Current implementation is a utility class, but a plugin
      would allow agents to directly call citation extraction functions.
      
      Proposed plugin structure:
      - plugins/content/citation_plugin.py
      - Functions: extract_citations(), validate_citations(), format_citations()
      - Would integrate with ContentCreator and ComplianceOfficer agents
"""

from semantic_kernel.contents import ChatMessageContent
from typing import List, Dict
import logging


class CitationExtractor:
    """Extract citation metadata from agent responses."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_citations(self, message: ChatMessageContent) -> List[Dict]:
        """
        Extract citations from message content items.
        
        Returns list of citation dictionaries with:
        - source_file: document name
        - page_number: page reference
        - quote: relevant text snippet
        - url: link to document (if available)
        """
        
        citations = []
        
        # Iterate through message content items
        for item in message.items:
            # Check for text content with annotations
            if hasattr(item, 'text') and hasattr(item, 'annotations'):
                for annotation in item.annotations:
                    citation_data = self._parse_annotation(annotation)
                    if citation_data:
                        citations.append(citation_data)
        
        self.logger.info(f"Extracted {len(citations)} citations")
        return citations
    
    def _parse_annotation(self, annotation) -> Dict:
        """Parse individual annotation into citation data."""
        
        citation = {}
        
        # Handle file citations
        if hasattr(annotation, 'file_citation'):
            file_cit = annotation.file_citation
            citation['source_file'] = getattr(file_cit, 'file_name', 'Unknown')
            citation['page_number'] = getattr(file_cit, 'page_number', None)
            citation['quote'] = getattr(file_cit, 'quote', None)
        
        # Handle URL citations
        elif hasattr(annotation, 'url_citation'):
            url_cit = annotation.url_citation
            citation['url'] = getattr(url_cit, 'url', None)
            citation['title'] = getattr(url_cit, 'title', 'Web Source')
        
        return citation if citation else None
    
    def format_citations(self, citations: List[Dict]) -> str:
        """Format citations as readable text."""
        
        if not citations:
            return ""
        
        formatted = "\n\nSources:\n"
        for i, cit in enumerate(citations, 1):
            if 'source_file' in cit:
                formatted += f"{i}. {cit['source_file']}"
                if cit.get('page_number'):
                    formatted += f", Page {cit['page_number']}"
            elif 'url' in cit:
                formatted += f"{i}. {cit.get('title', 'Web Source')}: {cit['url']}"
            formatted += "\n"
        
        return formatted
