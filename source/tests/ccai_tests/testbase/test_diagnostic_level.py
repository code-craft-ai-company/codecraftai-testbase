"""
    .. module:: ccai_tests.testbase.test_diagnostic_level
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the diagnostic_level module.

    .. moduleauthor:: CodeCraftX

    Unit tests for the diagnostic level configuration module that provides
    functions for managing diagnostic verbosity levels.
    
    These tests verify Requirements 7.1-7.5 from the Diagnostics System specification.
"""

__author__ = "CodeCraftX"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import unittest

from ccai.testbase.diagnostic_level import (
    get_diagnostic_level,
    set_diagnostic_level,
    reset_diagnostic_level,
    is_basic_level,
    is_standard_level,
    is_detailed_level,
    DEFAULT_DIAGNOSTIC_LEVEL
)


class DiagnosticLevelConstantsTests(unittest.TestCase):
    """Tests for diagnostic level constants."""

    def test_default_diagnostic_level_is_9(self):
        """
        Verify DEFAULT_DIAGNOSTIC_LEVEL is 9.
        
        Requirement 7.5: THE default diagnostic level SHALL be 9 (maximum detail)
        when not explicitly specified.
        """
        self.assertEqual(DEFAULT_DIAGNOSTIC_LEVEL, 9)


class DiagnosticLevelGetSetTests(unittest.TestCase):
    """Tests for get_diagnostic_level and set_diagnostic_level functions."""

    def setUp(self):
        """Reset diagnostic level before each test."""
        reset_diagnostic_level()

    def tearDown(self):
        """Reset diagnostic level after each test."""
        reset_diagnostic_level()

    def test_get_diagnostic_level_returns_default(self):
        """
        Verify get_diagnostic_level returns default value when not set.
        
        Requirement 7.5: THE default diagnostic level SHALL be 9 (maximum detail)
        when not explicitly specified.
        """
        self.assertEqual(get_diagnostic_level(), 9)

    def test_set_diagnostic_level_changes_value(self):
        """
        Verify set_diagnostic_level changes the configured level.
        
        Requirement 7.1: THE diagnostic level parameter SHALL accept integer values from 1 to 9.
        """
        set_diagnostic_level(5)
        self.assertEqual(get_diagnostic_level(), 5)

    def test_set_diagnostic_level_accepts_all_valid_values(self):
        """
        Verify set_diagnostic_level accepts all values from 1 to 9.
        
        Requirement 7.1: THE diagnostic level parameter SHALL accept integer values from 1 to 9.
        """
        for level in range(1, 10):
            set_diagnostic_level(level)
            self.assertEqual(get_diagnostic_level(), level)

    def test_set_diagnostic_level_rejects_zero(self):
        """
        Verify set_diagnostic_level rejects 0.
        
        Requirement 7.1: THE diagnostic level parameter SHALL accept integer values from 1 to 9.
        """
        with self.assertRaises(ValueError) as context:
            set_diagnostic_level(0)
        self.assertIn("between 1 and 9", str(context.exception))

    def test_set_diagnostic_level_rejects_negative(self):
        """
        Verify set_diagnostic_level rejects negative values.
        
        Requirement 7.1: THE diagnostic level parameter SHALL accept integer values from 1 to 9.
        """
        with self.assertRaises(ValueError) as context:
            set_diagnostic_level(-1)
        self.assertIn("between 1 and 9", str(context.exception))

    def test_set_diagnostic_level_rejects_greater_than_9(self):
        """
        Verify set_diagnostic_level rejects values greater than 9.
        
        Requirement 7.1: THE diagnostic level parameter SHALL accept integer values from 1 to 9.
        """
        with self.assertRaises(ValueError) as context:
            set_diagnostic_level(10)
        self.assertIn("between 1 and 9", str(context.exception))

    def test_set_diagnostic_level_rejects_non_integer(self):
        """
        Verify set_diagnostic_level rejects non-integer values.
        
        Requirement 7.1: THE diagnostic level parameter SHALL accept integer values from 1 to 9.
        """
        with self.assertRaises(ValueError) as context:
            set_diagnostic_level("5")
        self.assertIn("must be an integer", str(context.exception))

    def test_set_diagnostic_level_rejects_float(self):
        """
        Verify set_diagnostic_level rejects float values.
        
        Requirement 7.1: THE diagnostic level parameter SHALL accept integer values from 1 to 9.
        """
        with self.assertRaises(ValueError) as context:
            set_diagnostic_level(5.5)
        self.assertIn("must be an integer", str(context.exception))


class DiagnosticLevelResetTests(unittest.TestCase):
    """Tests for reset_diagnostic_level function."""

    def setUp(self):
        """Reset diagnostic level before each test."""
        reset_diagnostic_level()

    def tearDown(self):
        """Reset diagnostic level after each test."""
        reset_diagnostic_level()

    def test_reset_diagnostic_level_restores_default(self):
        """
        Verify reset_diagnostic_level restores the default value.
        
        Requirement 7.5: THE default diagnostic level SHALL be 9 (maximum detail)
        when not explicitly specified.
        """
        set_diagnostic_level(3)
        self.assertEqual(get_diagnostic_level(), 3)
        
        reset_diagnostic_level()
        self.assertEqual(get_diagnostic_level(), 9)


class DiagnosticLevelRangeTests(unittest.TestCase):
    """Tests for diagnostic level range helper functions."""

    def setUp(self):
        """Reset diagnostic level before each test."""
        reset_diagnostic_level()

    def tearDown(self):
        """Reset diagnostic level after each test."""
        reset_diagnostic_level()

    def test_is_basic_level_for_levels_1_to_3(self):
        """
        Verify is_basic_level returns True for levels 1-3.
        
        Requirement 7.2: WHEN diagnostic level is 1-3, THE integration coupling
        SHALL capture basic diagnostic information.
        """
        for level in [1, 2, 3]:
            self.assertTrue(is_basic_level(level), f"Level {level} should be basic")

    def test_is_basic_level_false_for_levels_4_to_9(self):
        """
        Verify is_basic_level returns False for levels 4-9.
        
        Requirement 7.2: WHEN diagnostic level is 1-3, THE integration coupling
        SHALL capture basic diagnostic information.
        """
        for level in [4, 5, 6, 7, 8, 9]:
            self.assertFalse(is_basic_level(level), f"Level {level} should not be basic")

    def test_is_standard_level_for_levels_4_to_6(self):
        """
        Verify is_standard_level returns True for levels 4-6.
        
        Requirement 7.3: WHEN diagnostic level is 4-6, THE integration coupling
        SHALL capture standard diagnostic information.
        """
        for level in [4, 5, 6]:
            self.assertTrue(is_standard_level(level), f"Level {level} should be standard")

    def test_is_standard_level_false_for_other_levels(self):
        """
        Verify is_standard_level returns False for levels outside 4-6.
        
        Requirement 7.3: WHEN diagnostic level is 4-6, THE integration coupling
        SHALL capture standard diagnostic information.
        """
        for level in [1, 2, 3, 7, 8, 9]:
            self.assertFalse(is_standard_level(level), f"Level {level} should not be standard")

    def test_is_detailed_level_for_levels_7_to_9(self):
        """
        Verify is_detailed_level returns True for levels 7-9.
        
        Requirement 7.4: WHEN diagnostic level is 7-9, THE integration coupling
        SHALL capture detailed diagnostic information.
        """
        for level in [7, 8, 9]:
            self.assertTrue(is_detailed_level(level), f"Level {level} should be detailed")

    def test_is_detailed_level_false_for_other_levels(self):
        """
        Verify is_detailed_level returns False for levels outside 7-9.
        
        Requirement 7.4: WHEN diagnostic level is 7-9, THE integration coupling
        SHALL capture detailed diagnostic information.
        """
        for level in [1, 2, 3, 4, 5, 6]:
            self.assertFalse(is_detailed_level(level), f"Level {level} should not be detailed")

    def test_is_basic_level_uses_configured_level_when_none(self):
        """
        Verify is_basic_level uses configured level when no argument provided.
        """
        set_diagnostic_level(2)
        self.assertTrue(is_basic_level())
        
        set_diagnostic_level(5)
        self.assertFalse(is_basic_level())

    def test_is_standard_level_uses_configured_level_when_none(self):
        """
        Verify is_standard_level uses configured level when no argument provided.
        """
        set_diagnostic_level(5)
        self.assertTrue(is_standard_level())
        
        set_diagnostic_level(2)
        self.assertFalse(is_standard_level())

    def test_is_detailed_level_uses_configured_level_when_none(self):
        """
        Verify is_detailed_level uses configured level when no argument provided.
        """
        set_diagnostic_level(8)
        self.assertTrue(is_detailed_level())
        
        set_diagnostic_level(5)
        self.assertFalse(is_detailed_level())


if __name__ == '__main__':
    unittest.main()
