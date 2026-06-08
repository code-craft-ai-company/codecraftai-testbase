"""
    .. module:: ccai_tests.testbase.cli.test_results_command
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the services results command.

    .. moduleauthor:: CodeCraftX

    Tests for the services results command defined in ccai.testbase.cli.cmdtree.services.results.
    These tests verify command decorator configuration, default directory resolution,
    and server configuration as specified in Requirements 16.1-16.7.
"""

__author__ = "CodeCraftX"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock


class ResultsCommandDecoratorTests(unittest.TestCase):
    """Tests for results command decorator configuration (Requirements 16.1-16.4)."""

    def test_command_name_is_results(self):
        """Test that the results command is named 'results' (Requirement 16.1)."""
        from ccai.testbase.cli.cmdtree.services.results import command_testbase_services_results
        self.assertEqual(command_testbase_services_results.name, "results")

    def test_directory_option_exists(self):
        """Test that directory option is attached (Requirement 16.2)."""
        from ccai.testbase.cli.cmdtree.services.results import command_testbase_services_results
        self.assertIn("directory", command_testbase_services_results.options)

    def test_directory_option_default_is_none(self):
        """Test that directory option default is None (Requirement 16.5)."""
        from ccai.testbase.cli.cmdtree.services.results import command_testbase_services_results
        directory_option = command_testbase_services_results.options["directory"]
        self.assertIsNone(directory_option.default)

    def test_bind_option_exists(self):
        """Test that bind option is attached (Requirement 16.3)."""
        from ccai.testbase.cli.cmdtree.services.results import command_testbase_services_results
        self.assertIn("bind", command_testbase_services_results.options)

    def test_bind_option_default_is_empty_string(self):
        """Test that bind option default is empty string for all interfaces (Requirement 16.3)."""
        from ccai.testbase.cli.cmdtree.services.results import command_testbase_services_results
        bind_option = command_testbase_services_results.options["bind"]
        self.assertEqual(bind_option.default, "")

    def test_port_option_exists(self):
        """Test that port option is attached (Requirement 16.4)."""
        from ccai.testbase.cli.cmdtree.services.results import command_testbase_services_results
        self.assertIn("port", command_testbase_services_results.options)

    def test_port_option_default_is_8880(self):
        """Test that port option default is 8880 (Requirement 16.4)."""
        from ccai.testbase.cli.cmdtree.services.results import command_testbase_services_results
        port_option = command_testbase_services_results.options["port"]
        self.assertEqual(port_option.default, 8880)


class ResultsCommandDefaultDirectoryTests(unittest.TestCase):
    """Tests for default directory resolution (Requirement 16.5)."""

    @patch('ccai.testbase.cli.cmdtree.services.results.TestResultServer')
    @patch('ccai.testbase.cli.cmdtree.services.results.try_create_bug_server_interface_from_environment')
    @patch('ccai.testbase.cli.cmdtree.services.results.get_presence_directory')
    @patch('ccai.testbase.cli.cmdtree.services.results.activate_profile_service')
    @patch('ccai.testbase.cli.cmdtree.services.results.ThisApplicationSingleton')
    @patch('builtins.print')
    def test_default_directory_uses_presence_dir_results(self, mock_print, mock_this_app, 
                                                          mock_activate, mock_get_presence,
                                                          mock_bug_svc, mock_server):
        """Test that default directory is <presence_dir>/results when not specified (Requirement 16.5)."""
        mock_this_app_instance = MagicMock()
        mock_this_app.return_value = mock_this_app_instance
        mock_get_presence.return_value = "/home/user/.ccai"
        mock_bug_svc.return_value = None
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        # Make serve_forever raise an exception to exit the function
        mock_server_instance.serve_forever.side_effect = KeyboardInterrupt()

        from ccai.testbase.cli.cmdtree.services.results import command_testbase_services_results

        try:
            command_testbase_services_results._callable(directory=None, bind="", port=8880)
        except KeyboardInterrupt:
            pass

        expected_directory = os.path.join("/home/user/.ccai", "results")
        mock_server.assert_called_once()
        call_args = mock_server.call_args
        self.assertEqual(call_args[0][0], expected_directory)

    @patch('ccai.testbase.cli.cmdtree.services.results.TestResultServer')
    @patch('ccai.testbase.cli.cmdtree.services.results.try_create_bug_server_interface_from_environment')
    @patch('ccai.testbase.cli.cmdtree.services.results.get_presence_directory')
    @patch('ccai.testbase.cli.cmdtree.services.results.activate_profile_service')
    @patch('ccai.testbase.cli.cmdtree.services.results.ThisApplicationSingleton')
    @patch('builtins.print')
    def test_custom_directory_is_resolved_to_absolute_path(self, mock_print, mock_this_app,
                                                            mock_activate, mock_get_presence,
                                                            mock_bug_svc, mock_server):
        """Test that custom directory is resolved to absolute path (Requirement 16.2)."""
        mock_this_app_instance = MagicMock()
        mock_this_app.return_value = mock_this_app_instance
        mock_bug_svc.return_value = None
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        mock_server_instance.serve_forever.side_effect = KeyboardInterrupt()

        with tempfile.TemporaryDirectory() as tmpdir:
            from ccai.testbase.cli.cmdtree.services.results import command_testbase_services_results

            try:
                command_testbase_services_results._callable(directory=tmpdir, bind="", port=8880)
            except KeyboardInterrupt:
                pass

            expected_directory = os.path.abspath(tmpdir)
            mock_server.assert_called_once()
            call_args = mock_server.call_args
            self.assertEqual(call_args[0][0], expected_directory)


class ResultsCommandServerConfigurationTests(unittest.TestCase):
    """Tests for server configuration (Requirements 16.3, 16.4, 16.6, 16.7)."""

    @patch('ccai.testbase.cli.cmdtree.services.results.TestResultServer')
    @patch('ccai.testbase.cli.cmdtree.services.results.try_create_bug_server_interface_from_environment')
    @patch('ccai.testbase.cli.cmdtree.services.results.get_presence_directory')
    @patch('ccai.testbase.cli.cmdtree.services.results.activate_profile_service')
    @patch('ccai.testbase.cli.cmdtree.services.results.ThisApplicationSingleton')
    @patch('builtins.print')
    def test_server_endpoint_uses_bind_and_port(self, mock_print, mock_this_app,
                                                 mock_activate, mock_get_presence,
                                                 mock_bug_svc, mock_server):
        """Test that server endpoint uses bind and port parameters (Requirements 16.3, 16.4)."""
        mock_this_app_instance = MagicMock()
        mock_this_app.return_value = mock_this_app_instance
        mock_get_presence.return_value = "/home/user/.ccai"
        mock_bug_svc.return_value = None
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        mock_server_instance.serve_forever.side_effect = KeyboardInterrupt()

        from ccai.testbase.cli.cmdtree.services.results import command_testbase_services_results

        try:
            command_testbase_services_results._callable(directory=None, bind="127.0.0.1", port=9000)
        except KeyboardInterrupt:
            pass

        mock_server.assert_called_once()
        call_args = mock_server.call_args
        expected_endpoint = ("127.0.0.1", 9000)
        self.assertEqual(call_args[0][1], expected_endpoint)

    @patch('ccai.testbase.cli.cmdtree.services.results.TestResultServer')
    @patch('ccai.testbase.cli.cmdtree.services.results.try_create_bug_server_interface_from_environment')
    @patch('ccai.testbase.cli.cmdtree.services.results.get_presence_directory')
    @patch('ccai.testbase.cli.cmdtree.services.results.activate_profile_service')
    @patch('ccai.testbase.cli.cmdtree.services.results.ThisApplicationSingleton')
    @patch('builtins.print')
    def test_startup_message_is_printed(self, mock_print, mock_this_app,
                                         mock_activate, mock_get_presence,
                                         mock_bug_svc, mock_server):
        """Test that startup message is printed with port and directory (Requirement 16.6)."""
        mock_this_app_instance = MagicMock()
        mock_this_app.return_value = mock_this_app_instance
        mock_get_presence.return_value = "/home/user/.ccai"
        mock_bug_svc.return_value = None
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        mock_server_instance.serve_forever.side_effect = KeyboardInterrupt()

        from ccai.testbase.cli.cmdtree.services.results import command_testbase_services_results

        try:
            command_testbase_services_results._callable(directory="/custom/results", bind="", port=8880)
        except KeyboardInterrupt:
            pass

        mock_print.assert_called_once()
        print_call_args = mock_print.call_args[0][0]
        self.assertIn("8880", print_call_args)
        self.assertIn("/custom/results", print_call_args)

    @patch('ccai.testbase.cli.cmdtree.services.results.TestResultServer')
    @patch('ccai.testbase.cli.cmdtree.services.results.try_create_bug_server_interface_from_environment')
    @patch('ccai.testbase.cli.cmdtree.services.results.get_presence_directory')
    @patch('ccai.testbase.cli.cmdtree.services.results.activate_profile_service')
    @patch('ccai.testbase.cli.cmdtree.services.results.ThisApplicationSingleton')
    @patch('builtins.print')
    def test_serve_forever_is_called(self, mock_print, mock_this_app,
                                      mock_activate, mock_get_presence,
                                      mock_bug_svc, mock_server):
        """Test that serve_forever is called to run server indefinitely (Requirement 16.7)."""
        mock_this_app_instance = MagicMock()
        mock_this_app.return_value = mock_this_app_instance
        mock_get_presence.return_value = "/home/user/.ccai"
        mock_bug_svc.return_value = None
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        mock_server_instance.serve_forever.side_effect = KeyboardInterrupt()

        from ccai.testbase.cli.cmdtree.services.results import command_testbase_services_results

        try:
            command_testbase_services_results._callable(directory=None, bind="", port=8880)
        except KeyboardInterrupt:
            pass

        mock_server_instance.serve_forever.assert_called_once()

    @patch('ccai.testbase.cli.cmdtree.services.results.TestResultServer')
    @patch('ccai.testbase.cli.cmdtree.services.results.TestResultRequestHandler')
    @patch('ccai.testbase.cli.cmdtree.services.results.try_create_bug_server_interface_from_environment')
    @patch('ccai.testbase.cli.cmdtree.services.results.get_presence_directory')
    @patch('ccai.testbase.cli.cmdtree.services.results.activate_profile_service')
    @patch('ccai.testbase.cli.cmdtree.services.results.ThisApplicationSingleton')
    @patch('builtins.print')
    def test_server_uses_test_result_request_handler(self, mock_print, mock_this_app,
                                                      mock_activate, mock_get_presence,
                                                      mock_bug_svc, mock_handler, mock_server):
        """Test that server uses TestResultRequestHandler (Requirement 16.1)."""
        mock_this_app_instance = MagicMock()
        mock_this_app.return_value = mock_this_app_instance
        mock_get_presence.return_value = "/home/user/.ccai"
        mock_bug_svc.return_value = None
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        mock_server_instance.serve_forever.side_effect = KeyboardInterrupt()

        from ccai.testbase.cli.cmdtree.services.results import command_testbase_services_results

        try:
            command_testbase_services_results._callable(directory=None, bind="", port=8880)
        except KeyboardInterrupt:
            pass

        mock_server.assert_called_once()
        call_args = mock_server.call_args
        self.assertEqual(call_args[0][2], mock_handler)


class ResultsCommandServiceGroupTests(unittest.TestCase):
    """Tests for services group registration."""

    def test_results_command_is_in_services_group(self):
        """Test that results command is registered in services group."""
        from ccai.testbase.cli.cmdtree.services import group_testbase_services
        from ccai.testbase.cli.cmdtree.services.results import command_testbase_services_results
        
        # Check that the command is in the group's command nodes
        self.assertIn(command_testbase_services_results.name, 
                      group_testbase_services._command_nodes.keys())


if __name__ == "__main__":
    unittest.main()
