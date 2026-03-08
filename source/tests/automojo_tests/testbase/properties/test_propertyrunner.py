"""
    .. module:: automojo_tests.testbase.properties.test_propertyrunner
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the PropertyRunner and seed derivation.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

import unittest
import random

from automojo.testbase.properties.propertyrunner import PropertyRunner, derive_test_seed
from automojo.testbase.properties.strategies import integers, text, booleans
from automojo.testbase.properties.assumptions import assume, UnsatisfiedAssumption

from automojo.testbase.results.model.checkresult import CheckResult
from automojo.testbase.results.model.resultcode import ResultCode


class MockRecorder:
    """
        A mock recorder that captures preview and record calls
        for verifying PropertyRunner behavior without requiring
        the full ResultRecorder infrastructure.
    """

    def __init__(self):
        self.previewed = []
        self.recorded = []

    def preview(self, result_node):
        self.previewed.append(result_node)

    def record(self, result_node):
        self.recorded.append(result_node)


class SeedDerivationTests(unittest.TestCase):
    """Tests for derive_test_seed()."""

    def test_deterministic(self):
        """Test that same inputs always produce same seed."""
        s1 = derive_test_seed(12345, "pkg.module#test_func")
        s2 = derive_test_seed(12345, "pkg.module#test_func")
        self.assertEqual(s1, s2)

    def test_different_test_names_different_seeds(self):
        """Test that different test names produce different seeds."""
        s1 = derive_test_seed(12345, "test_a")
        s2 = derive_test_seed(12345, "test_b")
        self.assertNotEqual(s1, s2)

    def test_different_job_seeds_different_seeds(self):
        """Test that different job seeds produce different seeds."""
        s1 = derive_test_seed(111, "test_a")
        s2 = derive_test_seed(222, "test_a")
        self.assertNotEqual(s1, s2)

    def test_returns_int(self):
        """Test that the derived seed is an integer."""
        s = derive_test_seed(42, "test")
        self.assertIsInstance(s, int)


class PropertyRunnerConstructionTests(unittest.TestCase):
    """Tests for PropertyRunner initialization."""

    def test_construction_with_defaults(self):
        """Test PropertyRunner construction with default constraints."""
        recorder = MockRecorder()
        runner = PropertyRunner({}, 12345, "test_func", recorder, "parent-001")

        self.assertEqual(runner.job_seed, 12345)
        self.assertIsInstance(runner.test_seed, int)

    def test_construction_always_derives_seed_from_job_seed(self):
        """Test that seed is always derived from job_seed + test_name."""
        recorder = MockRecorder()
        runner = PropertyRunner({}, 12345, "test_func", recorder, "parent-001")

        expected = derive_test_seed(12345, "test_func")
        self.assertEqual(runner.test_seed, expected)

    def test_construction_with_custom_constraints(self):
        """Test PropertyRunner construction with custom constraints."""
        constraints = {"max_examples": 50, "max_shrink_attempts": 25}
        recorder = MockRecorder()
        runner = PropertyRunner(constraints, 12345, "test_func", recorder, "parent-001")

        self.assertEqual(runner._max_examples, 50)
        self.assertEqual(runner._max_shrink_attempts, 25)

    def test_construction_defaults_max_examples(self):
        """Test that max_examples defaults to 100 when not in constraints."""
        recorder = MockRecorder()
        runner = PropertyRunner({}, 12345, "test_func", recorder, "parent-001")

        self.assertEqual(runner._max_examples, 100)

    def test_construction_defaults_max_shrink_attempts(self):
        """Test that max_shrink_attempts defaults to 100 when not in constraints."""
        recorder = MockRecorder()
        runner = PropertyRunner({}, 12345, "test_func", recorder, "parent-001")

        self.assertEqual(runner._max_shrink_attempts, 100)


class PropertyRunnerExecutionTests(unittest.TestCase):
    """Tests for PropertyRunner.run() execution."""

    def test_run_all_pass(self):
        """Test that a passing property test records PASSED CheckResults."""
        constraints = {"max_examples": 10}
        recorder = MockRecorder()
        runner = PropertyRunner(constraints, 42, "test_add_comm", recorder, "parent-001")

        def test_func(x, y):
            assert x + y == y + x

        strategies = {"x": integers(0, 100), "y": integers(0, 100)}
        metadata = runner.run(test_func, strategies, {})

        self.assertEqual(metadata["examples_run"], 10)
        self.assertEqual(metadata["max_examples"], 10)
        self.assertTrue(metadata["is_property_test"])
        self.assertNotIn("counterexample", metadata)

        # All 10 checks should be recorded
        self.assertEqual(len(recorder.recorded), 10)
        for cr in recorder.recorded:
            self.assertIsInstance(cr, CheckResult)
            self.assertEqual(cr.result_code, ResultCode.PASSED)

    def test_run_detects_failure(self):
        """Test that PropertyRunner detects and reports a failing property."""
        constraints = {"max_examples": 100}
        recorder = MockRecorder()
        runner = PropertyRunner(constraints, 42, "test_bad", recorder, "parent-001")

        def test_func(x):
            assert x < 50  # Will fail for x >= 50

        strategies = {"x": integers(0, 100)}

        with self.assertRaises(AssertionError) as ctx:
            runner.run(test_func, strategies, {})

        self.assertIn("falsified", str(ctx.exception).lower())

    def test_run_records_failed_check(self):
        """Test that a failing check is recorded with FAILED status."""
        constraints = {"max_examples": 100}
        recorder = MockRecorder()
        runner = PropertyRunner(constraints, 42, "test_bad", recorder, "parent-001")

        def test_func(x):
            assert x < 50

        strategies = {"x": integers(0, 100)}

        try:
            runner.run(test_func, strategies, {})
        except AssertionError:
            pass

        # At least one check should be FAILED
        failed_checks = [cr for cr in recorder.recorded if cr.result_code == ResultCode.FAILED]
        self.assertGreater(len(failed_checks), 0)

    def test_run_records_error_check(self):
        """Test that an unexpected error is recorded with ERRORED status."""
        constraints = {"max_examples": 10}
        recorder = MockRecorder()
        runner = PropertyRunner(constraints, 42, "test_err", recorder, "parent-001")

        def test_func(x):
            raise RuntimeError("unexpected")

        strategies = {"x": integers(0, 10)}

        with self.assertRaises(RuntimeError):
            runner.run(test_func, strategies, {})

        # First check should be ERRORED
        self.assertEqual(len(recorder.recorded), 1)
        self.assertEqual(recorder.recorded[0].result_code, ResultCode.ERRORED)

    def test_run_with_injected_args(self):
        """Test that injected args are merged with generated args."""
        constraints = {"max_examples": 5}
        recorder = MockRecorder()
        runner = PropertyRunner(constraints, 42, "test_inject", recorder, "parent-001")

        captured_args = []

        def test_func(x, injected_param):
            captured_args.append({"x": x, "injected_param": injected_param})

        strategies = {"x": integers(0, 10)}
        injected = {"injected_param": "fixed_value"}

        runner.run(test_func, strategies, injected)

        self.assertEqual(len(captured_args), 5)
        for args in captured_args:
            self.assertEqual(args["injected_param"], "fixed_value")
            self.assertIsInstance(args["x"], int)

    def test_run_metadata_includes_strategies(self):
        """Test that run metadata includes strategy descriptions."""
        constraints = {"max_examples": 5}
        recorder = MockRecorder()
        runner = PropertyRunner(constraints, 42, "test_meta", recorder, "parent-001")

        def test_func(x, name):
            pass

        strategies = {"x": integers(0, 10), "name": text(max_size=5)}
        metadata = runner.run(test_func, strategies, {})

        self.assertIn("strategy_descriptions", metadata)
        self.assertIn("x", metadata["strategy_descriptions"])
        self.assertIn("name", metadata["strategy_descriptions"])

    def test_run_metadata_includes_seed_info(self):
        """Test that run metadata includes seed and job_seed."""
        constraints = {"max_examples": 5}
        recorder = MockRecorder()
        runner = PropertyRunner(constraints, 999, "test_seed", recorder, "parent-001")

        def test_func(x):
            pass

        strategies = {"x": integers()}
        metadata = runner.run(test_func, strategies, {})

        expected_seed = derive_test_seed(999, "test_seed")
        self.assertEqual(metadata["seed"], expected_seed)
        self.assertEqual(metadata["job_seed"], 999)

    def test_run_check_names_sequential(self):
        """Test that check names are sequential (check_0000, check_0001, ...)."""
        constraints = {"max_examples": 5}
        recorder = MockRecorder()
        runner = PropertyRunner(constraints, 42, "test_names", recorder, "parent-001")

        def test_func(x):
            pass

        strategies = {"x": integers()}
        runner.run(test_func, strategies, {})

        for i, cr in enumerate(recorder.recorded):
            self.assertEqual(cr.name, f"check_{i:04d}")


class PropertyRunnerShrinkingTests(unittest.TestCase):
    """Tests for the PropertyRunner shrinking engine."""

    def test_shrinking_finds_simpler_counterexample(self):
        """Test that shrinking produces a simpler failing input."""
        constraints = {"max_examples": 200, "max_shrink_attempts": 50}
        recorder = MockRecorder()
        runner = PropertyRunner(constraints, 42, "test_shrink", recorder, "parent-001")

        def test_func(x):
            assert x < 10  # Fail for x >= 10

        strategies = {"x": integers(0, 100)}

        try:
            runner.run(test_func, strategies, {})
        except AssertionError as e:
            # The counterexample should be shrunk toward the boundary (10)
            msg = str(e)
            self.assertIn("counterexample", msg.lower())

    def test_shrinking_respects_max_attempts(self):
        """Test that shrinking is bounded by max_shrink_attempts."""
        constraints = {"max_examples": 200, "max_shrink_attempts": 3}
        recorder = MockRecorder()
        runner = PropertyRunner(constraints, 42, "test_bounded", recorder, "parent-001")

        def test_func(x):
            assert x < 10

        strategies = {"x": integers(0, 100)}

        try:
            runner.run(test_func, strategies, {})
        except AssertionError:
            pass
        # Just verify it completes without hanging


class PropertyRunnerReproducibilityTests(unittest.TestCase):
    """Tests for seed-based reproducibility of property test runs."""

    def test_same_job_seed_same_results(self):
        """Test that the same job seed + test name produces the same sequence."""
        captured1 = []
        captured2 = []

        def make_test(captured):
            def test_func(x, y):
                captured.append((x, y))
            return test_func

        strategies = {"x": integers(0, 100), "y": text(max_size=5)}

        # Run 1
        constraints = {"max_examples": 20}
        recorder1 = MockRecorder()
        runner1 = PropertyRunner(constraints, 999, "test_repro", recorder1, "p1")
        runner1.run(make_test(captured1), strategies, {})

        # Run 2 — same job_seed and test_name
        recorder2 = MockRecorder()
        runner2 = PropertyRunner(constraints, 999, "test_repro", recorder2, "p2")
        runner2.run(make_test(captured2), strategies, {})

        self.assertEqual(captured1, captured2)

    def test_different_job_seeds_different_results(self):
        """Test that different job seeds produce different results."""
        captured1 = []
        captured2 = []

        def make_test(captured):
            def test_func(x):
                captured.append(x)
            return test_func

        strategies = {"x": integers(0, 1000000)}
        constraints = {"max_examples": 20}

        recorder1 = MockRecorder()
        runner1 = PropertyRunner(constraints, 111, "test_diff", recorder1, "p1")
        runner1.run(make_test(captured1), strategies, {})

        recorder2 = MockRecorder()
        runner2 = PropertyRunner(constraints, 222, "test_diff", recorder2, "p2")
        runner2.run(make_test(captured2), strategies, {})

        self.assertNotEqual(captured1, captured2)

    def test_different_test_names_different_results(self):
        """Test that different test names with same job seed produce different results."""
        captured1 = []
        captured2 = []

        def make_test(captured):
            def test_func(x):
                captured.append(x)
            return test_func

        strategies = {"x": integers(0, 1000000)}
        constraints = {"max_examples": 20}

        recorder1 = MockRecorder()
        runner1 = PropertyRunner(constraints, 999, "test_a", recorder1, "p1")
        runner1.run(make_test(captured1), strategies, {})

        recorder2 = MockRecorder()
        runner2 = PropertyRunner(constraints, 999, "test_b", recorder2, "p2")
        runner2.run(make_test(captured2), strategies, {})

        self.assertNotEqual(captured1, captured2)


class PropertyRunnerAssumeTests(unittest.TestCase):
    """Tests for assume() integration with PropertyRunner."""

    def test_assume_skips_invalid_examples(self):
        """Test that assume(False) causes the example to be skipped."""
        constraints = {"max_examples": 10}
        recorder = MockRecorder()
        runner = PropertyRunner(constraints, 42, "test_assume", recorder, "parent-001")

        call_count = [0]

        def test_func(x):
            assume(x > 50)  # Skip roughly half the examples
            call_count[0] += 1

        strategies = {"x": integers(0, 100)}
        metadata = runner.run(test_func, strategies, {})

        # Should have run exactly 10 passing examples
        self.assertEqual(metadata["examples_run"], 10)
        # Some assumptions should have been rejected
        self.assertGreater(metadata["assumptions_rejected"], 0)

    def test_assume_true_is_noop(self):
        """Test that assume(True) has no effect."""
        constraints = {"max_examples": 5}
        recorder = MockRecorder()
        runner = PropertyRunner(constraints, 42, "test_assume_true", recorder, "parent-001")

        def test_func(x):
            assume(True)

        strategies = {"x": integers(0, 10)}
        metadata = runner.run(test_func, strategies, {})

        self.assertEqual(metadata["examples_run"], 5)
        self.assertEqual(metadata["assumptions_rejected"], 0)

    def test_assume_no_check_result_for_skipped(self):
        """Test that skipped examples don't produce CheckResults."""
        constraints = {"max_examples": 5}
        recorder = MockRecorder()
        runner = PropertyRunner(constraints, 42, "test_no_check", recorder, "parent-001")

        def test_func(x):
            assume(x > 50)

        strategies = {"x": integers(0, 100)}
        metadata = runner.run(test_func, strategies, {})

        # Only passing examples should have CheckResults
        passed_checks = [cr for cr in recorder.recorded
                         if cr.result_code == ResultCode.PASSED]
        self.assertEqual(len(passed_checks), 5)
        self.assertEqual(metadata["examples_run"], 5)

    def test_assume_too_many_rejections_aborts(self):
        """Test that too many assumption rejections cause an error."""
        constraints = {"max_examples": 2}
        recorder = MockRecorder()
        runner = PropertyRunner(constraints, 42, "test_abort", recorder, "parent-001")

        def test_func(x):
            assume(False)  # Always reject

        strategies = {"x": integers(0, 10)}

        with self.assertRaises(RuntimeError) as ctx:
            runner.run(test_func, strategies, {})

        self.assertIn("too many assumption rejections", str(ctx.exception).lower())

    def test_assume_metadata_includes_rejection_count(self):
        """Test that assumptions_rejected appears in metadata."""
        constraints = {"max_examples": 10}
        recorder = MockRecorder()
        runner = PropertyRunner(constraints, 42, "test_meta", recorder, "parent-001")

        def test_func(x):
            assume(x % 2 == 0)

        strategies = {"x": integers(0, 100)}
        metadata = runner.run(test_func, strategies, {})

        self.assertIn("assumptions_rejected", metadata)
        self.assertIsInstance(metadata["assumptions_rejected"], int)


if __name__ == '__main__':
    unittest.main()
