"""
.. module:: debug_sequence_generation_validators
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Example demonstrating sequence document generation with validators.

.. moduleauthor:: CodeCraftX

This example demonstrates how the TestSequencer generates sequence documents
that include validator integration. Validators are used to perform additional
validation during test execution, such as checking for memory leaks, verifying
API contracts, or monitoring resource usage.

Usage:
    python -m source.examples.debug_sequence_generation_validators

Requirements:
    - The ccai.testbase package must be installed
    - The example should be run from the repository root
"""

__author__ = "CodeCraftX"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import collections
import os
import tempfile

from ccai.thisapp.persona import APP_PERSONA_ESTABLISHED, establish_app_persona
from ccai.thisapp.wellknown import ThisApplicationSingleton
from ccai.runtime.enumerations import JobType
from ccai.runtime.runtimevariables import RuntimeVariablesDesc
import ccai.runtime.paths as runtime_paths

from ccai.testbase.testgroup import TestGroup
from ccai.testbase.testref import TestRef
from ccai.testbase.injection.injectionregistry import injection_registry
from ccai.testbase.injection.injectionscope import InjectionScope
from ccai.testbase.origins.validatororigin import ValidatorOrigin
from ccai.testbase.sources.sourcebase import SourceBase
from ccai.testbase.sequencing.testsequencer import TestSequencer


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
# VALIDATOR FACTORY FUNCTIONS FOR EXAMPLE
# ============================================================================

def create_memory_validator():
    """
    Factory that creates a memory usage validator.
    
    In a real test suite, this would create a validator that monitors
    memory usage during test execution and reports any leaks.
    """
    print("Creating memory validator...")
    yield "MemoryValidator(threshold_mb=100)"
    print("Memory validator finalized")


def create_api_contract_validator():
    """
    Factory that creates an API contract validator.
    
    This validator would verify that API responses conform to the
    expected schema or contract.
    """
    print("Creating API contract validator...")
    yield "APIContractValidator(schema='openapi.yaml')"
    print("API contract validator finalized")


def create_performance_validator():
    """
    Factory that creates a performance validator.
    
    This validator would measure and report on test execution time
    and resource usage.
    """
    print("Creating performance validator...")
    yield "PerformanceValidator(max_duration_ms=5000)"
    print("Performance validator finalized")


def create_database_integrity_validator():
    """
    Factory that creates a database integrity validator.
    
    This validator would verify that database state is consistent
    before and after test execution.
    """
    print("Creating database integrity validator...")
    yield "DatabaseIntegrityValidator(check_constraints=True)"
    print("Database integrity validator finalized")


# ============================================================================
# TEST FUNCTIONS FOR EXAMPLE
# ============================================================================

def test_with_single_validator():
    """Test that uses a single validator."""
    print("Running test with single validator")


def test_with_multiple_validators():
    """Test that uses multiple validators."""
    print("Running test with multiple validators")


def test_without_validators():
    """Test that does not use any validators."""
    print("Running test without validators")


def test_api_endpoint():
    """Test that validates API contract."""
    print("Testing API endpoint")


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


def add_validator_to_test(test_func, identifier, suffix, factory_func, constraints=None):
    """
    Add a validator origination to the injection registry for a test.
    
    Validators are attached to tests and perform additional validation
    during test execution. They follow a lifecycle:
    1. Construction (via factory function)
    2. Attachment to test scope
    3. Test execution
    4. Finalization (cleanup and reporting)
    
    Args:
        test_func: The test function (used to derive the scope name)
        identifier: Identifier for the validator instance
        suffix: Suffix for the validator attachment (used for naming)
        factory_func: The factory function to create the validator
        constraints: Optional constraints dictionary
        
    Returns:
        ValidatorOrigin: The created validator origin
    """
    scope_name = "{}#{}".format(test_func.__module__, test_func.__name__)
    source = MockSourceBase(factory_func)
    origin = ValidatorOrigin(
        scope_name,
        identifier,
        suffix,
        source,
        implied=False,
        constraints=constraints
    )
    
    injection_registry._scope_tree_root.add_descendent_validator_origination(scope_name, origin)
    
    return origin


def register_test_scope(test_func):
    """Register a test scope in the injection registry without validators."""
    scope_name = "{}#{}".format(test_func.__module__, test_func.__name__)
    injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, None)


# ============================================================================
# EXAMPLE FUNCTIONS
# ============================================================================

def example_single_validator():
    """
    Demonstrate sequence document generation with a single validator.
    
    This example shows how a validator is integrated into the generated
    sequence document, including the try/finally block structure.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Single Validator")
    print("=" * 70)
    print("""
Validators are used to perform additional validation during test execution.
When a test has validators, the generated document includes:

1. Validator factory import at the top of the file
2. A try/finally block wrapping the test execution
3. Validator construction and attachment in the try block
4. Validator finalization in the finally block

This ensures validators are always finalized, even if the test fails.
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
                test_with_single_validator,
                module_name="tests.example.test_validators"
            )
            
            # Add a single validator to the test
            add_validator_to_test(
                test_with_single_validator,
                identifier="memory_validator",
                suffix="memory",
                factory_func=create_memory_validator
            )
            
            sequencer = TestSequencer(
                jobtitle="Single Validator Example",
                root=tempdir,
                includes=["*"],
                excludes=[],
                metafilters=[]
            )
            sequencer._testtree = root
            
            output_file = os.path.join(tempdir, "single_validator.py")
            sequencer.generate_testrun_sequence_document(output_file)
            
            with open(output_file, 'r') as f:
                generated_code = f.read()
            
            print("\n" + "-" * 70)
            print("GENERATED DOCUMENT WITH SINGLE VALIDATOR:")
            print("-" * 70)
            print(generated_code)
            
            print("\n" + "-" * 70)
            print("KEY FEATURES:")
            print("-" * 70)
            print(f"  ✓ Validator factory import: {'create_memory_validator' in generated_code}")
            print(f"  ✓ Try block present: {'try:' in generated_code}")
            print(f"  ✓ Finally block present: {'finally:' in generated_code}")
            print(f"  ✓ Validator attachment: {'attach_to_test' in generated_code}")
            print(f"  ✓ Validator finalization: {'finalize()' in generated_code}")
            
        finally:
            injection_registry._scope_tree_root = original_scope_tree


def example_multiple_validators():
    """
    Demonstrate sequence document generation with multiple validators.
    
    This example shows how multiple validators are handled, including
    the reverse order finalization.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Multiple Validators")
    print("=" * 70)
    print("""
Tests can have multiple validators attached. When multiple validators
are present:

1. All validators are constructed in order
2. All validators are attached to the test scope
3. The test is executed
4. Validators are finalized in REVERSE order of construction

The reverse finalization order ensures proper cleanup when validators
have dependencies on each other.
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
                test_with_multiple_validators,
                module_name="tests.example.test_multi_validators"
            )
            
            # Add multiple validators to the test
            add_validator_to_test(
                test_with_multiple_validators,
                identifier="memory_validator",
                suffix="memory",
                factory_func=create_memory_validator
            )
            add_validator_to_test(
                test_with_multiple_validators,
                identifier="performance_validator",
                suffix="perf",
                factory_func=create_performance_validator
            )
            add_validator_to_test(
                test_with_multiple_validators,
                identifier="db_validator",
                suffix="db",
                factory_func=create_database_integrity_validator
            )
            
            sequencer = TestSequencer(
                jobtitle="Multiple Validators Example",
                root=tempdir,
                includes=["*"],
                excludes=[],
                metafilters=[]
            )
            sequencer._testtree = root
            
            output_file = os.path.join(tempdir, "multiple_validators.py")
            sequencer.generate_testrun_sequence_document(output_file)
            
            with open(output_file, 'r') as f:
                generated_code = f.read()
            
            print("\n" + "-" * 70)
            print("GENERATED DOCUMENT WITH MULTIPLE VALIDATORS:")
            print("-" * 70)
            print(generated_code)
            
            print("\n" + "-" * 70)
            print("KEY FEATURES:")
            print("-" * 70)
            print(f"  ✓ Memory validator import: {'create_memory_validator' in generated_code}")
            print(f"  ✓ Performance validator import: {'create_performance_validator' in generated_code}")
            print(f"  ✓ DB validator import: {'create_database_integrity_validator' in generated_code}")
            print(f"  ✓ Multiple attach_to_test calls: {generated_code.count('attach_to_test') >= 3}")
            print(f"  ✓ Multiple finalize calls: {generated_code.count('finalize()') >= 3}")
            
        finally:
            injection_registry._scope_tree_root = original_scope_tree


def example_test_without_validators():
    """
    Demonstrate sequence document generation for a test without validators.
    
    This example shows the simpler structure when no validators are present.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Test Without Validators")
    print("=" * 70)
    print("""
When a test has no validators, the generated document is simpler:
- No try/finally block
- Direct test function call
- No validator imports

This is the baseline structure for test execution.
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
                test_without_validators,
                module_name="tests.example.test_no_validators"
            )
            
            # Register the test scope without adding validators
            register_test_scope(test_without_validators)
            
            sequencer = TestSequencer(
                jobtitle="No Validators Example",
                root=tempdir,
                includes=["*"],
                excludes=[],
                metafilters=[]
            )
            sequencer._testtree = root
            
            output_file = os.path.join(tempdir, "no_validators.py")
            sequencer.generate_testrun_sequence_document(output_file)
            
            with open(output_file, 'r') as f:
                generated_code = f.read()
            
            print("\n" + "-" * 70)
            print("GENERATED DOCUMENT WITHOUT VALIDATORS:")
            print("-" * 70)
            print(generated_code)
            
            print("\n" + "-" * 70)
            print("KEY FEATURES:")
            print("-" * 70)
            # Check for absence of validator-related code
            has_try_finally = 'try:' in generated_code and 'finally:' in generated_code
            has_attach = 'attach_to_test' in generated_code
            has_finalize = 'finalize()' in generated_code
            
            print(f"  ✓ No try/finally block: {not has_try_finally}")
            print(f"  ✓ No attach_to_test: {not has_attach}")
            print(f"  ✓ No finalize calls: {not has_finalize}")
            print(f"  ✓ Direct test call: {'test_without_validators()' in generated_code}")
            
        finally:
            injection_registry._scope_tree_root = original_scope_tree


def example_validator_lifecycle():
    """
    Demonstrate the validator lifecycle in the generated document.
    
    This example explains the complete validator lifecycle as encoded
    in the sequence document.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Validator Lifecycle")
    print("=" * 70)
    print("""
The validator lifecycle in the generated sequence document:

1. CONSTRUCTION
   - Validator factory is called to create the validator instance
   - Constraints are looked up if the factory requires them
   - Example: memory_validator = create_memory_validator()

2. ATTACHMENT
   - Validator is attached to the test scope
   - The suffix identifies the validator in results
   - Example: memory_validator.attach_to_test(tscope, 'memory')

3. TEST EXECUTION
   - The test function is called
   - Validators may monitor execution or collect data

4. FINALIZATION
   - Validators are finalized in reverse order
   - Cleanup and reporting occurs
   - Example: memory_validator.finalize()

The try/finally structure ensures finalization always occurs.
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
                test_api_endpoint,
                module_name="tests.example.test_api"
            )
            
            # Add an API contract validator
            add_validator_to_test(
                test_api_endpoint,
                identifier="api_validator",
                suffix="contract",
                factory_func=create_api_contract_validator
            )
            
            sequencer = TestSequencer(
                jobtitle="Validator Lifecycle Example",
                root=tempdir,
                includes=["*"],
                excludes=[],
                metafilters=[]
            )
            sequencer._testtree = root
            
            output_file = os.path.join(tempdir, "validator_lifecycle.py")
            sequencer.generate_testrun_sequence_document(output_file)
            
            with open(output_file, 'r') as f:
                generated_code = f.read()
            
            print("\n" + "-" * 70)
            print("GENERATED DOCUMENT SHOWING VALIDATOR LIFECYCLE:")
            print("-" * 70)
            print(generated_code)
            
            # Find and highlight the test scope section
            test_scope_start = generated_code.find("# ================ Test Scope:")
            if test_scope_start != -1:
                print("\n" + "-" * 70)
                print("ANNOTATED LIFECYCLE:")
                print("-" * 70)
                print("""
The generated code follows this pattern:

    try:
        # 1. CONSTRUCTION
        api_validator = create_api_contract_validator()
        
        # 2. ATTACHMENT
        api_validator.attach_to_test(tscope, 'contract')
        
        # 3. TEST EXECUTION
        from tests.example.test_api import test_api_endpoint
        test_api_endpoint()
        
    finally:
        # 4. FINALIZATION
        api_validator.finalize()
""")
            
        finally:
            injection_registry._scope_tree_root = original_scope_tree


def main_debug_sequence_generation_validators():
    """
    Main entry point for the validator examples.
    """
    if not APP_PERSONA_ESTABLISHED:
        establish_app_persona(
            name="codecraftai-testbase",
            logger_name="codecraftai-testbase",
            log_basename="codecraftai-testbase"
        )
    
    print("\n" + "=" * 70)
    print("SEQUENCE DOCUMENT GENERATION - VALIDATOR EXAMPLES")
    print("=" * 70)
    print("""
This example demonstrates how the TestSequencer generates sequence documents
that include validator integration. Validators perform additional validation
during test execution, such as:

- Memory leak detection
- API contract verification
- Performance monitoring
- Database integrity checks

Validators follow a lifecycle: construction, attachment, test execution,
and finalization. The generated document encodes this lifecycle using
try/finally blocks to ensure proper cleanup.
""")
    
    example_single_validator()
    example_multiple_validators()
    example_test_without_validators()
    example_validator_lifecycle()
    
    print("\n" + "=" * 70)
    print("EXAMPLES COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main_debug_sequence_generation_validators()
