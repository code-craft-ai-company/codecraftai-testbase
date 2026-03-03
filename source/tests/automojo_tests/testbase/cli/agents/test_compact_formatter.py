"""
    Tests for the CompactFormatter utility module.
"""

import io
import sys
import unittest

from automojo.testbase.cli.cmdtree.agents.formatting import (
    omit_unset,
    format_kv,
    format_section,
    format_error,
)


class CompactFormatterOmitUnsetTests(unittest.TestCase):
    """Tests for the omit_unset function."""

    def test_omit_unset_returns_none_for_none(self):
        self.assertIsNone(omit_unset(None))

    def test_omit_unset_returns_none_for_not_set(self):
        self.assertIsNone(omit_unset("(not-set)"))

    def test_omit_unset_returns_none_for_unknown(self):
        self.assertIsNone(omit_unset("(unknown)"))

    def test_omit_unset_returns_none_for_empty_string(self):
        self.assertIsNone(omit_unset(""))

    def test_omit_unset_returns_value_for_valid_string(self):
        self.assertEqual(omit_unset("main"), "main")

    def test_omit_unset_returns_value_for_uuid(self):
        val = "8344f668-a0e3-4ef6-89ca-acf007fcb3a0"
        self.assertEqual(omit_unset(val), val)

    def test_omit_unset_returns_string_for_integer(self):
        self.assertEqual(omit_unset(42), "42")


class CompactFormatterFormatKvTests(unittest.TestCase):
    """Tests for the format_kv function."""

    def test_format_kv_basic(self):
        result = format_kv("result", "PASSED")
        self.assertEqual(result, "result: PASSED")

    def test_format_kv_with_indent(self):
        result = format_kv("passed", "3", indent=2)
        self.assertEqual(result, "  passed: 3")

    def test_format_kv_no_indent(self):
        result = format_kv("key", "value", indent=0)
        self.assertEqual(result, "key: value")


class CompactFormatterFormatSectionTests(unittest.TestCase):
    """Tests for the format_section function."""

    def test_format_section_basic(self):
        result = format_section("detail")
        self.assertEqual(result, "detail:")

    def test_format_section_with_indent(self):
        result = format_section("logging", indent=2)
        self.assertEqual(result, "  logging:")


class CompactFormatterFormatErrorTests(unittest.TestCase):
    """Tests for the format_error function."""

    def test_format_error_prints_to_stderr(self):
        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured
        try:
            format_error("File not found: /tmp/test.json")
        finally:
            sys.stderr = old_stderr

        self.assertEqual(captured.getvalue(), "ERROR: File not found: /tmp/test.json\n")


if __name__ == "__main__":
    unittest.main()
