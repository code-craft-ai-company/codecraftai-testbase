"""
.. module:: debug_sequence_generation_debugger
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Example demonstrating sequence document generation with debugger breakpoints.

.. moduleauthor:: AutomationX

This example demonstrates how the TestSequencer generates sequence documents
that include debugger breakpoint integration. When debugging is configured,
the generated document includes breakpoint code at specified locations.

Usage:
    python -m source.examples.debug_sequence_generation_debugger

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
from unittest.mock import patch

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
from automojo.testbase.breakpoints import WELLKNOWN_BREAKPOINTS
from automojo.xmodules.debugging import DEBUGGER


# ============================================================================
# MOCK CLASSES FOR EXAMPLE
# ============================================================================

class MockInjectionScope:
    """Mock InjectionScope for demonstrating sequence document generation."""
    
    def __init__(self):
        self.parameter_originations = collections.OrderedDict()
        self.validator_originations = collections.OrderedDict()


class MockTestGroup(TestGroup):
    """Mock TestGroup that returns a mock injection scope."""
    
    def __init__(self, name, package=None):
        super().__init__(name, package)
        self._mock_scope = MockInjectionScope()
    
    def get_resource_scope(self):
        return self._mock_scope


# ============================================================================
# TEST FUNCTIONS FOR EXAMPLE
# ============================================================================

def test_with_debugging():
    """Test function that can be debugged."""
    print("Running test with debugging enabled")


def test_another_function():
    """Another test function for debugging."""
    print("Running another test function")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_tracking_test_function(name, module_name):
    """Create a test function with the specified name and module."""
    def test_func():
        print(f"Executing {name}")
    test_func.__name__ = name
    test_func.__module__ = module_name
    return test_func


def register_test_scope(test_name, module_name):
    """Register a test scope in the injection registry."""
    scope_name = "{}#{}".format(module_name, test_name)
    injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, None)


def create_simple_test_tree(module_name, test_names):
    """
    Create a simple test tree with one module containing the specified tests.
    
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


# ============================================================================
# EXAMPLE FUNCTIONS
# ============================================================================

def example_no_debugger_configured():
    """
    Demonstrate sequence document generation without debugger configuration.
    
    This is the baseline case where no debugger is configured.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: No Debugger Configured")
    print("=" * 70)
    print("""
When no debugger is configured (the default), the generated sequence
document does not include any breakpoint code. This is the normal
production mode.

The runtime variables that control debugging are:
- AM_DEBUG_DEBUGGER: The debugger to use (None, PDB, DEBUGPY)
- AM_DEBUG_BREAKPOINTS: List of breakpoint locations to enable
""")
    
    with tempfile.TemporaryDirectory() as tempdir:
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        
        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, tempdir)
        
        original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()
        
        try:
            test_tree = create_simple_test_tree(
                "tests.example.test_debug",
                ["test_with_debugging", "test_another_function"]
            )
            
            sequencer = TestSequencer(
                jobtitle="No Debugger Example",
                root=tempdir,
                includes=["*"],
                excludes=[],
                metafilters=[]
            )
            sequencer._testtree = test_tree
            
            output_file = os.path.join(tempdir, "no_debugger.py")
            sequencer.generate_testrun_sequence_document(output_file)
            
            with open(output_file, 'r') as f:
                generated_code = f.read()
            
            print("\n" + "-" * 70)
            print("GENERATED DOCUMENT WITHOUT DEBUGGER:")
            print("-" * 70)
            print(generated_code)
            
            print("\n" + "-" * 70)
            print("KEY FEATURES:")
            print("-" * 70)
            has_breakpoint = 'breakpoint()' in generated_code or 'pdb.set_trace()' in generated_code
            has_debugpy = 'debugpy' in generated_code
            print(f"  ✓ No breakpoint code: {not has_breakpoint}")
            print(f"  ✓ No debugpy references: {not has_debugpy}")
            
        finally:
            injection_registry._scope_tree_root = original_scope_tree


def example_pdb_debugger_testrun_start():
    """
    Demonstrate sequence document generation with PDB debugger at TESTRUN_START.
    
    This example shows how breakpoint code is inserted when PDB debugging
    is configured with the TESTRUN_START breakpoint.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: PDB Debugger at TESTRUN_START")
    print("=" * 70)
    print("""
When PDB debugging is configured with the TESTRUN_START breakpoint,
the generated document includes breakpoint code at the start of the
session() function.

This allows you to:
- Inspect the sequencer state before any tests run
- Step through the test execution flow
- Debug test discovery issues

The breakpoint code is inserted after the docstring and before the
session scope context.
""")
    
    with tempfile.TemporaryDirectory() as tempdir:
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        
        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, tempdir)
        
        original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()
        
        try:
            test_tree = create_simple_test_tree(
                "tests.example.test_debug",
                ["test_with_debugging"]
            )
            
            sequencer = TestSequencer(
                jobtitle="PDB Debugger Example",
                root=tempdir,
                includes=["*"],
                excludes=[],
                metafilters=[]
            )
            sequencer._testtree = test_tree
            
            output_file = os.path.join(tempdir, "pdb_debugger.py")
            
            # Patch the runtime variables to enable PDB debugging
            with patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_DEBUGGER', DEBUGGER.PDB):
                with patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_BREAKPOINTS', [WELLKNOWN_BREAKPOINTS.TESTRUN_START]):
                    sequencer.generate_testrun_sequence_document(output_file)
            
            with open(output_file, 'r') as f:
                generated_code = f.read()
            
            print("\n" + "-" * 70)
            print("GENERATED DOCUMENT WITH PDB DEBUGGER:")
            print("-" * 70)
            print(generated_code)
            
            print("\n" + "-" * 70)
            print("KEY FEATURES:")
            print("-" * 70)
            has_pdb_import = 'import pdb' in generated_code
            has_set_trace = 'pdb.set_trace()' in generated_code
            has_breakpoint = 'breakpoint()' in generated_code
            
            print(f"  ✓ PDB import present: {has_pdb_import}")
            print(f"  ✓ pdb.set_trace() call: {has_set_trace}")
            print(f"  ✓ Or breakpoint() call: {has_breakpoint}")
            
            # Show where the breakpoint is inserted
            if has_set_trace or has_breakpoint:
                print("\n  Breakpoint location: After session() docstring, before scope context")
            
        finally:
            injection_registry._scope_tree_root = original_scope_tree


def example_debugpy_debugger():
    """
    Demonstrate sequence document generation with debugpy debugger.
    
    This example shows how breakpoint code is inserted when debugpy
    (VS Code debugger) is configured.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Debugpy (VS Code) Debugger")
    print("=" * 70)
    print("""
When debugpy is configured, the generated document includes code to
enable remote debugging with VS Code or other debugpy-compatible IDEs.

Debugpy allows you to:
- Set breakpoints in VS Code
- Inspect variables in the VS Code debugger
- Step through code with full IDE support
- Debug tests running in containers or remote environments

The debugpy breakpoint code includes:
- Import of the debugpy module
- Configuration for listening on a port
- Wait for debugger attachment (optional)
""")
    
    with tempfile.TemporaryDirectory() as tempdir:
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        
        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, tempdir)
        
        original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()
        
        try:
            test_tree = create_simple_test_tree(
                "tests.example.test_debug",
                ["test_with_debugging"]
            )
            
            sequencer = TestSequencer(
                jobtitle="Debugpy Example",
                root=tempdir,
                includes=["*"],
                excludes=[],
                metafilters=[]
            )
            sequencer._testtree = test_tree
            
            output_file = os.path.join(tempdir, "debugpy_debugger.py")
            
            # Patch the runtime variables to enable debugpy debugging
            with patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_DEBUGGER', DEBUGGER.DEBUGPY):
                with patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_BREAKPOINTS', [WELLKNOWN_BREAKPOINTS.TESTRUN_START]):
                    sequencer.generate_testrun_sequence_document(output_file)
            
            with open(output_file, 'r') as f:
                generated_code = f.read()
            
            print("\n" + "-" * 70)
            print("GENERATED DOCUMENT WITH DEBUGPY:")
            print("-" * 70)
            print(generated_code)
            
            print("\n" + "-" * 70)
            print("KEY FEATURES:")
            print("-" * 70)
            has_debugpy_import = 'import debugpy' in generated_code
            has_debugpy_listen = 'debugpy.listen' in generated_code
            has_debugpy_wait = 'debugpy.wait_for_client' in generated_code
            has_debugpy_breakpoint = 'debugpy.breakpoint' in generated_code
            
            print(f"  ✓ Debugpy import: {has_debugpy_import}")
            print(f"  ✓ Debugpy listen: {has_debugpy_listen}")
            print(f"  ✓ Wait for client: {has_debugpy_wait}")
            print(f"  ✓ Debugpy breakpoint: {has_debugpy_breakpoint}")
            
        finally:
            injection_registry._scope_tree_root = original_scope_tree


def example_breakpoint_locations():
    """
    Explain the available breakpoint locations.
    
    This example documents the well-known breakpoint locations that
    can be configured.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Breakpoint Locations")
    print("=" * 70)
    print("""
The TestBase framework supports several well-known breakpoint locations
that can be configured via the AM_DEBUG_BREAKPOINTS runtime variable.

Available breakpoint locations:

1. TESTRUN_START
   - Location: Start of the session() function
   - Purpose: Debug test run initialization
   - Use case: Inspect sequencer state before any tests run

2. (Future) MODULE_SCOPE_ENTRY
   - Location: Start of each scope_*() function
   - Purpose: Debug module-level setup
   - Use case: Inspect module state before tests in that module

3. (Future) TEST_SCOPE_ENTRY
   - Location: Start of each test scope block
   - Purpose: Debug individual test setup
   - Use case: Inspect test parameters and validators

4. (Future) TEST_COMPLETION
   - Location: After each test completes
   - Purpose: Debug test results
   - Use case: Inspect test outcome and state

To configure breakpoints, set the runtime variables:
- AM_DEBUG_DEBUGGER: DEBUGGER.PDB or DEBUGGER.DEBUGPY
- AM_DEBUG_BREAKPOINTS: List of WELLKNOWN_BREAKPOINTS values
""")
    
    print("\n" + "-" * 70)
    print("WELLKNOWN_BREAKPOINTS VALUES:")
    print("-" * 70)
    print(f"  TESTRUN_START = {WELLKNOWN_BREAKPOINTS.TESTRUN_START}")
    
    print("\n" + "-" * 70)
    print("DEBUGGER VALUES:")
    print("-" * 70)
    print(f"  PDB = {DEBUGGER.PDB}")
    print(f"  DEBUGPY = {DEBUGGER.DEBUGPY}")


def example_debugging_workflow():
    """
    Demonstrate a typical debugging workflow.
    
    This example shows how to use the debugger integration in practice.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Debugging Workflow")
    print("=" * 70)
    print("""
TYPICAL DEBUGGING WORKFLOW:

1. CONFIGURE DEBUGGING
   Set environment variables or use command-line options:
   
   # For PDB debugging
   export AM_DEBUG_DEBUGGER=pdb
   export AM_DEBUG_BREAKPOINTS=TESTRUN_START
   
   # Or for debugpy (VS Code)
   export AM_DEBUG_DEBUGGER=debugpy
   export AM_DEBUG_BREAKPOINTS=TESTRUN_START

2. RUN TESTS
   Run your test suite as normal:
   
   testbase run --include "tests.example@*"

3. DEBUG
   - For PDB: The debugger will stop at the breakpoint
   - For debugpy: Attach VS Code to the running process

4. INSPECT AND STEP
   - Inspect variables: sequencer, test_tree, etc.
   - Step through code to understand execution flow
   - Set additional breakpoints as needed

5. CONTINUE OR QUIT
   - Continue execution to the next breakpoint
   - Or quit the debugger to stop the test run

TIPS:
- Use TESTRUN_START to debug test discovery issues
- Use debugpy for complex debugging with IDE support
- The generated sequence document is human-readable for manual inspection
""")


def main_debug_sequence_generation_debugger():
    """
    Main entry point for the debugger examples.
    """
    if not APP_PERSONA_ESTABLISHED:
        establish_app_persona(
            name="automojo-testbase",
            logger_name="automojo-testbase",
            log_basename="automojo-testbase"
        )
    
    print("\n" + "=" * 70)
    print("SEQUENCE DOCUMENT GENERATION - DEBUGGER EXAMPLES")
    print("=" * 70)
    print("""
This example demonstrates how the TestSequencer generates sequence documents
that include debugger breakpoint integration. When debugging is configured,
the generated document includes breakpoint code at specified locations.

Supported debuggers:
- PDB: Python's built-in debugger
- Debugpy: VS Code's Python debugger (supports remote debugging)

Breakpoint locations:
- TESTRUN_START: At the start of the test run
- (Future) Additional locations for module and test scope entry
""")
    
    example_no_debugger_configured()
    example_pdb_debugger_testrun_start()
    example_debugpy_debugger()
    example_breakpoint_locations()
    example_debugging_workflow()
    
    print("\n" + "=" * 70)
    print("EXAMPLES COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main_debug_sequence_generation_debugger()
