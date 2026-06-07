"""
.. module:: test_debugger_breakpoint_scenarios_integration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Integration tests for debugger breakpoint scenarios in sequence document generation.

.. moduleauthor:: CodeCraftX

Integration tests that verify debugger breakpoint code is correctly inserted into
the generated sequence document when debugging options are configured, and that
the generated document is valid Python.

Requirements covered:
- 7.1: WHEN AM_DEBUG_DEBUGGER runtime variable is set, THE System SHALL check for configured breakpoints
- 7.2: WHEN AM_DEBUG_BREAKPOINTS includes TESTRUN_START, THE System SHALL insert breakpoint code in the session method
- 7.3: THE breakpoint code SHALL be inserted after the docstring and before the scope context
- 7.4: THE System SHALL use `debugger_wellknown_breakpoint_code_append` to generate the breakpoint code
- 7.5: WHEN debugger is not configured, THE System SHALL not insert any breakpoint code
"""

__author__ = "CodeCraftX"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import ast
import collections
import os
import tempfile
import unittest
from unittest.mock import patch

from ccai.testbase.sequencing.testsequencer import TestSequencer
from ccai.testbase.testgroup import TestGroup
from ccai.testbase.testref import TestRef
from ccai.testbase.breakpoints import WELLKNOWN_BREAKPOINTS
from ccai.testbase.injection.injectionregistry import injection_registry
from ccai.testbase.injection.injectionscope import InjectionScope
from ccai.xmodules.debugging import DEBUGGER
from ccai.xmodules.ximport import import_file


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
        pass
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
        register_test_scope(test_name, module_name)
    
    root._children[module_name] = module_group
    return root


class DebuggerConfiguredDocumentGenerationTests(unittest.TestCase):
    """
    Integration tests for document generation with debugger configured.

    **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
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

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_pdb_document_generation_produces_valid_python(self):
        """
        Test that document generation with pdb debugger produces valid Python.

        **Validates: Requirements 7.1, 7.2**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Generated document with pdb debugger should be valid Python syntax"
        )

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_pdb_document_contains_breakpoint_code(self):
        """
        Test that document with pdb debugger contains breakpoint code.

        **Validates: Requirements 7.1, 7.2**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            'import pdb',
            generated_code,
            "Generated document should contain pdb import"
        )
        self.assertIn(
            'pdb.set_trace()',
            generated_code,
            "Generated document should contain pdb.set_trace() call"
        )

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_pdb_document_is_importable(self):
        """
        Test that document with pdb debugger can be imported.

        **Validates: Requirements 7.1, 7.2**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        try:
            sequence_mod = import_file("sequence_document_pdb", output_file)
            self.assertIsNotNone(
                sequence_mod,
                "Generated document with pdb debugger should be importable"
            )
        except Exception as e:
            self.fail(f"Generated document with pdb debugger should be importable: {e}")

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=False)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.DEBUGPY)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_debugpy_document_generation_produces_valid_python(self, mock_in_vscode):
        """
        Test that document generation with debugpy debugger produces valid Python.

        **Validates: Requirements 7.1, 7.2**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Generated document with debugpy debugger should be valid Python syntax"
        )

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=False)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.DEBUGPY)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_debugpy_document_contains_breakpoint_code(self, mock_in_vscode):
        """
        Test that document with debugpy debugger contains breakpoint code.

        **Validates: Requirements 7.1, 7.2**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            'import debugpy',
            generated_code,
            "Generated document should contain debugpy import"
        )
        self.assertIn(
            'debugpy.breakpoint()',
            generated_code,
            "Generated document should contain debugpy.breakpoint() call"
        )

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=False)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.DEBUGPY)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_debugpy_document_is_importable(self, mock_in_vscode):
        """
        Test that document with debugpy debugger can be imported.

        **Validates: Requirements 7.1, 7.2**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        try:
            sequence_mod = import_file("sequence_document_debugpy", output_file)
            self.assertIsNotNone(
                sequence_mod,
                "Generated document with debugpy debugger should be importable"
            )
        except Exception as e:
            self.fail(f"Generated document with debugpy debugger should be importable: {e}")


class DebuggerNotConfiguredDocumentGenerationTests(unittest.TestCase):
    """
    Integration tests for document generation without debugger configured.

    **Validates: Requirements 7.5**
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

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: None)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: None)
    def test_no_debugger_document_produces_valid_python(self):
        """
        Test that document generation without debugger produces valid Python.

        **Validates: Requirements 7.5**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Generated document without debugger should be valid Python syntax"
        )

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: None)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: None)
    def test_no_debugger_document_has_no_breakpoint_code(self):
        """
        Test that document without debugger has no breakpoint code.

        **Validates: Requirements 7.5**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertNotIn(
            'import pdb',
            generated_code,
            "Generated document should not contain pdb import when debugger not configured"
        )
        self.assertNotIn(
            'pdb.set_trace()',
            generated_code,
            "Generated document should not contain pdb.set_trace() when debugger not configured"
        )
        self.assertNotIn(
            'import debugpy',
            generated_code,
            "Generated document should not contain debugpy import when debugger not configured"
        )
        self.assertNotIn(
            'debugpy.breakpoint()',
            generated_code,
            "Generated document should not contain debugpy.breakpoint() when debugger not configured"
        )

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: None)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: None)
    def test_no_debugger_document_is_importable(self):
        """
        Test that document without debugger can be imported.

        **Validates: Requirements 7.5**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        try:
            sequence_mod = import_file("sequence_document_no_debug", output_file)
            self.assertIsNotNone(
                sequence_mod,
                "Generated document without debugger should be importable"
            )
        except Exception as e:
            self.fail(f"Generated document without debugger should be importable: {e}")

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: None)
    def test_debugger_set_but_no_breakpoints_has_no_breakpoint_code(self):
        """
        Test that document with debugger but no breakpoints has no breakpoint code.

        **Validates: Requirements 7.5**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertNotIn(
            'import pdb',
            generated_code,
            "Generated document should not contain pdb import when breakpoints is None"
        )
        self.assertNotIn(
            'pdb.set_trace()',
            generated_code,
            "Generated document should not contain pdb.set_trace() when breakpoints is None"
        )

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [])
    def test_debugger_set_but_empty_breakpoints_has_no_breakpoint_code(self):
        """
        Test that document with debugger but empty breakpoints list has no breakpoint code.

        **Validates: Requirements 7.5**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertNotIn(
            'import pdb',
            generated_code,
            "Generated document should not contain pdb import when breakpoints list is empty"
        )
        self.assertNotIn(
            'pdb.set_trace()',
            generated_code,
            "Generated document should not contain pdb.set_trace() when breakpoints list is empty"
        )


class BreakpointCodePlacementTests(unittest.TestCase):
    """
    Integration tests for verifying breakpoint code placement in generated document.

    **Validates: Requirements 7.3**
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

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_breakpoint_code_after_session_docstring(self):
        """
        Test that breakpoint code is placed after the session function docstring.

        **Validates: Requirements 7.3**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Find positions of key elements
        docstring_end_pos = generated_code.find('test run sequence document.')
        pdb_import_pos = generated_code.find('import pdb')

        self.assertNotEqual(docstring_end_pos, -1, "Session docstring should be present")
        self.assertNotEqual(pdb_import_pos, -1, "pdb import should be present")
        self.assertLess(
            docstring_end_pos,
            pdb_import_pos,
            "Breakpoint code should be after the session docstring"
        )

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_breakpoint_code_before_session_scope_context(self):
        """
        Test that breakpoint code is placed before the session scope context.

        **Validates: Requirements 7.3**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Find positions of key elements
        set_trace_pos = generated_code.find('pdb.set_trace()')
        enter_session_pos = generated_code.find('enter_session_scope_context()')

        self.assertNotEqual(set_trace_pos, -1, "pdb.set_trace() should be present")
        self.assertNotEqual(enter_session_pos, -1, "enter_session_scope_context() should be present")
        self.assertLess(
            set_trace_pos,
            enter_session_pos,
            "Breakpoint code should be before enter_session_scope_context()"
        )

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_breakpoint_code_properly_indented_in_document(self):
        """
        Test that breakpoint code is properly indented in the generated document.

        **Validates: Requirements 7.3, 7.4**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        lines = generated_code.split(os.linesep)

        # Find the pdb import line
        pdb_import_line = None
        for line in lines:
            if 'import pdb' in line:
                pdb_import_line = line
                break

        self.assertIsNotNone(pdb_import_line, "pdb import line should be found")
        self.assertTrue(
            pdb_import_line.startswith("    "),
            "pdb import should be indented with four spaces"
        )

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_breakpoint_comment_present_in_document(self):
        """
        Test that breakpoint comment is present in the generated document.

        **Validates: Requirements 7.4**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            '# The debug flag was passed on the commandline so we break here.',
            generated_code,
            "Generated document should contain breakpoint comment"
        )


if __name__ == '__main__':
    unittest.main()
