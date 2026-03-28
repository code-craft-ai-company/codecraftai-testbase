"""
    Unit tests for test scope code generation in _generate_scope_method.

    Tests verify the test scope code generation including comment header generation,
    test_scope_name variable generation, test scope context generation, and test
    function import and call.

    Requirements covered:
    - 13.1: Generate test scope code block when child node is TestRef
    - 13.2: Test scope block begins with comment header
    - 13.3: Test scope block sets test_scope_name variable
    - 13.4: Test scope block contains enter_test_scope_context context manager
    - 13.5: Test scope block imports and calls test function with all required parameters
"""

import collections
import io
import os
import tempfile
import unittest

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


class MockInjectionScope:
    """Mock InjectionScope for testing test scope code generation."""
    
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


class NamedTestRef(TestRef):
    """TestRef variant that can override the generated scope name and async flag."""

    def __init__(self, testfunc, scope_name=None, is_async=None):
        super().__init__(testfunc, is_async=is_async)
        self._scope_name_override = scope_name
        self._is_async_override = is_async

    @property
    def name(self):
        if self._scope_name_override is not None:
            return self._scope_name_override
        return super().name

    @property
    def is_async(self):
        if self._is_async_override is not None:
            return self._is_async_override
        return super().is_async


def create_test_function(name, module_name, params=None):
    """
    Create a mock test function with the given name, module, and parameters.
    
    Args:
        name: Name of the test function
        module_name: Module name for the test function
        params: Optional list of parameter names for the function signature
        
    Returns:
        A function object with the specified attributes
    """
    if params is None:
        params = []
    
    # Create function with specified parameters
    if len(params) == 0:
        def test_func():
            pass
    elif len(params) == 1:
        def test_func(param1):
            pass
    elif len(params) == 2:
        def test_func(param1, param2):
            pass
    elif len(params) == 3:
        def test_func(param1, param2, param3):
            pass
    else:
        def test_func(*args):
            pass
    
    test_func.__name__ = name
    test_func.__module__ = module_name
    return test_func


def create_scope_node_with_test(module_name, test_name, test_params=None):
    """
    Create a scope node with a single test reference.
    
    Args:
        module_name: Name of the module
        test_name: Name of the test function
        test_params: Optional list of parameter names for the test function
        
    Returns:
        MockTestGroup: A test group node with one test reference
    """
    parent = MockTestGroup(module_name, package="")
    test_func = create_test_function(test_name, module_name, test_params)
    test_ref = TestRef(test_func)
    parent._children[test_ref.base_name] = test_ref
    return parent


def create_scope_node_with_multiple_tests(module_name, test_names):
    """
    Create a scope node with multiple test references.
    
    Args:
        module_name: Name of the module
        test_names: List of test function names
        
    Returns:
        MockTestGroup: A test group node with multiple test references
    """
    parent = MockTestGroup(module_name, package="")
    for test_name in test_names:
        test_func = create_test_function(test_name, module_name)
        test_ref = TestRef(test_func)
        parent._children[test_ref.base_name] = test_ref
    return parent


def create_property_test_function(name, module_name, params=None, strategies=None):
    """Create a mock property test function for sequence code generation tests."""
    test_func = create_test_function(name, module_name, params=params)
    if strategies is None:
        strategies = {}
    test_func._property_ = {"strategies": strategies}
    return test_func


def create_scope_node_with_property_test(module_name, test_name, test_params=None,
                                         strategies=None, scope_name=None):
    """Create a scope node with a single property test reference."""
    parent = MockTestGroup(module_name, package="")
    test_func = create_property_test_function(test_name, module_name, test_params, strategies)
    test_ref = NamedTestRef(test_func, scope_name=scope_name)
    parent._children[test_ref.base_name] = test_ref
    return parent


def create_scope_node_with_async_test(module_name, test_name, test_params=None, scope_name=None):
    """Create a scope node with a single async test reference."""
    parent = MockTestGroup(module_name, package="")
    test_func = create_test_function(test_name, module_name, test_params)
    test_ref = NamedTestRef(test_func, scope_name=scope_name, is_async=True)
    parent._children[test_ref.base_name] = test_ref
    return parent


class TestScopeCommentHeaderTests(unittest.TestCase):
    """
    Tests for test scope comment header generation.

    **Validates: Requirements 13.1, 13.2**
    """

    def setUp(self):
        """Set up test fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()

        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

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


    def _register_test_scope(self, test_name, module_name):
        """Register a test scope in the injection registry."""
        scope_name = "{}#{}".format(module_name, test_name)
        injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, None)

    def test_test_scope_generates_comment_header(self):
        """
        Verify test scope code block begins with comment header.

        **Validates: Requirements 13.1, 13.2**
        """
        scope_node = create_scope_node_with_test("test_module", "test_example")
        sequencer = self._create_sequencer()
        
        # Register the test scope in the injection registry
        self._register_test_scope("test_example", "test_module")
        
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
            "# ================ Test Scope:",
            generated_code,
            "Generated code should contain test scope comment header"
        )

    def test_comment_header_contains_test_name(self):
        """
        Verify comment header contains the test function name.

        **Validates: Requirements 13.2**
        """
        scope_node = create_scope_node_with_test("test_module", "test_my_function")
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_my_function", "test_module")
        
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
        
        # The test scope name includes the module prefix (e.g., test_module#test_my_function)
        self.assertIn(
            "test_my_function",
            generated_code,
            "Comment header should contain the test function name"
        )
        self.assertIn(
            "Test Scope:",
            generated_code,
            "Comment header should have Test Scope label"
        )


    def test_comment_header_has_visual_separator(self):
        """
        Verify comment header has visual separator characters.

        **Validates: Requirements 13.2**
        """
        scope_node = create_scope_node_with_test("test_module", "test_example")
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_example", "test_module")
        
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
        
        # Check for the visual separator pattern with equals signs
        self.assertIn(
            "================",
            generated_code,
            "Comment header should have visual separator with equals signs"
        )

    def test_multiple_tests_each_have_comment_header(self):
        """
        Verify each test in a module has its own comment header.

        **Validates: Requirements 13.1, 13.2**
        """
        scope_node = create_scope_node_with_multiple_tests(
            "test_module", 
            ["test_first", "test_second"]
        )
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_first", "test_module")
        self._register_test_scope("test_second", "test_module")
        
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
        
        # The test scope name includes the module prefix (e.g., test_module#test_first)
        self.assertIn(
            "test_first",
            generated_code,
            "First test should have its own comment header"
        )
        self.assertIn(
            "test_second",
            generated_code,
            "Second test should have its own comment header"
        )
        # Verify both have the Test Scope label
        self.assertEqual(
            generated_code.count("# ================ Test Scope:"),
            2,
            "Should have two test scope comment headers"
        )



class TestScopeNameVariableTests(unittest.TestCase):
    """
    Tests for test_scope_name variable generation.

    **Validates: Requirements 13.3**
    """

    def setUp(self):
        """Set up test fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()

        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

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

    def _register_test_scope(self, test_name, module_name):
        """Register a test scope in the injection registry."""
        scope_name = "{}#{}".format(module_name, test_name)
        injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, None)


    def test_test_scope_name_variable_generated(self):
        """
        Verify test_scope_name variable is generated.

        **Validates: Requirements 13.3**
        """
        scope_node = create_scope_node_with_test("test_module", "test_example")
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_example", "test_module")
        
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
            "test_scope_name =",
            generated_code,
            "Generated code should contain test_scope_name variable assignment"
        )

    def test_test_scope_name_contains_test_name(self):
        """
        Verify test_scope_name variable contains the test function name.

        **Validates: Requirements 13.3**
        """
        scope_node = create_scope_node_with_test("test_module", "test_my_function")
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_my_function", "test_module")
        
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
        
        # Find the line with test_scope_name assignment
        lines = generated_code.split(os.linesep)
        scope_name_line = None
        for line in lines:
            if "test_scope_name =" in line:
                scope_name_line = line
                break
        
        self.assertIsNotNone(scope_name_line, "test_scope_name assignment should be found")
        self.assertIn(
            "test_my_function",
            scope_name_line,
            "test_scope_name should contain the test function name"
        )


    def test_test_scope_name_is_string_literal(self):
        """
        Verify test_scope_name is assigned as a string literal.

        **Validates: Requirements 13.3**
        """
        scope_node = create_scope_node_with_test("test_module", "test_example")
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_example", "test_module")
        
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
        
        # Check that the test_scope_name is assigned with quotes (string literal)
        self.assertIn(
            'test_scope_name = "',
            generated_code,
            "test_scope_name should be assigned as a string literal"
        )

    def test_test_scope_name_appears_before_context(self):
        """
        Verify test_scope_name variable is set before the test scope context.

        **Validates: Requirements 13.3**
        """
        scope_node = create_scope_node_with_test("test_module", "test_example")
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_example", "test_module")
        
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
        
        # Find positions of test_scope_name assignment and context manager
        scope_name_pos = generated_code.find('test_scope_name = "')
        context_pos = generated_code.find('enter_test_scope_context(')
        
        self.assertGreater(
            scope_name_pos, -1,
            "test_scope_name assignment should be found"
        )
        self.assertGreater(
            context_pos, -1,
            "enter_test_scope_context should be found"
        )
        self.assertLess(
            scope_name_pos, context_pos,
            "test_scope_name should appear before enter_test_scope_context"
        )



class TestScopeContextGenerationTests(unittest.TestCase):
    """
    Tests for test scope context manager generation.

    **Validates: Requirements 13.4**
    """

    def setUp(self):
        """Set up test fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()

        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

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

    def _register_test_scope(self, test_name, module_name):
        """Register a test scope in the injection registry."""
        scope_name = "{}#{}".format(module_name, test_name)
        injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, None)


    def test_test_scope_context_generated(self):
        """
        Verify test scope context manager is generated.

        **Validates: Requirements 13.4**
        """
        scope_node = create_scope_node_with_test("test_module", "test_example")
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_example", "test_module")
        
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
            "enter_test_scope_context(",
            generated_code,
            "Generated code should contain enter_test_scope_context"
        )

    def test_test_scope_context_uses_with_statement(self):
        """
        Verify test scope context uses 'with' statement.

        **Validates: Requirements 13.4**
        """
        scope_node = create_scope_node_with_test("test_module", "test_example")
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_example", "test_module")
        
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
            "with sequencer.enter_test_scope_context(",
            generated_code,
            "Test scope context should use 'with' statement"
        )


    def test_test_scope_context_assigns_to_tscope(self):
        """
        Verify test scope context is assigned to 'tscope' variable.

        **Validates: Requirements 13.4**
        """
        scope_node = create_scope_node_with_test("test_module", "test_example")
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_example", "test_module")
        
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
            "as tscope:",
            generated_code,
            "Test scope context should be assigned to 'tscope'"
        )

    def test_test_scope_context_uses_test_scope_name_variable(self):
        """
        Verify test scope context uses the test_scope_name variable.

        **Validates: Requirements 13.4**
        """
        scope_node = create_scope_node_with_test("test_module", "test_example")
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_example", "test_module")
        
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
            "enter_test_scope_context(test_scope_name",
            generated_code,
            "Test scope context should use test_scope_name variable"
        )



class TestFunctionImportAndCallTests(unittest.TestCase):
    """
    Tests for test function import and call generation.

    **Validates: Requirements 13.5**
    """

    def setUp(self):
        """Set up test fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()

        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

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

    def _register_test_scope(self, test_name, module_name):
        """Register a test scope in the injection registry."""
        scope_name = "{}#{}".format(module_name, test_name)
        injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, None)


    def test_test_function_import_generated(self):
        """
        Verify test function import statement is generated.

        **Validates: Requirements 13.5**
        """
        scope_node = create_scope_node_with_test("test_module", "test_example")
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_example", "test_module")
        
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
            "from test_module import test_example",
            generated_code,
            "Generated code should contain test function import"
        )

    def test_test_function_call_generated(self):
        """
        Verify test function call is generated.

        **Validates: Requirements 13.5**
        """
        scope_node = create_scope_node_with_test("test_module", "test_example")
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_example", "test_module")
        
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
            "test_example(",
            generated_code,
            "Generated code should contain test function call"
        )


    def test_import_appears_before_call(self):
        """
        Verify import statement appears before function call.

        **Validates: Requirements 13.5**
        """
        scope_node = create_scope_node_with_test("test_module", "test_example")
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_example", "test_module")
        
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
        
        import_pos = generated_code.find("from test_module import test_example")
        call_pos = generated_code.find("test_example(")
        
        self.assertGreater(
            import_pos, -1,
            "Import statement should be found"
        )
        self.assertGreater(
            call_pos, -1,
            "Function call should be found"
        )
        self.assertLess(
            import_pos, call_pos,
            "Import should appear before function call"
        )

    def test_import_inside_test_scope_context(self):
        """
        Verify import statement is inside the test scope context.

        **Validates: Requirements 13.5**
        """
        scope_node = create_scope_node_with_test("test_module", "test_example")
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_example", "test_module")
        
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
        
        # The import should appear after the test scope context
        context_pos = generated_code.find("enter_test_scope_context(")
        import_pos = generated_code.find("from test_module import test_example")
        
        self.assertGreater(
            import_pos, context_pos,
            "Import should be inside the test scope context"
        )


    def test_test_function_call_with_no_parameters(self):
        """
        Verify test function call with no parameters generates empty parentheses.

        **Validates: Requirements 13.5**
        """
        scope_node = create_scope_node_with_test("test_module", "test_no_params")
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_no_params", "test_module")
        
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
            "test_no_params()",
            generated_code,
            "Test function call with no parameters should have empty parentheses"
        )

    def test_multiple_tests_each_have_import_and_call(self):
        """
        Verify each test in a module has its own import and call.

        **Validates: Requirements 13.5**
        """
        scope_node = create_scope_node_with_multiple_tests(
            "test_module", 
            ["test_first", "test_second"]
        )
        sequencer = self._create_sequencer()
        
        self._register_test_scope("test_first", "test_module")
        self._register_test_scope("test_second", "test_module")
        
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
        
        # Check imports
        self.assertIn(
            "from test_module import test_first",
            generated_code,
            "First test should have its own import"
        )
        self.assertIn(
            "from test_module import test_second",
            generated_code,
            "Second test should have its own import"
        )
        
        # Check calls
        self.assertIn(
            "test_first(",
            generated_code,
            "First test should have its own call"
        )
        self.assertIn(
            "test_second(",
            generated_code,
            "Second test should have its own call"
        )


class PropertyTestCaseNameGenerationTests(unittest.TestCase):
    """Tests for generated property test case-name variables."""

    def setUp(self):
        """Set up test fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()

        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

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

    def _register_test_scope(self, scope_name):
        """Register a test scope in the injection registry."""
        injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, None)

    def test_property_test_generates_test_case_name_variable(self):
        """Verify property test generation assigns test_case_name before invocation."""
        scope_name = "test_module#test_property"
        scope_node = create_scope_node_with_property_test(
            "test_module",
            "test_property",
            strategies={"value": object()},
        )
        sequencer = self._create_sequencer()

        self._register_test_scope(scope_name)

        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()

        sequencer._generate_scope_method(
            output_buffer, "test_module", "test_module", scope_node,
            ["sequencer"], factory_imports, constraint_imports, "    "
        )

        generated_code = output_buffer.getvalue()

        self.assertIn(
            'test_case_name = "test_module#test_property"',
            generated_code,
            "Property tests should assign test_case_name"
        )
        self.assertIn(
            "sequencer.run_property_test(test_property, test_case_name, tscope.recorder, tscope.scope_id, {})",
            generated_code,
            "Property tests should pass test_case_name to run_property_test"
        )

    def test_property_test_keeps_scope_and_case_name_separate(self):
        """Verify property test generation keeps test_scope_name and test_case_name distinct."""
        scope_name = "test_module#test_property[param-set-a]"
        scope_node = create_scope_node_with_property_test(
            "test_module",
            "test_property",
            strategies={"value": object()},
            scope_name=scope_name,
        )
        sequencer = self._create_sequencer()

        self._register_test_scope(scope_name)

        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()

        sequencer._generate_scope_method(
            output_buffer, "test_module", "test_module", scope_node,
            ["sequencer"], factory_imports, constraint_imports, "    "
        )

        generated_code = output_buffer.getvalue()

        self.assertIn(
            'test_scope_name = "test_module#test_property[param-set-a]"',
            generated_code,
            "Generated code should preserve the scope name"
        )
        self.assertIn(
            'test_case_name = "test_module#test_property"',
            generated_code,
            "Generated code should define the property test case name separately"
        )
        self.assertNotIn(
            "sequencer.run_property_test(test_property, 'test_module#test_property'",
            generated_code,
            "Property test generation should not inline the case name literal"
        )


class AsyncTestCodeGenerationTests(unittest.TestCase):
    """Tests for generated async test execution calls."""

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()

        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

    def _create_sequencer(self):
        return TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def _register_test_scope(self, test_name, module_name):
        scope_name = "{}#{}".format(module_name, test_name)
        injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, None)

    def test_async_test_uses_run_async_test_helper(self):
        scope_node = create_scope_node_with_async_test(
            "test_module", "test_async_example", test_params=["param1", "param2"]
        )
        sequencer = self._create_sequencer()

        self._register_test_scope("test_async_example", "test_module")

        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()

        sequencer._generate_scope_method(
            output_buffer, "test_module", "test_module", scope_node,
            ["sequencer"], factory_imports, constraint_imports, "    "
        )

        generated_code = output_buffer.getvalue()

        self.assertIn(
            "sequencer.run_async_test(test_async_example, {'param1': param1, 'param2': param2})",
            generated_code,
            "Async tests should be routed through run_async_test with injected arguments"
        )
        self.assertNotIn(
            "test_async_example(param1, param2)",
            generated_code,
            "Async tests should not be emitted as direct function calls"
        )


if __name__ == '__main__':
    unittest.main()
