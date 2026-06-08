"""
    Integration tests for debug/script workflow expression parsing.
    
    Tests verify:
    - Expression parsing with actual module objects (Requirements 7.1-7.4)
    - Test selection in debug workflow
    - __main__ module handling (Requirements 10.1-10.3)
    
    Requirements: 7.1-7.4, 10.1-10.3
"""

import os
import unittest

from types import ModuleType

from ccai.thisapp.persona import APP_PERSONA_ESTABLISHED, establish_app_persona
from ccai.testbase.expressions import parse_test_include_expression


class DebugWorkflowExpressionParsingIntegration(unittest.TestCase):
    """
    Integration tests for expression parsing with actual module objects.
    
    These tests verify that expression parsing works correctly in the
    debug/script workflow where a testmodule object is provided.
    
    Requirements: 7.1-7.4
    """

    @classmethod
    def setUpClass(cls):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="codecraftai-testbase",
                logger_name="codecraftai-testbase",
                log_basename="codecraftai-testbase"
            )
        
        cls.repo_root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
        cls.testroot_dir = os.path.join(cls.repo_root, "source", "testroots", "ccai")

    def test_module_workflow_parses_expression_with_actual_module_object(self):
        """
        Test that module workflow correctly parses expression with actual module object.
        
        Verifies:
        - Expression parser accepts actual ModuleType objects
        - Package and module are extracted from testmodule.__name__
        
        Requirements: 7.1, 7.2
        """
        mod = ModuleType('ccai.tests.testbase.injection.test_constraints')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(pkg, 'ccai.tests.testbase.injection')
        self.assertEqual(module, 'test_constraints')
        self.assertIsNone(testclass)
        self.assertIsNone(testname)

    def test_module_workflow_uses_testmodule_name_for_package_extraction(self):
        """
        Test that module workflow uses testmodule.__name__ to determine module path.
        
        Verifies:
        - testmodule.__name__ is used to extract package and module
        - Correct splitting of dotted module name
        
        Requirements: 7.3
        """
        mod = ModuleType('ccai.tests.testbase.patterns.test_function_signatures')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(pkg, 'ccai.tests.testbase.patterns')
        self.assertEqual(module, 'test_function_signatures')

    def test_module_workflow_splits_module_name_correctly(self):
        """
        Test that module workflow correctly splits module name into package and module.
        
        Verifies:
        - Module name is split on '.' delimiter
        - All components except last become package
        - Last component becomes module
        
        Requirements: 7.4
        """
        mod = ModuleType('a.b.c.d.test_module')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(pkg, 'a.b.c.d')
        self.assertEqual(module, 'test_module')

    def test_module_workflow_with_testclass_expression(self):
        """
        Test that module workflow correctly handles testclass expression.
        
        Verifies:
        - Testclass is extracted from expression
        - Package and module come from testmodule
        
        Requirements: 7.1, 7.2
        """
        mod = ModuleType('ccai.tests.testbase.injection.test_constraints')
        pkg, module, testclass, testname = parse_test_include_expression('TestClass', mod)
        
        self.assertEqual(pkg, 'ccai.tests.testbase.injection')
        self.assertEqual(module, 'test_constraints')
        self.assertEqual(testclass, 'TestClass')
        self.assertIsNone(testname)

    def test_module_workflow_with_testclass_and_testname_expression(self):
        """
        Test that module workflow correctly handles testclass#testname expression.
        
        Verifies:
        - Both testclass and testname are extracted
        - Package and module come from testmodule
        
        Requirements: 7.1, 7.2
        """
        mod = ModuleType('ccai.tests.testbase.injection.test_constraints')
        pkg, module, testclass, testname = parse_test_include_expression(
            'TestClass#test_method', mod)
        
        self.assertEqual(pkg, 'ccai.tests.testbase.injection')
        self.assertEqual(module, 'test_constraints')
        self.assertEqual(testclass, 'TestClass')
        self.assertEqual(testname, 'test_method')

    def test_module_workflow_with_testname_only_expression(self):
        """
        Test that module workflow correctly handles #testname expression.
        
        Verifies:
        - Testname is extracted from expression
        - Testclass is None when not specified
        - Package and module come from testmodule
        
        Requirements: 7.1, 7.2
        """
        mod = ModuleType('ccai.tests.testbase.injection.test_constraints')
        pkg, module, testclass, testname = parse_test_include_expression(
            '#test_method', mod)
        
        self.assertEqual(pkg, 'ccai.tests.testbase.injection')
        self.assertEqual(module, 'test_constraints')
        self.assertIsNone(testclass)
        self.assertEqual(testname, 'test_method')

    def test_module_workflow_with_real_module_path_patterns(self):
        """
        Test module workflow with realistic module path patterns.
        
        Verifies:
        - Various realistic module paths are correctly parsed
        - Package and module extraction works for different path depths
        
        Requirements: 7.1, 7.2, 7.3, 7.4
        """
        test_cases = [
            ('ccai.tests.testbase.injection.test_constraints', 
             'ccai.tests.testbase.injection', 'test_constraints'),
            ('ccai.tests.testbase.patterns.test_function_signatures',
             'ccai.tests.testbase.patterns', 'test_function_signatures'),
            ('tests.unit.test_example',
             'tests.unit', 'test_example'),
            ('myproject.tests.integration.api.test_endpoints',
             'myproject.tests.integration.api', 'test_endpoints'),
        ]
        
        for module_name, expected_pkg, expected_mod in test_cases:
            mod = ModuleType(module_name)
            pkg, module, testclass, testname = parse_test_include_expression('*', mod)
            
            self.assertEqual(pkg, expected_pkg, 
                f"Package mismatch for {module_name}")
            self.assertEqual(module, expected_mod,
                f"Module mismatch for {module_name}")


class DebugWorkflowMainModuleHandlingIntegration(unittest.TestCase):
    """
    Integration tests for __main__ module handling in debug workflow.
    
    These tests verify that expression parsing correctly handles the
    __main__ module case which occurs when running test files directly.
    
    Requirements: 10.1-10.3
    """

    @classmethod
    def setUpClass(cls):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="codecraftai-testbase",
                logger_name="codecraftai-testbase",
                log_basename="codecraftai-testbase"
            )

    def test_main_module_sets_package_to_wildcard(self):
        """
        Test that __main__ module sets package to '*'.
        
        Verifies:
        - When testmodule.__name__ is "__main__", package is set to "*"
        - This enables test discovery without exact path matching
        
        Requirements: 10.1
        """
        mod = ModuleType('__main__')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(pkg, '*')

    def test_main_module_sets_module_to_wildcard(self):
        """
        Test that __main__ module sets module to '*'.
        
        Verifies:
        - When testmodule.__name__ is "__main__", module is set to "*"
        - This enables test discovery without exact path matching
        
        Requirements: 10.2
        """
        mod = ModuleType('__main__')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(module, '*')

    def test_main_module_enables_test_discovery_scanning(self):
        """
        Test that __main__ wildcard values enable test discovery scanning.
        
        Verifies:
        - Both package and module are wildcards for __main__
        - This allows test discovery to scan without exact path matching
        
        Requirements: 10.3
        """
        mod = ModuleType('__main__')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(pkg, '*')
        self.assertEqual(module, '*')
        self.assertIsNone(testclass)
        self.assertIsNone(testname)

    def test_main_module_with_testclass_preserves_wildcards(self):
        """
        Test that __main__ module with testclass expression preserves wildcards.
        
        Verifies:
        - Package and module remain wildcards even with testclass specified
        - Testclass is correctly extracted
        
        Requirements: 10.1, 10.2
        """
        mod = ModuleType('__main__')
        pkg, module, testclass, testname = parse_test_include_expression('TestClass', mod)
        
        self.assertEqual(pkg, '*')
        self.assertEqual(module, '*')
        self.assertEqual(testclass, 'TestClass')

    def test_main_module_with_testclass_and_testname_preserves_wildcards(self):
        """
        Test that __main__ module with testclass#testname preserves wildcards.
        
        Verifies:
        - Package and module remain wildcards
        - Both testclass and testname are correctly extracted
        
        Requirements: 10.1, 10.2
        """
        mod = ModuleType('__main__')
        pkg, module, testclass, testname = parse_test_include_expression(
            'TestClass#test_method', mod)
        
        self.assertEqual(pkg, '*')
        self.assertEqual(module, '*')
        self.assertEqual(testclass, 'TestClass')
        self.assertEqual(testname, 'test_method')

    def test_main_module_with_testname_only_preserves_wildcards(self):
        """
        Test that __main__ module with #testname preserves wildcards.
        
        Verifies:
        - Package and module remain wildcards
        - Testname is correctly extracted
        - Testclass is None
        
        Requirements: 10.1, 10.2
        """
        mod = ModuleType('__main__')
        pkg, module, testclass, testname = parse_test_include_expression(
            '#test_method', mod)
        
        self.assertEqual(pkg, '*')
        self.assertEqual(module, '*')
        self.assertIsNone(testclass)
        self.assertEqual(testname, 'test_method')

    def test_main_module_returns_consistent_tuple_structure(self):
        """
        Test that __main__ module returns consistent tuple structure.
        
        Verifies:
        - Return value is always a 4-element tuple
        - Elements are either strings or None
        
        Requirements: 10.1, 10.2, 10.3
        """
        mod = ModuleType('__main__')
        
        # Test with wildcard expression
        result = parse_test_include_expression('*', mod)
        self.assertEqual(len(result), 4)
        self.assertIsInstance(result, tuple)
        
        # Test with testclass expression
        result = parse_test_include_expression('TestClass', mod)
        self.assertEqual(len(result), 4)
        
        # Test with testclass#testname expression
        result = parse_test_include_expression('TestClass#test_method', mod)
        self.assertEqual(len(result), 4)


class DebugWorkflowTestSelectionIntegration(unittest.TestCase):
    """
    Integration tests for test selection in debug workflow.
    
    These tests verify that expression parsing correctly selects tests
    when running test modules directly via the debug/script workflow.
    
    Requirements: 7.1-7.4, 10.1-10.3
    """

    @classmethod
    def setUpClass(cls):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="codecraftai-testbase",
                logger_name="codecraftai-testbase",
                log_basename="codecraftai-testbase"
            )

    def test_debug_workflow_extracts_package_module_from_testmodule(self):
        """
        Test that debug workflow extracts package and module from testmodule object.
        
        Verifies:
        - Package is extracted from testmodule.__name__
        - Module is extracted from testmodule.__name__
        
        Requirements: 7.3, 7.4
        """
        mod = ModuleType('ccai.tests.testbase.injection.test_constraints')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(pkg, 'ccai.tests.testbase.injection')
        self.assertEqual(module, 'test_constraints')

    def test_debug_workflow_handles_nested_package_paths(self):
        """
        Test that debug workflow correctly handles nested package paths.
        
        Verifies:
        - Deeply nested package paths are correctly parsed
        - All components except last become package
        
        Requirements: 7.4
        """
        mod = ModuleType('ccai.tests.testbase.patterns.test_function_signatures')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(pkg, 'ccai.tests.testbase.patterns')
        self.assertEqual(module, 'test_function_signatures')

    def test_debug_workflow_wildcard_selects_all_tests(self):
        """
        Test that wildcard expression in debug workflow selects all tests.
        
        Verifies:
        - Wildcard '*' sets testclass to None
        - Wildcard '*' sets testname to None
        - This allows all tests in the module to be selected
        
        Requirements: 7.1, 7.2
        """
        mod = ModuleType('ccai.tests.testbase.injection.test_constraints')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertIsNone(testclass)
        self.assertIsNone(testname)

    def test_debug_workflow_testname_expression_selects_specific_test(self):
        """
        Test that testname expression in debug workflow selects specific test.
        
        Verifies:
        - Testname is extracted from expression
        - Only the specified test would be selected
        
        Requirements: 7.1, 7.2
        """
        mod = ModuleType('ccai.tests.testbase.injection.test_constraints')
        pkg, module, testclass, testname = parse_test_include_expression(
            '#test_constraint_constrained_parameter', mod)
        
        self.assertEqual(testname, 'test_constraint_constrained_parameter')
        self.assertIsNone(testclass)

    def test_debug_workflow_testclass_expression_selects_class_tests(self):
        """
        Test that testclass expression in debug workflow selects class tests.
        
        Verifies:
        - Testclass is extracted from expression
        - All tests in the specified class would be selected
        
        Requirements: 7.1, 7.2
        """
        mod = ModuleType('ccai.tests.testbase.injection.test_constraints')
        pkg, module, testclass, testname = parse_test_include_expression('TestClass', mod)
        
        self.assertEqual(testclass, 'TestClass')
        self.assertIsNone(testname)

    def test_debug_workflow_combined_expression_selects_specific_test_in_class(self):
        """
        Test that combined expression selects specific test in class.
        
        Verifies:
        - Both testclass and testname are extracted
        - Only the specified test in the specified class would be selected
        
        Requirements: 7.1, 7.2
        """
        mod = ModuleType('ccai.tests.testbase.injection.test_constraints')
        pkg, module, testclass, testname = parse_test_include_expression(
            'TestClass#test_method', mod)
        
        self.assertEqual(testclass, 'TestClass')
        self.assertEqual(testname, 'test_method')


class DebugWorkflowEndToEndIntegration(unittest.TestCase):
    """
    End-to-end integration tests for debug/script workflow expression parsing.
    
    These tests verify the complete expression parsing flow for the debug
    workflow, including various expression formats and edge cases.
    
    Requirements: 7.1-7.4, 10.1-10.3
    """

    @classmethod
    def setUpClass(cls):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="codecraftai-testbase",
                logger_name="codecraftai-testbase",
                log_basename="codecraftai-testbase"
            )

    def test_end_to_end_debug_workflow_module_resolution(self):
        """
        Test that debug workflow correctly resolves module identity.
        
        Verifies:
        - Module is correctly identified from module name
        - Package and module are extracted correctly
        
        Requirements: 7.3, 7.4
        """
        mod = ModuleType('ccai.tests.testbase.injection.test_constraints')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(pkg, 'ccai.tests.testbase.injection')
        self.assertEqual(module, 'test_constraints')
        self.assertIsNone(testclass)
        self.assertIsNone(testname)

    def test_end_to_end_debug_workflow_with_various_expressions(self):
        """
        Test end-to-end debug workflow with various expression formats.
        
        Verifies:
        - Different expression formats are correctly parsed
        - Package and module always come from testmodule
        
        Requirements: 7.1-7.4
        """
        mod = ModuleType('ccai.tests.testbase.injection.test_constraints')
        
        # Test wildcard
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        self.assertEqual(pkg, 'ccai.tests.testbase.injection')
        self.assertEqual(module, 'test_constraints')
        self.assertIsNone(testclass)
        self.assertIsNone(testname)
        
        # Test testclass only
        pkg, module, testclass, testname = parse_test_include_expression('TestClass', mod)
        self.assertEqual(pkg, 'ccai.tests.testbase.injection')
        self.assertEqual(module, 'test_constraints')
        self.assertEqual(testclass, 'TestClass')
        self.assertIsNone(testname)
        
        # Test testclass#testname
        pkg, module, testclass, testname = parse_test_include_expression(
            'TestClass#test_method', mod)
        self.assertEqual(pkg, 'ccai.tests.testbase.injection')
        self.assertEqual(module, 'test_constraints')
        self.assertEqual(testclass, 'TestClass')
        self.assertEqual(testname, 'test_method')
        
        # Test #testname only
        pkg, module, testclass, testname = parse_test_include_expression(
            '#test_method', mod)
        self.assertEqual(pkg, 'ccai.tests.testbase.injection')
        self.assertEqual(module, 'test_constraints')
        self.assertIsNone(testclass)
        self.assertEqual(testname, 'test_method')

    def test_end_to_end_main_module_handling(self):
        """
        Test end-to-end __main__ module handling.
        
        Verifies:
        - __main__ module correctly sets wildcards
        - Various expressions work with __main__ module
        
        Requirements: 10.1-10.3
        """
        mod = ModuleType('__main__')
        
        # Test wildcard
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        self.assertEqual(pkg, '*')
        self.assertEqual(module, '*')
        self.assertIsNone(testclass)
        self.assertIsNone(testname)
        
        # Test testclass
        pkg, module, testclass, testname = parse_test_include_expression('TestClass', mod)
        self.assertEqual(pkg, '*')
        self.assertEqual(module, '*')
        self.assertEqual(testclass, 'TestClass')
        
        # Test testclass#testname
        pkg, module, testclass, testname = parse_test_include_expression(
            'TestClass#test_method', mod)
        self.assertEqual(pkg, '*')
        self.assertEqual(module, '*')
        self.assertEqual(testclass, 'TestClass')
        self.assertEqual(testname, 'test_method')

    def test_end_to_end_invalid_expression_rejection(self):
        """
        Test that invalid expressions are rejected in debug workflow.
        
        Verifies:
        - Expressions with '.' are rejected
        - Expressions with '@' are rejected
        - Expressions with ':' are rejected
        
        Requirements: 7.1, 7.2
        """
        mod = ModuleType('ccai.tests.testbase.injection.test_constraints')
        
        # Test expression with '.'
        with self.assertRaises(ValueError):
            parse_test_include_expression('pkg.mod', mod)
        
        # Test expression with '@'
        with self.assertRaises(ValueError):
            parse_test_include_expression('TestClass@method', mod)
        
        # Test expression with ':'
        with self.assertRaises(ValueError):
            parse_test_include_expression('TestClass:method', mod)

    def test_end_to_end_method_prefix_validation(self):
        """
        Test that method prefix validation works in debug workflow.
        
        Verifies:
        - Testnames must start with method_prefix
        - Invalid testnames are rejected
        - Custom method prefixes are supported
        
        Requirements: 7.1, 7.2
        """
        mod = ModuleType('ccai.tests.testbase.injection.test_constraints')
        
        # Valid testname with default prefix
        pkg, module, testclass, testname = parse_test_include_expression(
            '#test_method', mod)
        self.assertEqual(testname, 'test_method')
        
        # Invalid testname with default prefix
        with self.assertRaises(ValueError):
            parse_test_include_expression('#invalid_method', mod)
        
        # Valid testname with custom prefix
        pkg, module, testclass, testname = parse_test_include_expression(
            '#check_method', mod, method_prefix='check')
        self.assertEqual(testname, 'check_method')


if __name__ == "__main__":
    unittest.main()
