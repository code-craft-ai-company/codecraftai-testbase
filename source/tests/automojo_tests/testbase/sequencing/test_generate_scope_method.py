"""
    Unit tests for _generate_scope_method private method.

    Tests verify the scope method generation including function signature with
    parameters, docstring content with scope name, module scope context generation,
    return statement generation, and scopes_called list return value.

    Requirements covered:
    - 9.1: Generate scope_{name}(sequencer, ...) function for each TestGroup
    - 9.2: Scope function signature includes all parameters passed from parent scopes
    - 9.3: Scope function includes docstring indicating scope name
    - 9.4: Scope function contains enter_module_scope_context context manager
    - 9.5: Scope function ends with return statement
    - 9.6: _generate_scope_method returns list of child scopes to be generated
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


def create_scope_node_with_multiple_children(name, child_names, package=None):
    """
    Create a scope node with multiple child modules.
    
    Args:
        name: Name of the parent scope
        child_names: List of child module names
        package: Optional package path for parent
        
    Returns:
        MockTestGroup: Parent scope with multiple child modules
    """
    parent = MockTestGroup(name, package=package)
    for child_name in child_names:
        child = MockTestGroup(child_name, package="")
        parent._children[child_name] = child
    return parent


class ScopeMethodFunctionSignatureTests(unittest.TestCase):
    """
    Tests for scope method function signature generation.

    **Validates: Requirements 9.1, 9.2**
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

    def test_scope_function_signature_generated(self):
        """
        Verify scope function signature is generated with correct name pattern.

        **Validates: Requirements 9.1**
        """
        scope_node = create_scope_node("test_module")
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
            'def scope_test_module(sequencer):',
            generated_code,
            "Generated code should contain scope function signature"
        )

    def test_scope_function_signature_with_underscores(self):
        """
        Verify scope function name replaces dots with underscores.

        **Validates: Requirements 9.1**
        """
        scope_node = create_scope_node("submodule", package="package")
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, "package.submodule", "package_submodule", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            'def scope_package_submodule(sequencer):',
            generated_code,
            "Scope function name should replace dots with underscores"
        )

    def test_scope_function_includes_sequencer_parameter(self):
        """
        Verify scope function signature includes sequencer parameter.

        **Validates: Requirements 9.2**
        """
        scope_node = create_scope_node("test_module")
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
            'sequencer',
            generated_code.split('\n')[0],
            "Scope function should include sequencer parameter"
        )

    def test_scope_function_includes_parent_parameters(self):
        """
        Verify scope function signature includes all parameters from parent scopes.

        **Validates: Requirements 9.2**
        """
        scope_node = create_scope_node("test_module")
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer", "session_param", "another_param"]
        
        sequencer._generate_scope_method(
            output_buffer, "test_module", "test_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            'def scope_test_module(sequencer, session_param, another_param):',
            generated_code,
            "Scope function should include all parent parameters"
        )

    def test_scope_function_signature_is_first_line(self):
        """
        Verify scope function signature appears at the start of generated code.

        **Validates: Requirements 9.1**
        """
        scope_node = create_scope_node("test_module")
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
        
        self.assertTrue(
            lines[0].startswith('def scope_'),
            "First line should be the scope function signature"
        )



class ScopeMethodDocstringTests(unittest.TestCase):
    """
    Tests for scope method docstring content.

    **Validates: Requirements 9.3**
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

    def test_scope_function_has_docstring(self):
        """
        Verify scope function includes a docstring.

        **Validates: Requirements 9.3**
        """
        scope_node = create_scope_node("test_module")
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
            '"""',
            generated_code,
            "Generated code should contain docstring delimiters"
        )

    def test_docstring_contains_scope_name(self):
        """
        Verify docstring indicates the scope name.

        **Validates: Requirements 9.3**
        """
        scope_node = create_scope_node("my_test_module")
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, "my_test_module", "my_test_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            "my_test_module",
            generated_code,
            "Docstring should contain the scope name"
        )

    def test_docstring_indicates_entry_point(self):
        """
        Verify docstring indicates this is the entry point for the test scope.

        **Validates: Requirements 9.3**
        """
        scope_node = create_scope_node("test_module")
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
            'entry point',
            generated_code,
            "Docstring should indicate this is the entry point"
        )
        self.assertIn(
            'test scope',
            generated_code,
            "Docstring should mention test scope"
        )

    def test_docstring_follows_function_signature(self):
        """
        Verify docstring appears immediately after function signature.

        **Validates: Requirements 9.3**
        """
        scope_node = create_scope_node("test_module")
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
        
        # Find the function signature line
        sig_index = None
        for i, line in enumerate(lines):
            if line.startswith('def scope_'):
                sig_index = i
                break
        
        self.assertIsNotNone(sig_index, "Function signature should be found")
        
        # The next line should start the docstring
        self.assertTrue(
            lines[sig_index + 1].strip().startswith('"""'),
            "Docstring should immediately follow function signature"
        )



class ModuleScopeContextTests(unittest.TestCase):
    """
    Tests for module scope context generation.

    **Validates: Requirements 9.4**
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

    def test_module_scope_context_generated(self):
        """
        Verify module scope context manager is generated.

        **Validates: Requirements 9.4**
        """
        scope_node = create_scope_node("test_module")
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
            'with sequencer.enter_module_scope_context("test_module") as msc:',
            generated_code,
            "Generated code should contain module scope context manager"
        )

    def test_module_scope_context_uses_with_statement(self):
        """
        Verify module scope context uses 'with' statement.

        **Validates: Requirements 9.4**
        """
        scope_node = create_scope_node("test_module")
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
            'with sequencer.enter_module_scope_context(',
            generated_code,
            "Module scope context should use 'with' statement"
        )

    def test_module_scope_context_assigns_to_msc(self):
        """
        Verify module scope context is assigned to 'msc' variable.

        **Validates: Requirements 9.4**
        """
        scope_node = create_scope_node("test_module")
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
            'as msc:',
            generated_code,
            "Module scope context should be assigned to 'msc'"
        )

    def test_module_scope_context_uses_scope_module_name(self):
        """
        Verify module scope context uses the fully qualified module name.

        **Validates: Requirements 9.4**
        """
        scope_node = create_scope_node("submodule", package="package")
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        sequencer._generate_scope_method(
            output_buffer, "package.submodule", "package_submodule", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            'enter_module_scope_context("package.submodule")',
            generated_code,
            "Module scope context should use fully qualified module name"
        )

    def test_module_scope_context_is_indented(self):
        """
        Verify module scope context is properly indented.

        **Validates: Requirements 9.4**
        """
        scope_node = create_scope_node("test_module")
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
        
        # Find the context manager line
        context_line = None
        for line in lines:
            if 'enter_module_scope_context(' in line:
                context_line = line
                break
        
        self.assertIsNotNone(context_line, "Context manager line should be found")
        self.assertTrue(
            context_line.startswith(indent_space),
            "Module scope context should be indented"
        )



class ScopeMethodReturnStatementTests(unittest.TestCase):
    """
    Tests for scope method return statement generation.

    **Validates: Requirements 9.5**
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

    def test_scope_function_has_return_statement(self):
        """
        Verify scope function ends with a return statement.

        **Validates: Requirements 9.5**
        """
        scope_node = create_scope_node("test_module")
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
            'return',
            generated_code,
            "Generated code should contain return statement"
        )

    def test_return_statement_is_indented(self):
        """
        Verify return statement is properly indented.

        **Validates: Requirements 9.5**
        """
        scope_node = create_scope_node("test_module")
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
        
        # Find the return statement line
        return_line = None
        for line in lines:
            if line.strip() == 'return':
                return_line = line
                break
        
        self.assertIsNotNone(return_line, "Return statement should be found")
        self.assertTrue(
            return_line.startswith(indent_space),
            "Return statement should be indented"
        )

    def test_return_statement_is_bare_return(self):
        """
        Verify return statement is a bare return (no value).

        **Validates: Requirements 9.5**
        """
        scope_node = create_scope_node("test_module")
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
        
        # Find the return statement line
        return_line = None
        for line in lines:
            if 'return' in line and line.strip() == 'return':
                return_line = line
                break
        
        self.assertIsNotNone(
            return_line,
            "Bare return statement should be found"
        )



class ScopesCalledReturnValueTests(unittest.TestCase):
    """
    Tests for scopes_called list return value.

    **Validates: Requirements 9.6**
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

    def test_returns_list(self):
        """
        Verify _generate_scope_method returns a list.

        **Validates: Requirements 9.6**
        """
        scope_node = create_scope_node("test_module")
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        result = sequencer._generate_scope_method(
            output_buffer, "test_module", "test_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        self.assertIsInstance(
            result,
            list,
            "_generate_scope_method should return a list"
        )

    def test_returns_empty_list_for_empty_scope(self):
        """
        Verify returns empty list when scope has no children.

        **Validates: Requirements 9.6**
        """
        scope_node = create_scope_node("test_module")
        sequencer = self._create_sequencer()
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        scope_call_args = ["sequencer"]
        
        result = sequencer._generate_scope_method(
            output_buffer, "test_module", "test_module", scope_node,
            scope_call_args, factory_imports, constraint_imports, indent_space
        )
        
        self.assertEqual(
            len(result),
            0,
            "Should return empty list when scope has no children"
        )

    def test_returns_one_scope_for_single_child_module(self):
        """
        Verify returns one scope tuple when scope has one child module.

        **Validates: Requirements 9.6**
        """
        scope_node = create_scope_node_with_child_module("parent_module", "child_module")
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
        
        self.assertEqual(
            len(result),
            1,
            "Should return one scope when scope has one child module"
        )

    def test_returns_multiple_scopes_for_multiple_children(self):
        """
        Verify returns multiple scope tuples when scope has multiple child modules.

        **Validates: Requirements 9.6**
        """
        scope_node = create_scope_node_with_multiple_children(
            "parent_module", 
            ["child_a", "child_b", "child_c"]
        )
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
        
        self.assertEqual(
            len(result),
            3,
            "Should return three scopes when scope has three child modules"
        )

    def test_scope_tuple_contains_four_elements(self):
        """
        Verify each scope tuple contains four elements.

        **Validates: Requirements 9.6**
        """
        scope_node = create_scope_node_with_child_module("parent_module", "child_module")
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
        
        self.assertEqual(
            len(result[0]),
            4,
            "Each scope tuple should contain four elements"
        )

    def test_scope_tuple_contains_scope_module(self):
        """
        Verify scope tuple contains the scope module name.

        **Validates: Requirements 9.6**
        """
        scope_node = create_scope_node_with_child_module("parent_module", "child_module")
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
        
        self.assertEqual(
            scope_module,
            "child_module",
            "First element should be the scope module name"
        )

    def test_scope_tuple_contains_scope_name(self):
        """
        Verify scope tuple contains the scope function name.

        **Validates: Requirements 9.6**
        """
        scope_node = create_scope_node_with_child_module("parent_module", "child_module")
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
        
        self.assertEqual(
            scope_name,
            "child_module",
            "Second element should be the scope function name"
        )

    def test_scope_tuple_contains_scope_node(self):
        """
        Verify scope tuple contains the scope node (TestGroup).

        **Validates: Requirements 9.6**
        """
        scope_node = create_scope_node_with_child_module("parent_module", "child_module")
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
        
        self.assertIsInstance(
            scope_node_result,
            TestGroup,
            "Third element should be a TestGroup instance"
        )

    def test_scope_tuple_contains_call_args(self):
        """
        Verify scope tuple contains the call arguments list.

        **Validates: Requirements 9.6**
        """
        scope_node = create_scope_node_with_child_module("parent_module", "child_module")
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
        
        self.assertIsInstance(
            scope_call_args_result,
            list,
            "Fourth element should be a list of call arguments"
        )
        self.assertIn(
            "sequencer",
            scope_call_args_result,
            "Call args should include sequencer"
        )
        self.assertIn(
            "session_param",
            scope_call_args_result,
            "Call args should include parent parameters"
        )


if __name__ == '__main__':
    unittest.main()
