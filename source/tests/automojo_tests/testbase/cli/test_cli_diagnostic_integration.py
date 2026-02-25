"""
    .. module:: automojo_tests.testbase.cli.test_cli_diagnostic_integration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Integration tests for CLI diagnostic options.

    .. moduleauthor:: AutomationX

    Integration tests for the CLI diagnostic options that verify the runtime variables
    AM_DIAGNOSTICS_PRERUN and AM_DIAGNOSTICS_POSTRUN are correctly set when the
    --prerun-diagnostic and --postrun-diagnostic CLI options are specified.
    
    These tests verify Requirements 3.5, 3.6, 11.1-11.5 from the Diagnostics System specification.
"""

__author__ = "AutomationX"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import tempfile
import unittest
from unittest.mock import patch, MagicMock


class CLIDiagnosticIntegrationTests(unittest.TestCase):
    """Integration tests for CLI diagnostic options (Requirements 3.5, 3.6, 11.1-11.5)."""

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

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_diagnostics_prerun')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_prerun_diagnostic_flag_sets_runtime_variable(
        self, mock_exit, mock_factory, mock_get_logger, mock_init_results,
        mock_runtime_vars, mock_prepend, mock_testroot, mock_prerun_diag
    ):
        """
        Test --prerun-diagnostic flag sets AM_DIAGNOSTICS_PRERUN runtime variable.
        
        Requirement 3.5: WHEN --prerun-diagnostic is specified, THE System SHALL
        set the AM_DIAGNOSTICS_PRERUN runtime variable to True.
        
        Requirement 11.3: WHEN AM_DIAGNOSTICS_PRERUN is True, THE System SHALL
        enable pre-run diagnostic capture.
        """
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
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                debug_log_level=None, prerun_diagnostic=True, postrun_diagnostic=False,
                diagnostic_level=None, include_marker_exp=None, exclude_marker_exp=None
            )

        mock_prerun_diag.assert_called_once_with({})

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_diagnostics_postrun')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_postrun_diagnostic_flag_sets_runtime_variable(
        self, mock_exit, mock_factory, mock_get_logger, mock_init_results,
        mock_runtime_vars, mock_prepend, mock_testroot, mock_postrun_diag
    ):
        """
        Test --postrun-diagnostic flag sets AM_DIAGNOSTICS_POSTRUN runtime variable.
        
        Requirement 3.6: WHEN --postrun-diagnostic is specified, THE System SHALL
        set the AM_DIAGNOSTICS_POSTRUN runtime variable to True.
        
        Requirement 11.4: WHEN AM_DIAGNOSTICS_POSTRUN is True, THE System SHALL
        enable post-run diagnostic capture.
        """
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
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                debug_log_level=None, prerun_diagnostic=False, postrun_diagnostic=True,
                diagnostic_level=None, include_marker_exp=None, exclude_marker_exp=None
            )

        mock_postrun_diag.assert_called_once_with({})

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_diagnostics_postrun')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_diagnostics_prerun')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_combined_diagnostic_flags_set_both_runtime_variables(
        self, mock_exit, mock_factory, mock_get_logger, mock_init_results,
        mock_runtime_vars, mock_prepend, mock_testroot, mock_prerun_diag, mock_postrun_diag
    ):
        """
        Test combined --prerun-diagnostic and --postrun-diagnostic flags set both runtime variables.
        
        Requirements 3.5, 3.6, 11.1-11.5: Both diagnostic flags should set their
        respective runtime variables when specified together.
        """
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
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                debug_log_level=None, prerun_diagnostic=True, postrun_diagnostic=True,
                diagnostic_level=None, include_marker_exp=None, exclude_marker_exp=None
            )

        mock_prerun_diag.assert_called_once_with({})
        mock_postrun_diag.assert_called_once_with({})

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_diagnostics_postrun')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_diagnostics_prerun')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_no_diagnostic_flags_does_not_set_variables(
        self, mock_exit, mock_factory, mock_get_logger, mock_init_results,
        mock_runtime_vars, mock_prepend, mock_testroot, mock_prerun_diag, mock_postrun_diag
    ):
        """
        Test that no diagnostic flags does not set diagnostic runtime variables.
        
        Requirement 11.5: THE runtime variables SHALL be settable via CLI options
        through the runtime option override mechanism. When not specified, the
        override methods should not be called.
        """
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
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                debug_log_level=None, prerun_diagnostic=False, postrun_diagnostic=False,
                diagnostic_level=None, include_marker_exp=None, exclude_marker_exp=None
            )

        mock_prerun_diag.assert_not_called()
        mock_postrun_diag.assert_not_called()


if __name__ == '__main__':
    unittest.main()



class CLIDiagnosticLevelIntegrationTests(unittest.TestCase):
    """Integration tests for CLI --diagnostic-level option (Requirements 7.1-7.5)."""

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

    @patch('automojo.testbase.diagnostic_level.set_diagnostic_level')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_diagnostic_level_flag_sets_level(
        self, mock_exit, mock_factory, mock_get_logger, mock_init_results,
        mock_runtime_vars, mock_prepend, mock_testroot, mock_set_level
    ):
        """
        Test --diagnostic-level flag sets the diagnostic level.
        
        Requirement 7.1: THE diagnostic level parameter SHALL accept integer values from 1 to 9.
        """
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
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                debug_log_level=None, prerun_diagnostic=False, postrun_diagnostic=False,
                diagnostic_level="5", include_marker_exp=None, exclude_marker_exp=None
            )

        mock_set_level.assert_called_once_with(5)

    @patch('automojo.testbase.diagnostic_level.set_diagnostic_level')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_diagnostic_level_not_set_when_not_specified(
        self, mock_exit, mock_factory, mock_get_logger, mock_init_results,
        mock_runtime_vars, mock_prepend, mock_testroot, mock_set_level
    ):
        """
        Test that diagnostic level is not set when --diagnostic-level is not specified.
        
        Requirement 7.5: THE default diagnostic level SHALL be 9 (maximum detail) when not explicitly specified.
        """
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
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                debug_log_level=None, prerun_diagnostic=False, postrun_diagnostic=False,
                diagnostic_level=None, include_marker_exp=None, exclude_marker_exp=None
            )

        mock_set_level.assert_not_called()

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_diagnostic_level_invalid_value_raises_error(
        self, mock_exit, mock_factory, mock_get_logger, mock_init_results,
        mock_runtime_vars, mock_prepend, mock_testroot
    ):
        """
        Test that invalid diagnostic level values raise ValueError.
        
        Requirement 7.1: THE diagnostic level parameter SHALL accept integer values from 1 to 9.
        """
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = self._create_mock_job()
        mock_factory.return_value = self._create_mock_factory(mock_job)

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            
            # Test value out of range (too high)
            with self.assertRaises(ValueError) as context:
                command_testbase_testing_run._callable(
                    root=tmpdir, includes=None, excludes=None, output=None,
                    start=None, runid=None, branch=None, build=None, flavor=None,
                    job_id=None, job_initiator=None, job_label=None, job_name=None,
                    job_owner=None, console_level=None, logfile_level=None,
                    debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                    debug_log_level=None, prerun_diagnostic=False, postrun_diagnostic=False,
                    diagnostic_level="10", include_marker_exp=None, exclude_marker_exp=None
                )
            self.assertIn("between 1 and 9", str(context.exception))

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_diagnostic_level_invalid_non_integer_raises_error(
        self, mock_exit, mock_factory, mock_get_logger, mock_init_results,
        mock_runtime_vars, mock_prepend, mock_testroot
    ):
        """
        Test that non-integer diagnostic level values raise ValueError.
        
        Requirement 7.1: THE diagnostic level parameter SHALL accept integer values from 1 to 9.
        """
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = self._create_mock_job()
        mock_factory.return_value = self._create_mock_factory(mock_job)

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            
            # Test non-integer value
            with self.assertRaises(ValueError) as context:
                command_testbase_testing_run._callable(
                    root=tmpdir, includes=None, excludes=None, output=None,
                    start=None, runid=None, branch=None, build=None, flavor=None,
                    job_id=None, job_initiator=None, job_label=None, job_name=None,
                    job_owner=None, console_level=None, logfile_level=None,
                    debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                    debug_log_level=None, prerun_diagnostic=False, postrun_diagnostic=False,
                    diagnostic_level="abc", include_marker_exp=None, exclude_marker_exp=None
                )
            self.assertIn("integer between 1 and 9", str(context.exception))

    @patch('automojo.testbase.diagnostic_level.set_diagnostic_level')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_diagnostics_prerun')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_diagnostic_level_with_prerun_diagnostic(
        self, mock_exit, mock_factory, mock_get_logger, mock_init_results,
        mock_runtime_vars, mock_prepend, mock_testroot, mock_prerun_diag, mock_set_level
    ):
        """
        Test --diagnostic-level combined with --prerun-diagnostic.
        
        Requirements 7.2-7.4: Different diagnostic levels control verbosity.
        """
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
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                debug_log_level=None, prerun_diagnostic=True, postrun_diagnostic=False,
                diagnostic_level="3", include_marker_exp=None, exclude_marker_exp=None
            )

        mock_prerun_diag.assert_called_once_with({})
        mock_set_level.assert_called_once_with(3)
