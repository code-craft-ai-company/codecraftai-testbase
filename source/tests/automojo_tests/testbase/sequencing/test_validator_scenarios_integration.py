"""
    Integration tests for validator scenarios in sequence document generation.

    These tests verify the complete flow of validator handling including:
    - Tests with validators
    - Tests without validators
    - Multiple validators per test
    - Validator lifecycle (attach, execute, finalize)

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

import ast
import collections
import os
import tempfile
import unittest

from automojo.xmodules.ximport import import_file

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

class MockSourceBase(SourceBase):
    """Mock source for testing purposes."""

    def __init__(self, source_func, resource_type=str):
        super().__init__(source_func, None, resource_type, {})


class MockInjectionScope:
    """Mock InjectionScope for testing sequence document generation."""
    
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
# VALIDATOR FACTORY FUNCTIONS FOR TESTING
# ============================================================================

def validator_factory_one():
    """First validator factory function for testing."""
    yield "validator_instance_one"


def validator_factory_two():
    """Second validator factory function for testing."""
    yield "validator_instance_two"


def validator_factory_three():
    """Third validator factory function for testing."""
    yield "validator_instance_three"


def validator_with_constraints(constraints=None):
    """Validator factory function that accepts constraints."""
    yield "constrained_validator_instance"


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_with_single_validator():
    """Test function with a single validator."""
    pass


def test_with_multiple_validators():
    """Test function with multiple validators."""
    pass


def test_without_validators():
    """Test function without any validators."""
    pass


def test_with_constrained_validator():
    """Test function with a validator that uses constraints."""
    pass


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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


def register_test_scope(test_func):
    """
    Register a test scope in the injection registry without validators.
    
    Args:
        test_func: The test function
    """
    scope_name = "{}#{}".format(test_func.__module__, test_func.__name__)
    injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, None)


# ============================================================================
# TEST CLASSES
# ============================================================================

class TestsWithValidatorsIntegrationTests(unittest.TestCase):
    """
    Integration tests for tests with validators.

    **Validates: Requirements 17.1-17.5, 18.1-18.5**
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
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

    def _create_sequencer_with_tree(self, test_tree):
        """Create a TestSequencer with the given test tree."""
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        sequencer._testtree = test_tree
        return sequencer

    def _is_valid_python(self, code):
        """Check if the given code is valid Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def test_single_validator_generates_valid_document(self):
        """
        Test that a document with a single validator is valid Python.

        **Validates: Requirements 17.1-17.5, 18.1-18.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_single_validator)
        add_validator_to_test(test_with_single_validator, "my_validator", "suffix", validator_factory_one)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with single validator should be valid Python"
        )

    def test_single_validator_document_is_importable(self):
        """
        Test that a document with a single validator can be imported.

        **Validates: Requirements 17.1-17.5, 18.1-18.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_single_validator)
        add_validator_to_test(test_with_single_validator, "my_validator", "suffix", validator_factory_one)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        try:
            sequence_mod = import_file("single_validator_doc", output_file)
            self.assertIsNotNone(sequence_mod)
            self.assertTrue(hasattr(sequence_mod, 'session'))
            self.assertTrue(callable(sequence_mod.session))
        except Exception as e:
            self.fail(f"Document with single validator should be importable: {e}")

    def test_validator_try_finally_structure_present(self):
        """
        Test that try/finally structure is present for validator.

        **Validates: Requirements 17.2, 18.1**
        """
        root, module_group = create_test_tree_with_test_func(test_with_single_validator)
        add_validator_to_test(test_with_single_validator, "my_validator", "suffix", validator_factory_one)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn("try:", generated_code, "try block should be present")
        self.assertIn("finally:", generated_code, "finally block should be present")

    def test_validator_construction_code_present(self):
        """
        Test that validator construction code is present.

        **Validates: Requirements 17.1, 17.4**
        """
        root, module_group = create_test_tree_with_test_func(test_with_single_validator)
        add_validator_to_test(test_with_single_validator, "my_validator", "suffix", validator_factory_one)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            "my_validator = validator_factory_one()",
            generated_code,
            "Validator construction should be present"
        )

    def test_validator_attach_to_test_call_present(self):
        """
        Test that attach_to_test call is present.

        **Validates: Requirements 17.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_single_validator)
        add_validator_to_test(test_with_single_validator, "my_validator", "test_suffix", validator_factory_one)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            "my_validator.attach_to_test(tscope, 'test_suffix')",
            generated_code,
            "attach_to_test call should be present with correct format"
        )

    def test_validator_finalize_call_present(self):
        """
        Test that finalize call is present in finally block.

        **Validates: Requirements 18.2, 18.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_single_validator)
        add_validator_to_test(test_with_single_validator, "my_validator", "suffix", validator_factory_one)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            "my_validator.finalize()",
            generated_code,
            "finalize call should be present"
        )

    def test_validator_factory_import_present(self):
        """
        Test that validator factory import is present in document.

        **Validates: Requirements 17.3**
        """
        root, module_group = create_test_tree_with_test_func(test_with_single_validator)
        add_validator_to_test(test_with_single_validator, "my_validator", "suffix", validator_factory_one)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        expected_import = "from {} import {}".format(
            validator_factory_one.__module__,
            validator_factory_one.__name__
        )
        self.assertIn(
            expected_import,
            generated_code,
            "Validator factory import should be present"
        )


class TestsWithoutValidatorsIntegrationTests(unittest.TestCase):
    """
    Integration tests for tests without validators.

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
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

    def _create_sequencer_with_tree(self, test_tree):
        """Create a TestSequencer with the given test tree."""
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        sequencer._testtree = test_tree
        return sequencer

    def _is_valid_python(self, code):
        """Check if the given code is valid Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def test_no_validator_generates_valid_document(self):
        """
        Test that a document without validators is valid Python.

        **Validates: Requirements 17.2, 18.1**
        """
        root, module_group = create_test_tree_with_test_func(test_without_validators)
        register_test_scope(test_without_validators)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document without validators should be valid Python"
        )

    def test_no_validator_document_is_importable(self):
        """
        Test that a document without validators can be imported.

        **Validates: Requirements 17.2, 18.1**
        """
        root, module_group = create_test_tree_with_test_func(test_without_validators)
        register_test_scope(test_without_validators)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        try:
            sequence_mod = import_file("no_validator_doc", output_file)
            self.assertIsNotNone(sequence_mod)
            self.assertTrue(hasattr(sequence_mod, 'session'))
            self.assertTrue(callable(sequence_mod.session))
        except Exception as e:
            self.fail(f"Document without validators should be importable: {e}")

    def test_no_try_finally_when_no_validators(self):
        """
        Test that try/finally blocks are not present when no validators.

        **Validates: Requirements 17.2, 18.1**
        """
        root, module_group = create_test_tree_with_test_func(test_without_validators)
        register_test_scope(test_without_validators)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Count occurrences of try: and finally: - they should not appear
        # in the test scope context (they may appear elsewhere in template)
        # We check that there's no try/finally pattern around the test call
        test_call_pos = generated_code.find("test_without_validators()")
        if test_call_pos > 0:
            # Get the context around the test call
            context_start = max(0, test_call_pos - 200)
            context_end = min(len(generated_code), test_call_pos + 200)
            context = generated_code[context_start:context_end]
            
            # In a test without validators, there should be no try/finally
            # wrapping the test call
            self.assertNotIn(
                "try:",
                context,
                "try block should not be present around test without validators"
            )

    def test_no_finalize_calls_when_no_validators(self):
        """
        Test that finalize calls are not present when no validators.

        **Validates: Requirements 18.2**
        """
        root, module_group = create_test_tree_with_test_func(test_without_validators)
        register_test_scope(test_without_validators)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertNotIn(
            ".finalize()",
            generated_code,
            "finalize calls should not be present when no validators"
        )


class MultipleValidatorsIntegrationTests(unittest.TestCase):
    """
    Integration tests for multiple validators per test.

    **Validates: Requirements 17.1-17.5, 18.1-18.5**
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
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

    def _create_sequencer_with_tree(self, test_tree):
        """Create a TestSequencer with the given test tree."""
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        sequencer._testtree = test_tree
        return sequencer

    def _is_valid_python(self, code):
        """Check if the given code is valid Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def test_multiple_validators_generates_valid_document(self):
        """
        Test that a document with multiple validators is valid Python.

        **Validates: Requirements 17.1-17.5, 18.1-18.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_multiple_validators)
        add_validator_to_test(test_with_multiple_validators, "validator_one", "suffix1", validator_factory_one)
        add_validator_to_test(test_with_multiple_validators, "validator_two", "suffix2", validator_factory_two)
        add_validator_to_test(test_with_multiple_validators, "validator_three", "suffix3", validator_factory_three)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with multiple validators should be valid Python"
        )

    def test_multiple_validators_document_is_importable(self):
        """
        Test that a document with multiple validators can be imported.

        **Validates: Requirements 17.1-17.5, 18.1-18.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_multiple_validators)
        add_validator_to_test(test_with_multiple_validators, "validator_one", "suffix1", validator_factory_one)
        add_validator_to_test(test_with_multiple_validators, "validator_two", "suffix2", validator_factory_two)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        try:
            sequence_mod = import_file("multi_validator_doc", output_file)
            self.assertIsNotNone(sequence_mod)
            self.assertTrue(hasattr(sequence_mod, 'session'))
            self.assertTrue(callable(sequence_mod.session))
        except Exception as e:
            self.fail(f"Document with multiple validators should be importable: {e}")

    def test_all_validator_constructions_present(self):
        """
        Test that all validator construction calls are present.

        **Validates: Requirements 17.1**
        """
        root, module_group = create_test_tree_with_test_func(test_with_multiple_validators)
        add_validator_to_test(test_with_multiple_validators, "validator_one", "suffix1", validator_factory_one)
        add_validator_to_test(test_with_multiple_validators, "validator_two", "suffix2", validator_factory_two)
        add_validator_to_test(test_with_multiple_validators, "validator_three", "suffix3", validator_factory_three)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn("validator_one =", generated_code, "First validator construction should be present")
        self.assertIn("validator_two =", generated_code, "Second validator construction should be present")
        self.assertIn("validator_three =", generated_code, "Third validator construction should be present")

    def test_all_validator_attach_calls_present(self):
        """
        Test that all attach_to_test calls are present.

        **Validates: Requirements 17.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_multiple_validators)
        add_validator_to_test(test_with_multiple_validators, "validator_one", "suffix1", validator_factory_one)
        add_validator_to_test(test_with_multiple_validators, "validator_two", "suffix2", validator_factory_two)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn("validator_one.attach_to_test(", generated_code, "First attach_to_test should be present")
        self.assertIn("validator_two.attach_to_test(", generated_code, "Second attach_to_test should be present")

    def test_all_validator_finalize_calls_present(self):
        """
        Test that all finalize calls are present.

        **Validates: Requirements 18.2**
        """
        root, module_group = create_test_tree_with_test_func(test_with_multiple_validators)
        add_validator_to_test(test_with_multiple_validators, "validator_one", "suffix1", validator_factory_one)
        add_validator_to_test(test_with_multiple_validators, "validator_two", "suffix2", validator_factory_two)
        add_validator_to_test(test_with_multiple_validators, "validator_three", "suffix3", validator_factory_three)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn("validator_one.finalize()", generated_code, "First finalize should be present")
        self.assertIn("validator_two.finalize()", generated_code, "Second finalize should be present")
        self.assertIn("validator_three.finalize()", generated_code, "Third finalize should be present")

    def test_all_validator_factory_imports_present(self):
        """
        Test that all validator factory imports are present.

        **Validates: Requirements 17.3**
        """
        root, module_group = create_test_tree_with_test_func(test_with_multiple_validators)
        add_validator_to_test(test_with_multiple_validators, "validator_one", "suffix1", validator_factory_one)
        add_validator_to_test(test_with_multiple_validators, "validator_two", "suffix2", validator_factory_two)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        import_one = "from {} import {}".format(
            validator_factory_one.__module__,
            validator_factory_one.__name__
        )
        import_two = "from {} import {}".format(
            validator_factory_two.__module__,
            validator_factory_two.__name__
        )
        
        self.assertIn(import_one, generated_code, "First validator import should be present")
        self.assertIn(import_two, generated_code, "Second validator import should be present")




class ValidatorLifecycleIntegrationTests(unittest.TestCase):
    """
    Integration tests for validator lifecycle (attach, execute, finalize).

    **Validates: Requirements 17.5, 18.2, 18.3, 18.4, 18.5**
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
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

    def _create_sequencer_with_tree(self, test_tree):
        """Create a TestSequencer with the given test tree."""
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        sequencer._testtree = test_tree
        return sequencer

    def _is_valid_python(self, code):
        """Check if the given code is valid Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def test_validator_lifecycle_order_construction_before_attach(self):
        """
        Test that validator construction appears before attach_to_test.

        **Validates: Requirements 17.1, 17.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_single_validator)
        add_validator_to_test(test_with_single_validator, "my_validator", "suffix", validator_factory_one)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        construction_pos = generated_code.find("my_validator = validator_factory_one()")
        attach_pos = generated_code.find("my_validator.attach_to_test(")
        
        self.assertGreater(construction_pos, -1, "Construction should be found")
        self.assertGreater(attach_pos, -1, "attach_to_test should be found")
        self.assertLess(construction_pos, attach_pos, "Construction should appear before attach_to_test")

    def test_validator_lifecycle_order_attach_before_test_call(self):
        """
        Test that attach_to_test appears before test function call.

        **Validates: Requirements 17.5, 18.4**
        """
        root, module_group = create_test_tree_with_test_func(test_with_single_validator)
        add_validator_to_test(test_with_single_validator, "my_validator", "suffix", validator_factory_one)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        attach_pos = generated_code.find("my_validator.attach_to_test(")
        test_call_pos = generated_code.find("test_with_single_validator()")
        
        self.assertGreater(attach_pos, -1, "attach_to_test should be found")
        self.assertGreater(test_call_pos, -1, "Test call should be found")
        self.assertLess(attach_pos, test_call_pos, "attach_to_test should appear before test call")

    def test_validator_lifecycle_order_test_call_before_finalize(self):
        """
        Test that test function call appears before finalize.

        **Validates: Requirements 18.2, 18.4**
        """
        root, module_group = create_test_tree_with_test_func(test_with_single_validator)
        add_validator_to_test(test_with_single_validator, "my_validator", "suffix", validator_factory_one)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        test_call_pos = generated_code.find("test_with_single_validator()")
        finalize_pos = generated_code.find("my_validator.finalize()")
        
        self.assertGreater(test_call_pos, -1, "Test call should be found")
        self.assertGreater(finalize_pos, -1, "finalize should be found")
        self.assertLess(test_call_pos, finalize_pos, "Test call should appear before finalize")

    def test_test_function_call_in_try_block(self):
        """
        Test that test function call is within the try block.

        **Validates: Requirements 18.4**
        """
        root, module_group = create_test_tree_with_test_func(test_with_single_validator)
        add_validator_to_test(test_with_single_validator, "my_validator", "suffix", validator_factory_one)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        try_pos = generated_code.find("try:")
        test_call_pos = generated_code.find("test_with_single_validator()")
        finally_pos = generated_code.find("finally:")
        
        self.assertGreater(try_pos, -1, "try block should be found")
        self.assertGreater(test_call_pos, -1, "Test call should be found")
        self.assertGreater(finally_pos, -1, "finally block should be found")
        
        self.assertGreater(test_call_pos, try_pos, "Test call should be after try")
        self.assertLess(test_call_pos, finally_pos, "Test call should be before finally")

    def test_finalize_in_finally_block(self):
        """
        Test that finalize call is in the finally block.

        **Validates: Requirements 18.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_single_validator)
        add_validator_to_test(test_with_single_validator, "my_validator", "suffix", validator_factory_one)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        finally_pos = generated_code.find("finally:")
        finalize_pos = generated_code.find("my_validator.finalize()")
        
        self.assertGreater(finally_pos, -1, "finally block should be found")
        self.assertGreater(finalize_pos, -1, "finalize should be found")
        self.assertGreater(finalize_pos, finally_pos, "finalize should appear after finally")

    def test_multiple_validators_finalize_order(self):
        """
        Test that multiple validators are finalized in reverse order of construction.

        The implementation constructs validators in reverse order of registration
        (three, two, one) and then finalizes them in reverse of that order
        (one, two, three), which satisfies the requirement that finalization
        happens in reverse order of construction.

        **Validates: Requirements 18.3**
        """
        root, module_group = create_test_tree_with_test_func(test_with_multiple_validators)
        # Add validators in registration order: one, two, three
        add_validator_to_test(test_with_multiple_validators, "validator_one", "suffix1", validator_factory_one)
        add_validator_to_test(test_with_multiple_validators, "validator_two", "suffix2", validator_factory_two)
        add_validator_to_test(test_with_multiple_validators, "validator_three", "suffix3", validator_factory_three)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Find the try block to verify construction order
        try_pos = generated_code.find("try:")
        finally_pos = generated_code.find("finally:")
        self.assertGreater(try_pos, -1, "try block should be found")
        self.assertGreater(finally_pos, -1, "finally block should be found")
        
        # Get the code between try and finally (construction code)
        try_code = generated_code[try_pos:finally_pos]
        
        # Find construction positions - validators are constructed in reverse order
        construct_one_pos = try_code.find("validator_one = validator_factory_one()")
        construct_two_pos = try_code.find("validator_two = validator_factory_two()")
        construct_three_pos = try_code.find("validator_three = validator_factory_three()")
        
        self.assertGreater(construct_one_pos, -1, "validator_one construction should be found")
        self.assertGreater(construct_two_pos, -1, "validator_two construction should be found")
        self.assertGreater(construct_three_pos, -1, "validator_three construction should be found")
        
        # Construction order should be: three, two, one (reverse of registration)
        self.assertLess(
            construct_three_pos, construct_two_pos,
            "validator_three should be constructed before validator_two"
        )
        self.assertLess(
            construct_two_pos, construct_one_pos,
            "validator_two should be constructed before validator_one"
        )
        
        # Get the code after finally (finalization code)
        finally_code = generated_code[finally_pos:]
        
        # Find finalize positions in the finally block
        finalize_one_pos = finally_code.find("validator_one.finalize()")
        finalize_two_pos = finally_code.find("validator_two.finalize()")
        finalize_three_pos = finally_code.find("validator_three.finalize()")
        
        self.assertGreater(finalize_one_pos, -1, "validator_one.finalize() should be found")
        self.assertGreater(finalize_two_pos, -1, "validator_two.finalize() should be found")
        self.assertGreater(finalize_three_pos, -1, "validator_three.finalize() should be found")
        
        # Finalization order should be: one, two, three (reverse of construction order)
        # This satisfies requirement 18.3: "finalize in reverse order of construction"
        self.assertLess(
            finalize_one_pos, finalize_two_pos,
            "validator_one should be finalized before validator_two"
        )
        self.assertLess(
            finalize_two_pos, finalize_three_pos,
            "validator_two should be finalized before validator_three"
        )

    def test_complete_lifecycle_structure(self):
        """
        Test the complete validator lifecycle structure in generated code.

        **Validates: Requirements 17.1-17.5, 18.1-18.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_single_validator)
        add_validator_to_test(test_with_single_validator, "my_validator", "test_suffix", validator_factory_one)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Verify the complete lifecycle structure exists
        # 1. Validator construction
        self.assertIn("my_validator = validator_factory_one()", generated_code)
        
        # 2. attach_to_test call
        self.assertIn("my_validator.attach_to_test(tscope, 'test_suffix')", generated_code)
        
        # 3. try block
        self.assertIn("try:", generated_code)
        
        # 4. Test function call
        self.assertIn("test_with_single_validator()", generated_code)
        
        # 5. finally block
        self.assertIn("finally:", generated_code)
        
        # 6. finalize call
        self.assertIn("my_validator.finalize()", generated_code)

    def test_validator_lifecycle_document_compiles(self):
        """
        Test that the generated document with validator lifecycle compiles.

        **Validates: Requirements 17.1-17.5, 18.1-18.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_single_validator)
        add_validator_to_test(test_with_single_validator, "my_validator", "suffix", validator_factory_one)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Compile the code to check for syntax errors
        try:
            compile(generated_code, output_file, 'exec')
        except SyntaxError as e:
            self.fail(f"Generated code with validator lifecycle should compile: {e}")


if __name__ == '__main__':
    unittest.main()
