"""
    .. module:: test_parameterization
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the ``parametrize`` declaration decorator.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import inspect
import unittest

from ccai.testbase.declaration.parameterization import (
    parametrize, ParametrizedCaseError
)


class TestParametrizeExpansion(unittest.TestCase):
    """
        Verifies that every case runs, with the right arguments.
    """

    def test_single_name_runs_every_case(self):
        seen = []

        @parametrize("value", ["a", "b", "c"])
        def sample(value):
            seen.append(value)
            return

        sample()

        self.assertEqual(seen, ["a", "b", "c"])
        return

    def test_multiple_names_unpack_positionally(self):
        seen = []

        @parametrize("left,right", [(1, 2), (3, 4)])
        def sample(left, right):
            seen.append((left, right))
            return

        sample()

        self.assertEqual(seen, [(1, 2), (3, 4)])
        return

    def test_names_accepted_as_a_sequence(self):
        seen = []

        @parametrize(["left", "right"], [(1, 2)])
        def sample(left, right):
            seen.append((left, right))
            return

        sample()

        self.assertEqual(seen, [(1, 2)])
        return

    def test_a_list_per_case_is_accepted(self):
        seen = []

        @parametrize("left,right", [[1, 2], [3, 4]])
        def sample(left, right):
            seen.append((left, right))
            return

        sample()

        self.assertEqual(seen, [(1, 2), (3, 4)])
        return


class TestParametrizeInjectionInterop(unittest.TestCase):
    """
        Verifies the decorator hides its own parameters from the injector.

        This is the load-bearing behaviour.  testbase resolves a test's
        parameters by inspecting its signature, so a parametrized name left in
        place is reported as an unresolvable parameter and the test never runs —
        the decorator supplies it, but the injector cannot know that.
    """

    def test_parametrized_names_are_removed_from_the_signature(self):

        @parametrize("value", [1])
        def sample(value, credential, tmp_path):
            return

        visible = list(inspect.signature(sample).parameters)

        self.assertEqual(visible, ["credential", "tmp_path"])
        return

    def test_injected_arguments_reach_the_test(self):
        seen = []

        @parametrize("value", [1, 2])
        def sample(value, credential):
            seen.append((value, credential))
            return

        sample(credential="cred")

        self.assertEqual(seen, [(1, "cred"), (2, "cred")])
        return

    def test_injected_arguments_may_be_positional(self):
        seen = []

        @parametrize("value", [1, 2])
        def sample(credential, value):
            seen.append((credential, value))
            return

        sample("cred")

        self.assertEqual(seen, [("cred", 1), ("cred", 2)])
        return


class TestParametrizeFailureReporting(unittest.TestCase):
    """
        Verifies that all cases run and every failure is reported.
    """

    def test_every_case_runs_even_after_a_failure(self):
        seen = []

        @parametrize("value", [1, 2, 3])
        def sample(value):
            seen.append(value)
            assert value != 2, "two is bad"
            return

        with self.assertRaises(ParametrizedCaseError):
            sample()

        self.assertEqual(seen, [1, 2, 3])
        return

    def test_the_error_names_the_failing_arguments(self):

        @parametrize("value", [1, 2])
        def sample(value):
            assert value != 2, "two is bad"
            return

        with self.assertRaises(ParametrizedCaseError) as caught:
            sample()

        message = str(caught.exception)

        self.assertIn("1 of 2", message)
        self.assertIn("value=2", message)
        self.assertIn("two is bad", message)
        return

    def test_all_failures_are_reported_together(self):

        @parametrize("value", [1, 2, 3])
        def sample(value):
            raise ValueError("no good: {}".format(value))

        with self.assertRaises(ParametrizedCaseError) as caught:
            sample()

        message = str(caught.exception)

        self.assertIn("3 of 3", message)
        for value in (1, 2, 3):
            self.assertIn("value={}".format(value), message)
        return

    def test_a_case_failure_is_a_failure_not_an_error(self):

        @parametrize("value", [1])
        def sample(value):
            raise ValueError("boom")

        # A failing case means the assertion under test did not hold, which
        # reports differently from a test that could not run at all.
        self.assertTrue(issubclass(ParametrizedCaseError, AssertionError))

        with self.assertRaises(AssertionError):
            sample()
        return

    def test_passing_cases_return_none(self):

        @parametrize("value", [1, 2])
        def sample(value):
            return "ignored"

        self.assertIsNone(sample())
        return


class TestParametrizeRejectsBadDeclarations(unittest.TestCase):
    """
        Verifies mistakes are caught at decoration time, not mid-run.
    """

    def test_case_arity_must_match_the_names(self):

        with self.assertRaises(ValueError) as caught:
            parametrize("left,right", [(1, 2), (3,)])

        self.assertIn("expects 2 values per case", str(caught.exception))
        return

    def test_a_bare_value_for_multiple_names_is_rejected(self):

        with self.assertRaises(ValueError) as caught:
            parametrize("left,right", [1])

        self.assertIn("tuple or list per case", str(caught.exception))
        return

    def test_an_empty_case_list_is_rejected(self):

        # A test that runs zero times passes, which reads as coverage that
        # is not there.
        with self.assertRaises(ValueError):
            parametrize("value", [])
        return

    def test_no_names_is_rejected(self):

        with self.assertRaises(ValueError):
            parametrize("", [1])
        return

    def test_a_name_the_test_does_not_take_is_rejected(self):

        decorator = parametrize("missing", [1])

        with self.assertRaises(ValueError) as caught:
            decorator(lambda value: None)

        self.assertIn("does not take", str(caught.exception))
        return


if __name__ == "__main__":
    unittest.main()
