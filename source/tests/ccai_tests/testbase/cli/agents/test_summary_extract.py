"""
    Tests for the summary extract command.
"""

import json
import os
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

from ccai.testbase.cli.cmdtree.agents.summary.extract import command_agents_summary_extract


SAMPLE_SUMMARY = {
    "version": "2",
    "title": "Test Job",
    "runid": "(not-set)",
    "build": {
        "release": "(not-set)",
        "branch": "main",
        "build": "1.0.0",
        "flavor": "(not-set)",
        "url": "(not-set)"
    },
    "pipeline": {
        "id": "(not-set)",
        "name": "(not-set)",
        "instance": "(not-set)"
    },
    "job": {
        "id": "8344f668-a0e3-4ef6-89ca-acf007fcb3a0",
        "initiator": "(not-set)",
        "label": "(not-set)",
        "name": "(not-set)",
        "owner": "(not-set)",
        "type": "TestRun",
        "venue": "(not-set)",
        "seed": "(unknown)",
        "tag": "(not-set)"
    },
    "start": "2026-02-24T22:04:46.299524",
    "stop": "2026-02-24 22:04:50.357629",
    "result": "PASSED",
    "apod": "(not-set)",
    "totals": None,
    "running": {},
    "detail": {
        "errors": 0,
        "failed": 0,
        "skipped": 0,
        "passed": 3,
        "total": 3
    }
}


class SummaryExtractCommandTests(unittest.TestCase):
    """Tests for the summary extract command."""

    def _write_summary(self, data):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as fh:
            json.dump(data, fh)
        return path

    def test_extract_includes_result(self):
        path = self._write_summary(SAMPLE_SUMMARY)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_summary_extract._callable(summary_file=path)
            output = captured.getvalue()
            self.assertIn("result: PASSED", output)
        finally:
            os.unlink(path)

    def test_extract_includes_timing(self):
        path = self._write_summary(SAMPLE_SUMMARY)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_summary_extract._callable(summary_file=path)
            output = captured.getvalue()
            self.assertIn("start: 2026-02-24T22:04:46.299524", output)
            self.assertIn("stop: 2026-02-24 22:04:50.357629", output)
        finally:
            os.unlink(path)

    def test_extract_includes_detail_counters(self):
        path = self._write_summary(SAMPLE_SUMMARY)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_summary_extract._callable(summary_file=path)
            output = captured.getvalue()
            self.assertIn("passed: 3", output)
            self.assertIn("failed: 0", output)
            self.assertIn("total: 3", output)
        finally:
            os.unlink(path)

    def test_extract_includes_job_id_when_set(self):
        path = self._write_summary(SAMPLE_SUMMARY)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_summary_extract._callable(summary_file=path)
            output = captured.getvalue()
            self.assertIn("id: 8344f668-a0e3-4ef6-89ca-acf007fcb3a0", output)
        finally:
            os.unlink(path)

    def test_extract_omits_unset_job_name(self):
        path = self._write_summary(SAMPLE_SUMMARY)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_summary_extract._callable(summary_file=path)
            output = captured.getvalue()
            # Job name is "(not-set)" so should be omitted
            self.assertNotIn("name: (not-set)", output)
        finally:
            os.unlink(path)

    def test_extract_includes_build_branch_when_set(self):
        path = self._write_summary(SAMPLE_SUMMARY)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_summary_extract._callable(summary_file=path)
            output = captured.getvalue()
            self.assertIn("branch: main", output)
            self.assertIn("build: 1.0.0", output)
        finally:
            os.unlink(path)

    def test_extract_file_not_found_exits_nonzero(self):
        with self.assertRaises(SystemExit) as ctx:
            command_agents_summary_extract._callable(summary_file="/nonexistent/path.json")
        self.assertNotEqual(ctx.exception.code, 0)

    def test_extract_invalid_json_exits_nonzero(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as fh:
            fh.write("{ invalid json }")
        try:
            with self.assertRaises(SystemExit) as ctx:
                command_agents_summary_extract._callable(summary_file=path)
            self.assertNotEqual(ctx.exception.code, 0)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
