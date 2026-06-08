"""
.. module:: test_debuglogging
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the debuglogging module.

.. moduleauthor:: CodeCraftX
"""

import unittest
import logging
from unittest.mock import patch, MagicMock

from ccai.testbase.debuglogging import (
    DEBUG_LOG_LEVEL,
    get_debug_log_level,
    set_debug_log_level,
    log_breakpoint_triggered,
    log_debugger_connection,
    log_debug_session_start,
    log_debug_session_end,
    log_debug_error,
    log_debug_warning,
    _should_log
)


class DebugLogLevelEnumTests(unittest.TestCase):
    """
    Unit tests for the DEBUG_LOG_LEVEL enumeration.
    """

    def test_debug_level_value(self):
        """Verify DEBUG level has correct value."""
        self.assertEqual(DEBUG_LOG_LEVEL.DEBUG, "debug")

    def test_info_level_value(self):
        """Verify INFO level has correct value."""
        self.assertEqual(DEBUG_LOG_LEVEL.INFO, "info")

    def test_warning_level_value(self):
        """Verify WARNING level has correct value."""
        self.assertEqual(DEBUG_LOG_LEVEL.WARNING, "warning")

    def test_error_level_value(self):
        """Verify ERROR level has correct value."""
        self.assertEqual(DEBUG_LOG_LEVEL.ERROR, "error")

    def test_disabled_level_value(self):
        """Verify DISABLED level has correct value."""
        self.assertEqual(DEBUG_LOG_LEVEL.DISABLED, "disabled")

    def test_enum_inherits_from_str(self):
        """Verify enum inherits from str for string comparison."""
        self.assertIsInstance(DEBUG_LOG_LEVEL.DEBUG, str)

    def test_string_comparison(self):
        """Verify enum members can be compared to strings."""
        self.assertEqual(DEBUG_LOG_LEVEL.INFO, "info")
        self.assertTrue(DEBUG_LOG_LEVEL.INFO == "info")


class DebugLogLevelConfigurationTests(unittest.TestCase):
    """
    Unit tests for debug log level configuration functions.
    """

    def setUp(self):
        """Reset log level to default before each test."""
        set_debug_log_level(DEBUG_LOG_LEVEL.INFO)

    def tearDown(self):
        """Reset log level to default after each test."""
        set_debug_log_level(DEBUG_LOG_LEVEL.INFO)

    def test_get_debug_log_level_returns_current_level(self):
        """Verify get_debug_log_level returns the current level."""
        level = get_debug_log_level()
        self.assertEqual(level, DEBUG_LOG_LEVEL.INFO)

    def test_set_debug_log_level_changes_level(self):
        """Verify set_debug_log_level changes the current level."""
        set_debug_log_level(DEBUG_LOG_LEVEL.DEBUG)
        self.assertEqual(get_debug_log_level(), DEBUG_LOG_LEVEL.DEBUG)

    def test_set_debug_log_level_to_disabled(self):
        """Verify log level can be set to DISABLED."""
        set_debug_log_level(DEBUG_LOG_LEVEL.DISABLED)
        self.assertEqual(get_debug_log_level(), DEBUG_LOG_LEVEL.DISABLED)

    def test_set_debug_log_level_to_error(self):
        """Verify log level can be set to ERROR."""
        set_debug_log_level(DEBUG_LOG_LEVEL.ERROR)
        self.assertEqual(get_debug_log_level(), DEBUG_LOG_LEVEL.ERROR)


class ShouldLogTests(unittest.TestCase):
    """
    Unit tests for the _should_log helper function.
    """

    def setUp(self):
        """Reset log level to default before each test."""
        set_debug_log_level(DEBUG_LOG_LEVEL.INFO)

    def tearDown(self):
        """Reset log level to default after each test."""
        set_debug_log_level(DEBUG_LOG_LEVEL.INFO)

    def test_should_log_returns_false_when_disabled(self):
        """Verify _should_log returns False when level is DISABLED."""
        set_debug_log_level(DEBUG_LOG_LEVEL.DISABLED)
        self.assertFalse(_should_log(DEBUG_LOG_LEVEL.INFO))

    def test_should_log_debug_at_debug_level(self):
        """Verify DEBUG messages are logged at DEBUG level."""
        set_debug_log_level(DEBUG_LOG_LEVEL.DEBUG)
        self.assertTrue(_should_log(DEBUG_LOG_LEVEL.DEBUG))

    def test_should_not_log_debug_at_info_level(self):
        """Verify DEBUG messages are not logged at INFO level."""
        set_debug_log_level(DEBUG_LOG_LEVEL.INFO)
        self.assertFalse(_should_log(DEBUG_LOG_LEVEL.DEBUG))

    def test_should_log_info_at_info_level(self):
        """Verify INFO messages are logged at INFO level."""
        set_debug_log_level(DEBUG_LOG_LEVEL.INFO)
        self.assertTrue(_should_log(DEBUG_LOG_LEVEL.INFO))

    def test_should_log_error_at_info_level(self):
        """Verify ERROR messages are logged at INFO level."""
        set_debug_log_level(DEBUG_LOG_LEVEL.INFO)
        self.assertTrue(_should_log(DEBUG_LOG_LEVEL.ERROR))


class LogBreakpointTriggeredTests(unittest.TestCase):
    """
    Unit tests for the log_breakpoint_triggered function.
    """

    def setUp(self):
        """Reset log level to default before each test."""
        set_debug_log_level(DEBUG_LOG_LEVEL.INFO)

    def tearDown(self):
        """Reset log level to default after each test."""
        set_debug_log_level(DEBUG_LOG_LEVEL.INFO)

    @patch('ccai.testbase.debuglogging.debug_logger')
    def test_logs_breakpoint_with_pdb(self, mock_logger):
        """Verify breakpoint trigger is logged for pdb debugger."""
        log_breakpoint_triggered(
            breakpoint_name="testrun-start",
            debugger="pdb"
        )
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("testrun-start", call_args)
        self.assertIn("pdb", call_args)

    @patch('ccai.testbase.debuglogging.debug_logger')
    def test_logs_breakpoint_with_debugpy_and_port(self, mock_logger):
        """Verify breakpoint trigger is logged for debugpy with port."""
        log_breakpoint_triggered(
            breakpoint_name="test-discovery",
            debugger="debugpy",
            port=5678
        )
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("test-discovery", call_args)
        self.assertIn("debugpy", call_args)
        self.assertIn("5678", call_args)

    @patch('ccai.testbase.debuglogging.debug_logger')
    def test_does_not_log_when_disabled(self, mock_logger):
        """Verify no logging when level is DISABLED."""
        set_debug_log_level(DEBUG_LOG_LEVEL.DISABLED)
        log_breakpoint_triggered(
            breakpoint_name="testrun-start",
            debugger="pdb"
        )
        mock_logger.info.assert_not_called()


class LogDebuggerConnectionTests(unittest.TestCase):
    """
    Unit tests for the log_debugger_connection function.
    """

    def setUp(self):
        """Reset log level to default before each test."""
        set_debug_log_level(DEBUG_LOG_LEVEL.INFO)

    def tearDown(self):
        """Reset log level to default after each test."""
        set_debug_log_level(DEBUG_LOG_LEVEL.INFO)

    @patch('ccai.testbase.debuglogging.debug_logger')
    def test_logs_listening_event(self, mock_logger):
        """Verify listening event is logged."""
        log_debugger_connection(
            event="listening",
            debugger="debugpy",
            port=5678
        )
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("listening", call_args)
        self.assertIn("debugpy", call_args)

    @patch('ccai.testbase.debuglogging.debug_logger')
    def test_logs_connected_event_with_endpoint(self, mock_logger):
        """Verify connected event is logged with endpoint."""
        log_debugger_connection(
            event="connected",
            debugger="debugpy",
            endpoint=("0.0.0.0", 5678)
        )
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn("connected", call_args)
        self.assertIn("endpoint", call_args)

    @patch('ccai.testbase.debuglogging.debug_logger')
    def test_does_not_log_when_disabled(self, mock_logger):
        """Verify no logging when level is DISABLED."""
        set_debug_log_level(DEBUG_LOG_LEVEL.DISABLED)
        log_debugger_connection(
            event="listening",
            debugger="debugpy",
            port=5678
        )
        mock_logger.info.assert_not_called()


class LogDebugSessionTests(unittest.TestCase):
    """
    Unit tests for debug session logging functions.
    """

    def setUp(self):
        """Reset log level to DEBUG before each test."""
        set_debug_log_level(DEBUG_LOG_LEVEL.DEBUG)

    def tearDown(self):
        """Reset log level to default after each test."""
        set_debug_log_level(DEBUG_LOG_LEVEL.INFO)

    @patch('ccai.testbase.debuglogging.debug_logger')
    def test_logs_session_start(self, mock_logger):
        """Verify session start is logged."""
        log_debug_session_start(
            debugger="debugpy",
            breakpoint_name="testrun-start",
            port=5678
        )
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args[0][0]
        self.assertIn("starting", call_args)
        self.assertIn("testrun-start", call_args)

    @patch('ccai.testbase.debuglogging.debug_logger')
    def test_logs_session_end(self, mock_logger):
        """Verify session end is logged."""
        log_debug_session_end(
            debugger="debugpy",
            breakpoint_name="testrun-start"
        )
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args[0][0]
        self.assertIn("ended", call_args)

    @patch('ccai.testbase.debuglogging.debug_logger')
    def test_session_start_not_logged_at_info_level(self, mock_logger):
        """Verify session start is not logged at INFO level."""
        set_debug_log_level(DEBUG_LOG_LEVEL.INFO)
        log_debug_session_start(
            debugger="debugpy",
            breakpoint_name="testrun-start"
        )
        mock_logger.debug.assert_not_called()


class LogDebugErrorWarningTests(unittest.TestCase):
    """
    Unit tests for error and warning logging functions.
    """

    def setUp(self):
        """Reset log level to default before each test."""
        set_debug_log_level(DEBUG_LOG_LEVEL.INFO)

    def tearDown(self):
        """Reset log level to default after each test."""
        set_debug_log_level(DEBUG_LOG_LEVEL.INFO)

    @patch('ccai.testbase.debuglogging.debug_logger')
    def test_logs_error(self, mock_logger):
        """Verify error is logged."""
        log_debug_error(
            message="Failed to connect",
            debugger="debugpy"
        )
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        self.assertIn("Failed to connect", call_args)
        self.assertIn("debugpy", call_args)

    @patch('ccai.testbase.debuglogging.debug_logger')
    def test_logs_error_with_exception(self, mock_logger):
        """Verify error with exception is logged."""
        exc = ImportError("debugpy not found")
        log_debug_error(
            message="Failed to import",
            debugger="debugpy",
            exception=exc
        )
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        self.assertIn("ImportError", call_args)

    @patch('ccai.testbase.debuglogging.debug_logger')
    def test_logs_warning(self, mock_logger):
        """Verify warning is logged."""
        log_debug_warning(
            message="Port may be in use",
            debugger="debugpy"
        )
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        self.assertIn("Port may be in use", call_args)

    @patch('ccai.testbase.debuglogging.debug_logger')
    def test_error_not_logged_when_disabled(self, mock_logger):
        """Verify error is not logged when DISABLED."""
        set_debug_log_level(DEBUG_LOG_LEVEL.DISABLED)
        log_debug_error(message="Test error")
        mock_logger.error.assert_not_called()


if __name__ == "__main__":
    unittest.main()
