"""
.. module:: test_debugger_wellknown_breakpoint_entry
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the debugger_wellknown_breakpoint_entry function.

.. moduleauthor:: AutomationX
"""

import unittest
from unittest.mock import patch, MagicMock

from automojo.xmodules.debugging import (
    debugger_wellknown_breakpoint_entry,
    DEBUGGER,
    DEFAULT_DEBUG_PORT
)


class DebuggerWellknownBreakpointEntryTests(unittest.TestCase):
    """
    Unit tests for the debugger_wellknown_breakpoint_entry function.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7
    """

    def test_function_exists(self):
        """
        Verify debugger_wellknown_breakpoint_entry function exists.
        
        Requirement 5.1
        """
        self.assertTrue(callable(debugger_wellknown_breakpoint_entry))

    def test_accepts_debugger_parameter(self):
        """
        Verify function accepts debugger parameter.
        
        Requirement 5.2
        """
        # Should not raise TypeError when called with proper parameters
        result = debugger_wellknown_breakpoint_entry(
            debugger=DEBUGGER.PDB,
            breakpoint_name="test-breakpoint",
            configured_breakpoints=[]
        )
        self.assertIsNone(result)

    def test_accepts_breakpoint_name_parameter(self):
        """
        Verify function accepts breakpoint_name parameter.
        
        Requirement 5.3
        """
        result = debugger_wellknown_breakpoint_entry(
            debugger=DEBUGGER.PDB,
            breakpoint_name="testrun-start",
            configured_breakpoints=[]
        )
        self.assertIsNone(result)

    def test_accepts_configured_breakpoints_parameter(self):
        """
        Verify function accepts configured_breakpoints parameter.
        
        Requirement 5.4
        """
        result = debugger_wellknown_breakpoint_entry(
            debugger=DEBUGGER.PDB,
            breakpoint_name="test-breakpoint",
            configured_breakpoints=["test-discovery", "testrun-start"]
        )
        self.assertIsNone(result)

    @patch('pdb.set_trace')
    def test_returns_immediately_when_breakpoint_not_configured(self, mock_set_trace):
        """
        Verify function returns immediately when breakpoint_name is not in configured_breakpoints.
        
        Requirement 5.5
        """
        result = debugger_wellknown_breakpoint_entry(
            debugger=DEBUGGER.PDB,
            breakpoint_name="test-breakpoint",
            configured_breakpoints=["other-breakpoint"]
        )
        # pdb.set_trace should not be called
        mock_set_trace.assert_not_called()
        self.assertIsNone(result)

    @patch('pdb.set_trace')
    def test_returns_immediately_with_empty_configured_breakpoints(self, mock_set_trace):
        """
        Verify function returns immediately when configured_breakpoints is empty.
        
        Requirement 5.5
        """
        result = debugger_wellknown_breakpoint_entry(
            debugger=DEBUGGER.PDB,
            breakpoint_name="testrun-start",
            configured_breakpoints=[]
        )
        mock_set_trace.assert_not_called()
        self.assertIsNone(result)

    @patch('pdb.set_trace')
    def test_pdb_set_trace_called_when_breakpoint_configured(self, mock_set_trace):
        """
        Verify pdb.set_trace() is called when debugger is 'pdb' and breakpoint is configured.
        
        Requirement 5.6
        """
        debugger_wellknown_breakpoint_entry(
            debugger=DEBUGGER.PDB,
            breakpoint_name="testrun-start",
            configured_breakpoints=["testrun-start"]
        )
        mock_set_trace.assert_called_once()

    @patch('pdb.set_trace')
    def test_pdb_debugger_with_string_value(self, mock_set_trace):
        """
        Verify function works with string value 'pdb' for debugger parameter.
        
        Requirement 5.6
        """
        debugger_wellknown_breakpoint_entry(
            debugger="pdb",
            breakpoint_name="test-discovery",
            configured_breakpoints=["test-discovery"]
        )
        mock_set_trace.assert_called_once()

    @patch('debugpy.breakpoint')
    @patch('debugpy.wait_for_client')
    @patch('debugpy.listen')
    @patch('automojo.xmodules.debugging.in_vscode_debugger', return_value=True)
    def test_debugpy_breakpoint_called_when_configured(
        self, mock_in_vscode, mock_listen, mock_wait, mock_breakpoint
    ):
        """
        Verify debugpy.breakpoint() is called when debugger is 'debugpy' and breakpoint is configured.
        
        Requirement 5.7
        """
        debugger_wellknown_breakpoint_entry(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            configured_breakpoints=["testrun-start"]
        )
        mock_breakpoint.assert_called_once()

    @patch('debugpy.breakpoint')
    @patch('debugpy.wait_for_client')
    @patch('debugpy.listen')
    @patch('automojo.xmodules.debugging.in_vscode_debugger', return_value=True)
    def test_debugpy_listen_called_when_in_vscode(
        self, mock_in_vscode, mock_listen, mock_wait, mock_breakpoint
    ):
        """
        Verify debugpy.listen() is called when running under VS Code debugger.
        
        Requirement 5.7, 6.1
        """
        debugger_wellknown_breakpoint_entry(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            configured_breakpoints=["testrun-start"]
        )
        mock_listen.assert_called_once_with(("0.0.0.0", DEFAULT_DEBUG_PORT))

    @patch('debugpy.breakpoint')
    @patch('debugpy.wait_for_client')
    @patch('debugpy.listen')
    @patch('automojo.xmodules.debugging.in_vscode_debugger', return_value=True)
    def test_debugpy_wait_for_client_called_when_in_vscode(
        self, mock_in_vscode, mock_listen, mock_wait, mock_breakpoint
    ):
        """
        Verify debugpy.wait_for_client() is called when running under VS Code debugger.
        
        Requirement 5.7, 6.2
        """
        debugger_wellknown_breakpoint_entry(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            configured_breakpoints=["testrun-start"]
        )
        mock_wait.assert_called_once()

    @patch('debugpy.breakpoint')
    @patch('debugpy.wait_for_client')
    @patch('debugpy.listen')
    @patch('automojo.xmodules.debugging.in_vscode_debugger', return_value=False)
    def test_debugpy_skips_listen_wait_when_not_in_vscode(
        self, mock_in_vscode, mock_listen, mock_wait, mock_breakpoint
    ):
        """
        Verify debugpy.listen() and wait_for_client() are skipped when not in VS Code.
        
        Requirement 6.5
        """
        debugger_wellknown_breakpoint_entry(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            configured_breakpoints=["testrun-start"]
        )
        mock_listen.assert_not_called()
        mock_wait.assert_not_called()
        mock_breakpoint.assert_called_once()

    @patch('debugpy.breakpoint')
    @patch('automojo.xmodules.debugging.in_vscode_debugger', return_value=False)
    def test_debugpy_debugger_with_string_value(self, mock_in_vscode, mock_breakpoint):
        """
        Verify function works with string value 'debugpy' for debugger parameter.
        
        Requirement 5.7
        """
        debugger_wellknown_breakpoint_entry(
            debugger="debugpy",
            breakpoint_name="test-discovery",
            configured_breakpoints=["test-discovery"]
        )
        mock_breakpoint.assert_called_once()

    def test_returns_none(self):
        """
        Verify function returns None.
        
        Requirement 5.1
        """
        result = debugger_wellknown_breakpoint_entry(
            debugger=DEBUGGER.PDB,
            breakpoint_name="test-breakpoint",
            configured_breakpoints=[]
        )
        self.assertIsNone(result)

    @patch('pdb.set_trace')
    def test_breakpoint_name_in_list_with_multiple_breakpoints(self, mock_set_trace):
        """
        Verify function triggers when breakpoint_name is one of multiple configured breakpoints.
        
        Requirement 5.5
        """
        debugger_wellknown_breakpoint_entry(
            debugger=DEBUGGER.PDB,
            breakpoint_name="testrun-start",
            configured_breakpoints=["test-discovery", "testrun-start", "other-breakpoint"]
        )
        mock_set_trace.assert_called_once()

    def test_unknown_debugger_does_not_trigger_breakpoint(self):
        """
        Verify function does not trigger breakpoint for unknown debugger type.
        
        Requirement 5.2
        """
        with patch('pdb.set_trace') as mock_pdb_trace:
            with patch('debugpy.breakpoint') as mock_debugpy_bp:
                result = debugger_wellknown_breakpoint_entry(
                    debugger="unknown-debugger",
                    breakpoint_name="testrun-start",
                    configured_breakpoints=["testrun-start"]
                )
                mock_pdb_trace.assert_not_called()
                mock_debugpy_bp.assert_not_called()
                self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
