"""
    Tests for the testresult failures command.
"""

import os
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

from ccai.testbase.cli.cmdtree.agents.testresult.failures import command_agents_testresult_failures


SAMPLE_JSOS_WITH_FAILURES = """
{
    "name": "pkg.mod#test_alpha",
    "instance": "bbb-222",
    "parent": "aaa-111",
    "rtype": "TEST",
    "result": "PASSED",
    "start": "2026-02-24T10:00:00",
    "stop": "2026-02-24T10:00:01"
}

{
    "name": "pkg.mod#test_beta",
    "instance": "ccc-333",
    "parent": "aaa-111",
    "rtype": "TEST",
    "result": "FAILED",
    "start": "2026-02-24T10:00:01",
    "stop": "2026-02-24T10:00:02",
    "detail": {
        "errors": [{"message": "AssertionError: 3 != 4"}]
    }
}

{
    "name": "pkg.mod#test_gamma",
    "instance": "ddd-444",
    "parent": "aaa-111",
    "rtype": "TEST",
    "result": "ERRORED",
    "start": "2026-02-24T10:00:02",
    "stop": "2026-02-24T10:00:03",
    "detail": {
        "errors": [{"message": "ConnectionError: connection refused"}]
    }
}
"""

SAMPLE_JSOS_ALL_PASSED = """
{
    "name": "pkg.mod#test_alpha",
    "instance": "bbb-222",
    "parent": "aaa-111",
    "rtype": "TEST",
    "result": "PASSED",
    "start": "2026-02-24T10:00:00",
    "stop": "2026-02-24T10:00:01"
}
"""


class TestResultFailuresCommandTests(unittest.TestCase):
    """Tests for the testresult failures command."""

    def _write_jsos(self, content):
        fd, path = tempfile.mkstemp(suffix=".jsos")
        with os.fdopen(fd, "w") as fh:
            fh.write(content)
        return path

    def test_failures_lists_failed_tests(self):
        path = self._write_jsos(SAMPLE_JSOS_WITH_FAILURES)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_testresult_failures._callable(results_file=path)
            output = captured.getvalue()
            self.assertIn("pkg.mod#test_beta: FAILED", output)
            self.assertNotIn("test_alpha", output)
        finally:
            os.unlink(path)

    def test_failures_lists_errored_tests(self):
        path = self._write_jsos(SAMPLE_JSOS_WITH_FAILURES)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_testresult_failures._callable(results_file=path)
            output = captured.getvalue()
            self.assertIn("pkg.mod#test_gamma: ERRORED", output)
        finally:
            os.unlink(path)

    def test_failures_includes_error_summary(self):
        path = self._write_jsos(SAMPLE_JSOS_WITH_FAILURES)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_testresult_failures._callable(results_file=path)
            output = captured.getvalue()
            self.assertIn("AssertionError: 3 != 4", output)
            self.assertIn("ConnectionError: connection refused", output)
        finally:
            os.unlink(path)

    def test_failures_all_passed_message(self):
        path = self._write_jsos(SAMPLE_JSOS_ALL_PASSED)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_testresult_failures._callable(results_file=path)
            output = captured.getvalue()
            self.assertIn("All tests passed", output)
        finally:
            os.unlink(path)

    def test_failures_file_not_found_exits_nonzero(self):
        with self.assertRaises(SystemExit) as ctx:
            command_agents_testresult_failures._callable(results_file="/nonexistent/path.jsos")
        self.assertNotEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
