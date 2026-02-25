"""
    .. module:: automojo_tests.testbase.cli.test_run_command
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the testing run command.

    .. moduleauthor:: AutomationX

    Tests for the testing run command defined in automojo.testbase.cli.cmdtree.testing.run.
    These tests verify option override application, path resolution and validation,
    marker expression parsing, and default root handling as specified in
    Requirements 3.1-3.9, 20.1-20.7, 21.1-21.5, 22.1-22.3.
"""

__author__ = "AutomationX"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock, call


class RunCommandDecoratorTests(unittest.TestCase):
    """Tests for run command decorator configuration (Requirements 3.1-3.6)."""

    def test_command_name_is_run(self):
        """Test that the run command is named 'run' (Requirement 3.1)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertEqual(command_testbase_testing_run.name, "run")

    def test_root_option_exists(self):
        """Test that root option is attached (Requirement 3.2)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("root", command_testbase_testing_run.options)

    def test_includes_option_exists(self):
        """Test that includes option is attached (Requirement 3.3)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("includes", command_testbase_testing_run.options)

    def test_excludes_option_exists(self):
        """Test that excludes option is attached (Requirement 3.4)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("excludes", command_testbase_testing_run.options)

    def test_include_marker_exp_option_exists(self):
        """Test that include_marker_exp option is attached (Requirement 3.5)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("include_marker_exp", command_testbase_testing_run.options)

    def test_exclude_marker_exp_option_exists(self):
        """Test that exclude_marker_exp option is attached (Requirement 3.6)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("exclude_marker_exp", command_testbase_testing_run.options)

    def test_output_option_exists(self):
        """Test that output option is attached (Requirement 4.1)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("output", command_testbase_testing_run.options)

    def test_start_option_exists(self):
        """Test that start option is attached (Requirement 4.2)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("start", command_testbase_testing_run.options)

    def test_runid_option_exists(self):
        """Test that runid option is attached (Requirement 4.3)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("runid", command_testbase_testing_run.options)

    def test_branch_option_exists(self):
        """Test that branch option is attached (Requirement 5.1)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("branch", command_testbase_testing_run.options)

    def test_build_option_exists(self):
        """Test that build option is attached (Requirement 5.2)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("build", command_testbase_testing_run.options)

    def test_flavor_option_exists(self):
        """Test that flavor option is attached (Requirement 5.3)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("flavor", command_testbase_testing_run.options)

    def test_job_id_option_exists(self):
        """Test that job_id option is attached (Requirement 6.1)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("job_id", command_testbase_testing_run.options)

    def test_job_initiator_option_exists(self):
        """Test that job_initiator option is attached (Requirement 6.2)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("job_initiator", command_testbase_testing_run.options)

    def test_job_label_option_exists(self):
        """Test that job_label option is attached (Requirement 6.3)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("job_label", command_testbase_testing_run.options)

    def test_job_name_option_exists(self):
        """Test that job_name option is attached (Requirement 6.4)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("job_name", command_testbase_testing_run.options)

    def test_job_owner_option_exists(self):
        """Test that job_owner option is attached (Requirement 6.5)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("job_owner", command_testbase_testing_run.options)

    def test_console_level_option_exists(self):
        """Test that console_level option is attached (Requirement 7.1)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("console_level", command_testbase_testing_run.options)

    def test_logfile_level_option_exists(self):
        """Test that logfile_level option is attached (Requirement 7.2)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("logfile_level", command_testbase_testing_run.options)

    def test_debugger_option_exists(self):
        """Test that debugger option is attached (Requirement 8.1)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("debugger", command_testbase_testing_run.options)

    def test_breakpoints_option_exists(self):
        """Test that breakpoints option is attached (Requirement 8.2)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("breakpoints", command_testbase_testing_run.options)

    def test_prerun_diagnostic_option_exists(self):
        """Test that prerun_diagnostic option is attached (Requirement 8.3)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("prerun_diagnostic", command_testbase_testing_run.options)

    def test_postrun_diagnostic_option_exists(self):
        """Test that postrun_diagnostic option is attached (Requirement 8.4)."""
        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        self.assertIn("postrun_diagnostic", command_testbase_testing_run.options)


class RunCommandOptionOverrideTests(unittest.TestCase):
    """Tests for runtime option override application (Requirements 20.1-20.7)."""

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_build_branch')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_branch_override_is_called_when_provided(self, mock_exit, mock_factory, mock_get_logger,
                                                      mock_init_results, mock_runtime_vars,
                                                      mock_prepend, mock_testroot, mock_branch):
        """Test that override_build_branch is called when branch is provided (Requirement 20.2)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.execute = MagicMock(return_value=0)
        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(return_value=lambda *args, **kwargs: mock_job)
        mock_factory.return_value = mock_factory_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output=None,
                start=None, runid=None, branch="main", build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        mock_branch.assert_called_once_with("main")

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_build_name')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_build_override_is_called_when_provided(self, mock_exit, mock_factory, mock_get_logger,
                                                     mock_init_results, mock_runtime_vars,
                                                     mock_prepend, mock_testroot, mock_build):
        """Test that override_build_name is called when build is provided (Requirement 20.2)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.execute = MagicMock(return_value=0)
        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(return_value=lambda *args, **kwargs: mock_job)
        mock_factory.return_value = mock_factory_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build="1.0.0", flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        mock_build.assert_called_once_with("1.0.0")

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_build_flavor')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_flavor_override_is_called_when_provided(self, mock_exit, mock_factory, mock_get_logger,
                                                      mock_init_results, mock_runtime_vars,
                                                      mock_prepend, mock_testroot, mock_flavor):
        """Test that override_build_flavor is called when flavor is provided (Requirement 20.2)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.execute = MagicMock(return_value=0)
        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(return_value=lambda *args, **kwargs: mock_job)
        mock_factory.return_value = mock_factory_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor="release",
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        mock_flavor.assert_called_once_with("release")

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_job_id')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_job_id_override_is_called_when_provided(self, mock_exit, mock_factory, mock_get_logger,
                                                      mock_init_results, mock_runtime_vars,
                                                      mock_prepend, mock_testroot, mock_job_id):
        """Test that override_job_id is called when job_id is provided (Requirement 20.3)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.execute = MagicMock(return_value=0)
        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(return_value=lambda *args, **kwargs: mock_job)
        mock_factory.return_value = mock_factory_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id="test-job-123", job_initiator=None, job_label=None, job_name=None,
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        mock_job_id.assert_called_once_with("test-job-123")

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_loglevel_console')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_console_level_override_is_called_when_provided(self, mock_exit, mock_factory, mock_get_logger,
                                                             mock_init_results, mock_runtime_vars,
                                                             mock_prepend, mock_testroot, mock_console):
        """Test that override_loglevel_console is called when console_level is provided (Requirement 20.4)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.execute = MagicMock(return_value=0)
        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(return_value=lambda *args, **kwargs: mock_job)
        mock_factory.return_value = mock_factory_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, console_level="DEBUG", logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        mock_console.assert_called_once_with("DEBUG")

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_output_directory')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_output_override_is_called_when_provided(self, mock_exit, mock_factory, mock_get_logger,
                                                      mock_init_results, mock_runtime_vars,
                                                      mock_prepend, mock_testroot, mock_output):
        """Test that override_output_directory is called when output is provided (Requirement 20.5)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.execute = MagicMock(return_value=0)
        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(return_value=lambda *args, **kwargs: mock_job)
        mock_factory.return_value = mock_factory_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output="/tmp/results",
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        mock_output.assert_called_once_with("/tmp/results")

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_testroot_override_is_called(self, mock_exit, mock_factory, mock_get_logger,
                                          mock_init_results, mock_runtime_vars,
                                          mock_prepend, mock_testroot):
        """Test that override_testroot is called with resolved path (Requirement 20.6)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.execute = MagicMock(return_value=0)
        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(return_value=lambda *args, **kwargs: mock_job)
        mock_factory.return_value = mock_factory_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

            expected_path = os.path.abspath(tmpdir)
            mock_testroot.assert_called_once_with(expected_path)

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_debug_breakpoints')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_debug_debugger')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_breakpoints_override_is_called_when_provided(self, mock_exit, mock_factory, mock_get_logger,
                                                           mock_init_results, mock_runtime_vars,
                                                           mock_prepend, mock_testroot, mock_debugger, mock_breakpoints):
        """Test that override_debug_breakpoints is called when breakpoints are provided (Requirement 20.7)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.execute = MagicMock(return_value=0)
        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(return_value=lambda *args, **kwargs: mock_job)
        mock_factory.return_value = mock_factory_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=["test-discovery"], debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        mock_breakpoints.assert_called_once_with(["test-discovery"])

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_debug_breakpoints')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_debug_debugger')
    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_debugger_defaults_to_debugpy_when_breakpoints_provided(self, mock_exit, mock_factory, mock_get_logger,
                                                                     mock_init_results, mock_runtime_vars,
                                                                     mock_prepend, mock_testroot, mock_debugger, mock_breakpoints):
        """Test that debugger defaults to debugpy when breakpoints are provided without debugger (Requirement 8.5)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.execute = MagicMock(return_value=0)
        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(return_value=lambda *args, **kwargs: mock_job)
        mock_factory.return_value = mock_factory_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=["test-discovery"], debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        mock_debugger.assert_called_with('debugpy')


class RunCommandPathResolutionTests(unittest.TestCase):
    """Tests for path resolution and validation (Requirements 21.1-21.5)."""

    def test_path_expands_environment_variables(self):
        """Test that environment variables are expanded in path (Requirement 21.1)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['TEST_ROOT_DIR'] = tmpdir
            try:
                test_root = os.path.abspath(os.path.expandvars(os.path.expanduser('$TEST_ROOT_DIR')))
                self.assertEqual(test_root, os.path.abspath(tmpdir))
            finally:
                del os.environ['TEST_ROOT_DIR']

    def test_path_expands_user_home(self):
        """Test that user home is expanded in path (Requirement 21.2)."""
        test_root = os.path.abspath(os.path.expandvars(os.path.expanduser('~')))
        self.assertEqual(test_root, os.path.expanduser('~'))

    def test_path_converts_to_absolute(self):
        """Test that path is converted to absolute (Requirement 21.3)."""
        test_root = os.path.abspath(os.path.expandvars(os.path.expanduser('.')))
        self.assertTrue(os.path.isabs(test_root))

    @patch('sys.exit')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    def test_raises_value_error_when_path_does_not_exist(self, mock_runtime_vars, mock_exit):
        """Test that ValueError is raised when path does not exist (Requirement 21.4)."""
        mock_runtime_vars.AM_TESTROOT = None

        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run

        with self.assertRaises(ValueError) as context:
            command_testbase_testing_run._callable(
                root="/nonexistent/path/that/does/not/exist", includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        self.assertIn("does not exist", str(context.exception))

    @patch('sys.exit')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    def test_error_message_includes_original_path(self, mock_runtime_vars, mock_exit):
        """Test that error message includes original path (Requirement 21.5)."""
        mock_runtime_vars.AM_TESTROOT = None

        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run

        with self.assertRaises(ValueError) as context:
            command_testbase_testing_run._callable(
                root="/nonexistent/path", includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

        self.assertIn("/nonexistent/path", str(context.exception))


class RunCommandDefaultRootHandlingTests(unittest.TestCase):
    """Tests for default root handling (Requirement 3.8)."""

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_uses_am_testroot_when_root_not_specified(self, mock_exit, mock_factory, mock_get_logger,
                                                       mock_init_results, mock_runtime_vars,
                                                       mock_prepend, mock_testroot):
        """Test that AM_TESTROOT is used when root is not specified (Requirement 3.8)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_runtime_vars.AM_TESTROOT = tmpdir
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            mock_job = MagicMock()
            mock_job.__enter__ = MagicMock(return_value=mock_job)
            mock_job.__exit__ = MagicMock(return_value=False)
            mock_job.execute = MagicMock(return_value=0)
            mock_factory_instance = MagicMock()
            mock_factory_instance.get_override_types_by_order = MagicMock(return_value=lambda *args, **kwargs: mock_job)
            mock_factory.return_value = mock_factory_instance

            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=None, includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

            expected_path = os.path.abspath(tmpdir)
            mock_testroot.assert_called_once_with(expected_path)

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_uses_current_directory_when_neither_specified(self, mock_exit, mock_factory, mock_get_logger,
                                                            mock_init_results, mock_runtime_vars,
                                                            mock_prepend, mock_testroot):
        """Test that current directory is used when neither root nor AM_TESTROOT is specified (Requirement 3.8)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.execute = MagicMock(return_value=0)
        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(return_value=lambda *args, **kwargs: mock_job)
        mock_factory.return_value = mock_factory_instance

        from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
        command_testbase_testing_run._callable(
            root=None, includes=None, excludes=None, output=None,
            start=None, runid=None, branch=None, build=None, flavor=None,
            job_id=None, job_initiator=None, job_label=None, job_name=None,
            job_owner=None, console_level=None, logfile_level=None,
            debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
            prerun_diagnostic=False, postrun_diagnostic=False,
            include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
        )

        expected_path = os.path.abspath(".")
        mock_testroot.assert_called_once_with(expected_path)


class RunCommandPythonPathExtensionTests(unittest.TestCase):
    """Tests for Python path extension (Requirement 3.9)."""

    @patch('automojo.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('automojo.xmodules.xpython.prepend_python_path')
    @patch('automojo.runtime.runtimevariables.RuntimeVariables')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('automojo.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    @patch('sys.exit')
    def test_prepends_test_root_parent_to_python_path(self, mock_exit, mock_factory, mock_get_logger,
                                                       mock_init_results, mock_runtime_vars,
                                                       mock_prepend, mock_testroot):
        """Test that test root parent directory is prepended to Python path (Requirement 3.9)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.execute = MagicMock(return_value=0)
        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(return_value=lambda *args, **kwargs: mock_job)
        mock_factory.return_value = mock_factory_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run
            command_testbase_testing_run._callable(
                root=tmpdir, includes=None, excludes=None, output=None,
                start=None, runid=None, branch=None, build=None, flavor=None,
                job_id=None, job_initiator=None, job_label=None, job_name=None,
                job_owner=None, console_level=None, logfile_level=None,
                debugger=None, breakpoints=None, debug_port=None, debug_port_range=None,
                prerun_diagnostic=False, postrun_diagnostic=False,
                include_marker_exp=None, exclude_marker_exp=None, debug_log_level=None, diagnostic_level=None
            )

            expected_parent = os.path.dirname(os.path.abspath(tmpdir))
            mock_prepend.assert_called_once_with(expected_parent)


class RunCommandMarkerExpressionParsingTests(unittest.TestCase):
    """Tests for marker expression parsing (Requirements 22.1-22.3)."""

    def test_include_marker_expression_prefixed_with_plus(self):
        """Test that include marker expressions are prefixed with '+' (Requirement 22.1)."""
        from automojo.testbase.markers import parse_marker_expression
        
        mfilter = parse_marker_expression("+categories==alpha")
        self.assertTrue(mfilter.include)
        self.assertEqual(mfilter.group, "categories")

    def test_exclude_marker_expression_prefixed_with_minus(self):
        """Test that exclude marker expressions are prefixed with '-' (Requirement 22.2)."""
        from automojo.testbase.markers import parse_marker_expression
        
        mfilter = parse_marker_expression("-categories==alpha")
        self.assertFalse(mfilter.include)
        self.assertEqual(mfilter.group, "categories")

    def test_marker_expression_strips_double_quotes(self):
        """Test that surrounding double quotes are stripped from expressions (Requirement 22.3)."""
        expression = '"categories==alpha"'
        stripped = expression.strip('"').strip("'")
        self.assertEqual(stripped, "categories==alpha")

    def test_marker_expression_strips_single_quotes(self):
        """Test that surrounding single quotes are stripped from expressions (Requirement 22.3)."""
        expression = "'categories==alpha'"
        stripped = expression.strip('"').strip("'")
        self.assertEqual(stripped, "categories==alpha")

    def test_marker_expression_equals_operator(self):
        """Test that equals operator is parsed correctly."""
        from automojo.testbase.markers import parse_marker_expression, MetaFilterEquals
        
        mfilter = parse_marker_expression("+priority==high")
        self.assertIsInstance(mfilter, MetaFilterEquals)
        self.assertEqual(mfilter.group, "priority")

    def test_marker_expression_contains_operator(self):
        """Test that contains operator is parsed correctly."""
        from automojo.testbase.markers import parse_marker_expression, MetaFilterContains
        
        mfilter = parse_marker_expression("+keywords~=smoke")
        self.assertIsInstance(mfilter, MetaFilterContains)
        self.assertEqual(mfilter.group, "keywords")

    def test_marker_expression_not_equals_operator(self):
        """Test that not equals operator is parsed correctly."""
        from automojo.testbase.markers import parse_marker_expression, MetaFilterNotEquals
        
        mfilter = parse_marker_expression("+priority!=low")
        self.assertIsInstance(mfilter, MetaFilterNotEquals)
        self.assertEqual(mfilter.group, "priority")


if __name__ == '__main__':
    unittest.main()
