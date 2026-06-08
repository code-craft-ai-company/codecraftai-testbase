"""
    Integration tests for end-to-end test execution.
    
    Tests verify:
    - Complete flow from TestJob creation to result recording (Requirements 1.4, 1.5)
    - Scope nesting and exception propagation (Requirements 11.3, 11.4)
    
    Requirements: 1.4, 1.5, 11.3, 11.4
"""

import os
import sys
import tempfile
import unittest
import subprocess

from ccai.thisapp.persona import APP_PERSONA_ESTABLISHED, establish_app_persona
from ccai.thisapp.wellknown import ThisApplicationSingleton
from ccai.runtime.enumerations import JobType
from ccai.runtime.runtimevariables import RuntimeVariablesDesc
import ccai.runtime.paths as runtime_paths


class TestExecutionEndToEndIntegration(unittest.TestCase):
    """
    Integration tests for end-to-end test execution flow.
    
    These tests verify the complete flow from TestJob creation through
    test execution to result recording.
    
    Requirements: 1.4, 1.5, 11.3, 11.4
    """

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="codecraftai-testbase",
                logger_name="codecraftai-testbase",
                log_basename="codecraftai-testbase"
            )

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

    def _run_testbase_cli(self, testroot: str, include_patterns: list = None) -> tuple:
        """
        Run tests using the testbase CLI command and return result code and output.
        
        Args:
            testroot: Path to the test root directory
            include_patterns: List of include patterns (optional)
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd = [
            sys.executable, "-m", "ccai.testbase.cli.testbase_command",
            "testing", "run",
            "--root", testroot
        ]
        
        if include_patterns:
            for pattern in include_patterns:
                cmd.extend(["-i", pattern])
        else:
            cmd.extend(["-i", "*"])
        
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "USER": os.environ.get("USER", ""),
            "LANG": os.environ.get("LANG", "en_US.UTF-8"),
            "TERM": os.environ.get("TERM", "xterm"),
        }
        
        pythonpath_parts = [p for p in sys.path if p and p != os.getcwd()]
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=120
        )
        
        return result.returncode, result.stdout, result.stderr

    def test_complete_flow_testjob_to_result_recording(self):
        """
        Test complete flow from TestJob creation to result recording.
        
        Verifies:
        - TestJob is created and initialized (Requirement 1.4)
        - Test execution completes successfully (Requirement 1.5)
        - Results are recorded properly (Requirement 11.3)
        
        Requirements: 1.4, 1.5, 11.3
        """
        test_file = os.path.join(self.tests_dir, "test_flow.py")
        test_content = '''"""
    Test module for complete flow verification.
"""

import ccai.testbase as testbase

def test_complete_flow():
    """A test that verifies the complete execution flow."""
    testbase.logger.info("test_complete_flow: executing")
    assert True
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        # Verify execution completed successfully
        self.assertEqual(return_code, 0,
            f"Complete flow should succeed.\nStdout: {stdout}\nStderr: {stderr}")

    def test_result_code_reflects_test_pass(self):
        """
        Test that result code reflects passing test outcomes.
        
        Verifies:
        - Passing tests result in exit code 0 (Requirement 1.5)
        - Result recording captures pass status (Requirement 11.4)
        
        Requirements: 1.5, 11.4
        """
        test_file = os.path.join(self.tests_dir, "test_pass.py")
        test_content = '''"""
    Test module with passing test.
"""

import ccai.testbase as testbase

def test_should_pass():
    """A test that should pass."""
    testbase.logger.info("test_should_pass: executing")
    assert True
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        self.assertEqual(return_code, 0,
            f"Passing test should return exit code 0.\nStdout: {stdout}\nStderr: {stderr}")

    def test_result_code_reflects_test_failure(self):
        """
        Test that result code reflects failing test outcomes.
        
        Verifies:
        - Failing tests result in non-zero exit code (Requirement 1.5)
        - Result recording captures failure status (Requirement 11.4)
        
        Requirements: 1.5, 11.4
        """
        test_file = os.path.join(self.tests_dir, "test_fail.py")
        test_content = '''"""
    Test module with failing test.
"""

import ccai.testbase as testbase

def test_should_fail():
    """A test that should fail."""
    testbase.logger.info("test_should_fail: executing")
    assert False, "Intentional failure"
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        self.assertNotEqual(return_code, 0,
            f"Failing test should return non-zero exit code.\nStdout: {stdout}\nStderr: {stderr}")


class TestScopeNestingIntegration(unittest.TestCase):
    """
    Integration tests for scope nesting and exception propagation.
    
    These tests verify that scope contexts are properly nested and
    exceptions are correctly propagated through the scope hierarchy.
    
    Requirements: 11.3, 11.4
    """

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="codecraftai-testbase",
                logger_name="codecraftai-testbase",
                log_basename="codecraftai-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()
        self.testroot_dir = os.path.join(self.tempdir.name, "testroot")
        self.tests_dir = os.path.join(self.testroot_dir, "tests")
        self.subpackage_dir = os.path.join(self.tests_dir, "subpackage")
        
        # Create test directory structure with subpackage
        os.makedirs(self.subpackage_dir)
        
        # Create __testroot__.py marker file
        testroot_marker = os.path.join(self.testroot_dir, "__testroot__.py")
        with open(testroot_marker, "w") as f:
            f.write('ROOT_TYPE = "testbase"\n')
        
        # Create __init__.py files
        for dir_path in [self.testroot_dir, self.tests_dir, self.subpackage_dir]:
            with open(os.path.join(dir_path, "__init__.py"), "w") as f:
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

    def _run_testbase_cli(self, testroot: str, include_patterns: list = None) -> tuple:
        """Run tests using the testbase CLI command."""
        cmd = [
            sys.executable, "-m", "ccai.testbase.cli.testbase_command",
            "testing", "run",
            "--root", testroot
        ]
        
        if include_patterns:
            for pattern in include_patterns:
                cmd.extend(["-i", pattern])
        else:
            cmd.extend(["-i", "*"])
        
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "USER": os.environ.get("USER", ""),
            "LANG": os.environ.get("LANG", "en_US.UTF-8"),
            "TERM": os.environ.get("TERM", "xterm"),
        }
        
        pythonpath_parts = [p for p in sys.path if p and p != os.getcwd()]
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=120
        )
        
        return result.returncode, result.stdout, result.stderr

    def test_nested_module_scope_execution(self):
        """
        Test that nested module scopes execute correctly.
        
        Verifies:
        - Tests in nested packages are discovered (Requirement 11.3)
        - Module scope contexts are properly nested (Requirement 11.3)
        - Results are recorded for nested tests (Requirement 11.4)
        
        Requirements: 11.3, 11.4
        """
        # Create test in root tests directory
        root_test = os.path.join(self.tests_dir, "test_root.py")
        root_content = '''"""
    Test module at root level.
"""

import ccai.testbase as testbase

def test_root_level():
    """A test at the root level."""
    testbase.logger.info("test_root_level: executing")
    assert True
    return
'''
        with open(root_test, "w") as f:
            f.write(root_content)
        
        # Create test in nested subpackage
        nested_test = os.path.join(self.subpackage_dir, "test_nested.py")
        nested_content = '''"""
    Test module in nested subpackage.
"""

import ccai.testbase as testbase

def test_nested_level():
    """A test in a nested package."""
    testbase.logger.info("test_nested_level: executing")
    assert True
    return
'''
        with open(nested_test, "w") as f:
            f.write(nested_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        self.assertEqual(return_code, 0,
            f"Nested scope execution should succeed.\nStdout: {stdout}\nStderr: {stderr}")

    def test_exception_propagation_assertion_error(self):
        """
        Test that AssertionError is properly propagated and recorded as failure.
        
        Verifies:
        - AssertionError in test scope is caught (Requirement 11.3)
        - Test is marked as failed (Requirement 11.4)
        - Result code reflects failure (Requirement 11.4)
        
        Requirements: 11.3, 11.4
        """
        test_file = os.path.join(self.tests_dir, "test_assertion.py")
        test_content = '''"""
    Test module with assertion failure.
"""

import ccai.testbase as testbase

def test_assertion_failure():
    """A test that raises AssertionError."""
    testbase.logger.info("test_assertion_failure: executing")
    assert False, "Expected assertion failure"
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        # AssertionError should result in test failure (non-zero exit)
        self.assertNotEqual(return_code, 0,
            f"AssertionError should result in failure.\nStdout: {stdout}\nStderr: {stderr}")

    def test_exception_propagation_runtime_error(self):
        """
        Test that RuntimeError is properly propagated and recorded as error.
        
        Verifies:
        - RuntimeError in test scope is caught (Requirement 11.3)
        - Test is marked as errored (Requirement 11.4)
        - Result code reflects error (Requirement 11.4)
        
        Requirements: 11.3, 11.4
        """
        test_file = os.path.join(self.tests_dir, "test_runtime.py")
        test_content = '''"""
    Test module with runtime error.
"""

import ccai.testbase as testbase

def test_runtime_error():
    """A test that raises RuntimeError."""
    testbase.logger.info("test_runtime_error: executing")
    raise RuntimeError("Expected runtime error")
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        # RuntimeError should result in test error (non-zero exit)
        self.assertNotEqual(return_code, 0,
            f"RuntimeError should result in error.\nStdout: {stdout}\nStderr: {stderr}")

    def test_mixed_results_across_scopes(self):
        """
        Test that mixed results across different scopes are properly recorded.
        
        Verifies:
        - Multiple tests in different modules execute (Requirement 11.3)
        - Pass/fail results are correctly recorded (Requirement 11.4)
        - Overall result reflects any failure (Requirement 11.4)
        
        Requirements: 11.3, 11.4
        """
        # Create passing test module
        pass_test = os.path.join(self.tests_dir, "test_passing.py")
        pass_content = '''"""
    Test module with passing tests.
"""

import ccai.testbase as testbase

def test_pass_one():
    """A passing test."""
    testbase.logger.info("test_pass_one: executing")
    assert True
    return

def test_pass_two():
    """Another passing test."""
    testbase.logger.info("test_pass_two: executing")
    assert True
    return
'''
        with open(pass_test, "w") as f:
            f.write(pass_content)
        
        # Create failing test module
        fail_test = os.path.join(self.tests_dir, "test_failing.py")
        fail_content = '''"""
    Test module with failing test.
"""

import ccai.testbase as testbase

def test_fail_one():
    """A failing test."""
    testbase.logger.info("test_fail_one: executing")
    assert False, "Intentional failure"
    return
'''
        with open(fail_test, "w") as f:
            f.write(fail_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        # Mixed results with any failure should result in non-zero exit
        self.assertNotEqual(return_code, 0,
            f"Mixed results with failure should return non-zero.\nStdout: {stdout}\nStderr: {stderr}")

    def test_multiple_tests_in_single_module(self):
        """
        Test that multiple tests in a single module execute in proper scope.
        
        Verifies:
        - All tests in module are discovered (Requirement 11.3)
        - Each test executes in its own test scope (Requirement 11.3)
        - Results are recorded for each test (Requirement 11.4)
        
        Requirements: 11.3, 11.4
        """
        test_file = os.path.join(self.tests_dir, "test_multiple.py")
        test_content = '''"""
    Test module with multiple tests.
"""

import ccai.testbase as testbase

def test_first():
    """First test in module."""
    testbase.logger.info("test_first: executing")
    assert True
    return

def test_second():
    """Second test in module."""
    testbase.logger.info("test_second: executing")
    assert True
    return

def test_third():
    """Third test in module."""
    testbase.logger.info("test_third: executing")
    assert True
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        self.assertEqual(return_code, 0,
            f"Multiple tests in module should all pass.\nStdout: {stdout}\nStderr: {stderr}")


class TestScopeExceptionHandling(unittest.TestCase):
    """
    Integration tests for scope-level exception handling.
    
    These tests verify that exceptions at different scope levels
    are properly handled and propagated.
    
    Requirements: 11.3, 11.4
    """

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="codecraftai-testbase",
                logger_name="codecraftai-testbase",
                log_basename="codecraftai-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()
        self.testroot_dir = os.path.join(self.tempdir.name, "testroot")
        self.tests_dir = os.path.join(self.testroot_dir, "tests")
        
        os.makedirs(self.tests_dir)
        
        testroot_marker = os.path.join(self.testroot_dir, "__testroot__.py")
        with open(testroot_marker, "w") as f:
            f.write('ROOT_TYPE = "testbase"\n')
        
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

    def _run_testbase_cli(self, testroot: str, include_patterns: list = None) -> tuple:
        """Run tests using the testbase CLI command."""
        cmd = [
            sys.executable, "-m", "ccai.testbase.cli.testbase_command",
            "testing", "run",
            "--root", testroot
        ]
        
        if include_patterns:
            for pattern in include_patterns:
                cmd.extend(["-i", pattern])
        else:
            cmd.extend(["-i", "*"])
        
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "USER": os.environ.get("USER", ""),
            "LANG": os.environ.get("LANG", "en_US.UTF-8"),
            "TERM": os.environ.get("TERM", "xterm"),
        }
        
        pythonpath_parts = [p for p in sys.path if p and p != os.getcwd()]
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=120
        )
        
        return result.returncode, result.stdout, result.stderr

    def test_exception_does_not_crash_execution(self):
        """
        Test that exceptions in one test do not crash the entire execution.
        
        Verifies:
        - Exception in one test is contained (Requirement 11.3)
        - Other tests continue to execute (Requirement 11.4)
        - Results are recorded for all tests (Requirement 11.4)
        
        Requirements: 11.3, 11.4
        """
        test_file = os.path.join(self.tests_dir, "test_exception.py")
        test_content = '''"""
    Test module with exception and passing test.
"""

import ccai.testbase as testbase

def test_raises_exception():
    """A test that raises an exception."""
    testbase.logger.info("test_raises_exception: executing")
    raise RuntimeError("Test exception")
    return

def test_should_pass():
    """A test that should pass."""
    testbase.logger.info("test_should_pass: executing")
    assert True
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        # Execution should complete (non-zero due to error) but not crash
        self.assertNotEqual(return_code, 0,
            f"Exception should result in non-zero exit.\nStdout: {stdout}\nStderr: {stderr}")

    def test_value_error_handling(self):
        """
        Test that ValueError is properly handled and recorded as error.
        
        Verifies:
        - ValueError in test scope is caught (Requirement 11.3)
        - Test is marked as errored (Requirement 11.4)
        
        Requirements: 11.3, 11.4
        """
        test_file = os.path.join(self.tests_dir, "test_value.py")
        test_content = '''"""
    Test module with ValueError.
"""

import ccai.testbase as testbase

def test_value_error():
    """A test that raises ValueError."""
    testbase.logger.info("test_value_error: executing")
    raise ValueError("Invalid value")
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        self.assertNotEqual(return_code, 0,
            f"ValueError should result in error.\nStdout: {stdout}\nStderr: {stderr}")

    def test_type_error_handling(self):
        """
        Test that TypeError is properly handled and recorded as error.
        
        Verifies:
        - TypeError in test scope is caught (Requirement 11.3)
        - Test is marked as errored (Requirement 11.4)
        
        Requirements: 11.3, 11.4
        """
        test_file = os.path.join(self.tests_dir, "test_type.py")
        test_content = '''"""
    Test module with TypeError.
"""

import ccai.testbase as testbase

def test_type_error():
    """A test that raises TypeError."""
    testbase.logger.info("test_type_error: executing")
    raise TypeError("Type mismatch")
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        self.assertNotEqual(return_code, 0,
            f"TypeError should result in error.\nStdout: {stdout}\nStderr: {stderr}")


if __name__ == "__main__":
    unittest.main()
