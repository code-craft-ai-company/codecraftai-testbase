"""
    Tests for the summary compare command.
"""

import json
import os
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

from automojo.testbase.cli.cmdtree.agents.summary.compare import command_agents_summary_compare


def _make_summary(result, passed, failed, errors, skipped, total):
    return {
        "result": result,
        "detail": {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "total": total,
        }
    }


class SummaryCompareCommandTests(unittest.TestCase):
    """Tests for the summary compare command."""

    def _write_summary(self, data):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as fh:
            json.dump(data, fh)
        return path

    def test_compare_stable_same_result(self):
        baseline = self._write_summary(_make_summary("PASSED", 5, 0, 0, 0, 5))
        current = self._write_summary(_make_summary("PASSED", 5, 0, 0, 0, 5))
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_summary_compare._callable(baseline=baseline, current=current)
            output = captured.getvalue()
            self.assertIn("PASSED (stable)", output)
        finally:
            os.unlink(baseline)
            os.unlink(current)

    def test_compare_regression(self):
        baseline = self._write_summary(_make_summary("PASSED", 5, 0, 0, 0, 5))
        current = self._write_summary(_make_summary("FAILED", 3, 2, 0, 0, 5))
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_summary_compare._callable(baseline=baseline, current=current)
            output = captured.getvalue()
            self.assertIn("PASSED->FAILED (regression)", output)
        finally:
            os.unlink(baseline)
            os.unlink(current)

    def test_compare_improvement(self):
        baseline = self._write_summary(_make_summary("FAILED", 3, 2, 0, 0, 5))
        current = self._write_summary(_make_summary("PASSED", 5, 0, 0, 0, 5))
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_summary_compare._callable(baseline=baseline, current=current)
            output = captured.getvalue()
            self.assertIn("FAILED->PASSED (improvement)", output)
        finally:
            os.unlink(baseline)
            os.unlink(current)

    def test_compare_includes_deltas(self):
        baseline = self._write_summary(_make_summary("PASSED", 5, 0, 0, 0, 5))
        current = self._write_summary(_make_summary("FAILED", 3, 2, 0, 0, 5))
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_summary_compare._callable(baseline=baseline, current=current)
            output = captured.getvalue()
            self.assertIn("passed: -2", output)
            self.assertIn("failed: +2", output)
            self.assertIn("total: 0", output)
        finally:
            os.unlink(baseline)
            os.unlink(current)

    def test_compare_file_not_found_exits_nonzero(self):
        current = self._write_summary(_make_summary("PASSED", 5, 0, 0, 0, 5))
        try:
            with self.assertRaises(SystemExit) as ctx:
                command_agents_summary_compare._callable(baseline="/nonexistent/path.json", current=current)
            self.assertNotEqual(ctx.exception.code, 0)
        finally:
            os.unlink(current)


if __name__ == "__main__":
    unittest.main()
