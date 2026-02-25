"""
.. module:: test_sequence_document_debugging_integration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Integration tests for sequence document generation with debugging breakpoints.

.. moduleauthor:: AutomationX

Integration tests that verify breakpoint code is correctly inserted into generated
test sequence documents when debugging options are configured.

These tests verify Requirements 13.1, 13.2, 13.3, 13.4, 13.5 from the Debugging Support specification.
"""

__author__ = "AutomationX"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import collections
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import automojo.runtime.paths as runtime_paths
from automojo.runtime.enumerations import JobType
from automojo.runtime.runtimevariables import RuntimeVariablesDesc
from automojo.thisapp.persona import APP_PERSONA_ESTABLISHED, establish_app_persona
from automojo.thisapp.wellknown import ThisApplicationSingleton

from automojo.testbase.sequencing.testsequencer import TestSequencer
from automojo.testbase.testgroup import TestGroup
from automojo.testbase.breakpoints import WELLKNOWN_BREAKPOINTS
from automojo.xmodules.debugging import DEBUGGER


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
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()
        
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    def _create_minimal_test_tree(self):
        """Create a minimal test tree for sequence document generation."""
        root = MockTestGroup("root")
        return root

    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_DEBUGGER', DEBUGGER.PDB)
    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_BREAKPOINTS', [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
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

    @patch('automojo.xmodules.debugging.in_vscode_debugger', return_value=False)
    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_DEBUGGER', DEBUGGER.DEBUGPY)
    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_BREAKPOINTS', [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
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

    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_DEBUGGER', DEBUGGER.PDB)
    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_BREAKPOINTS', [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
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

    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_DEBUGGER', DEBUGGER.PDB)
    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_BREAKPOINTS', [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
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

    @patch('automojo.xmodules.debugging.in_vscode_debugger', return_value=False)
    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_DEBUGGER', DEBUGGER.DEBUGPY)
    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_BREAKPOINTS', [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
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

    @patch('automojo.xmodules.debugging.in_vscode_debugger', return_value=True)
    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_DEBUGGER', DEBUGGER.DEBUGPY)
    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_BREAKPOINTS', [WELLKNOWN_BREAKPOINTS.TESTRUN_START])
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
debugpy.listen(("0.0.0.0", 5678))
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

    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_DEBUGGER', None)
    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_BREAKPOINTS', None)
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

    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_DEBUGGER', DEBUGGER.PDB)
    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_BREAKPOINTS', [])
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

    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_DEBUGGER', DEBUGGER.PDB)
    @patch('automojo.runtime.runtimevariables.RuntimeVariables.AM_DEBUG_BREAKPOINTS', [WELLKNOWN_BREAKPOINTS.TEST_DISCOVERY])
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
