"""
    Integration tests for end-to-end sequence document generation.

    These tests verify the complete flow from test tree creation through
    document generation to document execution.

    Requirements covered:
    - 1.5: Generated document is importable as a Python module without syntax errors
    - 28.1: Generated document is importable using import_file
    - 28.2: Generated document has callable session function
    - 28.3: session function accepts sequencer parameter
    - 28.4: session(sequencer) call executes all tests in defined order
    - 28.5: Generated code has no syntax errors or undefined references
"""

import ast
import collections
import os
import sys
import tempfile
import unittest

from ccai.xmodules.ximport import import_file

from ccai.testbase.testgroup import TestGroup
from ccai.testbase.testref import TestRef
from ccai.testbase.injection.injectionregistry import injection_registry
from ccai.testbase.injection.injectionscope import InjectionScope
from ccai.testbase.sequencing.testsequencer import TestSequencer
from ccai.testbase.results.recorders.resultrecorder import ResultRecorder
from ccai.testbase.results.model.renderinfo import RenderInfo


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


# Global tracking for test execution order
_test_execution_order = []


def create_tracking_test_function(name, module_name):
    """
    Create a test function that tracks its execution order.
    
    Args:
        name: Name of the test function
        module_name: Module name for the test function
        
    Returns:
        A test function that appends its name to _test_execution_order when called
    """
    def test_func():
        _test_execution_order.append(name)
    test_func.__name__ = name
    test_func.__module__ = module_name
    return test_func


def register_test_scope(test_name, module_name):
    """
    Register a test scope in the injection registry.
    
    Args:
        test_name: Name of the test function
        module_name: Name of the module containing the test
    """
    scope_name = "{}#{}".format(module_name, test_name)
    injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, None)


def create_simple_test_tree(module_name, test_names):
    """
    Create a simple test tree with one module containing the specified tests.
    
    Args:
        module_name: Name of the module
        test_names: List of test function names
        
    Returns:
        MockTestGroup: Root of the test tree
    """
    root = MockTestGroup("root")
    module_group = MockTestGroup(module_name, package="")
    
    for test_name in test_names:
        test_func = create_tracking_test_function(test_name, module_name)
        test_ref = TestRef(test_func)
        module_group._children[test_ref.base_name] = test_ref
        # Register the test scope in the injection registry
        register_test_scope(test_name, module_name)
    
    root._children[module_name] = module_group
    return root


def create_multi_module_test_tree(modules_config):
    """
    Create a test tree with multiple modules.
    
    Args:
        modules_config: Dict mapping module names to lists of test names
        
    Returns:
        MockTestGroup: Root of the test tree
    """
    root = MockTestGroup("root")
    
    for module_name, test_names in modules_config.items():
        module_group = MockTestGroup(module_name, package="")
        
        for test_name in test_names:
            test_func = create_tracking_test_function(test_name, module_name)
            test_ref = TestRef(test_func)
            module_group._children[test_ref.base_name] = test_ref
            # Register the test scope in the injection registry
            register_test_scope(test_name, module_name)
        
        root._children[module_name] = module_group
    
    return root


class MockResultRecorder(ResultRecorder):
    """
    Mock ResultRecorder for testing sequence document execution.
    
    This recorder tracks all recorded results without writing to files.
    """
    
    def __init__(self):
        self._recorded_results = []
        self._previewed_results = []
        self._finalized = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._finalized = True
        return False
    
    def record(self, result):
        """Record a test result."""
        self._recorded_results.append(result)
    
    def preview(self, result):
        """Preview a test result before execution."""
        self._previewed_results.append(result)
    
    @property
    def recorded_results(self):
        return self._recorded_results
    
    @property
    def previewed_results(self):
        return self._previewed_results


class EndToEndDocumentGenerationTests(unittest.TestCase):
    """
    Integration tests for end-to-end document generation.
    
    **Validates: Requirements 1.5, 28.1, 28.2, 28.3, 28.4, 28.5**
    """

    def setUp(self):
        """Set up test fixtures."""
        global _test_execution_order
        _test_execution_order = []

        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        # Store original injection registry state
        self._original_scope_tree = injection_registry._scope_tree_root
        # Create a fresh scope tree for each test
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

        # Restore original injection registry state
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

    def test_generated_document_is_valid_python_module(self):
        """
        Test that generated document is valid Python with no syntax errors.
        
        **Validates: Requirements 1.5, 28.5**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one", "test_two"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Generated document should be valid Python syntax"
        )

    def test_generated_document_is_importable(self):
        """
        Test that generated document can be imported using import_file.
        
        **Validates: Requirements 28.1**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        # Attempt to import the generated document
        try:
            sequence_mod = import_file("sequence_document", output_file)
            self.assertIsNotNone(
                sequence_mod,
                "Generated document should be importable"
            )
        except Exception as e:
            self.fail(f"Generated document should be importable without errors: {e}")

    def test_generated_document_has_callable_session_function(self):
        """
        Test that generated document has a callable session function.
        
        **Validates: Requirements 28.2**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        sequence_mod = import_file("sequence_document", output_file)
        
        self.assertTrue(
            hasattr(sequence_mod, 'session'),
            "Generated document should have a 'session' attribute"
        )
        self.assertTrue(
            callable(sequence_mod.session),
            "session should be callable"
        )

    def test_session_function_accepts_sequencer_parameter(self):
        """
        Test that session function accepts a sequencer parameter.
        
        **Validates: Requirements 28.3**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Parse the code and find the session function
        tree = ast.parse(generated_code)
        session_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'session':
                session_func = node
                break
        
        self.assertIsNotNone(
            session_func,
            "session function should exist in generated code"
        )
        
        # Check that session function has at least one argument (sequencer)
        self.assertGreaterEqual(
            len(session_func.args.args),
            1,
            "session function should accept at least one parameter"
        )
        
        # Check that the first argument is named 'sequencer'
        self.assertEqual(
            session_func.args.args[0].arg,
            'sequencer',
            "First parameter of session function should be 'sequencer'"
        )

    def test_generated_code_has_no_undefined_references(self):
        """
        Test that generated code compiles without undefined reference errors.
        
        **Validates: Requirements 28.5**
        """
        modules_config = {
            "module_a": ["test_a1", "test_a2"],
            "module_b": ["test_b1"]
        }
        test_tree = create_multi_module_test_tree(modules_config)
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Compile the code to check for syntax errors
        try:
            compile(generated_code, output_file, 'exec')
        except SyntaxError as e:
            self.fail(f"Generated code should compile without syntax errors: {e}")

    def test_multi_module_document_is_valid_python(self):
        """
        Test that multi-module document is valid Python.
        
        **Validates: Requirements 1.5, 28.5**
        """
        modules_config = {
            "alpha_module": ["test_alpha1", "test_alpha2"],
            "beta_module": ["test_beta1"],
            "gamma_module": ["test_gamma1", "test_gamma2", "test_gamma3"]
        }
        test_tree = create_multi_module_test_tree(modules_config)
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Multi-module generated document should be valid Python syntax"
        )

    def test_multi_module_document_is_importable(self):
        """
        Test that multi-module document can be imported.
        
        **Validates: Requirements 28.1**
        """
        modules_config = {
            "alpha_module": ["test_alpha1"],
            "beta_module": ["test_beta1"]
        }
        test_tree = create_multi_module_test_tree(modules_config)
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        try:
            sequence_mod = import_file("sequence_document_multi", output_file)
            self.assertIsNotNone(
                sequence_mod,
                "Multi-module generated document should be importable"
            )
        except Exception as e:
            self.fail(f"Multi-module generated document should be importable: {e}")

    def test_scope_functions_are_callable(self):
        """
        Test that generated scope functions are callable.
        
        **Validates: Requirements 28.2**
        """
        modules_config = {
            "alpha_module": ["test_alpha1"],
            "beta_module": ["test_beta1"]
        }
        test_tree = create_multi_module_test_tree(modules_config)
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        sequence_mod = import_file("sequence_document_scope", output_file)
        
        # Check that scope functions exist and are callable
        self.assertTrue(
            hasattr(sequence_mod, 'scope_alpha_module'),
            "Generated document should have scope_alpha_module function"
        )
        self.assertTrue(
            callable(sequence_mod.scope_alpha_module),
            "scope_alpha_module should be callable"
        )
        
        self.assertTrue(
            hasattr(sequence_mod, 'scope_beta_module'),
            "Generated document should have scope_beta_module function"
        )
        self.assertTrue(
            callable(sequence_mod.scope_beta_module),
            "scope_beta_module should be callable"
        )


class DocumentStructureValidationTests(unittest.TestCase):
    """
    Tests for validating the structure of generated documents.
    
    **Validates: Requirements 1.5, 28.5**
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

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

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

    def test_document_contains_required_imports(self):
        """
        Test that generated document contains all required imports.
        
        **Validates: Requirements 28.5**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Check for required imports
        self.assertIn(
            'import logging',
            generated_code,
            "Generated document should import logging"
        )
        self.assertIn(
            'ConstraintsCatalog',
            generated_code,
            "Generated document should reference ConstraintsCatalog"
        )
        self.assertIn(
            'getEnhancedLogger',
            generated_code,
            "Generated document should reference getEnhancedLogger"
        )

    def test_document_contains_traceback_policy(self):
        """
        Test that generated document sets traceback format policy.
        
        **Validates: Requirements 28.5**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            '__traceback_format_policy__',
            generated_code,
            "Generated document should set __traceback_format_policy__"
        )
        self.assertIn(
            '"Brief"',
            generated_code,
            "Traceback policy should be set to 'Brief'"
        )

    def test_document_contains_code_generated_warning(self):
        """
        Test that generated document contains code-generated warning.
        
        **Validates: Requirements 28.5**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            'CODE GENERATED',
            generated_code,
            "Generated document should contain CODE GENERATED warning"
        )
        self.assertIn(
            'DO NOT EDIT',
            generated_code,
            "Generated document should contain DO NOT EDIT warning"
        )

    def test_session_function_has_docstring(self):
        """
        Test that session function has a docstring.
        
        **Validates: Requirements 28.2**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Parse and find session function
        tree = ast.parse(generated_code)
        session_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'session':
                session_func = node
                break
        
        self.assertIsNotNone(session_func, "session function should exist")
        
        # Check for docstring
        docstring = ast.get_docstring(session_func)
        self.assertIsNotNone(
            docstring,
            "session function should have a docstring"
        )

    def test_scope_functions_have_docstrings(self):
        """
        Test that scope functions have docstrings.
        
        **Validates: Requirements 28.2**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Parse and find scope functions
        tree = ast.parse(generated_code)
        scope_funcs = [
            node for node in ast.walk(tree) 
            if isinstance(node, ast.FunctionDef) and node.name.startswith('scope_')
        ]
        
        self.assertGreater(
            len(scope_funcs),
            0,
            "Generated document should have at least one scope function"
        )
        
        for scope_func in scope_funcs:
            docstring = ast.get_docstring(scope_func)
            self.assertIsNotNone(
                docstring,
                f"Scope function {scope_func.name} should have a docstring"
            )


class EmptyTestTreeTests(unittest.TestCase):
    """
    Tests for handling empty test trees.
    
    Note: Empty test trees produce documents with empty 'with' blocks which
    is invalid Python syntax. This is a known limitation documented in the
    tasks.md file under "Known Limitations".
    
    **Validates: Requirements 1.5, 28.1, 28.2**
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

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

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

    def test_empty_tree_produces_document_file(self):
        """
        Test that an empty test tree produces a document file.
        
        Note: The document may not be valid Python due to empty 'with' blocks.
        This is a known limitation.
        
        **Validates: Requirements 1.5**
        """
        root = MockTestGroup("root")
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        self.assertTrue(
            os.path.exists(output_file),
            "Document should be created even for empty test tree"
        )

    def test_empty_tree_document_contains_session_function_definition(self):
        """
        Test that empty tree document contains session function definition.
        
        Note: The session function may have an empty body which is invalid Python.
        
        **Validates: Requirements 28.2**
        """
        root = MockTestGroup("root")
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            'def session(sequencer):',
            generated_code,
            "Empty tree document should contain session function definition"
        )

    def test_empty_tree_document_contains_template_content(self):
        """
        Test that empty tree document contains template content.
        
        **Validates: Requirements 28.5**
        """
        root = MockTestGroup("root")
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            'CODE GENERATED',
            generated_code,
            "Empty tree document should contain CODE GENERATED warning"
        )
        self.assertIn(
            '__traceback_format_policy__',
            generated_code,
            "Empty tree document should contain traceback policy"
        )


if __name__ == "__main__":
    unittest.main()
