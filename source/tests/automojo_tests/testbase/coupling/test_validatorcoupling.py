"""
    .. module:: automojo_tests.testbase.coupling.test_validatorcoupling
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for ValidatorCoupling class.

    .. moduleauthor:: AutomationX
"""

import unittest

from automojo.testbase.coupling.validatorcoupling import ValidatorCoupling
from automojo.errors.exceptions import AbstractMethodError


class DerivedValidatorCoupling(ValidatorCoupling):
    """A derived ValidatorCoupling class that implements attach_to_test for testing."""

    def __init__(self):
        self.attached_testscope = None
        self.attached_suffix = None

    def attach_to_test(self, testscope, suffix: str):
        """Implementation of attach_to_test that stores the parameters."""
        self.attached_testscope = testscope
        self.attached_suffix = suffix


class ValidatorCouplingTests(unittest.TestCase):
    """Tests for the ValidatorCoupling class."""

    def test_attach_to_test_raises_abstract_method_error(self):
        """Test that attach_to_test raises AbstractMethodError when called on base class."""
        validator = ValidatorCoupling()
        with self.assertRaises(AbstractMethodError):
            validator.attach_to_test(testscope=None, suffix="test_suffix")

    def test_derived_class_attach_to_test_accepts_testscope_parameter(self):
        """Test that derived class attach_to_test accepts testscope parameter (Requirement 10.2)."""
        validator = DerivedValidatorCoupling()
        mock_testscope = object()
        
        validator.attach_to_test(testscope=mock_testscope, suffix="suffix")
        
        self.assertEqual(validator.attached_testscope, mock_testscope)

    def test_derived_class_attach_to_test_accepts_suffix_parameter(self):
        """Test that derived class attach_to_test accepts suffix string parameter (Requirement 10.3)."""
        validator = DerivedValidatorCoupling()
        test_suffix = "my_test_suffix"
        
        validator.attach_to_test(testscope=None, suffix=test_suffix)
        
        self.assertEqual(validator.attached_suffix, test_suffix)

    def test_derived_class_attach_to_test_does_not_raise(self):
        """Test that derived class implementing attach_to_test does not raise AbstractMethodError."""
        validator = DerivedValidatorCoupling()
        
        # Should not raise any exception
        validator.attach_to_test(testscope=object(), suffix="suffix")


if __name__ == "__main__":
    unittest.main()
