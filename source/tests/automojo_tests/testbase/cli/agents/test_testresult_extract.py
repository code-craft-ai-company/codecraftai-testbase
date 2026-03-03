"""
    Tests for the testresult extract command.
"""

import os
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

from automojo.testbase.cli.cmdtree.agents.testresult.extract import command_agents_testresult_extract


SAMPLE_JSOS = """
{
    "name": "<session>",
    "instance": "(not-set)",
    "parent": null,
    "rtype": "JOB"
}

{
    "name": "pkg.mod#test_alpha",
    "instance": "bbb-222",
    "parent": "aaa-111",
    "rtype": "TEST",
    "result": "UNSET",
    "start": "2026-02-24T10:00:00",
    "stop": ""
}

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
"""


class TestResultExtractCommandTests(unittest.TestCase):
    """Tests for the testresult extract command."""

    def _write_jsos(self, content):
        fd, path = tempfile.mkstemp(suffix=".jsos")
        with os.fdopen(fd, "w") as fh:
            fh.write(content)
        return path

    def test_extract_returns_final_result(self):
        path = self._write_jsos(SAMPLE_JSOS)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_testresult_extract._callable(
                    results_file=path, testname="pkg.mod#test_alpha"
                )
            output = captured.getvalue()
            self.assertIn("result: PASSED", output)
            self.assertNotIn("UNSET", output)
        finally:
            os.unlink(path)

    def test_extract_includes_timing(self):
        path = self._write_jsos(SAMPLE_JSOS)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_testresult_extract._callable(
                    results_file=path, testname="pkg.mod#test_alpha"
                )
            output = captured.getvalue()
            self.assertIn("start: 2026-02-24T10:00:00", output)
            self.assertIn("stop: 2026-02-24T10:00:01", output)
        finally:
            os.unlink(path)

    def test_extract_includes_error_details(self):
        path = self._write_jsos(SAMPLE_JSOS)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_testresult_extract._callable(
                    results_file=path, testname="pkg.mod#test_beta"
                )
            output = captured.getvalue()
            self.assertIn("result: FAILED", output)
            self.assertIn("AssertionError: 3 != 4", output)
        finally:
            os.unlink(path)

    def test_extract_test_not_found_exits_nonzero(self):
        path = self._write_jsos(SAMPLE_JSOS)
        try:
            with self.assertRaises(SystemExit) as ctx:
                command_agents_testresult_extract._callable(
                    results_file=path, testname="nonexistent#test"
                )
            self.assertNotEqual(ctx.exception.code, 0)
        finally:
            os.unlink(path)

    def test_extract_file_not_found_exits_nonzero(self):
        with self.assertRaises(SystemExit) as ctx:
            command_agents_testresult_extract._callable(
                results_file="/nonexistent/path.jsos", testname="test"
            )
        self.assertNotEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
