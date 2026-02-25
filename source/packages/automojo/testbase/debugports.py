"""
.. module:: debugports
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module providing port utilities for debugging support.

.. moduleauthor:: AutomationX

This module provides utilities for managing debug ports in the TestBase framework.
It includes functions for:

- Checking if a port is available
- Finding an available port within a range
- Parsing port range specifications
- Detecting port conflicts
- Global debug port configuration

Example Usage::

    from automojo.testbase.debugports import (
        is_port_available,
        find_available_port,
        parse_port_range,
        PortConflictError,
        get_configured_debug_port,
        set_configured_debug_port
    )

    # Check if a specific port is available
    if is_port_available(5678):
        print("Port 5678 is available")

    # Find an available port in a range
    port = find_available_port(5678, 5688)
    print(f"Using port {port}")

    # Parse a port range string
    start, end = parse_port_range("5678-5688")

    # Set and get the configured debug port
    set_configured_debug_port(5680)
    port = get_configured_debug_port()

"""

__author__ = "AutomationX"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Optional, Tuple

import socket
import logging


logger = logging.getLogger()


# Default debug port for debugpy
DEFAULT_DEBUG_PORT = 5678

# Default port for DebugPyAssistant
PORT_DEBUGPY_ASSISTANT = 5679

# Global configured debug port (can be set via CLI)
_configured_debug_port: Optional[int] = None


class PortConflictError(Exception):
    """
    Exception raised when a port conflict is detected.

    This exception is raised when attempting to use a port that is already
    in use by another process, or when no available port can be found
    within a specified range.

    Attributes:
        port (int): The port that caused the conflict.
        message (str): Explanation of the conflict.

    Example::

        try:
            port = find_available_port(5678, 5680)
        except PortConflictError as e:
            print(f"Port conflict: {e}")
    """

    def __init__(self, port: int, message: str = None):
        """
        Initialize the PortConflictError.

        :param port: The port that caused the conflict.
        :param message: Optional custom message explaining the conflict.
        """
        self.port = port
        if message is None:
            message = f"Port {port} is already in use"
        self.message = message
        super().__init__(self.message)


class PortRangeError(Exception):
    """
    Exception raised when a port range specification is invalid.

    This exception is raised when the port range string cannot be parsed
    or when the range values are invalid (e.g., start > end, invalid port numbers).

    Attributes:
        range_spec (str): The invalid port range specification.
        message (str): Explanation of the error.

    Example::

        try:
            start, end = parse_port_range("invalid-range")
        except PortRangeError as e:
            print(f"Invalid range: {e}")
    """

    def __init__(self, range_spec: str, message: str = None):
        """
        Initialize the PortRangeError.

        :param range_spec: The invalid port range specification.
        :param message: Optional custom message explaining the error.
        """
        self.range_spec = range_spec
        if message is None:
            message = f"Invalid port range specification: {range_spec}"
        self.message = message
        super().__init__(self.message)


def is_port_available(port: int, host: str = "0.0.0.0") -> bool:
    """
    Check if a specific port is available for binding.

    This function attempts to bind to the specified port to determine
    if it is available. It uses a TCP socket to test the port.

    :param port: The port number to check (1-65535).
    :param host: The host address to bind to. Default is "0.0.0.0" (all interfaces).
    :returns: True if the port is available, False if it is in use.

    Example::

        if is_port_available(5678):
            print("Port 5678 is available for debugging")
        else:
            print("Port 5678 is already in use")

    Note:
        This function performs a quick check by attempting to bind to the port.
        There is a small race condition window between checking and actually
        using the port, but this is acceptable for debugging purposes.
    """
    # Port Availability Check Algorithm:
    # -----------------------------------
    # 1. Create a TCP socket
    # 2. Set SO_REUSEADDR to allow quick rebinding after close
    # 3. Attempt to bind to the specified host:port
    # 4. If bind succeeds, the port is available
    # 5. If bind fails with an error, the port is in use
    # 6. Always close the socket to release resources

    available = False
    sock = None

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        available = True
    except OSError:
        # Port is in use or cannot be bound
        available = False
    finally:
        if sock is not None:
            sock.close()

    return available


def find_available_port(start_port: int, end_port: int, host: str = "0.0.0.0") -> int:
    """
    Find an available port within a specified range.

    This function iterates through the port range and returns the first
    available port. If no port is available in the range, it raises
    a PortConflictError.

    :param start_port: The starting port of the range (inclusive).
    :param end_port: The ending port of the range (inclusive).
    :param host: The host address to check. Default is "0.0.0.0".
    :returns: The first available port in the range.
    :raises PortConflictError: If no port is available in the range.
    :raises ValueError: If the port range is invalid.

    Example::

        try:
            port = find_available_port(5678, 5688)
            print(f"Using debug port: {port}")
        except PortConflictError:
            print("No available ports in range 5678-5688")

    Note:
        The function checks ports sequentially from start_port to end_port.
        For better distribution in multi-session scenarios, consider using
        a random starting point within the range.
    """
    # Validate port range
    if start_port < 1 or start_port > 65535:
        raise ValueError(f"Invalid start port: {start_port}. Must be between 1 and 65535.")
    if end_port < 1 or end_port > 65535:
        raise ValueError(f"Invalid end port: {end_port}. Must be between 1 and 65535.")
    if start_port > end_port:
        raise ValueError(f"Start port ({start_port}) must be less than or equal to end port ({end_port}).")

    # Port Range Search Algorithm:
    # ----------------------------
    # 1. Iterate through each port in the range [start_port, end_port]
    # 2. For each port, check if it is available using is_port_available()
    # 3. Return the first available port found
    # 4. If no port is available after checking all ports, raise PortConflictError

    for port in range(start_port, end_port + 1):
        if is_port_available(port, host):
            logger.debug(f"Found available debug port: {port}")
            return port

    # No available port found in range
    raise PortConflictError(
        port=start_port,
        message=f"No available port found in range {start_port}-{end_port}"
    )


def parse_port_range(range_spec: str) -> Tuple[int, int]:
    """
    Parse a port range specification string.

    The port range specification should be in the format "start-end"
    where start and end are valid port numbers (1-65535).

    :param range_spec: The port range specification string (e.g., "5678-5688").
    :returns: A tuple of (start_port, end_port).
    :raises PortRangeError: If the specification is invalid.

    Example::

        start, end = parse_port_range("5678-5688")
        print(f"Port range: {start} to {end}")

        # Invalid examples that raise PortRangeError:
        # parse_port_range("invalid")
        # parse_port_range("5678")
        # parse_port_range("5688-5678")  # start > end
        # parse_port_range("0-5678")     # invalid port
    """
    # Port Range Parsing Algorithm:
    # -----------------------------
    # 1. Split the specification by '-' delimiter
    # 2. Validate that exactly two parts are present
    # 3. Parse each part as an integer
    # 4. Validate that both ports are in valid range (1-65535)
    # 5. Validate that start <= end
    # 6. Return the tuple (start, end)

    if not range_spec or not isinstance(range_spec, str):
        raise PortRangeError(range_spec, "Port range specification cannot be empty")

    parts = range_spec.strip().split('-')

    if len(parts) != 2:
        raise PortRangeError(
            range_spec,
            f"Port range must be in format 'start-end', got: {range_spec}"
        )

    try:
        start_port = int(parts[0].strip())
        end_port = int(parts[1].strip())
    except ValueError:
        raise PortRangeError(
            range_spec,
            f"Port range values must be integers, got: {range_spec}"
        )

    if start_port < 1 or start_port > 65535:
        raise PortRangeError(
            range_spec,
            f"Start port must be between 1 and 65535, got: {start_port}"
        )

    if end_port < 1 or end_port > 65535:
        raise PortRangeError(
            range_spec,
            f"End port must be between 1 and 65535, got: {end_port}"
        )

    if start_port > end_port:
        raise PortRangeError(
            range_spec,
            f"Start port ({start_port}) must be less than or equal to end port ({end_port})"
        )

    return (start_port, end_port)


def validate_debug_port(port: int) -> int:
    """
    Validate a debug port number.

    :param port: The port number to validate.
    :returns: The validated port number.
    :raises ValueError: If the port is invalid.

    Example::

        port = validate_debug_port(5678)  # Returns 5678
        port = validate_debug_port(0)     # Raises ValueError
    """
    if not isinstance(port, int):
        try:
            port = int(port)
        except (ValueError, TypeError):
            raise ValueError(f"Port must be an integer, got: {type(port).__name__}")

    if port < 1 or port > 65535:
        raise ValueError(f"Port must be between 1 and 65535, got: {port}")

    return port


def resolve_debug_port(
    port: Optional[int] = None,
    port_range: Optional[str] = None,
    default_port: int = DEFAULT_DEBUG_PORT
) -> int:
    """
    Resolve the debug port to use based on configuration options.

    This function determines which debug port to use based on the provided
    options. The resolution order is:

    1. If port_range is specified, find an available port in the range
    2. If port is specified, validate and use it (with conflict detection)
    3. Otherwise, use the default port (with conflict detection)

    :param port: A specific port to use (optional).
    :param port_range: A port range specification string (optional).
    :param default_port: The default port to use if no other option is specified.
    :returns: The resolved debug port.
    :raises PortConflictError: If the specified port is in use and no range is provided.
    :raises PortRangeError: If the port range specification is invalid.

    Example::

        # Use default port
        port = resolve_debug_port()

        # Use specific port
        port = resolve_debug_port(port=5680)

        # Use port range (auto-select)
        port = resolve_debug_port(port_range="5678-5688")

        # Port range takes precedence over specific port
        port = resolve_debug_port(port=5678, port_range="5680-5690")
    """
    # Port Resolution Algorithm:
    # --------------------------
    # Priority order:
    # 1. port_range - Find available port in range (most flexible)
    # 2. port - Use specific port with conflict check
    # 3. default_port - Use default with conflict check
    #
    # When using a specific port or default, we check for conflicts
    # and raise an error if the port is in use. When using a range,
    # we automatically find an available port.

    if port_range is not None:
        # Parse and find available port in range
        start_port, end_port = parse_port_range(port_range)
        resolved_port = find_available_port(start_port, end_port)
        logger.info(f"Resolved debug port from range {port_range}: {resolved_port}")
        return resolved_port

    if port is not None:
        # Validate and check specific port
        validated_port = validate_debug_port(port)
        if not is_port_available(validated_port):
            raise PortConflictError(
                validated_port,
                f"Specified debug port {validated_port} is already in use. "
                f"Consider using --debug-port-range to auto-select an available port."
            )
        logger.info(f"Using specified debug port: {validated_port}")
        return validated_port

    # Use default port with conflict check
    if not is_port_available(default_port):
        raise PortConflictError(
            default_port,
            f"Default debug port {default_port} is already in use. "
            f"Use --debug-port to specify a different port or "
            f"--debug-port-range to auto-select an available port."
        )
    logger.info(f"Using default debug port: {default_port}")
    return default_port


def get_configured_debug_port() -> int:
    """
    Get the currently configured debug port.

    Returns the debug port that has been configured via CLI options,
    or the default port (5678) if no custom port has been set.

    :returns: The configured debug port.

    Example::

        port = get_configured_debug_port()
        print(f"Debug port: {port}")
    """
    global _configured_debug_port
    if _configured_debug_port is not None:
        return _configured_debug_port
    return DEFAULT_DEBUG_PORT


def set_configured_debug_port(port: int) -> None:
    """
    Set the configured debug port.

    This function is typically called by the CLI command handler when
    the --debug-port or --debug-port-range options are specified.

    :param port: The port number to configure.
    :raises ValueError: If the port is invalid.

    Example::

        set_configured_debug_port(5680)
    """
    global _configured_debug_port
    validated_port = validate_debug_port(port)
    _configured_debug_port = validated_port
    logger.info(f"Configured debug port: {validated_port}")


def reset_configured_debug_port() -> None:
    """
    Reset the configured debug port to None (use default).

    This function is primarily used for testing purposes to reset
    the global state between tests.

    Example::

        reset_configured_debug_port()
        assert get_configured_debug_port() == DEFAULT_DEBUG_PORT
    """
    global _configured_debug_port
    _configured_debug_port = None
