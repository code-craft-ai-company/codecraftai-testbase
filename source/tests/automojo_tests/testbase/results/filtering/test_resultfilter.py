"""
    .. module:: automojo_tests.testbase.results.filtering.test_resultfilter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for ResultFilter class and filtering functions.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import unittest
from datetime import datetime

from automojo.testbase.results.filtering.resultfilter import (
    ResultFilter,
    ResultFilterCriteria,
    filter_results,
    search_results
)


class ResultFilterCriteriaTests(unittest.TestCase):
    """Tests for the ResultFilterCriteria dataclass."""

    def test_default_criteria_has_none_values(self):
        """Test that default criteria has all None values."""
        criteria = ResultFilterCriteria()
        
        self.assertIsNone(criteria.status_codes)
        self.assertIsNone(criteria.start_time_min)
        self.assertIsNone(criteria.start_time_max)
        self.assertIsNone(criteria.stop_time_min)
        self.assertIsNone(criteria.stop_time_max)
        self.assertIsNone(criteria.name_pattern)
        self.assertIsNone(criteria.metadata_filters)
        self.assertIsNone(criteria.result_types)

    def test_criteria_with_status_codes(self):
        """Test criteria with status codes."""
        criteria = ResultFilterCriteria(status_codes=["PASSED", "FAILED"])
        
        self.assertEqual(criteria.status_codes, ["PASSED", "FAILED"])

    def test_criteria_with_time_range(self):
        """Test criteria with time range."""
        min_time = datetime(2025, 1, 1)
        max_time = datetime(2025, 12, 31)
        
        criteria = ResultFilterCriteria(
            start_time_min=min_time,
            start_time_max=max_time
        )
        
        self.assertEqual(criteria.start_time_min, min_time)
        self.assertEqual(criteria.start_time_max, max_time)


class ResultFilterStatusFilterTests(unittest.TestCase):
    """Tests for filtering by status codes."""

    def setUp(self):
        """Set up test results."""
        self.results = [
            {"name": "test_passed", "result": "PASSED", "rtype": "TEST"},
            {"name": "test_failed", "result": "FAILED", "rtype": "TEST"},
            {"name": "test_errored", "result": "ERRORED", "rtype": "TEST"},
            {"name": "test_skipped", "result": "SKIPPED", "rtype": "TEST"},
        ]

    def test_filter_by_single_status(self):
        """Test filtering by a single status code."""
        criteria = ResultFilterCriteria(status_codes=["PASSED"])
        result_filter = ResultFilter(criteria)
        
        filtered = result_filter.filter(self.results)
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["name"], "test_passed")

    def test_filter_by_multiple_statuses(self):
        """Test filtering by multiple status codes."""
        criteria = ResultFilterCriteria(status_codes=["FAILED", "ERRORED"])
        result_filter = ResultFilter(criteria)
        
        filtered = result_filter.filter(self.results)
        
        self.assertEqual(len(filtered), 2)
        names = [r["name"] for r in filtered]
        self.assertIn("test_failed", names)
        self.assertIn("test_errored", names)

    def test_filter_no_status_returns_all(self):
        """Test that no status filter returns all results."""
        criteria = ResultFilterCriteria()
        result_filter = ResultFilter(criteria)
        
        filtered = result_filter.filter(self.results)
        
        self.assertEqual(len(filtered), 4)


class ResultFilterTimeRangeTests(unittest.TestCase):
    """Tests for filtering by time range."""

    def setUp(self):
        """Set up test results with timestamps."""
        self.results = [
            {
                "name": "test_early",
                "result": "PASSED",
                "rtype": "TEST",
                "start": "2025-01-15T10:00:00",
                "stop": "2025-01-15T10:05:00"
            },
            {
                "name": "test_mid",
                "result": "PASSED",
                "rtype": "TEST",
                "start": "2025-02-15T10:00:00",
                "stop": "2025-02-15T10:05:00"
            },
            {
                "name": "test_late",
                "result": "PASSED",
                "rtype": "TEST",
                "start": "2025-03-15T10:00:00",
                "stop": "2025-03-15T10:05:00"
            },
        ]

    def test_filter_by_start_time_min(self):
        """Test filtering by minimum start time."""
        criteria = ResultFilterCriteria(
            start_time_min=datetime(2025, 2, 1)
        )
        result_filter = ResultFilter(criteria)
        
        filtered = result_filter.filter(self.results)
        
        self.assertEqual(len(filtered), 2)
        names = [r["name"] for r in filtered]
        self.assertIn("test_mid", names)
        self.assertIn("test_late", names)

    def test_filter_by_start_time_max(self):
        """Test filtering by maximum start time."""
        criteria = ResultFilterCriteria(
            start_time_max=datetime(2025, 2, 1)
        )
        result_filter = ResultFilter(criteria)
        
        filtered = result_filter.filter(self.results)
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["name"], "test_early")

    def test_filter_by_time_range(self):
        """Test filtering by both min and max start time."""
        criteria = ResultFilterCriteria(
            start_time_min=datetime(2025, 2, 1),
            start_time_max=datetime(2025, 3, 1)
        )
        result_filter = ResultFilter(criteria)
        
        filtered = result_filter.filter(self.results)
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["name"], "test_mid")


class ResultFilterNamePatternTests(unittest.TestCase):
    """Tests for filtering by name pattern."""

    def setUp(self):
        """Set up test results."""
        self.results = [
            {"name": "test_integration_login", "result": "PASSED", "rtype": "TEST"},
            {"name": "test_integration_logout", "result": "PASSED", "rtype": "TEST"},
            {"name": "test_unit_helper", "result": "PASSED", "rtype": "TEST"},
            {"name": "test_e2e_workflow", "result": "PASSED", "rtype": "TEST"},
        ]

    def test_filter_by_name_pattern(self):
        """Test filtering by name pattern."""
        criteria = ResultFilterCriteria(name_pattern="integration")
        result_filter = ResultFilter(criteria)
        
        filtered = result_filter.filter(self.results)
        
        self.assertEqual(len(filtered), 2)
        for r in filtered:
            self.assertIn("integration", r["name"])

    def test_filter_by_regex_pattern(self):
        """Test filtering by regex pattern."""
        criteria = ResultFilterCriteria(name_pattern="test_(integration|e2e)_.*")
        result_filter = ResultFilter(criteria)
        
        filtered = result_filter.filter(self.results)
        
        self.assertEqual(len(filtered), 3)


class ResultFilterResultTypeTests(unittest.TestCase):
    """Tests for filtering by result type."""

    def setUp(self):
        """Set up test results with different types."""
        self.results = [
            {"name": "test_1", "result": "PASSED", "rtype": "TEST"},
            {"name": "tasking_1", "result": "PASSED", "rtype": "TASKING"},
            {"name": "container_1", "result": "PASSED", "rtype": "TEST_CONTAINER"},
            {"name": "test_2", "result": "FAILED", "rtype": "TEST"},
        ]

    def test_filter_by_single_type(self):
        """Test filtering by a single result type."""
        criteria = ResultFilterCriteria(result_types=["TEST"])
        result_filter = ResultFilter(criteria)
        
        filtered = result_filter.filter(self.results)
        
        self.assertEqual(len(filtered), 2)
        for r in filtered:
            self.assertEqual(r["rtype"], "TEST")

    def test_filter_by_multiple_types(self):
        """Test filtering by multiple result types."""
        criteria = ResultFilterCriteria(result_types=["TEST", "TASKING"])
        result_filter = ResultFilter(criteria)
        
        filtered = result_filter.filter(self.results)
        
        self.assertEqual(len(filtered), 3)


class ResultFilterMetadataTests(unittest.TestCase):
    """Tests for filtering by metadata."""

    def setUp(self):
        """Set up test results with metadata."""
        self.results = [
            {
                "name": "test_1",
                "result": "PASSED",
                "rtype": "TEST",
                "monikers": ["smoke", "critical"],
                "pivots": {"browser": "chrome", "os": "linux"}
            },
            {
                "name": "test_2",
                "result": "FAILED",
                "rtype": "TEST",
                "monikers": ["regression"],
                "pivots": {"browser": "firefox", "os": "windows"}
            },
            {
                "name": "test_3",
                "result": "PASSED",
                "rtype": "TEST",
                "monikers": ["smoke"],
                "pivots": {"browser": "chrome", "os": "macos"}
            },
        ]

    def test_filter_by_moniker(self):
        """Test filtering by moniker."""
        criteria = ResultFilterCriteria(metadata_filters={"moniker": "smoke"})
        result_filter = ResultFilter(criteria)
        
        filtered = result_filter.filter(self.results)
        
        self.assertEqual(len(filtered), 2)

    def test_filter_by_pivot(self):
        """Test filtering by pivot value."""
        criteria = ResultFilterCriteria(metadata_filters={"browser": "chrome"})
        result_filter = ResultFilter(criteria)
        
        filtered = result_filter.filter(self.results)
        
        self.assertEqual(len(filtered), 2)


class ResultFilterSearchTests(unittest.TestCase):
    """Tests for full-text search functionality."""

    def setUp(self):
        """Set up test results with detail sections."""
        self.results = [
            {
                "name": "test_connection",
                "result": "FAILED",
                "rtype": "TEST",
                "detail": {
                    "errors": [],
                    "failures": [
                        {
                            "extype": "AssertionError",
                            "exargs": ["Connection refused to server"],
                            "traces": []
                        }
                    ],
                    "warnings": []
                }
            },
            {
                "name": "test_timeout",
                "result": "ERRORED",
                "rtype": "TEST",
                "detail": {
                    "errors": [
                        {
                            "extype": "TimeoutError",
                            "exargs": ["Request timed out after 30 seconds"],
                            "traces": []
                        }
                    ],
                    "failures": [],
                    "warnings": []
                }
            },
            {
                "name": "test_success",
                "result": "PASSED",
                "rtype": "TEST",
                "detail": {
                    "errors": [],
                    "failures": [],
                    "warnings": [["Deprecation warning: use new_method instead"]]
                }
            },
        ]

    def test_search_in_name(self):
        """Test searching in result name."""
        result_filter = ResultFilter()
        
        found = result_filter.search(self.results, "connection")
        
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["name"], "test_connection")

    def test_search_in_error_message(self):
        """Test searching in error messages."""
        result_filter = ResultFilter()
        
        found = result_filter.search(self.results, "timed out")
        
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["name"], "test_timeout")

    def test_search_in_failure_message(self):
        """Test searching in failure messages."""
        result_filter = ResultFilter()
        
        found = result_filter.search(self.results, "refused")
        
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["name"], "test_connection")

    def test_search_in_warnings(self):
        """Test searching in warning messages."""
        result_filter = ResultFilter()
        
        found = result_filter.search(self.results, "deprecation")
        
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["name"], "test_success")

    def test_search_case_insensitive(self):
        """Test case-insensitive search."""
        result_filter = ResultFilter()
        
        found = result_filter.search(self.results, "TIMEOUT")
        
        self.assertEqual(len(found), 1)

    def test_search_case_sensitive(self):
        """Test case-sensitive search."""
        result_filter = ResultFilter()
        
        found = result_filter.search(self.results, "TIMEOUT", case_sensitive=True)
        
        self.assertEqual(len(found), 0)


class ResultFilterCombinedTests(unittest.TestCase):
    """Tests for combined filtering and searching."""

    def setUp(self):
        """Set up test results."""
        self.results = [
            {
                "name": "test_api_connection",
                "result": "FAILED",
                "rtype": "TEST",
                "start": "2025-02-15T10:00:00",
                "detail": {
                    "errors": [],
                    "failures": [{"extype": "AssertionError", "exargs": ["API error"], "traces": []}],
                    "warnings": []
                }
            },
            {
                "name": "test_api_timeout",
                "result": "ERRORED",
                "rtype": "TEST",
                "start": "2025-02-15T11:00:00",
                "detail": {
                    "errors": [{"extype": "TimeoutError", "exargs": ["API timeout"], "traces": []}],
                    "failures": [],
                    "warnings": []
                }
            },
            {
                "name": "test_db_connection",
                "result": "FAILED",
                "rtype": "TEST",
                "start": "2025-01-15T10:00:00",
                "detail": {
                    "errors": [],
                    "failures": [{"extype": "AssertionError", "exargs": ["DB error"], "traces": []}],
                    "warnings": []
                }
            },
        ]

    def test_filter_and_search(self):
        """Test combined filter and search."""
        criteria = ResultFilterCriteria(
            status_codes=["FAILED"],
            start_time_min=datetime(2025, 2, 1)
        )
        result_filter = ResultFilter(criteria)
        
        found = result_filter.filter_and_search(self.results, "API")
        
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["name"], "test_api_connection")


class FilterResultsFunctionTests(unittest.TestCase):
    """Tests for the filter_results convenience function."""

    def test_filter_results_by_status(self):
        """Test filter_results function with status codes."""
        results = [
            {"name": "test_1", "result": "PASSED", "rtype": "TEST"},
            {"name": "test_2", "result": "FAILED", "rtype": "TEST"},
        ]
        
        filtered = filter_results(results, status_codes=["PASSED"])
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["name"], "test_1")


class SearchResultsFunctionTests(unittest.TestCase):
    """Tests for the search_results convenience function."""

    def test_search_results_function(self):
        """Test search_results function."""
        results = [
            {
                "name": "test_connection",
                "result": "FAILED",
                "rtype": "TEST",
                "detail": {
                    "errors": [],
                    "failures": [{"extype": "Error", "exargs": ["Connection failed"], "traces": []}],
                    "warnings": []
                }
            },
            {
                "name": "test_other",
                "result": "PASSED",
                "rtype": "TEST",
                "detail": {"errors": [], "failures": [], "warnings": []}
            },
        ]
        
        found = search_results(results, "connection")
        
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["name"], "test_connection")


if __name__ == "__main__":
    unittest.main()
