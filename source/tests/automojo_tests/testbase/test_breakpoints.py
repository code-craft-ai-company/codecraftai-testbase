"""
.. module:: test_breakpoints
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the WELLKNOWN_BREAKPOINTS enumeration.

.. moduleauthor:: AutomationX
"""

import unittest

from enum import Enum

from automojo.testbase.breakpoints import WELLKNOWN_BREAKPOINTS


class WellknownBreakpointsEnumTests(unittest.TestCase):
    """
    Unit tests for the WELLKNOWN_BREAKPOINTS enumeration.
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
    """

    def test_test_discovery_value_is_correct(self):
        """
        Verify TEST_DISCOVERY value is "test-discovery".
        
        Requirement 1.2
        """
        self.assertEqual(WELLKNOWN_BREAKPOINTS.TEST_DISCOVERY.value, "test-discovery")

    def test_testrun_start_value_is_correct(self):
        """
        Verify TESTRUN_START value is "testrun-start".
        
        Requirement 1.3
        """
        self.assertEqual(WELLKNOWN_BREAKPOINTS.TESTRUN_START.value, "testrun-start")

    def test_enum_inherits_from_str(self):
        """
        Verify enum inherits from str.
        
        Requirement 1.1
        """
        self.assertTrue(issubclass(WELLKNOWN_BREAKPOINTS, str))

    def test_enum_inherits_from_enum(self):
        """
        Verify enum inherits from Enum.
        
        Requirement 1.1
        """
        self.assertTrue(issubclass(WELLKNOWN_BREAKPOINTS, Enum))

    def test_test_discovery_string_comparison(self):
        """
        Verify TEST_DISCOVERY can be compared to string values.
        
        Requirement 1.5
        """
        self.assertEqual(WELLKNOWN_BREAKPOINTS.TEST_DISCOVERY, "test-discovery")

    def test_testrun_start_string_comparison(self):
        """
        Verify TESTRUN_START can be compared to string values.
        
        Requirement 1.5
        """
        self.assertEqual(WELLKNOWN_BREAKPOINTS.TESTRUN_START, "testrun-start")

    def test_test_discovery_accessible_as_class_attribute(self):
        """
        Verify TEST_DISCOVERY is accessible as a class attribute without instantiation.
        
        Requirement 1.4
        """
        self.assertIsNotNone(WELLKNOWN_BREAKPOINTS.TEST_DISCOVERY)
        self.assertIsInstance(WELLKNOWN_BREAKPOINTS.TEST_DISCOVERY, WELLKNOWN_BREAKPOINTS)

    def test_testrun_start_accessible_as_class_attribute(self):
        """
        Verify TESTRUN_START is accessible as a class attribute without instantiation.
        
        Requirement 1.4
        """
        self.assertIsNotNone(WELLKNOWN_BREAKPOINTS.TESTRUN_START)
        self.assertIsInstance(WELLKNOWN_BREAKPOINTS.TESTRUN_START, WELLKNOWN_BREAKPOINTS)

    def test_enum_member_is_instance_of_str(self):
        """
        Verify enum members are instances of str due to str inheritance.
        
        Requirement 1.1, 1.5
        """
        self.assertIsInstance(WELLKNOWN_BREAKPOINTS.TEST_DISCOVERY, str)
        self.assertIsInstance(WELLKNOWN_BREAKPOINTS.TESTRUN_START, str)

    def test_enum_member_in_string_list(self):
        """
        Verify enum members can be found in string lists due to str inheritance.
        
        Requirement 1.5
        """
        breakpoint_list = ["test-discovery", "testrun-start"]
        self.assertIn(WELLKNOWN_BREAKPOINTS.TEST_DISCOVERY, breakpoint_list)
        self.assertIn(WELLKNOWN_BREAKPOINTS.TESTRUN_START, breakpoint_list)


if __name__ == "__main__":
    unittest.main()
