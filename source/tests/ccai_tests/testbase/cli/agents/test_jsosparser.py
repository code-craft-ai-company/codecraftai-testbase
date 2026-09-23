"""
    Tests for the JSOS Parser utility module.
"""

import os
import tempfile
import unittest

from ccai.testbase.cli.cmdtree.agents.jsosparser import (
    parse_file,
    filter_tests,
    get_final_results,
)


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
    "result": "UNSET",
    "start": "2026-02-24T10:00:01",
    "stop": ""
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


class JSOSParserParseFileTests(unittest.TestCase):
    """Tests for parse_file function."""

    def _write_jsos(self, content):
        fd, path = tempfile.mkstemp(suffix=".jsos")
        with os.fdopen(fd, "w") as fh:
            fh.write(content)
        return path

    def test_parse_file_returns_all_entries(self):
        path = self._write_jsos(SAMPLE_JSOS)
        try:
            entries = parse_file(path)
            self.assertEqual(len(entries), 6)
        finally:
            os.unlink(path)

    def test_parse_file_empty_file(self):
        path = self._write_jsos("")
        try:
            entries = parse_file(path)
            self.assertEqual(len(entries), 0)
        finally:
            os.unlink(path)

    def test_parse_file_invalid_json_raises_value_error(self):
        path = self._write_jsos("{ invalid json }")
        try:
            with self.assertRaises(ValueError):
                parse_file(path)
        finally:
            os.unlink(path)


class JSOSParserFilterTestsTests(unittest.TestCase):
    """Tests for filter_tests function."""

    def test_filter_tests_returns_only_test_entries(self):
        entries = [
            {"rtype": "JOB", "name": "<session>"},
            {"rtype": "TEST_CONTAINER", "name": "pkg"},
            {"rtype": "TEST", "name": "pkg#test_a", "result": "PASSED"},
            {"rtype": "TEST", "name": "pkg#test_b", "result": "FAILED"},
        ]
        result = filter_tests(entries)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(e["rtype"] == "TEST" for e in result))

    def test_filter_tests_empty_list(self):
        result = filter_tests([])
        self.assertEqual(len(result), 0)


class JSOSParserGetFinalResultsTests(unittest.TestCase):
    """Tests for get_final_results function."""

    def test_get_final_results_deduplicates_by_name(self):
        entries = [
            {"rtype": "TEST", "name": "pkg#test_a", "result": "UNSET"},
            {"rtype": "TEST", "name": "pkg#test_a", "result": "PASSED"},
        ]
        results = get_final_results(entries)
        self.assertEqual(len(results), 1)
        self.assertEqual(results["pkg#test_a"]["result"], "PASSED")

    def test_get_final_results_preserves_order(self):
        entries = [
            {"rtype": "TEST", "name": "pkg#test_a", "result": "PASSED"},
            {"rtype": "TEST", "name": "pkg#test_b", "result": "FAILED"},
            {"rtype": "TEST", "name": "pkg#test_c", "result": "SKIPPED"},
        ]
        results = get_final_results(entries)
        names = list(results.keys())
        self.assertEqual(names, ["pkg#test_a", "pkg#test_b", "pkg#test_c"])

    def test_get_final_results_excludes_containers(self):
        entries = [
            {"rtype": "JOB", "name": "<session>"},
            {"rtype": "TEST_CONTAINER", "name": "pkg"},
            {"rtype": "TEST", "name": "pkg#test_a", "result": "PASSED"},
        ]
        results = get_final_results(entries)
        self.assertEqual(len(results), 1)
        self.assertIn("pkg#test_a", results)


if __name__ == "__main__":
    unittest.main()
