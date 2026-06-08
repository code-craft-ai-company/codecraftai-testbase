"""
.. module:: test_debugger_enum
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the DEBUGGER enumeration.

.. moduleauthor:: CodeCraftX
"""

import unittest

from enum import Enum

from ccai.xmodules.debugging import DEBUGGER


class DebuggerEnumTests(unittest.TestCase):
    """
    Unit tests for the DEBUGGER enumeration.
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
    """

    def test_pdb_value_is_correct(self):
        """
        Verify PDB value is "pdb".
        
        Requirement 2.2
        """
        self.assertEqual(DEBUGGER.PDB.value, "pdb")

    def test_debugpy_value_is_correct(self):
        """
        Verify DEBUGPY value is "debugpy".
        
        Requirement 2.3
        """
        self.assertEqual(DEBUGGER.DEBUGPY.value, "debugpy")

    def test_enum_inherits_from_str(self):
        """
        Verify enum inherits from str.
        
        Requirement 2.1
        """
        self.assertTrue(issubclass(DEBUGGER, str))

    def test_enum_inherits_from_enum(self):
        """
        Verify enum inherits from Enum.
        
        Requirement 2.1
        """
        self.assertTrue(issubclass(DEBUGGER, Enum))

    def test_pdb_string_comparison(self):
        """
        Verify PDB can be compared to string values.
        
        Requirement 2.5
        """
        self.assertEqual(DEBUGGER.PDB, "pdb")

    def test_debugpy_string_comparison(self):
        """
        Verify DEBUGPY can be compared to string values.
        
        Requirement 2.5
        """
        self.assertEqual(DEBUGGER.DEBUGPY, "debugpy")

    def test_pdb_accessible_as_class_attribute(self):
        """
        Verify PDB is accessible as a class attribute without instantiation.
        
        Requirement 2.4
        """
        self.assertIsNotNone(DEBUGGER.PDB)
        self.assertIsInstance(DEBUGGER.PDB, DEBUGGER)

    def test_debugpy_accessible_as_class_attribute(self):
        """
        Verify DEBUGPY is accessible as a class attribute without instantiation.
        
        Requirement 2.4
        """
        self.assertIsNotNone(DEBUGGER.DEBUGPY)
        self.assertIsInstance(DEBUGGER.DEBUGPY, DEBUGGER)

    def test_enum_member_is_instance_of_str(self):
        """
        Verify enum members are instances of str due to str inheritance.
        
        Requirement 2.1, 2.5
        """
        self.assertIsInstance(DEBUGGER.PDB, str)
        self.assertIsInstance(DEBUGGER.DEBUGPY, str)

    def test_enum_member_in_string_list(self):
        """
        Verify enum members can be found in string lists due to str inheritance.
        
        Requirement 2.5
        """
        debugger_list = ["pdb", "debugpy"]
        self.assertIn(DEBUGGER.PDB, debugger_list)
        self.assertIn(DEBUGGER.DEBUGPY, debugger_list)


if __name__ == "__main__":
    unittest.main()
