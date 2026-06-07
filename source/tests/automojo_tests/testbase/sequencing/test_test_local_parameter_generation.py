"""
    Unit tests for test-local parameter generation.

    Tests verify the test-local parameter generation including test setup context
    generation, factory import addition, for loop generation for test-local
    parameters, and nesting within test setup context.

    Requirements covered:
    - 14.1: Generate test setup context when test has test-local parameter originations
    - 14.2: Test setup context format is `with sequencer.enter_test_setup_context(test_scope_name) as tsetup:`
    - 14.3: Add factory imports for test-local parameter factories to factory_imports set
    - 14.4: Generate for loops for each test-local parameter
    - 14.5: Test-local parameter loops nested within test setup context
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
from automojo.testbase.origins.resourceorigin import ResourceOrigin
from automojo.testbase.resourcelifespan import ResourceLifespan
from automojo.testbase.sources.sourcebase import SourceBase
from automojo.testbase.sequencing.testsequencer import TestSequencer


# ============================================================================
# MOCK CLASSES FOR TESTING
# ============================================================================

def test_local_factory_func():
    """Sample test-local factory function for testing."""
    yield "test_local_resource"


def another_test_local_factory_func():
    """Another test-local factory function for testing multiple parameters."""
    yield "another_test_local_resource"


class MockSourceBase(SourceBase):
    """Mock source for testing purposes."""

    def __init__(self, source_func, resource_type=str):
        super().__init__(source_func, None, resource_type, {})


class MockInjectionScope:
    """Mock InjectionScope for testing test-local parameter generation."""
    
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
# TEST FUNCTIONS WITH SPECIFIC PARAMETER NAMES
# ============================================================================

def test_with_test_param(test_param):
    """Test function with a single test_param parameter."""
    pass


def test_with_my_custom_param(my_custom_param):
    """Test function with a custom parameter name."""
    pass


def test_with_param_a_and_b(param_a, param_b):
    """Test function with two parameters."""
    pass


def test_with_no_params():
    """Test function with no parameters."""
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


def add_test_local_parameter(test_func, param_name, factory_func, implied=False, constraints=None):
    """
    Add a test-local parameter origination to the injection registry.
    
    Args:
        test_func: The test function (used to derive the scope name)
        param_name: Name of the parameter
        factory_func: The factory function to use
        implied: Whether the parameter is implied (default False)
        constraints: Optional constraints dictionary
        
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
        implied=implied,
        constraints=constraints
    )
    
    injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, origin)
    
    return origin


# ============================================================================
# TEST CLASSES
# ============================================================================

class TestSetupContextGenerationTests(unittest.TestCase):
    """
    Tests for test setup context generation.

    **Validates: Requirements 14.1, 14.2**
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

    def _create_sequencer(self):
        """Create a TestSequencer for testing."""
        return TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def test_test_setup_context_generated_when_test_has_local_params(self):
        """
        Verify test setup context is generated when test has test-local parameters.

        **Validates: Requirements 14.1**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_test_param)
        add_test_local_parameter(test_with_test_param, "test_param", test_local_factory_func)
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
            "enter_test_setup_context(",
            generated_code,
            "Generated code should contain enter_test_setup_context when test has local params"
        )

    def test_test_setup_context_not_generated_when_no_local_params(self):
        """
        Verify test setup context is not generated when test has no test-local parameters.

        **Validates: Requirements 14.1**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_no_params)
        # Register the test scope without any parameters
        scope_name = "{}#{}".format(test_with_no_params.__module__, test_with_no_params.__name__)
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
            "enter_test_setup_context(",
            generated_code,
            "Generated code should not contain enter_test_setup_context when no local params"
        )

    def test_test_setup_context_uses_correct_format(self):
        """
        Verify test setup context uses the correct format with test_scope_name.

        **Validates: Requirements 14.2**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_test_param)
        add_test_local_parameter(test_with_test_param, "test_param", test_local_factory_func)
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
            "with sequencer.enter_test_setup_context(test_scope_name) as tsetup:",
            generated_code,
            "Test setup context should use correct format with test_scope_name"
        )

    def test_test_setup_context_uses_with_statement(self):
        """
        Verify test setup context uses 'with' statement.

        **Validates: Requirements 14.2**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_test_param)
        add_test_local_parameter(test_with_test_param, "test_param", test_local_factory_func)
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
            "with sequencer.enter_test_setup_context(",
            generated_code,
            "Test setup context should use 'with' statement"
        )

    def test_test_setup_context_assigns_to_tsetup(self):
        """
        Verify test setup context is assigned to 'tsetup' variable.

        **Validates: Requirements 14.2**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_test_param)
        add_test_local_parameter(test_with_test_param, "test_param", test_local_factory_func)
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
            "as tsetup:",
            generated_code,
            "Test setup context should be assigned to 'tsetup'"
        )


class TestLocalFactoryImportTests(unittest.TestCase):
    """
    Tests for test-local parameter factory import addition to set.

    **Validates: Requirements 14.3**
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

    def _create_sequencer(self):
        """Create a TestSequencer for testing."""
        return TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def test_factory_import_added_to_set_for_test_local_parameter(self):
        """
        Verify factory import is added to factory_imports set for test-local parameter.

        **Validates: Requirements 14.3**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_test_param)
        add_test_local_parameter(test_with_test_param, "test_param", test_local_factory_func)
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
            test_local_factory_func.__module__,
            test_local_factory_func.__name__
        )
        self.assertIn(
            expected_import,
            factory_imports,
            "Factory import should be added to factory_imports set"
        )

    def test_multiple_factory_imports_added_to_set(self):
        """
        Verify multiple factory imports are added to factory_imports set.

        **Validates: Requirements 14.3**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_param_a_and_b)
        add_test_local_parameter(test_with_param_a_and_b, "param_a", test_local_factory_func)
        add_test_local_parameter(test_with_param_a_and_b, "param_b", another_test_local_factory_func)
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
        
        import_a = "from {} import {}".format(
            test_local_factory_func.__module__,
            test_local_factory_func.__name__
        )
        import_b = "from {} import {}".format(
            another_test_local_factory_func.__module__,
            another_test_local_factory_func.__name__
        )
        
        self.assertIn(import_a, factory_imports, "First factory import should be in set")
        self.assertIn(import_b, factory_imports, "Second factory import should be in set")

    def test_factory_import_format_is_correct(self):
        """
        Verify factory import uses format `from {module} import {function}`.

        **Validates: Requirements 14.3**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_test_param)
        add_test_local_parameter(test_with_test_param, "test_param", test_local_factory_func)
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
            self.assertTrue(
                import_stmt.startswith("from "),
                "Import should start with 'from '"
            )
            self.assertIn(
                " import ",
                import_stmt,
                "Import should contain ' import '"
            )


class TestLocalForLoopTests(unittest.TestCase):
    """
    Tests for test-local parameter for loop generation.

    **Validates: Requirements 14.4**
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

    def _create_sequencer(self):
        """Create a TestSequencer for testing."""
        return TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def test_for_loop_generated_for_test_local_parameter(self):
        """
        Verify for loop is generated for test-local parameter.

        **Validates: Requirements 14.4**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_test_param)
        add_test_local_parameter(test_with_test_param, "test_param", test_local_factory_func)
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
        
        expected_loop = "for test_param in {}():".format(test_local_factory_func.__name__)
        self.assertIn(
            expected_loop,
            generated_code,
            "Generated code should contain for loop iterating over factory function"
        )

    def test_for_loop_uses_parameter_name_as_variable(self):
        """
        Verify for loop uses the parameter name as the loop variable.

        **Validates: Requirements 14.4**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_my_custom_param)
        add_test_local_parameter(test_with_my_custom_param, "my_custom_param", test_local_factory_func)
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
            "for my_custom_param in",
            generated_code,
            "For loop should use parameter name as loop variable"
        )

    def test_multiple_for_loops_generated_for_multiple_parameters(self):
        """
        Verify multiple for loops are generated for multiple test-local parameters.

        **Validates: Requirements 14.4**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_param_a_and_b)
        add_test_local_parameter(test_with_param_a_and_b, "param_a", test_local_factory_func)
        add_test_local_parameter(test_with_param_a_and_b, "param_b", another_test_local_factory_func)
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
            "for param_a in",
            generated_code,
            "Should contain for loop for first parameter"
        )
        self.assertIn(
            "for param_b in",
            generated_code,
            "Should contain for loop for second parameter"
        )

    def test_for_loop_calls_factory_function(self):
        """
        Verify for loop calls the factory function.

        **Validates: Requirements 14.4**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_test_param)
        add_test_local_parameter(test_with_test_param, "test_param", test_local_factory_func)
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
            "{}()".format(test_local_factory_func.__name__),
            generated_code,
            "For loop should call the factory function"
        )


class TestLocalParameterNestingTests(unittest.TestCase):
    """
    Tests for test-local parameter loop nesting within test setup context.

    **Validates: Requirements 14.5**
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

    def _create_sequencer(self):
        """Create a TestSequencer for testing."""
        return TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def test_parameter_loop_nested_within_test_setup_context(self):
        """
        Verify parameter loop is nested within test setup context.

        **Validates: Requirements 14.5**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_test_param)
        add_test_local_parameter(test_with_test_param, "test_param", test_local_factory_func)
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
        lines = generated_code.split(os.linesep)
        
        setup_context_index = None
        for_loop_index = None
        
        for i, line in enumerate(lines):
            if 'enter_test_setup_context(' in line:
                setup_context_index = i
            if 'for test_param in' in line:
                for_loop_index = i
        
        self.assertIsNotNone(setup_context_index, "Test setup context should be found")
        self.assertIsNotNone(for_loop_index, "For loop should be found")
        
        self.assertGreater(
            for_loop_index,
            setup_context_index,
            "For loop should appear after test setup context"
        )

    def test_parameter_loop_indented_within_test_setup_context(self):
        """
        Verify parameter loop is properly indented within test setup context.

        **Validates: Requirements 14.5**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_test_param)
        add_test_local_parameter(test_with_test_param, "test_param", test_local_factory_func)
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
        lines = generated_code.split(os.linesep)
        
        setup_context_indent = None
        for_loop_indent = None
        
        for line in lines:
            if 'enter_test_setup_context(' in line:
                setup_context_indent = len(line) - len(line.lstrip())
            if 'for test_param in' in line:
                for_loop_indent = len(line) - len(line.lstrip())
        
        self.assertIsNotNone(setup_context_indent, "Test setup context should be found")
        self.assertIsNotNone(for_loop_indent, "For loop should be found")
        
        self.assertGreater(
            for_loop_indent,
            setup_context_indent,
            "For loop should be indented more than test setup context"
        )

    def test_nested_parameter_loops_have_increasing_indentation(self):
        """
        Verify nested parameter loops have increasing indentation levels.

        **Validates: Requirements 14.5**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_param_a_and_b)
        add_test_local_parameter(test_with_param_a_and_b, "param_a", test_local_factory_func)
        add_test_local_parameter(test_with_param_a_and_b, "param_b", another_test_local_factory_func)
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
        lines = generated_code.split(os.linesep)
        
        param_a_indent = None
        param_b_indent = None
        
        for line in lines:
            if 'for param_a in' in line:
                param_a_indent = len(line) - len(line.lstrip())
            if 'for param_b in' in line:
                param_b_indent = len(line) - len(line.lstrip())
        
        self.assertIsNotNone(param_a_indent, "First parameter loop should be found")
        self.assertIsNotNone(param_b_indent, "Second parameter loop should be found")
        
        self.assertGreater(
            param_b_indent,
            param_a_indent,
            "Second parameter loop should be indented more than first"
        )


if __name__ == '__main__':
    unittest.main()
