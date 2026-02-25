"""
    .. module:: automojo_tests.testbase.cli.test_testbase_command
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the root testbase command.

    .. moduleauthor:: AutomationX

    Tests for the root testbase command defined in automojo.testbase.cli.testbase_command.
    These tests verify verbosity level mapping, runtime initialization, and variable
    override application as specified in Requirements 1.1-1.7.
"""

__author__ = "AutomationX"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import unittest
from unittest.mock import patch, MagicMock

from automojo.arcli.model.fields.optionfield import OptionMode


class TestbaseRootCommandDecoratorTests(unittest.TestCase):
    """Tests for root command decorator configuration (Requirements 1.1, 1.2)."""

    def test_entry_point_is_testbase(self):
        """Test that the root command entry point is 'testbase' (Requirement 1.1)."""
        from automojo.testbase.cli.testbase_command import testbase_root_command
        self.assertEqual(testbase_root_command.name, "testbase")

    def test_verbose_option_exists(self):
        """Test that the verbose option is defined (Requirement 1.3)."""
        from automojo.testbase.cli.testbase_command import testbase_root_command
        self.assertIn("verbose", testbase_root_command.options)

    def test_verbose_option_has_short_flag(self):
        """Test that verbose option has -v short flag (Requirement 1.3)."""
        from automojo.testbase.cli.testbase_command import testbase_root_command
        verbose_option = testbase_root_command.options["verbose"]
        self.assertEqual(verbose_option.flag_short, "-v")

    def test_verbose_option_has_long_flag(self):
        """Test that verbose option has --verbose long flag (Requirement 1.3)."""
        from automojo.testbase.cli.testbase_command import testbase_root_command
        verbose_option = testbase_root_command.options["verbose"]
        self.assertEqual(verbose_option.flag_long, "--verbose")

    def test_verbose_option_has_counter_mode(self):
        """Test that verbose option uses Counter mode (Requirement 1.3)."""
        from automojo.testbase.cli.testbase_command import testbase_root_command
        verbose_option = testbase_root_command.options["verbose"]
        self.assertEqual(verbose_option.mode, OptionMode.Counter)

    def test_verbose_option_default_is_zero(self):
        """Test that verbose option default is 0 (Requirement 1.4)."""
        from automojo.testbase.cli.testbase_command import testbase_root_command
        verbose_option = testbase_root_command.options["verbose"]
        self.assertEqual(verbose_option.default, 0)


class TestbaseRootCommandVerbosityMappingTests(unittest.TestCase):
    """Tests for verbosity level mapping (Requirements 1.4-1.7)."""

    @patch('automojo.testbase.cli.testbase_command.initialize_testbase_runtime')
    @patch('automojo.testbase.cli.testbase_command.ThisApplicationSingleton')
    def test_verbose_zero_sets_warning_level_and_interactive_true(self, mock_singleton_class, mock_init_runtime):
        """Test verbose=0 sets WARNING level and interactive console enabled (Requirement 1.4)."""
        mock_this_app = MagicMock()
        mock_singleton_class.return_value = mock_this_app

        from automojo.testbase.cli.testbase_command import testbase_root_command
        from automojo.runtime.runtimevariables import RuntimeVariablesDesc

        testbase_root_command._callable(verbose=0)

        calls = mock_this_app.override_variable_value.call_args_list
        self.assertEqual(len(calls), 2)

        interactive_call = calls[0]
        self.assertEqual(interactive_call[0][0], RuntimeVariablesDesc.AM_INTERACTIVE_CONSOLE)
        self.assertTrue(interactive_call[0][1])

        log_level_call = calls[1]
        self.assertEqual(log_level_call[0][0], RuntimeVariablesDesc.AM_LOG_LEVEL_CONSOLE)
        self.assertEqual(log_level_call[0][1], "WARNING")

    @patch('automojo.testbase.cli.testbase_command.initialize_testbase_runtime')
    @patch('automojo.testbase.cli.testbase_command.ThisApplicationSingleton')
    def test_verbose_one_sets_info_level_and_interactive_false(self, mock_singleton_class, mock_init_runtime):
        """Test verbose=1 sets INFO level and interactive console disabled (Requirement 1.5)."""
        mock_this_app = MagicMock()
        mock_singleton_class.return_value = mock_this_app

        from automojo.testbase.cli.testbase_command import testbase_root_command
        from automojo.runtime.runtimevariables import RuntimeVariablesDesc

        testbase_root_command._callable(verbose=1)

        calls = mock_this_app.override_variable_value.call_args_list
        self.assertEqual(len(calls), 2)

        interactive_call = calls[0]
        self.assertEqual(interactive_call[0][0], RuntimeVariablesDesc.AM_INTERACTIVE_CONSOLE)
        self.assertFalse(interactive_call[0][1])

        log_level_call = calls[1]
        self.assertEqual(log_level_call[0][0], RuntimeVariablesDesc.AM_LOG_LEVEL_CONSOLE)
        self.assertEqual(log_level_call[0][1], "INFO")

    @patch('automojo.testbase.cli.testbase_command.initialize_testbase_runtime')
    @patch('automojo.testbase.cli.testbase_command.ThisApplicationSingleton')
    def test_verbose_two_sets_debug_level_and_interactive_false(self, mock_singleton_class, mock_init_runtime):
        """Test verbose=2 sets DEBUG level and interactive console disabled (Requirement 1.6)."""
        mock_this_app = MagicMock()
        mock_singleton_class.return_value = mock_this_app

        from automojo.testbase.cli.testbase_command import testbase_root_command
        from automojo.runtime.runtimevariables import RuntimeVariablesDesc

        testbase_root_command._callable(verbose=2)

        calls = mock_this_app.override_variable_value.call_args_list
        self.assertEqual(len(calls), 2)

        interactive_call = calls[0]
        self.assertEqual(interactive_call[0][0], RuntimeVariablesDesc.AM_INTERACTIVE_CONSOLE)
        self.assertFalse(interactive_call[0][1])

        log_level_call = calls[1]
        self.assertEqual(log_level_call[0][0], RuntimeVariablesDesc.AM_LOG_LEVEL_CONSOLE)
        self.assertEqual(log_level_call[0][1], "DEBUG")

    @patch('automojo.testbase.cli.testbase_command.initialize_testbase_runtime')
    @patch('automojo.testbase.cli.testbase_command.ThisApplicationSingleton')
    def test_verbose_three_sets_notset_level_and_interactive_false(self, mock_singleton_class, mock_init_runtime):
        """Test verbose=3 sets NOTSET level and interactive console disabled (Requirement 1.7)."""
        mock_this_app = MagicMock()
        mock_singleton_class.return_value = mock_this_app

        from automojo.testbase.cli.testbase_command import testbase_root_command
        from automojo.runtime.runtimevariables import RuntimeVariablesDesc

        testbase_root_command._callable(verbose=3)

        calls = mock_this_app.override_variable_value.call_args_list
        self.assertEqual(len(calls), 2)

        interactive_call = calls[0]
        self.assertEqual(interactive_call[0][0], RuntimeVariablesDesc.AM_INTERACTIVE_CONSOLE)
        self.assertFalse(interactive_call[0][1])

        log_level_call = calls[1]
        self.assertEqual(log_level_call[0][0], RuntimeVariablesDesc.AM_LOG_LEVEL_CONSOLE)
        self.assertEqual(log_level_call[0][1], "NOTSET")

    @patch('automojo.testbase.cli.testbase_command.initialize_testbase_runtime')
    @patch('automojo.testbase.cli.testbase_command.ThisApplicationSingleton')
    def test_verbose_greater_than_three_sets_notset_level(self, mock_singleton_class, mock_init_runtime):
        """Test verbose>3 also sets NOTSET level (Requirement 1.7)."""
        mock_this_app = MagicMock()
        mock_singleton_class.return_value = mock_this_app

        from automojo.testbase.cli.testbase_command import testbase_root_command
        from automojo.runtime.runtimevariables import RuntimeVariablesDesc

        testbase_root_command._callable(verbose=5)

        calls = mock_this_app.override_variable_value.call_args_list
        log_level_call = calls[1]
        self.assertEqual(log_level_call[0][0], RuntimeVariablesDesc.AM_LOG_LEVEL_CONSOLE)
        self.assertEqual(log_level_call[0][1], "NOTSET")


class TestbaseRootCommandRuntimeInitializationTests(unittest.TestCase):
    """Tests for runtime initialization call (Requirement 1.2)."""

    @patch('automojo.testbase.cli.testbase_command.initialize_testbase_runtime')
    @patch('automojo.testbase.cli.testbase_command.ThisApplicationSingleton')
    def test_initialize_testbase_runtime_is_called(self, mock_singleton_class, mock_init_runtime):
        """Test that initialize_testbase_runtime is called when command executes (Requirement 1.2)."""
        mock_this_app = MagicMock()
        mock_singleton_class.return_value = mock_this_app

        from automojo.testbase.cli.testbase_command import testbase_root_command

        testbase_root_command._callable(verbose=0)

        mock_init_runtime.assert_called_once()


class TestbaseRootCommandGroupRegistrationTests(unittest.TestCase):
    """Tests for command group registration (Requirements 2.1-2.3)."""

    def test_services_group_is_registered(self):
        """Test that services group is registered to root command (Requirement 2.1)."""
        from automojo.testbase.cli.testbase_command import testbase_root_command

        command_nodes = testbase_root_command._command_nodes
        self.assertIn("services", command_nodes)

    def test_testing_group_is_registered(self):
        """Test that testing group is registered to root command (Requirement 2.2)."""
        from automojo.testbase.cli.testbase_command import testbase_root_command

        command_nodes = testbase_root_command._command_nodes
        self.assertIn("testing", command_nodes)

    def test_utilities_group_is_registered(self):
        """Test that utilities group is registered to root command (Requirement 2.3)."""
        from automojo.testbase.cli.testbase_command import testbase_root_command

        command_nodes = testbase_root_command._command_nodes
        self.assertIn("utilities", command_nodes)

    def test_has_three_command_groups(self):
        """Test that root command has exactly three command groups."""
        from automojo.testbase.cli.testbase_command import testbase_root_command

        command_nodes = testbase_root_command._command_nodes
        self.assertEqual(len(command_nodes), 3)


if __name__ == '__main__':
    unittest.main()
