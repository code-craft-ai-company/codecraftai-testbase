"""
.. module:: test_debugger_wellknown_breakpoint_code_append
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the debugger_wellknown_breakpoint_code_append function.

.. moduleauthor:: CodeCraftX
"""

import unittest
from unittest.mock import patch

from ccai.xmodules.debugging import (
    debugger_wellknown_breakpoint_code_append,
    DEBUGGER,
    DEFAULT_DEBUG_PORT
)


class DebuggerWellknownBreakpointCodeAppendTests(unittest.TestCase):
    """
    Unit tests for the debugger_wellknown_breakpoint_code_append function.
    
    Requirements: 7.1-7.7, 8.1-8.5, 9.1-9.7
    """

    def test_function_exists(self):
        """
        Verify debugger_wellknown_breakpoint_code_append function exists.
        
        Requirement 7.1
        """
        self.assertTrue(callable(debugger_wellknown_breakpoint_code_append))

    def test_accepts_debugger_parameter(self):
        """
        Verify function accepts debugger parameter.
        
        Requirement 7.2
        """
        code_lines = []
        # Should not raise TypeError when called with proper parameters
        result = debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="test-breakpoint",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=[]
        )
        self.assertIsNone(result)

    def test_accepts_breakpoint_name_parameter(self):
        """
        Verify function accepts breakpoint_name parameter.
        
        Requirement 7.3
        """
        code_lines = []
        result = debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=[]
        )
        self.assertIsNone(result)

    def test_accepts_code_lines_parameter(self):
        """
        Verify function accepts code_lines parameter as a list.
        
        Requirement 7.4
        """
        code_lines = []
        result = debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="test-breakpoint",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=[]
        )
        self.assertIsNone(result)
        self.assertIsInstance(code_lines, list)

    def test_accepts_current_indent_parameter(self):
        """
        Verify function accepts current_indent parameter.
        
        Requirement 7.5
        """
        code_lines = []
        result = debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="test-breakpoint",
            code_lines=code_lines,
            current_indent="    ",
            configured_breakpoints=[]
        )
        self.assertIsNone(result)

    def test_accepts_configured_breakpoints_parameter(self):
        """
        Verify function accepts configured_breakpoints parameter.
        
        Requirement 7.6
        """
        code_lines = []
        result = debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="test-breakpoint",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["test-discovery", "testrun-start"]
        )
        self.assertIsNone(result)

    def test_no_code_appended_when_breakpoint_not_configured(self):
        """
        Verify no code is appended when breakpoint_name is not in configured_breakpoints.
        
        Requirement 7.7
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="test-breakpoint",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["other-breakpoint"]
        )
        self.assertEqual(len(code_lines), 0)

    def test_no_code_appended_with_empty_configured_breakpoints(self):
        """
        Verify no code is appended when configured_breakpoints is empty.
        
        Requirement 7.7
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=[]
        )
        self.assertEqual(len(code_lines), 0)

    # PDB Code Generation Tests (Requirements 8.1-8.5)

    def test_pdb_appends_blank_line(self):
        """
        Verify pdb code generation appends a blank line for readability.
        
        Requirement 8.1
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        self.assertEqual(code_lines[0], '')

    def test_pdb_appends_comment(self):
        """
        Verify pdb code generation appends a comment explaining the breakpoint.
        
        Requirement 8.2
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        self.assertIn('# The debug flag was passed on the commandline so we break here.', code_lines[1])

    def test_pdb_appends_import_statement(self):
        """
        Verify pdb code generation appends an import statement for pdb.
        
        Requirement 8.3
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        self.assertIn('import pdb', code_lines[2])

    def test_pdb_appends_set_trace_call(self):
        """
        Verify pdb code generation appends a pdb.set_trace() call.
        
        Requirement 8.4
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        self.assertIn('pdb.set_trace()', code_lines[3])

    def test_pdb_uses_provided_indentation(self):
        """
        Verify pdb code generation uses the provided current_indent for all lines.
        
        Requirement 8.5
        """
        code_lines = []
        indent = "        "  # 8 spaces
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent=indent,
            configured_breakpoints=["testrun-start"]
        )
        # First line is blank, so skip it
        self.assertTrue(code_lines[1].startswith(indent))
        self.assertTrue(code_lines[2].startswith(indent))
        self.assertTrue(code_lines[3].startswith(indent))

    def test_pdb_generates_four_lines(self):
        """
        Verify pdb code generation produces exactly 4 lines.
        
        Requirement 8.1-8.4
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        self.assertEqual(len(code_lines), 4)

    # Debugpy Code Generation Tests (Requirements 9.1-9.7)

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=False)
    def test_debugpy_appends_blank_line(self, mock_in_vscode):
        """
        Verify debugpy code generation appends a blank line for readability.
        
        Requirement 9.1
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        self.assertEqual(code_lines[0], '')

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=False)
    def test_debugpy_appends_comment(self, mock_in_vscode):
        """
        Verify debugpy code generation appends a comment explaining the breakpoint.
        
        Requirement 9.2
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        self.assertIn('# The remote debug flag was passed on the commandline so we break here.', code_lines[1])

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=False)
    def test_debugpy_appends_import_statement(self, mock_in_vscode):
        """
        Verify debugpy code generation appends an import statement for debugpy.
        
        Requirement 9.3
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        self.assertIn('import debugpy', code_lines[2])

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=True)
    def test_debugpy_appends_listen_call_when_in_vscode(self, mock_in_vscode):
        """
        Verify debugpy code generation appends debugpy.listen() call when in VS Code.
        
        Requirement 9.4
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        listen_line = [line for line in code_lines if 'debugpy.listen' in line]
        self.assertEqual(len(listen_line), 1)
        self.assertIn(f'debugpy.listen(("127.0.0.1", {DEFAULT_DEBUG_PORT}))', listen_line[0])

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=True)
    def test_debugpy_appends_wait_for_client_call_when_in_vscode(self, mock_in_vscode):
        """
        Verify debugpy code generation appends debugpy.wait_for_client() call when in VS Code.
        
        Requirement 9.5
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        wait_line = [line for line in code_lines if 'debugpy.wait_for_client()' in line]
        self.assertEqual(len(wait_line), 1)

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=False)
    def test_debugpy_appends_breakpoint_call(self, mock_in_vscode):
        """
        Verify debugpy code generation appends debugpy.breakpoint() call.
        
        Requirement 9.6
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        breakpoint_line = [line for line in code_lines if 'debugpy.breakpoint()' in line]
        self.assertEqual(len(breakpoint_line), 1)

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=False)
    def test_debugpy_uses_provided_indentation(self, mock_in_vscode):
        """
        Verify debugpy code generation uses the provided current_indent for all lines.
        
        Requirement 9.7
        """
        code_lines = []
        indent = "    "  # 4 spaces
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent=indent,
            configured_breakpoints=["testrun-start"]
        )
        # First line is blank, so skip it
        for line in code_lines[1:]:
            self.assertTrue(line.startswith(indent), f"Line '{line}' does not start with indent")

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=False)
    def test_debugpy_skips_listen_wait_when_not_in_vscode(self, mock_in_vscode):
        """
        Verify debugpy code generation skips listen and wait_for_client when not in VS Code.
        
        Requirement 9.4, 9.5
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        listen_lines = [line for line in code_lines if 'debugpy.listen' in line]
        wait_lines = [line for line in code_lines if 'debugpy.wait_for_client' in line]
        self.assertEqual(len(listen_lines), 0)
        self.assertEqual(len(wait_lines), 0)

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=True)
    def test_debugpy_generates_six_lines_when_in_vscode(self, mock_in_vscode):
        """
        Verify debugpy code generation produces 6 lines when in VS Code.
        
        Requirement 9.1-9.6
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        # blank, comment, import, listen, wait, breakpoint = 6 lines
        self.assertEqual(len(code_lines), 6)

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=False)
    def test_debugpy_generates_four_lines_when_not_in_vscode(self, mock_in_vscode):
        """
        Verify debugpy code generation produces 4 lines when not in VS Code.
        
        Requirement 9.1-9.3, 9.6
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        # blank, comment, import, breakpoint = 4 lines
        self.assertEqual(len(code_lines), 4)

    # Syntactic Correctness Tests

    def test_pdb_generated_code_is_syntactically_correct(self):
        """
        Verify pdb generated code is syntactically correct Python.
        
        Requirement 8.1-8.5
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        code_str = '\n'.join(code_lines)
        # This should not raise a SyntaxError
        try:
            compile(code_str, '<string>', 'exec')
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False
        self.assertTrue(syntax_valid, f"Generated code is not syntactically correct:\n{code_str}")

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=False)
    def test_debugpy_generated_code_is_syntactically_correct_not_in_vscode(self, mock_in_vscode):
        """
        Verify debugpy generated code is syntactically correct Python when not in VS Code.
        
        Requirement 9.1-9.7
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        code_str = '\n'.join(code_lines)
        # This should not raise a SyntaxError
        try:
            compile(code_str, '<string>', 'exec')
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False
        self.assertTrue(syntax_valid, f"Generated code is not syntactically correct:\n{code_str}")

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=True)
    def test_debugpy_generated_code_is_syntactically_correct_in_vscode(self, mock_in_vscode):
        """
        Verify debugpy generated code is syntactically correct Python when in VS Code.
        
        Requirement 9.1-9.7
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        code_str = '\n'.join(code_lines)
        # This should not raise a SyntaxError
        try:
            compile(code_str, '<string>', 'exec')
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False
        self.assertTrue(syntax_valid, f"Generated code is not syntactically correct:\n{code_str}")

    def test_pdb_generated_code_with_indentation_is_syntactically_correct(self):
        """
        Verify pdb generated code with indentation is syntactically correct Python.
        
        Requirement 8.5
        """
        code_lines = ["def test_function():"]
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="    ",
            configured_breakpoints=["testrun-start"]
        )
        code_str = '\n'.join(code_lines)
        # This should not raise a SyntaxError
        try:
            compile(code_str, '<string>', 'exec')
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False
        self.assertTrue(syntax_valid, f"Generated code is not syntactically correct:\n{code_str}")

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=True)
    def test_debugpy_generated_code_with_indentation_is_syntactically_correct(self, mock_in_vscode):
        """
        Verify debugpy generated code with indentation is syntactically correct Python.
        
        Requirement 9.7
        """
        code_lines = ["def test_function():"]
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.DEBUGPY,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="    ",
            configured_breakpoints=["testrun-start"]
        )
        code_str = '\n'.join(code_lines)
        # This should not raise a SyntaxError
        try:
            compile(code_str, '<string>', 'exec')
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False
        self.assertTrue(syntax_valid, f"Generated code is not syntactically correct:\n{code_str}")

    # Additional Edge Case Tests

    def test_function_works_with_string_debugger_pdb(self):
        """
        Verify function works with string value 'pdb' for debugger parameter.
        
        Requirement 7.2
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger="pdb",
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        self.assertEqual(len(code_lines), 4)

    @patch('ccai.xmodules.debugging.in_vscode_debugger', return_value=False)
    def test_function_works_with_string_debugger_debugpy(self, mock_in_vscode):
        """
        Verify function works with string value 'debugpy' for debugger parameter.
        
        Requirement 7.2
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger="debugpy",
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        self.assertEqual(len(code_lines), 4)

    def test_breakpoint_name_in_list_with_multiple_breakpoints(self):
        """
        Verify function generates code when breakpoint_name is one of multiple configured breakpoints.
        
        Requirement 7.6
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["test-discovery", "testrun-start", "other-breakpoint"]
        )
        self.assertEqual(len(code_lines), 4)

    def test_unknown_debugger_does_not_append_code(self):
        """
        Verify function does not append code for unknown debugger type.
        
        Requirement 7.2
        """
        code_lines = []
        debugger_wellknown_breakpoint_code_append(
            debugger="unknown-debugger",
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        self.assertEqual(len(code_lines), 0)

    def test_returns_none(self):
        """
        Verify function returns None.
        
        Requirement 7.1
        """
        code_lines = []
        result = debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="test-breakpoint",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=[]
        )
        self.assertIsNone(result)

    def test_appends_to_existing_code_lines(self):
        """
        Verify function appends to existing code_lines list.
        
        Requirement 7.4
        """
        code_lines = ["# Existing code", "print('hello')"]
        debugger_wellknown_breakpoint_code_append(
            debugger=DEBUGGER.PDB,
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="",
            configured_breakpoints=["testrun-start"]
        )
        self.assertEqual(len(code_lines), 6)  # 2 existing + 4 new
        self.assertEqual(code_lines[0], "# Existing code")
        self.assertEqual(code_lines[1], "print('hello')")


if __name__ == "__main__":
    unittest.main()
