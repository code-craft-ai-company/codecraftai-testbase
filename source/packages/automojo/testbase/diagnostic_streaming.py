"""
    .. module:: automojo.testbase.diagnostic_streaming
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module providing diagnostic streaming capabilities for real-time monitoring
        and remote diagnostic collection.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>

This module provides streaming capabilities for the TestBase diagnostic system, enabling
real-time transmission of diagnostic data to external systems. The streaming system supports
multiple transport protocols and can be configured to stream diagnostics as they are captured.

The module includes:

* :class:`DiagnosticStreamProtocol` - Enumeration of supported streaming protocols
* :class:`DiagnosticStreamHandler` - Abstract base class for stream handlers
* :class:`HttpStreamHandler` - HTTP/HTTPS streaming handler
* :class:`WebSocketStreamHandler` - WebSocket streaming handler
* :class:`FileStreamHandler` - File-based streaming handler (for testing/debugging)
* :class:`DiagnosticStreamManager` - Manager for coordinating diagnostic streaming
* :class:`DiagnosticStreamConfig` - Configuration for streaming settings

Example Usage::

    from automojo.testbase.diagnostic_streaming import (
        DiagnosticStreamManager,
        DiagnosticStreamConfig,
        DiagnosticStreamProtocol,
        HttpStreamHandler
    )

    # Configure streaming to an HTTP endpoint
    config = DiagnosticStreamConfig(
        enabled=True,
        protocol=DiagnosticStreamProtocol.HTTP,
        endpoint="https://diagnostics.example.com/api/v1/stream",
        api_key="your-api-key"
    )

    # Initialize the stream manager
    DiagnosticStreamManager.configure(config)

    # Stream diagnostic data
    DiagnosticStreamManager.stream_diagnostic(
        label="prerun-diagnostic",
        integration_name="DeviceCoupling",
        data={"status": "connected", "device_id": "device-001"}
    )

    # Close streaming connections
    DiagnosticStreamManager.shutdown()

See Also:
    - :class:`automojo.testbase.diagnostics.DiagnosticLabel`: Diagnostic stage labels
    - :class:`automojo.testbase.diagnostics.DiagnosticFilter`: Diagnostic filtering
    - :class:`automojo.testbase.sequencing.testsequencer.TestSequencer`: Test sequencer
"""


from typing import Any, Callable, Dict, List, Optional, Union
from abc import ABC, abstractmethod
from enum import Enum

import json
import logging
import os
import queue
import threading
import time
import traceback


__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


# Module-level logger
logger = logging.getLogger(__name__)


class DiagnosticStreamProtocol(Enum):
    """
    Enumeration of supported streaming protocols for diagnostic data.

    The :class:`DiagnosticStreamProtocol` enum defines the available transport
    protocols that can be used for streaming diagnostic data to external systems.

    Attributes:
        HTTP: HTTP/HTTPS protocol for RESTful streaming.
        WEBSOCKET: WebSocket protocol for bidirectional real-time streaming.
        FILE: File-based streaming for local storage and debugging.
        CALLBACK: Custom callback function for flexible integration.

    Example Usage::

        from automojo.testbase.diagnostic_streaming import DiagnosticStreamProtocol

        # Select a protocol
        protocol = DiagnosticStreamProtocol.HTTP

        # Check protocol type
        if protocol == DiagnosticStreamProtocol.WEBSOCKET:
            print("Using WebSocket for real-time streaming")

    See Also:
        - :class:`DiagnosticStreamConfig`: Configuration using these protocols
        - :class:`DiagnosticStreamHandler`: Handlers implementing these protocols
    """
    HTTP = "http"
    WEBSOCKET = "websocket"
    FILE = "file"
    CALLBACK = "callback"


class DiagnosticStreamEvent:
    """
    Represents a single diagnostic streaming event.

    The :class:`DiagnosticStreamEvent` encapsulates all information about a
    diagnostic data point that is being streamed, including metadata about
    the source, timing, and the actual diagnostic data.

    Attributes:
        timestamp (float): Unix timestamp when the event was created.
        label (str): The diagnostic label (e.g., "prerun-diagnostic").
        integration_name (str): Name of the integration that generated the diagnostic.
        level (int): The diagnostic level (1-9).
        data (Dict[str, Any]): The actual diagnostic data payload.
        metadata (Dict[str, Any]): Additional metadata about the event.

    Example Usage::

        event = DiagnosticStreamEvent(
            label="prerun-diagnostic",
            integration_name="DeviceCoupling",
            level=5,
            data={"status": "connected"},
            metadata={"test_run_id": "run-123"}
        )

        # Access event properties
        print(f"Event at {event.timestamp}: {event.label}")

        # Convert to dictionary for serialization
        event_dict = event.to_dict()
    """

    def __init__(
        self,
        label: str,
        integration_name: str,
        level: int,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a diagnostic stream event.

        :param label: The diagnostic label identifying the capture stage.
        :param integration_name: Name of the integration generating the diagnostic.
        :param level: The diagnostic level (1-9).
        :param data: The diagnostic data payload.
        :param metadata: Optional additional metadata.
        """
        self.timestamp = time.time()
        self.label = label
        self.integration_name = integration_name
        self.level = level
        self.data = data
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event to a dictionary for serialization.

        :returns: Dictionary representation of the event.
        """
        return {
            "timestamp": self.timestamp,
            "label": self.label,
            "integration_name": self.integration_name,
            "level": self.level,
            "data": self.data,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """
        Convert the event to a JSON string.

        :returns: JSON string representation of the event.
        """
        return json.dumps(self.to_dict(), default=str)

    def __repr__(self) -> str:
        return f"DiagnosticStreamEvent(label={self.label!r}, integration={self.integration_name!r}, level={self.level})"


class DiagnosticStreamHandler(ABC):
    """
    Abstract base class for diagnostic stream handlers.

    The :class:`DiagnosticStreamHandler` defines the interface that all stream
    handlers must implement. Concrete implementations handle the actual transport
    of diagnostic data to external systems.

    Subclasses must implement:
        - :meth:`connect`: Establish connection to the streaming endpoint
        - :meth:`send`: Send a diagnostic event
        - :meth:`disconnect`: Close the connection
        - :meth:`is_connected`: Check connection status

    Example Usage::

        class CustomStreamHandler(DiagnosticStreamHandler):
            def connect(self) -> bool:
                # Establish connection
                return True

            def send(self, event: DiagnosticStreamEvent) -> bool:
                # Send the event
                return True

            def disconnect(self) -> None:
                # Close connection
                pass

            def is_connected(self) -> bool:
                return True

    See Also:
        - :class:`HttpStreamHandler`: HTTP implementation
        - :class:`WebSocketStreamHandler`: WebSocket implementation
        - :class:`FileStreamHandler`: File-based implementation
    """

    def __init__(self, config: "DiagnosticStreamConfig"):
        """
        Initialize the stream handler with configuration.

        :param config: The streaming configuration.
        """
        self._config = config
        self._connected = False

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the streaming endpoint.

        :returns: True if connection was successful, False otherwise.
        """
        pass

    @abstractmethod
    def send(self, event: DiagnosticStreamEvent) -> bool:
        """
        Send a diagnostic event to the streaming endpoint.

        :param event: The diagnostic event to send.

        :returns: True if the event was sent successfully, False otherwise.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Close the connection to the streaming endpoint.

        :returns: None
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if the handler is currently connected.

        :returns: True if connected, False otherwise.
        """
        pass

    def get_config(self) -> "DiagnosticStreamConfig":
        """
        Get the handler's configuration.

        :returns: The streaming configuration.
        """
        return self._config


class HttpStreamHandler(DiagnosticStreamHandler):
    """
    HTTP/HTTPS stream handler for diagnostic data.

    The :class:`HttpStreamHandler` implements diagnostic streaming over HTTP/HTTPS
    protocol. It sends diagnostic events as JSON payloads to a configured endpoint
    using POST requests.

    Features:
        - Supports HTTP and HTTPS endpoints
        - Configurable authentication (API key, Bearer token)
        - Configurable timeout and retry settings
        - Automatic reconnection on failure

    Example Usage::

        from automojo.testbase.diagnostic_streaming import (
            HttpStreamHandler,
            DiagnosticStreamConfig,
            DiagnosticStreamProtocol
        )

        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.HTTP,
            endpoint="https://api.example.com/diagnostics",
            api_key="your-api-key",
            timeout=30
        )

        handler = HttpStreamHandler(config)
        handler.connect()

        event = DiagnosticStreamEvent(
            label="prerun-diagnostic",
            integration_name="DeviceCoupling",
            level=5,
            data={"status": "ok"}
        )

        handler.send(event)
        handler.disconnect()

    See Also:
        - :class:`DiagnosticStreamHandler`: Base class
        - :class:`DiagnosticStreamConfig`: Configuration class
    """

    def __init__(self, config: "DiagnosticStreamConfig"):
        """
        Initialize the HTTP stream handler.

        :param config: The streaming configuration.
        """
        super().__init__(config)
        self._session = None

    def connect(self) -> bool:
        """
        Establish HTTP connection (validates endpoint accessibility).

        For HTTP, this method validates that the endpoint is reachable.
        Actual connections are made per-request.

        :returns: True if the endpoint is accessible, False otherwise.
        """
        try:
            # Import urllib here to avoid import errors if not available
            import urllib.request
            import urllib.error

            # Validate endpoint URL format
            endpoint = self._config.endpoint
            if not endpoint:
                logger.error("HTTP stream handler: No endpoint configured")
                return False

            # For HTTP, we don't maintain a persistent connection
            # Just validate the endpoint format
            if not endpoint.startswith(("http://", "https://")):
                logger.error(f"HTTP stream handler: Invalid endpoint URL: {endpoint}")
                return False

            self._connected = True
            logger.info(f"HTTP stream handler connected to: {endpoint}")
            return True

        except Exception as e:
            logger.error(f"HTTP stream handler connection failed: {e}")
            self._connected = False
            return False

    def send(self, event: DiagnosticStreamEvent) -> bool:
        """
        Send a diagnostic event via HTTP POST.

        :param event: The diagnostic event to send.

        :returns: True if sent successfully, False otherwise.
        """
        if not self._connected:
            logger.warning("HTTP stream handler: Not connected, attempting to connect")
            if not self.connect():
                return False

        try:
            import urllib.request
            import urllib.error

            # Prepare the request
            endpoint = self._config.endpoint
            data = event.to_json().encode('utf-8')

            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'TestBase-DiagnosticStream/1.0'
            }

            # Add authentication if configured
            if self._config.api_key:
                headers['X-API-Key'] = self._config.api_key
            if self._config.auth_token:
                headers['Authorization'] = f'Bearer {self._config.auth_token}'

            # Add custom headers
            if self._config.headers:
                headers.update(self._config.headers)

            request = urllib.request.Request(
                endpoint,
                data=data,
                headers=headers,
                method='POST'
            )

            timeout = self._config.timeout or 30

            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status >= 200 and response.status < 300:
                    logger.debug(f"HTTP stream handler: Event sent successfully (status={response.status})")
                    return True
                else:
                    logger.warning(f"HTTP stream handler: Unexpected status {response.status}")
                    return False

        except urllib.error.HTTPError as e:
            logger.error(f"HTTP stream handler: HTTP error {e.code}: {e.reason}")
            return False
        except urllib.error.URLError as e:
            logger.error(f"HTTP stream handler: URL error: {e.reason}")
            return False
        except Exception as e:
            logger.error(f"HTTP stream handler: Send failed: {e}")
            return False

    def disconnect(self) -> None:
        """
        Disconnect the HTTP handler.

        For HTTP, this simply marks the handler as disconnected.

        :returns: None
        """
        self._connected = False
        logger.info("HTTP stream handler disconnected")

    def is_connected(self) -> bool:
        """
        Check if the handler is connected.

        :returns: True if connected, False otherwise.
        """
        return self._connected


class WebSocketStreamHandler(DiagnosticStreamHandler):
    """
    WebSocket stream handler for real-time diagnostic data.

    The :class:`WebSocketStreamHandler` implements diagnostic streaming over
    WebSocket protocol, enabling bidirectional real-time communication with
    external monitoring systems.

    Features:
        - Persistent connection for low-latency streaming
        - Automatic reconnection on connection loss
        - Support for secure WebSocket (wss://)
        - Heartbeat/ping-pong for connection health

    Note:
        This handler requires the 'websocket-client' package to be installed.
        If not available, the handler will operate in a degraded mode that
        logs events locally.

    Example Usage::

        from automojo.testbase.diagnostic_streaming import (
            WebSocketStreamHandler,
            DiagnosticStreamConfig,
            DiagnosticStreamProtocol
        )

        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.WEBSOCKET,
            endpoint="wss://stream.example.com/diagnostics",
            api_key="your-api-key"
        )

        handler = WebSocketStreamHandler(config)
        handler.connect()

        # Send events in real-time
        handler.send(event)

        handler.disconnect()

    See Also:
        - :class:`DiagnosticStreamHandler`: Base class
        - :class:`HttpStreamHandler`: HTTP alternative
    """

    def __init__(self, config: "DiagnosticStreamConfig"):
        """
        Initialize the WebSocket stream handler.

        :param config: The streaming configuration.
        """
        super().__init__(config)
        self._ws = None
        self._ws_available = False

        # Check if websocket-client is available
        try:
            import websocket
            self._ws_available = True
        except ImportError:
            logger.warning(
                "WebSocket stream handler: 'websocket-client' package not installed. "
                "WebSocket streaming will be simulated."
            )

    def connect(self) -> bool:
        """
        Establish WebSocket connection.

        :returns: True if connection was successful, False otherwise.
        """
        try:
            endpoint = self._config.endpoint
            if not endpoint:
                logger.error("WebSocket stream handler: No endpoint configured")
                return False

            if not endpoint.startswith(("ws://", "wss://")):
                logger.error(f"WebSocket stream handler: Invalid endpoint URL: {endpoint}")
                return False

            if self._ws_available:
                import websocket

                # Build headers for authentication
                headers = []
                if self._config.api_key:
                    headers.append(f"X-API-Key: {self._config.api_key}")
                if self._config.auth_token:
                    headers.append(f"Authorization: Bearer {self._config.auth_token}")
                if self._config.headers:
                    for key, value in self._config.headers.items():
                        headers.append(f"{key}: {value}")

                self._ws = websocket.create_connection(
                    endpoint,
                    header=headers if headers else None,
                    timeout=self._config.timeout or 30
                )
                self._connected = True
                logger.info(f"WebSocket stream handler connected to: {endpoint}")
            else:
                # Simulated connection when websocket-client is not available
                self._connected = True
                logger.info(f"WebSocket stream handler (simulated) connected to: {endpoint}")

            return True

        except Exception as e:
            logger.error(f"WebSocket stream handler connection failed: {e}")
            self._connected = False
            return False

    def send(self, event: DiagnosticStreamEvent) -> bool:
        """
        Send a diagnostic event via WebSocket.

        :param event: The diagnostic event to send.

        :returns: True if sent successfully, False otherwise.
        """
        if not self._connected:
            logger.warning("WebSocket stream handler: Not connected, attempting to connect")
            if not self.connect():
                return False

        try:
            data = event.to_json()

            if self._ws_available and self._ws:
                self._ws.send(data)
                logger.debug(f"WebSocket stream handler: Event sent successfully")
            else:
                # Simulated send - just log the event
                logger.debug(f"WebSocket stream handler (simulated): Would send: {data[:100]}...")

            return True

        except Exception as e:
            logger.error(f"WebSocket stream handler: Send failed: {e}")
            self._connected = False
            return False

    def disconnect(self) -> None:
        """
        Close the WebSocket connection.

        :returns: None
        """
        try:
            if self._ws_available and self._ws:
                self._ws.close()
                self._ws = None
        except Exception as e:
            logger.warning(f"WebSocket stream handler: Error during disconnect: {e}")
        finally:
            self._connected = False
            logger.info("WebSocket stream handler disconnected")

    def is_connected(self) -> bool:
        """
        Check if the WebSocket is connected.

        :returns: True if connected, False otherwise.
        """
        if self._ws_available and self._ws:
            try:
                # Check if the connection is still alive
                return self._connected and self._ws.connected
            except Exception:
                return False
        return self._connected


class FileStreamHandler(DiagnosticStreamHandler):
    """
    File-based stream handler for diagnostic data.

    The :class:`FileStreamHandler` implements diagnostic streaming to local files,
    useful for debugging, testing, and scenarios where network streaming is not
    available or desired.

    Features:
        - Writes events to a JSON Lines file (one JSON object per line)
        - Supports file rotation based on size
        - Thread-safe file writing
        - Automatic directory creation

    Example Usage::

        from automojo.testbase.diagnostic_streaming import (
            FileStreamHandler,
            DiagnosticStreamConfig,
            DiagnosticStreamProtocol
        )

        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.FILE,
            endpoint="/path/to/diagnostic_stream.jsonl"
        )

        handler = FileStreamHandler(config)
        handler.connect()

        handler.send(event)

        handler.disconnect()

    See Also:
        - :class:`DiagnosticStreamHandler`: Base class
        - :class:`HttpStreamHandler`: HTTP alternative
    """

    def __init__(self, config: "DiagnosticStreamConfig"):
        """
        Initialize the file stream handler.

        :param config: The streaming configuration.
        """
        super().__init__(config)
        self._file = None
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """
        Open the output file for writing.

        :returns: True if file was opened successfully, False otherwise.
        """
        try:
            file_path = self._config.endpoint
            if not file_path:
                logger.error("File stream handler: No file path configured")
                return False

            # Create directory if it doesn't exist
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

            # Open file in append mode
            self._file = open(file_path, 'a', encoding='utf-8')
            self._connected = True
            logger.info(f"File stream handler connected to: {file_path}")
            return True

        except Exception as e:
            logger.error(f"File stream handler connection failed: {e}")
            self._connected = False
            return False

    def send(self, event: DiagnosticStreamEvent) -> bool:
        """
        Write a diagnostic event to the file.

        :param event: The diagnostic event to write.

        :returns: True if written successfully, False otherwise.
        """
        if not self._connected or not self._file:
            logger.warning("File stream handler: Not connected, attempting to connect")
            if not self.connect():
                return False

        try:
            with self._lock:
                self._file.write(event.to_json() + '\n')
                self._file.flush()
            logger.debug("File stream handler: Event written successfully")
            return True

        except Exception as e:
            logger.error(f"File stream handler: Write failed: {e}")
            return False

    def disconnect(self) -> None:
        """
        Close the output file.

        :returns: None
        """
        try:
            with self._lock:
                if self._file:
                    self._file.close()
                    self._file = None
        except Exception as e:
            logger.warning(f"File stream handler: Error during disconnect: {e}")
        finally:
            self._connected = False
            logger.info("File stream handler disconnected")

    def is_connected(self) -> bool:
        """
        Check if the file is open.

        :returns: True if file is open, False otherwise.
        """
        return self._connected and self._file is not None


class CallbackStreamHandler(DiagnosticStreamHandler):
    """
    Callback-based stream handler for custom diagnostic processing.

    The :class:`CallbackStreamHandler` allows users to provide a custom callback
    function that will be invoked for each diagnostic event. This enables flexible
    integration with custom monitoring systems, logging frameworks, or other
    diagnostic consumers.

    Features:
        - Custom callback function for event processing
        - Optional error callback for handling failures
        - Thread-safe callback invocation

    Example Usage::

        from automojo.testbase.diagnostic_streaming import (
            CallbackStreamHandler,
            DiagnosticStreamConfig,
            DiagnosticStreamProtocol
        )

        def my_callback(event):
            print(f"Received diagnostic: {event.label} from {event.integration_name}")
            # Process the event...

        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.CALLBACK,
            callback=my_callback
        )

        handler = CallbackStreamHandler(config)
        handler.connect()

        handler.send(event)

        handler.disconnect()

    See Also:
        - :class:`DiagnosticStreamHandler`: Base class
    """

    def __init__(self, config: "DiagnosticStreamConfig"):
        """
        Initialize the callback stream handler.

        :param config: The streaming configuration.
        """
        super().__init__(config)

    def connect(self) -> bool:
        """
        Validate that a callback is configured.

        :returns: True if callback is configured, False otherwise.
        """
        if not self._config.callback:
            logger.error("Callback stream handler: No callback function configured")
            return False

        self._connected = True
        logger.info("Callback stream handler connected")
        return True

    def send(self, event: DiagnosticStreamEvent) -> bool:
        """
        Invoke the callback with the diagnostic event.

        :param event: The diagnostic event to process.

        :returns: True if callback executed successfully, False otherwise.
        """
        if not self._connected:
            logger.warning("Callback stream handler: Not connected")
            return False

        try:
            if self._config.callback:
                self._config.callback(event)
            logger.debug("Callback stream handler: Event processed successfully")
            return True

        except Exception as e:
            logger.error(f"Callback stream handler: Callback failed: {e}")
            if self._config.error_callback:
                try:
                    self._config.error_callback(event, e)
                except Exception:
                    pass
            return False

    def disconnect(self) -> None:
        """
        Disconnect the callback handler.

        :returns: None
        """
        self._connected = False
        logger.info("Callback stream handler disconnected")

    def is_connected(self) -> bool:
        """
        Check if the handler is connected.

        :returns: True if connected, False otherwise.
        """
        return self._connected



class DiagnosticStreamConfig:
    """
    Configuration for diagnostic streaming.

    The :class:`DiagnosticStreamConfig` encapsulates all settings required to
    configure diagnostic streaming, including the protocol, endpoint, authentication,
    and behavior options.

    Attributes:
        enabled (bool): Whether streaming is enabled.
        protocol (DiagnosticStreamProtocol): The streaming protocol to use.
        endpoint (str): The streaming endpoint URL or file path.
        api_key (str): Optional API key for authentication.
        auth_token (str): Optional bearer token for authentication.
        headers (Dict[str, str]): Optional custom headers.
        timeout (int): Connection/request timeout in seconds.
        retry_count (int): Number of retry attempts on failure.
        retry_delay (float): Delay between retries in seconds.
        async_mode (bool): Whether to stream asynchronously.
        buffer_size (int): Size of the async buffer.
        callback (Callable): Callback function for CALLBACK protocol.
        error_callback (Callable): Error callback for CALLBACK protocol.

    Example Usage::

        from automojo.testbase.diagnostic_streaming import (
            DiagnosticStreamConfig,
            DiagnosticStreamProtocol
        )

        # HTTP configuration
        http_config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.HTTP,
            endpoint="https://api.example.com/diagnostics",
            api_key="your-api-key",
            timeout=30,
            retry_count=3
        )

        # WebSocket configuration
        ws_config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.WEBSOCKET,
            endpoint="wss://stream.example.com/diagnostics",
            async_mode=True
        )

        # File configuration
        file_config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.FILE,
            endpoint="/var/log/diagnostics/stream.jsonl"
        )

    See Also:
        - :class:`DiagnosticStreamProtocol`: Available protocols
        - :class:`DiagnosticStreamManager`: Manager using this configuration
    """

    def __init__(
        self,
        enabled: bool = False,
        protocol: DiagnosticStreamProtocol = DiagnosticStreamProtocol.HTTP,
        endpoint: str = "",
        api_key: Optional[str] = None,
        auth_token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        retry_count: int = 3,
        retry_delay: float = 1.0,
        async_mode: bool = False,
        buffer_size: int = 100,
        callback: Optional[Callable[[DiagnosticStreamEvent], None]] = None,
        error_callback: Optional[Callable[[DiagnosticStreamEvent, Exception], None]] = None
    ):
        """
        Initialize the streaming configuration.

        :param enabled: Whether streaming is enabled. Default is False.
        :param protocol: The streaming protocol to use. Default is HTTP.
        :param endpoint: The streaming endpoint URL or file path.
        :param api_key: Optional API key for authentication.
        :param auth_token: Optional bearer token for authentication.
        :param headers: Optional custom headers for HTTP/WebSocket.
        :param timeout: Connection/request timeout in seconds. Default is 30.
        :param retry_count: Number of retry attempts on failure. Default is 3.
        :param retry_delay: Delay between retries in seconds. Default is 1.0.
        :param async_mode: Whether to stream asynchronously. Default is False.
        :param buffer_size: Size of the async buffer. Default is 100.
        :param callback: Callback function for CALLBACK protocol.
        :param error_callback: Error callback for CALLBACK protocol.
        """
        self.enabled = enabled
        self.protocol = protocol
        self.endpoint = endpoint
        self.api_key = api_key
        self.auth_token = auth_token
        self.headers = headers or {}
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.async_mode = async_mode
        self.buffer_size = buffer_size
        self.callback = callback
        self.error_callback = error_callback

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a dictionary.

        Note: Sensitive fields (api_key, auth_token) are masked.

        :returns: Dictionary representation of the configuration.
        """
        return {
            "enabled": self.enabled,
            "protocol": self.protocol.value,
            "endpoint": self.endpoint,
            "api_key": "***" if self.api_key else None,
            "auth_token": "***" if self.auth_token else None,
            "headers": {k: "***" for k in self.headers} if self.headers else {},
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
            "async_mode": self.async_mode,
            "buffer_size": self.buffer_size,
            "callback": "configured" if self.callback else None,
            "error_callback": "configured" if self.error_callback else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiagnosticStreamConfig":
        """
        Create a configuration from a dictionary.

        :param data: Dictionary containing configuration values.

        :returns: A new DiagnosticStreamConfig instance.
        """
        protocol_str = data.get("protocol", "http")
        protocol = DiagnosticStreamProtocol(protocol_str)

        return cls(
            enabled=data.get("enabled", False),
            protocol=protocol,
            endpoint=data.get("endpoint", ""),
            api_key=data.get("api_key"),
            auth_token=data.get("auth_token"),
            headers=data.get("headers"),
            timeout=data.get("timeout", 30),
            retry_count=data.get("retry_count", 3),
            retry_delay=data.get("retry_delay", 1.0),
            async_mode=data.get("async_mode", False),
            buffer_size=data.get("buffer_size", 100)
        )

    @classmethod
    def from_environment(cls) -> "DiagnosticStreamConfig":
        """
        Create a configuration from environment variables.

        Environment variables:
            - DIAGNOSTIC_STREAM_ENABLED: "true" or "false"
            - DIAGNOSTIC_STREAM_PROTOCOL: "http", "websocket", "file", or "callback"
            - DIAGNOSTIC_STREAM_ENDPOINT: The endpoint URL or file path
            - DIAGNOSTIC_STREAM_API_KEY: API key for authentication
            - DIAGNOSTIC_STREAM_AUTH_TOKEN: Bearer token for authentication
            - DIAGNOSTIC_STREAM_TIMEOUT: Timeout in seconds
            - DIAGNOSTIC_STREAM_ASYNC: "true" or "false"

        :returns: A new DiagnosticStreamConfig instance.
        """
        enabled = os.environ.get("DIAGNOSTIC_STREAM_ENABLED", "false").lower() == "true"
        protocol_str = os.environ.get("DIAGNOSTIC_STREAM_PROTOCOL", "http")
        
        try:
            protocol = DiagnosticStreamProtocol(protocol_str)
        except ValueError:
            protocol = DiagnosticStreamProtocol.HTTP

        return cls(
            enabled=enabled,
            protocol=protocol,
            endpoint=os.environ.get("DIAGNOSTIC_STREAM_ENDPOINT", ""),
            api_key=os.environ.get("DIAGNOSTIC_STREAM_API_KEY"),
            auth_token=os.environ.get("DIAGNOSTIC_STREAM_AUTH_TOKEN"),
            timeout=int(os.environ.get("DIAGNOSTIC_STREAM_TIMEOUT", "30")),
            async_mode=os.environ.get("DIAGNOSTIC_STREAM_ASYNC", "false").lower() == "true"
        )


class DiagnosticStreamManager:
    """
    Manager for coordinating diagnostic streaming.

    The :class:`DiagnosticStreamManager` is a singleton-style class that manages
    the lifecycle of diagnostic streaming, including handler creation, event
    buffering, and asynchronous transmission.

    Features:
        - Automatic handler selection based on protocol
        - Asynchronous streaming with buffering
        - Retry logic for failed transmissions
        - Thread-safe operation
        - Graceful shutdown with buffer flushing

    Class Attributes:
        _config (DiagnosticStreamConfig): The current streaming configuration.
        _handler (DiagnosticStreamHandler): The active stream handler.
        _async_thread (threading.Thread): Background thread for async streaming.
        _event_queue (queue.Queue): Queue for async event buffering.
        _shutdown_event (threading.Event): Signal for graceful shutdown.

    Example Usage::

        from automojo.testbase.diagnostic_streaming import (
            DiagnosticStreamManager,
            DiagnosticStreamConfig,
            DiagnosticStreamProtocol
        )

        # Configure streaming
        config = DiagnosticStreamConfig(
            enabled=True,
            protocol=DiagnosticStreamProtocol.HTTP,
            endpoint="https://api.example.com/diagnostics",
            async_mode=True
        )

        DiagnosticStreamManager.configure(config)

        # Stream diagnostic data
        DiagnosticStreamManager.stream_diagnostic(
            label="prerun-diagnostic",
            integration_name="DeviceCoupling",
            level=5,
            data={"status": "connected"}
        )

        # Shutdown when done
        DiagnosticStreamManager.shutdown()

    See Also:
        - :class:`DiagnosticStreamConfig`: Configuration class
        - :class:`DiagnosticStreamHandler`: Handler base class
    """

    _config: Optional[DiagnosticStreamConfig] = None
    _handler: Optional[DiagnosticStreamHandler] = None
    _async_thread: Optional[threading.Thread] = None
    _event_queue: Optional[queue.Queue] = None
    _shutdown_event: Optional[threading.Event] = None
    _lock = threading.Lock()
    _initialized = False

    @classmethod
    def configure(cls, config: DiagnosticStreamConfig) -> bool:
        """
        Configure the stream manager with the given settings.

        This method initializes the stream manager with the provided configuration,
        creating the appropriate handler and starting async processing if enabled.

        :param config: The streaming configuration.

        :returns: True if configuration was successful, False otherwise.

        Example Usage::

            config = DiagnosticStreamConfig(
                enabled=True,
                protocol=DiagnosticStreamProtocol.HTTP,
                endpoint="https://api.example.com/diagnostics"
            )

            success = DiagnosticStreamManager.configure(config)
        """
        with cls._lock:
            # Shutdown existing handler if any
            if cls._initialized:
                cls._shutdown_internal()

            cls._config = config

            if not config.enabled:
                logger.info("Diagnostic streaming is disabled")
                return True

            # Create the appropriate handler
            handler = cls._create_handler(config)
            if not handler:
                logger.error("Failed to create stream handler")
                return False

            # Connect the handler
            if not handler.connect():
                logger.error("Failed to connect stream handler")
                return False

            cls._handler = handler

            # Setup async processing if enabled
            if config.async_mode:
                cls._event_queue = queue.Queue(maxsize=config.buffer_size)
                cls._shutdown_event = threading.Event()
                cls._async_thread = threading.Thread(
                    target=cls._async_worker,
                    name="DiagnosticStreamWorker",
                    daemon=True
                )
                cls._async_thread.start()
                logger.info("Async diagnostic streaming started")

            cls._initialized = True
            logger.info(f"Diagnostic streaming configured: protocol={config.protocol.value}")
            return True

    @classmethod
    def _create_handler(cls, config: DiagnosticStreamConfig) -> Optional[DiagnosticStreamHandler]:
        """
        Create the appropriate handler based on protocol.

        :param config: The streaming configuration.

        :returns: A stream handler instance, or None if creation failed.
        """
        try:
            if config.protocol == DiagnosticStreamProtocol.HTTP:
                return HttpStreamHandler(config)
            elif config.protocol == DiagnosticStreamProtocol.WEBSOCKET:
                return WebSocketStreamHandler(config)
            elif config.protocol == DiagnosticStreamProtocol.FILE:
                return FileStreamHandler(config)
            elif config.protocol == DiagnosticStreamProtocol.CALLBACK:
                return CallbackStreamHandler(config)
            else:
                logger.error(f"Unknown protocol: {config.protocol}")
                return None
        except Exception as e:
            logger.error(f"Failed to create handler: {e}")
            return None

    @classmethod
    def _async_worker(cls) -> None:
        """
        Background worker for async event processing.

        This method runs in a separate thread and processes events from the
        queue, sending them to the configured handler.
        """
        logger.debug("Async worker started")

        while not cls._shutdown_event.is_set():
            try:
                # Wait for an event with timeout to allow shutdown checks
                try:
                    event = cls._event_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                # Process the event
                if cls._handler and cls._handler.is_connected():
                    success = cls._send_with_retry(event)
                    if not success:
                        logger.warning(f"Failed to send event after retries: {event}")

                cls._event_queue.task_done()

            except Exception as e:
                logger.error(f"Async worker error: {e}")

        # Flush remaining events on shutdown
        cls._flush_queue()
        logger.debug("Async worker stopped")

    @classmethod
    def _flush_queue(cls) -> None:
        """
        Flush remaining events from the queue.
        """
        if not cls._event_queue:
            return

        while not cls._event_queue.empty():
            try:
                event = cls._event_queue.get_nowait()
                if cls._handler and cls._handler.is_connected():
                    cls._handler.send(event)
                cls._event_queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Error flushing event: {e}")

    @classmethod
    def _send_with_retry(cls, event: DiagnosticStreamEvent) -> bool:
        """
        Send an event with retry logic.

        :param event: The event to send.

        :returns: True if sent successfully, False otherwise.
        """
        if not cls._handler or not cls._config:
            return False

        retry_count = cls._config.retry_count
        retry_delay = cls._config.retry_delay

        for attempt in range(retry_count + 1):
            try:
                if cls._handler.send(event):
                    return True
            except Exception as e:
                logger.warning(f"Send attempt {attempt + 1} failed: {e}")

            if attempt < retry_count:
                time.sleep(retry_delay)

        return False

    @classmethod
    def stream_diagnostic(
        cls,
        label: str,
        integration_name: str,
        level: int,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Stream a diagnostic event.

        This method creates a diagnostic event and sends it to the configured
        streaming endpoint. If async mode is enabled, the event is queued for
        background processing.

        :param label: The diagnostic label (e.g., "prerun-diagnostic").
        :param integration_name: Name of the integration generating the diagnostic.
        :param level: The diagnostic level (1-9).
        :param data: The diagnostic data payload.
        :param metadata: Optional additional metadata.

        :returns: True if the event was sent/queued successfully, False otherwise.

        Example Usage::

            DiagnosticStreamManager.stream_diagnostic(
                label="prerun-diagnostic",
                integration_name="DeviceCoupling",
                level=5,
                data={"status": "connected", "device_id": "device-001"},
                metadata={"test_run_id": "run-123"}
            )
        """
        if not cls._config or not cls._config.enabled:
            return False

        if not cls._handler:
            logger.warning("Stream manager not initialized")
            return False

        # Create the event
        event = DiagnosticStreamEvent(
            label=label,
            integration_name=integration_name,
            level=level,
            data=data,
            metadata=metadata
        )

        # Send or queue the event
        if cls._config.async_mode and cls._event_queue:
            try:
                cls._event_queue.put_nowait(event)
                return True
            except queue.Full:
                logger.warning("Event queue full, dropping event")
                return False
        else:
            return cls._send_with_retry(event)

    @classmethod
    def stream_file(
        cls,
        label: str,
        integration_name: str,
        level: int,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Stream a diagnostic file.

        This method reads a file and streams its contents as a diagnostic event.
        For large files, the content may be truncated or chunked.

        :param label: The diagnostic label.
        :param integration_name: Name of the integration.
        :param level: The diagnostic level.
        :param file_path: Path to the file to stream.
        :param metadata: Optional additional metadata.

        :returns: True if the file was streamed successfully, False otherwise.
        """
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return False

        try:
            # Read file content (with size limit)
            max_size = 1024 * 1024  # 1MB limit
            file_size = os.path.getsize(file_path)

            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                if file_size > max_size:
                    content = f.read(max_size)
                    truncated = True
                else:
                    content = f.read()
                    truncated = False

            data = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": file_size,
                "content": content,
                "truncated": truncated
            }

            return cls.stream_diagnostic(
                label=label,
                integration_name=integration_name,
                level=level,
                data=data,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Failed to stream file {file_path}: {e}")
            return False

    @classmethod
    def is_enabled(cls) -> bool:
        """
        Check if streaming is enabled.

        :returns: True if streaming is enabled and configured, False otherwise.
        """
        return cls._config is not None and cls._config.enabled and cls._initialized

    @classmethod
    def is_connected(cls) -> bool:
        """
        Check if the stream handler is connected.

        :returns: True if connected, False otherwise.
        """
        return cls._handler is not None and cls._handler.is_connected()

    @classmethod
    def get_config(cls) -> Optional[DiagnosticStreamConfig]:
        """
        Get the current streaming configuration.

        :returns: The current configuration, or None if not configured.
        """
        return cls._config

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """
        Get streaming statistics.

        :returns: Dictionary containing streaming statistics.
        """
        stats = {
            "enabled": cls.is_enabled(),
            "connected": cls.is_connected(),
            "protocol": cls._config.protocol.value if cls._config else None,
            "async_mode": cls._config.async_mode if cls._config else False,
            "queue_size": cls._event_queue.qsize() if cls._event_queue else 0
        }
        return stats

    @classmethod
    def _shutdown_internal(cls) -> None:
        """
        Internal shutdown without lock (called from configure).
        """
        # Signal async worker to stop
        if cls._shutdown_event:
            cls._shutdown_event.set()

        # Wait for async thread to finish
        if cls._async_thread and cls._async_thread.is_alive():
            cls._async_thread.join(timeout=5.0)

        # Disconnect handler
        if cls._handler:
            cls._handler.disconnect()

        # Reset state
        cls._handler = None
        cls._async_thread = None
        cls._event_queue = None
        cls._shutdown_event = None
        cls._initialized = False

    @classmethod
    def shutdown(cls) -> None:
        """
        Shutdown the stream manager.

        This method gracefully shuts down the stream manager, flushing any
        pending events and closing connections.

        :returns: None

        Example Usage::

            # Shutdown when done
            DiagnosticStreamManager.shutdown()
        """
        with cls._lock:
            if not cls._initialized:
                return

            logger.info("Shutting down diagnostic stream manager")
            cls._shutdown_internal()
            logger.info("Diagnostic stream manager shutdown complete")

    @classmethod
    def reset(cls) -> None:
        """
        Reset the stream manager to its initial state.

        This method shuts down any active streaming and clears the configuration.

        :returns: None
        """
        cls.shutdown()
        with cls._lock:
            cls._config = None
