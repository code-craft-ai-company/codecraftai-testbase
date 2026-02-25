import unittest
from types import ModuleType

from automojo.testbase.expressions import parse_test_include_expression


class ParseTestIncludeExpressionTests(unittest.TestCase):

    def test_module_run_invalid_expression(self):
        mod = ModuleType('pkg.mod')
        with self.assertRaises(ValueError):
            parse_test_include_expression('Bad.Expression', mod)

    # =========================================================================
    # Module Workflow Invalid Expression Rejection Tests (Requirements 8.1-8.4)
    # =========================================================================

    def test_module_workflow_rejects_expression_with_dot(self):
        """Test that module workflow raises ValueError when expression contains '.'
        
        Requirements: 8.1
        """
        mod = ModuleType('pkg.mod')
        with self.assertRaises(ValueError) as context:
            parse_test_include_expression('pkg.submod', mod)
        
        error_message = str(context.exception)
        self.assertIn("test class and test method", error_message)

    def test_module_workflow_rejects_expression_with_at_symbol(self):
        """Test that module workflow raises ValueError when expression contains '@'
        
        Requirements: 8.2
        """
        mod = ModuleType('pkg.mod')
        with self.assertRaises(ValueError) as context:
            parse_test_include_expression('TestClass@method', mod)
        
        error_message = str(context.exception)
        self.assertIn("test class and test method", error_message)

    def test_module_workflow_rejects_expression_with_colon(self):
        """Test that module workflow raises ValueError when expression contains ':'
        
        Requirements: 8.3
        """
        mod = ModuleType('pkg.mod')
        with self.assertRaises(ValueError) as context:
            parse_test_include_expression('TestClass:method', mod)
        
        error_message = str(context.exception)
        self.assertIn("test class and test method", error_message)

    def test_module_workflow_error_message_includes_function_context(self):
        """Test that error message includes function name for context
        
        Requirements: 8.4, 13.1
        """
        mod = ModuleType('pkg.mod')
        with self.assertRaises(ValueError) as context:
            parse_test_include_expression('invalid.expression', mod)
        
        error_message = str(context.exception)
        self.assertIn("parse_test_include_expression:", error_message)

    def test_module_run_extracts_package_module(self):
        mod = ModuleType('pkg.mod')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        self.assertEqual(pkg, 'pkg')
        self.assertEqual(module, 'mod')
        self.assertIsNone(testclass)
        self.assertIsNone(testname)

    # =========================================================================
    # Module Workflow Package/Module Extraction Tests (Requirements 7.1-7.4)
    # =========================================================================

    def test_module_workflow_extracts_package_from_simple_module_name(self):
        """Test extraction from simple module name (e.g., pkg.mod)
        
        Requirements: 7.1, 7.2, 7.3
        """
        mod = ModuleType('pkg.mod')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(pkg, 'pkg')
        self.assertEqual(module, 'mod')

    def test_module_workflow_extracts_package_from_nested_package(self):
        """Test extraction from nested package (e.g., pkg.subpkg.mod)
        
        Requirements: 7.1, 7.2, 7.4
        """
        mod = ModuleType('pkg.subpkg.mod')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(pkg, 'pkg.subpkg')
        self.assertEqual(module, 'mod')

    def test_module_workflow_extracts_from_deeply_nested_package(self):
        """Test extraction from deeply nested package (e.g., a.b.c.d.mod)
        
        Requirements: 7.1, 7.2, 7.4
        """
        mod = ModuleType('a.b.c.d.mod')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(pkg, 'a.b.c.d')
        self.assertEqual(module, 'mod')

    def test_module_workflow_uses_testmodule_name_attribute(self):
        """Test that module workflow uses testmodule.__name__ to determine path
        
        Requirements: 7.3
        """
        mod = ModuleType('custom.package.testmodule')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(pkg, 'custom.package')
        self.assertEqual(module, 'testmodule')

    def test_module_workflow_single_component_module_uses_wildcards(self):
        """Test extraction from single-component module name uses wildcards
        
        When module name has no dots (single component), the implementation
        keeps wildcards since it cannot split into package and module.
        
        Requirements: 7.4
        """
        mod = ModuleType('singlemod')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        # Single component module name - wildcards are kept
        self.assertEqual(pkg, '*')
        self.assertEqual(module, '*')

    # =========================================================================
    # Module Workflow Wildcard Expression Tests (Requirements 9.1-9.3)
    # =========================================================================

    def test_module_workflow_wildcard_sets_testclass_to_none(self):
        """Test that '*' expression sets testclass to None
        
        Requirements: 9.1
        """
        mod = ModuleType('pkg.mod')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertIsNone(testclass)

    def test_module_workflow_wildcard_preserves_package_from_testmodule(self):
        """Test that '*' expression preserves package from testmodule
        
        Requirements: 9.2
        """
        mod = ModuleType('mypackage.subpackage.testmod')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(pkg, 'mypackage.subpackage')

    def test_module_workflow_wildcard_preserves_module_from_testmodule(self):
        """Test that '*' expression preserves module from testmodule
        
        Requirements: 9.2
        """
        mod = ModuleType('mypackage.subpackage.testmod')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(module, 'testmod')

    def test_module_workflow_wildcard_sets_testname_to_none(self):
        """Test that '*' expression sets testname to None (matches all tests)
        
        Requirements: 9.2
        """
        mod = ModuleType('pkg.mod')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertIsNone(testname)

    def test_module_workflow_wildcard_returns_complete_tuple(self):
        """Test that '*' expression returns all four tuple elements correctly
        
        Requirements: 9.1, 9.2
        """
        mod = ModuleType('pkg.mod')
        result = parse_test_include_expression('*', mod)
        
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0], 'pkg')  # package
        self.assertEqual(result[1], 'mod')  # module
        self.assertIsNone(result[2])        # testclass
        self.assertIsNone(result[3])        # testname

    # =========================================================================
    # Module Workflow __main__ Handling Tests (Requirements 10.1-10.3)
    # =========================================================================

    def test_module_workflow_main_sets_package_to_wildcard(self):
        """Test that __main__ module sets package to '*'
        
        Requirements: 10.1
        """
        mod = ModuleType('__main__')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(pkg, '*')

    def test_module_workflow_main_sets_module_to_wildcard(self):
        """Test that __main__ module sets module to '*'
        
        Requirements: 10.2
        """
        mod = ModuleType('__main__')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        self.assertEqual(module, '*')

    def test_module_workflow_main_enables_test_discovery_scanning(self):
        """Test that __main__ wildcard values enable test discovery without exact path matching
        
        Requirements: 10.3
        """
        mod = ModuleType('__main__')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        
        # Both package and module should be wildcards to enable scanning
        self.assertEqual(pkg, '*')
        self.assertEqual(module, '*')
        # testclass and testname should be None for full module scan
        self.assertIsNone(testclass)
        self.assertIsNone(testname)

    def test_module_workflow_main_with_testclass_expression(self):
        """Test that __main__ module with testclass expression preserves wildcards for package/module
        
        Requirements: 10.1, 10.2
        """
        mod = ModuleType('__main__')
        pkg, module, testclass, testname = parse_test_include_expression('TestClass', mod)
        
        self.assertEqual(pkg, '*')
        self.assertEqual(module, '*')

    def test_module_workflow_main_with_testclass_and_testname(self):
        """Test that __main__ module with testclass#testname expression works correctly
        
        Requirements: 10.1, 10.2
        """
        mod = ModuleType('__main__')
        pkg, module, testclass, testname = parse_test_include_expression('TestClass#test_method', mod)
        
        self.assertEqual(pkg, '*')
        self.assertEqual(module, '*')
        self.assertEqual(testname, 'test_method')

    # =========================================================================
    # Module Workflow TestClass/TestName Extraction Tests (Requirements 11.1-11.4)
    # =========================================================================

    def test_module_workflow_testclass_with_testname_extraction(self):
        """Test `TestClass#test_method` expression extracts both testclass and testname
        
        Requirements: 11.1, 11.3
        """
        mod = ModuleType('pkg.mod')
        pkg, module, testclass, testname = parse_test_include_expression('TestClass#test_method', mod)
        
        self.assertEqual(pkg, 'pkg')
        self.assertEqual(module, 'mod')
        self.assertEqual(testclass, 'TestClass')
        self.assertEqual(testname, 'test_method')

    def test_module_workflow_testclass_only_no_testname(self):
        """Test `TestClass` expression (no testname) sets testclass and testname to None
        
        Requirements: 11.2
        """
        mod = ModuleType('pkg.mod')
        pkg, module, testclass, testname = parse_test_include_expression('TestClass', mod)
        
        self.assertEqual(pkg, 'pkg')
        self.assertEqual(module, 'mod')
        self.assertEqual(testclass, 'TestClass')
        self.assertIsNone(testname)

    def test_module_workflow_testname_only_no_testclass(self):
        """Test `#test_method` expression (no testclass) extracts testname with testclass as None
        
        When expression is '#test_method', after splitting on '#', the testclass
        portion becomes an empty string which is converted to None.
        
        Requirements: 11.1, 11.3
        """
        mod = ModuleType('pkg.mod')
        pkg, module, testclass, testname = parse_test_include_expression('#test_method', mod)
        
        self.assertEqual(pkg, 'pkg')
        self.assertEqual(module, 'mod')
        # The testclass is the part before '#', which is empty string, converted to None
        self.assertIsNone(testclass)
        self.assertEqual(testname, 'test_method')

    def test_module_workflow_testname_method_prefix_validation(self):
        """Test that method_prefix validation applies to testnames in module workflow
        
        Requirements: 11.4
        """
        mod = ModuleType('pkg.mod')
        with self.assertRaises(ValueError) as context:
            parse_test_include_expression('TestClass#invalid_method', mod)
        
        error_message = str(context.exception)
        self.assertIn('method_prefix', error_message)

    def test_module_workflow_testname_custom_prefix_validation(self):
        """Test that custom method_prefix validation applies in module workflow
        
        Requirements: 11.4
        """
        mod = ModuleType('pkg.mod')
        # Should succeed with custom prefix
        pkg, module, testclass, testname = parse_test_include_expression(
            'TestClass#check_something', mod, method_prefix='check')
        
        self.assertEqual(testname, 'check_something')

    def test_module_workflow_testname_extracted_before_testclass(self):
        """Test that testname extraction occurs before testclass determination
        
        Requirements: 11.3
        """
        mod = ModuleType('pkg.mod')
        pkg, module, testclass, testname = parse_test_include_expression('MyTestClass#test_example', mod)
        
        # Testname should be extracted first, then remaining expression is testclass
        self.assertEqual(testclass, 'MyTestClass')
        self.assertEqual(testname, 'test_example')

    def test_cli_expression_full(self):
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.mod@TestClass#test_demo', None)
        self.assertEqual(pkg, 'pkg')
        self.assertEqual(module, 'mod')
        self.assertEqual(testclass, 'TestClass')
        self.assertEqual(testname, 'test_demo')

    def test_cli_method_prefix_validation(self):
        with self.assertRaises(ValueError):
            parse_test_include_expression('pkg.mod@TestClass#demo', None)

    def test_empty_testclass_becomes_none(self):
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.mod@#test_demo', None)
        self.assertIsNone(testclass)
        self.assertEqual(testname, 'test_demo')

    # =========================================================================
    # CLI Workflow Full Expression Parsing Tests (Requirements 2.1-2.5)
    # =========================================================================

    def test_cli_workflow_full_expression_simple_package(self):
        """Test `pkg.mod@TestClass#test_demo` format extracts all four components
        
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.mod@TestClass#test_demo', None)
        
        self.assertEqual(pkg, 'pkg')
        self.assertEqual(module, 'mod')
        self.assertEqual(testclass, 'TestClass')
        self.assertEqual(testname, 'test_demo')

    def test_cli_workflow_full_expression_nested_package(self):
        """Test `pkg.subpkg.mod@TestClass#test_demo` format with nested packages
        
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.subpkg.mod@TestClass#test_demo', None)
        
        self.assertEqual(pkg, 'pkg.subpkg')
        self.assertEqual(module, 'mod')
        self.assertEqual(testclass, 'TestClass')
        self.assertEqual(testname, 'test_demo')

    def test_cli_workflow_full_expression_deeply_nested_package(self):
        """Test deeply nested package format (e.g., a.b.c.d.mod@TestClass#test_demo)
        
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'a.b.c.d.mod@TestClass#test_demo', None)
        
        self.assertEqual(pkg, 'a.b.c.d')
        self.assertEqual(module, 'mod')
        self.assertEqual(testclass, 'TestClass')
        self.assertEqual(testname, 'test_demo')

    def test_cli_workflow_parses_testname_first_via_hash_delimiter(self):
        """Test that expression is split on '#' to extract testname component first
        
        Requirements: 2.2, 2.5
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.mod@TestClass#test_example_method', None)
        
        # Testname should be extracted via '#' delimiter
        self.assertEqual(testname, 'test_example_method')

    def test_cli_workflow_parses_testclass_via_at_delimiter(self):
        """Test that expression is split on '@' to extract testclass component
        
        Requirements: 2.3
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.mod@MyTestClass#test_method', None)
        
        # Testclass should be extracted via '@' delimiter
        self.assertEqual(testclass, 'MyTestClass')

    def test_cli_workflow_parses_package_module_via_dot_delimiter(self):
        """Test that expression is split on '.' to extract package and module components
        
        Requirements: 2.4
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'mypackage.mymodule@TestClass#test_method', None)
        
        # Package and module should be extracted via '.' delimiter
        self.assertEqual(pkg, 'mypackage')
        self.assertEqual(module, 'mymodule')

    def test_cli_workflow_delimiter_precedence_hash_then_at_then_dot(self):
        """Test that parsing uses delimiter precedence: '#' then '@' then '.'
        
        Requirements: 2.5
        """
        # This expression has all three delimiters
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.subpkg.mod@TestClass#test_demo', None)
        
        # Verify correct parsing order: '#' extracts testname first
        self.assertEqual(testname, 'test_demo')
        # Then '@' extracts testclass
        self.assertEqual(testclass, 'TestClass')
        # Finally '.' splits package and module
        self.assertEqual(pkg, 'pkg.subpkg')
        self.assertEqual(module, 'mod')

    def test_cli_workflow_returns_four_element_tuple(self):
        """Test that CLI workflow returns tuple of exactly four elements
        
        Requirements: 2.1
        """
        result = parse_test_include_expression(
            'pkg.mod@TestClass#test_demo', None)
        
        self.assertEqual(len(result), 4)
        self.assertIsInstance(result, tuple)

    def test_cli_workflow_all_components_are_strings(self):
        """Test that all four components are strings when fully specified
        
        Requirements: 2.1
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.mod@TestClass#test_demo', None)
        
        self.assertIsInstance(pkg, str)
        self.assertIsInstance(module, str)
        self.assertIsInstance(testclass, str)
        self.assertIsInstance(testname, str)

    # =========================================================================
    # CLI Workflow Partial Expression Tests (Requirements 12.1-12.6)
    # =========================================================================

    def test_cli_workflow_pkg_mod_format_package_and_module_only(self):
        """Test `pkg.mod` format (package and module only)
        
        Requirements: 12.1
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.mod', None)
        
        self.assertEqual(pkg, 'pkg')
        self.assertEqual(module, 'mod')
        self.assertIsNone(testclass)
        self.assertIsNone(testname)

    def test_cli_workflow_pkg_mod_testclass_format_no_testname(self):
        """Test `pkg.mod@TestClass` format (no testname)
        
        Requirements: 12.2
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.mod@TestClass', None)
        
        self.assertEqual(pkg, 'pkg')
        self.assertEqual(module, 'mod')
        self.assertEqual(testclass, 'TestClass')
        self.assertIsNone(testname)

    def test_cli_workflow_pkg_mod_testname_format_no_testclass(self):
        """Test `pkg.mod@#test_demo` format (test name without class)
        
        Requirements: 12.4
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.mod@#test_demo', None)
        
        self.assertEqual(pkg, 'pkg')
        self.assertEqual(module, 'mod')
        self.assertIsNone(testclass)
        self.assertEqual(testname, 'test_demo')

    def test_cli_workflow_mod_format_module_only(self):
        """Test `mod` format (module only, no package)
        
        Requirements: 12.6
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'mod', None)
        
        self.assertIsNone(pkg)
        self.assertEqual(module, 'mod')
        self.assertIsNone(testclass)
        self.assertIsNone(testname)

    def test_cli_workflow_nested_package_format(self):
        """Test `pkg.subpkg.mod` format (nested packages)
        
        Requirements: 12.5
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.subpkg.mod', None)
        
        self.assertEqual(pkg, 'pkg.subpkg')
        self.assertEqual(module, 'mod')
        self.assertIsNone(testclass)
        self.assertIsNone(testname)

    def test_cli_workflow_deeply_nested_package_format(self):
        """Test deeply nested package format (e.g., a.b.c.d.mod)
        
        Requirements: 12.5
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'a.b.c.d.mod', None)
        
        self.assertEqual(pkg, 'a.b.c.d')
        self.assertEqual(module, 'mod')
        self.assertIsNone(testclass)
        self.assertIsNone(testname)

    def test_cli_workflow_nested_package_with_testclass(self):
        """Test nested package with testclass format (e.g., pkg.subpkg.mod@TestClass)
        
        Requirements: 12.2, 12.5
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.subpkg.mod@TestClass', None)
        
        self.assertEqual(pkg, 'pkg.subpkg')
        self.assertEqual(module, 'mod')
        self.assertEqual(testclass, 'TestClass')
        self.assertIsNone(testname)

    def test_cli_workflow_module_only_with_testclass(self):
        """Test module only with testclass format (e.g., mod@TestClass)
        
        Requirements: 12.2, 12.6
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'mod@TestClass', None)
        
        self.assertIsNone(pkg)
        self.assertEqual(module, 'mod')
        self.assertEqual(testclass, 'TestClass')
        self.assertIsNone(testname)

    def test_cli_workflow_module_only_with_testname(self):
        """Test module only with testname format (e.g., mod@#test_demo)
        
        Requirements: 12.4, 12.6
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'mod@#test_demo', None)
        
        self.assertIsNone(pkg)
        self.assertEqual(module, 'mod')
        self.assertIsNone(testclass)
        self.assertEqual(testname, 'test_demo')

    def test_cli_workflow_full_expression_format(self):
        """Test `pkg.mod@TestClass#test_demo` format (full specification)
        
        Requirements: 12.3
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.mod@TestClass#test_demo', None)
        
        self.assertEqual(pkg, 'pkg')
        self.assertEqual(module, 'mod')
        self.assertEqual(testclass, 'TestClass')
        self.assertEqual(testname, 'test_demo')

    def test_cli_workflow_partial_expression_returns_four_element_tuple(self):
        """Test that partial expressions return tuple of exactly four elements
        
        Requirements: 12.1, 12.6
        """
        # Test pkg.mod format
        result = parse_test_include_expression('pkg.mod', None)
        self.assertEqual(len(result), 4)
        
        # Test mod format
        result = parse_test_include_expression('mod', None)
        self.assertEqual(len(result), 4)

    def test_cli_workflow_partial_expression_unspecified_components_are_none(self):
        """Test that unspecified components are None in partial expressions
        
        Requirements: 12.1, 12.2, 12.4, 12.6
        """
        # pkg.mod - testclass and testname should be None
        pkg, module, testclass, testname = parse_test_include_expression('pkg.mod', None)
        self.assertIsNone(testclass)
        self.assertIsNone(testname)
        
        # pkg.mod@TestClass - testname should be None
        pkg, module, testclass, testname = parse_test_include_expression('pkg.mod@TestClass', None)
        self.assertIsNone(testname)
        
        # mod - package, testclass, and testname should be None
        pkg, module, testclass, testname = parse_test_include_expression('mod', None)
        self.assertIsNone(pkg)
        self.assertIsNone(testclass)
        self.assertIsNone(testname)

    # =========================================================================
    # Method Prefix Validation Tests (Requirements 6.1-6.5)
    # =========================================================================

    def test_method_prefix_default_test_prefix_validation_cli_workflow(self):
        """Test that default 'test' prefix validation works in CLI workflow
        
        Requirements: 6.1, 6.4
        """
        # Valid testname starting with 'test' should succeed
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.mod@TestClass#test_example', None)
        
        self.assertEqual(testname, 'test_example')

    def test_method_prefix_default_test_prefix_validation_module_workflow(self):
        """Test that default 'test' prefix validation works in module workflow
        
        Requirements: 6.1, 6.4
        """
        mod = ModuleType('pkg.mod')
        # Valid testname starting with 'test' should succeed
        pkg, module, testclass, testname = parse_test_include_expression(
            'TestClass#test_example', mod)
        
        self.assertEqual(testname, 'test_example')

    def test_method_prefix_custom_check_prefix_validation_cli_workflow(self):
        """Test custom 'check' prefix validation in CLI workflow
        
        Requirements: 6.5
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.mod@TestClass#check_something', None, method_prefix='check')
        
        self.assertEqual(testname, 'check_something')

    def test_method_prefix_custom_verify_prefix_validation_cli_workflow(self):
        """Test custom 'verify' prefix validation in CLI workflow
        
        Requirements: 6.5
        """
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.mod@TestClass#verify_behavior', None, method_prefix='verify')
        
        self.assertEqual(testname, 'verify_behavior')

    def test_method_prefix_custom_check_prefix_validation_module_workflow(self):
        """Test custom 'check' prefix validation in module workflow
        
        Requirements: 6.5
        """
        mod = ModuleType('pkg.mod')
        pkg, module, testclass, testname = parse_test_include_expression(
            'TestClass#check_something', mod, method_prefix='check')
        
        self.assertEqual(testname, 'check_something')

    def test_method_prefix_custom_verify_prefix_validation_module_workflow(self):
        """Test custom 'verify' prefix validation in module workflow
        
        Requirements: 6.5
        """
        mod = ModuleType('pkg.mod')
        pkg, module, testclass, testname = parse_test_include_expression(
            'TestClass#verify_behavior', mod, method_prefix='verify')
        
        self.assertEqual(testname, 'verify_behavior')

    def test_method_prefix_invalid_raises_valueerror_cli_workflow(self):
        """Test that invalid prefix raises ValueError in CLI workflow
        
        Requirements: 6.2
        """
        with self.assertRaises(ValueError):
            parse_test_include_expression('pkg.mod@TestClass#invalid_method', None)

    def test_method_prefix_invalid_raises_valueerror_module_workflow(self):
        """Test that invalid prefix raises ValueError in module workflow
        
        Requirements: 6.2
        """
        mod = ModuleType('pkg.mod')
        with self.assertRaises(ValueError):
            parse_test_include_expression('TestClass#invalid_method', mod)

    def test_method_prefix_error_message_includes_prefix_cli_workflow(self):
        """Test that error message includes method_prefix value in CLI workflow
        
        Requirements: 6.3
        """
        with self.assertRaises(ValueError) as context:
            parse_test_include_expression('pkg.mod@TestClass#bad_method', None)
        
        error_message = str(context.exception)
        self.assertIn('method_prefix', error_message)
        self.assertIn('test', error_message)

    def test_method_prefix_error_message_includes_expression_cli_workflow(self):
        """Test that error message includes expression value in CLI workflow
        
        Requirements: 6.3
        """
        with self.assertRaises(ValueError) as context:
            parse_test_include_expression('pkg.mod@TestClass#bad_method', None)
        
        error_message = str(context.exception)
        self.assertIn('expression', error_message)

    def test_method_prefix_error_message_includes_prefix_module_workflow(self):
        """Test that error message includes method_prefix value in module workflow
        
        Requirements: 6.3
        """
        mod = ModuleType('pkg.mod')
        with self.assertRaises(ValueError) as context:
            parse_test_include_expression('TestClass#bad_method', mod)
        
        error_message = str(context.exception)
        self.assertIn('method_prefix', error_message)
        self.assertIn('test', error_message)

    def test_method_prefix_error_message_includes_expression_module_workflow(self):
        """Test that error message includes expression value in module workflow
        
        Requirements: 6.3
        """
        mod = ModuleType('pkg.mod')
        with self.assertRaises(ValueError) as context:
            parse_test_include_expression('TestClass#bad_method', mod)
        
        error_message = str(context.exception)
        self.assertIn('expression', error_message)

    def test_method_prefix_custom_prefix_invalid_raises_valueerror_cli_workflow(self):
        """Test that testname not matching custom prefix raises ValueError in CLI workflow
        
        Requirements: 6.2, 6.5
        """
        # Using 'check' prefix but testname starts with 'test'
        with self.assertRaises(ValueError):
            parse_test_include_expression(
                'pkg.mod@TestClass#test_method', None, method_prefix='check')

    def test_method_prefix_custom_prefix_invalid_raises_valueerror_module_workflow(self):
        """Test that testname not matching custom prefix raises ValueError in module workflow
        
        Requirements: 6.2, 6.5
        """
        mod = ModuleType('pkg.mod')
        # Using 'verify' prefix but testname starts with 'test'
        with self.assertRaises(ValueError):
            parse_test_include_expression(
                'TestClass#test_method', mod, method_prefix='verify')

    def test_method_prefix_error_message_includes_custom_prefix(self):
        """Test that error message includes custom method_prefix value
        
        Requirements: 6.3, 6.5
        """
        with self.assertRaises(ValueError) as context:
            parse_test_include_expression(
                'pkg.mod@TestClass#test_method', None, method_prefix='check')
        
        error_message = str(context.exception)
        self.assertIn('method_prefix', error_message)
        self.assertIn('check', error_message)

    # =========================================================================
    # Return Value Consistency Tests (Requirements 14.1-14.4)
    # =========================================================================

    def test_return_value_always_tuple_of_four_elements_cli_full_expression(self):
        """Test that CLI workflow full expression returns tuple of exactly four elements
        
        Requirements: 14.1
        """
        result = parse_test_include_expression('pkg.mod@TestClass#test_demo', None)
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 4)

    def test_return_value_always_tuple_of_four_elements_cli_partial_expression(self):
        """Test that CLI workflow partial expression returns tuple of exactly four elements
        
        Requirements: 14.1
        """
        # Test pkg.mod format
        result = parse_test_include_expression('pkg.mod', None)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 4)
        
        # Test mod format
        result = parse_test_include_expression('mod', None)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 4)
        
        # Test pkg.mod@TestClass format
        result = parse_test_include_expression('pkg.mod@TestClass', None)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 4)

    def test_return_value_always_tuple_of_four_elements_module_workflow(self):
        """Test that module workflow returns tuple of exactly four elements
        
        Requirements: 14.1
        """
        mod = ModuleType('pkg.mod')
        
        # Test wildcard expression
        result = parse_test_include_expression('*', mod)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 4)
        
        # Test testclass expression
        result = parse_test_include_expression('TestClass', mod)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 4)
        
        # Test testclass#testname expression
        result = parse_test_include_expression('TestClass#test_method', mod)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 4)

    def test_return_value_elements_are_string_or_none_cli_workflow(self):
        """Test that each element in CLI workflow result is either string or None
        
        Requirements: 14.2
        """
        # Full expression - all strings
        result = parse_test_include_expression('pkg.mod@TestClass#test_demo', None)
        for element in result:
            self.assertTrue(isinstance(element, str) or element is None)
        
        # Partial expression - mix of strings and None
        result = parse_test_include_expression('pkg.mod', None)
        for element in result:
            self.assertTrue(isinstance(element, str) or element is None)
        
        # Module only - package is None
        result = parse_test_include_expression('mod', None)
        for element in result:
            self.assertTrue(isinstance(element, str) or element is None)

    def test_return_value_elements_are_string_or_none_module_workflow(self):
        """Test that each element in module workflow result is either string or None
        
        Requirements: 14.2
        """
        mod = ModuleType('pkg.mod')
        
        # Wildcard expression
        result = parse_test_include_expression('*', mod)
        for element in result:
            self.assertTrue(isinstance(element, str) or element is None)
        
        # TestClass expression
        result = parse_test_include_expression('TestClass', mod)
        for element in result:
            self.assertTrue(isinstance(element, str) or element is None)
        
        # TestClass#testname expression
        result = parse_test_include_expression('TestClass#test_method', mod)
        for element in result:
            self.assertTrue(isinstance(element, str) or element is None)

    def test_return_value_none_for_unspecified_package_cli_workflow(self):
        """Test that package is None when not specified in CLI workflow
        
        Requirements: 14.3
        """
        # Module only - no package specified
        pkg, module, testclass, testname = parse_test_include_expression('mod', None)
        self.assertIsNone(pkg)
        
        # Module with testclass - no package specified
        pkg, module, testclass, testname = parse_test_include_expression('mod@TestClass', None)
        self.assertIsNone(pkg)

    def test_return_value_none_for_unspecified_testclass_cli_workflow(self):
        """Test that testclass is None when not specified in CLI workflow
        
        Requirements: 14.3
        """
        # pkg.mod format - no testclass
        pkg, module, testclass, testname = parse_test_include_expression('pkg.mod', None)
        self.assertIsNone(testclass)
        
        # pkg.mod@#test_demo format - empty testclass becomes None
        pkg, module, testclass, testname = parse_test_include_expression('pkg.mod@#test_demo', None)
        self.assertIsNone(testclass)

    def test_return_value_none_for_unspecified_testname_cli_workflow(self):
        """Test that testname is None when not specified in CLI workflow
        
        Requirements: 14.3
        """
        # pkg.mod format - no testname
        pkg, module, testclass, testname = parse_test_include_expression('pkg.mod', None)
        self.assertIsNone(testname)
        
        # pkg.mod@TestClass format - no testname
        pkg, module, testclass, testname = parse_test_include_expression('pkg.mod@TestClass', None)
        self.assertIsNone(testname)

    def test_return_value_none_for_unspecified_testclass_module_workflow(self):
        """Test that testclass is None when wildcard used in module workflow
        
        Requirements: 14.3
        """
        mod = ModuleType('pkg.mod')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        self.assertIsNone(testclass)

    def test_return_value_none_for_unspecified_testname_module_workflow(self):
        """Test that testname is None when not specified in module workflow
        
        Requirements: 14.3
        """
        mod = ModuleType('pkg.mod')
        
        # Wildcard expression - no testname
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        self.assertIsNone(testname)
        
        # TestClass expression - no testname
        pkg, module, testclass, testname = parse_test_include_expression('TestClass', mod)
        self.assertIsNone(testname)

    def test_return_value_tuple_order_cli_workflow(self):
        """Test that tuple order is (package, module, testclass, testname) in CLI workflow
        
        Requirements: 14.4
        """
        result = parse_test_include_expression('mypackage.mymodule@MyTestClass#test_mymethod', None)
        
        # Verify order by checking specific values at each position
        self.assertEqual(result[0], 'mypackage')   # package at index 0
        self.assertEqual(result[1], 'mymodule')    # module at index 1
        self.assertEqual(result[2], 'MyTestClass') # testclass at index 2
        self.assertEqual(result[3], 'test_mymethod') # testname at index 3

    def test_return_value_tuple_order_module_workflow(self):
        """Test that tuple order is (package, module, testclass, testname) in module workflow
        
        Requirements: 14.4
        """
        mod = ModuleType('mypackage.mymodule')
        result = parse_test_include_expression('MyTestClass#test_mymethod', mod)
        
        # Verify order by checking specific values at each position
        self.assertEqual(result[0], 'mypackage')   # package at index 0
        self.assertEqual(result[1], 'mymodule')    # module at index 1
        self.assertEqual(result[2], 'MyTestClass') # testclass at index 2
        self.assertEqual(result[3], 'test_mymethod') # testname at index 3

    def test_return_value_tuple_order_consistent_across_workflows(self):
        """Test that tuple order is consistent between CLI and module workflows
        
        Requirements: 14.4
        """
        # CLI workflow
        cli_result = parse_test_include_expression('pkg.mod@TestClass#test_demo', None)
        
        # Module workflow with same package/module
        mod = ModuleType('pkg.mod')
        module_result = parse_test_include_expression('TestClass#test_demo', mod)
        
        # Both should have same order: (package, module, testclass, testname)
        self.assertEqual(cli_result[0], module_result[0])  # package
        self.assertEqual(cli_result[1], module_result[1])  # module
        self.assertEqual(cli_result[2], module_result[2])  # testclass
        self.assertEqual(cli_result[3], module_result[3])  # testname

    def test_return_value_tuple_order_with_nested_package(self):
        """Test that tuple order is maintained with nested packages
        
        Requirements: 14.4
        """
        result = parse_test_include_expression('a.b.c.mod@TestClass#test_method', None)
        
        # Verify order with nested package
        self.assertEqual(result[0], 'a.b.c')       # package at index 0 (nested)
        self.assertEqual(result[1], 'mod')         # module at index 1
        self.assertEqual(result[2], 'TestClass')   # testclass at index 2
        self.assertEqual(result[3], 'test_method') # testname at index 3

    def test_return_value_tuple_unpacking_works_correctly(self):
        """Test that tuple can be unpacked into four variables correctly
        
        Requirements: 14.1, 14.4
        """
        # CLI workflow
        pkg, mod, cls, name = parse_test_include_expression('pkg.mod@TestClass#test_demo', None)
        self.assertEqual(pkg, 'pkg')
        self.assertEqual(mod, 'mod')
        self.assertEqual(cls, 'TestClass')
        self.assertEqual(name, 'test_demo')
        
        # Module workflow
        testmod = ModuleType('pkg.mod')
        pkg, mod, cls, name = parse_test_include_expression('TestClass#test_demo', testmod)
        self.assertEqual(pkg, 'pkg')
        self.assertEqual(mod, 'mod')
        self.assertEqual(cls, 'TestClass')
        self.assertEqual(name, 'test_demo')


if __name__ == '__main__':
    unittest.main()
