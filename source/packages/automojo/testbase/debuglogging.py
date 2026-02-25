"""
.. module:: debuglogging
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Breakpoint logging support with configurable log levels.

.. moduleauthor:: AutomationX

This module provides logging infrastructure for debugging events within the
TestBase framework. It enables logging of:

- Breakpoint trigger events
- Debugger connection events
- Debug session lifecycle events

The logging level can be configured via the ``AM_DEBUG_LOG_LEVEL`` runtime
variable or programmatically through the ``set_debug_log_level`` function.

Example Usage::

    from automojo.testbase.debuglogging import (
        log_breakpoint_triggered,
        log_debugger_connection,
        set_debug_log_level,
        DEBUG_LOG_LEVEL
    )

    # Set debug logging level
    set_debug_log_level(DEBUG_LOG_LEVEL.DEBUG)

    # Log a breakpoint trigger event
    log_breakpoint_triggered(
        breakpoint_name="testrun-start",
        debugger="debugpy",
        port=5678
    )

    # Log a debugger connection event
    log_debugger_connection(
        event="connected",
        debugger="debugpy",
        port=5678
    )

"""

__author__ = "AutomationX"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Optional
from enum import Enum

import logging


# Module-level logger for debug events
debug_logger = logging.getLogger("automojo.testbase.debugging")


class DEBUG_LOG_LEVEL(str, Enum):
    """
    Enumeration of supported debug logging levels.

    This enum provides predefined logging levels for debug event logging.
    It inherits from both ``str`` and ``Enum`` for easy comparison with
    string values.

    Attributes:
        DEBUG (str): Most verbose level, logs all debug events.
        INFO (str): Standard level, logs significant debug events.
        WARNING (str): Logs only warning-level debug events.
        ERROR (str): Logs only error-level debug events.
        DISABLED (str): Disables all debug event logging.

    Example::

        from automojo.testbase.debuglogging import DEBUG_LOG_LEVEL, set_debug_log_level

        # Enable verbose debug logging
        set_debug_log_level(DEBUG_LOG_LEVEL.DEBUG)

        # Disable debug logging
        set_debug_log_level(DEBUG_LOG_LEVEL.DISABLED)
    """
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DISABLED = "disabled"


# Module-level variable to track the current debug log level
_current_debug_log_level: DEBUG_LOG_LEVEL = DEBUG_LOG_LEVEL.INFO


def get_debug_log_level() -> DEBUG_LOG_LEVEL:
    """
    Returns the current debug logging level.

    :returns: The current debug log level.

    Example::

        from automojo.testbase.debuglogging import get_debug_log_level

        level = get_debug_log_level()
        print(f"Current debug log level: {level}")
    """
    return _current_debug_log_level


def set_debug_log_level(level: DEBUG_LOG_LEVEL) -> None:
    """
    Sets the debug logging level.

    This function configures the verbosity of debug event logging.
    The level can be set to any value from the ``DEBUG_LOG_LEVEL`` enum.

    :param level: The desired debug log level.

    Example::

        from automojo.testbase.debuglogging import set_debug_log_level, DEBUG_LOG_LEVEL

        # Enable verbose logging
        set_debug_log_level(DEBUG_LOG_LEVEL.DEBUG)

        # Set to info level
        set_debug_log_level(DEBUG_LOG_LEVEL.INFO)

        # Disable debug logging
        set_debug_log_level(DEBUG_LOG_LEVEL.DISABLED)
    """
    global _current_debug_log_level
    _current_debug_log_level = level
    return


def _should_log(min_level: DEBUG_LOG_LEVEL) -> bool:
    """
    Determines if a message at the given level should be logged.

    :param min_level: The minimum level required for logging.
    :returns: True if the message should be logged, False otherwise.
    """
    if _current_debug_log_level == DEBUG_LOG_LEVEL.DISABLED:
        return False

    level_order = [
        DEBUG_LOG_LEVEL.DEBUG,
        DEBUG_LOG_LEVEL.INFO,
        DEBUG_LOG_LEVEL.WARNING,
        DEBUG_LOG_LEVEL.ERROR
    ]

    current_index = level_order.index(_current_debug_log_level) if _current_debug_log_level in level_order else 0
    min_index = level_order.index(min_level) if min_level in level_order else 0

    return current_index <= min_index


def log_breakpoint_triggered(
    breakpoint_name: str,
    debugger: str,
    port: Optional[int] = None
) -> None:
    """
    Logs a breakpoint trigger event.

    This function logs when a well-known breakpoint is triggered during
    test execution. The log message includes the breakpoint name, debugger
    type, and optionally the debug port.

    :param breakpoint_name: The name of the breakpoint being triggered
        (e.g., 'test-discovery', 'testrun-start').
    :param debugger: The debugger backend being used ('pdb' or 'debugpy').
    :param port: Optional debug port for debugpy connections.

    Example::

        from automojo.testbase.debuglogging import log_breakpoint_triggered

        # Log pdb breakpoint
        log_breakpoint_triggered(
            breakpoint_name="testrun-start",
            debugger="pdb"
        )

        # Log debugpy breakpoint with port
        log_breakpoint_triggered(
            breakpoint_name="test-discovery",
            debugger="debugpy",
            port=5678
        )
    """
    if not _should_log(DEBUG_LOG_LEVEL.INFO):
        return

    if port is not None:
        message = f"Breakpoint triggered: name='{breakpoint_name}', debugger='{debugger}', port={port}"
    else:
        message = f"Breakpoint triggered: name='{breakpoint_name}', debugger='{debugger}'"

    debug_logger.info(message)
    return


def log_debugger_connection(
    event: str,
    debugger: str,
    port: Optional[int] = None,
    endpoint: Optional[tuple] = None
) -> None:
    """
    Logs a debugger connection event.

    This function logs debugger connection lifecycle events such as
    listening, waiting for client, client connected, and client disconnected.

    :param event: The connection event type. Common values:
        - 'listening': Debugger started listening for connections
        - 'waiting': Debugger waiting for client to connect
        - 'connected': Debug client connected
        - 'disconnected': Debug client disconnected
    :param debugger: The debugger backend being used ('pdb' or 'debugpy').
    :param port: Optional debug port for the connection.
    :param endpoint: Optional (host, port) tuple for the connection endpoint.

    Example::

        from automojo.testbase.debuglogging import log_debugger_connection

        # Log listening event
        log_debugger_connection(
            event="listening",
            debugger="debugpy",
            port=5678
        )

        # Log connection with endpoint
        log_debugger_connection(
            event="connected",
            debugger="debugpy",
            endpoint=("0.0.0.0", 5678)
        )
    """
    if not _should_log(DEBUG_LOG_LEVEL.INFO):
        return

    if endpoint is not None:
        message = f"Debugger {event}: debugger='{debugger}', endpoint={endpoint}"
    elif port is not None:
        message = f"Debugger {event}: debugger='{debugger}', port={port}"
    else:
        message = f"Debugger {event}: debugger='{debugger}'"

    debug_logger.info(message)
    return


def log_debug_session_start(
    debugger: str,
    breakpoint_name: str,
    port: Optional[int] = None
) -> None:
    """
    Logs the start of a debug session.

    This function logs when a debug session begins, typically when
    a breakpoint is about to be triggered and the debugger is ready.

    :param debugger: The debugger backend being used ('pdb' or 'debugpy').
    :param breakpoint_name: The name of the breakpoint starting the session.
    :param port: Optional debug port for debugpy sessions.

    Example::

        from automojo.testbase.debuglogging import log_debug_session_start

        log_debug_session_start(
            debugger="debugpy",
            breakpoint_name="testrun-start",
            port=5678
        )
    """
    if not _should_log(DEBUG_LOG_LEVEL.DEBUG):
        return

    if port is not None:
        message = f"Debug session starting: debugger='{debugger}', breakpoint='{breakpoint_name}', port={port}"
    else:
        message = f"Debug session starting: debugger='{debugger}', breakpoint='{breakpoint_name}'"

    debug_logger.debug(message)
    return


def log_debug_session_end(
    debugger: str,
    breakpoint_name: Optional[str] = None
) -> None:
    """
    Logs the end of a debug session.

    This function logs when a debug session ends, typically when
    the debugger client disconnects or execution resumes.

    :param debugger: The debugger backend that was used ('pdb' or 'debugpy').
    :param breakpoint_name: Optional name of the breakpoint that started the session.

    Example::

        from automojo.testbase.debuglogging import log_debug_session_end

        log_debug_session_end(
            debugger="debugpy",
            breakpoint_name="testrun-start"
        )
    """
    if not _should_log(DEBUG_LOG_LEVEL.DEBUG):
        return

    if breakpoint_name is not None:
        message = f"Debug session ended: debugger='{debugger}', breakpoint='{breakpoint_name}'"
    else:
        message = f"Debug session ended: debugger='{debugger}'"

    debug_logger.debug(message)
    return


def log_debug_error(
    message: str,
    debugger: Optional[str] = None,
    exception: Optional[Exception] = None
) -> None:
    """
    Logs a debug-related error.

    This function logs errors that occur during debugging operations,
    such as port conflicts, connection failures, or missing debugger modules.

    :param message: The error message to log.
    :param debugger: Optional debugger backend related to the error.
    :param exception: Optional exception that caused the error.

    Example::

        from automojo.testbase.debuglogging import log_debug_error

        try:
            import debugpy
        except ImportError as e:
            log_debug_error(
                message="Failed to import debugpy module",
                debugger="debugpy",
                exception=e
            )
    """
    if not _should_log(DEBUG_LOG_LEVEL.ERROR):
        return

    if debugger is not None:
        full_message = f"Debug error ({debugger}): {message}"
    else:
        full_message = f"Debug error: {message}"

    if exception is not None:
        full_message += f" - {type(exception).__name__}: {str(exception)}"

    debug_logger.error(full_message)
    return


def log_debug_warning(
    message: str,
    debugger: Optional[str] = None
) -> None:
    """
    Logs a debug-related warning.

    This function logs warnings that occur during debugging operations,
    such as potential issues that don't prevent debugging but may affect behavior.

    :param message: The warning message to log.
    :param debugger: Optional debugger backend related to the warning.

    Example::

        from automojo.testbase.debuglogging import log_debug_warning

        log_debug_warning(
            message="Debug port 5678 may already be in use",
            debugger="debugpy"
        )
    """
    if not _should_log(DEBUG_LOG_LEVEL.WARNING):
        return

    if debugger is not None:
        full_message = f"Debug warning ({debugger}): {message}"
    else:
        full_message = f"Debug warning: {message}"

    debug_logger.warning(full_message)
    return
