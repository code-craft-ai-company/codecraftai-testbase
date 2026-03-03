"""
    Tests for the config extract command.
"""

import json
import os
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

from automojo.testbase.cli.cmdtree.agents.config.extract import command_agents_config_extract


SAMPLE_CONFIG = {
    "testroot": "/Users/myron/automojo/tests",
    "output_directory": "/Users/myron/automojo/results",
    "runid": "abc-123-def",
    "starttime": "2026-02-24T22:04:46.299524",
    "console_log_level": "WARNING",
    "file_log_level": "DEBUG",
    "debugger": None,
    "breakpoints": None,
}


class ConfigExtractCommandTests(unittest.TestCase):
    """Tests for the config extract command."""

    def _write_config(self, data):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as fh:
            json.dump(data, fh)
        return path

    def test_extract_includes_testroot(self):
        path = self._write_config(SAMPLE_CONFIG)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_config_extract._callable(config_file=path)
            output = captured.getvalue()
            self.assertIn("testroot: /Users/myron/automojo/tests", output)
        finally:
            os.unlink(path)

    def test_extract_includes_logging_levels(self):
        path = self._write_config(SAMPLE_CONFIG)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_config_extract._callable(config_file=path)
            output = captured.getvalue()
            self.assertIn("logging:", output)
            self.assertIn("console: WARNING", output)
            self.assertIn("file: DEBUG", output)
        finally:
            os.unlink(path)

    def test_extract_omits_null_debug_settings(self):
        path = self._write_config(SAMPLE_CONFIG)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_config_extract._callable(config_file=path)
            output = captured.getvalue()
            # debugger and breakpoints are None, so debug section should be omitted
            self.assertNotIn("debug:", output)
        finally:
            os.unlink(path)

    def test_extract_includes_debug_when_set(self):
        config = dict(SAMPLE_CONFIG)
        config["debugger"] = "debugpy"
        config["breakpoints"] = "test-discovery"
        path = self._write_config(config)
        try:
            captured = StringIO()
            with patch("sys.stdout", captured):
                command_agents_config_extract._callable(config_file=path)
            output = captured.getvalue()
            self.assertIn("debug:", output)
            self.assertIn("debugger: debugpy", output)
        finally:
            os.unlink(path)

    def test_extract_file_not_found_exits_nonzero(self):
        with self.assertRaises(SystemExit) as ctx:
            command_agents_config_extract._callable(config_file="/nonexistent/path.json")
        self.assertNotEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
