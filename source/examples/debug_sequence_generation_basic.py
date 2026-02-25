"""
.. module:: debug_sequence_generation_basic
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Example demonstrating basic sequence document generation.

.. moduleauthor:: AutomationX

This example demonstrates the basic usage of the TestSequencer to generate
a sequence document from a test tree. The sequence document is a Python
module that encodes the test execution order.

Usage:
    python -m source.examples.debug_sequence_generation_basic

Requirements:
    - The automojo.testbase package must be installed
    - The example should be run from the repository root
"""

__author__ = "AutomationX"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import collections
import os
import tempfile

from automojo.thisapp.persona import APP_PERSONA_ESTABLISHED, establish_app_persona
from automojo.thisapp.wellknown import ThisApplicationSingleton
from automojo.runtime.enumerations import JobType
from automojo.runtime.runtimevariables import RuntimeVariablesDesc
import automojo.runtime.paths as runtime_paths

from automojo.testbase.testgroup import TestGroup
from automojo.testbase.testref import TestRef
from automojo.testbase.injection.injectionregistry import injection_registry
from automojo.testbase.injection.injectionscope import InjectionScope
from automojo.testbase.sequencing.testsequencer import TestSequencer


# ============================================================================
# MOCK CLASSES FOR EXAMPLE
# ============================================================================

class MockInjectionScope:
    """
    Mock InjectionScope for demonstrating sequence document generation.
    
    In a real test run, the InjectionScope would be populated by the
    test discovery process with parameter and validator originations.
    """
    
    def __init__(self):
        self.parameter_originations = collections.OrderedDict()
        self.validator_originations = collections.OrderedDict()


class MockTestGroup(TestGroup):
    """
    Mock TestGroup that returns a mock injection scope.
    
    This allows us to demonstrate sequence document generation without
    running the full test discovery process.
    """
    
    def __init__(self, name, package=None):
        super().__init__(name, package)
        self._mock_scope = MockInjectionScope()
    
    def get_resource_scope(self):
        return self._mock_scope


# ============================================================================
# TEST FUNCTIONS FOR EXAMPLE
# ============================================================================

def test_basic_functionality():
    """
    A simple test function that demonstrates basic functionality.
    
    In a real test, this would contain assertions and test logic.
    """
    print("Executing test_basic_functionality")
    return


def test_another_feature():
    """
    Another test function demonstrating a different feature.
    """
    print("Executing test_another_feature")
    return


def test_edge_case():
    """
    A test function for edge case handling.
    """
    print("Executing test_edge_case")
    return


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_tracking_test_function(name, module_name):
    """
    Create a test function with the specified name and module.
    
    Args:
        name: Name of the test function
        module_name: Module name for the test function
        
    Returns:
        A test function with the specified attributes
    """
    def test_func():
        print(f"Executing {name}")
    test_func.__name__ = name
    test_func.__module__ = module_name
    return test_func


def register_test_scope(test_name, module_name):
    """
    Register a test scope in the injection registry.
    
    This is necessary for the sequence document generator to find
    the resource scope for each test.
    
    Args:
        test_name: Name of the test function
        module_name: Name of the module containing the test
    """
    scope_name = "{}#{}".format(module_name, test_name)
    injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, None)


def create_simple_test_tree(module_name, test_names):
    """
    Create a simple test tree with one module containing the specified tests.
    
    This demonstrates the structure of a test tree that would normally
    be created by the test discovery process.
    
    Args:
        module_name: Name of the module
        test_names: List of test function names
        
    Returns:
        MockTestGroup: Root of the test tree
    """
    root = MockTestGroup("root")
    module_group = MockTestGroup(module_name, package="")
    
    for test_name in test_names:
        test_func = create_tracking_test_function(test_name, module_name)
        test_ref = TestRef(test_func)
        module_group._children[test_ref.base_name] = test_ref
        register_test_scope(test_name, module_name)
    
    root._children[module_name] = module_group
    return root


def create_multi_module_test_tree(modules_config):
    """
    Create a test tree with multiple modules.
    
    This demonstrates how tests are organized across multiple modules
    in a typical test suite.
    
    Args:
        modules_config: Dict mapping module names to lists of test names
        
    Returns:
        MockTestGroup: Root of the test tree
    """
    root = MockTestGroup("root")
    
    for module_name, test_names in modules_config.items():
        module_group = MockTestGroup(module_name, package="")
        
        for test_name in test_names:
            test_func = create_tracking_test_function(test_name, module_name)
            test_ref = TestRef(test_func)
            module_group._children[test_ref.base_name] = test_ref
            register_test_scope(test_name, module_name)
        
        root._children[module_name] = module_group
    
    return root


# ============================================================================
# EXAMPLE FUNCTIONS
# ============================================================================

def example_basic_sequence_document_generation():
    """
    Demonstrate basic sequence document generation.
    
    This example shows how to:
    1. Create a simple test tree
    2. Configure the TestSequencer
    3. Generate a sequence document
    4. Examine the generated document
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Basic Sequence Document Generation")
    print("=" * 70)
    
    # Create a temporary directory for the output
    with tempfile.TemporaryDirectory() as tempdir:
        # Set up the runtime environment
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        
        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, tempdir)
        
        # Store and reset the injection registry
        original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()
        
        try:
            # Create a simple test tree with three tests
            test_tree = create_simple_test_tree(
                "example_module",
                ["test_basic_functionality", "test_another_feature", "test_edge_case"]
            )
            
            # Create the TestSequencer
            sequencer = TestSequencer(
                jobtitle="Basic Example Job",
                root=tempdir,
                includes=["*"],
                excludes=[],
                metafilters=[]
            )
            
            # Set the test tree (normally done by discover())
            sequencer._testtree = test_tree
            
            # Generate the sequence document
            output_file = os.path.join(tempdir, "sequence_document.py")
            print(f"\nGenerating sequence document: {output_file}")
            
            sequencer.generate_testrun_sequence_document(output_file)
            
            # Read and display the generated document
            print("\n" + "-" * 70)
            print("GENERATED SEQUENCE DOCUMENT:")
            print("-" * 70)
            
            with open(output_file, 'r') as f:
                generated_code = f.read()
            
            print(generated_code)
            
            # Verify the document is valid Python
            import ast
            try:
                ast.parse(generated_code)
                print("\n✓ Generated document is valid Python syntax")
            except SyntaxError as e:
                print(f"\n✗ Syntax error in generated document: {e}")
            
            # Verify the document has the expected structure
            print("\nDocument structure verification:")
            print(f"  - Contains 'def session(sequencer):' : {'def session(sequencer):' in generated_code}")
            print(f"  - Contains 'def scope_example_module' : {'def scope_example_module' in generated_code}")
            print(f"  - Contains 'CODE GENERATED' warning  : {'CODE GENERATED' in generated_code}")
            print(f"  - Contains 'ConstraintsCatalog'      : {'ConstraintsCatalog' in generated_code}")
            
        finally:
            # Restore the injection registry
            injection_registry._scope_tree_root = original_scope_tree


def example_multi_module_sequence_document():
    """
    Demonstrate sequence document generation with multiple modules.
    
    This example shows how the sequence document handles tests
    organized across multiple modules.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Multi-Module Sequence Document Generation")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tempdir:
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        
        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, tempdir)
        
        original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()
        
        try:
            # Create a test tree with multiple modules
            modules_config = {
                "tests.unit.test_core": ["test_initialization", "test_cleanup"],
                "tests.unit.test_utils": ["test_helper_function", "test_utility_class"],
                "tests.integration.test_api": ["test_endpoint_get", "test_endpoint_post"]
            }
            
            test_tree = create_multi_module_test_tree(modules_config)
            
            sequencer = TestSequencer(
                jobtitle="Multi-Module Example Job",
                root=tempdir,
                includes=["*"],
                excludes=[],
                metafilters=[]
            )
            sequencer._testtree = test_tree
            
            output_file = os.path.join(tempdir, "multi_module_sequence.py")
            print(f"\nGenerating multi-module sequence document: {output_file}")
            
            sequencer.generate_testrun_sequence_document(output_file)
            
            with open(output_file, 'r') as f:
                generated_code = f.read()
            
            print("\n" + "-" * 70)
            print("GENERATED MULTI-MODULE SEQUENCE DOCUMENT:")
            print("-" * 70)
            print(generated_code)
            
            # Count the scope functions
            scope_count = generated_code.count("def scope_")
            print(f"\n✓ Generated {scope_count} scope functions for {len(modules_config)} modules")
            
        finally:
            injection_registry._scope_tree_root = original_scope_tree


def example_custom_indentation():
    """
    Demonstrate sequence document generation with custom indentation.
    
    The TestSequencer supports custom indentation styles through
    the indent_space parameter.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Custom Indentation")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tempdir:
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        
        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, tempdir)
        
        original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()
        
        try:
            test_tree = create_simple_test_tree("example_module", ["test_one"])
            
            sequencer = TestSequencer(
                jobtitle="Custom Indent Example",
                root=tempdir,
                includes=["*"],
                excludes=[],
                metafilters=[]
            )
            sequencer._testtree = test_tree
            
            # Generate with 2-space indentation
            output_file = os.path.join(tempdir, "two_space_indent.py")
            print(f"\nGenerating with 2-space indentation: {output_file}")
            
            sequencer.generate_testrun_sequence_document(output_file, indent_space="  ")
            
            with open(output_file, 'r') as f:
                generated_code = f.read()
            
            print("\n" + "-" * 70)
            print("GENERATED DOCUMENT WITH 2-SPACE INDENTATION:")
            print("-" * 70)
            # Show just the session function to highlight indentation
            session_start = generated_code.find("def session(")
            session_end = generated_code.find("\ndef scope_")
            if session_end == -1:
                session_end = len(generated_code)
            print(generated_code[session_start:session_end])
            
        finally:
            injection_registry._scope_tree_root = original_scope_tree


def main_debug_sequence_generation_basic():
    """
    Main entry point for the basic sequence generation examples.
    """
    # Establish the application persona if not already done
    if not APP_PERSONA_ESTABLISHED:
        establish_app_persona(
            name="automojo-testbase",
            logger_name="automojo-testbase",
            log_basename="automojo-testbase"
        )
    
    print("\n" + "=" * 70)
    print("SEQUENCE DOCUMENT GENERATION - BASIC EXAMPLES")
    print("=" * 70)
    print("""
This example demonstrates the basic usage of the TestSequencer to generate
sequence documents. A sequence document is a Python module that encodes
the test execution order, parameter provisioning, and scope management.

The sequence document serves as the bridge between test discovery and
test execution, providing a human-readable and debuggable representation
of the test run structure.
""")
    
    example_basic_sequence_document_generation()
    example_multi_module_sequence_document()
    example_custom_indentation()
    
    print("\n" + "=" * 70)
    print("EXAMPLES COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main_debug_sequence_generation_basic()
