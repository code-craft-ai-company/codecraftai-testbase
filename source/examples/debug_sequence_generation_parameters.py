"""
.. module:: debug_sequence_generation_parameters
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Example demonstrating sequence document generation with parameters.

.. moduleauthor:: AutomationX

This example demonstrates how the TestSequencer generates sequence documents
that include parameter provisioning at different scope levels:
- Session-scoped parameters (created once per test run)
- Module-scoped parameters (created once per module)
- Test-local parameters (created for each test instance)

Usage:
    python -m source.examples.debug_sequence_generation_parameters

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
from automojo.testbase.origins.resourceorigin import ResourceOrigin
from automojo.testbase.resourcelifespan import ResourceLifespan
from automojo.testbase.sources.sourcebase import SourceBase
from automojo.testbase.sequencing.testsequencer import TestSequencer


# ============================================================================
# MOCK CLASSES FOR EXAMPLE
# ============================================================================

class MockSourceBase(SourceBase):
    """Mock source for testing purposes."""

    def __init__(self, source_func, resource_type=str):
        super().__init__(source_func, None, resource_type, {})


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
# FACTORY FUNCTIONS FOR EXAMPLE
# ============================================================================

def create_database_connection():
    """
    Session-scoped factory that creates a database connection.
    
    In a real test suite, this would create an actual database connection
    that is shared across all tests in the session.
    """
    print("Creating database connection...")
    yield "DatabaseConnection(host='localhost', port=5432)"
    print("Closing database connection...")


def create_test_user():
    """
    Module-scoped factory that creates a test user.
    
    This factory creates a test user that is shared across all tests
    in a module.
    """
    print("Creating test user...")
    yield "User(name='test_user', role='admin')"
    print("Cleaning up test user...")


def create_request_context():
    """
    Test-local factory that creates a request context.
    
    This factory creates a fresh request context for each test instance,
    ensuring test isolation.
    """
    print("Creating request context...")
    yield "RequestContext(method='GET', path='/api/test')"
    print("Cleaning up request context...")


def create_api_client():
    """
    Another session-scoped factory for API client.
    """
    print("Creating API client...")
    yield "APIClient(base_url='https://api.example.com')"
    print("Closing API client...")


def create_test_data():
    """
    Test-local factory that creates test data.
    """
    print("Creating test data...")
    yield "TestData(items=[1, 2, 3])"
    print("Cleaning up test data...")


# ============================================================================
# TEST FUNCTIONS FOR EXAMPLE
# ============================================================================

def test_with_session_param(db_connection):
    """Test that uses a session-scoped database connection."""
    print(f"Running test with db_connection: {db_connection}")


def test_with_module_param(test_user):
    """Test that uses a module-scoped test user."""
    print(f"Running test with test_user: {test_user}")


def test_with_test_local_param(request_context):
    """Test that uses a test-local request context."""
    print(f"Running test with request_context: {request_context}")


def test_with_mixed_params(db_connection, test_user, request_context):
    """Test that uses parameters from all scope levels."""
    print(f"Running test with db_connection: {db_connection}")
    print(f"Running test with test_user: {test_user}")
    print(f"Running test with request_context: {request_context}")


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


def create_test_tree_with_test_func(test_func, module_name=None):
    """
    Create a test tree with a single test function.
    
    Args:
        test_func: The test function to include
        module_name: Optional module name override
        
    Returns:
        tuple: (root MockTestGroup, module MockTestGroup)
    """
    if module_name is None:
        module_name = test_func.__module__
    
    root = MockTestGroup("root")
    module_group = MockTestGroup(module_name, package="")
    test_ref = TestRef(test_func)
    module_group._children[test_ref.base_name] = test_ref
    root._children[module_name] = module_group
    
    return root, module_group


def add_session_parameter(root, param_name, factory_func, implied=False):
    """
    Add a session-level parameter origination to the root node.
    
    Session-scoped parameters are created once at the start of the test run
    and are available to all tests.
    
    Args:
        root: The root MockTestGroup
        param_name: Name of the parameter
        factory_func: The factory function to use
        implied: Whether the parameter is implied (not explicitly passed)
        
    Returns:
        ResourceOrigin: The created resource origin
    """
    source = MockSourceBase(factory_func)
    origin = ResourceOrigin(
        "<session>",
        param_name,
        ResourceLifespan.Session,
        source,
        implied=implied
    )
    root._mock_scope.parameter_originations[param_name] = origin
    return origin


def add_module_parameter(module_group, param_name, factory_func, implied=False):
    """
    Add a module-level parameter origination to the module node.
    
    Module-scoped parameters are created once per module and are available
    to all tests within that module.
    
    Args:
        module_group: The module MockTestGroup
        param_name: Name of the parameter
        factory_func: The factory function to use
        implied: Whether the parameter is implied
        
    Returns:
        ResourceOrigin: The created resource origin
    """
    source = MockSourceBase(factory_func)
    origin = ResourceOrigin(
        module_group.name,
        param_name,
        ResourceLifespan.Test,
        source,
        implied=implied
    )
    module_group._mock_scope.parameter_originations[param_name] = origin
    return origin


def add_test_local_parameter(test_func, param_name, factory_func, implied=False):
    """
    Add a test-local parameter origination to the injection registry.
    
    Test-local parameters are created fresh for each test instance,
    ensuring test isolation.
    
    Args:
        test_func: The test function
        param_name: Name of the parameter
        factory_func: The factory function to use
        implied: Whether the parameter is implied
        
    Returns:
        ResourceOrigin: The created resource origin
    """
    scope_name = "{}#{}".format(test_func.__module__, test_func.__name__)
    source = MockSourceBase(factory_func)
    origin = ResourceOrigin(
        scope_name,
        param_name,
        ResourceLifespan.Test,
        source,
        implied=implied
    )
    injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, origin)
    return origin


def register_test_scope(test_func):
    """Register a test scope in the injection registry without parameters."""
    scope_name = "{}#{}".format(test_func.__module__, test_func.__name__)
    injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, None)


# ============================================================================
# EXAMPLE FUNCTIONS
# ============================================================================

def example_session_scoped_parameters():
    """
    Demonstrate sequence document generation with session-scoped parameters.
    
    Session-scoped parameters are created once at the start of the test run
    and are passed to all scope functions and tests.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Session-Scoped Parameters")
    print("=" * 70)
    print("""
Session-scoped parameters are created once at the start of the test run.
They are typically used for expensive resources like database connections
or API clients that should be shared across all tests.

In the generated document, you'll see:
- Factory import at the top of the file
- A 'for' loop in the session() function iterating over factory results
- The parameter passed to all child scope functions
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
            # Create test tree with session parameter
            root, module_group = create_test_tree_with_test_func(
                test_with_session_param, 
                module_name="tests.example.test_session"
            )
            add_session_parameter(root, "db_connection", create_database_connection)
            register_test_scope(test_with_session_param)
            
            sequencer = TestSequencer(
                jobtitle="Session Parameter Example",
                root=tempdir,
                includes=["*"],
                excludes=[],
                metafilters=[]
            )
            sequencer._testtree = root
            
            output_file = os.path.join(tempdir, "session_params.py")
            sequencer.generate_testrun_sequence_document(output_file)
            
            with open(output_file, 'r') as f:
                generated_code = f.read()
            
            print("\n" + "-" * 70)
            print("GENERATED DOCUMENT WITH SESSION PARAMETER:")
            print("-" * 70)
            print(generated_code)
            
            # Highlight key features
            print("\n" + "-" * 70)
            print("KEY FEATURES:")
            print("-" * 70)
            print(f"  ✓ Factory import present: {'create_database_connection' in generated_code}")
            print(f"  ✓ Session loop present: {'for db_connection in' in generated_code}")
            print(f"  ✓ Parameter passed to scope: {'sequencer, db_connection' in generated_code}")
            
        finally:
            injection_registry._scope_tree_root = original_scope_tree


def example_module_scoped_parameters():
    """
    Demonstrate sequence document generation with module-scoped parameters.
    
    Module-scoped parameters are created once per module and are available
    to all tests within that module.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Module-Scoped Parameters")
    print("=" * 70)
    print("""
Module-scoped parameters are created once per module. They are useful for
resources that should be shared within a module but isolated between modules.

In the generated document, you'll see:
- Factory import at the top of the file
- A 'for' loop in the scope_*() function iterating over factory results
- The parameter available to all tests in that module
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
            root, module_group = create_test_tree_with_test_func(
                test_with_module_param,
                module_name="tests.example.test_module"
            )
            add_module_parameter(module_group, "test_user", create_test_user)
            register_test_scope(test_with_module_param)
            
            sequencer = TestSequencer(
                jobtitle="Module Parameter Example",
                root=tempdir,
                includes=["*"],
                excludes=[],
                metafilters=[]
            )
            sequencer._testtree = root
            
            output_file = os.path.join(tempdir, "module_params.py")
            sequencer.generate_testrun_sequence_document(output_file)
            
            with open(output_file, 'r') as f:
                generated_code = f.read()
            
            print("\n" + "-" * 70)
            print("GENERATED DOCUMENT WITH MODULE PARAMETER:")
            print("-" * 70)
            print(generated_code)
            
            print("\n" + "-" * 70)
            print("KEY FEATURES:")
            print("-" * 70)
            print(f"  ✓ Factory import present: {'create_test_user' in generated_code}")
            print(f"  ✓ Module loop present: {'for test_user in' in generated_code}")
            
        finally:
            injection_registry._scope_tree_root = original_scope_tree


def example_test_local_parameters():
    """
    Demonstrate sequence document generation with test-local parameters.
    
    Test-local parameters are created fresh for each test instance,
    ensuring complete test isolation.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Test-Local Parameters")
    print("=" * 70)
    print("""
Test-local parameters are created fresh for each test instance. They ensure
complete test isolation and are useful for resources that should not be
shared between tests.

In the generated document, you'll see:
- Factory import at the top of the file
- A test setup context: enter_test_setup_context()
- A 'for' loop within the setup context
- A notables dictionary tracking parameter values
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
            root, module_group = create_test_tree_with_test_func(
                test_with_test_local_param,
                module_name="tests.example.test_local"
            )
            add_test_local_parameter(test_with_test_local_param, "request_context", create_request_context)
            
            sequencer = TestSequencer(
                jobtitle="Test-Local Parameter Example",
                root=tempdir,
                includes=["*"],
                excludes=[],
                metafilters=[]
            )
            sequencer._testtree = root
            
            output_file = os.path.join(tempdir, "test_local_params.py")
            sequencer.generate_testrun_sequence_document(output_file)
            
            with open(output_file, 'r') as f:
                generated_code = f.read()
            
            print("\n" + "-" * 70)
            print("GENERATED DOCUMENT WITH TEST-LOCAL PARAMETER:")
            print("-" * 70)
            print(generated_code)
            
            print("\n" + "-" * 70)
            print("KEY FEATURES:")
            print("-" * 70)
            print(f"  ✓ Factory import present: {'create_request_context' in generated_code}")
            print(f"  ✓ Test setup context: {'enter_test_setup_context' in generated_code}")
            print(f"  ✓ Test-local loop: {'for request_context in' in generated_code}")
            print(f"  ✓ Notables dictionary: {'notables' in generated_code}")
            
        finally:
            injection_registry._scope_tree_root = original_scope_tree


def example_mixed_scope_parameters():
    """
    Demonstrate sequence document generation with parameters from all scopes.
    
    This example shows how parameters from different scope levels are
    combined in a single test.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Mixed Scope Parameters")
    print("=" * 70)
    print("""
Tests can use parameters from multiple scope levels simultaneously.
The generated document shows how these parameters are nested:
- Session parameters in the outermost loop
- Module parameters in the scope function
- Test-local parameters in the test setup context
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
            root, module_group = create_test_tree_with_test_func(
                test_with_mixed_params,
                module_name="tests.example.test_mixed"
            )
            
            # Add parameters at all scope levels
            add_session_parameter(root, "db_connection", create_database_connection)
            add_module_parameter(module_group, "test_user", create_test_user)
            add_test_local_parameter(test_with_mixed_params, "request_context", create_request_context)
            
            sequencer = TestSequencer(
                jobtitle="Mixed Parameters Example",
                root=tempdir,
                includes=["*"],
                excludes=[],
                metafilters=[]
            )
            sequencer._testtree = root
            
            output_file = os.path.join(tempdir, "mixed_params.py")
            sequencer.generate_testrun_sequence_document(output_file)
            
            with open(output_file, 'r') as f:
                generated_code = f.read()
            
            print("\n" + "-" * 70)
            print("GENERATED DOCUMENT WITH MIXED SCOPE PARAMETERS:")
            print("-" * 70)
            print(generated_code)
            
            print("\n" + "-" * 70)
            print("KEY FEATURES:")
            print("-" * 70)
            print(f"  ✓ Session parameter loop: {'for db_connection in' in generated_code}")
            print(f"  ✓ Module parameter loop: {'for test_user in' in generated_code}")
            print(f"  ✓ Test-local parameter loop: {'for request_context in' in generated_code}")
            print(f"  ✓ All parameters in scope call: {'db_connection' in generated_code and 'test_user' in generated_code}")
            
        finally:
            injection_registry._scope_tree_root = original_scope_tree


def main_debug_sequence_generation_parameters():
    """
    Main entry point for the parameter examples.
    """
    if not APP_PERSONA_ESTABLISHED:
        establish_app_persona(
            name="automojo-testbase",
            logger_name="automojo-testbase",
            log_basename="automojo-testbase"
        )
    
    print("\n" + "=" * 70)
    print("SEQUENCE DOCUMENT GENERATION - PARAMETER EXAMPLES")
    print("=" * 70)
    print("""
This example demonstrates how the TestSequencer generates sequence documents
that include parameter provisioning at different scope levels:

1. Session-scoped: Created once per test run, shared by all tests
2. Module-scoped: Created once per module, shared within the module
3. Test-local: Created fresh for each test instance

Parameters are created by factory functions that yield resources. The
sequence document encodes the factory calls and parameter passing.
""")
    
    example_session_scoped_parameters()
    example_module_scoped_parameters()
    example_test_local_parameters()
    example_mixed_scope_parameters()
    
    print("\n" + "=" * 70)
    print("EXAMPLES COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main_debug_sequence_generation_parameters()
