"""
    Unit tests for _generate_session_method private method.

    Tests verify the session method generation including function signature,
    docstring content, session scope context, return statement, and scopes_called
    list return value.

    Requirements covered:
    - 5.1: Generate session(sequencer) function as entry point
    - 5.2: Session function includes docstring indicating entry point
    - 5.3: Session function contains enter_session_scope_context context manager
    - 5.4: Session function ends with return statement
    - 5.5: _generate_session_method returns list of child scopes to be generated
"""

import collections
import io
import os
import tempfile
import unittest

from ccai.testbase.testgroup import TestGroup
from ccai.testbase.injection.injectionregistry import injection_registry
from ccai.testbase.injection.injectionscope import InjectionScope
from ccai.testbase.sequencing.testsequencer import TestSequencer


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


def create_test_function(name, module_name):
    """Create a mock test function with the given name and module."""
    def test_func():
        pass
    test_func.__name__ = name
    test_func.__module__ = module_name
    return test_func


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


def create_test_tree_with_multiple_modules(module_names):
    """
    Create a test tree with multiple modules (no tests).
    
    Args:
        module_names: List of module names
        
    Returns:
        MockTestGroup: Root of the test tree with multiple child modules
    """
    root = MockTestGroup("root")
    for module_name in module_names:
        module_group = MockTestGroup(module_name, package="")
        root._children[module_name] = module_group
    return root


class SessionMethodFunctionSignatureTests(unittest.TestCase):
    """
    Tests for session method function signature generation.

    **Validates: Requirements 5.1**
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

    def test_session_function_signature_generated(self):
        """
        Verify session function signature is generated correctly.

        **Validates: Requirements 5.1**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            'def session(sequencer):',
            generated_code,
            "Generated code should contain session function signature"
        )

    def test_session_function_signature_is_first_line(self):
        """
        Verify session function signature appears at the start of generated code.

        **Validates: Requirements 5.1**
        """
        test_tree = create_minimal_test_tree()
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
        
        self.assertEqual(
            lines[0],
            'def session(sequencer):',
            "First line should be the session function signature"
        )

    def test_session_function_takes_sequencer_parameter(self):
        """
        Verify session function takes sequencer as its only parameter.

        **Validates: Requirements 5.1**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        # Verify the function signature has exactly one parameter: sequencer
        self.assertIn(
            'def session(sequencer):',
            generated_code,
            "Session function should take exactly one parameter: sequencer"
        )
        # Verify no additional parameters
        self.assertNotIn(
            'def session(sequencer,',
            generated_code,
            "Session function should not have additional parameters"
        )


class SessionMethodDocstringTests(unittest.TestCase):
    """
    Tests for session method docstring content.

    **Validates: Requirements 5.2**
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

    def test_session_function_has_docstring(self):
        """
        Verify session function includes a docstring.

        **Validates: Requirements 5.2**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            '"""',
            generated_code,
            "Generated code should contain docstring delimiters"
        )

    def test_docstring_indicates_entry_point(self):
        """
        Verify docstring indicates this is the entry point for test run sequence document.

        **Validates: Requirements 5.2**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            'entry point',
            generated_code,
            "Docstring should indicate this is the entry point"
        )
        self.assertIn(
            'test run sequence document',
            generated_code,
            "Docstring should mention test run sequence document"
        )

    def test_docstring_follows_function_signature(self):
        """
        Verify docstring appears immediately after function signature.

        **Validates: Requirements 5.2**
        """
        test_tree = create_minimal_test_tree()
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
        
        # Find the function signature line
        sig_index = None
        for i, line in enumerate(lines):
            if line == 'def session(sequencer):':
                sig_index = i
                break
        
        self.assertIsNotNone(sig_index, "Function signature should be found")
        
        # The next line should start the docstring
        self.assertTrue(
            lines[sig_index + 1].strip().startswith('"""'),
            "Docstring should immediately follow function signature"
        )


class SessionScopeContextTests(unittest.TestCase):
    """
    Tests for session scope context generation.

    **Validates: Requirements 5.3**
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

    def test_session_scope_context_generated(self):
        """
        Verify session scope context manager is generated.

        **Validates: Requirements 5.3**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            'with sequencer.enter_session_scope_context() as ssc:',
            generated_code,
            "Generated code should contain session scope context manager"
        )

    def test_session_scope_context_uses_with_statement(self):
        """
        Verify session scope context uses 'with' statement.

        **Validates: Requirements 5.3**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        # Verify the context manager uses 'with' statement
        self.assertIn(
            'with sequencer.enter_session_scope_context()',
            generated_code,
            "Session scope context should use 'with' statement"
        )

    def test_session_scope_context_assigns_to_ssc(self):
        """
        Verify session scope context is assigned to 'ssc' variable.

        **Validates: Requirements 5.3**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        generated_code = output_buffer.getvalue()
        
        self.assertIn(
            'as ssc:',
            generated_code,
            "Session scope context should be assigned to 'ssc'"
        )

    def test_session_scope_context_is_indented(self):
        """
        Verify session scope context is properly indented.

        **Validates: Requirements 5.3**
        """
        test_tree = create_minimal_test_tree()
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
        
        # Find the context manager line
        context_line = None
        for line in lines:
            if 'enter_session_scope_context()' in line:
                context_line = line
                break
        
        self.assertIsNotNone(context_line, "Context manager line should be found")
        self.assertTrue(
            context_line.startswith(indent_space),
            "Session scope context should be indented"
        )


class SessionMethodReturnStatementTests(unittest.TestCase):
    """
    Tests for session method return statement generation.

    **Validates: Requirements 5.4**
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

    def test_session_function_has_return_statement(self):
        """
        Verify session function ends with a return statement.

        **Validates: Requirements 5.4**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
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

        **Validates: Requirements 5.4**
        """
        test_tree = create_minimal_test_tree()
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

        **Validates: Requirements 5.4**
        """
        test_tree = create_minimal_test_tree()
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

    **Validates: Requirements 5.5**
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

    def test_returns_list(self):
        """
        Verify _generate_session_method returns a list.

        **Validates: Requirements 5.5**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        result = sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        self.assertIsInstance(
            result,
            list,
            "_generate_session_method should return a list"
        )

    def test_returns_empty_list_for_empty_tree(self):
        """
        Verify returns empty list when root has no children.

        **Validates: Requirements 5.5**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        result = sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        self.assertEqual(
            len(result),
            0,
            "Should return empty list when root has no children"
        )

    def test_returns_one_scope_for_single_child(self):
        """
        Verify returns one scope tuple when root has one child.

        **Validates: Requirements 5.5**
        """
        test_tree = create_test_tree_with_single_module("test_module")
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        result = sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        self.assertEqual(
            len(result),
            1,
            "Should return one scope when root has one child"
        )

    def test_returns_multiple_scopes_for_multiple_children(self):
        """
        Verify returns multiple scope tuples when root has multiple children.

        **Validates: Requirements 5.5**
        """
        test_tree = create_test_tree_with_multiple_modules(["module_a", "module_b", "module_c"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        result = sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        self.assertEqual(
            len(result),
            3,
            "Should return three scopes when root has three children"
        )

    def test_scope_tuple_contains_four_elements(self):
        """
        Verify each scope tuple contains four elements.

        **Validates: Requirements 5.5**
        """
        test_tree = create_test_tree_with_single_module("test_module")
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        result = sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        self.assertEqual(
            len(result[0]),
            4,
            "Each scope tuple should contain four elements"
        )

    def test_scope_tuple_contains_scope_module(self):
        """
        Verify scope tuple contains the scope module name.

        **Validates: Requirements 5.5**
        """
        test_tree = create_test_tree_with_single_module("test_module")
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
            scope_module,
            "test_module",
            "First element should be the scope module name"
        )

    def test_scope_tuple_contains_scope_name(self):
        """
        Verify scope tuple contains the scope function name.

        **Validates: Requirements 5.5**
        """
        test_tree = create_test_tree_with_single_module("test_module")
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
            scope_name,
            "test_module",
            "Second element should be the scope function name"
        )

    def test_scope_tuple_contains_scope_node(self):
        """
        Verify scope tuple contains the scope node (TestGroup).

        **Validates: Requirements 5.5**
        """
        test_tree = create_test_tree_with_single_module("test_module")
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        result = sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        scope_module, scope_name, scope_node, scope_call_args = result[0]
        
        self.assertIsInstance(
            scope_node,
            TestGroup,
            "Third element should be a TestGroup instance"
        )

    def test_scope_tuple_contains_call_args(self):
        """
        Verify scope tuple contains the call arguments list.

        **Validates: Requirements 5.5**
        """
        test_tree = create_test_tree_with_single_module("test_module")
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        result = sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        scope_module, scope_name, scope_node, scope_call_args = result[0]
        
        self.assertIsInstance(
            scope_call_args,
            list,
            "Fourth element should be a list of call arguments"
        )
        self.assertIn(
            'sequencer',
            scope_call_args,
            "Call arguments should include 'sequencer'"
        )

    def test_scopes_returned_in_sorted_order(self):
        """
        Verify scopes are returned in sorted order by name.

        **Validates: Requirements 5.5**
        """
        test_tree = create_test_tree_with_multiple_modules(["zebra", "alpha", "middle"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        
        output_buffer = io.StringIO()
        factory_imports = set()
        constraint_imports = set()
        indent_space = "    "
        
        result = sequencer._generate_session_method(
            output_buffer, test_tree, factory_imports, constraint_imports, indent_space
        )
        
        scope_names = [scope[0] for scope in result]
        
        self.assertEqual(
            scope_names,
            sorted(scope_names),
            "Scopes should be returned in sorted order"
        )


if __name__ == "__main__":
    unittest.main()
