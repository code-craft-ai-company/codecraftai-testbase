"""
    Tests for :func:`ccai.testbase.properties.run_property`.
"""

import unittest

from ccai.testbase.properties import assume, run_property
from ccai.testbase.properties import strategies as st


class RunPropertyTests(unittest.TestCase):

    def test_runs_the_requested_number_of_examples(self) -> None:
        seen = []

        def check(value: int) -> None:
            seen.append(value)
            self.assertTrue(0 <= value <= 10)

        count = run_property(check, 25, value=st.integers(min_value=0, max_value=10))

        self.assertEqual(count, 25)
        self.assertEqual(len(seen), 25)
        return

    def test_examples_are_reproducible_for_a_seed(self) -> None:
        first = []
        second = []

        run_property(lambda value: first.append(value), 20, seed=7, value=st.integers())
        run_property(lambda value: second.append(value), 20, seed=7, value=st.integers())

        self.assertEqual(first, second)
        return

    def test_rejected_assumptions_are_not_counted(self) -> None:
        accepted = []

        def check(value: int) -> None:
            assume(value % 2 == 0)
            accepted.append(value)

        count = run_property(check, 15, value=st.integers(min_value=0, max_value=100))

        self.assertEqual(count, 15)
        self.assertEqual(len(accepted), 15)
        self.assertTrue(all(value % 2 == 0 for value in accepted))
        return

    def test_unsatisfiable_assumptions_raise(self) -> None:
        def check(value: int) -> None:
            assume(False)

        with self.assertRaises(RuntimeError):
            run_property(check, 2, value=st.integers())
        return

    def test_failure_propagates_without_a_case(self) -> None:
        def check(value: int) -> None:
            self.assertLess(value, 0)

        with self.assertRaises(AssertionError):
            run_property(check, 3, value=st.integers(min_value=1, max_value=5))
        return

    def test_failure_is_recorded_on_the_case_subtest(self) -> None:
        class Probe(unittest.TestCase):
            def runTest(self) -> None:
                run_property(lambda value: self.assertLess(value, 0), 3, case=self,
                             value=st.integers(min_value=1, max_value=5))
                return

        result = unittest.TestResult()
        Probe().run(result)

        self.assertEqual(len(result.failures), 3)
        return


if __name__ == "__main__":
    unittest.main()
