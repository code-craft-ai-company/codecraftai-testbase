"""
    Unit tests for notables map generation.

    Tests verify the notables map generation including notables dictionary generation,
    trailing comma for single notable, notables passed to test scope context, and
    notables skipped when no test-local parameters.

    Requirements covered:
    - 15.1: Generate notables dictionary when test has test-local parameters
    - 15.2: Format is `notables = { 'param1': param1, 'param2': param2, }`
    - 15.3: Include trailing comma for single notable (dict syntax)
    - 15.4: Pass notables dictionary to test scope context as `notables=notables`
    - 15.5: Skip notables dictionary when no test-local parameters
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


def third_test_local_factory_func():
    """Third test-local factory function for testing three parameters."""
    yield "third_test_local_resource"


class MockSourceBase(SourceBase):
    """Mock source for testing purposes."""

    def __init__(self, source_func, resource_type=str):
        super().__init__(source_func, None, resource_type, {})


class MockInjectionScope:
    """Mock InjectionScope for testing notables map generation."""
    
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

def test_with_single_param(single_param):
    """Test function with a single parameter."""
    pass


def test_with_two_params(param_a, param_b):
    """Test function with two parameters."""
    pass


def test_with_three_params(param_x, param_y, param_z):
    """Test function with three parameters."""
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

class NotablesDictionaryGenerationTests(unittest.TestCase):
    """
    Tests for notables dictionary generation when test has test-local parameters.

    **Validates: Requirements 15.1**
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

    def test_notables_dictionary_generated_when_test_has_local_params(self):
        """
        Verify notables dictionary is generated when test has test-local parameters.

        **Validates: Requirements 15.1**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_single_param)
        add_test_local_parameter(test_with_single_param, "single_param", test_local_factory_func)
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
            "notables",
            generated_code,
            "Generated code should contain notables dictionary when test has local params"
        )

    def test_notables_dictionary_contains_parameter_name_and_value(self):
        """
        Verify notables dictionary contains parameter name as key and value.

        **Validates: Requirements 15.1**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_single_param)
        add_test_local_parameter(test_with_single_param, "single_param", test_local_factory_func)
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
            "'single_param': single_param",
            generated_code,
            "Notables dictionary should contain parameter name as key and value"
        )


class NotablesFormatTests(unittest.TestCase):
    """
    Tests for notables dictionary format.

    **Validates: Requirements 15.2**
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

    def test_notables_uses_dict_literal_format(self):
        """
        Verify notables uses dictionary literal format with curly braces.

        **Validates: Requirements 15.2**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_single_param)
        add_test_local_parameter(test_with_single_param, "single_param", test_local_factory_func)
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
            "notables = {",
            generated_code,
            "Notables should use dictionary literal format with curly braces"
        )

    def test_notables_format_with_multiple_params(self):
        """
        Verify notables format with multiple parameters.

        **Validates: Requirements 15.2**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_two_params)
        add_test_local_parameter(test_with_two_params, "param_a", test_local_factory_func)
        add_test_local_parameter(test_with_two_params, "param_b", another_test_local_factory_func)
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
            "'param_a': param_a",
            generated_code,
            "Notables should contain first parameter"
        )
        self.assertIn(
            "'param_b': param_b",
            generated_code,
            "Notables should contain second parameter"
        )


class NotablesTrailingCommaTests(unittest.TestCase):
    """
    Tests for trailing comma in single notable dictionary.

    **Validates: Requirements 15.3**
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

    def test_single_notable_has_trailing_comma(self):
        """
        Verify single notable has trailing comma for valid dict syntax.

        **Validates: Requirements 15.3**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_single_param)
        add_test_local_parameter(test_with_single_param, "single_param", test_local_factory_func)
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
        
        # Find the notables line and check for trailing comma
        lines = generated_code.split(os.linesep)
        notables_line = None
        for line in lines:
            if "notables = {" in line:
                notables_line = line
                break
        
        self.assertIsNotNone(notables_line, "Notables line should be found")
        self.assertIn(
            "'single_param': single_param,",
            notables_line,
            "Single notable should have trailing comma"
        )

    def test_multiple_notables_format_is_valid(self):
        """
        Verify multiple notables format is valid Python dict syntax.

        **Validates: Requirements 15.3**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_two_params)
        add_test_local_parameter(test_with_two_params, "param_a", test_local_factory_func)
        add_test_local_parameter(test_with_two_params, "param_b", another_test_local_factory_func)
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
        
        # Find the notables line
        lines = generated_code.split(os.linesep)
        notables_line = None
        for line in lines:
            if "notables = {" in line:
                notables_line = line
                break
        
        self.assertIsNotNone(notables_line, "Notables line should be found")
        # Multiple notables should be comma-separated
        self.assertIn(
            ", ",
            notables_line,
            "Multiple notables should be comma-separated"
        )


class NotablesPassedToTestScopeContextTests(unittest.TestCase):
    """
    Tests for notables passed to test scope context.

    **Validates: Requirements 15.4**
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

    def test_notables_passed_to_test_scope_context(self):
        """
        Verify notables dictionary is passed to test scope context.

        **Validates: Requirements 15.4**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_single_param)
        add_test_local_parameter(test_with_single_param, "single_param", test_local_factory_func)
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
            "notables=notables",
            generated_code,
            "Notables should be passed to test scope context as notables=notables"
        )

    def test_notables_passed_as_keyword_argument(self):
        """
        Verify notables is passed as keyword argument to enter_test_scope_context.

        **Validates: Requirements 15.4**
        """
        scope_node, module_name = create_scope_node_with_test_func(test_with_single_param)
        add_test_local_parameter(test_with_single_param, "single_param", test_local_factory_func)
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
            "enter_test_scope_context(test_scope_name, notables=notables)",
            generated_code,
            "Notables should be passed as keyword argument to enter_test_scope_context"
        )


class NotablesSkippedWhenNoLocalParamsTests(unittest.TestCase):
    """
    Tests for notables skipped when no test-local parameters.

    **Validates: Requirements 15.5**
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

    def test_notables_not_generated_when_no_local_params(self):
        """
        Verify notables dictionary is not generated when test has no local parameters.

        **Validates: Requirements 15.5**
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
            "notables = {",
            generated_code,
            "Notables dictionary should not be generated when no local params"
        )

    def test_notables_not_passed_to_context_when_no_local_params(self):
        """
        Verify notables is not passed to test scope context when no local parameters.

        **Validates: Requirements 15.5**
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
            "notables=notables",
            generated_code,
            "Notables should not be passed to context when no local params"
        )

    def test_test_scope_context_without_notables_argument(self):
        """
        Verify test scope context is called without notables argument when no local params.

        **Validates: Requirements 15.5**
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
        
        # Should have enter_test_scope_context with just test_scope_name
        self.assertIn(
            "enter_test_scope_context(test_scope_name)",
            generated_code,
            "Test scope context should be called with just test_scope_name when no local params"
        )


if __name__ == '__main__':
    unittest.main()
