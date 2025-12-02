"""
Azure service configuration loader (merged YAML + env vars with overrides)
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


def merge(base: dict, override: dict) -> dict:
    """Recursively merge dictionaries (override env vars into YAML)."""
    result = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        elif value is not None:
            result[key] = value
    return result


def load_config() -> Dict[str, Any]:
    """
    Load configuration from:
    1. YAML file (base defaults)
    2. ENV variables (override sensitive settings)
    """

    config_path = Path(__file__).parent

    with open(config_path / "base_config.yaml", "r") as f:
        base_cfg = yaml.safe_load(f)

    #
    # Build overrides from env vars (NULL ignored)
    #
    # Load Azure OpenAI config with debug logging
    openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    # Debug logging (without exposing sensitive data)
    import logging
    logger = logging.getLogger(__name__)
    if openai_api_key:
        logger.info(f"AZURE_OPENAI_API_KEY found in environment (length: {len(openai_api_key)})")
    else:
        logger.warning("AZURE_OPENAI_API_KEY not found in environment variables")
    
    if openai_endpoint:
        logger.info(f"AZURE_OPENAI_ENDPOINT: {openai_endpoint[:50]}...")
    
    env_cfg = {
        "azure_openai": {
            "endpoint": openai_endpoint,
            "deployment_name": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
            "api_key": openai_api_key,
        },

        "azure_search": {
            "endpoint": os.getenv("AZURE_SEARCH_ENDPOINT"),
            "admin_key": os.getenv("AZURE_SEARCH_ADMIN_KEY"),
            "index_name": os.getenv("AZURE_SEARCH_INDEX"),
            "embedding_deployment": os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
            "semantic_configuration": os.getenv("AZURE_SEARCH_SEMANTIC_CONFIG"),
            "vector_dimensions": os.getenv("AZURE_SEARCH_VECTOR_DIM"),
        },

        "cosmos_db": {
            "endpoint": os.getenv("COSMOS_DB_ENDPOINT"),
            "key": os.getenv("COSMOS_DB_KEY"),
            "database_name": os.getenv("COSMOS_DB_DATABASE"),
            "container_name": os.getenv("COSMOS_DB_CONTAINER"),
            "partition_key": os.getenv("COSMOS_DB_PARTITION_KEY"),
        },

        "azure_monitor": {
            "connection_string": os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING") or os.getenv("APPLICATION_INSIGHTS_CONNECTION_STRING")
        },

        "content_safety": {
            "endpoint": os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT"),
            "key": os.getenv("AZURE_CONTENT_SAFETY_KEY")
        },

        "app_configuration": {
            "endpoint": os.getenv("AZURE_APP_CONFIG_ENDPOINT")
        },

        "synapse": {
            "endpoint": os.getenv("AZURE_SYNAPSE_ENDPOINT"),
            "database": os.getenv("AZURE_SYNAPSE_DATABASE"),
            "spark_pool": os.getenv("AZURE_SYNAPSE_SPARK_POOL"),
        },
    }

    #
    # Merge YAML + env overrides
    #
    merged = merge(base_cfg, env_cfg)

    return merged
