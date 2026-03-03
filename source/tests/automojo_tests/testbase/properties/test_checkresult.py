"""
    .. module:: automojo_tests.testbase.properties.test_checkresult
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the CheckResult result model.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

import unittest
import uuid

from automojo.testbase.results.model.checkresult import CheckResult
from automojo.testbase.results.model.resultcode import ResultCode
from automojo.testbase.results.model.resulttype import ResultType


class CheckResultConstructionTests(unittest.TestCase):
    """Tests for CheckResult initialization."""

    def test_construction_sets_fields(self):
        """Test that constructor properly sets all fields."""
        gen_vals = {"x": 42, "y": "hello"}
        cr = CheckResult(
            inst_id="inst-001",
            name="check_0001",
            parent_inst="parent-001",
            generated_values=gen_vals,
            example_index=0,
            seed=12345
        )

        self.assertEqual(cr.inst_id, "inst-001")
        self.assertEqual(cr.name, "check_0001")
        self.assertEqual(cr.parent_inst, "parent-001")
        self.assertEqual(cr.generated_values, gen_vals)
        self.assertEqual(cr.example_index, 0)
        self.assertEqual(cr.seed, 12345)

    def test_construction_default_result_code(self):
        """Test that default result code is UNSET."""
        cr = CheckResult("i", "n", "p", {}, 0, 0)
        self.assertEqual(cr.result_code, ResultCode.UNSET)

    def test_construction_custom_result_code(self):
        """Test providing a custom result code."""
        cr = CheckResult("i", "n", "p", {}, 0, 0, result_code=ResultCode.PASSED)
        self.assertEqual(cr.result_code, ResultCode.PASSED)

    def test_result_type_is_check(self):
        """Test that the result type is always CHECK."""
        cr = CheckResult("i", "n", "p", {}, 0, 0)
        self.assertEqual(cr.result_type, ResultType.CHECK)


class CheckResultSerializationTests(unittest.TestCase):
    """Tests for CheckResult.as_dict() serialization."""

    def test_as_dict_preview_mode(self):
        """Test as_dict in preview mode (no detail section)."""
        gen_vals = {"x": 42, "name": "test"}
        cr = CheckResult("inst-001", "check_0001", "parent-001", gen_vals, 5, 99999)

        d = cr.as_dict(is_preview=True)

        self.assertEqual(d["name"], "check_0001")
        self.assertEqual(d["instance"], "inst-001")
        self.assertEqual(d["parent"], "parent-001")
        self.assertEqual(d["rtype"], "CHECK")
        self.assertEqual(d["generated_values"], gen_vals)
        self.assertEqual(d["example_index"], 5)
        self.assertEqual(d["seed"], 99999)
        self.assertNotIn("detail", d)

    def test_as_dict_full_mode(self):
        """Test as_dict in full mode (with detail section)."""
        cr = CheckResult("inst-001", "check_0001", "parent-001", {"x": 1}, 0, 123)

        d = cr.as_dict(is_preview=False)

        self.assertIn("detail", d)
        self.assertIn("errors", d["detail"])
        self.assertIn("failures", d["detail"])
        self.assertIn("warnings", d["detail"])

    def test_as_dict_non_serializable_values(self):
        """Test that non-JSON-serializable generated values are converted to repr."""
        gen_vals = {"obj": object()}
        cr = CheckResult("inst-001", "check_0001", "parent-001", gen_vals, 0, 0)

        d = cr.as_dict(is_preview=True)

        # Non-serializable should be converted to repr string
        self.assertIsInstance(d["generated_values"]["obj"], str)

    def test_as_dict_includes_start_stop(self):
        """Test that start and stop times are included."""
        cr = CheckResult("inst-001", "check_0001", "parent-001", {}, 0, 0)

        d = cr.as_dict(is_preview=True)

        self.assertIn("start", d)
        self.assertIn("stop", d)


class CheckResultFinalizeTests(unittest.TestCase):
    """Tests for CheckResult finalize behavior."""

    def test_finalize_passed(self):
        """Test that finalize sets PASSED when no errors or failures."""
        cr = CheckResult("i", "n", "p", {}, 0, 0)
        cr.finalize()
        self.assertEqual(cr.result_code, ResultCode.PASSED)

    def test_finalize_failed_with_failure(self):
        """Test that finalize sets FAILED when failures exist."""
        from automojo.errors.xtraceback import TracebackDetail
        cr = CheckResult("i", "n", "p", {}, 0, 0)
        tb = TracebackDetail(extype="AssertionError", exargs=["fail"], traces=[])
        cr.add_failure(tb)
        cr.finalize()
        self.assertEqual(cr.result_code, ResultCode.FAILED)

    def test_finalize_errored_with_error(self):
        """Test that finalize sets ERRORED when errors exist."""
        from automojo.errors.xtraceback import TracebackDetail
        cr = CheckResult("i", "n", "p", {}, 0, 0)
        tb = TracebackDetail(extype="RuntimeError", exargs=["err"], traces=[])
        cr.add_error(tb)
        cr.finalize()
        self.assertEqual(cr.result_code, ResultCode.ERRORED)


class CheckResultFormatTests(unittest.TestCase):
    """Tests for CheckResult.format_result() output."""

    def test_format_result_includes_name(self):
        """Test that format_result includes the check name."""
        cr = CheckResult("i", "check_0005", "p", {"x": 10}, 5, 0)
        cr.finalize()
        lines = cr.format_result()
        text = "\n".join(lines)
        self.assertIn("check_0005", text)

    def test_format_result_includes_generated_values(self):
        """Test that format_result includes generated values."""
        cr = CheckResult("i", "check_0001", "p", {"x": 42, "y": "abc"}, 0, 0)
        cr.finalize()
        lines = cr.format_result()
        text = "\n".join(lines)
        self.assertIn("x=42", text)
        self.assertIn("y='abc'", text)


if __name__ == '__main__':
    unittest.main()
