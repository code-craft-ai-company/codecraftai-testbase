#!/usr/bin/env python3
"""
Example script demonstrating diagnostic streaming capabilities.

This script shows how to use the diagnostic streaming system to stream
diagnostic data to external systems in real-time. It covers:

1. Basic HTTP streaming configuration
2. WebSocket streaming for real-time monitoring
3. File-based streaming for local debugging
4. Callback-based streaming for custom processing
5. Async streaming with buffering

Usage:
    python debug_diagnostics_streaming.py

Note:
    This script demonstrates the streaming API but does not require
    actual external endpoints. It uses simulated/local endpoints for
    demonstration purposes.
"""

import json
import os
import sys
import tempfile
import time

# Add the source packages to the path for development
script_dir = os.path.dirname(os.path.abspath(__file__))
packages_dir = os.path.join(script_dir, "..", "packages")
sys.path.insert(0, packages_dir)

from ccai.testbase.diagnostic_streaming import (
    DiagnosticStreamManager,
    DiagnosticStreamConfig,
    DiagnosticStreamProtocol,
    DiagnosticStreamEvent,
    FileStreamHandler,
)


def print_section(title: str) -> None:
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def example_file_streaming():
    """
    Demonstrates file-based diagnostic streaming.
    
    File streaming is useful for:
    - Local debugging and development
    - Scenarios without network connectivity
    - Creating audit trails of diagnostic data
    """
    print_section("File-Based Diagnostic Streaming")
    
    # Create a temporary file for streaming
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        stream_file = f.name
    
    print(f"Streaming to file: {stream_file}")
    
    # Configure file streaming
    config = DiagnosticStreamConfig(
        enabled=True,
        protocol=DiagnosticStreamProtocol.FILE,
        endpoint=stream_file
    )
    
    # Initialize the stream manager
    success = DiagnosticStreamManager.configure(config)
    print(f"Configuration successful: {success}")
    print(f"Stream manager enabled: {DiagnosticStreamManager.is_enabled()}")
    print(f"Stream manager connected: {DiagnosticStreamManager.is_connected()}")
    
    # Stream some diagnostic events
    print("\nStreaming diagnostic events...")
    
    events = [
        {
            "label": "prerun-diagnostic",
            "integration_name": "DeviceCoupling",
            "level": 5,
            "data": {"status": "connected", "device_id": "device-001"}
        },
        {
            "label": "prerun-diagnostic",
            "integration_name": "NetworkCoupling",
            "level": 5,
            "data": {"status": "online", "ip_address": "192.168.1.100"}
        },
        {
            "label": "postrun-diagnostic",
            "integration_name": "DeviceCoupling",
            "level": 5,
            "data": {"status": "disconnected", "test_count": 10}
        }
    ]
    
    for event_data in events:
        success = DiagnosticStreamManager.stream_diagnostic(
            label=event_data["label"],
            integration_name=event_data["integration_name"],
            level=event_data["level"],
            data=event_data["data"],
            metadata={"test_run_id": "run-123", "timestamp": time.time()}
        )
        print(f"  Streamed {event_data['integration_name']}: {success}")
    
    # Shutdown and read the file
    DiagnosticStreamManager.shutdown()
    
    print("\nContents of stream file:")
    print("-" * 40)
    with open(stream_file, 'r') as f:
        for line in f:
            event = json.loads(line)
            print(f"  {event['integration_name']}: {event['data']}")
    
    # Cleanup
    os.unlink(stream_file)
    print(f"\nCleaned up temporary file")


def example_callback_streaming():
    """
    Demonstrates callback-based diagnostic streaming.
    
    Callback streaming is useful for:
    - Custom processing of diagnostic events
    - Integration with existing logging frameworks
    - Real-time alerting based on diagnostic data
    """
    print_section("Callback-Based Diagnostic Streaming")
    
    # Store received events for demonstration
    received_events = []
    
    def my_callback(event: DiagnosticStreamEvent):
        """Custom callback to process diagnostic events."""
        received_events.append(event)
        print(f"  [CALLBACK] Received: {event.integration_name} - {event.label}")
        print(f"             Data: {event.data}")
    
    def my_error_callback(event: DiagnosticStreamEvent, error: Exception):
        """Error callback for handling failures."""
        print(f"  [ERROR] Failed to process event: {error}")
    
    # Configure callback streaming
    config = DiagnosticStreamConfig(
        enabled=True,
        protocol=DiagnosticStreamProtocol.CALLBACK,
        callback=my_callback,
        error_callback=my_error_callback
    )
    
    success = DiagnosticStreamManager.configure(config)
    print(f"Configuration successful: {success}")
    
    # Stream some events
    print("\nStreaming events to callback...")
    
    DiagnosticStreamManager.stream_diagnostic(
        label="prerun-diagnostic",
        integration_name="DatabaseCoupling",
        level=7,
        data={"connection_pool_size": 10, "active_connections": 3}
    )
    
    DiagnosticStreamManager.stream_diagnostic(
        label="checkpoint-diagnostic",
        integration_name="CacheCoupling",
        level=5,
        data={"cache_hits": 150, "cache_misses": 12}
    )
    
    # Shutdown
    DiagnosticStreamManager.shutdown()
    
    print(f"\nTotal events received: {len(received_events)}")


def example_http_streaming_config():
    """
    Demonstrates HTTP streaming configuration.
    
    Note: This example shows configuration only, as it requires
    an actual HTTP endpoint to send data to.
    """
    print_section("HTTP Streaming Configuration")
    
    print("HTTP streaming configuration example:")
    print("-" * 40)
    
    # Example HTTP configuration
    config = DiagnosticStreamConfig(
        enabled=True,
        protocol=DiagnosticStreamProtocol.HTTP,
        endpoint="https://diagnostics.example.com/api/v1/stream",
        api_key="your-api-key-here",
        timeout=30,
        retry_count=3,
        retry_delay=1.0,
        headers={
            "X-Custom-Header": "custom-value"
        }
    )
    
    print(f"Protocol: {config.protocol.value}")
    print(f"Endpoint: {config.endpoint}")
    print(f"Timeout: {config.timeout}s")
    print(f"Retry count: {config.retry_count}")
    print(f"Retry delay: {config.retry_delay}s")
    print(f"Async mode: {config.async_mode}")
    
    print("\nConfiguration dictionary (sensitive data masked):")
    config_dict = config.to_dict()
    for key, value in config_dict.items():
        print(f"  {key}: {value}")


def example_websocket_streaming_config():
    """
    Demonstrates WebSocket streaming configuration.
    
    Note: This example shows configuration only, as it requires
    an actual WebSocket endpoint to connect to.
    """
    print_section("WebSocket Streaming Configuration")
    
    print("WebSocket streaming configuration example:")
    print("-" * 40)
    
    # Example WebSocket configuration
    config = DiagnosticStreamConfig(
        enabled=True,
        protocol=DiagnosticStreamProtocol.WEBSOCKET,
        endpoint="wss://stream.example.com/diagnostics",
        api_key="your-api-key-here",
        timeout=30,
        async_mode=True,  # WebSocket typically uses async mode
        buffer_size=100
    )
    
    print(f"Protocol: {config.protocol.value}")
    print(f"Endpoint: {config.endpoint}")
    print(f"Async mode: {config.async_mode}")
    print(f"Buffer size: {config.buffer_size}")
    
    print("\nWebSocket streaming benefits:")
    print("  - Persistent connection for low latency")
    print("  - Bidirectional communication")
    print("  - Real-time event streaming")
    print("  - Automatic reconnection support")


def example_environment_config():
    """
    Demonstrates configuration from environment variables.
    """
    print_section("Environment Variable Configuration")
    
    print("Supported environment variables:")
    print("-" * 40)
    
    env_vars = [
        ("DIAGNOSTIC_STREAM_ENABLED", "Enable/disable streaming (true/false)"),
        ("DIAGNOSTIC_STREAM_PROTOCOL", "Protocol (http, websocket, file, callback)"),
        ("DIAGNOSTIC_STREAM_ENDPOINT", "Endpoint URL or file path"),
        ("DIAGNOSTIC_STREAM_API_KEY", "API key for authentication"),
        ("DIAGNOSTIC_STREAM_AUTH_TOKEN", "Bearer token for authentication"),
        ("DIAGNOSTIC_STREAM_TIMEOUT", "Timeout in seconds"),
        ("DIAGNOSTIC_STREAM_ASYNC", "Enable async mode (true/false)")
    ]
    
    for var, description in env_vars:
        print(f"  {var}")
        print(f"    {description}")
    
    print("\nExample usage:")
    print("  export DIAGNOSTIC_STREAM_ENABLED=true")
    print("  export DIAGNOSTIC_STREAM_PROTOCOL=http")
    print("  export DIAGNOSTIC_STREAM_ENDPOINT=https://api.example.com/diagnostics")
    print("  export DIAGNOSTIC_STREAM_API_KEY=your-api-key")
    
    print("\nLoading configuration from environment:")
    config = DiagnosticStreamConfig.from_environment()
    print(f"  Enabled: {config.enabled}")
    print(f"  Protocol: {config.protocol.value}")
    print(f"  Endpoint: {config.endpoint or '(not set)'}")


def example_async_streaming():
    """
    Demonstrates asynchronous streaming with buffering.
    
    Async streaming is useful for:
    - High-throughput diagnostic capture
    - Non-blocking diagnostic operations
    - Buffering during network issues
    """
    print_section("Asynchronous Streaming")
    
    # Create a temporary file for async streaming demo
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        stream_file = f.name
    
    print(f"Async streaming to file: {stream_file}")
    
    # Configure async file streaming
    config = DiagnosticStreamConfig(
        enabled=True,
        protocol=DiagnosticStreamProtocol.FILE,
        endpoint=stream_file,
        async_mode=True,
        buffer_size=50
    )
    
    success = DiagnosticStreamManager.configure(config)
    print(f"Configuration successful: {success}")
    print(f"Async mode: {config.async_mode}")
    print(f"Buffer size: {config.buffer_size}")
    
    # Stream multiple events quickly
    print("\nStreaming 10 events asynchronously...")
    start_time = time.time()
    
    for i in range(10):
        DiagnosticStreamManager.stream_diagnostic(
            label="benchmark-diagnostic",
            integration_name=f"Integration-{i}",
            level=5,
            data={"iteration": i, "value": i * 100}
        )
    
    elapsed = time.time() - start_time
    print(f"Queued 10 events in {elapsed:.4f} seconds")
    
    # Get stats
    stats = DiagnosticStreamManager.get_stats()
    print(f"\nStream manager stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Wait for async processing
    print("\nWaiting for async processing...")
    time.sleep(2)
    
    # Shutdown (flushes remaining events)
    DiagnosticStreamManager.shutdown()
    
    # Count events in file
    with open(stream_file, 'r') as f:
        event_count = sum(1 for _ in f)
    print(f"Events written to file: {event_count}")
    
    # Cleanup
    os.unlink(stream_file)


def example_stream_event():
    """
    Demonstrates the DiagnosticStreamEvent class.
    """
    print_section("DiagnosticStreamEvent")
    
    print("Creating a diagnostic stream event:")
    print("-" * 40)
    
    event = DiagnosticStreamEvent(
        label="prerun-diagnostic",
        integration_name="DeviceCoupling",
        level=7,
        data={
            "device_id": "device-001",
            "status": "connected",
            "firmware_version": "1.2.3"
        },
        metadata={
            "test_run_id": "run-456",
            "environment": "staging"
        }
    )
    
    print(f"Event: {event}")
    print(f"Timestamp: {event.timestamp}")
    print(f"Label: {event.label}")
    print(f"Integration: {event.integration_name}")
    print(f"Level: {event.level}")
    print(f"Data: {event.data}")
    print(f"Metadata: {event.metadata}")
    
    print("\nEvent as dictionary:")
    event_dict = event.to_dict()
    print(json.dumps(event_dict, indent=2))
    
    print("\nEvent as JSON:")
    print(event.to_json())


def example_handler_direct_usage():
    """
    Demonstrates direct usage of stream handlers.
    """
    print_section("Direct Handler Usage")
    
    print("Using FileStreamHandler directly:")
    print("-" * 40)
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        stream_file = f.name
    
    # Create handler directly
    config = DiagnosticStreamConfig(
        enabled=True,
        protocol=DiagnosticStreamProtocol.FILE,
        endpoint=stream_file
    )
    
    handler = FileStreamHandler(config)
    
    # Connect
    connected = handler.connect()
    print(f"Connected: {connected}")
    print(f"Is connected: {handler.is_connected()}")
    
    # Create and send an event
    event = DiagnosticStreamEvent(
        label="test-diagnostic",
        integration_name="TestIntegration",
        level=5,
        data={"test": "value"}
    )
    
    sent = handler.send(event)
    print(f"Event sent: {sent}")
    
    # Disconnect
    handler.disconnect()
    print(f"Disconnected. Is connected: {handler.is_connected()}")
    
    # Verify file contents
    with open(stream_file, 'r') as f:
        content = f.read()
    print(f"\nFile contents:\n{content}")
    
    # Cleanup
    os.unlink(stream_file)


def main():
    """Run all streaming examples."""
    print("\n" + "=" * 70)
    print(" DIAGNOSTIC STREAMING EXAMPLES")
    print("=" * 70)
    print("\nThis script demonstrates the diagnostic streaming capabilities")
    print("of the TestBase framework.\n")
    
    # Run examples
    example_stream_event()
    example_file_streaming()
    example_callback_streaming()
    example_async_streaming()
    example_handler_direct_usage()
    example_http_streaming_config()
    example_websocket_streaming_config()
    example_environment_config()
    
    print("\n" + "=" * 70)
    print(" EXAMPLES COMPLETE")
    print("=" * 70)
    print("\nFor more information, see the diagnostic_streaming module documentation.")


if __name__ == "__main__":
    main()
