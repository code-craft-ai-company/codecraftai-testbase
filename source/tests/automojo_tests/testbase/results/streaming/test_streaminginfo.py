"""
    .. module:: automojo_tests.testbase.results.streaming.test_streaminginfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for StreamingInfo configuration.

    This module contains unit tests for the StreamingInfo dataclass and
    related configuration classes.

    .. moduleauthor:: AutomationX
"""

import unittest

from automojo.testbase.results.model.streaminginfo import (
    StreamingInfo,
    StreamingProtocol,
    StreamingCallback
)


class StreamingProtocolTests(unittest.TestCase):
    """Tests for the StreamingProtocol enumeration."""

    def test_rest_protocol_value(self):
        """Test that REST protocol has correct value."""
        self.assertEqual(StreamingProtocol.REST.value, "REST")

    def test_websocket_protocol_value(self):
        """Test that WebSocket protocol has correct value."""
        self.assertEqual(StreamingProtocol.WEBSOCKET.value, "WebSocket")


class StreamingInfoTests(unittest.TestCase):
    """Tests for the StreamingInfo dataclass."""

    def test_rest_streaming_info_creation(self):
        """Test creating StreamingInfo for REST streaming."""
        info = StreamingInfo(
            protocol=StreamingProtocol.REST,
            streaming_url="https://example.com/api/results"
        )
        
        self.assertEqual(info.protocol, StreamingProtocol.REST)
        self.assertEqual(info.streaming_url, "https://example.com/api/results")
        self.assertIsNone(info.streaming_headers)
        self.assertTrue(info.stream_previews)
        self.assertTrue(info.stream_results)

    def test_websocket_streaming_info_creation(self):
        """Test creating StreamingInfo for WebSocket streaming."""
        info = StreamingInfo(
            protocol=StreamingProtocol.WEBSOCKET,
            streaming_url="wss://example.com/ws/results"
        )
        
        self.assertEqual(info.protocol, StreamingProtocol.WEBSOCKET)
        self.assertEqual(info.streaming_url, "wss://example.com/ws/results")

    def test_streaming_info_with_headers(self):
        """Test creating StreamingInfo with custom headers."""
        headers = {
            "Authorization": "Bearer token123",
            "X-Custom-Header": "custom-value"
        }
        
        info = StreamingInfo(
            protocol=StreamingProtocol.REST,
            streaming_url="https://example.com/api/results",
            streaming_headers=headers
        )
        
        self.assertEqual(info.streaming_headers, headers)

    def test_streaming_info_with_custom_options(self):
        """Test creating StreamingInfo with custom options."""
        info = StreamingInfo(
            protocol=StreamingProtocol.WEBSOCKET,
            streaming_url="wss://example.com/ws/results",
            stream_previews=False,
            stream_results=True,
            reconnect_on_failure=True,
            reconnect_interval=10.0,
            batch_size=5,
            batch_timeout=2.0
        )
        
        self.assertFalse(info.stream_previews)
        self.assertTrue(info.stream_results)
        self.assertTrue(info.reconnect_on_failure)
        self.assertEqual(info.reconnect_interval, 10.0)
        self.assertEqual(info.batch_size, 5)
        self.assertEqual(info.batch_timeout, 2.0)

    def test_streaming_info_default_values(self):
        """Test that StreamingInfo has correct default values."""
        info = StreamingInfo(
            protocol=StreamingProtocol.REST,
            streaming_url="https://example.com/api/results"
        )
        
        self.assertIsNone(info.streaming_headers)
        self.assertTrue(info.stream_previews)
        self.assertTrue(info.stream_results)
        self.assertTrue(info.reconnect_on_failure)
        self.assertEqual(info.reconnect_interval, 5.0)
        self.assertEqual(info.batch_size, 1)
        self.assertEqual(info.batch_timeout, 1.0)


class StreamingCallbackTests(unittest.TestCase):
    """Tests for the StreamingCallback dataclass."""

    def test_callback_creation_with_required_fields(self):
        """Test creating StreamingCallback with required fields only."""
        def on_result(result_dict, is_preview):
            return True
        
        callback = StreamingCallback(on_result=on_result)
        
        self.assertIsNotNone(callback.on_result)
        self.assertIsNone(callback.on_error)
        self.assertIsNone(callback.on_connect)
        self.assertIsNone(callback.on_disconnect)

    def test_callback_creation_with_all_fields(self):
        """Test creating StreamingCallback with all fields."""
        def on_result(result_dict, is_preview):
            return True
        
        def on_error(err):
            pass
        
        def on_connect():
            pass
        
        def on_disconnect():
            pass
        
        callback = StreamingCallback(
            on_result=on_result,
            on_error=on_error,
            on_connect=on_connect,
            on_disconnect=on_disconnect
        )
        
        self.assertIsNotNone(callback.on_result)
        self.assertIsNotNone(callback.on_error)
        self.assertIsNotNone(callback.on_connect)
        self.assertIsNotNone(callback.on_disconnect)

    def test_callback_on_result_invocation(self):
        """Test that on_result callback can be invoked."""
        results_received = []
        
        def on_result(result_dict, is_preview):
            results_received.append((result_dict, is_preview))
            return True
        
        callback = StreamingCallback(on_result=on_result)
        
        # Invoke the callback
        result = callback.on_result({"name": "test"}, True)
        
        self.assertTrue(result)
        self.assertEqual(len(results_received), 1)
        self.assertEqual(results_received[0], ({"name": "test"}, True))


if __name__ == "__main__":
    unittest.main()
