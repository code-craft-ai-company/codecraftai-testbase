"""
    .. module:: ccai.testbase.results.model.streaminginfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for streaming configuration information.

    This module provides configuration dataclasses for result streaming to external
    services. It supports both REST endpoint streaming and WebSocket-based streaming.

    .. moduleauthor:: CodeCraftX
"""



__author__ = "CodeCraftX"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum


class StreamingProtocol(Enum):
    """
        Enumeration of supported streaming protocols for result delivery.
        
        This enum defines the available protocols for streaming test results
        to external services in real-time.
    """
    REST = "REST"           # HTTP REST endpoint streaming
    WEBSOCKET = "WebSocket" # WebSocket-based streaming


@dataclass
class StreamingInfo:
    """
        Configuration for streaming test results to external services.
        
        This dataclass contains all configuration needed to stream test results
        in real-time to external monitoring services. It supports both REST
        endpoint streaming and WebSocket-based streaming.
        
        REST Streaming:
            Results are POSTed to the configured URL as JSON payloads.
            Each result (preview or final) triggers an HTTP POST request.
            
        WebSocket Streaming:
            Results are sent over a persistent WebSocket connection.
            The connection is established when recording begins and
            maintained throughout the test run.
        
        Example Usage::
        
            # REST streaming configuration
            streaming_info = StreamingInfo(
                protocol=StreamingProtocol.REST,
                streaming_url="https://monitoring.example.com/api/results",
                streaming_headers={"Authorization": "Bearer token123"},
                stream_previews=True,
                stream_results=True
            )
            
            # WebSocket streaming configuration
            streaming_info = StreamingInfo(
                protocol=StreamingProtocol.WEBSOCKET,
                streaming_url="wss://monitoring.example.com/ws/results",
                stream_previews=True,
                stream_results=True,
                reconnect_on_failure=True,
                reconnect_interval=5.0
            )
    """
    
    protocol: StreamingProtocol  # The streaming protocol to use (REST or WebSocket)
    streaming_url: str           # The URL to stream results to
    streaming_headers: Optional[dict] = None  # Optional headers for REST requests or WebSocket handshake
    stream_previews: bool = True  # Whether to stream preview records
    stream_results: bool = True   # Whether to stream final result records
    reconnect_on_failure: bool = True  # Whether to reconnect on connection failure (WebSocket)
    reconnect_interval: float = 5.0    # Interval in seconds between reconnection attempts
    batch_size: int = 1          # Number of results to batch before sending (1 = immediate)
    batch_timeout: float = 1.0   # Maximum time to wait before sending a partial batch


@dataclass
class StreamingCallback:
    """
        Protocol for custom streaming callbacks.
        
        This dataclass allows users to provide custom callbacks for handling
        streamed results. The callback is invoked for each result that would
        be streamed, allowing custom processing or routing.
        
        Example Usage::
        
            def my_result_handler(result_dict: dict, is_preview: bool) -> bool:
                # Custom handling logic
                print(f"Result: {result_dict['name']}, Preview: {is_preview}")
                return True  # Return True to indicate success
            
            callback = StreamingCallback(
                on_result=my_result_handler,
                on_error=lambda e: print(f"Error: {e}")
            )
    """
    
    on_result: Callable[[dict, bool], bool]  # Callback for each result (result_dict, is_preview) -> success
    on_error: Optional[Callable[[Exception], None]] = None  # Optional error callback
    on_connect: Optional[Callable[[], None]] = None  # Optional connection established callback
    on_disconnect: Optional[Callable[[], None]] = None  # Optional disconnection callback
