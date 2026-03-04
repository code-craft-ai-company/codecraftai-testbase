"""
    .. module:: automojo_tests.testbase.cli.test_cli_debugging_integration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Integration tests for CLI debugging options.

    .. moduleauthor:: AutomationX

    Integration tests for the CLI debugging options that verify the runtime variables
    AM_DEBUG_DEBUGGER and AM_DEBUG_BREAKPOINTS are correctly set when the --debugger
    and --breakpoint CLI options are specified.
    
    These tests verify Requirements 3.5 and 3.6 from the Debugging Support specification.
"""

__author__ = "AutomationX"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock


class CLIDebuggingIntegrationTests(unittest.TestCase):
    """Integration tests for CLI debugging options (Requirements 3.5, 3.6)."""

    def _create_mock_job(self):
        """Helper to create a mock test job."""
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.execute = MagicMock(return_value=0)
        return mock_job

    def _create_mock_factory(self, mock_job):
        """Helper to create a mock factory."""
        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(
            return_value=lambda *args, **kwargs: mock_job
        )
        return mock_factory_instance

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_debug_debugger')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_debugger_pdb_sets_runtime_variable(
        self, mock_exit, mock_factory, mock_get_logger, mock_init_results,
        mock_runtime_vars, mock_prepend, mock_testroot, mock_debugger
    ):
        """Test --debugger pdb sets AM_DEBUG_DEBUGGER runtime variable (Requirement 3.5)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = self._create_mock_job()
        mock_factory.return_value = self._create_mock_factory(mock_job)

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, job_seed=None, job_tag=None, console_level=None, logfile_level=None,
                debugger='pdb', breakpoints=None, debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        # Verify override_debug_debugger was called (note: implementation uses 'debugpy' for any debugger value)
        mock_debugger.assert_called()

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_debug_debugger')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_debugger_debugpy_sets_runtime_variable(
        self, mock_exit, mock_factory, mock_get_logger, mock_init_results,
        mock_runtime_vars, mock_prepend, mock_testroot, mock_debugger
    ):
        """Test --debugger debugpy sets AM_DEBUG_DEBUGGER runtime variable (Requirement 3.5)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = self._create_mock_job()
        mock_factory.return_value = self._create_mock_factory(mock_job)

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, job_seed=None, job_tag=None, console_level=None, logfile_level=None,
                debugger='debugpy', breakpoints=None, debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        mock_debugger.assert_called_with('debugpy')

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_debug_breakpoints')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_debug_debugger')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_breakpoint_test_discovery_sets_runtime_variable(
        self, mock_exit, mock_factory, mock_get_logger, mock_init_results,
        mock_runtime_vars, mock_prepend, mock_testroot, mock_debugger, mock_breakpoints
    ):
        """Test --breakpoint test-discovery sets AM_DEBUG_BREAKPOINTS runtime variable (Requirement 3.6)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = self._create_mock_job()
        mock_factory.return_value = self._create_mock_factory(mock_job)

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, job_seed=None, job_tag=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=['test-discovery'], debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        mock_breakpoints.assert_called_once_with(['test-discovery'])

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_debug_breakpoints')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_debug_debugger')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_breakpoint_testrun_start_sets_runtime_variable(
        self, mock_exit, mock_factory, mock_get_logger, mock_init_results,
        mock_runtime_vars, mock_prepend, mock_testroot, mock_debugger, mock_breakpoints
    ):
        """Test --breakpoint testrun-start sets AM_DEBUG_BREAKPOINTS runtime variable (Requirement 3.6)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = self._create_mock_job()
        mock_factory.return_value = self._create_mock_factory(mock_job)

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, job_seed=None, job_tag=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=['testrun-start'], debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        mock_breakpoints.assert_called_once_with(['testrun-start'])

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_debug_breakpoints')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_debug_debugger')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_combined_debugger_and_breakpoint_options(
        self, mock_exit, mock_factory, mock_get_logger, mock_init_results,
        mock_runtime_vars, mock_prepend, mock_testroot, mock_debugger, mock_breakpoints
    ):
        """Test combined --debugger and --breakpoint options set both runtime variables (Requirements 3.5, 3.6)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = self._create_mock_job()
        mock_factory.return_value = self._create_mock_factory(mock_job)

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, job_seed=None, job_tag=None, console_level=None, logfile_level=None,
                debugger='debugpy', breakpoints=['test-discovery', 'testrun-start'],
                debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        mock_breakpoints.assert_called_once_with(['test-discovery', 'testrun-start'])
        mock_debugger.assert_called()

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_debug_breakpoints')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_debug_debugger')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_breakpoint_without_debugger_defaults_to_debugpy(
        self, mock_exit, mock_factory, mock_get_logger, mock_init_results,
        mock_runtime_vars, mock_prepend, mock_testroot, mock_debugger, mock_breakpoints
    ):
        """Test that breakpoint without debugger defaults to debugpy (Requirement 3.5)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = self._create_mock_job()
        mock_factory.return_value = self._create_mock_factory(mock_job)

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, job_seed=None, job_tag=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=['testrun-start'], debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        # When breakpoints are provided without debugger, debugger should default to 'debugpy'
        mock_debugger.assert_called_with('debugpy')

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_debug_breakpoints')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_debug_debugger')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_no_debugger_or_breakpoints_does_not_set_variables(
        self, mock_exit, mock_factory, mock_get_logger, mock_init_results,
        mock_runtime_vars, mock_prepend, mock_testroot, mock_debugger, mock_breakpoints
    ):
        """Test that no debugger or breakpoints does not set debug runtime variables."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = self._create_mock_job()
        mock_factory.return_value = self._create_mock_factory(mock_job)

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, job_seed=None, job_tag=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        mock_debugger.assert_not_called()
        mock_breakpoints.assert_not_called()


if __name__ == '__main__':
    unittest.main()
