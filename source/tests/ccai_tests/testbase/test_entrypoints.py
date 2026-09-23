"""
    Unit tests for the generic_test_entrypoint function.
    
    Tests verify:
    - Runtime initialization is called (Requirement 1.3)
    - Profile activation is called (Requirement 1.4)
    - Results initialization is called (Requirement 1.5)
    - Argument parsing with various options (Requirements 4.1-4.6)
"""

import argparse
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from ccai.thisapp.persona import APP_PERSONA_ESTABLISHED, establish_app_persona
from ccai.thisapp.wellknown import ThisApplicationSingleton
from ccai.runtime.enumerations import JobType
from ccai.runtime.runtimevariables import RuntimeVariablesDesc
import ccai.runtime.paths as runtime_paths


class DummyLogger:
    """A dummy logger for testing purposes."""
    def __init__(self):
        self.debug_messages = []
        self.sections = []
        self.errors = []

    def debug(self, msg):
        self.debug_messages.append(msg)

    def section(self, msg):
        self.sections.append(msg)

    def error(self, msg):
        self.errors.append(msg)

    def render(self, msg):
        pass


class DummyTestJob:
    """A dummy TestJob for testing purposes."""
    def __init__(self, logger, testroot, includes=None, excludes=None, metafilters=None, test_module=None):
        self.logger = logger
        self.testroot = testroot
        self.includes = includes
        self.excludes = excludes
        self.metafilters = metafilters
        self.test_module = test_module
        self.execute_called = False
        self.result_code = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute(self):
        self.execute_called = True
        return self.result_code


class TestGenericTestEntrypointInitialization(unittest.TestCase):
    """Tests for initialization calls in generic_test_entrypoint (Requirements 1.3, 1.4, 1.5)."""

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(name="codecraftai-testbase", logger_name="codecraftai-testbase", log_basename="codecraftai-testbase")

        self.tempdir = tempfile.TemporaryDirectory()
        
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

    def tearDown(self):
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @unittest.skip("Relocated: generic_test_entrypoint no longer performs runtime init; "
                   "moved to the integration-runtime entrypoint (testbase/integration-runtime refactor).")
    def test_runtime_initialization_is_called(self, mock_init_runtime,
                                               mock_init_results, mock_get_path, mock_get_logger,
                                               mock_find_fullname, mock_find_root, mock_exit):
        """Test that initialize_testbase_runtime is called (Requirement 1.3)."""
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        mock_find_fullname.return_value = "test.module"
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a mock test module
        mock_module = MagicMock()
        mock_module.__name__ = "__main__"
        mock_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": mock_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify initialize_testbase_runtime was called
        mock_init_runtime.assert_called_once()

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.activate_profile_job')
    @unittest.skip("Relocated: generic_test_entrypoint no longer performs profile activation; "
                   "moved to the integration-runtime entrypoint (testbase/integration-runtime refactor).")
    def test_profile_activation_is_called(self, mock_activate_profile, mock_get_path, mock_get_logger,
                                          mock_find_fullname, mock_find_root, mock_exit):
        """Test that activate_profile_job is called with JobType.TestRun (Requirement 1.4)."""
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        mock_find_fullname.return_value = "test.module"
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a mock test module
        mock_module = MagicMock()
        mock_module.__name__ = "__main__"
        mock_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": mock_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify activate_profile_job was called with JobType.TestRun
        mock_activate_profile.assert_called_once_with(job_type=JobType.TestRun)

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.activate_profile_job')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @unittest.skip("Relocated: generic_test_entrypoint no longer performs results init; "
                   "moved to the integration-runtime entrypoint (testbase/integration-runtime refactor).")
    def test_results_initialization_is_called(self, mock_init_results, mock_activate_profile,
                                               mock_get_path, mock_get_logger,
                                               mock_find_fullname, mock_find_root, mock_exit):
        """Test that initialize_testbase_results is called (Requirement 1.5)."""
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        mock_find_fullname.return_value = "test.module"
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a mock test module
        mock_module = MagicMock()
        mock_module.__name__ = "__main__"
        mock_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": mock_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify initialize_testbase_results was called
        mock_init_results.assert_called_once()

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @unittest.skip("Relocated: generic_test_entrypoint no longer orchestrates runtime/results/activation init; "
                   "moved to the integration-runtime entrypoint (testbase/integration-runtime refactor).")
    def test_initialization_order(self, mock_init_runtime, mock_init_results,
                                   mock_get_path, mock_get_logger,
                                   mock_find_fullname, mock_find_root, mock_exit):
        """Test that initialization functions are called in correct order."""
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        mock_find_fullname.return_value = "test.module"
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Track call order
        call_order = []
        mock_init_runtime.side_effect = lambda: call_order.append('runtime')
        mock_init_results.side_effect = lambda: call_order.append('results')
        
        # Create a mock test module
        mock_module = MagicMock()
        mock_module.__name__ = "__main__"
        mock_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": mock_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify order: runtime -> results
        self.assertEqual(call_order, ['runtime', 'results'])


class TestGenericTestEntrypointArgumentParsing(unittest.TestCase):
    """Tests for argument parsing in generic_test_entrypoint (Requirements 4.1-4.6)."""

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(name="codecraftai-testbase", logger_name="codecraftai-testbase", log_basename="codecraftai-testbase")

        self.tempdir = tempfile.TemporaryDirectory()
        
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

    def tearDown(self):
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    def test_include_option_short_form(self):
        """Test -i option for include expressions (Requirement 4.1)."""
        from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
        
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--include", dest="includes", action="append", default=[], help="Add an include search statement.")
        parser.add_argument("-x", "--exclude", dest="excludes", action="append", default=[], help="Add an exclude filter statement.")
        parser.add_argument("--console-level", dest="consolelevel", action="store", default="INFO", choices=LOG_LEVEL_NAMES)
        parser.add_argument("--logfile-level", dest="logfilelevel", action="store", default="DEBUG", choices=LOG_LEVEL_NAMES)
        
        args = parser.parse_args(['-i', 'test_*'])
        self.assertEqual(args.includes, ['test_*'])

    def test_include_option_long_form(self):
        """Test --include option for include expressions (Requirement 4.1)."""
        from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
        
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--include", dest="includes", action="append", default=[], help="Add an include search statement.")
        parser.add_argument("-x", "--exclude", dest="excludes", action="append", default=[], help="Add an exclude filter statement.")
        parser.add_argument("--console-level", dest="consolelevel", action="store", default="INFO", choices=LOG_LEVEL_NAMES)
        parser.add_argument("--logfile-level", dest="logfilelevel", action="store", default="DEBUG", choices=LOG_LEVEL_NAMES)
        
        args = parser.parse_args(['--include', 'test_feature_*'])
        self.assertEqual(args.includes, ['test_feature_*'])

    def test_multiple_include_options(self):
        """Test multiple -i options can be specified (Requirement 4.1)."""
        from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
        
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--include", dest="includes", action="append", default=[], help="Add an include search statement.")
        parser.add_argument("-x", "--exclude", dest="excludes", action="append", default=[], help="Add an exclude filter statement.")
        parser.add_argument("--console-level", dest="consolelevel", action="store", default="INFO", choices=LOG_LEVEL_NAMES)
        parser.add_argument("--logfile-level", dest="logfilelevel", action="store", default="DEBUG", choices=LOG_LEVEL_NAMES)
        
        args = parser.parse_args(['-i', 'test_unit_*', '-i', 'test_integration_*'])
        self.assertEqual(args.includes, ['test_unit_*', 'test_integration_*'])

    def test_exclude_option_short_form(self):
        """Test -x option for exclude expressions (Requirement 4.2)."""
        from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
        
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--include", dest="includes", action="append", default=[], help="Add an include search statement.")
        parser.add_argument("-x", "--exclude", dest="excludes", action="append", default=[], help="Add an exclude filter statement.")
        parser.add_argument("--console-level", dest="consolelevel", action="store", default="INFO", choices=LOG_LEVEL_NAMES)
        parser.add_argument("--logfile-level", dest="logfilelevel", action="store", default="DEBUG", choices=LOG_LEVEL_NAMES)
        
        args = parser.parse_args(['-x', 'test_slow_*'])
        self.assertEqual(args.excludes, ['test_slow_*'])

    def test_exclude_option_long_form(self):
        """Test --exclude option for exclude expressions (Requirement 4.2)."""
        from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
        
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--include", dest="includes", action="append", default=[], help="Add an include search statement.")
        parser.add_argument("-x", "--exclude", dest="excludes", action="append", default=[], help="Add an exclude filter statement.")
        parser.add_argument("--console-level", dest="consolelevel", action="store", default="INFO", choices=LOG_LEVEL_NAMES)
        parser.add_argument("--logfile-level", dest="logfilelevel", action="store", default="DEBUG", choices=LOG_LEVEL_NAMES)
        
        args = parser.parse_args(['--exclude', 'test_slow_*'])
        self.assertEqual(args.excludes, ['test_slow_*'])

    def test_multiple_exclude_options(self):
        """Test multiple -x options can be specified (Requirement 4.2)."""
        from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
        
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--include", dest="includes", action="append", default=[], help="Add an include search statement.")
        parser.add_argument("-x", "--exclude", dest="excludes", action="append", default=[], help="Add an exclude filter statement.")
        parser.add_argument("--console-level", dest="consolelevel", action="store", default="INFO", choices=LOG_LEVEL_NAMES)
        parser.add_argument("--logfile-level", dest="logfilelevel", action="store", default="DEBUG", choices=LOG_LEVEL_NAMES)
        
        args = parser.parse_args(['-x', 'test_slow_*', '-x', 'test_flaky_*'])
        self.assertEqual(args.excludes, ['test_slow_*', 'test_flaky_*'])

    def test_console_level_default(self):
        """Test --console-level default is INFO (Requirement 4.3)."""
        from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
        
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--include", dest="includes", action="append", default=[], help="Add an include search statement.")
        parser.add_argument("-x", "--exclude", dest="excludes", action="append", default=[], help="Add an exclude filter statement.")
        parser.add_argument("--console-level", dest="consolelevel", action="store", default="INFO", choices=LOG_LEVEL_NAMES)
        parser.add_argument("--logfile-level", dest="logfilelevel", action="store", default="DEBUG", choices=LOG_LEVEL_NAMES)
        
        args = parser.parse_args([])
        self.assertEqual(args.consolelevel, 'INFO')

    def test_console_level_custom_value(self):
        """Test --console-level accepts custom value (Requirement 4.3)."""
        from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
        
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--include", dest="includes", action="append", default=[], help="Add an include search statement.")
        parser.add_argument("-x", "--exclude", dest="excludes", action="append", default=[], help="Add an exclude filter statement.")
        parser.add_argument("--console-level", dest="consolelevel", action="store", default="INFO", choices=LOG_LEVEL_NAMES)
        parser.add_argument("--logfile-level", dest="logfilelevel", action="store", default="DEBUG", choices=LOG_LEVEL_NAMES)
        
        args = parser.parse_args(['--console-level', 'DEBUG'])
        self.assertEqual(args.consolelevel, 'DEBUG')

    def test_logfile_level_default(self):
        """Test --logfile-level default is DEBUG (Requirement 4.4)."""
        from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
        
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--include", dest="includes", action="append", default=[], help="Add an include search statement.")
        parser.add_argument("-x", "--exclude", dest="excludes", action="append", default=[], help="Add an exclude filter statement.")
        parser.add_argument("--console-level", dest="consolelevel", action="store", default="INFO", choices=LOG_LEVEL_NAMES)
        parser.add_argument("--logfile-level", dest="logfilelevel", action="store", default="DEBUG", choices=LOG_LEVEL_NAMES)
        
        args = parser.parse_args([])
        self.assertEqual(args.logfilelevel, 'DEBUG')

    def test_logfile_level_custom_value(self):
        """Test --logfile-level accepts custom value (Requirement 4.4)."""
        from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
        
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--include", dest="includes", action="append", default=[], help="Add an include search statement.")
        parser.add_argument("-x", "--exclude", dest="excludes", action="append", default=[], help="Add an exclude filter statement.")
        parser.add_argument("--console-level", dest="consolelevel", action="store", default="INFO", choices=LOG_LEVEL_NAMES)
        parser.add_argument("--logfile-level", dest="logfilelevel", action="store", default="DEBUG", choices=LOG_LEVEL_NAMES)
        
        args = parser.parse_args(['--logfile-level', 'WARNING'])
        self.assertEqual(args.logfilelevel, 'WARNING')

    def test_log_level_validates_against_allowed_names(self):
        """Test log level options validate against LOG_LEVEL_NAMES (Requirement 4.5)."""
        from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
        
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--include", dest="includes", action="append", default=[], help="Add an include search statement.")
        parser.add_argument("-x", "--exclude", dest="excludes", action="append", default=[], help="Add an exclude filter statement.")
        parser.add_argument("--console-level", dest="consolelevel", action="store", default="INFO", choices=LOG_LEVEL_NAMES)
        parser.add_argument("--logfile-level", dest="logfilelevel", action="store", default="DEBUG", choices=LOG_LEVEL_NAMES)
        
        # Test that invalid log level raises an error
        with self.assertRaises(SystemExit):
            parser.parse_args(['--console-level', 'INVALID_LEVEL'])

    def test_default_includes_to_all_when_empty(self):
        """Test that includes defaults to ['*'] when no include expressions provided (Requirement 4.6)."""
        from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
        
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--include", dest="includes", action="append", default=[], help="Add an include search statement.")
        parser.add_argument("-x", "--exclude", dest="excludes", action="append", default=[], help="Add an exclude filter statement.")
        parser.add_argument("--console-level", dest="consolelevel", action="store", default="INFO", choices=LOG_LEVEL_NAMES)
        parser.add_argument("--logfile-level", dest="logfilelevel", action="store", default="DEBUG", choices=LOG_LEVEL_NAMES)
        
        args = parser.parse_args([])
        
        # Simulate the logic in generic_test_entrypoint
        includes = args.includes
        if len(includes) == 0:
            includes.append("*")
        
        self.assertEqual(includes, ['*'])

    def test_combined_include_and_exclude_options(self):
        """Test combined include and exclude options work together."""
        from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
        
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--include", dest="includes", action="append", default=[], help="Add an include search statement.")
        parser.add_argument("-x", "--exclude", dest="excludes", action="append", default=[], help="Add an exclude filter statement.")
        parser.add_argument("--console-level", dest="consolelevel", action="store", default="INFO", choices=LOG_LEVEL_NAMES)
        parser.add_argument("--logfile-level", dest="logfilelevel", action="store", default="DEBUG", choices=LOG_LEVEL_NAMES)
        
        args = parser.parse_args(['-i', 'test_*', '-x', 'test_slow_*', '--console-level', 'WARNING'])
        
        self.assertEqual(args.includes, ['test_*'])
        self.assertEqual(args.excludes, ['test_slow_*'])
        self.assertEqual(args.consolelevel, 'WARNING')
        self.assertEqual(args.logfilelevel, 'DEBUG')


class TestLogLevelValidation(unittest.TestCase):
    """Tests for the validate_log_level function (Requirement 4.5)."""

    def test_validate_log_level_accepts_valid_levels(self):
        """Test that validate_log_level accepts all valid log level names."""
        from ccai.testbase.entrypoints import validate_log_level
        from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
        
        for level in LOG_LEVEL_NAMES:
            result = validate_log_level(level)
            self.assertEqual(result, level)

    def test_validate_log_level_case_insensitive(self):
        """Test that validate_log_level is case-insensitive."""
        from ccai.testbase.entrypoints import validate_log_level
        
        # Test lowercase
        self.assertEqual(validate_log_level('debug'), 'DEBUG')
        self.assertEqual(validate_log_level('info'), 'INFO')
        self.assertEqual(validate_log_level('warning'), 'WARNING')
        
        # Test mixed case
        self.assertEqual(validate_log_level('Debug'), 'DEBUG')
        self.assertEqual(validate_log_level('InFo'), 'INFO')

    def test_validate_log_level_rejects_invalid_level(self):
        """Test that validate_log_level raises ArgumentTypeError for invalid levels."""
        from ccai.testbase.entrypoints import validate_log_level
        
        with self.assertRaises(argparse.ArgumentTypeError) as context:
            validate_log_level('INVALID')
        
        error_message = str(context.exception)
        self.assertIn("Invalid log level 'INVALID'", error_message)
        self.assertIn("Valid options are:", error_message)

    def test_validate_log_level_error_message_includes_valid_options(self):
        """Test that the error message includes all valid log level options."""
        from ccai.testbase.entrypoints import validate_log_level
        from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
        
        with self.assertRaises(argparse.ArgumentTypeError) as context:
            validate_log_level('BADLEVEL')
        
        error_message = str(context.exception)
        # Verify all valid options are mentioned in the error message
        for level in LOG_LEVEL_NAMES:
            self.assertIn(level, error_message)

    def test_validate_log_level_error_message_is_helpful(self):
        """Test that the error message provides helpful guidance about log levels."""
        from ccai.testbase.entrypoints import validate_log_level
        
        with self.assertRaises(argparse.ArgumentTypeError) as context:
            validate_log_level('WRONG')
        
        error_message = str(context.exception)
        # Verify the error message includes helpful guidance
        self.assertIn("DEBUG", error_message)
        self.assertIn("INFO", error_message)
        self.assertIn("WARNING", error_message)
        self.assertIn("ERROR", error_message)


class TestModuleRegistration(unittest.TestCase):
    """Tests for module registration in generic_test_entrypoint (Requirements 7.1, 7.2, 7.3, 7.4)."""

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(name="codecraftai-testbase", logger_name="codecraftai-testbase", log_basename="codecraftai-testbase")

        self.tempdir = tempfile.TemporaryDirectory()
        
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

    def tearDown(self):
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    def test_parent_module_import_called_when_module_has_parent(self, mock_import_by_name, mock_init_runtime, mock_init_results,
                                                                  mock_get_path, mock_get_logger,
                                                                  mock_find_fullname, mock_find_root, mock_exit):
        """Test that parent modules are imported before registration (Requirement 7.2)."""
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        mock_find_fullname.return_value = "tests.package.subpackage.test_module"
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a mock test module
        mock_module = MagicMock()
        mock_module.__name__ = "__main__"
        mock_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": mock_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify import_by_name was called with parent module name
        mock_import_by_name.assert_called_once_with("tests.package.subpackage")

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    def test_parent_module_import_not_called_for_top_level_module(self, mock_import_by_name, mock_init_runtime, mock_init_results,
                                                                    mock_get_path, mock_get_logger,
                                                                    mock_find_fullname, mock_find_root, mock_exit):
        """Test that import_by_name is not called for top-level modules without parent (Requirement 7.2)."""
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        mock_find_fullname.return_value = "test_module"  # No parent module
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a mock test module
        mock_module = MagicMock()
        mock_module.__name__ = "__main__"
        mock_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": mock_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify import_by_name was NOT called since there's no parent module
        mock_import_by_name.assert_not_called()

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    def test_module_registered_in_sys_modules(self, mock_import_by_name, mock_init_runtime,
                                               mock_init_results, mock_get_path, mock_get_logger,
                                               mock_find_fullname, mock_find_root, mock_exit):
        """Test that test module is registered in sys.modules under full name (Requirement 7.1)."""
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "tests.package.test_module"
        mock_find_fullname.return_value = module_fullname
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a mock test module
        mock_module = MagicMock()
        mock_module.__name__ = "__main__"
        mock_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        # Track if module was registered
        registered_module = None
        
        def capture_module_registration():
            nonlocal registered_module
            if module_fullname in sys.modules:
                registered_module = sys.modules[module_fullname]
        
        with patch.dict(sys.modules, {"__main__": mock_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
                capture_module_registration()
        
        # Verify module was registered under full name
        self.assertIsNotNone(registered_module)
        self.assertEqual(registered_module, mock_module)

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    def test_module_name_attribute_updated(self, mock_import_by_name, mock_init_runtime,
                                            mock_init_results, mock_get_path, mock_get_logger,
                                            mock_find_fullname, mock_find_root, mock_exit):
        """Test that test module's __name__ attribute is updated to full module name (Requirement 7.3)."""
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "tests.package.test_module"
        mock_find_fullname.return_value = module_fullname
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a mock test module with __name__ = "__main__"
        mock_module = MagicMock()
        mock_module.__name__ = "__main__"
        mock_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": mock_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify __name__ was updated to full module name
        self.assertEqual(mock_module.__name__, module_fullname)


class TestClassModuleRemapping(unittest.TestCase):
    """Tests for class __module__ attribute remapping (Requirements 8.1-8.4)."""

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(name="codecraftai-testbase", logger_name="codecraftai-testbase", log_basename="codecraftai-testbase")

        self.tempdir = tempfile.TemporaryDirectory()
        
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

    def tearDown(self):
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    def test_class_module_attribute_updated_from_main(self, mock_import_by_name, mock_init_runtime, mock_init_results,
                                                       mock_get_path, mock_get_logger,
                                                       mock_find_fullname, mock_find_root, mock_exit):
        """Test that class __module__ attribute is updated from __main__ to full module name (Requirement 8.2)."""
        import types
        
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "tests.package.test_module"
        mock_find_fullname.return_value = module_fullname
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a real module with a class that has __module__ = "__main__"
        test_module = types.ModuleType("__main__")
        test_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        # Create a test class with __module__ = "__main__"
        class TestClass:
            pass
        TestClass.__module__ = "__main__"
        test_module.TestClass = TestClass
        
        with patch.dict(sys.modules, {"__main__": test_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify class __module__ was updated to full module name
        self.assertEqual(TestClass.__module__, module_fullname)

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    def test_class_module_attribute_not_updated_when_not_main(self, mock_import_by_name, mock_init_runtime, mock_init_results,
                                                               mock_get_path, mock_get_logger,
                                                               mock_find_fullname, mock_find_root, mock_exit):
        """Test that class __module__ attribute is NOT updated when not __main__ (Requirement 8.4)."""
        import types
        
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "tests.package.test_module"
        mock_find_fullname.return_value = module_fullname
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a real module with a class that has __module__ != "__main__"
        test_module = types.ModuleType("__main__")
        test_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        # Create a test class with __module__ = "some.other.module"
        class ImportedClass:
            pass
        original_module = "some.other.module"
        ImportedClass.__module__ = original_module
        test_module.ImportedClass = ImportedClass
        
        with patch.dict(sys.modules, {"__main__": test_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify class __module__ was NOT updated (remains original)
        self.assertEqual(ImportedClass.__module__, original_module)

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    def test_multiple_classes_remapped(self, mock_import_by_name, mock_init_runtime, mock_init_results,
                                        mock_get_path, mock_get_logger,
                                        mock_find_fullname, mock_find_root, mock_exit):
        """Test that multiple classes with __module__ = __main__ are all remapped (Requirement 8.1, 8.3)."""
        import types
        
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "tests.package.test_module"
        mock_find_fullname.return_value = module_fullname
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a real module with multiple classes
        test_module = types.ModuleType("__main__")
        test_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        # Create multiple test classes with __module__ = "__main__"
        class TestClassA:
            pass
        TestClassA.__module__ = "__main__"
        
        class TestClassB:
            pass
        TestClassB.__module__ = "__main__"
        
        # Create a class with different __module__ (should not be remapped)
        class ImportedClass:
            pass
        ImportedClass.__module__ = "external.module"
        
        test_module.TestClassA = TestClassA
        test_module.TestClassB = TestClassB
        test_module.ImportedClass = ImportedClass
        
        with patch.dict(sys.modules, {"__main__": test_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify __main__ classes were remapped
        self.assertEqual(TestClassA.__module__, module_fullname)
        self.assertEqual(TestClassB.__module__, module_fullname)
        # Verify imported class was NOT remapped
        self.assertEqual(ImportedClass.__module__, "external.module")


class TestInjectionRegistryRenaming(unittest.TestCase):
    """Tests for injection registry origin renaming (Requirements 10.1, 10.2, 10.3)."""

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(name="codecraftai-testbase", logger_name="codecraftai-testbase", log_basename="codecraftai-testbase")

        self.tempdir = tempfile.TemporaryDirectory()
        
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

    def tearDown(self):
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    @patch('ccai.testbase.entrypoints.InjectionRegistry')
    def test_injection_registry_rename_called_when_module_is_main(self, mock_registry_class, mock_import_by_name, 
                                                                   mock_init_runtime,
                                                                   mock_init_results, mock_get_path, mock_get_logger,
                                                                   mock_find_fullname, mock_find_root, mock_exit):
        """Test that InjectionRegistry.rename_resource_origins_from_main is called when module is __main__ (Requirement 10.1, 10.2)."""
        import types
        
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "tests.package.test_module"
        mock_find_fullname.return_value = module_fullname
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create mock registry instance
        mock_registry_instance = MagicMock()
        mock_registry_class.return_value = mock_registry_instance
        
        # Create a real module with __name__ = "__main__"
        test_module = types.ModuleType("__main__")
        test_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": test_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify rename_resource_origins_from_main was called with the full module name
        mock_registry_instance.rename_resource_origins_from_main.assert_called_once_with(module_fullname)

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    @patch('ccai.testbase.entrypoints.InjectionRegistry')
    def test_injection_registry_rename_called_with_correct_module_name(self, mock_registry_class, mock_import_by_name, 
                                                                        mock_init_runtime,
                                                                        mock_init_results, mock_get_path, mock_get_logger,
                                                                        mock_find_fullname, mock_find_root, mock_exit):
        """Test that rename_resource_origins_from_main is called with the correct full module name (Requirement 10.2)."""
        import types
        
        # Setup mocks with a specific module name
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "mypackage.subpackage.test_authentication"
        mock_find_fullname.return_value = module_fullname
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create mock registry instance
        mock_registry_instance = MagicMock()
        mock_registry_class.return_value = mock_registry_instance
        
        # Create a real module with __name__ = "__main__"
        test_module = types.ModuleType("__main__")
        test_module.__file__ = os.path.join(self.tempdir.name, "test_authentication.py")
        
        with patch.dict(sys.modules, {"__main__": test_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_authentication.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify rename_resource_origins_from_main was called with the exact module name
        mock_registry_instance.rename_resource_origins_from_main.assert_called_once_with("mypackage.subpackage.test_authentication")

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    @patch('ccai.testbase.entrypoints.InjectionRegistry')
    def test_injection_registry_rename_not_called_when_module_not_main(self, mock_registry_class, mock_import_by_name, 
                                                                        mock_init_runtime,
                                                                        mock_init_results, mock_get_path, mock_get_logger,
                                                                        mock_find_fullname, mock_find_root, mock_exit):
        """Test that rename_resource_origins_from_main is NOT called when module is not __main__."""
        import types
        
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "tests.package.test_module"
        mock_find_fullname.return_value = module_fullname
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create mock registry instance
        mock_registry_instance = MagicMock()
        mock_registry_class.return_value = mock_registry_instance
        
        # Create a module with __name__ != "__main__" (already has proper name)
        test_module = types.ModuleType("tests.package.test_module")
        test_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": test_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify rename_resource_origins_from_main was NOT called
        mock_registry_instance.rename_resource_origins_from_main.assert_not_called()


class TestFunctionModuleRemapping(unittest.TestCase):
    """Tests for function __module__ attribute remapping (Requirements 9.1-9.4)."""

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(name="codecraftai-testbase", logger_name="codecraftai-testbase", log_basename="codecraftai-testbase")

        self.tempdir = tempfile.TemporaryDirectory()
        
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

    def tearDown(self):
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    def test_function_module_attribute_updated_from_main(self, mock_import_by_name, mock_init_runtime, mock_init_results,
                                                          mock_get_path, mock_get_logger,
                                                          mock_find_fullname, mock_find_root, mock_exit):
        """Test that function __module__ attribute is updated from __main__ to full module name (Requirement 9.2)."""
        import types
        
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "tests.package.test_module"
        mock_find_fullname.return_value = module_fullname
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a real module with a function that has __module__ = "__main__"
        test_module = types.ModuleType("__main__")
        test_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        # Create a test function with __module__ = "__main__"
        def test_function():
            pass
        test_function.__module__ = "__main__"
        test_module.test_function = test_function
        
        with patch.dict(sys.modules, {"__main__": test_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify function __module__ was updated to full module name
        self.assertEqual(test_function.__module__, module_fullname)

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    def test_function_module_attribute_not_updated_when_not_main(self, mock_import_by_name, mock_init_runtime, mock_init_results,
                                                                  mock_get_path, mock_get_logger,
                                                                  mock_find_fullname, mock_find_root, mock_exit):
        """Test that function __module__ attribute is NOT updated when not __main__ (Requirement 9.4)."""
        import types
        
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "tests.package.test_module"
        mock_find_fullname.return_value = module_fullname
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a real module with a function that has __module__ != "__main__"
        test_module = types.ModuleType("__main__")
        test_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        # Create a function with __module__ = "some.other.module"
        def imported_function():
            pass
        original_module = "some.other.module"
        imported_function.__module__ = original_module
        test_module.imported_function = imported_function
        
        with patch.dict(sys.modules, {"__main__": test_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify function __module__ was NOT updated (remains original)
        self.assertEqual(imported_function.__module__, original_module)

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    def test_multiple_functions_remapped(self, mock_import_by_name, mock_init_runtime, mock_init_results,
                                          mock_get_path, mock_get_logger,
                                          mock_find_fullname, mock_find_root, mock_exit):
        """Test that multiple functions with __module__ = __main__ are all remapped (Requirement 9.1, 9.3)."""
        import types
        
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "tests.package.test_module"
        mock_find_fullname.return_value = module_fullname
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a real module with multiple functions
        test_module = types.ModuleType("__main__")
        test_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        # Create multiple test functions with __module__ = "__main__"
        def test_func_a():
            pass
        test_func_a.__module__ = "__main__"
        
        def test_func_b():
            pass
        test_func_b.__module__ = "__main__"
        
        # Create a function with different __module__ (should not be remapped)
        def imported_func():
            pass
        imported_func.__module__ = "external.module"
        
        test_module.test_func_a = test_func_a
        test_module.test_func_b = test_func_b
        test_module.imported_func = imported_func
        
        with patch.dict(sys.modules, {"__main__": test_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify __main__ functions were remapped
        self.assertEqual(test_func_a.__module__, module_fullname)
        self.assertEqual(test_func_b.__module__, module_fullname)
        # Verify imported function was NOT remapped
        self.assertEqual(imported_func.__module__, "external.module")


class TestEnvironmentConfiguration(unittest.TestCase):
    """Tests for environment configuration in generic_test_entrypoint (Requirements 17.1-17.4)."""

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(name="codecraftai-testbase", logger_name="codecraftai-testbase", log_basename="codecraftai-testbase")

        self.tempdir = tempfile.TemporaryDirectory()
        
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

    def tearDown(self):
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    @unittest.skip("Relocated: jobtype/environment setup moved out of generic_test_entrypoint to the "
                   "integration-runtime entrypoint (testbase/integration-runtime refactor).")
    def test_jobtype_set_to_testrun(self, mock_import_by_name, mock_init_runtime, mock_init_results,
                                     mock_get_path, mock_get_logger,
                                     mock_find_fullname, mock_find_root, mock_exit):
        """Test that jobtype is set to 'testrun' in the environment (Requirement 17.3)."""
        import types
        
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "tests.package.test_module"
        mock_find_fullname.return_value = module_fullname
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a test module
        test_module = types.ModuleType("__main__")
        test_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": test_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify jobtype was set to "testrun" in the environment
        this_app = ThisApplicationSingleton()
        env = this_app.context.lookup("/environment")
        self.assertEqual(env["jobtype"], "testrun")

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    @unittest.skip("Relocated: output-directory/results-path setup moved out of generic_test_entrypoint to the "
                   "integration-runtime entrypoint (testbase/integration-runtime refactor).")
    def test_output_directory_set_correctly(self, mock_import_by_name, mock_init_runtime, mock_init_results,
                                             mock_get_path, mock_get_logger,
                                             mock_find_fullname, mock_find_root, mock_exit):
        """Test that output_directory is set to the test results path (Requirement 17.4)."""
        import types
        
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "tests.package.test_module"
        mock_find_fullname.return_value = module_fullname
        expected_results_path = self.tempdir.name
        mock_get_path.return_value = expected_results_path
        mock_get_logger.return_value = DummyLogger()
        
        # Create a test module
        test_module = types.ModuleType("__main__")
        test_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": test_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=DummyTestJob)
        
        # Verify output_directory was set to the test results path
        this_app = ThisApplicationSingleton()
        env = this_app.context.lookup("/environment")
        self.assertEqual(env["output_directory"], expected_results_path)


if __name__ == "__main__":
    unittest.main()


class TestExitCodeHandling(unittest.TestCase):
    """Tests for exit code handling in generic_test_entrypoint (Requirements 16.1, 16.2, 16.3, 16.4)."""

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(name="codecraftai-testbase", logger_name="codecraftai-testbase", log_basename="codecraftai-testbase")

        self.tempdir = tempfile.TemporaryDirectory()
        
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

    def tearDown(self):
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    def test_exit_code_zero_for_passing_tests(self, mock_import_by_name, mock_init_runtime, mock_init_results,
                                               mock_get_path, mock_get_logger,
                                               mock_find_fullname, mock_find_root, mock_exit):
        """Test that sys.exit is called with code 0 when all tests pass (Requirement 16.1)."""
        import types
        
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "tests.package.test_module"
        mock_find_fullname.return_value = module_fullname
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a test module
        test_module = types.ModuleType("__main__")
        test_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        # Create a custom job type that returns 0 (passing)
        class PassingTestJob:
            def __init__(self, logger, testroot, includes=None, excludes=None, metafilters=None, test_module=None):
                pass
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
            def execute(self):
                return 0  # All tests pass
        
        with patch.dict(sys.modules, {"__main__": test_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=PassingTestJob)
        
        # Verify sys.exit was called with 0
        mock_exit.assert_called_once_with(0)

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    def test_exit_code_nonzero_for_failing_tests(self, mock_import_by_name, mock_init_runtime, mock_init_results,
                                                  mock_get_path, mock_get_logger,
                                                  mock_find_fullname, mock_find_root, mock_exit):
        """Test that sys.exit is called with non-zero code when tests fail (Requirement 16.2)."""
        import types
        
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "tests.package.test_module"
        mock_find_fullname.return_value = module_fullname
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a test module
        test_module = types.ModuleType("__main__")
        test_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        # Create a custom job type that returns -1 (failing)
        class FailingTestJob:
            def __init__(self, logger, testroot, includes=None, excludes=None, metafilters=None, test_module=None):
                pass
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
            def execute(self):
                return -1  # Tests failed
        
        with patch.dict(sys.modules, {"__main__": test_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=FailingTestJob)
        
        # Verify sys.exit was called with non-zero code
        mock_exit.assert_called_once_with(-1)

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    def test_exit_code_from_testjob_execute(self, mock_import_by_name, mock_init_runtime, mock_init_results,
                                             mock_get_path, mock_get_logger,
                                             mock_find_fullname, mock_find_root, mock_exit):
        """Test that exit code is the result code returned by TestJob.execute() (Requirement 16.3)."""
        import types
        
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "tests.package.test_module"
        mock_find_fullname.return_value = module_fullname
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a test module
        test_module = types.ModuleType("__main__")
        test_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        # Create a custom job type that returns a specific code
        specific_code = 42
        
        class CustomCodeTestJob:
            def __init__(self, logger, testroot, includes=None, excludes=None, metafilters=None, test_module=None):
                pass
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
            def execute(self):
                return specific_code
        
        with patch.dict(sys.modules, {"__main__": test_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=CustomCodeTestJob)
        
        # Verify sys.exit was called with the exact code from execute()
        mock_exit.assert_called_once_with(specific_code)

    @patch('sys.exit')
    @patch('ccai.testbase.entrypoints.find_testmodule_root')
    @patch('ccai.testbase.entrypoints.find_testmodule_fullname')
    @patch('ccai.testbase.entrypoints.getEnhancedLogger')
    @patch('ccai.thisapp.paths.get_path_for_testresults')
    @patch('ccai.testbase.initialize.initialize_testbase_results')
    @patch('ccai.testbase.initialize.initialize_testbase_runtime')
    @patch('ccai.testbase.entrypoints.import_by_name')
    def test_sys_exit_is_called_with_result_code(self, mock_import_by_name, mock_init_runtime, mock_init_results,
                                                  mock_get_path, mock_get_logger,
                                                  mock_find_fullname, mock_find_root, mock_exit):
        """Test that sys.exit() is called with the result code (Requirement 16.4)."""
        import types
        
        # Setup mocks
        mock_find_root.return_value = self.tempdir.name
        module_fullname = "tests.package.test_module"
        mock_find_fullname.return_value = module_fullname
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a test module
        test_module = types.ModuleType("__main__")
        test_module.__file__ = os.path.join(self.tempdir.name, "test_module.py")
        
        # Track if execute was called and what code was returned
        execute_called = []
        
        class TrackingTestJob:
            def __init__(self, logger, testroot, includes=None, excludes=None, metafilters=None, test_module=None):
                pass
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
            def execute(self):
                execute_called.append(True)
                return 0
        
        with patch.dict(sys.modules, {"__main__": test_module, "ccai.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=TrackingTestJob)
        
        # Verify execute was called
        self.assertEqual(len(execute_called), 1)
        # Verify sys.exit was called exactly once
        self.assertEqual(mock_exit.call_count, 1)
        # Verify sys.exit was called with the result code
        mock_exit.assert_called_with(0)


class TestMarkerExpressionValidation(unittest.TestCase):
    """Tests for the validate_marker_expression function."""

    def test_validate_marker_expression_accepts_include_equals(self):
        """Test that validate_marker_expression accepts include equals expressions."""
        from ccai.testbase.entrypoints import validate_marker_expression
        
        result = validate_marker_expression('+categories==unit')
        self.assertEqual(result, '+categories==unit')

    def test_validate_marker_expression_accepts_include_contains(self):
        """Test that validate_marker_expression accepts include contains expressions."""
        from ccai.testbase.entrypoints import validate_marker_expression
        
        result = validate_marker_expression('+keywords~=smoke')
        self.assertEqual(result, '+keywords~=smoke')

    def test_validate_marker_expression_accepts_exclude_equals(self):
        """Test that validate_marker_expression accepts exclude equals expressions."""
        from ccai.testbase.entrypoints import validate_marker_expression
        
        result = validate_marker_expression('-priority==1')
        self.assertEqual(result, '-priority==1')

    def test_validate_marker_expression_accepts_exclude_contains(self):
        """Test that validate_marker_expression accepts exclude contains expressions."""
        from ccai.testbase.entrypoints import validate_marker_expression
        
        result = validate_marker_expression('-categories~=slow')
        self.assertEqual(result, '-categories~=slow')

    def test_validate_marker_expression_accepts_not_equals(self):
        """Test that validate_marker_expression accepts not equals expressions."""
        from ccai.testbase.entrypoints import validate_marker_expression
        
        result = validate_marker_expression('+priority!=3')
        self.assertEqual(result, '+priority!=3')

    def test_validate_marker_expression_rejects_invalid_expression(self):
        """Test that validate_marker_expression raises ArgumentTypeError for invalid expressions."""
        from ccai.testbase.entrypoints import validate_marker_expression
        
        with self.assertRaises(argparse.ArgumentTypeError) as context:
            validate_marker_expression('invalid')
        
        error_message = str(context.exception)
        self.assertIn("Invalid marker expression 'invalid'", error_message)

    def test_validate_marker_expression_rejects_missing_prefix(self):
        """Test that validate_marker_expression raises ArgumentTypeError for expressions without + or - prefix."""
        from ccai.testbase.entrypoints import validate_marker_expression
        
        with self.assertRaises(argparse.ArgumentTypeError) as context:
            validate_marker_expression('categories==unit')
        
        error_message = str(context.exception)
        self.assertIn("Invalid marker expression", error_message)

    def test_validate_marker_expression_error_message_includes_examples(self):
        """Test that the error message includes helpful examples."""
        from ccai.testbase.entrypoints import validate_marker_expression
        
        with self.assertRaises(argparse.ArgumentTypeError) as context:
            validate_marker_expression('bad')
        
        error_message = str(context.exception)
        self.assertIn("+categories~=unit", error_message)
        self.assertIn("-priority==1", error_message)


class TestMarkerArgumentParsing(unittest.TestCase):
    """Tests for marker argument parsing in generic_test_entrypoint."""

    def test_include_marker_option(self):
        """Test --include-marker option for marker-based include filters."""
        from ccai.testbase.entrypoints import validate_marker_expression
        
        parser = argparse.ArgumentParser()
        parser.add_argument("--include-marker", dest="include_markers", action="append", default=[], 
                          type=validate_marker_expression, metavar="EXPR")
        
        args = parser.parse_args(['--include-marker', '+categories~=unit'])
        self.assertEqual(args.include_markers, ['+categories~=unit'])

    def test_exclude_marker_option(self):
        """Test --exclude-marker option for marker-based exclude filters."""
        from ccai.testbase.entrypoints import validate_marker_expression
        
        parser = argparse.ArgumentParser()
        parser.add_argument("--exclude-marker", dest="exclude_markers", action="append", default=[], 
                          type=validate_marker_expression, metavar="EXPR")
        
        # Use = syntax to avoid argparse interpreting - as option prefix
        args = parser.parse_args(['--exclude-marker=-categories~=slow'])
        self.assertEqual(args.exclude_markers, ['-categories~=slow'])

    def test_multiple_include_marker_options(self):
        """Test multiple --include-marker options can be specified."""
        from ccai.testbase.entrypoints import validate_marker_expression
        
        parser = argparse.ArgumentParser()
        parser.add_argument("--include-marker", dest="include_markers", action="append", default=[], 
                          type=validate_marker_expression, metavar="EXPR")
        
        args = parser.parse_args(['--include-marker', '+categories~=unit', '--include-marker', '+priority==1'])
        self.assertEqual(args.include_markers, ['+categories~=unit', '+priority==1'])

    def test_multiple_exclude_marker_options(self):
        """Test multiple --exclude-marker options can be specified."""
        from ccai.testbase.entrypoints import validate_marker_expression
        
        parser = argparse.ArgumentParser()
        parser.add_argument("--exclude-marker", dest="exclude_markers", action="append", default=[], 
                          type=validate_marker_expression, metavar="EXPR")
        
        # Use = syntax to avoid argparse interpreting - as option prefix
        args = parser.parse_args(['--exclude-marker=-categories~=slow', '--exclude-marker=-priority==3'])
        self.assertEqual(args.exclude_markers, ['-categories~=slow', '-priority==3'])

    def test_combined_include_and_exclude_marker_options(self):
        """Test combined include and exclude marker options work together."""
        from ccai.testbase.entrypoints import validate_marker_expression
        
        parser = argparse.ArgumentParser()
        parser.add_argument("--include-marker", dest="include_markers", action="append", default=[], 
                          type=validate_marker_expression, metavar="EXPR")
        parser.add_argument("--exclude-marker", dest="exclude_markers", action="append", default=[], 
                          type=validate_marker_expression, metavar="EXPR")
        
        # Use = syntax for exclude marker to avoid argparse interpreting - as option prefix
        args = parser.parse_args(['--include-marker', '+categories~=unit', '--exclude-marker=-categories~=slow'])
        self.assertEqual(args.include_markers, ['+categories~=unit'])
        self.assertEqual(args.exclude_markers, ['-categories~=slow'])

    def test_marker_option_validates_expression(self):
        """Test that marker options validate expressions."""
        from ccai.testbase.entrypoints import validate_marker_expression
        
        parser = argparse.ArgumentParser()
        parser.add_argument("--include-marker", dest="include_markers", action="append", default=[], 
                          type=validate_marker_expression, metavar="EXPR")
        
        # Test that invalid marker expression raises an error
        with self.assertRaises(SystemExit):
            parser.parse_args(['--include-marker', 'invalid'])


if __name__ == '__main__':
    unittest.main()
