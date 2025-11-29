"""
Diagnostic script to test Application Insights connection and verify logs are being sent.
Run this script and then check Azure Portal → Application Insights → Logs
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from config.azure_config import load_config
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

def test_application_insights():
    """Test Application Insights configuration and send test logs."""
    
    print("=" * 80)
    print("APPLICATION INSIGHTS DIAGNOSTIC TEST")
    print("=" * 80)
    
    # Step 1: Load configuration
    print("\n1. Loading configuration...")
    try:
        config = load_config()
        connection_string = config.get("azure_monitor", {}).get("connection_string")
        
        if not connection_string:
            print("❌ ERROR: APPLICATIONINSIGHTS_CONNECTION_STRING not found in environment")
            print("\nPlease set the environment variable:")
            print("  export APPLICATIONINSIGHTS_CONNECTION_STRING='InstrumentationKey=...;IngestionEndpoint=...'")
            return False
        
        # Mask the connection string for display
        if connection_string:
            parts = connection_string.split(';')
            masked = ';'.join([p if 'IngestionEndpoint' in p else 'InstrumentationKey=***' for p in parts])
            print(f"   ✓ Connection string found: {masked}")
        else:
            print("   ❌ Connection string is empty")
            return False
            
    except Exception as e:
        print(f"   ❌ Failed to load config: {e}")
        return False
    
    # Step 2: Configure Azure Monitor
    print("\n2. Configuring Azure Monitor...")
    try:
        configure_azure_monitor(
            connection_string=connection_string
        )
        print("   ✓ Azure Monitor configured successfully")
    except Exception as e:
        print(f"   ❌ Failed to configure Azure Monitor: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Set up logging and verify OpenTelemetry handler
    print("\n3. Setting up logging...")
    try:
        # Get root logger before basicConfig
        root_logger = logging.getLogger()
        
        # Configure logging - but DON'T use force=True as it removes existing handlers
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            force=False  # Don't force - preserve OpenTelemetry handlers
        )
        logger = logging.getLogger(__name__)
        
        # Check if OpenTelemetry logging handler is present
        handlers = root_logger.handlers
        print(f"   ✓ Logging configured with {len(handlers)} handler(s)")
        
        # Check for OpenTelemetry handler
        otel_handler_found = False
        for handler in handlers:
            handler_type = type(handler).__name__
            print(f"      - Handler: {handler_type}")
            if 'opentelemetry' in handler_type.lower() or 'logging' in handler_type.lower():
                otel_handler_found = True
        
        if not otel_handler_found:
            print("   ⚠️  WARNING: OpenTelemetry logging handler not found!")
            print("      This means logs may not be sent to Application Insights")
            print("      Trying to add OpenTelemetry logging handler explicitly...")
            
            # Try to add OpenTelemetry logging handler explicitly
            try:
                from opentelemetry.instrumentation.logging import LoggingInstrumentor
                LoggingInstrumentor().instrument()
                print("      ✓ OpenTelemetry logging handler added explicitly")
            except Exception as e:
                print(f"      ❌ Failed to add handler: {e}")
        else:
            print("   ✓ OpenTelemetry logging handler detected")
            
    except Exception as e:
        print(f"   ❌ Failed to configure logging: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Test OpenTelemetry tracer
    print("\n4. Testing OpenTelemetry tracer...")
    try:
        tracer = trace.get_tracer("test_app_insights")
        with tracer.start_as_current_span("test_span") as span:
            span.set_attribute("test.attribute", "test_value")
            span.set_attribute("test.number", 42)
            print("   ✓ Tracer working - created test span")
    except Exception as e:
        print(f"   ❌ Failed to create tracer span: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 5: Send test logs
    print("\n5. Sending test logs to Application Insights...")
    try:
        logger.info("🔍 TEST LOG: This is an INFO level test message from diagnostic script")
        logger.warning("⚠️ TEST LOG: This is a WARNING level test message")
        logger.error("❌ TEST LOG: This is an ERROR level test message")
        
        # Log with custom dimensions
        logger.info(
            "📊 TEST LOG: Agent Activity Test",
            extra={
                "custom_dimensions": {
                    "agent": "test_agent",
                    "function": "test_function",
                    "test": True
                }
            }
        )
        
        print("   ✓ Test logs sent")
    except Exception as e:
        print(f"   ❌ Failed to send logs: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 6: Test custom metrics
    print("\n6. Testing custom metrics...")
    try:
        from opentelemetry import metrics
        meter = metrics.get_meter("test_app_insights")
        counter = meter.create_counter(
            name="test.counter",
            description="Test counter metric",
            unit="1"
        )
        counter.add(1, {"test": "diagnostic"})
        print("   ✓ Custom metric sent")
    except Exception as e:
        print(f"   ⚠️ Failed to send custom metric: {e}")
    
    # Step 7: Flush and wait
    print("\n7. Flushing telemetry...")
    try:
        # Force flush of OpenTelemetry exporters
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        
        # Give time for telemetry to be sent
        import time
        print("   Waiting 10 seconds for telemetry to be sent...")
        time.sleep(10)  # Increased wait time
        
        # Try to force flush
        try:
            from opentelemetry.sdk.trace import TracerProvider
            provider = trace.get_tracer_provider()
            if hasattr(provider, 'force_flush'):
                provider.force_flush()
        except:
            pass
            
        print("   ✓ Flush complete")
    except Exception as e:
        print(f"   ⚠️ Flush issue: {e}")
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC TEST COMPLETE")
    print("=" * 80)
    print("\n📊 Next Steps:")
    print("1. Go to Azure Portal → Your Application Insights resource")
    print("2. Navigate to 'Logs' (in the left menu)")
    print("3. Run this query to see traces:")
    print("   traces | where message contains 'TEST LOG' | order by timestamp desc")
    print("\n4. Or run this query to see custom events:")
    print("   customEvents | where name contains 'test' | order by timestamp desc")
    print("\n5. Check 'Live Metrics' for real-time data")
    print("\n⏱️  Note: It may take 2-5 minutes for logs to appear in the portal")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    success = test_application_insights()
    sys.exit(0 if success else 1)

