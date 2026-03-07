"""
    Integration tests for custom job types with the entry point system.
    
    Tests verify:
    - Custom TestJob subclass is used for execution (Requirements 14.1, 14.2, 14.3, 14.4)
    - Custom job type receives correct parameters
    - Custom job type lifecycle methods are called
    
    Requirements: 14.1, 14.2, 14.3, 14.4
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from automojo.thisapp.persona import APP_PERSONA_ESTABLISHED, establish_app_persona
from automojo.thisapp.wellknown import ThisApplicationSingleton
from automojo.runtime.enumerations import JobType
from automojo.runtime.runtimevariables import RuntimeVariablesDesc
import automojo.runtime.paths as runtime_paths

from automojo.testbase.testjob import TestJob, DefaultTestJob


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


class CustomTestJob(TestJob):
    """
    A custom TestJob subclass for testing custom job type support.
    
    This class tracks whether it was instantiated and executed,
    allowing tests to verify that custom job types are properly used.
    """
    
    name = "Custom Test Job"
    description = "A custom test job for integration testing"
    
    # Class-level tracking for test verification
    instances_created = []
    execute_calls = []
    
    def __init__(self, logger, testroot, includes=None, excludes=None, 
                 metafilters=None, test_module=None, parser=None):
        super().__init__(logger, testroot, includes=includes, excludes=excludes,
                        metafilters=metafilters, test_module=test_module, parser=parser)
        # Track instance creation
        CustomTestJob.instances_created.append({
            'testroot': testroot,
            'includes': includes,
            'excludes': excludes,
            'test_module': test_module
        })
    
    def begin(self):
        """Override begin to avoid path resolution dependencies."""
        pass
    
    def finalize(self):
        """Override finalize to avoid cleanup dependencies."""
        pass
    
    def execute(self):
        """Override execute to track calls and return success."""
        CustomTestJob.execute_calls.append({
            'testroot': self._testroot,
            'includes': self.includes,
            'excludes': self.excludes
        })
        # Return 0 to indicate success
        return 0
    
    @classmethod
    def reset_tracking(cls):
        """Reset tracking lists for test isolation."""
        cls.instances_created = []
        cls.execute_calls = []


class FailingCustomTestJob(TestJob):
    """
    A custom TestJob that returns a non-zero exit code.
    
    Used to verify that custom job result codes are properly propagated.
    """
    
    name = "Failing Custom Test Job"
    description = "A custom test job that always fails"
    
    def begin(self):
        """Override begin to avoid path resolution dependencies."""
        pass
    
    def finalize(self):
        """Override finalize to avoid cleanup dependencies."""
        pass
    
    def execute(self):
        """Return non-zero to indicate failure."""
        return 1


class TestCustomJobTypeIntegration(unittest.TestCase):
    """
    Integration tests for custom job type support in generic_test_entrypoint.
    
    These tests verify that custom TestJob subclasses can be passed to the
    entry point and are properly used for test execution.
    
    Requirements: 14.1, 14.2, 14.3, 14.4
    """

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(name="automojo-testbase", logger_name="automojo-testbase", log_basename="automojo-testbase")

        self.tempdir = tempfile.TemporaryDirectory()
        self.testroot_dir = os.path.join(self.tempdir.name, "testroot")
        self.tests_dir = os.path.join(self.testroot_dir, "tests")
        
        # Create test directory structure
        os.makedirs(self.tests_dir)
        
        # Create __testroot__.py marker file
        testroot_marker = os.path.join(self.testroot_dir, "__testroot__.py")
        with open(testroot_marker, "w") as f:
            f.write('ROOT_TYPE = "testbase"\n')
        
        # Create __init__.py files
        with open(os.path.join(self.testroot_dir, "__init__.py"), "w") as f:
            f.write("")
        with open(os.path.join(self.tests_dir, "__init__.py"), "w") as f:
            f.write("")

        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)
        
        # Reset custom job tracking
        CustomTestJob.reset_tracking()

    def tearDown(self):
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()
        CustomTestJob.reset_tracking()

    @patch('sys.exit')
    @patch('automojo.testbase.entrypoints.import_by_name')
    @patch('automojo.testbase.entrypoints.find_testmodule_root')
    @patch('automojo.testbase.entrypoints.find_testmodule_fullname')
    @patch('automojo.testbase.entrypoints.getEnhancedLogger')
    @patch('automojo.testbase.entrypoints.get_path_for_testresults')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.testbase.initialize.initialize_testbase_runtime')
    def test_custom_job_type_is_instantiated(self, mock_init_runtime,
                                              mock_init_results, mock_get_path, mock_get_logger,
                                              mock_find_fullname, mock_find_root, mock_import_by_name, mock_exit):
        """
        Test that a custom TestJob subclass is instantiated when specified.
        
        Verifies that when a custom job_type is passed to generic_test_entrypoint,
        an instance of that custom type is created.
        
        Requirements: 14.1, 14.3
        """
        # Setup mocks
        mock_find_root.return_value = self.testroot_dir
        mock_find_fullname.return_value = "tests.test_module"
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a mock test module
        mock_module = MagicMock()
        mock_module.__name__ = "__main__"
        mock_module.__file__ = os.path.join(self.tests_dir, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": mock_module, "automojo.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from automojo.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=CustomTestJob)
        
        # Verify CustomTestJob was instantiated
        self.assertEqual(len(CustomTestJob.instances_created), 1,
                        "CustomTestJob should be instantiated exactly once")

    @patch('sys.exit')
    @patch('automojo.testbase.entrypoints.import_by_name')
    @patch('automojo.testbase.entrypoints.find_testmodule_root')
    @patch('automojo.testbase.entrypoints.find_testmodule_fullname')
    @patch('automojo.testbase.entrypoints.getEnhancedLogger')
    @patch('automojo.testbase.entrypoints.get_path_for_testresults')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.testbase.initialize.initialize_testbase_runtime')
    def test_custom_job_type_execute_is_called(self, mock_init_runtime,
                                                mock_init_results, mock_get_path, mock_get_logger,
                                                mock_find_fullname, mock_find_root, mock_import_by_name, mock_exit):
        """
        Test that the custom TestJob's execute method is called.
        
        Verifies that when a custom job_type is used, its execute() method
        is invoked during the entry point execution.
        
        Requirements: 14.3
        """
        # Setup mocks
        mock_find_root.return_value = self.testroot_dir
        mock_find_fullname.return_value = "tests.test_module"
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a mock test module
        mock_module = MagicMock()
        mock_module.__name__ = "__main__"
        mock_module.__file__ = os.path.join(self.tests_dir, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": mock_module, "automojo.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from automojo.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=CustomTestJob)
        
        # Verify execute was called
        self.assertEqual(len(CustomTestJob.execute_calls), 1,
                        "CustomTestJob.execute() should be called exactly once")

    @patch('sys.exit')
    @patch('automojo.testbase.entrypoints.import_by_name')
    @patch('automojo.testbase.entrypoints.find_testmodule_root')
    @patch('automojo.testbase.entrypoints.find_testmodule_fullname')
    @patch('automojo.testbase.entrypoints.getEnhancedLogger')
    @patch('automojo.testbase.entrypoints.get_path_for_testresults')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.testbase.initialize.initialize_testbase_runtime')
    def test_custom_job_receives_testroot_parameter(self, mock_init_runtime,
                                                     mock_init_results, mock_get_path, mock_get_logger,
                                                     mock_find_fullname, mock_find_root, mock_import_by_name, mock_exit):
        """
        Test that the custom TestJob receives the correct testroot parameter.
        
        Verifies that the testroot discovered by find_testmodule_root is
        passed to the custom job type constructor.
        
        Requirements: 14.3
        """
        # Setup mocks
        mock_find_root.return_value = self.testroot_dir
        mock_find_fullname.return_value = "tests.test_module"
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a mock test module
        mock_module = MagicMock()
        mock_module.__name__ = "__main__"
        mock_module.__file__ = os.path.join(self.tests_dir, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": mock_module, "automojo.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from automojo.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=CustomTestJob)
        
        # Verify testroot was passed correctly
        self.assertEqual(len(CustomTestJob.instances_created), 1)
        self.assertEqual(CustomTestJob.instances_created[0]['testroot'], self.testroot_dir,
                        "CustomTestJob should receive the correct testroot")

    @patch('sys.exit')
    @patch('automojo.testbase.entrypoints.import_by_name')
    @patch('automojo.testbase.entrypoints.find_testmodule_root')
    @patch('automojo.testbase.entrypoints.find_testmodule_fullname')
    @patch('automojo.testbase.entrypoints.getEnhancedLogger')
    @patch('automojo.testbase.entrypoints.get_path_for_testresults')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.testbase.initialize.initialize_testbase_runtime')
    def test_custom_job_receives_include_patterns(self, mock_init_runtime,
                                                   mock_init_results, mock_get_path, mock_get_logger,
                                                   mock_find_fullname, mock_find_root, mock_import_by_name, mock_exit):
        """
        Test that the custom TestJob receives include patterns from command line.
        
        Verifies that include patterns specified via -i/--include are passed
        to the custom job type.
        
        Requirements: 14.3
        """
        # Setup mocks
        mock_find_root.return_value = self.testroot_dir
        mock_find_fullname.return_value = "tests.test_module"
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a mock test module
        mock_module = MagicMock()
        mock_module.__name__ = "__main__"
        mock_module.__file__ = os.path.join(self.tests_dir, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": mock_module, "automojo.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py', '-i', 'test_specific_*']):
                from automojo.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=CustomTestJob)
        
        # Verify includes were passed correctly
        self.assertEqual(len(CustomTestJob.instances_created), 1)
        self.assertEqual(CustomTestJob.instances_created[0]['includes'], ['test_specific_*'],
                        "CustomTestJob should receive the include patterns")

    @patch('sys.exit')
    @patch('automojo.testbase.entrypoints.import_by_name')
    @patch('automojo.testbase.entrypoints.find_testmodule_root')
    @patch('automojo.testbase.entrypoints.find_testmodule_fullname')
    @patch('automojo.testbase.entrypoints.getEnhancedLogger')
    @patch('automojo.testbase.entrypoints.get_path_for_testresults')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.testbase.initialize.initialize_testbase_runtime')
    def test_custom_job_receives_exclude_patterns(self, mock_init_runtime,
                                                   mock_init_results, mock_get_path, mock_get_logger,
                                                   mock_find_fullname, mock_find_root, mock_import_by_name, mock_exit):
        """
        Test that the custom TestJob receives exclude patterns from command line.
        
        Verifies that exclude patterns specified via -x/--exclude are passed
        to the custom job type.
        
        Requirements: 14.3
        """
        # Setup mocks
        mock_find_root.return_value = self.testroot_dir
        mock_find_fullname.return_value = "tests.test_module"
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a mock test module
        mock_module = MagicMock()
        mock_module.__name__ = "__main__"
        mock_module.__file__ = os.path.join(self.tests_dir, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": mock_module, "automojo.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py', '-i', '*', '-x', 'test_slow_*']):
                from automojo.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=CustomTestJob)
        
        # Verify excludes were passed correctly
        self.assertEqual(len(CustomTestJob.instances_created), 1)
        self.assertEqual(CustomTestJob.instances_created[0]['excludes'], ['test_slow_*'],
                        "CustomTestJob should receive the exclude patterns")

    @patch('sys.exit')
    @patch('automojo.testbase.entrypoints.import_by_name')
    @patch('automojo.testbase.entrypoints.find_testmodule_root')
    @patch('automojo.testbase.entrypoints.find_testmodule_fullname')
    @patch('automojo.testbase.entrypoints.getEnhancedLogger')
    @patch('automojo.testbase.entrypoints.get_path_for_testresults')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.testbase.initialize.initialize_testbase_runtime')
    def test_custom_job_receives_test_module(self, mock_init_runtime,
                                              mock_init_results, mock_get_path, mock_get_logger,
                                              mock_find_fullname, mock_find_root, mock_import_by_name, mock_exit):
        """
        Test that the custom TestJob receives the test module reference.
        
        Verifies that the test module being executed is passed to the
        custom job type constructor.
        
        Requirements: 14.3
        """
        # Setup mocks
        mock_find_root.return_value = self.testroot_dir
        mock_find_fullname.return_value = "tests.test_module"
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a mock test module
        mock_module = MagicMock()
        mock_module.__name__ = "__main__"
        mock_module.__file__ = os.path.join(self.tests_dir, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": mock_module, "automojo.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from automojo.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=CustomTestJob)
        
        # Verify test_module was passed
        self.assertEqual(len(CustomTestJob.instances_created), 1)
        self.assertIsNotNone(CustomTestJob.instances_created[0]['test_module'],
                            "CustomTestJob should receive the test module")

    @patch('sys.exit')
    @patch('automojo.testbase.entrypoints.import_by_name')
    @patch('automojo.testbase.entrypoints.find_testmodule_root')
    @patch('automojo.testbase.entrypoints.find_testmodule_fullname')
    @patch('automojo.testbase.entrypoints.getEnhancedLogger')
    @patch('automojo.testbase.entrypoints.get_path_for_testresults')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.testbase.initialize.initialize_testbase_runtime')
    def test_custom_job_result_code_passed_to_exit(self, mock_init_runtime,
                                                    mock_init_results, mock_get_path, mock_get_logger,
                                                    mock_find_fullname, mock_find_root, mock_import_by_name, mock_exit):
        """
        Test that the custom TestJob's result code is passed to sys.exit.
        
        Verifies that the return value from the custom job's execute() method
        is used as the exit code.
        
        Requirements: 14.3
        """
        # Setup mocks
        mock_find_root.return_value = self.testroot_dir
        mock_find_fullname.return_value = "tests.test_module"
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a mock test module
        mock_module = MagicMock()
        mock_module.__name__ = "__main__"
        mock_module.__file__ = os.path.join(self.tests_dir, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": mock_module, "automojo.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from automojo.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=CustomTestJob)
        
        # Verify sys.exit was called with the result code from execute()
        mock_exit.assert_called_once_with(0)

    @patch('sys.exit')
    @patch('automojo.testbase.entrypoints.import_by_name')
    @patch('automojo.testbase.entrypoints.find_testmodule_root')
    @patch('automojo.testbase.entrypoints.find_testmodule_fullname')
    @patch('automojo.testbase.entrypoints.getEnhancedLogger')
    @patch('automojo.testbase.entrypoints.get_path_for_testresults')
    @patch('automojo.testbase.initialize.initialize_testbase_results')
    @patch('automojo.testbase.initialize.initialize_testbase_runtime')
    def test_failing_custom_job_result_code_propagated(self, mock_init_runtime,
                                                        mock_init_results, mock_get_path, mock_get_logger,
                                                        mock_find_fullname, mock_find_root, mock_import_by_name, mock_exit):
        """
        Test that a failing custom TestJob's result code is propagated.
        
        Verifies that when a custom job returns a non-zero exit code,
        that code is passed to sys.exit.
        
        Requirements: 14.3
        """
        # Setup mocks
        mock_find_root.return_value = self.testroot_dir
        mock_find_fullname.return_value = "tests.test_module"
        mock_get_path.return_value = self.tempdir.name
        mock_get_logger.return_value = DummyLogger()
        
        # Create a mock test module
        mock_module = MagicMock()
        mock_module.__name__ = "__main__"
        mock_module.__file__ = os.path.join(self.tests_dir, "test_module.py")
        
        with patch.dict(sys.modules, {"__main__": mock_module, "automojo.testbase": MagicMock()}):
            with patch('sys.argv', ['test_module.py']):
                from automojo.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=FailingCustomTestJob)
        
        # Verify sys.exit was called with non-zero code
        mock_exit.assert_called_once_with(1)


class TestCustomJobTypeIsSubclassOfTestJob(unittest.TestCase):
    """
    Tests verifying that custom job types must be subclasses of TestJob.
    
    Requirements: 14.4
    """

    def test_custom_test_job_is_subclass_of_testjob(self):
        """
        Test that CustomTestJob is a subclass of TestJob.
        
        Verifies that custom job types properly inherit from TestJob.
        
        Requirements: 14.4
        """
        self.assertTrue(issubclass(CustomTestJob, TestJob),
                       "CustomTestJob must be a subclass of TestJob")

    def test_failing_custom_test_job_is_subclass_of_testjob(self):
        """
        Test that FailingCustomTestJob is a subclass of TestJob.
        
        Verifies that custom job types properly inherit from TestJob.
        
        Requirements: 14.4
        """
        self.assertTrue(issubclass(FailingCustomTestJob, TestJob),
                       "FailingCustomTestJob must be a subclass of TestJob")

    def test_default_test_job_is_subclass_of_testjob(self):
        """
        Test that DefaultTestJob is a subclass of TestJob.
        
        Verifies that the default job type properly inherits from TestJob.
        
        Requirements: 14.2, 14.4
        """
        self.assertTrue(issubclass(DefaultTestJob, TestJob),
                       "DefaultTestJob must be a subclass of TestJob")


class TestDefaultJobTypeUsage(unittest.TestCase):
    """
    Tests verifying that DefaultTestJob is used when no job_type is specified.
    
    Requirements: 14.2
    """

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(name="automojo-testbase", logger_name="automojo-testbase", log_basename="automojo-testbase")

        self.tempdir = tempfile.TemporaryDirectory()
        self.testroot_dir = os.path.join(self.tempdir.name, "testroot")
        self.tests_dir = os.path.join(self.testroot_dir, "tests")
        
        # Create test directory structure
        os.makedirs(self.tests_dir)
        
        # Create __testroot__.py marker file
        testroot_marker = os.path.join(self.testroot_dir, "__testroot__.py")
        with open(testroot_marker, "w") as f:
            f.write('ROOT_TYPE = "testbase"\n')
        
        # Create __init__.py files
        with open(os.path.join(self.testroot_dir, "__init__.py"), "w") as f:
            f.write("")
        with open(os.path.join(self.tests_dir, "__init__.py"), "w") as f:
            f.write("")

        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

    def tearDown(self):
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    def test_generic_test_entrypoint_default_job_type_parameter(self):
        """
        Test that generic_test_entrypoint has DefaultTestJob as default job_type.
        
        Verifies that the function signature specifies DefaultTestJob as the
        default value for the job_type parameter.
        
        Requirements: 14.1, 14.2
        """
        import inspect
        from automojo.testbase.entrypoints import generic_test_entrypoint
        
        sig = inspect.signature(generic_test_entrypoint)
        job_type_param = sig.parameters.get('job_type')
        
        self.assertIsNotNone(job_type_param, 
                            "generic_test_entrypoint should have a job_type parameter")
        self.assertEqual(job_type_param.default, DefaultTestJob,
                        "job_type parameter should default to DefaultTestJob")


if __name__ == "__main__":
    unittest.main()
