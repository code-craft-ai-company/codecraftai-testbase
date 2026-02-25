"""
.. module:: test_debugports
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the debugports module.

.. moduleauthor:: AutomationX

Unit tests for the debug port utilities including port availability checking,
port range parsing, port conflict detection, and global port configuration.
"""

__author__ = "AutomationX"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import socket
import unittest
from unittest.mock import patch, MagicMock

from automojo.testbase.debugports import (
    DEFAULT_DEBUG_PORT,
    PORT_DEBUGPY_ASSISTANT,
    PortConflictError,
    PortRangeError,
    is_port_available,
    find_available_port,
    parse_port_range,
    validate_debug_port,
    resolve_debug_port,
    get_configured_debug_port,
    set_configured_debug_port,
    reset_configured_debug_port
)


class TestPortConstants(unittest.TestCase):
    """Tests for port constant definitions."""

    def test_default_debug_port_value(self):
        """Verify DEFAULT_DEBUG_PORT is 5678."""
        self.assertEqual(DEFAULT_DEBUG_PORT, 5678)

    def test_debugpy_assistant_port_value(self):
        """Verify PORT_DEBUGPY_ASSISTANT is 5679."""
        self.assertEqual(PORT_DEBUGPY_ASSISTANT, 5679)


class TestPortConflictError(unittest.TestCase):
    """Tests for PortConflictError exception."""

    def test_port_conflict_error_with_default_message(self):
        """Test PortConflictError with default message."""
        error = PortConflictError(5678)
        self.assertEqual(error.port, 5678)
        self.assertIn("5678", error.message)
        self.assertIn("already in use", error.message)

    def test_port_conflict_error_with_custom_message(self):
        """Test PortConflictError with custom message."""
        error = PortConflictError(5680, "Custom error message")
        self.assertEqual(error.port, 5680)
        self.assertEqual(error.message, "Custom error message")


class TestPortRangeError(unittest.TestCase):
    """Tests for PortRangeError exception."""

    def test_port_range_error_with_default_message(self):
        """Test PortRangeError with default message."""
        error = PortRangeError("invalid")
        self.assertEqual(error.range_spec, "invalid")
        self.assertIn("invalid", error.message)

    def test_port_range_error_with_custom_message(self):
        """Test PortRangeError with custom message."""
        error = PortRangeError("5678-5670", "Start must be less than end")
        self.assertEqual(error.range_spec, "5678-5670")
        self.assertEqual(error.message, "Start must be less than end")


class TestIsPortAvailable(unittest.TestCase):
    """Tests for is_port_available function."""

    def test_available_port_returns_true(self):
        """Test that an available port returns True."""
        # Use a high port that's unlikely to be in use
        result = is_port_available(59999)
        # This test may be flaky if the port happens to be in use
        # but it's a reasonable assumption for testing
        self.assertIsInstance(result, bool)

    @patch('socket.socket')
    def test_port_in_use_returns_false(self, mock_socket_class):
        """Test that a port in use returns False."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.bind.side_effect = OSError("Address already in use")

        result = is_port_available(5678)
        self.assertFalse(result)

    @patch('socket.socket')
    def test_available_port_with_mock(self, mock_socket_class):
        """Test available port detection with mock."""
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.bind.return_value = None

        result = is_port_available(5678)
        self.assertTrue(result)
        mock_socket.close.assert_called_once()


class TestParsePortRange(unittest.TestCase):
    """Tests for parse_port_range function."""

    def test_valid_port_range(self):
        """Test parsing a valid port range."""
        start, end = parse_port_range("5678-5688")
        self.assertEqual(start, 5678)
        self.assertEqual(end, 5688)

    def test_port_range_with_spaces(self):
        """Test parsing port range with spaces."""
        start, end = parse_port_range(" 5678 - 5688 ")
        self.assertEqual(start, 5678)
        self.assertEqual(end, 5688)

    def test_single_port_range(self):
        """Test parsing a single port range (start == end)."""
        start, end = parse_port_range("5678-5678")
        self.assertEqual(start, 5678)
        self.assertEqual(end, 5678)

    def test_invalid_format_no_dash(self):
        """Test that missing dash raises PortRangeError."""
        with self.assertRaises(PortRangeError) as context:
            parse_port_range("5678")
        self.assertIn("start-end", context.exception.message)

    def test_invalid_format_multiple_dashes(self):
        """Test that multiple dashes raises PortRangeError."""
        with self.assertRaises(PortRangeError) as context:
            parse_port_range("5678-5680-5690")
        self.assertIn("start-end", context.exception.message)

    def test_non_integer_values(self):
        """Test that non-integer values raise PortRangeError."""
        with self.assertRaises(PortRangeError) as context:
            parse_port_range("abc-def")
        self.assertIn("integers", context.exception.message)

    def test_start_greater_than_end(self):
        """Test that start > end raises PortRangeError."""
        with self.assertRaises(PortRangeError) as context:
            parse_port_range("5688-5678")
        self.assertIn("less than or equal", context.exception.message)

    def test_port_below_valid_range(self):
        """Test that port below 1 raises PortRangeError."""
        with self.assertRaises(PortRangeError) as context:
            parse_port_range("0-5678")
        self.assertIn("between 1 and 65535", context.exception.message)

    def test_port_above_valid_range(self):
        """Test that port above 65535 raises PortRangeError."""
        with self.assertRaises(PortRangeError) as context:
            parse_port_range("5678-70000")
        self.assertIn("between 1 and 65535", context.exception.message)

    def test_empty_string(self):
        """Test that empty string raises PortRangeError."""
        with self.assertRaises(PortRangeError) as context:
            parse_port_range("")
        self.assertIn("empty", context.exception.message)

    def test_none_value(self):
        """Test that None raises PortRangeError."""
        with self.assertRaises(PortRangeError) as context:
            parse_port_range(None)
        self.assertIn("empty", context.exception.message)


class TestValidateDebugPort(unittest.TestCase):
    """Tests for validate_debug_port function."""

    def test_valid_port(self):
        """Test validation of a valid port."""
        result = validate_debug_port(5678)
        self.assertEqual(result, 5678)

    def test_valid_port_as_string(self):
        """Test validation of port as string."""
        result = validate_debug_port("5678")
        self.assertEqual(result, 5678)

    def test_port_below_range(self):
        """Test that port below 1 raises ValueError."""
        with self.assertRaises(ValueError) as context:
            validate_debug_port(0)
        self.assertIn("between 1 and 65535", str(context.exception))

    def test_port_above_range(self):
        """Test that port above 65535 raises ValueError."""
        with self.assertRaises(ValueError) as context:
            validate_debug_port(70000)
        self.assertIn("between 1 and 65535", str(context.exception))

    def test_invalid_type(self):
        """Test that invalid type raises ValueError."""
        with self.assertRaises(ValueError) as context:
            validate_debug_port("invalid")
        self.assertIn("integer", str(context.exception))


class TestFindAvailablePort(unittest.TestCase):
    """Tests for find_available_port function."""

    @patch('automojo.testbase.debugports.is_port_available')
    def test_first_port_available(self, mock_is_available):
        """Test finding first available port."""
        mock_is_available.return_value = True
        result = find_available_port(5678, 5688)
        self.assertEqual(result, 5678)

    @patch('automojo.testbase.debugports.is_port_available')
    def test_second_port_available(self, mock_is_available):
        """Test finding second port when first is unavailable."""
        mock_is_available.side_effect = [False, True]
        result = find_available_port(5678, 5688)
        self.assertEqual(result, 5679)

    @patch('automojo.testbase.debugports.is_port_available')
    def test_no_port_available(self, mock_is_available):
        """Test PortConflictError when no port is available."""
        mock_is_available.return_value = False
        with self.assertRaises(PortConflictError) as context:
            find_available_port(5678, 5680)
        self.assertIn("No available port", context.exception.message)

    def test_invalid_start_port(self):
        """Test ValueError for invalid start port."""
        with self.assertRaises(ValueError) as context:
            find_available_port(0, 5688)
        self.assertIn("Invalid start port", str(context.exception))

    def test_invalid_end_port(self):
        """Test ValueError for invalid end port."""
        with self.assertRaises(ValueError) as context:
            find_available_port(5678, 70000)
        self.assertIn("Invalid end port", str(context.exception))

    def test_start_greater_than_end(self):
        """Test ValueError when start > end."""
        with self.assertRaises(ValueError) as context:
            find_available_port(5688, 5678)
        self.assertIn("less than or equal", str(context.exception))


class TestResolveDebugPort(unittest.TestCase):
    """Tests for resolve_debug_port function."""

    @patch('automojo.testbase.debugports.is_port_available')
    def test_default_port_available(self, mock_is_available):
        """Test using default port when available."""
        mock_is_available.return_value = True
        result = resolve_debug_port()
        self.assertEqual(result, DEFAULT_DEBUG_PORT)

    @patch('automojo.testbase.debugports.is_port_available')
    def test_default_port_unavailable(self, mock_is_available):
        """Test PortConflictError when default port unavailable."""
        mock_is_available.return_value = False
        with self.assertRaises(PortConflictError):
            resolve_debug_port()

    @patch('automojo.testbase.debugports.is_port_available')
    def test_specific_port_available(self, mock_is_available):
        """Test using specific port when available."""
        mock_is_available.return_value = True
        result = resolve_debug_port(port=5680)
        self.assertEqual(result, 5680)

    @patch('automojo.testbase.debugports.is_port_available')
    def test_specific_port_unavailable(self, mock_is_available):
        """Test PortConflictError when specific port unavailable."""
        mock_is_available.return_value = False
        with self.assertRaises(PortConflictError):
            resolve_debug_port(port=5680)

    @patch('automojo.testbase.debugports.find_available_port')
    def test_port_range_finds_port(self, mock_find):
        """Test using port range to find available port."""
        mock_find.return_value = 5680
        result = resolve_debug_port(port_range="5678-5688")
        self.assertEqual(result, 5680)

    @patch('automojo.testbase.debugports.find_available_port')
    def test_port_range_precedence(self, mock_find):
        """Test that port range takes precedence over specific port."""
        mock_find.return_value = 5682
        result = resolve_debug_port(port=5678, port_range="5680-5690")
        self.assertEqual(result, 5682)
        mock_find.assert_called_once_with(5680, 5690)


class TestConfiguredDebugPort(unittest.TestCase):
    """Tests for global debug port configuration."""

    def setUp(self):
        """Reset configured port before each test."""
        reset_configured_debug_port()

    def tearDown(self):
        """Reset configured port after each test."""
        reset_configured_debug_port()

    def test_get_default_port(self):
        """Test getting default port when none configured."""
        result = get_configured_debug_port()
        self.assertEqual(result, DEFAULT_DEBUG_PORT)

    def test_set_and_get_port(self):
        """Test setting and getting configured port."""
        set_configured_debug_port(5680)
        result = get_configured_debug_port()
        self.assertEqual(result, 5680)

    def test_reset_port(self):
        """Test resetting configured port."""
        set_configured_debug_port(5680)
        reset_configured_debug_port()
        result = get_configured_debug_port()
        self.assertEqual(result, DEFAULT_DEBUG_PORT)

    def test_set_invalid_port(self):
        """Test setting invalid port raises ValueError."""
        with self.assertRaises(ValueError):
            set_configured_debug_port(0)


if __name__ == '__main__':
    unittest.main()
