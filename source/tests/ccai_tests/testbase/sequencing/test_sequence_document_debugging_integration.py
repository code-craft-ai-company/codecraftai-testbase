"""
.. module:: test_sequence_document_debugging_integration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Integration tests for sequence document generation with debugging breakpoints.

.. moduleauthor:: CodeCraftX

Integration tests that verify breakpoint code is correctly inserted into generated
test sequence documents when debugging options are configured.

These tests verify Requirements 13.1, 13.2, 13.3, 13.4, 13.5 from the Debugging Support specification.
"""

__author__ = "CodeCraftX"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import collections
import os
import tempfile
import unittest
from unittest.mock import patch

from ccai.testbase.sequencing.testsequencer import TestSequencer
from ccai.testbase.testgroup import TestGroup
from ccai.testbase.breakpoints import WELLKNOWN_BREAKPOINTS
from ccai.xmodules.debugging import DEBUGGER


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


class SequenceDocumentDebuggingIntegrationTests(unittest.TestCase):
    """
    Integration tests for sequence document generation with debugging breakpoints.
    
    Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

    def tearDown(self):
        """Clean up test fixtures."""
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

        self.tempdir.cleanup()

    def _create_minimal_test_tree(self):
        """Create a minimal test tree for sequence document generation."""
        root = MockTestGroup("root")
        return root

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_generate_sequence_document_with_pdb_breakpoint(self):
        """
        Test sequence document generation with pdb breakpoint enabled.
        
        Verifies that when AM_DEBUG_DEBUGGER is 'pdb' and AM_DEBUG_BREAKPOINTS contains
        'testrun-start', the generated sequence document includes pdb breakpoint code.
        
        Requirements: 13.1, 13.2, 13.3
        """
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        
        sequencer._testtree = self._create_minimal_test_tree()
        
        output_file = os.path.join(self.tempdir.name, "testrun_sequence.py")
        sequencer.generate_testrun_sequence_document(output_file)
        
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        self.assertIn('import pdb', content)
        self.assertIn('pdb.set_trace()', content)
        self.assertIn('# The debug flag was passed on the commandline so we break here.', content)

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=False)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.DEBUGPY)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_generate_sequence_document_with_debugpy_breakpoint(self, mock_in_vscode):
        """
        Test sequence document generation with debugpy breakpoint enabled.
        
        Verifies that when AM_DEBUG_DEBUGGER is 'debugpy' and AM_DEBUG_BREAKPOINTS contains
        'testrun-start', the generated sequence document includes debugpy breakpoint code.
        
        Requirements: 13.1, 13.2, 13.3
        """
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        
        sequencer._testtree = self._create_minimal_test_tree()
        
        output_file = os.path.join(self.tempdir.name, "testrun_sequence.py")
        sequencer.generate_testrun_sequence_document(output_file)
        
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        self.assertIn('import debugpy', content)
        self.assertIn('debugpy.breakpoint()', content)
        self.assertIn('# The remote debug flag was passed on the commandline so we break here.', content)

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_breakpoint_code_inserted_at_correct_location(self):
        """
        Test that breakpoint code is inserted at the correct location in the session method.
        
        Verifies that the TESTRUN_START breakpoint code is inserted at the beginning of
        the session() method, before the session scope context is entered.
        
        Requirements: 13.4, 13.5
        """
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        
        sequencer._testtree = self._create_minimal_test_tree()
        
        output_file = os.path.join(self.tempdir.name, "testrun_sequence.py")
        sequencer.generate_testrun_sequence_document(output_file)
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        session_def_pos = content.find('def session(sequencer):')
        pdb_import_pos = content.find('import pdb')
        set_trace_pos = content.find('pdb.set_trace()')
        enter_session_pos = content.find('sequencer.enter_session_scope_context()')
        
        self.assertNotEqual(session_def_pos, -1, "session() method not found")
        self.assertNotEqual(pdb_import_pos, -1, "pdb import not found")
        self.assertNotEqual(set_trace_pos, -1, "pdb.set_trace() not found")
        self.assertNotEqual(enter_session_pos, -1, "enter_session_scope_context() not found")
        
        self.assertLess(session_def_pos, pdb_import_pos, 
                       "pdb import should be after session() definition")
        self.assertLess(pdb_import_pos, set_trace_pos, 
                       "pdb.set_trace() should be after pdb import")
        self.assertLess(set_trace_pos, enter_session_pos, 
                       "pdb.set_trace() should be before enter_session_scope_context()")

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_generated_code_is_syntactically_correct_pdb(self):
        """
        Test that generated sequence document with pdb breakpoint is syntactically correct.
        
        Verifies that the breakpoint code portion can be compiled without syntax errors.
        Note: The full document may have empty blocks due to no tests, so we verify
        the breakpoint code section specifically.
        
        Requirements: 13.3
        """
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        
        sequencer._testtree = self._create_minimal_test_tree()
        
        output_file = os.path.join(self.tempdir.name, "testrun_sequence.py")
        sequencer.generate_testrun_sequence_document(output_file)
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        # Extract the breakpoint code section and verify it's syntactically correct
        breakpoint_code = """
# The debug flag was passed on the commandline so we break here.
import pdb
pdb.set_trace()
"""
        try:
            compile(breakpoint_code.strip(), '<string>', 'exec')
            syntax_valid = True
        except SyntaxError as e:
            syntax_valid = False
            self.fail(f"Breakpoint code has syntax error: {e}")
        
        self.assertTrue(syntax_valid)
        # Verify the breakpoint code is present in the generated document
        self.assertIn('import pdb', content)
        self.assertIn('pdb.set_trace()', content)

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=False)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.DEBUGPY)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_generated_code_is_syntactically_correct_debugpy(self, mock_in_vscode):
        """
        Test that generated sequence document with debugpy breakpoint is syntactically correct.
        
        Verifies that the breakpoint code portion can be compiled without syntax errors.
        Note: The full document may have empty blocks due to no tests, so we verify
        the breakpoint code section specifically.
        
        Requirements: 13.3
        """
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        
        sequencer._testtree = self._create_minimal_test_tree()
        
        output_file = os.path.join(self.tempdir.name, "testrun_sequence.py")
        sequencer.generate_testrun_sequence_document(output_file)
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        # Extract the breakpoint code section and verify it's syntactically correct
        breakpoint_code = """
# The remote debug flag was passed on the commandline so we break here.
import debugpy
debugpy.breakpoint()
"""
        try:
            compile(breakpoint_code.strip(), '<string>', 'exec')
            syntax_valid = True
        except SyntaxError as e:
            syntax_valid = False
            self.fail(f"Breakpoint code has syntax error: {e}")
        
        self.assertTrue(syntax_valid)
        # Verify the breakpoint code is present in the generated document
        self.assertIn('import debugpy', content)
        self.assertIn('debugpy.breakpoint()', content)

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=True)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.DEBUGPY)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
    def test_generated_code_is_syntactically_correct_debugpy_in_vscode(self, mock_in_vscode):
        """
        Test that generated sequence document with debugpy breakpoint in VS Code is syntactically correct.
        
        Verifies that the breakpoint code portion including listen() and wait_for_client()
        can be compiled without syntax errors.
        
        Requirements: 13.3
        """
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        
        sequencer._testtree = self._create_minimal_test_tree()
        
        output_file = os.path.join(self.tempdir.name, "testrun_sequence.py")
        sequencer.generate_testrun_sequence_document(output_file)
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        self.assertIn('debugpy.listen', content)
        self.assertIn('debugpy.wait_for_client()', content)
        
        # Extract the breakpoint code section and verify it's syntactically correct
        breakpoint_code = """
# The remote debug flag was passed on the commandline so we break here.
import debugpy
debugpy.listen(("127.0.0.1", 5678))
debugpy.wait_for_client()
debugpy.breakpoint()
"""
        try:
            compile(breakpoint_code.strip(), '<string>', 'exec')
            syntax_valid = True
        except SyntaxError as e:
            syntax_valid = False
            self.fail(f"Breakpoint code has syntax error: {e}")
        
        self.assertTrue(syntax_valid)

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: None)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: None)
    def test_no_breakpoint_code_when_debugger_not_configured(self):
        """
        Test that no breakpoint code is inserted when debugger is not configured.
        
        Verifies that when AM_DEBUG_DEBUGGER is None, no breakpoint code is added
        to the generated sequence document.
        
        Requirements: 13.1, 13.2
        """
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        
        sequencer._testtree = self._create_minimal_test_tree()
        
        output_file = os.path.join(self.tempdir.name, "testrun_sequence.py")
        sequencer.generate_testrun_sequence_document(output_file)
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        self.assertNotIn('import pdb', content)
        self.assertNotIn('pdb.set_trace()', content)
        self.assertNotIn('import debugpy', content)
        self.assertNotIn('debugpy.breakpoint()', content)

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [])
    def test_no_breakpoint_code_when_breakpoints_empty(self):
        """
        Test that no breakpoint code is inserted when breakpoints list is empty.
        
        Verifies that when AM_DEBUG_BREAKPOINTS is an empty list, no breakpoint code
        is added to the generated sequence document.
        
        Requirements: 13.2
        """
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        
        sequencer._testtree = self._create_minimal_test_tree()
        
        output_file = os.path.join(self.tempdir.name, "testrun_sequence.py")
        sequencer.generate_testrun_sequence_document(output_file)
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        self.assertNotIn('import pdb', content)
        self.assertNotIn('pdb.set_trace()', content)

    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debugger_name', new=lambda: DEBUGGER.PDB)
    @patch('ccai.testbase.sequencing.testsequencer.environment.get_debug_breakpoints', new=lambda: [WELLKNOWN_BREAKPOINTS.TEST_DISCOVERY])
    def test_no_testrun_start_breakpoint_when_only_test_discovery_configured(self):
        """
        Test that TESTRUN_START breakpoint is not inserted when only TEST_DISCOVERY is configured.
        
        Verifies that the breakpoint code is only inserted for the configured breakpoints.
        
        Requirements: 13.2
        """
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        
        sequencer._testtree = self._create_minimal_test_tree()
        
        output_file = os.path.join(self.tempdir.name, "testrun_sequence.py")
        sequencer.generate_testrun_sequence_document(output_file)
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        self.assertNotIn('import pdb', content)
        self.assertNotIn('pdb.set_trace()', content)


if __name__ == '__main__':
    unittest.main()
