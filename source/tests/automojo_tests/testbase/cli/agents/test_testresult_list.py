"""
    Tests for the testresult list command.
"""

import os
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

from automojo.testbase.cli.cmdtree.agents.testresult.list import command_agents_testresult_list


SAMPLE_JSOS = """
{
    "name": "<session>",
    "instance": "(not-set)",
    "parent": null,
    "rtype": "JOB"
}

{
    "name": "pkg.mod",
    "instance": "aaa-111",
    "parent": "(not-set)",
    "rtype": "TEST_CONTAINER"
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
    "stop": "2026-02-24T10:00:02"
}

{
    "name": "pkg.mod#test_gamma",
    "instance": "ddd-444",
    "parent": "aaa-111",
    "rtype": "TEST",
    "result": "SKIPPED",
    "start": "2026-02-24T10:00:02",
    "stop": "2026-02-24T10:00:02"
}
"""


class TestResultListCommandTests(unittest.TestCase):
    """Tests for the testresult list command."""

    def _write_jsos(self, content):
        fd, path = tempfile.mkstemp(suffix=".jsos")
        with os.fdopen(fd, "w") as fh:
            fh.write(content)
        return path

    def test_list_all_tests(self):
        path = self._write_jsos(SAMPLE_JSOS)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_testresult_list._callable(results_file=path, result_filter=None)
            output = captured.getvalue()
            self.assertIn("pkg.mod#test_alpha: PASSED", output)
            self.assertIn("pkg.mod#test_beta: FAILED", output)
            self.assertIn("pkg.mod#test_gamma: SKIPPED", output)
        finally:
            os.unlink(path)

    def test_list_excludes_containers(self):
        path = self._write_jsos(SAMPLE_JSOS)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_testresult_list._callable(results_file=path, result_filter=None)
            output = captured.getvalue()
            self.assertNotIn("<session>", output)
            self.assertNotIn("TEST_CONTAINER", output)
        finally:
            os.unlink(path)

    def test_list_filter_by_failed(self):
        path = self._write_jsos(SAMPLE_JSOS)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_testresult_list._callable(results_file=path, result_filter="FAILED")
            output = captured.getvalue()
            self.assertIn("pkg.mod#test_beta: FAILED", output)
            self.assertNotIn("test_alpha", output)
            self.assertNotIn("test_gamma", output)
        finally:
            os.unlink(path)

    def test_list_filter_no_matches(self):
        path = self._write_jsos(SAMPLE_JSOS)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_testresult_list._callable(results_file=path, result_filter="ERRORED")
            output = captured.getvalue()
            self.assertIn("No tests with result 'ERRORED' found", output)
        finally:
            os.unlink(path)

    def test_list_file_not_found_exits_nonzero(self):
        with self.assertRaises(SystemExit) as ctx:
            command_agents_testresult_list._callable(
                results_file="/nonexistent/path.jsos", result_filter=None
            )
        self.assertNotEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
