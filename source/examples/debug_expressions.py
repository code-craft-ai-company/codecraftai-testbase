"""
    .. module:: debug_expressions
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Example usage of the parse_test_include_expression function.

    This module demonstrates how to use the expression parsing functionality
    in the TestBase framework for test discovery and filtering.

    .. moduleauthor:: CodeCraftX
"""

from types import ModuleType
from typing import Optional

from ccai.testbase.expressions import parse_test_include_expression


# =============================================================================
# CLI WORKFLOW EXAMPLES
# =============================================================================
# The CLI workflow is used when running tests from the command line.
# In this mode, testmodule is None and full expressions are parsed.
# =============================================================================

def example_cli_full_expression():
    """
    Demonstrates parsing a full CLI expression with all components:
    package, module, test class, and test name.
    """
    print("\n--- CLI Workflow: Full Expression ---")
    
    expression = "mypackage.mymodule@TestClass#test_example"
    pkg, mod, cls, name = parse_test_include_expression(expression, testmodule=None)
    
    print(f"Expression: {expression}")
    print(f"  Package:   {pkg}")
    print(f"  Module:    {mod}")
    print(f"  TestClass: {cls}")
    print(f"  TestName:  {name}")
    
    assert pkg == "mypackage"
    assert mod == "mymodule"
    assert cls == "TestClass"
    assert name == "test_example"


def example_cli_package_module_only():
    """
    Demonstrates parsing a CLI expression with only package and module.
    This targets all tests within a specific module.
    """
    print("\n--- CLI Workflow: Package and Module Only ---")
    
    expression = "mypackage.mymodule"
    pkg, mod, cls, name = parse_test_include_expression(expression, testmodule=None)
    
    print(f"Expression: {expression}")
    print(f"  Package:   {pkg}")
    print(f"  Module:    {mod}")
    print(f"  TestClass: {cls}")
    print(f"  TestName:  {name}")
    
    assert pkg == "mypackage"
    assert mod == "mymodule"
    assert cls is None
    assert name is None


def example_cli_nested_package():
    """
    Demonstrates parsing a CLI expression with nested packages.
    All components except the last are treated as the package path.
    """
    print("\n--- CLI Workflow: Nested Package ---")
    
    expression = "pkg.subpkg.deepsubpkg.mod@TestClass"
    pkg, mod, cls, name = parse_test_include_expression(expression, testmodule=None)
    
    print(f"Expression: {expression}")
    print(f"  Package:   {pkg}")
    print(f"  Module:    {mod}")
    print(f"  TestClass: {cls}")
    print(f"  TestName:  {name}")
    
    assert pkg == "pkg.subpkg.deepsubpkg"
    assert mod == "mod"
    assert cls == "TestClass"
    assert name is None


def example_cli_module_only():
    """
    Demonstrates parsing a CLI expression with only a module name.
    When there's no dot, the expression is treated as a module with no package.
    """
    print("\n--- CLI Workflow: Module Only (No Package) ---")
    
    expression = "mymodule"
    pkg, mod, cls, name = parse_test_include_expression(expression, testmodule=None)
    
    print(f"Expression: {expression}")
    print(f"  Package:   {pkg}")
    print(f"  Module:    {mod}")
    print(f"  TestClass: {cls}")
    print(f"  TestName:  {name}")
    
    assert pkg is None
    assert mod == "mymodule"
    assert cls is None
    assert name is None


def example_cli_testname_without_class():
    """
    Demonstrates parsing a CLI expression with a test name but no test class.
    The empty testclass (between @ and #) becomes None.
    """
    print("\n--- CLI Workflow: Test Name Without Class ---")
    
    expression = "pkg.mod@#test_specific_method"
    pkg, mod, cls, name = parse_test_include_expression(expression, testmodule=None)
    
    print(f"Expression: {expression}")
    print(f"  Package:   {pkg}")
    print(f"  Module:    {mod}")
    print(f"  TestClass: {cls}")
    print(f"  TestName:  {name}")
    
    assert pkg == "pkg"
    assert mod == "mod"
    assert cls is None
    assert name == "test_specific_method"


def example_cli_with_testclass_only():
    """
    Demonstrates parsing a CLI expression with package, module, and test class.
    This targets all tests within a specific test class.
    """
    print("\n--- CLI Workflow: With TestClass Only ---")
    
    expression = "pkg.mod@MyTestClass"
    pkg, mod, cls, name = parse_test_include_expression(expression, testmodule=None)
    
    print(f"Expression: {expression}")
    print(f"  Package:   {pkg}")
    print(f"  Module:    {mod}")
    print(f"  TestClass: {cls}")
    print(f"  TestName:  {name}")
    
    assert pkg == "pkg"
    assert mod == "mod"
    assert cls == "MyTestClass"
    assert name is None


# =============================================================================
# DEBUG/SCRIPT WORKFLOW EXAMPLES
# =============================================================================
# The debug/script workflow is used when running a test module directly
# (e.g., python test_module.py or via IDE debugger).
# In this mode, testmodule is provided and simplified expressions are used.
# =============================================================================

class MockModule:
    """A mock module object for demonstration purposes."""
    def __init__(self, name: str):
        self.__name__ = name


def example_module_workflow_wildcard():
    """
    Demonstrates using the wildcard expression in module workflow.
    The '*' expression matches all tests in the module.
    """
    print("\n--- Module Workflow: Wildcard Expression ---")
    
    # Simulate a test module with a known path
    mock_module = MockModule("mypackage.mymodule")
    
    expression = "*"
    pkg, mod, cls, name = parse_test_include_expression(expression, testmodule=mock_module)
    
    print(f"Module:     {mock_module.__name__}")
    print(f"Expression: {expression}")
    print(f"  Package:   {pkg}")
    print(f"  Module:    {mod}")
    print(f"  TestClass: {cls}")
    print(f"  TestName:  {name}")
    
    assert pkg == "mypackage"
    assert mod == "mymodule"
    assert cls is None
    assert name is None


def example_module_workflow_testclass():
    """
    Demonstrates specifying a test class in module workflow.
    The expression is treated as the test class name.
    """
    print("\n--- Module Workflow: Test Class Only ---")
    
    mock_module = MockModule("mypackage.mymodule")
    
    expression = "TestClass"
    pkg, mod, cls, name = parse_test_include_expression(expression, testmodule=mock_module)
    
    print(f"Module:     {mock_module.__name__}")
    print(f"Expression: {expression}")
    print(f"  Package:   {pkg}")
    print(f"  Module:    {mod}")
    print(f"  TestClass: {cls}")
    print(f"  TestName:  {name}")
    
    assert pkg == "mypackage"
    assert mod == "mymodule"
    assert cls == "TestClass"
    assert name is None


def example_module_workflow_testclass_and_method():
    """
    Demonstrates specifying both test class and test method in module workflow.
    """
    print("\n--- Module Workflow: Test Class and Method ---")
    
    mock_module = MockModule("mypackage.mymodule")
    
    expression = "TestClass#test_specific"
    pkg, mod, cls, name = parse_test_include_expression(expression, testmodule=mock_module)
    
    print(f"Module:     {mock_module.__name__}")
    print(f"Expression: {expression}")
    print(f"  Package:   {pkg}")
    print(f"  Module:    {mod}")
    print(f"  TestClass: {cls}")
    print(f"  TestName:  {name}")
    
    assert pkg == "mypackage"
    assert mod == "mymodule"
    assert cls == "TestClass"
    assert name == "test_specific"


def example_module_workflow_testmethod_only():
    """
    Demonstrates specifying only a test method in module workflow.
    The '#' prefix indicates a test method without a class filter.
    """
    print("\n--- Module Workflow: Test Method Only ---")
    
    mock_module = MockModule("mypackage.mymodule")
    
    expression = "#test_specific"
    pkg, mod, cls, name = parse_test_include_expression(expression, testmodule=mock_module)
    
    print(f"Module:     {mock_module.__name__}")
    print(f"Expression: {expression}")
    print(f"  Package:   {pkg}")
    print(f"  Module:    {mod}")
    print(f"  TestClass: {cls}")
    print(f"  TestName:  {name}")
    
    assert pkg == "mypackage"
    assert mod == "mymodule"
    assert cls is None or cls == ""  # Empty string becomes the testclass
    assert name == "test_specific"


def example_module_workflow_main():
    """
    Demonstrates __main__ module handling in module workflow.
    When a module is run directly, its __name__ is "__main__".
    The parser returns wildcards for package and module.
    """
    print("\n--- Module Workflow: __main__ Module ---")
    
    # Simulate running a module directly (python test_module.py)
    mock_module = MockModule("__main__")
    
    expression = "*"
    pkg, mod, cls, name = parse_test_include_expression(expression, testmodule=mock_module)
    
    print(f"Module:     {mock_module.__name__}")
    print(f"Expression: {expression}")
    print(f"  Package:   {pkg}")
    print(f"  Module:    {mod}")
    print(f"  TestClass: {cls}")
    print(f"  TestName:  {name}")
    
    assert pkg == "*"
    assert mod == "*"
    assert cls is None
    assert name is None


def example_module_workflow_nested_package():
    """
    Demonstrates module workflow with a deeply nested package path.
    """
    print("\n--- Module Workflow: Nested Package ---")
    
    mock_module = MockModule("pkg.subpkg.deepsubpkg.testmodule")
    
    expression = "TestClass#test_method"
    pkg, mod, cls, name = parse_test_include_expression(expression, testmodule=mock_module)
    
    print(f"Module:     {mock_module.__name__}")
    print(f"Expression: {expression}")
    print(f"  Package:   {pkg}")
    print(f"  Module:    {mod}")
    print(f"  TestClass: {cls}")
    print(f"  TestName:  {name}")
    
    assert pkg == "pkg.subpkg.deepsubpkg"
    assert mod == "testmodule"
    assert cls == "TestClass"
    assert name == "test_method"


# =============================================================================
# CUSTOM METHOD PREFIX EXAMPLES
# =============================================================================
# The method_prefix parameter allows customization of the test method
# naming convention. By default, test methods must start with "test".
# =============================================================================

def example_custom_prefix_check():
    """
    Demonstrates using a custom method prefix 'check'.
    """
    print("\n--- Custom Method Prefix: 'check' ---")
    
    expression = "pkg.mod@TestClass#check_validation"
    pkg, mod, cls, name = parse_test_include_expression(
        expression, 
        testmodule=None, 
        method_prefix="check"
    )
    
    print(f"Expression:    {expression}")
    print(f"Method Prefix: check")
    print(f"  Package:   {pkg}")
    print(f"  Module:    {mod}")
    print(f"  TestClass: {cls}")
    print(f"  TestName:  {name}")
    
    assert pkg == "pkg"
    assert mod == "mod"
    assert cls == "TestClass"
    assert name == "check_validation"


def example_custom_prefix_verify():
    """
    Demonstrates using a custom method prefix 'verify'.
    """
    print("\n--- Custom Method Prefix: 'verify' ---")
    
    expression = "pkg.mod@TestClass#verify_output"
    pkg, mod, cls, name = parse_test_include_expression(
        expression, 
        testmodule=None, 
        method_prefix="verify"
    )
    
    print(f"Expression:    {expression}")
    print(f"Method Prefix: verify")
    print(f"  Package:   {pkg}")
    print(f"  Module:    {mod}")
    print(f"  TestClass: {cls}")
    print(f"  TestName:  {name}")
    
    assert pkg == "pkg"
    assert mod == "mod"
    assert cls == "TestClass"
    assert name == "verify_output"


def example_custom_prefix_module_workflow():
    """
    Demonstrates using a custom method prefix in module workflow.
    """
    print("\n--- Custom Method Prefix in Module Workflow ---")
    
    mock_module = MockModule("mypackage.mymodule")
    
    expression = "TestClass#check_something"
    pkg, mod, cls, name = parse_test_include_expression(
        expression, 
        testmodule=mock_module, 
        method_prefix="check"
    )
    
    print(f"Module:        {mock_module.__name__}")
    print(f"Expression:    {expression}")
    print(f"Method Prefix: check")
    print(f"  Package:   {pkg}")
    print(f"  Module:    {mod}")
    print(f"  TestClass: {cls}")
    print(f"  TestName:  {name}")
    
    assert pkg == "mypackage"
    assert mod == "mymodule"
    assert cls == "TestClass"
    assert name == "check_something"


# =============================================================================
# ERROR HANDLING EXAMPLES
# =============================================================================
# These examples demonstrate how the parser handles invalid expressions
# and provides descriptive error messages.
# =============================================================================

def example_error_invalid_prefix():
    """
    Demonstrates the error when a test name doesn't start with the method prefix.
    """
    print("\n--- Error Handling: Invalid Method Prefix ---")
    
    expression = "pkg.mod@TestClass#invalid_method"
    
    try:
        parse_test_include_expression(expression, testmodule=None)
        print("ERROR: Expected ValueError was not raised!")
    except ValueError as e:
        print(f"Expression: {expression}")
        print(f"Caught expected ValueError:")
        print(f"  {e}")
        assert "method_prefix" in str(e)


def example_error_module_workflow_with_dot():
    """
    Demonstrates the error when module workflow expression contains a dot.
    Module workflow expressions should only have test class and test method.
    """
    print("\n--- Error Handling: Module Workflow with Dot ---")
    
    mock_module = MockModule("mypackage.mymodule")
    expression = "pkg.mod"  # Invalid: contains dot
    
    try:
        parse_test_include_expression(expression, testmodule=mock_module)
        print("ERROR: Expected ValueError was not raised!")
    except ValueError as e:
        print(f"Module:     {mock_module.__name__}")
        print(f"Expression: {expression}")
        print(f"Caught expected ValueError:")
        print(f"  {e}")
        assert "test class and test method" in str(e)


def example_error_module_workflow_with_at():
    """
    Demonstrates the error when module workflow expression contains '@'.
    """
    print("\n--- Error Handling: Module Workflow with @ ---")
    
    mock_module = MockModule("mypackage.mymodule")
    expression = "TestClass@something"  # Invalid: contains @
    
    try:
        parse_test_include_expression(expression, testmodule=mock_module)
        print("ERROR: Expected ValueError was not raised!")
    except ValueError as e:
        print(f"Module:     {mock_module.__name__}")
        print(f"Expression: {expression}")
        print(f"Caught expected ValueError:")
        print(f"  {e}")
        assert "test class and test method" in str(e)


def example_error_module_workflow_with_colon():
    """
    Demonstrates the error when module workflow expression contains ':'.
    """
    print("\n--- Error Handling: Module Workflow with Colon ---")
    
    mock_module = MockModule("mypackage.mymodule")
    expression = "TestClass:something"  # Invalid: contains colon
    
    try:
        parse_test_include_expression(expression, testmodule=mock_module)
        print("ERROR: Expected ValueError was not raised!")
    except ValueError as e:
        print(f"Module:     {mock_module.__name__}")
        print(f"Expression: {expression}")
        print(f"Caught expected ValueError:")
        print(f"  {e}")
        assert "test class and test method" in str(e)


def example_error_custom_prefix_mismatch():
    """
    Demonstrates the error when test name doesn't match custom prefix.
    """
    print("\n--- Error Handling: Custom Prefix Mismatch ---")
    
    expression = "pkg.mod@TestClass#test_method"  # Uses 'test' prefix
    
    try:
        # But we require 'check' prefix
        parse_test_include_expression(expression, testmodule=None, method_prefix="check")
        print("ERROR: Expected ValueError was not raised!")
    except ValueError as e:
        print(f"Expression:    {expression}")
        print(f"Method Prefix: check")
        print(f"Caught expected ValueError:")
        print(f"  {e}")
        assert "method_prefix" in str(e)
        assert "check" in str(e)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main_debug_expressions():
    """Run all expression parsing examples."""
    
    print("=" * 70)
    print("Expression Parsing Examples")
    print("=" * 70)
    
    # CLI Workflow Examples
    print("\n" + "=" * 70)
    print("CLI WORKFLOW EXAMPLES")
    print("=" * 70)
    example_cli_full_expression()
    example_cli_package_module_only()
    example_cli_nested_package()
    example_cli_module_only()
    example_cli_testname_without_class()
    example_cli_with_testclass_only()
    
    # Debug/Script Workflow Examples
    print("\n" + "=" * 70)
    print("DEBUG/SCRIPT WORKFLOW EXAMPLES")
    print("=" * 70)
    example_module_workflow_wildcard()
    example_module_workflow_testclass()
    example_module_workflow_testclass_and_method()
    example_module_workflow_testmethod_only()
    example_module_workflow_main()
    example_module_workflow_nested_package()
    
    # Custom Method Prefix Examples
    print("\n" + "=" * 70)
    print("CUSTOM METHOD PREFIX EXAMPLES")
    print("=" * 70)
    example_custom_prefix_check()
    example_custom_prefix_verify()
    example_custom_prefix_module_workflow()
    
    # Error Handling Examples
    print("\n" + "=" * 70)
    print("ERROR HANDLING EXAMPLES")
    print("=" * 70)
    example_error_invalid_prefix()
    example_error_module_workflow_with_dot()
    example_error_module_workflow_with_at()
    example_error_module_workflow_with_colon()
    example_error_custom_prefix_mismatch()
    
    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main_debug_expressions()
