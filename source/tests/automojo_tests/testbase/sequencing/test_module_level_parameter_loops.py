"""
    Unit tests for module-level parameter loop generation.

    Tests verify the module-level parameter loop generation including factory
    import addition to set, for loop generation, parameter nesting within
    module scope, child call args accumulation, and import format.

    Requirements covered:
    - 10.1: Add factory imports to the factory_imports set
    - 10.2: Generate for loops iterating over factory function calls
    - 10.3: Parameter loops nested within module scope context
    - 10.4: Parameter variable names added to child scope call arguments
    - 10.5: Factory import format is `from {module} import {function}`
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

def module_factory_func():
    """Sample module-level factory function for testing."""
    yield "module_resource"


def another_module_factory_func():
    """Another module-level factory function for testing multiple parameters."""
    yield "another_module_resource"


def factory_with_constraints(constraints):
    """Factory function with constraints parameter."""
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


def create_scope_node_with_child_module(name, child_name, package=None, child_package=None):
    """
    Create a scope node with a child module (TestGroup).
    
    Args:
        name: Name of the parent scope
        child_name: Name of the child module
        package: Optional package path for parent
        child_package: Optional package path for child
        
    Returns:
        MockTestGroup: Parent scope with one child module
    """
    parent = MockTestGroup(name, package=package)
    child = MockTestGroup(child_name, package=child_package)
    parent._children[child_name] = child
    return parent


def add_module_parameter(scope_node, param_name, factory_func, implied=False, constraints=None):
    """
    Add a module-level parameter origination to the scope node.
    
    Args:
        scope_node: The MockTestGroup to add the parameter to
        param_name: Name of the parameter
        factory_func: The factory function to use
        implied: Whether the parameter is implied (default False)
        constraints: Optional constraints dictionary
        
    Returns:
        ResourceOrigin: The created resource origin
    """
    source = MockSourceBase(factory_func)
    origin = ResourceOrigin(
        scope_node.name,
        param_name,
        ResourceLifespan.Test,
        source,
        implied=implied,
        constraints=constraints
    )
    scope_node._mock_scope.parameter_originations[param_name] = origin
    return origin


# ============================================================================
# TEST CLASSES
# ============================================================================

class ModuleParameterFactoryImportTests(unittest.TestCase):
    """
    Tests for module-level parameter factory import addition to set.

    **Validates: Requirements 10.1, 10.5**
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

    def test_factory_import_added_to_set_for_module_parameter(self):
        """
        Verify factory import is added to factory_imports set for module-scoped parameter.

        **Validates: Requirements 10.1**
        """
        scope_node = create_scope_node("test_module")
        add_module_parameter(scope_node, "module_resource", module_factory_func)
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
        
        # Verify factory import was added to the set
        expected_import = "from {} import {}".format(
            module_factory_func.__module__,
            module_factory_func.__name__
        )
        self.assertIn(
            expected_import,
            factory_imports,
            "Factory import should be added to factory_imports set"
        )

    def test_multiple_factory_imports_added_to_set(self):
        """
        Verify multiple factory imports are added to factory_imports set.

        **Validates: Requirements 10.1**
        """
        scope_node = create_scope_node("test_module")
        add_module_parameter(scope_node, "resource_a", module_factory_func)
        add_module_parameter(scope_node, "resource_b", another_module_factory_func)
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
        
        # Verify both factory imports were added
        import_a = "from {} import {}".format(
            module_factory_func.__module__,
            module_factory_func.__name__
        )
        import_b = "from {} import {}".format(
            another_module_factory_func.__module__,
            another_module_factory_func.__name__
        )
        
        self.assertIn(import_a, factory_imports, "First factory import should be in set")
        self.assertIn(import_b, factory_imports, "Second factory import should be in set")

    def test_factory_import_format_is_correct(self):
        """
        Verify factory import uses format `from {module} import {function}`.

        **Validates: Requirements 10.5**
        """
        scope_node = create_scope_node("test_module")
        add_module_parameter(scope_node, "module_resource", module_factory_func)
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
        
        # Verify the import format
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

    def test_factory_import_contains_module_path(self):
        """
        Verify factory import contains the correct module path.

        **Validates: Requirements 10.5**
        """
        scope_node = create_scope_node("test_module")
        add_module_parameter(scope_node, "module_resource", module_factory_func)
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
        
        # Verify the module path is in the import
        found_import = None
        for import_stmt in factory_imports:
            if module_factory_func.__name__ in import_stmt:
                found_import = import_stmt
                break
        
        self.assertIsNotNone(found_import, "Should find import for factory function")
        self.assertIn(
            module_factory_func.__module__,
            found_import,
            "Import should contain the correct module path"
        )

    def test_factory_import_contains_function_name(self):
        """
        Verify factory import contains the correct function name.

        **Validates: Requirements 10.5**
        """
        scope_node = create_scope_node("test_module")
        add_module_parameter(scope_node, "module_resource", module_factory_func)
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
        
        # Verify the function name is in the import
        found_import = None
        for import_stmt in factory_imports:
            if module_factory_func.__name__ in import_stmt:
                found_import = import_stmt
                break
        
        self.assertIsNotNone(found_import, "Should find import for factory function")
        self.assertIn(
            module_factory_func.__name__,
            found_import,
            "Import should contain the function name"
        )


class ModuleParameterForLoopTests(unittest.TestCase):
    """
    Tests for module-level parameter for loop generation.

    **Validates: Requirements 10.2**
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

    def test_for_loop_generated_for_module_parameter(self):
        """
        Verify for loop is generated for module-scoped parameter.

        **Validates: Requirements 10.2**
        """
        scope_node = create_scope_node("test_module")
        add_module_parameter(scope_node, "module_resource", module_factory_func)
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
        
        # Verify for loop is generated with parameter name and factory call
        expected_loop = "for module_resource in {}():".format(module_factory_func.__name__)
        self.assertIn(
            expected_loop,
            generated_code,
            "Generated code should contain for loop iterating over factory function"
        )

    def test_for_loop_uses_parameter_name_as_variable(self):
        """
        Verify for loop uses the parameter name as the loop variable.

        **Validates: Requirements 10.2**
        """
        scope_node = create_scope_node("test_module")
        add_module_parameter(scope_node, "my_custom_module_param", module_factory_func)
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
        
        # Verify the parameter name is used as the loop variable
        self.assertIn(
            "for my_custom_module_param in",
            generated_code,
            "For loop should use parameter name as loop variable"
        )

    def test_multiple_for_loops_generated_for_multiple_parameters(self):
        """
        Verify multiple for loops are generated for multiple module parameters.

        **Validates: Requirements 10.2**
        """
        scope_node = create_scope_node("test_module")
        add_module_parameter(scope_node, "param_a", module_factory_func)
        add_module_parameter(scope_node, "param_b", another_module_factory_func)
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

    def test_for_loop_calls_factory_function(self):
        """
        Verify for loop calls the factory function.

        **Validates: Requirements 10.2**
        """
        scope_node = create_scope_node("test_module")
        add_module_parameter(scope_node, "module_resource", module_factory_func)
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
        
        # Verify the factory function is called in the for loop
        self.assertIn(
            "{}()".format(module_factory_func.__name__),
            generated_code,
            "For loop should call the factory function"
        )


class ModuleParameterNestingTests(unittest.TestCase):
    """
    Tests for parameter loop nesting within module scope context.

    **Validates: Requirements 10.3**
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

    def test_parameter_loop_nested_within_module_scope(self):
        """
        Verify parameter loop is nested within module scope context.

        **Validates: Requirements 10.3**
        """
        scope_node = create_scope_node("test_module")
        add_module_parameter(scope_node, "module_resource", module_factory_func)
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
        
        # Find the module scope context line and the for loop line
        scope_context_index = None
        for_loop_index = None
        
        for i, line in enumerate(lines):
            if 'enter_module_scope_context(' in line:
                scope_context_index = i
            if 'for module_resource in' in line:
                for_loop_index = i
        
        self.assertIsNotNone(scope_context_index, "Module scope context should be found")
        self.assertIsNotNone(for_loop_index, "For loop should be found")
        
        # Verify for loop comes after module scope context
        self.assertGreater(
            for_loop_index,
            scope_context_index,
            "For loop should appear after module scope context"
        )

    def test_parameter_loop_indented_within_module_scope(self):
        """
        Verify parameter loop is properly indented within module scope.

        **Validates: Requirements 10.3**
        """
        scope_node = create_scope_node("test_module")
        add_module_parameter(scope_node, "module_resource", module_factory_func)
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
        
        # Find the for loop line
        for_loop_line = None
        for line in lines:
            if 'for module_resource in' in line:
                for_loop_line = line
                break
        
        self.assertIsNotNone(for_loop_line, "For loop line should be found")
        
        # Verify the for loop is indented (at least 2 levels: function + scope context)
        expected_indent = indent_space * 2  # Two levels of indentation
        self.assertTrue(
            for_loop_line.startswith(expected_indent),
            "For loop should be indented within module scope context"
        )

    def test_nested_parameter_loops_have_increasing_indentation(self):
        """
        Verify nested parameter loops have increasing indentation levels.

        **Validates: Requirements 10.3**
        """
        scope_node = create_scope_node("test_module")
        add_module_parameter(scope_node, "param_a", module_factory_func)
        add_module_parameter(scope_node, "param_b", another_module_factory_func)
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

    **Validates: Requirements 10.4**
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

    def test_module_parameter_added_to_child_scope_call_args(self):
        """
        Verify module parameter is added to child scope call arguments.

        **Validates: Requirements 10.4**
        """
        scope_node = create_scope_node_with_child_module("parent_module", "child_module")
        add_module_parameter(scope_node, "module_resource", module_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        result = sequencer._generate_scope_method(
            output_buffer, "parent_module", "parent_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        # Check the returned scopes_called list
        self.assertEqual(len(result), 1, "Should have one child scope")
        
        scope_module, scope_name, scope_node_result, scope_call_args_result = result[0]
        
        self.assertIn(
            "module_resource",
            scope_call_args_result,
            "Module parameter should be in child scope call args"
        )

    def test_multiple_module_parameters_added_to_child_scope_call_args(self):
        """
        Verify multiple module parameters are added to child scope call arguments.

        **Validates: Requirements 10.4**
        """
        scope_node = create_scope_node_with_child_module("parent_module", "child_module")
        add_module_parameter(scope_node, "param_a", module_factory_func)
        add_module_parameter(scope_node, "param_b", another_module_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        result = sequencer._generate_scope_method(
            output_buffer, "parent_module", "parent_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        scope_module, scope_name, scope_node_result, scope_call_args_result = result[0]
        
        self.assertIn("param_a", scope_call_args_result, "First parameter should be in call args")
        self.assertIn("param_b", scope_call_args_result, "Second parameter should be in call args")

    def test_parent_args_preserved_in_child_scope_call_args(self):
        """
        Verify parent scope arguments are preserved in child scope call args.

        **Validates: Requirements 10.4**
        """
        scope_node = create_scope_node_with_child_module("parent_module", "child_module")
        add_module_parameter(scope_node, "module_resource", module_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer", "session_param"]
        
        result = sequencer._generate_scope_method(
            output_buffer, "parent_module", "parent_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        scope_module, scope_name, scope_node_result, scope_call_args_result = result[0]
        
        self.assertIn(
            "sequencer",
            scope_call_args_result,
            "Sequencer should be preserved in child scope call args"
        )
        self.assertIn(
            "session_param",
            scope_call_args_result,
            "Session parameter should be preserved in child scope call args"
        )

    def test_child_scope_function_call_includes_module_parameters(self):
        """
        Verify generated child scope function call includes module parameters.

        **Validates: Requirements 10.4**
        """
        scope_node = create_scope_node_with_child_module("parent_module", "child_module")
        add_module_parameter(scope_node, "module_resource", module_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, "parent_module", "parent_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        # Verify the child scope call includes the parameter
        self.assertIn(
            "scope_child_module(sequencer, module_resource)",
            generated_code,
            "Child scope call should include module parameter"
        )

    def test_child_scope_function_call_includes_all_parameters(self):
        """
        Verify generated child scope function call includes all accumulated parameters.

        **Validates: Requirements 10.4**
        """
        scope_node = create_scope_node_with_child_module("parent_module", "child_module")
        add_module_parameter(scope_node, "param_a", module_factory_func)
        add_module_parameter(scope_node, "param_b", another_module_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer", "session_param"]
        
        sequencer._generate_scope_method(
            output_buffer, "parent_module", "parent_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        # Verify the child scope call includes all parameters
        self.assertIn(
            "scope_child_module(sequencer, session_param, param_a, param_b)",
            generated_code,
            "Child scope call should include all accumulated parameters"
        )

    def test_parameters_added_in_order(self):
        """
        Verify parameters are added to child call args in order of origination.

        **Validates: Requirements 10.4**
        """
        scope_node = create_scope_node_with_child_module("parent_module", "child_module")
        add_module_parameter(scope_node, "first_param", module_factory_func)
        add_module_parameter(scope_node, "second_param", another_module_factory_func)
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        result = sequencer._generate_scope_method(
            output_buffer, "parent_module", "parent_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        scope_module, scope_name, scope_node_result, scope_call_args_result = result[0]
        
        # Find the indices of the parameters
        first_index = scope_call_args_result.index("first_param")
        second_index = scope_call_args_result.index("second_param")
        
        self.assertLess(
            first_index,
            second_index,
            "Parameters should be added in order of origination"
        )


if __name__ == '__main__':
    unittest.main()
