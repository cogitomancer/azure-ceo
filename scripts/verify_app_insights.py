#!/usr/bin/env python3
"""
Quick script to verify Application Insights connection string is set correctly.
Run this before starting your application to ensure logs will be sent to Azure.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

def verify_connection_string():
    """Verify Application Insights connection string is properly configured."""
    
    print("=" * 80)
    print("APPLICATION INSIGHTS CONNECTION STRING VERIFICATION")
    print("=" * 80)
    
    # Check both possible environment variable names
    conn_str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING") or os.getenv("APPLICATION_INSIGHTS_CONNECTION_STRING")
    
    if not conn_str:
        print("\n❌ ERROR: Connection string not found!")
        print("\nPlease set one of these environment variables:")
        print("  APPLICATIONINSIGHTS_CONNECTION_STRING (recommended)")
        print("  APPLICATION_INSIGHTS_CONNECTION_STRING (alternative)")
        print("\nYou can set it in:")
        print("  1. .env file in the project root")
        print("  2. Environment variables")
        print("  3. Shell: export APPLICATIONINSIGHTS_CONNECTION_STRING='...'")
        print("\nTo get your connection string:")
        print("  1. Go to Azure Portal")
        print("  2. Navigate to your Application Insights resource")
        print("  3. Go to 'Overview' → Copy 'Connection String'")
        print("\nExpected format:")
        print("  InstrumentationKey=xxxx-xxxx-xxxx-xxxx;IngestionEndpoint=https://...")
        return False
    
    # Verify format
    print(f"\n✓ Connection string found")
    
    # Check for required components
    has_instrumentation_key = "InstrumentationKey=" in conn_str
    has_ingestion_endpoint = "IngestionEndpoint=" in conn_str
    
    if not has_instrumentation_key:
        print("⚠️  WARNING: Connection string missing 'InstrumentationKey='")
        print("   This may cause issues sending telemetry to Application Insights")
    
    if not has_ingestion_endpoint:
        print("⚠️  WARNING: Connection string missing 'IngestionEndpoint='")
        print("   This may cause issues sending telemetry to Application Insights")
    
    if has_instrumentation_key and has_ingestion_endpoint:
        print("✓ Connection string format looks correct")
        
        # Extract and mask the instrumentation key for display
        parts = conn_str.split(';')
        for part in parts:
            if part.startswith('InstrumentationKey='):
                key = part.split('=')[1]
                if len(key) > 8:
                    masked_key = key[:4] + "-" + "xxxx-xxxx-xxxx-" + key[-4:]
                    print(f"  InstrumentationKey: {masked_key}")
                break
        
        for part in parts:
            if part.startswith('IngestionEndpoint='):
                endpoint = part.split('=')[1]
                print(f"  IngestionEndpoint: {endpoint}")
                break
        
        print("\n✓ Connection string verification passed!")
        print("\nNext steps:")
        print("  1. Run: python scripts/test_application_insights.py")
        print("  2. Check Azure Portal → Application Insights → Logs")
        print("  3. Query: traces | where message contains 'TEST LOG'")
        return True
    else:
        print("\n❌ Connection string format appears incorrect")
        print("   Please verify your connection string from Azure Portal")
        return False

if __name__ == "__main__":
    success = verify_connection_string()
    sys.exit(0 if success else 1)

