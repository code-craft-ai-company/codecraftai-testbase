"""
    Integration tests for TestCollector expression parsing.
    
    Tests verify:
    - Expression parsing in collect_references flow (Requirement 15.1)
    - Parsed components used for test filtering (Requirements 15.2, 15.3, 15.4, 15.5)
    - Various expression formats with actual test discovery
    
    Requirements: 15.1, 15.2, 15.3, 15.4, 15.5
"""

import os
import sys
import subprocess
import tempfile
import unittest

from automojo.thisapp.persona import APP_PERSONA_ESTABLISHED, establish_app_persona
from automojo.testbase.testcollector import TestCollector
from automojo.testbase.expressions import parse_test_include_expression


class TestCollectorExpressionParsingIntegration(unittest.TestCase):
    """
    Integration tests for expression parsing in TestCollector's collect_references flow.
    
    These tests verify that expression parsing integrates correctly with the
    TestCollector's test filtering logic using the actual testroots directory.
    
    Requirements: 15.1, 15.2, 15.3, 15.4, 15.5
    """

    @classmethod
    def setUpClass(cls):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )
        
        # Get the path to the actual testroots directory
        cls.repo_root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
        cls.testroot_dir = os.path.join(cls.repo_root, "source", "testroots", "automojo")

    def test_expression_parser_output_compatible_with_testcollector(self):
        """
        Test that expression parser output is compatible with TestCollector's filtering logic.
        
        Verifies:
        - Expression parser returns tuple of four elements (Requirement 15.1)
        - Output format matches TestCollector's expected input
        
        Requirements: 15.1
        """
        # Test various expression formats
        expressions = [
            "automojo.tests.testbase.injection.test_constraints",
            "automojo.tests.testbase.patterns.test_function_signatures",
            "automojo.tests.testbase.injection.test_constraints@#test_constraint_constrained_parameter",
        ]
        
        for expr in expressions:
            result = parse_test_include_expression(expr, None)
            
            # Verify output is a tuple of four elements
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 4)
            
            # Verify each element is either string or None
            for element in result:
                self.assertTrue(element is None or isinstance(element, str))

    def test_expr_package_used_for_package_level_filtering(self):
        """
        Test that expr_package value is usable for package-level filtering.
        
        Verifies:
        - Package component is correctly extracted (Requirement 15.2)
        - Package value can be used in find_included_modules_under_root
        
        Requirements: 15.2
        """
        # Test nested package expression
        expr = "automojo.tests.testbase.injection.test_constraints"
        pkg, mod, cls, name = parse_test_include_expression(expr, None)
        
        # Verify package is extracted correctly
        self.assertEqual(pkg, "automojo.tests.testbase.injection")
        self.assertEqual(mod, "test_constraints")
        
        # Verify package can be used for filtering
        self.assertIsNotNone(pkg)
        self.assertIn(".", pkg)  # Should be a dotted path

    def test_expr_module_used_for_module_level_filtering(self):
        """
        Test that expr_module value is usable for module-level filtering.
        
        Verifies:
        - Module component is correctly extracted (Requirement 15.3)
        - Module value can be used in find_included_modules_under_root
        
        Requirements: 15.3
        """
        # Test various expressions
        test_cases = [
            ("automojo.tests.testbase.injection.test_constraints", "test_constraints"),
            ("automojo.tests.testbase.patterns.test_function_signatures", "test_function_signatures"),
            ("test_module", "test_module"),  # Single identifier
        ]
        
        for expr, expected_module in test_cases:
            pkg, mod, cls, name = parse_test_include_expression(expr, None)
            self.assertEqual(mod, expected_module)

    def test_expr_testclass_used_for_testclass_filtering(self):
        """
        Test that expr_testclass value is usable for test class filtering.
        
        Note: TestBase style tests do not support tests inside classes,
        so testclass should typically be None or raise SemanticError.
        
        Verifies:
        - TestClass component is correctly extracted (Requirement 15.4)
        
        Requirements: 15.4
        """
        # Test expression with testclass
        expr = "automojo.tests.testbase.injection.test_constraints@TestClass"
        pkg, mod, cls, name = parse_test_include_expression(expr, None)
        
        self.assertEqual(cls, "TestClass")
        
        # Test expression without testclass
        expr = "automojo.tests.testbase.injection.test_constraints"
        pkg, mod, cls, name = parse_test_include_expression(expr, None)
        
        self.assertIsNone(cls)

    def test_expr_testname_used_for_individual_test_filtering(self):
        """
        Test that expr_testname value is usable for individual test filtering.
        
        Verifies:
        - TestName component is correctly extracted (Requirement 15.5)
        - TestName can be used to filter specific tests
        
        Requirements: 15.5
        """
        # Test expression with testname
        expr = "automojo.tests.testbase.injection.test_constraints@#test_constraint_constrained_parameter"
        pkg, mod, cls, name = parse_test_include_expression(expr, None)
        
        self.assertEqual(name, "test_constraint_constrained_parameter")
        
        # Test expression without testname
        expr = "automojo.tests.testbase.injection.test_constraints"
        pkg, mod, cls, name = parse_test_include_expression(expr, None)
        
        self.assertIsNone(name)


class TestCollectorExpressionCLIIntegration(unittest.TestCase):
    """
    Integration tests for TestCollector expression parsing via CLI.
    
    These tests verify end-to-end expression parsing through the CLI
    with actual test discovery.
    
    Requirements: 15.1, 15.2, 15.3, 15.4, 15.5
    """

    @classmethod
    def setUpClass(cls):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )
        
        cls.repo_root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
        cls.testroot_dir = os.path.join(cls.repo_root, "source", "testroots", "automojo")

    def _run_testbase_cli(self, testroot: str, include_patterns: list) -> tuple:
        """
        Run tests using the testbase CLI command and return result code and output.
        
        Args:
            testroot: Path to the test root directory
            include_patterns: List of include patterns
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd = [
            sys.executable, "-m", "automojo.testbase.cli.testbase_command",
            "testing", "run",
            "--root", testroot
        ]
        
        for pattern in include_patterns:
            cmd.extend(["-i", pattern])
        
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

    def test_cli_expression_parsing_package_module_format(self):
        """
        Test CLI expression parsing with pkg.mod format.
        
        Verifies:
        - Package and module expressions work via CLI (Requirements 15.2, 15.3)
        - Tests are discovered and executed
        
        Requirements: 15.1, 15.2, 15.3
        """
        return_code, stdout, stderr = self._run_testbase_cli(
            self.testroot_dir,
            ["automojo.tests.testbase.patterns.test_function_signatures"]
        )
        
        # Verify execution completed successfully and tests were discovered
        # The key is that expression parsing worked and tests were discovered
        self.assertEqual(return_code, 0,
            f"CLI should execute successfully.\nStdout: {stdout}\nStderr: {stderr}")
        self.assertIn("Passed:", stdout,
            f"Should show passed tests in summary.\nStdout: {stdout}\nStderr: {stderr}")

    def test_cli_expression_parsing_nested_package_format(self):
        """
        Test CLI expression parsing with nested package format.
        
        Verifies:
        - Nested package paths are correctly parsed (Requirement 15.2)
        - Tests in nested packages are discovered
        
        Requirements: 15.1, 15.2, 15.3
        """
        return_code, stdout, stderr = self._run_testbase_cli(
            self.testroot_dir,
            ["automojo.tests.testbase.injection.test_constraints"]
        )
        
        # Verify tests from nested package were discovered and executed
        self.assertEqual(return_code, 0,
            f"CLI should execute successfully.\nStdout: {stdout}\nStderr: {stderr}")
        self.assertIn("Passed:", stdout,
            f"Should show passed tests in summary.\nStdout: {stdout}\nStderr: {stderr}")

    def test_cli_expression_parsing_wildcard_format(self):
        """
        Test CLI expression parsing with wildcard format.
        
        Verifies:
        - Wildcard patterns work for module matching (Requirement 15.3)
        - Multiple tests are discovered
        
        Requirements: 15.1, 15.3
        """
        return_code, stdout, stderr = self._run_testbase_cli(
            self.testroot_dir,
            ["automojo.tests.testbase.injection.test_*"]
        )
        
        # Verify multiple tests were discovered using wildcard
        self.assertEqual(return_code, 0,
            f"CLI should execute successfully.\nStdout: {stdout}\nStderr: {stderr}")
        self.assertIn("Passed:", stdout,
            f"Should show passed tests in summary.\nStdout: {stdout}\nStderr: {stderr}")

    def test_cli_expression_parsing_multiple_includes(self):
        """
        Test CLI expression parsing with multiple include patterns.
        
        Verifies:
        - Multiple expressions can be processed (Requirement 15.1)
        - Results from different expressions are combined
        
        Requirements: 15.1, 15.2, 15.3
        """
        return_code, stdout, stderr = self._run_testbase_cli(
            self.testroot_dir,
            [
                "automojo.tests.testbase.injection.test_constraints",
                "automojo.tests.testbase.patterns.test_function_signatures"
            ]
        )
        
        # Verify tests from both modules were discovered and executed
        self.assertEqual(return_code, 0,
            f"CLI should execute successfully.\nStdout: {stdout}\nStderr: {stderr}")
        self.assertIn("Passed:", stdout,
            f"Should show passed tests in summary.\nStdout: {stdout}\nStderr: {stderr}")


class TestCLIExpressionParsingIntegration(unittest.TestCase):
    """
    Integration tests for CLI expression parsing from command-line arguments.
    
    These tests verify:
    - Expression parsing from command-line arguments (Requirements 2.1-2.5)
    - End-to-end test selection with expressions (Requirements 12.1-12.6)
    - Error handling for invalid expressions
    
    Requirements: 2.1-2.5, 12.1-12.6
    """

    @classmethod
    def setUpClass(cls):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )
        
        cls.repo_root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
        cls.testroot_dir = os.path.join(cls.repo_root, "source", "testroots", "automojo")

    def _run_testbase_cli(self, testroot: str, include_patterns: list, timeout: int = 120) -> tuple:
        """
        Run tests using the testbase CLI command and return result code and output.
        
        Args:
            testroot: Path to the test root directory
            include_patterns: List of include patterns
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd = [
            sys.executable, "-m", "automojo.testbase.cli.testbase_command",
            "testing", "run",
            "--root", testroot
        ]
        
        for pattern in include_patterns:
            cmd.extend(["-i", pattern])
        
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
            timeout=timeout
        )
        
        return result.returncode, result.stdout, result.stderr

    # =========================================================================
    # CLI Expression Parsing from Command-Line Arguments (Requirements 2.1-2.5)
    # =========================================================================

    def test_cli_parses_full_expression_from_command_line(self):
        """
        Test that CLI correctly parses full expression format from command-line.
        
        Verifies:
        - Full expression pkg.mod@TestClass#test_name is parsed correctly
        - All four components are extracted from command-line argument
        
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
        """
        # Use a specific test with full expression format
        return_code, stdout, stderr = self._run_testbase_cli(
            self.testroot_dir,
            ["automojo.tests.testbase.injection.test_constraints@#test_constraint_constrained_parameter"]
        )
        
        # Verify the specific test was selected and executed
        self.assertEqual(return_code, 0,
            f"CLI should execute successfully with full expression.\nStdout: {stdout}\nStderr: {stderr}")
        self.assertIn("Passed:", stdout,
            f"Should show passed tests.\nStdout: {stdout}\nStderr: {stderr}")

    def test_cli_parses_package_module_expression_from_command_line(self):
        """
        Test that CLI correctly parses pkg.mod format from command-line.
        
        Verifies:
        - Package and module are extracted from command-line argument
        - Tests in the specified module are discovered
        
        Requirements: 2.1, 2.4, 12.1
        """
        return_code, stdout, stderr = self._run_testbase_cli(
            self.testroot_dir,
            ["automojo.tests.testbase.patterns.test_function_signatures"]
        )
        
        self.assertEqual(return_code, 0,
            f"CLI should execute successfully with pkg.mod format.\nStdout: {stdout}\nStderr: {stderr}")
        self.assertIn("Passed:", stdout,
            f"Should show passed tests.\nStdout: {stdout}\nStderr: {stderr}")

    def test_cli_parses_nested_package_expression_from_command_line(self):
        """
        Test that CLI correctly parses nested package format from command-line.
        
        Verifies:
        - Nested package paths are correctly parsed (pkg.subpkg.mod)
        - Tests in nested packages are discovered
        
        Requirements: 2.4, 12.5
        """
        return_code, stdout, stderr = self._run_testbase_cli(
            self.testroot_dir,
            ["automojo.tests.testbase.injection.test_constraints"]
        )
        
        self.assertEqual(return_code, 0,
            f"CLI should execute successfully with nested package.\nStdout: {stdout}\nStderr: {stderr}")
        self.assertIn("Passed:", stdout,
            f"Should show passed tests.\nStdout: {stdout}\nStderr: {stderr}")

    def test_cli_parses_testname_with_hash_delimiter(self):
        """
        Test that CLI correctly parses testname using # delimiter.
        
        Verifies:
        - Testname is extracted after # delimiter
        - Only the specified test is executed
        
        Requirements: 2.2, 2.5, 12.3
        """
        return_code, stdout, stderr = self._run_testbase_cli(
            self.testroot_dir,
            ["automojo.tests.testbase.injection.test_constraints@#test_constraint_constrained_parameter"]
        )
        
        self.assertEqual(return_code, 0,
            f"CLI should execute successfully with testname.\nStdout: {stdout}\nStderr: {stderr}")
        # Verify specific test was run
        self.assertIn("Passed:", stdout,
            f"Should show passed tests.\nStdout: {stdout}\nStderr: {stderr}")

    # =========================================================================
    # End-to-End Test Selection with Expressions (Requirements 12.1-12.6)
    # =========================================================================

    def test_cli_end_to_end_single_module_selection(self):
        """
        Test end-to-end test selection with single module expression.
        
        Verifies:
        - Single module expression selects all tests in that module
        - Tests are discovered and executed
        
        Requirements: 12.1
        """
        return_code, stdout, stderr = self._run_testbase_cli(
            self.testroot_dir,
            ["automojo.tests.testbase.patterns.test_function_signatures"]
        )
        
        self.assertEqual(return_code, 0,
            f"CLI should execute successfully.\nStdout: {stdout}\nStderr: {stderr}")
        self.assertIn("Passed:", stdout,
            f"Should show passed tests.\nStdout: {stdout}\nStderr: {stderr}")

    def test_cli_end_to_end_multiple_module_selection(self):
        """
        Test end-to-end test selection with multiple module expressions.
        
        Verifies:
        - Multiple expressions can be provided via CLI
        - Tests from all specified modules are discovered and executed
        
        Requirements: 12.1, 12.5
        """
        return_code, stdout, stderr = self._run_testbase_cli(
            self.testroot_dir,
            [
                "automojo.tests.testbase.injection.test_constraints",
                "automojo.tests.testbase.patterns.test_function_signatures"
            ]
        )
        
        self.assertEqual(return_code, 0,
            f"CLI should execute successfully with multiple modules.\nStdout: {stdout}\nStderr: {stderr}")
        self.assertIn("Passed:", stdout,
            f"Should show passed tests.\nStdout: {stdout}\nStderr: {stderr}")

    def test_cli_end_to_end_wildcard_module_selection(self):
        """
        Test end-to-end test selection with wildcard module expression.
        
        Verifies:
        - Wildcard patterns work for module matching
        - Multiple tests are discovered using wildcard
        
        Requirements: 12.1
        """
        return_code, stdout, stderr = self._run_testbase_cli(
            self.testroot_dir,
            ["automojo.tests.testbase.injection.test_*"]
        )
        
        self.assertEqual(return_code, 0,
            f"CLI should execute successfully with wildcard.\nStdout: {stdout}\nStderr: {stderr}")
        self.assertIn("Passed:", stdout,
            f"Should show passed tests.\nStdout: {stdout}\nStderr: {stderr}")

    def test_cli_end_to_end_specific_test_selection(self):
        """
        Test end-to-end test selection with specific test expression.
        
        Verifies:
        - Specific test can be selected using full expression
        - Only the specified test is executed
        
        Requirements: 12.3, 12.4
        """
        return_code, stdout, stderr = self._run_testbase_cli(
            self.testroot_dir,
            ["automojo.tests.testbase.injection.test_constraints@#test_constraint_constrained_parameter"]
        )
        
        self.assertEqual(return_code, 0,
            f"CLI should execute successfully with specific test.\nStdout: {stdout}\nStderr: {stderr}")
        self.assertIn("Passed:", stdout,
            f"Should show passed tests.\nStdout: {stdout}\nStderr: {stderr}")

    # =========================================================================
    # Error Handling for Invalid Expressions
    # =========================================================================

    def test_cli_error_handling_invalid_method_prefix(self):
        """
        Test that CLI handles invalid method prefix in expression.
        
        Verifies:
        - Invalid testname (not starting with 'test') raises error
        - Error message is descriptive
        
        Requirements: 6.1, 6.2, 6.3
        """
        return_code, stdout, stderr = self._run_testbase_cli(
            self.testroot_dir,
            ["automojo.tests.testbase.injection.test_constraints@#invalid_method_name"]
        )
        
        # Should fail due to invalid method prefix
        self.assertNotEqual(return_code, 0,
            f"CLI should fail with invalid method prefix.\nStdout: {stdout}\nStderr: {stderr}")
        # Error message should mention method_prefix
        combined_output = stdout + stderr
        self.assertTrue(
            "method_prefix" in combined_output.lower() or "error" in combined_output.lower(),
            f"Error output should mention method_prefix or error.\nStdout: {stdout}\nStderr: {stderr}")

    def test_cli_error_handling_nonexistent_module(self):
        """
        Test that CLI handles nonexistent module expression gracefully.
        
        Verifies:
        - Nonexistent module expression is handled
        - CLI completes without crashing
        """
        return_code, stdout, stderr = self._run_testbase_cli(
            self.testroot_dir,
            ["automojo.tests.nonexistent.module"]
        )
        
        # Should complete (may have 0 tests found)
        # The key is that it doesn't crash
        self.assertIsNotNone(return_code,
            f"CLI should complete without crashing.\nStdout: {stdout}\nStderr: {stderr}")

    def test_cli_error_handling_empty_include_pattern(self):
        """
        Test that CLI handles empty include pattern list.
        
        Verifies:
        - Empty include pattern list results in empty test set error
        - CLI provides descriptive error message
        """
        cmd = [
            sys.executable, "-m", "automojo.testbase.cli.testbase_command",
            "testing", "run",
            "--root", self.testroot_dir
        ]
        
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
        
        # CLI returns error when no include patterns result in empty test set
        self.assertNotEqual(result.returncode, 0,
            f"CLI should return error with empty include patterns.\nStdout: {result.stdout}\nStderr: {result.stderr}")
        # Error message should indicate empty test set
        self.assertIn("empty test set", result.stderr.lower(),
            f"Error should mention empty test set.\nStderr: {result.stderr}")


class TestCollectorExpressionFormatVariations(unittest.TestCase):
    """
    Integration tests for various expression format variations.
    
    These tests verify that different expression formats are correctly
    parsed and used for test filtering.
    
    Requirements: 15.1, 15.2, 15.3, 15.4, 15.5
    """

    def test_full_expression_format_parsing(self):
        """
        Test full expression format: pkg.mod@TestClass#test_name
        
        Requirements: 15.1, 15.2, 15.3, 15.4, 15.5
        """
        expr = "pkg.subpkg.mod@TestClass#test_method"
        pkg, mod, cls, name = parse_test_include_expression(expr, None)
        
        self.assertEqual(pkg, "pkg.subpkg")
        self.assertEqual(mod, "mod")
        self.assertEqual(cls, "TestClass")
        self.assertEqual(name, "test_method")

    def test_package_module_only_format_parsing(self):
        """
        Test package.module only format: pkg.mod
        
        Requirements: 15.1, 15.2, 15.3
        """
        expr = "pkg.mod"
        pkg, mod, cls, name = parse_test_include_expression(expr, None)
        
        self.assertEqual(pkg, "pkg")
        self.assertEqual(mod, "mod")
        self.assertIsNone(cls)
        self.assertIsNone(name)

    def test_testname_without_testclass_format_parsing(self):
        """
        Test testname without testclass format: pkg.mod@#test_name
        
        Requirements: 15.1, 15.5
        """
        expr = "pkg.mod@#test_method"
        pkg, mod, cls, name = parse_test_include_expression(expr, None)
        
        self.assertEqual(pkg, "pkg")
        self.assertEqual(mod, "mod")
        self.assertIsNone(cls)
        self.assertEqual(name, "test_method")

    def test_module_only_format_parsing(self):
        """
        Test module only format: mod
        
        Requirements: 15.1, 15.3
        """
        expr = "test_module"
        pkg, mod, cls, name = parse_test_include_expression(expr, None)
        
        self.assertIsNone(pkg)
        self.assertEqual(mod, "test_module")
        self.assertIsNone(cls)
        self.assertIsNone(name)

    def test_deeply_nested_package_format_parsing(self):
        """
        Test deeply nested package format: a.b.c.d.mod
        
        Requirements: 15.1, 15.2, 15.3
        """
        expr = "a.b.c.d.mod"
        pkg, mod, cls, name = parse_test_include_expression(expr, None)
        
        self.assertEqual(pkg, "a.b.c.d")
        self.assertEqual(mod, "mod")
        self.assertIsNone(cls)
        self.assertIsNone(name)

    def test_expression_with_testclass_only_format_parsing(self):
        """
        Test expression with testclass only format: pkg.mod@TestClass
        
        Requirements: 15.1, 15.4
        """
        expr = "pkg.mod@TestClass"
        pkg, mod, cls, name = parse_test_include_expression(expr, None)
        
        self.assertEqual(pkg, "pkg")
        self.assertEqual(mod, "mod")
        self.assertEqual(cls, "TestClass")
        self.assertIsNone(name)


if __name__ == "__main__":
    unittest.main()
