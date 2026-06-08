"""
.. module:: test_debugger_breakpoint_integration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for debugger breakpoint integration in _generate_session_method.

.. moduleauthor:: CodeCraftX

Unit tests that verify debugger breakpoint code is correctly inserted into the
session method when debugging options are configured.

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

import collections
import io
import os
import tempfile
import unittest
from unittest.mock import patch

from ccai.testbase.sequencing.testsequencer import TestSequencer
from ccai.testbase.testgroup import TestGroup
from ccai.testbase.breakpoints import WELLKNOWN_BREAKPOINTS
from ccai.testbase.injection.injectionregistry import injection_registry
from ccai.testbase.injection.injectionscope import InjectionScope
from ccai.xmodules.debugging import DEBUGGER



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


def create_minimal_test_tree():
    """
    Create a minimal test tree with no tests for basic generation testing.
    
    Returns:
        MockTestGroup: Root of the test tree with no children
    """
    root = MockTestGroup("root")
    return root


class DebuggerBreakpointInsertionTests(unittest.TestCase):
    """
    Tests for debugger breakpoint insertion when debugger is configured.

    **Validates: Requirements 7.1, 7.2**
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
    def test_pdb_breakpoint_inserted_when_debugger_configured(self):
        """
        Verify pdb breakpoint code is inserted when AM_DEBUG_DEBUGGER is set to pdb.

        **Validates: Requirements 7.1, 7.2**
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
            'import pdb',
            generated_code,
            "Generated code should contain pdb import when debugger is configured"
        )
        self.assertIn(
            'pdb.set_trace()',
            generated_code,
            "Generated code should contain pdb.set_trace() when debugger is configured"
        )

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=False)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.DEBUGPY)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_debugpy_breakpoint_inserted_when_debugger_configured(self, mock_in_vscode):
        """
        Verify debugpy breakpoint code is inserted when AM_DEBUG_DEBUGGER is set to debugpy.

        **Validates: Requirements 7.1, 7.2**
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
            'import debugpy',
            generated_code,
            "Generated code should contain debugpy import when debugger is configured"
        )
        self.assertIn(
            'debugpy.breakpoint()',
            generated_code,
            "Generated code should contain debugpy.breakpoint() when debugger is configured"
        )

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_breakpoint_comment_inserted_for_pdb(self):
        """
        Verify breakpoint comment is inserted when pdb debugger is configured.

        **Validates: Requirements 7.1, 7.2**
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
            '# The debug flag was passed on the commandline so we break here.',
            generated_code,
            "Generated code should contain breakpoint comment for pdb"
        )



class DebuggerBreakpointSkippingTests(unittest.TestCase):
    """
    Tests for debugger breakpoint skipping when debugger is not configured.

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

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: None)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: None)
    def test_no_breakpoint_when_debugger_is_none(self):
        """
        Verify no breakpoint code is inserted when AM_DEBUG_DEBUGGER is None.

        **Validates: Requirements 7.5**
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
        
        self.assertNotIn(
            'import pdb',
            generated_code,
            "Generated code should not contain pdb import when debugger is not configured"
        )
        self.assertNotIn(
            'pdb.set_trace()',
            generated_code,
            "Generated code should not contain pdb.set_trace() when debugger is not configured"
        )
        self.assertNotIn(
            'import debugpy',
            generated_code,
            "Generated code should not contain debugpy import when debugger is not configured"
        )
        self.assertNotIn(
            'debugpy.breakpoint()',
            generated_code,
            "Generated code should not contain debugpy.breakpoint() when debugger is not configured"
        )

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: None)
    def test_no_breakpoint_when_breakpoints_is_none(self):
        """
        Verify no breakpoint code is inserted when AM_DEBUG_BREAKPOINTS is None.

        **Validates: Requirements 7.5**
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
        
        self.assertNotIn(
            'import pdb',
            generated_code,
            "Generated code should not contain pdb import when breakpoints is None"
        )
        self.assertNotIn(
            'pdb.set_trace()',
            generated_code,
            "Generated code should not contain pdb.set_trace() when breakpoints is None"
        )


    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [])
    def test_no_breakpoint_when_breakpoints_list_is_empty(self):
        """
        Verify no breakpoint code is inserted when AM_DEBUG_BREAKPOINTS is empty list.

        **Validates: Requirements 7.5**
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
        
        self.assertNotIn(
            'import pdb',
            generated_code,
            "Generated code should not contain pdb import when breakpoints list is empty"
        )
        self.assertNotIn(
            'pdb.set_trace()',
            generated_code,
            "Generated code should not contain pdb.set_trace() when breakpoints list is empty"
        )

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TEST_DISCOVERY])
    def test_no_testrun_start_breakpoint_when_only_test_discovery_configured(self):
        """
        Verify TESTRUN_START breakpoint is not inserted when only TEST_DISCOVERY is configured.

        **Validates: Requirements 7.5**
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
        
        self.assertNotIn(
            'import pdb',
            generated_code,
            "Generated code should not contain pdb import when TESTRUN_START not in breakpoints"
        )
        self.assertNotIn(
            'pdb.set_trace()',
            generated_code,
            "Generated code should not contain pdb.set_trace() when TESTRUN_START not in breakpoints"
        )


class TestrunStartBreakpointLocationTests(unittest.TestCase):
    """
    Tests for TESTRUN_START breakpoint location in the session method.

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
    def test_breakpoint_after_docstring(self):
        """
        Verify breakpoint code is inserted after the docstring.

        **Validates: Requirements 7.3**
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
        
        # Find positions of key elements
        docstring_end_pos = generated_code.find('test run sequence document.')
        pdb_import_pos = generated_code.find('import pdb')
        
        self.assertNotEqual(docstring_end_pos, -1, "Docstring should be present")
        self.assertNotEqual(pdb_import_pos, -1, "pdb import should be present")
        self.assertLess(
            docstring_end_pos,
            pdb_import_pos,
            "Breakpoint code should be after the docstring"
        )

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_breakpoint_before_session_scope_context(self):
        """
        Verify breakpoint code is inserted before the session scope context.

        **Validates: Requirements 7.3**
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
    def test_breakpoint_after_function_signature(self):
        """
        Verify breakpoint code is inserted after the function signature.

        **Validates: Requirements 7.3**
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
        
        # Find positions of key elements
        session_def_pos = generated_code.find('def session(sequencer):')
        pdb_import_pos = generated_code.find('import pdb')
        
        self.assertNotEqual(session_def_pos, -1, "session() definition should be present")
        self.assertNotEqual(pdb_import_pos, -1, "pdb import should be present")
        self.assertLess(
            session_def_pos,
            pdb_import_pos,
            "Breakpoint code should be after session() definition"
        )

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_breakpoint_code_is_properly_indented(self):
        """
        Verify breakpoint code is properly indented within the session method.

        **Validates: Requirements 7.3, 7.4**
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
        
        # Find the pdb import line
        pdb_import_line = None
        for line in lines:
            if 'import pdb' in line:
                pdb_import_line = line
                break
        
        self.assertIsNotNone(pdb_import_line, "pdb import line should be found")
        self.assertTrue(
            pdb_import_line.startswith(indent_space),
            "pdb import should be indented with the configured indent_space"
        )



class DebuggerWellknownBreakpointCodeAppendUsageTests(unittest.TestCase):
    """
    Tests verifying that debugger_wellknown_breakpoint_code_append is used correctly.

    **Validates: Requirements 7.4**
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

    @patch('ccai.testbase.sequencing.testsequencer.debugger_wellknown_breakpoint_code_append')
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_debugger_wellknown_breakpoint_code_append_called_when_configured(self, mock_breakpoint_append):
        """
        Verify debugger_wellknown_breakpoint_code_append is called when debugger is configured.

        **Validates: Requirements 7.4**
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
        
        mock_breakpoint_append.assert_called_once()

    @patch('ccai.testbase.sequencing.testsequencer.debugger_wellknown_breakpoint_code_append')
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_debugger_wellknown_breakpoint_code_append_called_with_correct_debugger(self, mock_breakpoint_append):
        """
        Verify debugger_wellknown_breakpoint_code_append is called with correct debugger parameter.

        **Validates: Requirements 7.4**
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
        
        call_args = mock_breakpoint_append.call_args
        self.assertEqual(call_args[0][0], DEBUGGER.PDB, "First argument should be the debugger name")

    @patch('ccai.testbase.sequencing.testsequencer.debugger_wellknown_breakpoint_code_append')
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_debugger_wellknown_breakpoint_code_append_called_with_testrun_start(self, mock_breakpoint_append):
        """
        Verify debugger_wellknown_breakpoint_code_append is called with TESTRUN_START breakpoint.

        **Validates: Requirements 7.4**
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
        
        call_args = mock_breakpoint_append.call_args
        self.assertEqual(
            call_args[0][1],
            WELLKNOWN_BREAKPOINTS.TESTRUN_START,
            "Second argument should be TESTRUN_START breakpoint"
        )

    @patch('ccai.testbase.sequencing.testsequencer.debugger_wellknown_breakpoint_code_append')
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: None)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: None)
    def test_debugger_wellknown_breakpoint_code_append_not_called_when_not_configured(self, mock_breakpoint_append):
        """
        Verify debugger_wellknown_breakpoint_code_append is not called when debugger is not configured.

        **Validates: Requirements 7.5**
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
        
        mock_breakpoint_append.assert_not_called()


if __name__ == '__main__':
    unittest.main()
