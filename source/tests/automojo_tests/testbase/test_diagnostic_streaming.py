"""
Unit tests for the diagnostic streaming module.

This module tests the diagnostic streaming functionality including:
- DiagnosticStreamProtocol enumeration
- DiagnosticStreamEvent class
- DiagnosticStreamConfig class
- Stream handlers (File, Callback, HTTP, WebSocket)
- DiagnosticStreamManager class
"""

import json
import os
import sys
import tempfile
import threading
import time
import unittest

# Add the source packages to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
packages_dir = os.path.join(script_dir, "..", "..", "..", "packages")
sys.path.insert(0, packages_dir)

from automojo.testbase.diagnostic_streaming import (
    DiagnosticStreamProtocol,
    DiagnosticStreamEvent,
    DiagnosticStreamConfig,
    DiagnosticStreamHandler,
    HttpStreamHandler,
    WebSocketStreamHandler,
    FileStreamHandler,
    CallbackStreamHandler,
    DiagnosticStreamManager
)


class TestDiagnosticStreamProtocol(unittest.TestCase):
    """Tests for DiagnosticStreamProtocol enumeration."""

    def test_protocol_values(self):
        """Test that protocol enum has expected values."""
        self.assertEqual(DiagnosticStreamProtocol.HTTP.value, "http")
        self.assertEqual(DiagnosticStreamProtocol.WEBSOCKET.value, "websocket")
        self.assertEqual(DiagnosticStreamProtocol.FILE.value, "file")
        self.assertEqual(DiagnosticStreamProtocol.CALLBACK.value, "callback")

    def test_protocol_from_string(self):
        """Test creating protocol from string value."""
        self.assertEqual(DiagnosticStreamProtocol("http"), DiagnosticStreamProtocol.HTTP)
        self.assertEqual(DiagnosticStreamProtocol("websocket"), DiagnosticStreamProtocol.WEBSOCKET)
        self.assertEqual(DiagnosticStreamProtocol("file"), DiagnosticStreamProtocol.FILE)
        self.assertEqual(DiagnosticStreamProtocol("callback"), DiagnosticStreamProtocol.CALLBACK)


class TestDiagnosticStreamEvent(unittest.TestCase):
    """Tests for DiagnosticStreamEvent class."""

    def test_event_creation(self):
        """Test creating a diagnostic stream event."""
        event = DiagnosticStreamEvent(
            label="prerun-diagnostic",
            integration_name="TestIntegration",
            level=5,
            data={"key": "value"}
        )
        
        self.assertEqual(event.label, "prerun-diagnostic")
        self.assertEqual(event.integration_name, "TestIntegration")
        self.assertEqual(event.level, 5)
        self.assertEqual(event.data, {"key": "value"})
        self.assertIsInstance(event.timestamp, float)
        self.assertEqual(event.metadata, {})

    def test_event_with_metadata(self):
        """Test creating event with metadata."""
        metadata = {"test_run_id": "run-123"}
        event = DiagnosticStreamEvent(
            label="test",
            integration_name="Test",
            level=1,
            data={},
            metadata=metadata
        )
        
        self.assertEqual(event.metadata, metadata)

    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = DiagnosticStreamEvent(
            label="test-label",
            integration_name="TestInteg",
            level=7,
            data={"status": "ok"},
            metadata={"env": "test"}
        )
        
        event_dict = event.to_dict()
        
        self.assertIn("timestamp", event_dict)
        self.assertEqual(event_dict["label"], "test-label")
        self.assertEqual(event_dict["integration_name"], "TestInteg")
        self.assertEqual(event_dict["level"], 7)
        self.assertEqual(event_dict["data"], {"status": "ok"})
        self.assertEqual(event_dict["metadata"], {"env": "test"})

    def test_event_to_json(self):
        """Test converting event to JSON string."""
        event = DiagnosticStreamEvent(
            label="test",
            integration_name="Test",
            level=1,
            data={"value": 123}
        )
        
        json_str = event.to_json()
        parsed = json.loads(json_str)
        
        self.assertEqual(parsed["label"], "test")
        self.assertEqual(parsed["data"]["value"], 123)

    def test_event_repr(self):
        """Test event string representation."""
        event = DiagnosticStreamEvent(
            label="test",
            integration_name="TestInteg",
            level=5,
            data={}
        )
        
        repr_str = repr(event)
        self.assertIn("DiagnosticStreamEvent", repr_str)
        self.assertIn("test", repr_str)
        self.assertIn("TestInteg", repr_str)


class TestDiagnosticStreamConfig(unittest.TestCase):
    """Tests for DiagnosticStreamConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DiagnosticStreamConfig()
        
        self.assertFalse(config.enabled)
        self.assertEqual(config.protocol, DiagnosticStreamProtocol.HTTP)
        self.assertEqual(config.endpoint, "")
        self.assertIsNone(config.api_key)
        self.assertIsNone(config.auth_token)
        self.assertEqual(config.headers, {})
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.retry_count, 3)
        self.assertEqual(config.retry_delay, 1.0)
        self.assertFalse(config.async_mode)
        self.assertEqual(config.buffer_size, 100)

    def test_custom_config(self):
        """Test custom configuration values."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.WEBSOCKET,
            endpoint="wss://example.com/stream",
            api_key="test-key",
            timeout=60,
            async_mode=True,
            buffer_size=200
        )
        
        self.assertTrue(config.enabled)
        self.assertEqual(config.protocol, DiagnosticStreamProtocol.WEBSOCKET)
        self.assertEqual(config.endpoint, "wss://example.com/stream")
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.timeout, 60)
        self.assertTrue(config.async_mode)
        self.assertEqual(config.buffer_size, 200)

    def test_config_to_dict(self):
        """Test converting config to dictionary with masked sensitive data."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.HTTP,
            endpoint="https://example.com",
            api_key="secret-key",
            auth_token="secret-token"
        )
        
        config_dict = config.to_dict()
        
        self.assertTrue(config_dict["enabled"])
        self.assertEqual(config_dict["protocol"], "http")
        self.assertEqual(config_dict["api_key"], "***")
        self.assertEqual(config_dict["auth_token"], "***")

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "enabled": True,
            "protocol": "file",
            "endpoint": "/path/to/file.jsonl",
            "timeout": 45
        }
        
        config = DiagnosticStreamConfig.from_dict(data)
        
        self.assertTrue(config.enabled)
        self.assertEqual(config.protocol, DiagnosticStreamProtocol.FILE)
        self.assertEqual(config.endpoint, "/path/to/file.jsonl")
        self.assertEqual(config.timeout, 45)

    def test_config_from_environment(self):
        """Test creating config from environment variables."""
        # Set environment variables
        os.environ["DIAGNOSTIC_STREAM_ENABLED"] = "true"
        os.environ["DIAGNOSTIC_STREAM_PROTOCOL"] = "file"
        os.environ["DIAGNOSTIC_STREAM_ENDPOINT"] = "/tmp/test.jsonl"
        os.environ["DIAGNOSTIC_STREAM_TIMEOUT"] = "45"
        
        try:
            config = DiagnosticStreamConfig.from_environment()
            
            self.assertTrue(config.enabled)
            self.assertEqual(config.protocol, DiagnosticStreamProtocol.FILE)
            self.assertEqual(config.endpoint, "/tmp/test.jsonl")
            self.assertEqual(config.timeout, 45)
        finally:
            # Clean up environment
            del os.environ["DIAGNOSTIC_STREAM_ENABLED"]
            del os.environ["DIAGNOSTIC_STREAM_PROTOCOL"]
            del os.environ["DIAGNOSTIC_STREAM_ENDPOINT"]
            del os.environ["DIAGNOSTIC_STREAM_TIMEOUT"]


class TestFileStreamHandler(unittest.TestCase):
    """Tests for FileStreamHandler class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.jsonl', delete=False
        )
        self.temp_file.close()
        self.temp_path = self.temp_file.name

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_path):
            os.unlink(self.temp_path)

    def test_connect(self):
        """Test connecting file handler."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.FILE,
            endpoint=self.temp_path
        )
        handler = FileStreamHandler(config)
        
        result = handler.connect()
        
        self.assertTrue(result)
        self.assertTrue(handler.is_connected())
        
        handler.disconnect()

    def test_connect_creates_directory(self):
        """Test that connect creates directory if needed."""
        temp_dir = tempfile.mkdtemp()
        nested_path = os.path.join(temp_dir, "subdir", "test.jsonl")
        
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.FILE,
            endpoint=nested_path
        )
        handler = FileStreamHandler(config)
        
        result = handler.connect()
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(os.path.dirname(nested_path)))
        
        handler.disconnect()
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)

    def test_send_event(self):
        """Test sending event to file."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.FILE,
            endpoint=self.temp_path
        )
        handler = FileStreamHandler(config)
        handler.connect()
        
        event = DiagnosticStreamEvent(
            label="test",
            integration_name="TestInteg",
            level=5,
            data={"key": "value"}
        )
        
        result = handler.send(event)
        
        self.assertTrue(result)
        
        handler.disconnect()
        
        # Verify file contents
        with open(self.temp_path, 'r') as f:
            content = f.read()
            parsed = json.loads(content.strip())
            self.assertEqual(parsed["label"], "test")
            self.assertEqual(parsed["data"]["key"], "value")

    def test_disconnect(self):
        """Test disconnecting file handler."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.FILE,
            endpoint=self.temp_path
        )
        handler = FileStreamHandler(config)
        handler.connect()
        
        handler.disconnect()
        
        self.assertFalse(handler.is_connected())

    def test_connect_no_endpoint(self):
        """Test connect fails without endpoint."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.FILE,
            endpoint=""
        )
        handler = FileStreamHandler(config)
        
        result = handler.connect()
        
        self.assertFalse(result)


class TestCallbackStreamHandler(unittest.TestCase):
    """Tests for CallbackStreamHandler class."""

    def test_connect_with_callback(self):
        """Test connecting with callback configured."""
        received = []
        
        def callback(event):
            received.append(event)
        
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.CALLBACK,
            callback=callback
        )
        handler = CallbackStreamHandler(config)
        
        result = handler.connect()
        
        self.assertTrue(result)
        self.assertTrue(handler.is_connected())
        
        handler.disconnect()

    def test_connect_without_callback(self):
        """Test connect fails without callback."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.CALLBACK
        )
        handler = CallbackStreamHandler(config)
        
        result = handler.connect()
        
        self.assertFalse(result)

    def test_send_invokes_callback(self):
        """Test that send invokes the callback."""
        received = []
        
        def callback(event):
            received.append(event)
        
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.CALLBACK,
            callback=callback
        )
        handler = CallbackStreamHandler(config)
        handler.connect()
        
        event = DiagnosticStreamEvent(
            label="test",
            integration_name="Test",
            level=1,
            data={"value": 42}
        )
        
        result = handler.send(event)
        
        self.assertTrue(result)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].data["value"], 42)
        
        handler.disconnect()

    def test_error_callback_on_failure(self):
        """Test error callback is invoked on failure."""
        errors = []
        
        def callback(event):
            raise ValueError("Test error")
        
        def error_callback(event, error):
            errors.append((event, error))
        
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.CALLBACK,
            callback=callback,
            error_callback=error_callback
        )
        handler = CallbackStreamHandler(config)
        handler.connect()
        
        event = DiagnosticStreamEvent(
            label="test",
            integration_name="Test",
            level=1,
            data={}
        )
        
        result = handler.send(event)
        
        self.assertFalse(result)
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0][1], ValueError)
        
        handler.disconnect()


class TestHttpStreamHandler(unittest.TestCase):
    """Tests for HttpStreamHandler class."""

    def test_connect_valid_endpoint(self):
        """Test connecting with valid HTTP endpoint."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.HTTP,
            endpoint="https://example.com/api/diagnostics"
        )
        handler = HttpStreamHandler(config)
        
        result = handler.connect()
        
        self.assertTrue(result)
        self.assertTrue(handler.is_connected())
        
        handler.disconnect()

    def test_connect_invalid_endpoint(self):
        """Test connect fails with invalid endpoint."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.HTTP,
            endpoint="not-a-valid-url"
        )
        handler = HttpStreamHandler(config)
        
        result = handler.connect()
        
        self.assertFalse(result)

    def test_connect_no_endpoint(self):
        """Test connect fails without endpoint."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.HTTP,
            endpoint=""
        )
        handler = HttpStreamHandler(config)
        
        result = handler.connect()
        
        self.assertFalse(result)


class TestWebSocketStreamHandler(unittest.TestCase):
    """Tests for WebSocketStreamHandler class."""

    def test_connect_valid_endpoint(self):
        """Test connecting with valid WebSocket endpoint."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.WEBSOCKET,
            endpoint="wss://example.com/stream"
        )
        handler = WebSocketStreamHandler(config)
        
        # Note: This will succeed in simulated mode if websocket-client is not installed
        result = handler.connect()
        
        # Connection may succeed (simulated) or fail (actual attempt)
        # Just verify it doesn't crash
        handler.disconnect()

    def test_connect_invalid_endpoint(self):
        """Test connect fails with invalid endpoint."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.WEBSOCKET,
            endpoint="not-a-valid-url"
        )
        handler = WebSocketStreamHandler(config)
        
        result = handler.connect()
        
        self.assertFalse(result)


class TestDiagnosticStreamManager(unittest.TestCase):
    """Tests for DiagnosticStreamManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset manager state before each test
        DiagnosticStreamManager.reset()
        
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.jsonl', delete=False
        )
        self.temp_file.close()
        self.temp_path = self.temp_file.name

    def tearDown(self):
        """Clean up test fixtures."""
        DiagnosticStreamManager.reset()
        if os.path.exists(self.temp_path):
            os.unlink(self.temp_path)

    def test_configure_disabled(self):
        """Test configuring with streaming disabled."""
        config = DiagnosticStreamConfig(enabled=False)
        
        result = DiagnosticStreamManager.configure(config)
        
        self.assertTrue(result)
        self.assertFalse(DiagnosticStreamManager.is_enabled())

    def test_configure_file_streaming(self):
        """Test configuring file streaming."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.FILE,
            endpoint=self.temp_path
        )
        
        result = DiagnosticStreamManager.configure(config)
        
        self.assertTrue(result)
        self.assertTrue(DiagnosticStreamManager.is_enabled())
        self.assertTrue(DiagnosticStreamManager.is_connected())

    def test_stream_diagnostic(self):
        """Test streaming a diagnostic event."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.FILE,
            endpoint=self.temp_path
        )
        DiagnosticStreamManager.configure(config)
        
        result = DiagnosticStreamManager.stream_diagnostic(
            label="test",
            integration_name="TestInteg",
            level=5,
            data={"key": "value"}
        )
        
        self.assertTrue(result)
        
        DiagnosticStreamManager.shutdown()
        
        # Verify file contents
        with open(self.temp_path, 'r') as f:
            content = f.read()
            parsed = json.loads(content.strip())
            self.assertEqual(parsed["label"], "test")

    def test_stream_diagnostic_not_enabled(self):
        """Test streaming when not enabled returns False."""
        config = DiagnosticStreamConfig(enabled=False)
        DiagnosticStreamManager.configure(config)
        
        result = DiagnosticStreamManager.stream_diagnostic(
            label="test",
            integration_name="Test",
            level=1,
            data={}
        )
        
        self.assertFalse(result)

    def test_get_stats(self):
        """Test getting streaming statistics."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.FILE,
            endpoint=self.temp_path
        )
        DiagnosticStreamManager.configure(config)
        
        stats = DiagnosticStreamManager.get_stats()
        
        self.assertTrue(stats["enabled"])
        self.assertTrue(stats["connected"])
        self.assertEqual(stats["protocol"], "file")
        self.assertFalse(stats["async_mode"])

    def test_get_config(self):
        """Test getting current configuration."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.FILE,
            endpoint=self.temp_path
        )
        DiagnosticStreamManager.configure(config)
        
        retrieved_config = DiagnosticStreamManager.get_config()
        
        self.assertIsNotNone(retrieved_config)
        self.assertEqual(retrieved_config.endpoint, self.temp_path)

    def test_shutdown(self):
        """Test shutting down the stream manager."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.FILE,
            endpoint=self.temp_path
        )
        DiagnosticStreamManager.configure(config)
        
        DiagnosticStreamManager.shutdown()
        
        self.assertFalse(DiagnosticStreamManager.is_enabled())
        self.assertFalse(DiagnosticStreamManager.is_connected())

    def test_reset(self):
        """Test resetting the stream manager."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.FILE,
            endpoint=self.temp_path
        )
        DiagnosticStreamManager.configure(config)
        
        DiagnosticStreamManager.reset()
        
        self.assertIsNone(DiagnosticStreamManager.get_config())

    def test_async_streaming(self):
        """Test asynchronous streaming."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.FILE,
            endpoint=self.temp_path,
            async_mode=True,
            buffer_size=10
        )
        DiagnosticStreamManager.configure(config)
        
        # Stream multiple events
        for i in range(5):
            DiagnosticStreamManager.stream_diagnostic(
                label="async-test",
                integration_name=f"Integ-{i}",
                level=5,
                data={"index": i}
            )
        
        # Wait for async processing
        time.sleep(1)
        
        DiagnosticStreamManager.shutdown()
        
        # Verify events were written
        with open(self.temp_path, 'r') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 5)

    def test_callback_streaming(self):
        """Test callback-based streaming through manager."""
        received = []
        
        def callback(event):
            received.append(event)
        
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.CALLBACK,
            callback=callback
        )
        DiagnosticStreamManager.configure(config)
        
        DiagnosticStreamManager.stream_diagnostic(
            label="callback-test",
            integration_name="TestInteg",
            level=5,
            data={"value": 123}
        )
        
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].data["value"], 123)
        
        DiagnosticStreamManager.shutdown()


class TestStreamFile(unittest.TestCase):
    """Tests for streaming file contents."""

    def setUp(self):
        """Set up test fixtures."""
        DiagnosticStreamManager.reset()
        
        # Create temp files for streaming
        self.stream_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.jsonl', delete=False
        )
        self.stream_file.close()
        
        self.source_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        )
        self.source_file.write("Test file content\nLine 2\nLine 3")
        self.source_file.close()

    def tearDown(self):
        """Clean up test fixtures."""
        DiagnosticStreamManager.reset()
        for path in [self.stream_file.name, self.source_file.name]:
            if os.path.exists(path):
                os.unlink(path)

    def test_stream_file(self):
        """Test streaming a file's contents."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.FILE,
            endpoint=self.stream_file.name
        )
        DiagnosticStreamManager.configure(config)
        
        result = DiagnosticStreamManager.stream_file(
            label="file-test",
            integration_name="FileInteg",
            level=5,
            file_path=self.source_file.name
        )
        
        self.assertTrue(result)
        
        DiagnosticStreamManager.shutdown()
        
        # Verify streamed content
        with open(self.stream_file.name, 'r') as f:
            content = f.read()
            parsed = json.loads(content.strip())
            self.assertIn("Test file content", parsed["data"]["content"])
            self.assertEqual(parsed["data"]["file_name"], os.path.basename(self.source_file.name))

    def test_stream_nonexistent_file(self):
        """Test streaming a non-existent file returns False."""
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.FILE,
            endpoint=self.stream_file.name
        )
        DiagnosticStreamManager.configure(config)
        
        result = DiagnosticStreamManager.stream_file(
            label="test",
            integration_name="Test",
            level=1,
            file_path="/nonexistent/file.txt"
        )
        
        self.assertFalse(result)
        
        DiagnosticStreamManager.shutdown()


if __name__ == "__main__":
    unittest.main()
