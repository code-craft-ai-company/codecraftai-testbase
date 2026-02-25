"""
.. module:: test_in_vscode_debugger
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the in_vscode_debugger function.

.. moduleauthor:: AutomationX
"""

import unittest
from unittest.mock import patch, MagicMock

from automojo.xmodules.debugging import in_vscode_debugger


class InVscodeDebuggerTests(unittest.TestCase):
    """
    Unit tests for the in_vscode_debugger function.
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """

    def test_function_returns_boolean(self):
        """
        Verify in_vscode_debugger returns a boolean value.
        
        Requirement 4.1
        """
        result = in_vscode_debugger()
        self.assertIsInstance(result, bool)

    def test_function_requires_no_parameters(self):
        """
        Verify in_vscode_debugger can be called without any parameters.
        
        Requirement 4.5
        """
        # Should not raise TypeError for missing arguments
        try:
            result = in_vscode_debugger()
            self.assertIsInstance(result, bool)
        except TypeError as err:
            self.fail(f"in_vscode_debugger() raised TypeError: {err}")

    def test_returns_false_when_not_in_vscode(self):
        """
        Verify function returns False when not running under VS Code debugger.
        
        Requirement 4.4
        """
        # When running tests normally (not under VS Code debugger),
        # the function should return False
        result = in_vscode_debugger()
        # In a normal test environment, we expect False
        self.assertFalse(result)

    def test_returns_true_when_pydevd_in_stack(self):
        """
        Verify function returns True when pydevd.py is found in stack frames.
        
        Requirement 4.3
        """
        # Create mock stack frames with pydevd.py
        mock_frame_info = MagicMock()
        mock_frame_info.__getitem__ = lambda self, idx: "/path/to/pydevd.py" if idx == 1 else None
        
        mock_stack = [mock_frame_info]
        
        with patch('automojo.xmodules.debugging.inspect.stack', return_value=mock_stack):
            result = in_vscode_debugger()
            self.assertTrue(result)

    def test_returns_false_when_pydevd_not_in_stack(self):
        """
        Verify function returns False when pydevd.py is not found in stack frames.
        
        Requirement 4.4
        """
        # Create mock stack frames without pydevd.py
        mock_frame_info = MagicMock()
        mock_frame_info.__getitem__ = lambda self, idx: "/path/to/some_other_file.py" if idx == 1 else None
        
        mock_stack = [mock_frame_info]
        
        with patch('automojo.xmodules.debugging.inspect.stack', return_value=mock_stack):
            result = in_vscode_debugger()
            self.assertFalse(result)

    def test_iterates_through_multiple_stack_frames(self):
        """
        Verify function iterates through all stack frames to find pydevd.py.
        
        Requirement 4.2
        """
        # Create mock stack frames where pydevd.py is in the middle
        mock_frame1 = MagicMock()
        mock_frame1.__getitem__ = lambda self, idx: "/path/to/first_file.py" if idx == 1 else None
        
        mock_frame2 = MagicMock()
        mock_frame2.__getitem__ = lambda self, idx: "/path/to/pydevd.py" if idx == 1 else None
        
        mock_frame3 = MagicMock()
        mock_frame3.__getitem__ = lambda self, idx: "/path/to/third_file.py" if idx == 1 else None
        
        mock_stack = [mock_frame1, mock_frame2, mock_frame3]
        
        with patch('automojo.xmodules.debugging.inspect.stack', return_value=mock_stack):
            result = in_vscode_debugger()
            self.assertTrue(result)

    def test_returns_false_with_empty_stack(self):
        """
        Verify function returns False when stack is empty.
        
        Requirement 4.4
        """
        with patch('automojo.xmodules.debugging.inspect.stack', return_value=[]):
            result = in_vscode_debugger()
            self.assertFalse(result)

    def test_detects_pydevd_at_end_of_filename(self):
        """
        Verify function correctly detects filenames ending with pydevd.py.
        
        Requirement 4.3
        """
        # Test various path formats that end with pydevd.py
        test_paths = [
            "/usr/lib/python3.8/site-packages/pydevd.py",
            "C:\\Python38\\Lib\\site-packages\\pydevd.py",
            "./pydevd.py",
            "pydevd.py"
        ]
        
        for path in test_paths:
            mock_frame_info = MagicMock()
            mock_frame_info.__getitem__ = lambda self, idx, p=path: p if idx == 1 else None
            
            mock_stack = [mock_frame_info]
            
            with patch('automojo.xmodules.debugging.inspect.stack', return_value=mock_stack):
                result = in_vscode_debugger()
                self.assertTrue(result, f"Failed to detect pydevd.py in path: {path}")

    def test_does_not_match_similar_filenames(self):
        """
        Verify function does not match filenames that contain but don't end with pydevd.py.
        
        Requirement 4.4
        """
        # Test paths that contain pydevd but don't end with pydevd.py
        test_paths = [
            "/path/to/pydevd_helper.py",
            "/path/to/my_pydevd_utils.py",
            "/path/to/pydevd.pyc",
            "/path/to/pydevd.pyo"
        ]
        
        for path in test_paths:
            mock_frame_info = MagicMock()
            mock_frame_info.__getitem__ = lambda self, idx, p=path: p if idx == 1 else None
            
            mock_stack = [mock_frame_info]
            
            with patch('automojo.xmodules.debugging.inspect.stack', return_value=mock_stack):
                result = in_vscode_debugger()
                self.assertFalse(result, f"Incorrectly matched path: {path}")


if __name__ == "__main__":
    unittest.main()
