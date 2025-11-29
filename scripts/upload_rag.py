# scripts/upload_to_azure_search.py

"""
Simple script to upload JSON documents to Azure AI Search.
Usage: python upload_rag.py
"""

import os
import json
import httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def upload_documents(index_name: str, json_file_path: str) -> dict:
    """Upload documents from a JSON file to Azure AI Search."""
    
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    api_key = os.getenv("AZURE_SEARCH_ADMIN_KEY") or os.getenv("AZURE_SEARCH_API_KEY")
    
    if not endpoint or not api_key:
        raise ValueError("Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_ADMIN_KEY in environment")
    
    # Read JSON file
    with open(json_file_path, "r") as f:
        data = json.load(f)
    
    # Ensure proper format
    if "value" not in data:
        data = {"value": data if isinstance(data, list) else [data]}
    
    # Upload to Azure Search
    url = f"{endpoint}/indexes/{index_name}/docs/index?api-version=2024-05-01-preview"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }
    
    response = httpx.post(url, json=data, headers=headers, timeout=60.0)
    response.raise_for_status()
    
    return response.json()


def main():
    # Configuration
    index_name = os.getenv("AZURE_SEARCH_INDEX", "microsoft-azure-products")
    
    # Files to upload
    tables_dir = Path(__file__).parent.parent / "tables" / "Microsoft"
    files_to_upload = [
        tables_dir / "brand_legal_ruleset_azure_search.json",
        tables_dir / "product_reference_azure_search.json",
    ]
    
    print(f"Uploading to index: {index_name}")
    print("-" * 50)
    
    for file_path in files_to_upload:
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue
        
        try:
            print(f"📤 Uploading: {file_path.name}")
            result = upload_documents(index_name, str(file_path))
            
            # Count results
            uploaded = sum(1 for r in result.get("value", []) if r.get("status"))
            failed = sum(1 for r in result.get("value", []) if not r.get("status"))
            
            print(f"   ✅ Uploaded: {uploaded} documents")
            if failed > 0:
                print(f"   ❌ Failed: {failed} documents")
                
        except httpx.HTTPStatusError as e:
            print(f"   ❌ HTTP Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("-" * 50)
    print("Done!")


if __name__ == "__main__":
    main()