#!/usr/bin/env python3
"""
Script to help you find logs in Application Insights.
Provides different queries to check various tables.
"""

print("=" * 80)
print("APPLICATION INSIGHTS LOG QUERIES")
print("=" * 80)
print("\nTry these queries in Azure Portal → Application Insights → Logs:\n")

queries = [
    ("All traces (last hour)", "traces | where timestamp > ago(1h) | order by timestamp desc | take 50"),
    ("Test logs", "traces | where message contains 'TEST LOG' | order by timestamp desc"),
    ("All logs (any table)", "union traces, customEvents, exceptions, requests | where timestamp > ago(1h) | order by timestamp desc | take 50"),
    ("Custom events", "customEvents | where timestamp > ago(1h) | order by timestamp desc"),
    ("Exceptions", "exceptions | where timestamp > ago(1h) | order by timestamp desc"),
    ("Requests", "requests | where timestamp > ago(1h) | order by timestamp desc"),
    ("Agent activity logs", "traces | where message contains 'Agent Activity' | order by timestamp desc"),
    ("All INFO level logs", "traces | where severityLevel == 2 | order by timestamp desc | take 50"),
    ("All ERROR level logs", "traces | where severityLevel >= 3 | order by timestamp desc | take 50"),
]

for i, (name, query) in enumerate(queries, 1):
    print(f"{i}. {name}:")
    print(f"   {query}\n")

print("=" * 80)
print("TIPS:")
print("=" * 80)
print("1. Wait 2-5 minutes after sending logs before querying")
print("2. Check 'Live Metrics' for real-time data")
print("3. If no results, check:")
print("   - Connection string is correct")
print("   - Application Insights resource is active")
print("   - Time range in query (try 'ago(24h)')")
print("   - Network connectivity to Azure")
print("=" * 80)

