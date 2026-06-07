"""
    Integration tests for mocking framework with TestBase execution.
    
    These tests verify:
    - Mocks used in test fixtures (resource factories)
    - Patches applied during test setup
    - Mock assertions in test verification
    
    Requirements: Integration with Test Execution Engine
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


class TestMockingInTestFixtures(unittest.TestCase):
    """
    Integration tests for mocks used in test fixtures (resource factories).
    
    These tests verify that mocks can be created and used within resource
    factories and properly injected into tests.
    
    Requirements: Integration with Test Execution Engine
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

    def test_mock_in_resource_factory_basic(self):
        """
        Test that a mock created in a resource factory can be used in tests.
        
        Verifies:
        - Mock can be created in resource factory
        - Mock is properly yielded to test
        - Test can use mock and verify behavior
        
        Requirements: Integration with Test Execution Engine
        """
        test_file = os.path.join(self.tests_dir, "test_mock_fixture.py")
        test_content = '''"""
    Test module for mock in resource factory.
"""

from typing import Generator
import ccai.testbase as testbase
from ccai.testbase.mocking import Mock


@testbase.register.resource_factory()
def create_mock_service() -> Generator[Mock, None, None]:
    """Factory that creates a mock service."""
    mock_service = Mock()
    mock_service.configure(recursive=True)
    mock_service.mock_context().mock_method("get_data", return_value={"key": "value"})
    yield mock_service


testbase.originate.parameter(create_mock_service, identifier="mock_service")


def test_mock_service_returns_configured_value(mock_service: Mock):
    """Test that mock service returns configured value."""
    testbase.logger.info("test_mock_service_returns_configured_value: executing")
    
    result = mock_service.get_data()
    
    testbase.assert_equal(result, {"key": "value"})
    return


def test_mock_service_tracks_calls(mock_service: Mock):
    """Test that mock service tracks method calls."""
    testbase.logger.info("test_mock_service_tracks_calls: executing")
    
    # Get the mock method and record initial call count
    get_data_mock = mock_service.mock_context().get_attribute("get_data")
    initial_count = get_data_mock.call_count
    
    mock_service.get_data()
    mock_service.get_data()
    
    # Verify call count increased by 2
    testbase.assert_equal(get_data_mock.call_count, initial_count + 2)
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        self.assertEqual(return_code, 0,
            f"Mock in resource factory should work.\nStdout: {stdout}\nStderr: {stderr}")

    def test_mock_with_side_effect_in_fixture(self):
        """
        Test that a mock with side effect works in resource factory.
        
        Verifies:
        - Mock with side_effect can be created in factory
        - Side effect executes when mock is called
        - Test can verify side effect behavior
        
        Requirements: Integration with Test Execution Engine
        """
        test_file = os.path.join(self.tests_dir, "test_mock_side_effect.py")
        test_content = '''"""
    Test module for mock with side effect in fixture.
"""

from typing import Generator
import ccai.testbase as testbase
from ccai.testbase.mocking import Mock, SideEffect


@testbase.register.resource_factory()
def create_mock_calculator() -> Generator[Mock, None, None]:
    """Factory that creates a mock calculator with side effect."""
    mock_calc = Mock()
    mock_calc.configure(recursive=True)
    
    def add_numbers(a, b):
        return a + b
    
    mock_calc.mock_context().mock_method("add", side_effect=add_numbers)
    yield mock_calc


testbase.originate.parameter(create_mock_calculator, identifier="mock_calc")


def test_mock_side_effect_executes(mock_calc: Mock):
    """Test that mock side effect executes correctly."""
    testbase.logger.info("test_mock_side_effect_executes: executing")
    
    result = mock_calc.add(3, 5)
    
    testbase.assert_equal(result, 8)
    return


def test_mock_side_effect_with_different_args(mock_calc: Mock):
    """Test that mock side effect works with different arguments."""
    testbase.logger.info("test_mock_side_effect_with_different_args: executing")
    
    result1 = mock_calc.add(10, 20)
    result2 = mock_calc.add(100, 200)
    
    testbase.assert_equal(result1, 30)
    testbase.assert_equal(result2, 300)
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        self.assertEqual(return_code, 0,
            f"Mock with side effect in fixture should work.\nStdout: {stdout}\nStderr: {stderr}")


class TestPatchingDuringTestSetup(unittest.TestCase):
    """
    Integration tests for patches applied during test setup.
    
    These tests verify that patches can be activated during test setup
    and properly deactivated after test completion.
    
    Requirements: Integration with Test Execution Engine
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

    def test_patch_in_resource_factory_with_cleanup(self):
        """
        Test that patches applied in resource factory are cleaned up properly.
        
        Verifies:
        - Patch can be activated in resource factory
        - Patch is active during test execution
        - Patch is deactivated after test completes
        
        Requirements: Integration with Test Execution Engine
        """
        test_file = os.path.join(self.tests_dir, "test_patch_cleanup.py")
        test_content = '''"""
    Test module for patch cleanup in resource factory.
"""

from typing import Generator
import os
import ccai.testbase as testbase
from ccai.testbase.mocking import create_module_patch, Mock


@testbase.register.resource_factory()
def create_patched_os_path() -> Generator[Mock, None, None]:
    """Factory that patches os.path.exists."""
    patch = create_module_patch(os.path, "exists")
    mock_exists = patch.activate()
    mock_exists.configure(return_value=True)
    
    yield mock_exists
    
    # Cleanup: deactivate patch
    patch.deactivate()


testbase.originate.parameter(create_patched_os_path, identifier="mock_exists")


def test_patched_function_returns_mock_value(mock_exists: Mock):
    """Test that patched function returns mock value."""
    testbase.logger.info("test_patched_function_returns_mock_value: executing")
    
    # os.path.exists should now return True for any path
    result = os.path.exists("/nonexistent/path/that/does/not/exist")
    
    testbase.assert_true(result)
    return


def test_patched_function_tracks_calls(mock_exists: Mock):
    """Test that patched function tracks calls."""
    testbase.logger.info("test_patched_function_tracks_calls: executing")
    
    # Record initial call count (may have been called by previous test)
    initial_count = mock_exists.call_count
    
    os.path.exists("/some/path")
    os.path.exists("/another/path")
    
    # Verify call count increased by 2
    testbase.assert_equal(mock_exists.call_count, initial_count + 2)
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        self.assertEqual(return_code, 0,
            f"Patch in resource factory should work.\nStdout: {stdout}\nStderr: {stderr}")

    def test_patch_context_manager_in_test(self):
        """
        Test that patch context manager works within test functions.
        
        Verifies:
        - Patch context manager can be used in test
        - Original is restored after context exit
        
        Requirements: Integration with Test Execution Engine
        """
        test_file = os.path.join(self.tests_dir, "test_patch_context.py")
        test_content = '''"""
    Test module for patch context manager in test.
"""

import os
import ccai.testbase as testbase
from ccai.testbase.mocking import create_module_patch


def test_patch_context_manager_basic():
    """Test that patch context manager works in test."""
    testbase.logger.info("test_patch_context_manager_basic: executing")
    
    original_exists = os.path.exists
    
    with create_module_patch(os.path, "exists") as mock_exists:
        mock_exists.configure(return_value=False)
        
        # Inside context, should return mocked value
        result = os.path.exists("/any/path")
        testbase.assert_false(result)
    
    # Outside context, original should be restored
    testbase.assert_true(os.path.exists is original_exists)
    return


def test_patch_context_manager_with_assertions():
    """Test that patch context manager allows assertions."""
    testbase.logger.info("test_patch_context_manager_with_assertions: executing")
    
    with create_module_patch(os.path, "isdir") as mock_isdir:
        mock_isdir.configure(return_value=True)
        
        os.path.isdir("/test/dir")
        
        mock_isdir.assert_called_once()
        mock_isdir.assert_called_with("/test/dir")
    
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        self.assertEqual(return_code, 0,
            f"Patch context manager in test should work.\nStdout: {stdout}\nStderr: {stderr}")


class TestMockAssertionsInVerification(unittest.TestCase):
    """
    Integration tests for mock assertions in test verification.
    
    These tests verify that mock assertion methods work correctly
    during test verification phase.
    
    Requirements: Integration with Test Execution Engine
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

    def test_mock_assert_called_passes(self):
        """
        Test that mock assert_called passes when mock was called.
        
        Verifies:
        - assert_called passes when mock is called
        - Test completes successfully
        
        Requirements: Integration with Test Execution Engine
        """
        test_file = os.path.join(self.tests_dir, "test_assert_called.py")
        test_content = '''"""
    Test module for mock assert_called.
"""

import ccai.testbase as testbase
from ccai.testbase.mocking import Mock


def test_assert_called_passes():
    """Test that assert_called passes when mock was called."""
    testbase.logger.info("test_assert_called_passes: executing")
    
    mock = Mock(return_value="result")
    mock()
    
    mock.assert_called()
    return


def test_assert_called_once_passes():
    """Test that assert_called_once passes when mock was called once."""
    testbase.logger.info("test_assert_called_once_passes: executing")
    
    mock = Mock(return_value="result")
    mock()
    
    mock.assert_called_once()
    return


def test_assert_called_with_passes():
    """Test that assert_called_with passes with correct arguments."""
    testbase.logger.info("test_assert_called_with_passes: executing")
    
    mock = Mock(return_value="result")
    mock("arg1", key="value")
    
    mock.assert_called_with("arg1", key="value")
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        self.assertEqual(return_code, 0,
            f"Mock assertions should pass.\nStdout: {stdout}\nStderr: {stderr}")

    def test_mock_assert_called_fails(self):
        """
        Test that mock assert_called fails when mock was not called.
        
        Verifies:
        - assert_called raises AssertionError when mock not called
        - Test fails with appropriate error
        
        Requirements: Integration with Test Execution Engine
        """
        test_file = os.path.join(self.tests_dir, "test_assert_called_fail.py")
        test_content = '''"""
    Test module for mock assert_called failure.
"""

import ccai.testbase as testbase
from ccai.testbase.mocking import Mock


def test_assert_called_fails_when_not_called():
    """Test that assert_called fails when mock was not called."""
    testbase.logger.info("test_assert_called_fails_when_not_called: executing")
    
    mock = Mock(return_value="result")
    # Not calling the mock
    
    mock.assert_called()  # This should raise AssertionError
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        # Test should fail because assert_called raises AssertionError
        self.assertNotEqual(return_code, 0,
            f"Mock assertion should fail.\nStdout: {stdout}\nStderr: {stderr}")

    def test_mock_assert_any_call_passes(self):
        """
        Test that mock assert_any_call passes when call is in history.
        
        Verifies:
        - assert_any_call passes when specified call exists
        - Test completes successfully
        
        Requirements: Integration with Test Execution Engine
        """
        test_file = os.path.join(self.tests_dir, "test_assert_any_call.py")
        test_content = '''"""
    Test module for mock assert_any_call.
"""

import ccai.testbase as testbase
from ccai.testbase.mocking import Mock


def test_assert_any_call_passes():
    """Test that assert_any_call passes when call is in history."""
    testbase.logger.info("test_assert_any_call_passes: executing")
    
    mock = Mock(return_value="result")
    mock("first")
    mock("second")
    mock("third")
    
    # Should pass because "second" was called
    mock.assert_any_call("second")
    return


def test_assert_has_calls_passes():
    """Test that assert_has_calls passes with correct sequence."""
    testbase.logger.info("test_assert_has_calls_passes: executing")
    
    mock = Mock(return_value="result")
    mock(1)
    mock(2)
    mock(3)
    
    # Should pass because sequence (1), (2) exists
    mock.assert_has_calls([((1,), {}), ((2,), {})])
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        self.assertEqual(return_code, 0,
            f"Mock assertions should pass.\nStdout: {stdout}\nStderr: {stderr}")

    def test_mock_assertions_with_recursive_mock(self):
        """
        Test that mock assertions work with recursive mocks.
        
        Verifies:
        - Recursive mock child methods can be asserted
        - Test completes successfully
        
        Requirements: Integration with Test Execution Engine
        """
        test_file = os.path.join(self.tests_dir, "test_recursive_assertions.py")
        test_content = '''"""
    Test module for mock assertions with recursive mocks.
"""

import ccai.testbase as testbase
from ccai.testbase.mocking import Mock


def test_recursive_mock_child_assertions():
    """Test that recursive mock child methods can be asserted."""
    testbase.logger.info("test_recursive_mock_child_assertions: executing")
    
    mock = Mock(recursive=True)
    mock.child.method.configure(return_value="child_result")
    
    result = mock.child.method()
    
    testbase.assert_equal(result, "child_result")
    mock.child.method.assert_called_once()
    return


def test_recursive_mock_deep_chain():
    """Test that deep recursive mock chains work."""
    testbase.logger.info("test_recursive_mock_deep_chain: executing")
    
    mock = Mock(recursive=True)
    mock.level1.level2.level3.configure(return_value="deep_result")
    
    result = mock.level1.level2.level3()
    
    testbase.assert_equal(result, "deep_result")
    mock.level1.level2.level3.assert_called()
    return
'''
        with open(test_file, "w") as f:
            f.write(test_content)
        
        return_code, stdout, stderr = self._run_testbase_cli(self.testroot_dir)
        
        self.assertEqual(return_code, 0,
            f"Recursive mock assertions should pass.\nStdout: {stdout}\nStderr: {stderr}")


if __name__ == "__main__":
    unittest.main()
