"""
    Unit tests for import insertion point constants.

    Tests verify the values and ordering of the import insertion point
    constants used in the test sequence document generation.

    Requirements covered:
    - 3.1: CONSTRAINT_IMPORT_INSERTION_POINT value
    - 3.2: FACTORY_IMPORT_INSERTION_POINT value
    - 3.3: Constraint insertion point appears before factory insertion point
"""

import unittest

from ccai.testbase.sequencing.testsequencer import (
    TEMPLATE_TESTRUN_SEQUENCE_MODULE,
    CONSTRAINT_IMPORT_INSERTION_POINT,
    FACTORY_IMPORT_INSERTION_POINT,
)


class ConstraintImportInsertionPointValueTests(unittest.TestCase):
    """
    Tests for the CONSTRAINT_IMPORT_INSERTION_POINT constant value.

    **Validates: Requirements 3.1**
    """

    def test_constraint_import_insertion_point_value(self):
        """
        Verify CONSTRAINT_IMPORT_INSERTION_POINT has the correct value.

        The constant should be set to the expected marker comment string
        that identifies where constraint imports are inserted.

        **Validates: Requirements 3.1**
        """
        expected_value = "# ------- INSERT CONSTRAINT IMPORTS HERE -------"
        self.assertEqual(
            CONSTRAINT_IMPORT_INSERTION_POINT,
            expected_value,
            "CONSTRAINT_IMPORT_INSERTION_POINT should have the correct marker value"
        )

    def test_constraint_import_insertion_point_is_string(self):
        """
        Verify CONSTRAINT_IMPORT_INSERTION_POINT is a string type.

        **Validates: Requirements 3.1**
        """
        self.assertIsInstance(
            CONSTRAINT_IMPORT_INSERTION_POINT,
            str,
            "CONSTRAINT_IMPORT_INSERTION_POINT should be a string"
        )

    def test_constraint_import_insertion_point_is_comment(self):
        """
        Verify CONSTRAINT_IMPORT_INSERTION_POINT starts with a comment marker.

        **Validates: Requirements 3.1**
        """
        self.assertTrue(
            CONSTRAINT_IMPORT_INSERTION_POINT.startswith('#'),
            "CONSTRAINT_IMPORT_INSERTION_POINT should be a Python comment"
        )


class FactoryImportInsertionPointValueTests(unittest.TestCase):
    """
    Tests for the FACTORY_IMPORT_INSERTION_POINT constant value.

    **Validates: Requirements 3.2**
    """

    def test_factory_import_insertion_point_value(self):
        """
        Verify FACTORY_IMPORT_INSERTION_POINT has the correct value.

        The constant should be set to the expected marker comment string
        that identifies where factory imports are inserted.

        **Validates: Requirements 3.2**
        """
        expected_value = "# ------- INSERT FACTORY IMPORTS HERE -------"
        self.assertEqual(
            FACTORY_IMPORT_INSERTION_POINT,
            expected_value,
            "FACTORY_IMPORT_INSERTION_POINT should have the correct marker value"
        )

    def test_factory_import_insertion_point_is_string(self):
        """
        Verify FACTORY_IMPORT_INSERTION_POINT is a string type.

        **Validates: Requirements 3.2**
        """
        self.assertIsInstance(
            FACTORY_IMPORT_INSERTION_POINT,
            str,
            "FACTORY_IMPORT_INSERTION_POINT should be a string"
        )

    def test_factory_import_insertion_point_is_comment(self):
        """
        Verify FACTORY_IMPORT_INSERTION_POINT starts with a comment marker.

        **Validates: Requirements 3.2**
        """
        self.assertTrue(
            FACTORY_IMPORT_INSERTION_POINT.startswith('#'),
            "FACTORY_IMPORT_INSERTION_POINT should be a Python comment"
        )


class InsertionPointOrderingTests(unittest.TestCase):
    """
    Tests for the ordering of insertion points in the template.

    **Validates: Requirements 3.3**
    """

    def test_constraint_insertion_point_before_factory_insertion_point(self):
        """
        Verify constraint insertion point appears before factory insertion point in template.

        The constraint imports must be placed before factory imports in the
        generated document to ensure proper import ordering.

        **Validates: Requirements 3.3**
        """
        constraint_pos = TEMPLATE_TESTRUN_SEQUENCE_MODULE.find(CONSTRAINT_IMPORT_INSERTION_POINT)
        factory_pos = TEMPLATE_TESTRUN_SEQUENCE_MODULE.find(FACTORY_IMPORT_INSERTION_POINT)

        self.assertGreater(
            constraint_pos,
            -1,
            "CONSTRAINT_IMPORT_INSERTION_POINT should be found in template"
        )
        self.assertGreater(
            factory_pos,
            -1,
            "FACTORY_IMPORT_INSERTION_POINT should be found in template"
        )
        self.assertLess(
            constraint_pos,
            factory_pos,
            "Constraint import insertion point should appear before factory import insertion point"
        )

    def test_both_insertion_points_present_in_template(self):
        """
        Verify both insertion points are present in the template.

        **Validates: Requirements 3.3**
        """
        self.assertIn(
            CONSTRAINT_IMPORT_INSERTION_POINT,
            TEMPLATE_TESTRUN_SEQUENCE_MODULE,
            "Template should contain constraint import insertion point"
        )
        self.assertIn(
            FACTORY_IMPORT_INSERTION_POINT,
            TEMPLATE_TESTRUN_SEQUENCE_MODULE,
            "Template should contain factory import insertion point"
        )

    def test_insertion_points_on_separate_lines(self):
        """
        Verify insertion points appear on separate lines in the template.

        **Validates: Requirements 3.3**
        """
        lines = TEMPLATE_TESTRUN_SEQUENCE_MODULE.split('\n')
        constraint_lines = [line for line in lines if CONSTRAINT_IMPORT_INSERTION_POINT in line]
        factory_lines = [line for line in lines if FACTORY_IMPORT_INSERTION_POINT in line]

        self.assertEqual(
            len(constraint_lines),
            1,
            "CONSTRAINT_IMPORT_INSERTION_POINT should appear on exactly one line"
        )
        self.assertEqual(
            len(factory_lines),
            1,
            "FACTORY_IMPORT_INSERTION_POINT should appear on exactly one line"
        )


if __name__ == "__main__":
    unittest.main()
