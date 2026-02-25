"""
    Unit tests for session-level parameter loop generation.

    Tests verify the session-level parameter loop generation including factory
    import generation, for loop generation, parameter nesting within session
    scope, child call args accumulation, and implied parameter skipping.

    Requirements covered:
    - 6.1: Generate import statements for each factory function
    - 6.2: Generate for loops iterating over factory function calls
    - 6.3: Parameter loops nested within session scope context
    - 6.4: Parameter variable names added to child scope call arguments
    - 6.5: Skip implied parameter originations
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
from automojo.testbase.injection.injectionregistry import injection_registry
from automojo.testbase.injection.injectionscope import InjectionScope
from automojo.testbase.origins.resourceorigin import ResourceOrigin
from automojo.testbase.resourcelifespan import ResourceLifespan
from automojo.testbase.sources.sourcebase import SourceBase
from automojo.testbase.sequencing.testsequencer import TestSequencer


# ============================================================================
# MOCK CLASSES FOR TESTING
# ============================================================================

def sample_factory_func():
    """Sample factory function for testing."""
    yield "resource"


def another_factory_func():
    """Another factory function for testing multiple parameters."""
    yield "another_resource"


def factory_with_constraints(constraints):
    """Factory function with constraints parameter."""
    yield constraints


class MockSourceBase(SourceBase):
    """Mock source for testing purposes."""

    def __init__(self, source_func, resource_type=str):
        super().__init__(source_func, None, resource_type, {})


class MockInjectionScope:
    """Mock InjectionScope for testing session method generation."""
    
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

def create_minimal_test_tree():
    """
    Create a minimal test tree with no tests for basic generation testing.
    
    Returns:
        MockTestGroup: Root of the test tree with no children
    """
    root = MockTestGroup("root")
    return root


def create_test_tree_with_single_module(module_name, package=""):
    """
    Create a test tree with a single module (no tests).
    
    Args:
        module_name: Name of the module
        package: Package path for the module
        
    Returns:
        MockTestGroup: Root of the test tree with one child module
    """
    root = MockTestGroup("root")
    module_group = MockTestGroup(module_name, package=package)
    root._children[module_name] = module_group
    return root


def add_session_parameter(test_tree, param_name, factory_func, implied=False, constraints=None):
    """
    Add a session-level parameter origination to the test tree.
    
    Args:
        test_tree: The root MockTestGroup
        param_name: Name of the parameter
        factory_func: The factory function to use
        implied: Whether the parameter is implied (default False)
        constraints: Optional constraints dictionary
        
    Returns:
        ResourceOrigin: The created resource origin
    """
    source = MockSourceBase(factory_func)
    origin = ResourceOrigin(
        "<session>",
        param_name,
        ResourceLifespan.Session,
        source,
        implied=implied,
        constraints=constraints
    )
    test_tree._mock_scope.parameter_originations[param_name] = origin
    return origin


# ============================================================================
# TEST CLASSES
# ============================================================================

class SessionParameterFactoryImportTests(unittest.TestCase):
    """
    Tests for session-level parameter factory import generation.

    **Validates: Requirements 6.1**
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


    def test_factory_import_generated_for_session_parameter(self):
        """
        Verify import statement is generated for session-scoped parameter factory.

        **Validates: Requirements 6.1**
        """
        test_tree = create_minimal_test_tree()
        add_session_parameter(test_tree, "session_resource", sample_factory_func)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        # Verify import statement is generated
        expected_import = "from {} import {}".format(
            sample_factory_func.__module__,
            sample_factory_func.__name__
        )
        self.assertIn(
            expected_import,
            generated_code,
            "Generated code should contain import for factory function"
        )

    def test_multiple_factory_imports_generated(self):
        """
        Verify import statements are generated for multiple session-scoped parameters.

        **Validates: Requirements 6.1**
        """
        test_tree = create_minimal_test_tree()
        add_session_parameter(test_tree, "resource_a", sample_factory_func)
        add_session_parameter(test_tree, "resource_b", another_factory_func)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        # Verify both import statements are generated
        import_a = "from {} import {}".format(
            sample_factory_func.__module__,
            sample_factory_func.__name__
        )
        import_b = "from {} import {}".format(
            another_factory_func.__module__,
            another_factory_func.__name__
        )
        
        self.assertIn(import_a, generated_code, "Should contain import for first factory")
        self.assertIn(import_b, generated_code, "Should contain import for second factory")


    def test_factory_import_uses_correct_module_path(self):
        """
        Verify import statement uses the correct module path.

        **Validates: Requirements 6.1**
        """
        test_tree = create_minimal_test_tree()
        add_session_parameter(test_tree, "session_resource", sample_factory_func)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        # Verify the module path is correct
        self.assertIn(
            sample_factory_func.__module__,
            generated_code,
            "Import should use correct module path"
        )


class SessionParameterForLoopTests(unittest.TestCase):
    """
    Tests for session-level parameter for loop generation.

    **Validates: Requirements 6.2**
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


    def test_for_loop_generated_for_session_parameter(self):
        """
        Verify for loop is generated for session-scoped parameter.

        **Validates: Requirements 6.2**
        """
        test_tree = create_minimal_test_tree()
        add_session_parameter(test_tree, "session_resource", sample_factory_func)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        # Verify for loop is generated with parameter name and factory call
        expected_loop = "for session_resource in {}():".format(sample_factory_func.__name__)
        self.assertIn(
            expected_loop,
            generated_code,
            "Generated code should contain for loop iterating over factory function"
        )

    def test_for_loop_uses_parameter_name_as_variable(self):
        """
        Verify for loop uses the parameter name as the loop variable.

        **Validates: Requirements 6.2**
        """
        test_tree = create_minimal_test_tree()
        add_session_parameter(test_tree, "my_custom_param", sample_factory_func)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        # Verify the parameter name is used as the loop variable
        self.assertIn(
            "for my_custom_param in",
            generated_code,
            "For loop should use parameter name as loop variable"
        )

    def test_multiple_for_loops_generated_for_multiple_parameters(self):
        """
        Verify multiple for loops are generated for multiple session parameters.

        **Validates: Requirements 6.2**
        """
        test_tree = create_minimal_test_tree()
        add_session_parameter(test_tree, "param_a", sample_factory_func)
        add_session_parameter(test_tree, "param_b", another_factory_func)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        # Verify both for loops are generated
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



class SessionParameterNestingTests(unittest.TestCase):
    """
    Tests for parameter loop nesting within session scope context.

    **Validates: Requirements 6.3**
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

    def test_parameter_loop_nested_within_session_scope(self):
        """
        Verify parameter loop is nested within session scope context.

        **Validates: Requirements 6.3**
        """
        test_tree = create_minimal_test_tree()
        add_session_parameter(test_tree, "session_resource", sample_factory_func)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        lines = generated_code.split(os.linesep)
        
        # Find the session scope context line and the for loop line
        scope_context_index = None
        for_loop_index = None
        
        for i, line in enumerate(lines):
            if 'enter_session_scope_context()' in line:
                scope_context_index = i
            if 'for session_resource in' in line:
                for_loop_index = i
        
        self.assertIsNotNone(scope_context_index, "Session scope context should be found")
        self.assertIsNotNone(for_loop_index, "For loop should be found")
        
        # Verify for loop comes after session scope context
        self.assertGreater(
            for_loop_index,
            scope_context_index,
            "For loop should appear after session scope context"
        )


    def test_parameter_loop_indented_within_session_scope(self):
        """
        Verify parameter loop is properly indented within session scope.

        **Validates: Requirements 6.3**
        """
        test_tree = create_minimal_test_tree()
        add_session_parameter(test_tree, "session_resource", sample_factory_func)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        lines = generated_code.split(os.linesep)
        
        # Find the for loop line
        for_loop_line = None
        for line in lines:
            if 'for session_resource in' in line:
                for_loop_line = line
                break
        
        self.assertIsNotNone(for_loop_line, "For loop line should be found")
        
        # Verify the for loop is indented (at least 2 levels: function + scope context)
        expected_indent = indent_space * 2  # Two levels of indentation
        self.assertTrue(
            for_loop_line.startswith(expected_indent),
            "For loop should be indented within session scope context"
        )

    def test_nested_parameter_loops_have_increasing_indentation(self):
        """
        Verify nested parameter loops have increasing indentation levels.

        **Validates: Requirements 6.3**
        """
        test_tree = create_minimal_test_tree()
        add_session_parameter(test_tree, "param_a", sample_factory_func)
        add_session_parameter(test_tree, "param_b", another_factory_func)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        lines = generated_code.split(os.linesep)
        
        # Find both for loop lines
        loop_a_line = None
        loop_b_line = None
        
        for line in lines:
            if 'for param_a in' in line:
                loop_a_line = line
            if 'for param_b in' in line:
                loop_b_line = line
        
        self.assertIsNotNone(loop_a_line, "First for loop should be found")
        self.assertIsNotNone(loop_b_line, "Second for loop should be found")
        
        # Count leading spaces
        indent_a = len(loop_a_line) - len(loop_a_line.lstrip())
        indent_b = len(loop_b_line) - len(loop_b_line.lstrip())
        
        # Second loop should be more indented than first
        self.assertGreater(
            indent_b,
            indent_a,
            "Second parameter loop should be more indented than first"
        )



class ChildCallArgsAccumulationTests(unittest.TestCase):
    """
    Tests for child scope call arguments accumulation.

    **Validates: Requirements 6.4**
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

    def test_parameter_added_to_child_scope_call_args(self):
        """
        Verify session parameter is added to child scope call arguments.

        **Validates: Requirements 6.4**
        """
        test_tree = create_test_tree_with_single_module("test_module")
        add_session_parameter(test_tree, "session_resource", sample_factory_func)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        result = sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        # Check the returned scopes_called list
        self.assertEqual(len(result), 1, "Should have one child scope")
        
        scope_module, scope_name, scope_node, scope_call_args = result[0]
        
        self.assertIn(
            "session_resource",
            scope_call_args,
            "Session parameter should be in child scope call args"
        )


    def test_multiple_parameters_added_to_child_scope_call_args(self):
        """
        Verify multiple session parameters are added to child scope call arguments.

        **Validates: Requirements 6.4**
        """
        test_tree = create_test_tree_with_single_module("test_module")
        add_session_parameter(test_tree, "param_a", sample_factory_func)
        add_session_parameter(test_tree, "param_b", another_factory_func)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        result = sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        scope_module, scope_name, scope_node, scope_call_args = result[0]
        
        self.assertIn("param_a", scope_call_args, "First parameter should be in call args")
        self.assertIn("param_b", scope_call_args, "Second parameter should be in call args")

    def test_sequencer_always_first_in_child_scope_call_args(self):
        """
        Verify sequencer is always the first argument in child scope call args.

        **Validates: Requirements 6.4**
        """
        test_tree = create_test_tree_with_single_module("test_module")
        add_session_parameter(test_tree, "session_resource", sample_factory_func)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        result = sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        scope_module, scope_name, scope_node, scope_call_args = result[0]
        
        self.assertEqual(
            scope_call_args[0],
            "sequencer",
            "Sequencer should be the first argument in child scope call args"
        )

    def test_child_scope_function_call_includes_parameters(self):
        """
        Verify generated child scope function call includes session parameters.

        **Validates: Requirements 6.4**
        """
        test_tree = create_test_tree_with_single_module("test_module")
        add_session_parameter(test_tree, "session_resource", sample_factory_func)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        # Verify the child scope call includes the parameter
        self.assertIn(
            "scope_test_module(sequencer, session_resource)",
            generated_code,
            "Child scope call should include session parameter"
        )


    def test_child_scope_function_call_includes_multiple_parameters(self):
        """
        Verify generated child scope function call includes multiple session parameters.

        **Validates: Requirements 6.4**
        """
        test_tree = create_test_tree_with_single_module("test_module")
        add_session_parameter(test_tree, "param_a", sample_factory_func)
        add_session_parameter(test_tree, "param_b", another_factory_func)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        # Verify the child scope call includes both parameters
        self.assertIn(
            "scope_test_module(sequencer, param_a, param_b)",
            generated_code,
            "Child scope call should include all session parameters"
        )


class ImpliedParameterSkippingTests(unittest.TestCase):
    """
    Tests for implied parameter skipping.

    **Validates: Requirements 6.5**
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


    def test_implied_parameter_import_not_generated(self):
        """
        Verify import statement is not generated for implied parameters.

        **Validates: Requirements 6.5**
        """
        test_tree = create_minimal_test_tree()
        add_session_parameter(test_tree, "implied_param", sample_factory_func, implied=True)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        # Verify import statement is NOT generated for implied parameter
        import_statement = "from {} import {}".format(
            sample_factory_func.__module__,
            sample_factory_func.__name__
        )
        self.assertNotIn(
            import_statement,
            generated_code,
            "Import should not be generated for implied parameter"
        )

    def test_implied_parameter_for_loop_not_generated(self):
        """
        Verify for loop is not generated for implied parameters.

        **Validates: Requirements 6.5**
        """
        test_tree = create_minimal_test_tree()
        add_session_parameter(test_tree, "implied_param", sample_factory_func, implied=True)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        # Verify for loop is NOT generated for implied parameter
        self.assertNotIn(
            "for implied_param in",
            generated_code,
            "For loop should not be generated for implied parameter"
        )

    def test_implied_parameter_not_added_to_child_call_args(self):
        """
        Verify implied parameters are not added to child scope call arguments.

        **Validates: Requirements 6.5**
        """
        test_tree = create_test_tree_with_single_module("test_module")
        add_session_parameter(test_tree, "implied_param", sample_factory_func, implied=True)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        result = sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        scope_module, scope_name, scope_node, scope_call_args = result[0]
        
        self.assertNotIn(
            "implied_param",
            scope_call_args,
            "Implied parameter should not be in child scope call args"
        )


    def test_non_implied_parameter_generated_when_implied_present(self):
        """
        Verify non-implied parameters are still generated when implied parameters are present.

        **Validates: Requirements 6.5**
        """
        test_tree = create_test_tree_with_single_module("test_module")
        add_session_parameter(test_tree, "implied_param", sample_factory_func, implied=True)
        add_session_parameter(test_tree, "regular_param", another_factory_func, implied=False)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        result = sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        scope_module, scope_name, scope_node, scope_call_args = result[0]
        
        # Verify non-implied parameter is generated
        self.assertIn(
            "for regular_param in",
            generated_code,
            "For loop should be generated for non-implied parameter"
        )
        
        # Verify non-implied parameter is in call args
        self.assertIn(
            "regular_param",
            scope_call_args,
            "Non-implied parameter should be in child scope call args"
        )
        
        # Verify implied parameter is NOT in call args
        self.assertNotIn(
            "implied_param",
            scope_call_args,
            "Implied parameter should not be in child scope call args"
        )

    def test_mixed_implied_and_non_implied_parameters(self):
        """
        Verify correct handling of mixed implied and non-implied parameters.

        **Validates: Requirements 6.5**
        """
        test_tree = create_test_tree_with_single_module("test_module")
        add_session_parameter(test_tree, "param_a", sample_factory_func, implied=False)
        add_session_parameter(test_tree, "implied_b", another_factory_func, implied=True)
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        # Verify only non-implied parameter has for loop
        self.assertIn("for param_a in", generated_code)
        self.assertNotIn("for implied_b in", generated_code)
        
        # Verify only non-implied parameter import is generated
        import_a = "from {} import {}".format(
            sample_factory_func.__module__,
            sample_factory_func.__name__
        )
        import_b = "from {} import {}".format(
            another_factory_func.__module__,
            another_factory_func.__name__
        )
        
        self.assertIn(import_a, generated_code)
        self.assertNotIn(import_b, generated_code)


if __name__ == "__main__":
    unittest.main()
