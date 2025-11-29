"""
Company Data Service — provides company-specific Azure resource configuration.

Default Company: Hudson Street Bakery
Alternative: Microsoft Azure (set COMPANY_ID=microsoft in .env)

This service provides:
- Azure AI Search index names for RAG
- Azure SQL Database table names for segmentation
- Cosmos DB container names for campaign state
- Brand rules and product catalog references
- Company context for AI agents

Data is stored in Azure services:
- Products & Brand Rules → Azure AI Search (RAG)
- Customer Segments → Azure SQL Database
- Campaign State → Azure Cosmos DB

Local tables/ folder contains reference data for Azure indexing.
"""

import os
import json
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# ==============================================================================
# COMPANY DEFINITIONS (Azure Resource Configuration)
# ==============================================================================

COMPANIES = {
    "hudson_street": {
        "id": "hudson_street",
        "name": "Hudson Street Bakery",
        "tagline": "Your neighborhood bakery since 2015",
        "industry": "Food & Beverage",
        "location": "West Village, Manhattan, NYC",
        # Azure AI Search configuration
        "azure_search_index": "hudson-street-products",
        "azure_search_semantic_config": "hudson-street-semantic",
        # Azure SQL Database configuration
        "sql_database": "hudson_street_marketing",
        "customer_table": "customers_hudson_street",
        # Azure Cosmos DB configuration
        "cosmos_container": "hudson_street_campaigns",
        # Local reference data (for development/indexing)
        "data_folder": "Hudson_street",
        "brand_rules_file": "brand_rules.json",
        "products_file": "products.json",
        "customers_file": "customers.csv",
    },
    "microsoft": {
        "id": "microsoft",
        "name": "Microsoft Azure",
        "tagline": "Empowering every person and organization",
        "industry": "Technology",
        "location": "Global",
        # Azure AI Search configuration
        "azure_search_index": "microsoft-azure-products",
        "azure_search_semantic_config": "microsoft-semantic",
        # Azure SQL Database configuration
        "sql_database": "microsoft_marketing",
        "customer_table": "customers_microsoft",
        # Azure Cosmos DB configuration
        "cosmos_container": "microsoft_campaigns",
        # Local reference data (for development/indexing)
        "data_folder": "Microsoft",
        "brand_rules_file": "Dataset 2_ Enterprise Brand & Legal Ruleset (JSON).txt",
        "products_file": "Dataset 1_ Azure Product Reference Documents (JSONL).txt",
        "customers_file": "Dataset 3_ Global Customer Segmentation Mock Data (CSV).txt",
    },
}

# Default to Hudson Street Bakery
DEFAULT_COMPANY = "hudson_street"


class CompanyDataService:
    """
    Service for company-specific Azure resource configuration and data access.
    
    Primary data sources (Production):
    - Azure AI Search: Products, brand rules (RAG)
    - Azure Synapse Analytics: Customer segments
    - Azure Cosmos DB: Campaign state
    
    Fallback data sources (Development):
    - Local tables/ folder for testing without Azure
    """
    
    def __init__(self, company_id: Optional[str] = None):
        """
        Initialize with company ID.
        
        Args:
            company_id: Company identifier. Defaults to COMPANY_ID env var or hudson_street.
        """
        self.company_id = company_id or os.getenv("COMPANY_ID", DEFAULT_COMPANY).lower()
        
        if self.company_id not in COMPANIES:
            logger.warning(f"Unknown company {self.company_id}, defaulting to {DEFAULT_COMPANY}")
            self.company_id = DEFAULT_COMPANY
        
        self.company_info = COMPANIES[self.company_id]
        self.tables_path = Path(__file__).parent.parent / "tables"
        
        # Cached data (for local fallback)
        self._brand_rules: Optional[Dict] = None
        self._products: Optional[Dict] = None
        self._customers: Optional[List] = None
        
        logger.info(f"CompanyDataService initialized for: {self.company_info['name']}")
    
    @property
    def data_path(self) -> Path:
        """Get the company's local data folder path (for development/indexing)."""
        folder_name = self.company_info["data_folder"]
        exact_path = self.tables_path / folder_name
        if exact_path.exists():
            return exact_path
            
        # Case-insensitive search
        if self.tables_path.exists() and self.tables_path.is_dir():
            for item in self.tables_path.iterdir():
                if item.name.lower() == folder_name.lower() and item.is_dir():
                    logger.info(f"Found case-insensitive match for data folder: {item.name}")
                    return item
                    
        return exact_path  # Will raise appropriate error if not found
    
    # ==========================================================================
    # AZURE RESOURCE CONFIGURATION
    # ==========================================================================
    
    def get_azure_search_config(self) -> Dict[str, str]:
        """Get Azure AI Search configuration for this company."""
        return {
            "index_name": self.company_info.get("azure_search_index", "product-docs"),
            "semantic_config": self.company_info.get("azure_search_semantic_config", "default"),
        }
    
    def get_sql_config(self) -> Dict[str, str]:
        """Get Azure SQL Database configuration for this company."""
        return {
            "database": self.company_info.get("sql_database", "marketing_data"),
            "customer_table": self.company_info.get("customer_table", "customers"),
        }
    
    def get_synapse_config(self) -> Dict[str, str]:
        """Deprecated: Use get_sql_config() instead. Kept for backward compatibility."""
        return self.get_sql_config()
    
    def get_cosmos_config(self) -> Dict[str, str]:
        """Get Azure Cosmos DB configuration for this company."""
        return {
            "container": self.company_info.get("cosmos_container", "campaigns"),
        }
    
    # ==========================================================================
    # COMPANY INFO
    # ==========================================================================
    
    def get_company_info(self) -> Dict[str, Any]:
        """Get basic company information."""
        return {
            "id": self.company_info["id"],
            "name": self.company_info["name"],
            "tagline": self.company_info["tagline"],
            "industry": self.company_info["industry"],
            "location": self.company_info["location"],
            "azure_search_index": self.company_info.get("azure_search_index"),
            "sql_database": self.company_info.get("sql_database"),
        }
    
    @staticmethod
    def list_companies() -> List[Dict[str, str]]:
        """List all available companies."""
        return [
            {
                "id": c["id"], 
                "name": c["name"], 
                "industry": c["industry"],
                "azure_search_index": c.get("azure_search_index"),
            }
            for c in COMPANIES.values()
        ]
    
    # ==========================================================================
    # BRAND RULES
    # ==========================================================================
    
    def get_brand_rules(self) -> Dict[str, Any]:
        """Load brand rules from company's JSON file."""
        if self._brand_rules is not None:
            return self._brand_rules
        
        file_path = self.data_path / self.company_info["brand_rules_file"]
        
        if not file_path.exists():
            logger.warning(f"Brand rules not found at {file_path}")
            return {}
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self._brand_rules = json.load(f)
            logger.info(f"Loaded brand rules for {self.company_info['name']}")
            return self._brand_rules
        except Exception as e:
            logger.error(f"Error loading brand rules: {e}")
            return {}
    
    def get_banned_phrases(self) -> List[str]:
        """Extract banned phrases from brand rules."""
        rules = self.get_brand_rules()
        banned = []
        
        # Hudson Street format
        compliance = rules.get("compliance_rules", {})
        if "banned_phrases" in compliance:
            banned.extend(compliance["banned_phrases"])
        
        # Microsoft format
        banned_claims = rules.get("banned_claims", {})
        for category in banned_claims.values():
            if isinstance(category, list):
                banned.extend(category)
        
        return [p.lower() for p in banned]
    
    def get_tone_guidelines(self) -> Dict[str, Any]:
        """Get tone and voice guidelines."""
        rules = self.get_brand_rules()
        
        # Hudson Street format
        if "tone_and_voice" in rules:
            return rules["tone_and_voice"]
        
        # Microsoft format
        if "tone_rules" in rules:
            return rules["tone_rules"]
        
        if "brand_voice" in rules:
            return rules["brand_voice"]
        
        return {}
    
    def get_compliance_rules(self) -> Dict[str, Any]:
        """Get compliance/legal rules."""
        rules = self.get_brand_rules()
        
        # Hudson Street format
        if "compliance_rules" in rules:
            return rules["compliance_rules"]
        
        # Microsoft format
        if "mandatory_disclaimers" in rules:
            return {
                "disclaimers": rules.get("mandatory_disclaimers", {}),
                "privacy": rules.get("privacy_rules", {}),
                "legal_triggers": rules.get("legal_review_triggers", {}),
            }
        
        return {}
    
    # ==========================================================================
    # PRODUCTS
    # ==========================================================================
    
    def get_products(self) -> Dict[str, Any]:
        """Load product catalog."""
        if self._products is not None:
            return self._products
        
        file_path = self.data_path / self.company_info["products_file"]
        
        if not file_path.exists():
            logger.warning(f"Products file not found at {file_path}")
            return {"products": []}
        
        try:
            # Microsoft uses JSONL format
            if self.company_id == "microsoft":
                products = []
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                products.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
                self._products = {"products": products, "source": "microsoft_azure_docs"}
            else:
                # Hudson Street uses standard JSON
                with open(file_path, "r", encoding="utf-8") as f:
                    self._products = json.load(f)
            
            logger.info(f"Loaded {len(self._products.get('products', []))} products for {self.company_info['name']}")
            return self._products
            
        except Exception as e:
            logger.error(f"Error loading products: {e}")
            return {"products": []}
    
    def get_product_list(self) -> List[Dict[str, Any]]:
        """Get just the product list."""
        return self.get_products().get("products", [])
    
    def search_products(self, query: str) -> List[Dict[str, Any]]:
        """Simple product search by name/description."""
        query_lower = query.lower()
        products = self.get_product_list()
        
        results = []
        for product in products:
            name = product.get("product_name", product.get("title", "")).lower()
            desc = product.get("description", product.get("content", "")).lower()
            
            if query_lower in name or query_lower in desc:
                results.append(product)
        
        return results[:10]  # Limit to 10 results
    
    # ==========================================================================
    # CUSTOMERS
    # ==========================================================================
    
    def get_customers(self) -> List[Dict[str, Any]]:
        """Load customer segment data."""
        if self._customers is not None:
            return self._customers
        
        file_path = self.data_path / self.company_info["customers_file"]
        
        if not file_path.exists():
            logger.warning(f"Customers file not found at {file_path}")
            return []
        
        try:
            customers = []
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    customers.append(row)
            
            self._customers = customers
            logger.info(f"Loaded {len(customers)} customer records for {self.company_info['name']}")
            return self._customers
            
        except Exception as e:
            logger.error(f"Error loading customers: {e}")
            return []
    
    def get_customer_segments(self) -> Dict[str, int]:
        """Get summary of customer segments."""
        customers = self.get_customers()
        
        if not customers:
            return {}
        
        # Try to find segment column
        segment_keys = ["segment", "customer_segment", "tier", "category"]
        segment_col = None
        
        if customers:
            first = customers[0]
            for key in segment_keys:
                if key in first:
                    segment_col = key
                    break
        
        if not segment_col:
            return {"total": len(customers)}
        
        segments = {}
        for c in customers:
            seg = c.get(segment_col, "unknown")
            segments[seg] = segments.get(seg, 0) + 1
        
        return segments
    
    # ==========================================================================
    # CONTEXT FOR AGENTS
    # ==========================================================================
    
    def get_agent_context(self) -> str:
        """
        Generate context string for AI agents about the current company.
        
        This is injected into agent prompts to ground them in company data.
        """
        info = self.get_company_info()
        tone = self.get_tone_guidelines()
        products = self.get_product_list()[:5]  # Top 5 products
        
        context = f"""
COMPANY CONTEXT:
================
Company: {info['name']}
Industry: {info['industry']}
Tagline: "{info['tagline']}"
Location: {info['location']}

BRAND VOICE:
"""
        # Add tone guidelines
        if tone:
            if "approved_tones" in tone:
                context += f"Approved tones: {', '.join(tone['approved_tones'][:5])}\n"
            if "characteristics" in tone:
                context += f"Characteristics: {', '.join(tone['characteristics'][:5])}\n"
        
        # Add sample products
        context += "\nSAMPLE PRODUCTS:\n"
        for p in products:
            name = p.get("product_name", p.get("title", "Unknown"))
            price = p.get("price", "N/A")
            context += f"- {name} (${price})\n" if price != "N/A" else f"- {name}\n"
        
        # Add banned phrases warning
        banned = self.get_banned_phrases()[:5]
        if banned:
            context += f"\nBANNED PHRASES (do not use): {', '.join(banned)}\n"
        
        return context


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def get_company_service(company_id: Optional[str] = None) -> CompanyDataService:
    """Get a CompanyDataService instance."""
    return CompanyDataService(company_id)


def get_current_company() -> Dict[str, Any]:
    """Get current company info."""
    return CompanyDataService().get_company_info()


def get_brand_rules() -> Dict[str, Any]:
    """Get brand rules for current company."""
    return CompanyDataService().get_brand_rules()


def get_products() -> Dict[str, Any]:
    """Get products for current company."""
    return CompanyDataService().get_products()
