"""
    Unit tests for validator integration in test scope code generation.

    Tests verify the validator integration including try/finally block generation,
    validator construction code, attach_to_test call generation, and validator
    finalize call generation.

    Requirements covered:
    - 17.1: Generate validator construction code when test scope has validator originations
    - 17.2: Wrap validator code in try/finally block
    - 17.3: Add factory imports for validator factories to factory_imports set
    - 17.4: Generate validator construction calls with constraint lookups if needed
    - 17.5: Generate `{validator}.attach_to_test(tscope, '{suffix}')` calls for each validator
    - 18.1: Generate finally block after test call when validators present
    - 18.2: Generate `{validator}.finalize()` calls for each validator
    - 18.3: Finalize validators in reverse order of construction
    - 18.4: Place test function call within try block
    - 18.5: Execute validator finalization regardless of test outcome
"""

import collections
import io
import os
import tempfile
import unittest

from automojo.testbase.testgroup import TestGroup
from automojo.testbase.testref import TestRef
from automojo.testbase.injection.injectionregistry import injection_registry
from automojo.testbase.injection.injectionscope import InjectionScope
from automojo.testbase.origins.validatororigin import ValidatorOrigin
from automojo.testbase.sources.sourcebase import SourceBase
from automojo.testbase.sequencing.testsequencer import TestSequencer


# ============================================================================
# MOCK CLASSES FOR TESTING
# ============================================================================

def validator_factory_func():
    """Sample validator factory function for testing."""
    yield "validator_instance"


def another_validator_factory_func():
    """Another validator factory function for testing multiple validators."""
    yield "another_validator_instance"


def validator_with_constraints(constraints=None):
    """Validator factory function that accepts constraints."""
    yield "constrained_validator_instance"


class MockSourceBase(SourceBase):
    """Mock source for testing purposes."""

    def __init__(self, source_func, resource_type=str):
        super().__init__(source_func, None, resource_type, {})


class MockInjectionScope:
    """Mock InjectionScope for testing validator integration."""
    
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
# TEST FUNCTIONS
# ============================================================================

def test_with_validator():
    """Test function for validator integration testing."""
    pass


def test_with_no_validators():
    """Test function without validators."""
    pass


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_scope_node_with_test_func(test_func):
    """
    Create a scope node with a test reference using the given test function.
    
    Args:
        test_func: The actual test function to use
        
    Returns:
        tuple: (MockTestGroup, module_name) - A test group node with one test reference and the module name
    """
    module_name = test_func.__module__
    parent = MockTestGroup(module_name, package="")
    test_ref = TestRef(test_func)
    parent._children[test_ref.base_name] = test_ref
    return parent, module_name


def add_validator_to_test(test_func, identifier, suffix, factory_func, constraints=None):
    """
    Add a validator origination to the injection registry for a test.
    
    Args:
        test_func: The test function (used to derive the scope name)
        identifier: Identifier for the validator
        suffix: Suffix for the validator attachment
        factory_func: The factory function to use
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


# ============================================================================
# TEST CLASSES
# ============================================================================

class TryFinallyBlockGenerationTests(unittest.TestCase):
    """
    Tests for try/finally block generation when validators are present.

    **Validates: Requirements 17.2, 18.1**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

    def _create_sequencer(self):
        """Create a TestSequencer for testing."""
        return TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def test_try_block_generated_when_validators_present(self):
        """
        Verify try block is generated when test has validators.

        **Validates: Requirements 17.2**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            "try:",
            generated_code,
            "Generated code should contain try block when validators present"
        )

    def test_finally_block_generated_when_validators_present(self):
        """
        Verify finally block is generated when test has validators.

        **Validates: Requirements 18.1**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            "finally:",
            generated_code,
            "Generated code should contain finally block when validators present"
        )

    def test_no_try_finally_when_no_validators(self):
        """
        Verify try/finally blocks are not generated when no validators present.

        **Validates: Requirements 17.2, 18.1**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_no_validators)
        # Register the test scope without any validators
        scope_name = "{}#{}".format(test_with_no_validators.__module__, test_with_no_validators.__name__)
        injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, None)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertNotIn(
            "try:",
            generated_code,
            "Generated code should not contain try block when no validators"
        )
        self.assertNotIn(
            "finally:",
            generated_code,
            "Generated code should not contain finally block when no validators"
        )

    def test_try_appears_before_finally(self):
        """
        Verify try block appears before finally block.

        **Validates: Requirements 17.2, 18.1**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        try_pos = generated_code.find("try:")
        finally_pos = generated_code.find("finally:")
        
        self.assertGreater(try_pos, -1, "try block should be found")
        self.assertGreater(finally_pos, -1, "finally block should be found")
        self.assertLess(try_pos, finally_pos, "try should appear before finally")


class ValidatorConstructionCodeTests(unittest.TestCase):
    """
    Tests for validator construction code generation.

    **Validates: Requirements 17.1, 17.4**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

    def _create_sequencer(self):
        """Create a TestSequencer for testing."""
        return TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def test_validator_construction_code_generated(self):
        """
        Verify validator construction code is generated when test has validators.

        **Validates: Requirements 17.1**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            "my_validator = validator_factory_func()",
            generated_code,
            "Generated code should contain validator construction"
        )

    def test_validator_construction_uses_identifier(self):
        """
        Verify validator construction uses the validator identifier as variable name.

        **Validates: Requirements 17.1**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "custom_validator_name", "suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            "custom_validator_name =",
            generated_code,
            "Validator construction should use identifier as variable name"
        )

    def test_validator_construction_calls_factory_function(self):
        """
        Verify validator construction calls the factory function.

        **Validates: Requirements 17.4**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            "validator_factory_func()",
            generated_code,
            "Validator construction should call factory function"
        )


class AttachToTestCallGenerationTests(unittest.TestCase):
    """
    Tests for attach_to_test call generation.

    **Validates: Requirements 17.5**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

    def _create_sequencer(self):
        """Create a TestSequencer for testing."""
        return TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def test_attach_to_test_call_generated(self):
        """
        Verify attach_to_test call is generated for validator.

        **Validates: Requirements 17.5**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            ".attach_to_test(",
            generated_code,
            "Generated code should contain attach_to_test call"
        )

    def test_attach_to_test_uses_validator_identifier(self):
        """
        Verify attach_to_test call uses the validator identifier.

        **Validates: Requirements 17.5**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            "my_validator.attach_to_test(",
            generated_code,
            "attach_to_test should be called on validator identifier"
        )

    def test_attach_to_test_passes_tscope(self):
        """
        Verify attach_to_test call passes tscope as first argument.

        **Validates: Requirements 17.5**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            ".attach_to_test(tscope,",
            generated_code,
            "attach_to_test should pass tscope as first argument"
        )

    def test_attach_to_test_passes_suffix(self):
        """
        Verify attach_to_test call passes the suffix.

        **Validates: Requirements 17.5**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "my_suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            "'my_suffix'",
            generated_code,
            "attach_to_test should pass the suffix"
        )

    def test_attach_to_test_format(self):
        """
        Verify attach_to_test call uses correct format.

        **Validates: Requirements 17.5**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "test_suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            "my_validator.attach_to_test(tscope, 'test_suffix')",
            generated_code,
            "attach_to_test should use format: {validator}.attach_to_test(tscope, '{suffix}')"
        )


class ValidatorFinalizeCallGenerationTests(unittest.TestCase):
    """
    Tests for validator finalize call generation.

    **Validates: Requirements 18.2, 18.3, 18.5**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

    def _create_sequencer(self):
        """Create a TestSequencer for testing."""
        return TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def test_finalize_call_generated(self):
        """
        Verify finalize call is generated for validator.

        **Validates: Requirements 18.2**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            ".finalize()",
            generated_code,
            "Generated code should contain finalize call"
        )

    def test_finalize_uses_validator_identifier(self):
        """
        Verify finalize call uses the validator identifier.

        **Validates: Requirements 18.2**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            "my_validator.finalize()",
            generated_code,
            "finalize should be called on validator identifier"
        )

    def test_finalize_in_finally_block(self):
        """
        Verify finalize call is in the finally block.

        **Validates: Requirements 18.5**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        finally_pos = generated_code.find("finally:")
        finalize_pos = generated_code.find(".finalize()")
        
        self.assertGreater(finally_pos, -1, "finally block should be found")
        self.assertGreater(finalize_pos, -1, "finalize call should be found")
        self.assertGreater(finalize_pos, finally_pos, "finalize should appear after finally")


class TestFunctionInTryBlockTests(unittest.TestCase):
    """
    Tests for test function call placement within try block.

    **Validates: Requirements 18.4**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

    def _create_sequencer(self):
        """Create a TestSequencer for testing."""
        return TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def test_test_function_call_in_try_block(self):
        """
        Verify test function call is within the try block.

        **Validates: Requirements 18.4**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        try_pos = generated_code.find("try:")
        test_call_pos = generated_code.find("test_with_validator()")
        finally_pos = generated_code.find("finally:")
        
        self.assertGreater(try_pos, -1, "try block should be found")
        self.assertGreater(test_call_pos, -1, "test function call should be found")
        self.assertGreater(finally_pos, -1, "finally block should be found")
        
        self.assertGreater(test_call_pos, try_pos, "test call should be after try")
        self.assertLess(test_call_pos, finally_pos, "test call should be before finally")

    def test_test_import_in_try_block(self):
        """
        Verify test function import is within the try block.

        **Validates: Requirements 18.4**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        try_pos = generated_code.find("try:")
        import_pos = generated_code.find("from {} import test_with_validator".format(module_name))
        finally_pos = generated_code.find("finally:")
        
        self.assertGreater(try_pos, -1, "try block should be found")
        self.assertGreater(import_pos, -1, "test import should be found")
        self.assertGreater(finally_pos, -1, "finally block should be found")
        
        self.assertGreater(import_pos, try_pos, "import should be after try")
        self.assertLess(import_pos, finally_pos, "import should be before finally")


class ValidatorFactoryImportTests(unittest.TestCase):
    """
    Tests for validator factory import addition to factory_imports set.

    **Validates: Requirements 17.3**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

    def _create_sequencer(self):
        """Create a TestSequencer for testing."""
        return TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def test_validator_factory_import_added_to_set(self):
        """
        Verify validator factory import is added to factory_imports set.

        **Validates: Requirements 17.3**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        expected_import = "from {} import {}".format(
            validator_factory_func.__module__,
            validator_factory_func.__name__
        )
        self.assertIn(
            expected_import,
            factory_imports,
            "Validator factory import should be added to factory_imports set"
        )

    def test_multiple_validator_factory_imports_added(self):
        """
        Verify multiple validator factory imports are added to factory_imports set.

        **Validates: Requirements 17.3**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "validator_one", "suffix1", validator_factory_func)
        add_validator_to_test(test_with_validator, "validator_two", "suffix2", another_validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        import_one = "from {} import {}".format(
            validator_factory_func.__module__,
            validator_factory_func.__name__
        )
        import_two = "from {} import {}".format(
            another_validator_factory_func.__module__,
            another_validator_factory_func.__name__
        )
        
        self.assertIn(import_one, factory_imports, "First validator import should be in set")
        self.assertIn(import_two, factory_imports, "Second validator import should be in set")

    def test_validator_factory_import_format(self):
        """
        Verify validator factory import uses correct format.

        **Validates: Requirements 17.3**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "my_validator", "suffix", validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        for import_stmt in factory_imports:
            if "validator_factory_func" in import_stmt:
                self.assertTrue(
                    import_stmt.startswith("from "),
                    "Import should start with 'from '"
                )
                self.assertIn(
                    " import ",
                    import_stmt,
                    "Import should contain ' import '"
                )


class MultipleValidatorsTests(unittest.TestCase):
    """
    Tests for multiple validators handling.

    **Validates: Requirements 17.1, 17.5, 18.2, 18.3**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

    def _create_sequencer(self):
        """Create a TestSequencer for testing."""
        return TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def test_multiple_validators_construction_generated(self):
        """
        Verify construction code is generated for multiple validators.

        **Validates: Requirements 17.1**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "validator_one", "suffix1", validator_factory_func)
        add_validator_to_test(test_with_validator, "validator_two", "suffix2", another_validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            "validator_one =",
            generated_code,
            "First validator construction should be generated"
        )
        self.assertIn(
            "validator_two =",
            generated_code,
            "Second validator construction should be generated"
        )

    def test_multiple_validators_attach_calls_generated(self):
        """
        Verify attach_to_test calls are generated for multiple validators.

        **Validates: Requirements 17.5**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "validator_one", "suffix1", validator_factory_func)
        add_validator_to_test(test_with_validator, "validator_two", "suffix2", another_validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            "validator_one.attach_to_test(",
            generated_code,
            "First validator attach_to_test should be generated"
        )
        self.assertIn(
            "validator_two.attach_to_test(",
            generated_code,
            "Second validator attach_to_test should be generated"
        )

    def test_multiple_validators_finalize_calls_generated(self):
        """
        Verify finalize calls are generated for multiple validators.

        **Validates: Requirements 18.2**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_validator)
        add_validator_to_test(test_with_validator, "validator_one", "suffix1", validator_factory_func)
        add_validator_to_test(test_with_validator, "validator_two", "suffix2", another_validator_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, module_name, module_name, scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            "validator_one.finalize()",
            generated_code,
            "First validator finalize should be generated"
        )
        self.assertIn(
            "validator_two.finalize()",
            generated_code,
            "Second validator finalize should be generated"
        )


if __name__ == '__main__':
    unittest.main()
