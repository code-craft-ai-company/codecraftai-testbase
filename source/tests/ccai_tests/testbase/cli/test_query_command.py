"""
    .. module:: ccai_tests.testbase.cli.test_query_command
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the testing query command.

    .. moduleauthor:: CodeCraftX

    Tests for the testing query command defined in ccai.testbase.cli.cmdtree.testing.query.
    These tests verify output format structure, import error reporting, and path validation
    as specified in Requirements 10.1-10.7, 11.1-11.5.
"""

__author__ = "CodeCraftX"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import tempfile
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock


class QueryCommandDecoratorTests(unittest.TestCase):
    """Tests for query command decorator configuration (Requirements 10.1-10.6)."""

    def test_command_name_is_query(self):
        """Test that the query command is named 'query' (Requirement 10.1)."""
        from ccai.testbase.cli.cmdtree.testing.query import command_testbase_testing_query
        self.assertEqual(command_testbase_testing_query.name, "query")

    def test_root_option_exists(self):
        """Test that root option is attached (Requirement 10.2)."""
        from ccai.testbase.cli.cmdtree.testing.query import command_testbase_testing_query
        self.assertIn("root", command_testbase_testing_query.options)

    def test_includes_option_exists(self):
        """Test that includes option is attached (Requirement 10.3)."""
        from ccai.testbase.cli.cmdtree.testing.query import command_testbase_testing_query
        self.assertIn("includes", command_testbase_testing_query.options)

    def test_excludes_option_exists(self):
        """Test that excludes option is attached (Requirement 10.4)."""
        from ccai.testbase.cli.cmdtree.testing.query import command_testbase_testing_query
        self.assertIn("excludes", command_testbase_testing_query.options)

    def test_include_marker_exp_option_exists(self):
        """Test that include_marker_exp option is attached (Requirement 10.5)."""
        from ccai.testbase.cli.cmdtree.testing.query import command_testbase_testing_query
        self.assertIn("include_marker_exp", command_testbase_testing_query.options)

    def test_exclude_marker_exp_option_exists(self):
        """Test that exclude_marker_exp option is attached (Requirement 10.6)."""
        from ccai.testbase.cli.cmdtree.testing.query import command_testbase_testing_query
        self.assertIn("exclude_marker_exp", command_testbase_testing_query.options)


class QueryCommandPathValidationTests(unittest.TestCase):
    """Tests for path resolution and validation (Requirement 10.7)."""

    @patch('ccai.runtime.runtimevariables.RuntimeVariables')
    def test_raises_value_error_when_path_does_not_exist(self, mock_runtime_vars):
        """Test that ValueError is raised when root path does not exist (Requirement 10.7)."""
        mock_runtime_vars.AM_TESTROOT = None

        from ccai.testbase.cli.cmdtree.testing.query import command_testbase_testing_query

        with self.assertRaises(ValueError) as context:
            command_testbase_testing_query._callable(
                root="/nonexistent/path/that/does/not/exist",
                includes=None,
                excludes=None,
                include_marker_exp=None,
                exclude_marker_exp=None
            )

        self.assertIn("does not exist", str(context.exception))

    @patch('ccai.runtime.runtimevariables.RuntimeVariables')
    def test_error_message_includes_original_path(self, mock_runtime_vars):
        """Test that error message includes the original path (Requirement 10.7)."""
        mock_runtime_vars.AM_TESTROOT = None

        from ccai.testbase.cli.cmdtree.testing.query import command_testbase_testing_query

        nonexistent_path = "/nonexistent/path/for/testing"
        with self.assertRaises(ValueError) as context:
            command_testbase_testing_query._callable(
                root=nonexistent_path,
                includes=None,
                excludes=None,
                include_marker_exp=None,
                exclude_marker_exp=None
            )

        self.assertIn(nonexistent_path, str(context.exception))



class QueryCommandOutputFormatTests(unittest.TestCase):
    """Tests for query output format structure (Requirements 11.1-11.3)."""

    @patch('ccai.runtime.runtimevariables.RuntimeVariables')
    @patch('ccai.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('ccai.xmodules.xpython.prepend_python_path')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('ccai.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    def test_output_prints_tests_header(self, mock_factory, mock_get_logger,
                                        mock_init_results, mock_prepend,
                                        mock_testroot, mock_runtime_vars):
        """Test that query output prints 'Tests:' header (Requirement 11.1)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Create mock test job with empty query results
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.query = MagicMock(return_value={})
        mock_job.import_errors = []

        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(
            return_value=lambda *args, **kwargs: mock_job
        )
        mock_factory.return_value = mock_factory_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            from ccai.testbase.cli.cmdtree.testing.query import command_testbase_testing_query

            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                command_testbase_testing_query._callable(
                    root=tmpdir,
                    includes=None,
                    excludes=None,
                    include_marker_exp=None,
                    exclude_marker_exp=None
                )

            output = captured_output.getvalue()
            self.assertIn("Tests:", output)

    @patch('ccai.runtime.runtimevariables.RuntimeVariables')
    @patch('ccai.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('ccai.xmodules.xpython.prepend_python_path')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('ccai.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    def test_output_prints_test_names_with_four_space_indent(self, mock_factory, mock_get_logger,
                                                              mock_init_results, mock_prepend,
                                                              mock_testroot, mock_runtime_vars):
        """Test that test names are printed with 4-space indent (Requirement 11.2)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Create mock test reference with no subscriptions
        mock_test_ref = MagicMock()
        mock_test_ref.subscriptions = {}

        # Create mock test job with one test
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.query = MagicMock(return_value={
            "package.module@test_example": mock_test_ref
        })
        mock_job.import_errors = []

        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(
            return_value=lambda *args, **kwargs: mock_job
        )
        mock_factory.return_value = mock_factory_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            from ccai.testbase.cli.cmdtree.testing.query import command_testbase_testing_query

            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                command_testbase_testing_query._callable(
                    root=tmpdir,
                    includes=None,
                    excludes=None,
                    include_marker_exp=None,
                    exclude_marker_exp=None
                )

            output = captured_output.getvalue()
            self.assertIn("    package.module@test_example", output)

    @patch('ccai.runtime.runtimevariables.RuntimeVariables')
    @patch('ccai.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('ccai.xmodules.xpython.prepend_python_path')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('ccai.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    def test_output_prints_parameters_with_eight_space_indent(self, mock_factory, mock_get_logger,
                                                               mock_init_results, mock_prepend,
                                                               mock_testroot, mock_runtime_vars):
        """Test that parameter subscriptions are printed with 8-space indent (Requirement 11.3)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Create mock parameter info
        mock_param_info = MagicMock()
        mock_param_info.describe_source = MagicMock(return_value="FactorySource(scope=session)")

        # Create mock test reference with subscriptions
        mock_test_ref = MagicMock()
        mock_test_ref.subscriptions = {
            "param1": mock_param_info
        }

        # Create mock test job with one test
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.query = MagicMock(return_value={
            "package.module@test_example": mock_test_ref
        })
        mock_job.import_errors = []

        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(
            return_value=lambda *args, **kwargs: mock_job
        )
        mock_factory.return_value = mock_factory_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            from ccai.testbase.cli.cmdtree.testing.query import command_testbase_testing_query

            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                command_testbase_testing_query._callable(
                    root=tmpdir,
                    includes=None,
                    excludes=None,
                    include_marker_exp=None,
                    exclude_marker_exp=None
                )

            output = captured_output.getvalue()
            self.assertIn("        param1: FactorySource(scope=session)", output)



class QueryCommandImportErrorReportingTests(unittest.TestCase):
    """Tests for import error reporting (Requirements 11.4-11.5)."""

    @patch('ccai.runtime.runtimevariables.RuntimeVariables')
    @patch('ccai.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('ccai.xmodules.xpython.prepend_python_path')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('ccai.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    def test_import_errors_header_printed_to_stderr(self, mock_factory, mock_get_logger,
                                                     mock_init_results, mock_prepend,
                                                     mock_testroot, mock_runtime_vars):
        """Test that 'IMPORT ERRORS:' header is printed to stderr when errors occur (Requirement 11.4)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Create mock test job with import errors
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.query = MagicMock(return_value={})
        mock_job.import_errors = ["path/to/broken_module.py"]

        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(
            return_value=lambda *args, **kwargs: mock_job
        )
        mock_factory.return_value = mock_factory_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            from ccai.testbase.cli.cmdtree.testing.query import command_testbase_testing_query

            captured_stderr = StringIO()
            with patch('sys.stderr', captured_stderr), patch('sys.stdout', StringIO()):
                command_testbase_testing_query._callable(
                    root=tmpdir,
                    includes=None,
                    excludes=None,
                    include_marker_exp=None,
                    exclude_marker_exp=None
                )

            stderr_output = captured_stderr.getvalue()
            self.assertIn("IMPORT ERRORS:", stderr_output)

    @patch('ccai.runtime.runtimevariables.RuntimeVariables')
    @patch('ccai.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('ccai.xmodules.xpython.prepend_python_path')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('ccai.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    def test_import_error_filenames_printed_with_four_space_indent(self, mock_factory, mock_get_logger,
                                                                    mock_init_results, mock_prepend,
                                                                    mock_testroot, mock_runtime_vars):
        """Test that import error filenames are printed with 4-space indent to stderr (Requirement 11.5)."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Create mock test job with import errors
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.query = MagicMock(return_value={})
        mock_job.import_errors = ["path/to/broken_module.py"]

        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(
            return_value=lambda *args, **kwargs: mock_job
        )
        mock_factory.return_value = mock_factory_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            from ccai.testbase.cli.cmdtree.testing.query import command_testbase_testing_query

            captured_stderr = StringIO()
            with patch('sys.stderr', captured_stderr), patch('sys.stdout', StringIO()):
                command_testbase_testing_query._callable(
                    root=tmpdir,
                    includes=None,
                    excludes=None,
                    include_marker_exp=None,
                    exclude_marker_exp=None
                )

            stderr_output = captured_stderr.getvalue()
            self.assertIn("    path/to/broken_module.py", stderr_output)

    @patch('ccai.runtime.runtimevariables.RuntimeVariables')
    @patch('ccai.runtime.optionoverrides.AM_RUNTIME_OPTION_OVERRIDES.override_testroot')
    @patch('ccai.xmodules.xpython.prepend_python_path')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.xmodules.xlogging.enhancedloggers.getEnhancedLogger')
    @patch('ccai.thisapp.wellknown.ConfiguredSuperFactorySingleton')
    def test_no_import_errors_header_when_no_errors(self, mock_factory, mock_get_logger,
                                                     mock_init_results, mock_prepend,
                                                     mock_testroot, mock_runtime_vars):
        """Test that 'IMPORT ERRORS:' header is not printed when there are no errors."""
        mock_runtime_vars.AM_TESTROOT = None
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Create mock test job with no import errors
        mock_job = MagicMock()
        mock_job.__enter__ = MagicMock(return_value=mock_job)
        mock_job.__exit__ = MagicMock(return_value=False)
        mock_job.query = MagicMock(return_value={})
        mock_job.import_errors = []

        mock_factory_instance = MagicMock()
        mock_factory_instance.get_override_types_by_order = MagicMock(
            return_value=lambda *args, **kwargs: mock_job
        )
        mock_factory.return_value = mock_factory_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            from ccai.testbase.cli.cmdtree.testing.query import command_testbase_testing_query

            captured_stderr = StringIO()
            with patch('sys.stderr', captured_stderr), patch('sys.stdout', StringIO()):
                command_testbase_testing_query._callable(
                    root=tmpdir,
                    includes=None,
                    excludes=None,
                    include_marker_exp=None,
                    exclude_marker_exp=None
                )

            stderr_output = captured_stderr.getvalue()
            self.assertNotIn("IMPORT ERRORS:", stderr_output)


if __name__ == '__main__':
    unittest.main()
