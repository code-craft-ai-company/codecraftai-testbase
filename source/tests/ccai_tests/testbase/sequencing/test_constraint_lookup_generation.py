"""
    Unit tests for constraint lookup generation in sequence document generation.

    Tests verify the constraint lookup generation including checking factory
    function signature for constraints parameter, checking for constraints_key,
    generating constraint lookup line, raising RuntimeError when constraint
    not found, and removing constraints from parameter list when no key.

    Requirements covered:
    - 11.1: Check factory function signature for `constraints` parameter
    - 11.2: Check for constraints_key when constraints parameter present
    - 11.3: Generate constraint lookup line: `constraints=constraints_catalog.lookup_constraints({key})`
    - 11.4: Raise RuntimeError when constraint not found in catalog
    - 11.5: Remove 'constraints' from parameter list when no constraints_key present
"""

import collections
import io
import os
import tempfile
import typing
import unittest

from ccai.testbase.testgroup import TestGroup
from ccai.testbase.injection.injectionregistry import injection_registry
from ccai.testbase.injection.injectionscope import InjectionScope
from ccai.testbase.origins.resourceorigin import ResourceOrigin
from ccai.testbase.resourcelifespan import ResourceLifespan
from ccai.testbase.sources.sourcebase import SourceBase
from ccai.testbase.sequencing.testsequencer import TestSequencer
from ccai.testbase.constraints import ConstraintsCatalog, ConstraintsOrigin


# ============================================================================
# MOCK CLASSES FOR TESTING
# ============================================================================

def factory_without_constraints():
    """Factory function without constraints parameter."""
    yield "resource_value"


def factory_with_constraints(constraints=None):
    """Factory function with constraints parameter."""
    yield constraints


def another_factory_with_constraints(constraints=None):
    """Another factory function with constraints parameter."""
    yield constraints


class MockSourceBase(SourceBase):
    """Mock source for testing purposes."""

    def __init__(self, source_func, resource_type=str):
        super().__init__(source_func, None, resource_type, {})


class MockInjectionScope:
    """Mock InjectionScope for testing scope method generation."""
    
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


def create_scope_node(name, package=None):
    """
    Create a MockTestGroup node for testing scope method generation.
    
    Args:
        name: Name of the scope/module
        package: Optional package path
        
    Returns:
        MockTestGroup: A test group node with mock injection scope
    """
    return MockTestGroup(name, package=package)


def add_parameter_with_constraints(scope_node, param_name, factory_func, constraints_dict):
    """
    Add a parameter origination with constraints to the scope node.
    
    Args:
        scope_node: The MockTestGroup to add the parameter to
        param_name: Name of the parameter
        factory_func: The factory function to use
        constraints_dict: Dictionary of constraints to pass
        
    Returns:
        ResourceOrigin: The created resource origin
    """
    source = MockSourceBase(factory_func)
    origin = ResourceOrigin(
        scope_node.name,
        param_name,
        ResourceLifespan.Test,
        source,
        implied=False,
        constraints=constraints_dict
    )
    scope_node._mock_scope.parameter_originations[param_name] = origin
    return origin


def add_parameter_without_constraints(scope_node, param_name, factory_func):
    """
    Add a parameter origination without constraints to the scope node.
    
    Args:
        scope_node: The MockTestGroup to add the parameter to
        param_name: Name of the parameter
        factory_func: The factory function to use
        
    Returns:
        ResourceOrigin: The created resource origin
    """
    source = MockSourceBase(factory_func)
    origin = ResourceOrigin(
        scope_node.name,
        param_name,
        ResourceLifespan.Test,
        source,
        implied=False,
        constraints=None
    )
    scope_node._mock_scope.parameter_originations[param_name] = origin
    return origin


# ============================================================================
# TEST CLASSES
# ============================================================================

class ConstraintLookupLineGenerationTests(unittest.TestCase):
    """
    Tests for constraint lookup line generation.

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

    def _create_sequencer(self):
        """Create a TestSequencer for testing."""
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        return sequencer

    def test_constraint_lookup_line_generated_when_constraints_present(self):
        """
        Verify constraint lookup line is generated when factory has constraints parameter
        and constraints_key is present.

        **Validates: Requirements 11.1, 11.2, 11.3**
        """
        scope_node = create_scope_node("test_module")
        test_constraints = {"key1": "value1", "key2": 42}
        add_parameter_with_constraints(
            scope_node, "constrained_param", factory_with_constraints, test_constraints
        )
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, "test_module", "test_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            "constraints=constraints_catalog.lookup_constraints(",
            generated_code,
            "Generated code should contain constraint lookup line"
        )

    def test_constraint_lookup_uses_correct_key_format(self):
        """
        Verify constraint lookup uses the correct key format.

        **Validates: Requirements 11.3**
        """
        scope_node = create_scope_node("test_module")
        test_constraints = {"timeout": 30}
        add_parameter_with_constraints(
            scope_node, "my_param", factory_with_constraints, test_constraints
        )
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, "test_module", "test_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        expected_key = "test_module:my_param"
        self.assertIn(
            repr(expected_key),
            generated_code,
            "Constraint lookup should use the correct key format"
        )

    def test_constraint_lookup_line_properly_indented(self):
        """
        Verify constraint lookup line is properly indented.

        **Validates: Requirements 11.3**
        """
        scope_node = create_scope_node("test_module")
        test_constraints = {"setting": "value"}
        add_parameter_with_constraints(
            scope_node, "param", factory_with_constraints, test_constraints
        )
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, "test_module", "test_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        lines = generated_code.split(os.linesep)
        
        constraint_line = None
        for line in lines:
            if "constraints=constraints_catalog.lookup_constraints(" in line:
                constraint_line = line
                break
        
        self.assertIsNotNone(constraint_line, "Constraint lookup line should be found")
        self.assertTrue(
            constraint_line.startswith(indent_space * 2),
            "Constraint lookup line should be properly indented"
        )

    def test_constraint_lookup_appears_before_for_loop(self):
        """
        Verify constraint lookup line appears before the for loop.

        **Validates: Requirements 11.3**
        """
        scope_node = create_scope_node("test_module")
        test_constraints = {"config": "test"}
        add_parameter_with_constraints(
            scope_node, "param", factory_with_constraints, test_constraints
        )
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, "test_module", "test_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        lines = generated_code.split(os.linesep)
        
        constraint_index = None
        for_loop_index = None
        
        for i, line in enumerate(lines):
            if "constraints=constraints_catalog.lookup_constraints(" in line:
                constraint_index = i
            if "for param in" in line:
                for_loop_index = i
        
        self.assertIsNotNone(constraint_index, "Constraint lookup line should be found")
        self.assertIsNotNone(for_loop_index, "For loop should be found")
        self.assertLess(
            constraint_index,
            for_loop_index,
            "Constraint lookup should appear before the for loop"
        )


class ConstraintNotFoundRuntimeErrorTests(unittest.TestCase):
    """
    Tests for RuntimeError when constraint not found in catalog.

    **Validates: Requirements 11.4**
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

    def _create_sequencer(self):
        """Create a TestSequencer for testing."""
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        return sequencer

    def test_runtime_error_raised_when_constraint_not_found(self):
        """
        Verify RuntimeError is raised when constraint is not found in catalog.

        **Validates: Requirements 11.4**
        """
        scope_node = create_scope_node("test_module")
        
        source = MockSourceBase(factory_with_constraints)
        origin = ResourceOrigin(
            scope_node.name,
            "missing_constraint_param",
            ResourceLifespan.Test,
            source,
            implied=False,
            constraints=None
        )
        origin._constraints_key = "nonexistent:key"
        scope_node._mock_scope.parameter_originations["missing_constraint_param"] = origin
        
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        with self.assertRaises(RuntimeError) as context:
            sequencer._generate_scope_method(
                output_buffer, "test_module", "test_module", scope_node,
                scope_call_args, factory_imports, constraint_imports, indent_space
            )
        
        self.assertIn(
            "Constraint required but not found",
            str(context.exception),
            "RuntimeError message should indicate constraint not found"
        )

    def test_runtime_error_includes_constraints_key(self):
        """
        Verify RuntimeError message includes the constraints_key.

        **Validates: Requirements 11.4**
        """
        scope_node = create_scope_node("test_module")
        
        source = MockSourceBase(factory_with_constraints)
        origin = ResourceOrigin(
            scope_node.name,
            "param_with_bad_key",
            ResourceLifespan.Test,
            source,
            implied=False,
            constraints=None
        )
        origin._constraints_key = "bad_scope:bad_identifier"
        scope_node._mock_scope.parameter_originations["param_with_bad_key"] = origin
        
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        with self.assertRaises(RuntimeError) as context:
            sequencer._generate_scope_method(
                output_buffer, "test_module", "test_module", scope_node,
                scope_call_args, factory_imports, constraint_imports, indent_space
            )
        
        self.assertIn(
            "bad_scope:bad_identifier",
            str(context.exception),
            "RuntimeError message should include the constraints_key"
        )


class ConstraintsParameterRemovalTests(unittest.TestCase):
    """
    Tests for constraints parameter removal when no constraints_key present.

    **Validates: Requirements 11.5**
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

    def _create_sequencer(self):
        """Create a TestSequencer for testing."""
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        return sequencer

    def test_constraints_parameter_removed_when_no_key(self):
        """
        Verify constraints parameter is removed from factory call when no constraints_key.

        **Validates: Requirements 11.5**
        """
        scope_node = create_scope_node("test_module")
        add_parameter_without_constraints(
            scope_node, "unconstrained_param", factory_with_constraints
        )
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, "test_module", "test_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertNotIn(
            "constraints=constraints_catalog.lookup_constraints(",
            generated_code,
            "Generated code should not contain constraint lookup when no constraints_key"
        )

    def test_factory_call_without_constraints_argument(self):
        """
        Verify factory function call does not include constraints argument when no key.

        **Validates: Requirements 11.5**
        """
        scope_node = create_scope_node("test_module")
        add_parameter_without_constraints(
            scope_node, "param", factory_with_constraints
        )
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, "test_module", "test_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            "for param in factory_with_constraints():",
            generated_code,
            "Factory call should not include constraints argument when no key"
        )

    def test_no_constraint_lookup_for_factory_without_constraints_param(self):
        """
        Verify no constraint lookup is generated for factory without constraints parameter.

        **Validates: Requirements 11.1, 11.5**
        """
        scope_node = create_scope_node("test_module")
        add_parameter_without_constraints(
            scope_node, "simple_param", factory_without_constraints
        )
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, "test_module", "test_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertNotIn(
            "constraints_catalog",
            generated_code,
            "Generated code should not reference constraints_catalog for factory without constraints param"
        )


class MixedConstraintParameterTests(unittest.TestCase):
    """
    Tests for mixed scenarios with constrained and unconstrained parameters.

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

    def _create_sequencer(self):
        """Create a TestSequencer for testing."""
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        return sequencer

    def test_mixed_constrained_and_unconstrained_parameters(self):
        """
        Verify correct handling of mixed constrained and unconstrained parameters.

        **Validates: Requirements 11.1, 11.2, 11.3, 11.5**
        """
        scope_node = create_scope_node("test_module")
        
        add_parameter_without_constraints(
            scope_node, "unconstrained", factory_without_constraints
        )
        add_parameter_with_constraints(
            scope_node, "constrained", factory_with_constraints, {"key": "value"}
        )
        
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, "test_module", "test_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            "for unconstrained in factory_without_constraints():",
            generated_code,
            "Unconstrained parameter should have simple factory call"
        )
        
        self.assertIn(
            "constraints=constraints_catalog.lookup_constraints(",
            generated_code,
            "Constrained parameter should have constraint lookup"
        )

    def test_multiple_constrained_parameters(self):
        """
        Verify correct handling of multiple constrained parameters.

        **Validates: Requirements 11.1, 11.2, 11.3**
        """
        scope_node = create_scope_node("test_module")
        
        add_parameter_with_constraints(
            scope_node, "param_a", factory_with_constraints, {"config_a": "value_a"}
        )
        add_parameter_with_constraints(
            scope_node, "param_b", another_factory_with_constraints, {"config_b": "value_b"}
        )
        
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, "test_module", "test_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        constraint_lookup_count = generated_code.count("constraints=constraints_catalog.lookup_constraints(")
        self.assertEqual(
            constraint_lookup_count,
            2,
            "Should have two constraint lookup lines for two constrained parameters"
        )


if __name__ == '__main__':
    unittest.main()
