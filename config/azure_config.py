"""
Azure service configuration loader.
"""

import os
import yaml
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def load_config() -> Dict:
    """
    Load configuration from environment variables and YAML files.
    Prioritizes environment variables for sensitive data.
    """
    
    config_path = Path(__file__).parent
    
    # Load base configuration from YAML
    with open(config_path / "base_config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    # Override with environment variables (for secrets)
    config["azure_openai"] = {
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", config.get("azure_openai", {}).get("endpoint")),
        "deployment_name": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        "api_version": "2024-02-01"
    }
    
    config["azure_search"] = {
        "endpoint": os.getenv("AZURE_SEARCH_ENDPOINT"),
        "index_name": os.getenv("AZURE_SEARCH_INDEX", "product-docs"),
    }
    
    config["cosmos_db"] = {
        "endpoint": os.getenv("COSMOS_DB_ENDPOINT"),
        "database_name": os.getenv("COSMOS_DB_DATABASE", "marketing_agents"),
        "container_name": os.getenv("COSMOS_DB_CONTAINER", "conversations")
    }
    
    config["content_safety"] = {
        "endpoint": os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT")
    }
    
    config["app_configuration"] = {
        "endpoint": os.getenv("AZURE_APP_CONFIG_ENDPOINT")
    }
    
    config["azure_monitor"] = {
        "connection_string": os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    }
    
    config["cdp"] = {
        "endpoint": os.getenv("CDP_ENDPOINT", "https://platform.adobe.io"),
        "org_id": os.getenv("CDP_ORG_ID"),
        "api_key": os.getenv("CDP_API_KEY")
    }
    
    return config