"""
    .. module:: test_raises
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the ``raises`` exception-assertion context manager.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import re
import unittest

from ccai.errors.exceptions import SemanticError
from ccai.testbase.verification import raises


class _Specific(ValueError):
    """A subclass, to check that subclasses satisfy the expectation."""


class TestRaisesAcceptsTheExpected(unittest.TestCase):
    """
        Verifies the expected exception is caught and suppressed.
    """

    def test_the_expected_exception_is_suppressed(self):

        with raises(ValueError):
            raise ValueError("expected")

        # Reaching here is the assertion: the exception did not propagate.
        return

    def test_a_subclass_satisfies_the_expectation(self):

        with raises(ValueError):
            raise _Specific("a subclass is still a ValueError")

        return

    def test_any_of_a_tuple_of_types_is_accepted(self):

        with raises((ValueError, KeyError)):
            raise KeyError("second of the tuple")

        return


class TestRaisesBindsTheException(unittest.TestCase):
    """
        Verifies the caught exception is available for further assertions.
    """

    def test_the_exception_is_available_after_the_block(self):

        with raises(ValueError) as caught:
            raise ValueError("inst-a is not valid")

        self.assertIsInstance(caught.exception, ValueError)
        self.assertIn("inst-a", str(caught.exception))
        return

    def test_value_is_an_alias_of_exception(self):

        with raises(ValueError) as caught:
            raise ValueError("either name works")

        self.assertIs(caught.value, caught.exception)
        return

    def test_reading_the_exception_inside_the_block_is_rejected(self):

        # Returning None here would read as "no exception was raised" rather
        # than "you asked too early", so it is named instead.
        context = raises(ValueError)

        with self.assertRaises(SemanticError):
            with context:
                _unused = context.exception
                raise ValueError("never reached")

        return


class TestRaisesFailsWhenNothingIsRaised(unittest.TestCase):
    """
        Verifies a block that completes normally is a failure.
    """

    def test_a_block_that_does_not_raise_fails(self):

        with self.assertRaises(AssertionError):
            with raises(ValueError):
                pass

        return

    def test_the_failure_names_the_expected_type(self):

        try:
            with raises(ValueError):
                pass
        except AssertionError as xcpt:
            message = str(xcpt)
        else:
            self.fail("expected an AssertionError")

        self.assertIn("ValueError", message)
        self.assertIn("completed normally", message)
        return

    def test_the_failure_names_every_expected_type(self):

        try:
            with raises((ValueError, KeyError)):
                pass
        except AssertionError as xcpt:
            message = str(xcpt)
        else:
            self.fail("expected an AssertionError")

        self.assertIn("ValueError", message)
        self.assertIn("KeyError", message)
        return


class TestRaisesLetsOtherExceptionsThrough(unittest.TestCase):
    """
        Verifies an unexpected exception propagates rather than being reported.
    """

    def test_an_unexpected_exception_propagates(self):

        # Propagating preserves the real exception and its traceback, which
        # says more than an assertion describing it second-hand.
        with self.assertRaises(KeyError):
            with raises(ValueError):
                raise KeyError("not what was asked for")

        return

    def test_a_parent_class_does_not_satisfy_a_subclass_expectation(self):

        with self.assertRaises(ValueError):
            with raises(_Specific):
                raise ValueError("a ValueError is not a _Specific")

        return


class TestRaisesMatching(unittest.TestCase):
    """
        Verifies the optional text match.
    """

    def test_a_matching_pattern_passes(self):

        with raises(ValueError, match="invalid literal"):
            int("not a number")

        return

    def test_a_pattern_is_searched_not_anchored(self):

        with raises(ValueError, match="middle"):
            raise ValueError("text with middle inside it")

        return

    def test_a_compiled_pattern_is_accepted(self):

        with raises(ValueError, match=re.compile(r"inst-\d+")):
            raise ValueError("failed on inst-42")

        return

    def test_a_non_matching_pattern_fails(self):

        with self.assertRaises(AssertionError):
            with raises(ValueError, match="absent"):
                raise ValueError("something else entirely")

        return

    def test_the_match_failure_shows_the_pattern_and_the_text(self):

        try:
            with raises(ValueError, match="absent"):
                raise ValueError("something else entirely")
        except AssertionError as xcpt:
            message = str(xcpt)
        else:
            self.fail("expected an AssertionError")

        self.assertIn("absent", message)
        self.assertIn("something else entirely", message)
        return

    def test_a_wrong_type_still_propagates_when_matching(self):

        with self.assertRaises(KeyError):
            with raises(ValueError, match="anything"):
                raise KeyError("wrong type")

        return


if __name__ == "__main__":
    unittest.main()
