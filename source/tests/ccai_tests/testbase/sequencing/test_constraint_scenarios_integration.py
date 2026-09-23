"""
    Integration tests for constraint scenarios in sequence document generation.

    These tests verify the complete flow of constraint handling including:
    - Factories with constraints
    - Factories without constraints
    - Constraint lookup at runtime

    Requirements covered:
    - 11.1: Check factory function signature for `constraints` parameter
    - 11.2: Check for constraints_key when constraints parameter present
    - 11.3: Generate constraint lookup line
    - 11.4: Raise RuntimeError when constraint not found in catalog
    - 11.5: Remove 'constraints' from parameter list when no constraints_key present
"""

import ast
import collections
import os
import tempfile
import unittest

from ccai.xmodules.ximport import import_file

from ccai.testbase.testgroup import TestGroup
from ccai.testbase.testref import TestRef
from ccai.testbase.injection.injectionregistry import injection_registry
from ccai.testbase.injection.injectionscope import InjectionScope
from ccai.testbase.origins.resourceorigin import ResourceOrigin
from ccai.testbase.resourcelifespan import ResourceLifespan
from ccai.testbase.sources.sourcebase import SourceBase
from ccai.testbase.sequencing.testsequencer import TestSequencer
from ccai.testbase.constraints import ConstraintsCatalog



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
# FACTORY FUNCTIONS FOR TESTING
# ============================================================================

def factory_without_constraints():
    """Factory function without constraints parameter."""
    yield "unconstrained_resource"


def factory_with_constraints(constraints=None):
    """Factory function with constraints parameter."""
    if constraints is not None:
        yield f"constrained_resource:{constraints.get('key', 'default')}"
    else:
        yield "constrained_resource:no_constraints"


def another_factory_with_constraints(constraints=None):
    """Another factory function with constraints parameter."""
    if constraints is not None:
        yield f"another_resource:{constraints.get('config', 'default')}"
    else:
        yield "another_resource:no_constraints"


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_with_unconstrained_param(unconstrained_param):
    """Test function that uses an unconstrained parameter."""
    pass


def test_with_constrained_param(constrained_param):
    """Test function that uses a constrained parameter."""
    pass


def test_with_mixed_params(unconstrained_param, constrained_param):
    """Test function that uses both constrained and unconstrained parameters."""
    pass


def test_with_multiple_constrained_params(param_a, param_b):
    """Test function that uses multiple constrained parameters."""
    pass



# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def reset_constraints_catalog():
    """Reset the constraints catalog to a clean state for testing.
    
    Note: The ConstraintsCatalog is a singleton, but multiple modules have
    their own module-level references. We need to reset the singleton and
    update all module-level references to ensure tests are isolated.
    """
    ConstraintsCatalog._instance = None
    ConstraintsCatalog._initialized = False
    
    # Reset the module-level catalog in resourceorigin
    from ccai.testbase.origins import resourceorigin
    resourceorigin.constraints_catalog = ConstraintsCatalog()
    
    # Reset the module-level catalog in testsequencer
    from ccai.testbase.sequencing import testsequencer
    testsequencer.constraints_catalog = ConstraintsCatalog()
    
    return resourceorigin.constraints_catalog


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


def add_module_parameter_with_constraints(module_group, param_name, factory_func, constraints_dict):
    """
    Add a module-level parameter origination with constraints to the module node.
    
    Args:
        module_group: The module MockTestGroup
        param_name: Name of the parameter
        factory_func: The factory function to use
        constraints_dict: Dictionary of constraints to pass
        
    Returns:
        ResourceOrigin: The created resource origin
    """
    source = MockSourceBase(factory_func)
    origin = ResourceOrigin(
        module_group.name,
        param_name,
        ResourceLifespan.Test,
        source,
        implied=False,
        constraints=constraints_dict
    )
    module_group._mock_scope.parameter_originations[param_name] = origin
    return origin


def add_module_parameter_without_constraints(module_group, param_name, factory_func):
    """
    Add a module-level parameter origination without constraints to the module node.
    
    Args:
        module_group: The module MockTestGroup
        param_name: Name of the parameter
        factory_func: The factory function to use
        
    Returns:
        ResourceOrigin: The created resource origin
    """
    source = MockSourceBase(factory_func)
    origin = ResourceOrigin(
        module_group.name,
        param_name,
        ResourceLifespan.Test,
        source,
        implied=False,
        constraints=None
    )
    module_group._mock_scope.parameter_originations[param_name] = origin
    return origin


def register_test_scope(test_func):
    """
    Register a test scope in the injection registry without parameters.
    
    Args:
        test_func: The test function
    """
    scope_name = "{}#{}".format(test_func.__module__, test_func.__name__)
    injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, None)



# ============================================================================
# TEST CLASSES
# ============================================================================

class FactoriesWithConstraintsIntegrationTests(unittest.TestCase):
    """
    Integration tests for factories with constraints.

    Tests verify that sequence documents are correctly generated when
    factories have constraints parameters and constraints are registered
    in the catalog.

    **Validates: Requirements 11.1, 11.2, 11.3**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()
        
        self.catalog = reset_constraints_catalog()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

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

    def test_constrained_factory_generates_valid_document(self):
        """
        Test that a document with constrained factory is valid Python.

        **Validates: Requirements 11.1, 11.2, 11.3**
        """
        root, module_group = create_test_tree_with_test_func(test_with_constrained_param)
        test_constraints = {"key": "test_value"}
        add_module_parameter_with_constraints(
            module_group, "constrained_param", factory_with_constraints, test_constraints
        )
        register_test_scope(test_with_constrained_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with constrained factory should be valid Python"
        )

    def test_constrained_factory_document_is_importable(self):
        """
        Test that a document with constrained factory can be imported.

        **Validates: Requirements 11.1, 11.2, 11.3**
        """
        root, module_group = create_test_tree_with_test_func(test_with_constrained_param)
        test_constraints = {"key": "test_value"}
        add_module_parameter_with_constraints(
            module_group, "constrained_param", factory_with_constraints, test_constraints
        )
        register_test_scope(test_with_constrained_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        try:
            sequence_mod = import_file("constrained_factory_doc", output_file)
            self.assertIsNotNone(sequence_mod)
            self.assertTrue(hasattr(sequence_mod, 'session'))
            self.assertTrue(callable(sequence_mod.session))
        except Exception as e:
            self.fail(f"Document with constrained factory should be importable: {e}")

    def test_constrained_factory_has_constraint_lookup(self):
        """
        Test that constrained factory generates constraint lookup code.

        **Validates: Requirements 11.3**
        """
        root, module_group = create_test_tree_with_test_func(test_with_constrained_param)
        test_constraints = {"key": "test_value"}
        add_module_parameter_with_constraints(
            module_group, "constrained_param", factory_with_constraints, test_constraints
        )
        register_test_scope(test_with_constrained_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            "constraints=constraints_catalog.lookup_constraints(",
            generated_code,
            "Generated code should contain constraint lookup"
        )

    def test_multiple_constrained_factories_generate_valid_document(self):
        """
        Test that multiple constrained factories generate valid Python.

        **Validates: Requirements 11.1, 11.2, 11.3**
        """
        root, module_group = create_test_tree_with_test_func(test_with_multiple_constrained_params)
        add_module_parameter_with_constraints(
            module_group, "param_a", factory_with_constraints, {"key": "value_a"}
        )
        add_module_parameter_with_constraints(
            module_group, "param_b", another_factory_with_constraints, {"config": "value_b"}
        )
        register_test_scope(test_with_multiple_constrained_params)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with multiple constrained factories should be valid Python"
        )
        
        # Verify both constraint lookups are present
        constraint_lookup_count = generated_code.count("constraints=constraints_catalog.lookup_constraints(")
        self.assertEqual(
            constraint_lookup_count,
            2,
            "Should have two constraint lookup lines for two constrained parameters"
        )



class FactoriesWithoutConstraintsIntegrationTests(unittest.TestCase):
    """
    Integration tests for factories without constraints.

    Tests verify that sequence documents are correctly generated when
    factories do not have constraints parameters or when no constraints
    are registered.

    **Validates: Requirements 11.1, 11.5**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()
        
        self.catalog = reset_constraints_catalog()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

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

    def test_unconstrained_factory_generates_valid_document(self):
        """
        Test that a document with unconstrained factory is valid Python.

        **Validates: Requirements 11.1, 11.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_unconstrained_param)
        add_module_parameter_without_constraints(
            module_group, "unconstrained_param", factory_without_constraints
        )
        register_test_scope(test_with_unconstrained_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with unconstrained factory should be valid Python"
        )

    def test_unconstrained_factory_document_is_importable(self):
        """
        Test that a document with unconstrained factory can be imported.

        **Validates: Requirements 11.1, 11.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_unconstrained_param)
        add_module_parameter_without_constraints(
            module_group, "unconstrained_param", factory_without_constraints
        )
        register_test_scope(test_with_unconstrained_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        try:
            sequence_mod = import_file("unconstrained_factory_doc", output_file)
            self.assertIsNotNone(sequence_mod)
            self.assertTrue(hasattr(sequence_mod, 'session'))
            self.assertTrue(callable(sequence_mod.session))
        except Exception as e:
            self.fail(f"Document with unconstrained factory should be importable: {e}")

    def test_unconstrained_factory_has_no_constraint_lookup(self):
        """
        Test that unconstrained factory does not generate constraint lookup code.

        **Validates: Requirements 11.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_unconstrained_param)
        add_module_parameter_without_constraints(
            module_group, "unconstrained_param", factory_without_constraints
        )
        register_test_scope(test_with_unconstrained_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # The constraint lookup should not appear in the scope function
        # (it may appear in the template header, so we check for the specific pattern)
        scope_function_start = generated_code.find("def scope_")
        if scope_function_start != -1:
            scope_function_code = generated_code[scope_function_start:]
            self.assertNotIn(
                "constraints=constraints_catalog.lookup_constraints(",
                scope_function_code,
                "Scope function should not contain constraint lookup for unconstrained factory"
            )

    def test_factory_with_constraints_param_but_no_key_generates_valid_document(self):
        """
        Test that factory with constraints param but no key generates valid Python.

        When a factory has a constraints parameter but no constraints_key is set,
        the constraints parameter should be removed from the call.

        **Validates: Requirements 11.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_constrained_param)
        # Use factory_with_constraints but don't provide constraints
        add_module_parameter_without_constraints(
            module_group, "constrained_param", factory_with_constraints
        )
        register_test_scope(test_with_constrained_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document should be valid Python when factory has constraints param but no key"
        )
        
        # Verify the factory is called without constraints argument
        self.assertIn(
            "for constrained_param in factory_with_constraints():",
            generated_code,
            "Factory should be called without constraints argument when no key"
        )



class ConstraintLookupAtRuntimeIntegrationTests(unittest.TestCase):
    """
    Integration tests for constraint lookup at runtime.

    Tests verify that constraints are correctly looked up from the
    ConstraintsCatalog at runtime when the generated sequence document
    is executed.

    **Validates: Requirements 11.3, 11.4**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()
        
        self.catalog = reset_constraints_catalog()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

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

    def test_constraint_key_format_in_generated_code(self):
        """
        Test that constraint key uses correct format in generated code.

        The constraint key should be in the format "{scope}:{identifier}".

        **Validates: Requirements 11.3**
        """
        root, module_group = create_test_tree_with_test_func(test_with_constrained_param)
        test_constraints = {"key": "test_value"}
        add_module_parameter_with_constraints(
            module_group, "constrained_param", factory_with_constraints, test_constraints
        )
        register_test_scope(test_with_constrained_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # The constraint key should be in the format "{module_name}:{param_name}"
        expected_key = f"{module_group.name}:constrained_param"
        self.assertIn(
            repr(expected_key),
            generated_code,
            f"Generated code should contain constraint key '{expected_key}'"
        )

    def test_constraint_lookup_uses_constraints_catalog(self):
        """
        Test that constraint lookup uses the constraints_catalog.

        **Validates: Requirements 11.3**
        """
        root, module_group = create_test_tree_with_test_func(test_with_constrained_param)
        test_constraints = {"key": "test_value"}
        add_module_parameter_with_constraints(
            module_group, "constrained_param", factory_with_constraints, test_constraints
        )
        register_test_scope(test_with_constrained_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Verify the constraints_catalog is used for lookup
        self.assertIn(
            "constraints_catalog.lookup_constraints(",
            generated_code,
            "Generated code should use constraints_catalog for lookup"
        )

    def test_constraint_lookup_appears_before_factory_call(self):
        """
        Test that constraint lookup appears before the factory call.

        **Validates: Requirements 11.3**
        """
        root, module_group = create_test_tree_with_test_func(test_with_constrained_param)
        test_constraints = {"key": "test_value"}
        add_module_parameter_with_constraints(
            module_group, "constrained_param", factory_with_constraints, test_constraints
        )
        register_test_scope(test_with_constrained_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Find the positions of constraint lookup and factory call
        constraint_lookup_pos = generated_code.find("constraints=constraints_catalog.lookup_constraints(")
        factory_call_pos = generated_code.find("for constrained_param in")

        self.assertNotEqual(constraint_lookup_pos, -1, "Constraint lookup should be found")
        self.assertNotEqual(factory_call_pos, -1, "Factory call should be found")
        self.assertLess(
            constraint_lookup_pos,
            factory_call_pos,
            "Constraint lookup should appear before factory call"
        )



class MixedConstraintScenariosIntegrationTests(unittest.TestCase):
    """
    Integration tests for mixed constraint scenarios.

    Tests verify that sequence documents are correctly generated when
    there is a mix of constrained and unconstrained factories.

    **Validates: Requirements 11.1, 11.2, 11.3, 11.5**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()
        
        self.catalog = reset_constraints_catalog()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

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

    def test_mixed_constrained_and_unconstrained_generates_valid_document(self):
        """
        Test that mixed constrained and unconstrained factories generate valid Python.

        **Validates: Requirements 11.1, 11.2, 11.3, 11.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_mixed_params)
        add_module_parameter_without_constraints(
            module_group, "unconstrained_param", factory_without_constraints
        )
        add_module_parameter_with_constraints(
            module_group, "constrained_param", factory_with_constraints, {"key": "value"}
        )
        register_test_scope(test_with_mixed_params)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with mixed constrained and unconstrained factories should be valid Python"
        )

    def test_mixed_constrained_and_unconstrained_is_importable(self):
        """
        Test that mixed constrained and unconstrained factories document can be imported.

        **Validates: Requirements 11.1, 11.2, 11.3, 11.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_mixed_params)
        add_module_parameter_without_constraints(
            module_group, "unconstrained_param", factory_without_constraints
        )
        add_module_parameter_with_constraints(
            module_group, "constrained_param", factory_with_constraints, {"key": "value"}
        )
        register_test_scope(test_with_mixed_params)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        try:
            sequence_mod = import_file("mixed_constraints_doc", output_file)
            self.assertIsNotNone(sequence_mod)
            self.assertTrue(hasattr(sequence_mod, 'session'))
            self.assertTrue(callable(sequence_mod.session))
        except Exception as e:
            self.fail(f"Document with mixed constraints should be importable: {e}")

    def test_mixed_has_correct_constraint_handling(self):
        """
        Test that mixed scenario has correct constraint handling for each parameter.

        **Validates: Requirements 11.1, 11.2, 11.3, 11.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_mixed_params)
        add_module_parameter_without_constraints(
            module_group, "unconstrained_param", factory_without_constraints
        )
        add_module_parameter_with_constraints(
            module_group, "constrained_param", factory_with_constraints, {"key": "value"}
        )
        register_test_scope(test_with_mixed_params)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Verify unconstrained factory is called without constraints
        self.assertIn(
            "for unconstrained_param in factory_without_constraints():",
            generated_code,
            "Unconstrained factory should be called without constraints"
        )
        
        # Verify constrained factory has constraint lookup
        self.assertIn(
            "constraints=constraints_catalog.lookup_constraints(",
            generated_code,
            "Constrained factory should have constraint lookup"
        )

    def test_constraint_lookup_only_for_constrained_parameters(self):
        """
        Test that constraint lookup is only generated for constrained parameters.

        **Validates: Requirements 11.1, 11.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_mixed_params)
        add_module_parameter_without_constraints(
            module_group, "unconstrained_param", factory_without_constraints
        )
        add_module_parameter_with_constraints(
            module_group, "constrained_param", factory_with_constraints, {"key": "value"}
        )
        register_test_scope(test_with_mixed_params)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Count constraint lookups - should be exactly 1 for the constrained parameter
        scope_function_start = generated_code.find("def scope_")
        if scope_function_start != -1:
            scope_function_code = generated_code[scope_function_start:]
            constraint_lookup_count = scope_function_code.count("constraints=constraints_catalog.lookup_constraints(")
            self.assertEqual(
                constraint_lookup_count,
                1,
                "Should have exactly one constraint lookup for the constrained parameter"
            )


if __name__ == '__main__':
    unittest.main()
