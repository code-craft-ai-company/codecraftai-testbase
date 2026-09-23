"""
    .. module:: ccai.testbase.results.filtering.resultfilter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for result filtering and search functionality.

    This module provides functionality to filter and search test results based on
    various criteria including status, time range, metadata, and full-text search
    in result details.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class ResultFilterCriteria:
    """
        Dataclass representing filter criteria for result filtering.

        This class encapsulates all possible filter criteria that can be applied
        to test results. Multiple criteria can be combined for complex filtering.

        Attributes:
            status_codes: List of result status codes to include (e.g., ["PASSED", "FAILED"])
            start_time_min: Minimum start time for results (inclusive)
            start_time_max: Maximum start time for results (inclusive)
            stop_time_min: Minimum stop time for results (inclusive)
            stop_time_max: Maximum stop time for results (inclusive)
            name_pattern: Regex pattern to match against result names
            metadata_filters: Dictionary of metadata key-value pairs to match
            result_types: List of result types to include (e.g., ["TEST", "TASKING"])

        Example::

            # Filter for failed tests in a specific time range
            criteria = ResultFilterCriteria(
                status_codes=["FAILED", "ERRORED"],
                start_time_min=datetime(2025, 1, 1),
                start_time_max=datetime(2025, 1, 31)
            )
    """
    status_codes: Optional[List[str]] = None
    start_time_min: Optional[datetime] = None
    start_time_max: Optional[datetime] = None
    stop_time_min: Optional[datetime] = None
    stop_time_max: Optional[datetime] = None
    name_pattern: Optional[str] = None
    metadata_filters: Optional[Dict[str, Any]] = None
    result_types: Optional[List[str]] = None


class ResultFilter:
    """
        Class for filtering test results based on various criteria.

        The ResultFilter provides methods to filter a list of result dictionaries
        based on status codes, time ranges, name patterns, metadata, and result types.
        It also supports full-text search within result details.

        FILTERING ALGORITHM:
        ====================
        The filter applies criteria in the following order:
        1. Result type filter (if specified)
        2. Status code filter (if specified)
        3. Time range filters (start_time_min/max, stop_time_min/max)
        4. Name pattern filter (regex matching)
        5. Metadata filters (key-value matching)

        All criteria are combined with AND logic - a result must match ALL
        specified criteria to be included in the output.

        Thread Safety:
            The ResultFilter is stateless and thread-safe. Multiple threads can
            use the same filter instance concurrently without synchronization.

        Usage Example::

            from ccai.testbase.results.filtering import ResultFilter, ResultFilterCriteria

            # Create filter with criteria
            criteria = ResultFilterCriteria(
                status_codes=["FAILED"],
                name_pattern="test_.*integration.*"
            )
            result_filter = ResultFilter(criteria)

            # Apply filter to results
            filtered = result_filter.filter(results)

            # Or use full-text search
            search_results = result_filter.search(results, "connection timeout")
    """

    def __init__(self, criteria: Optional[ResultFilterCriteria] = None):
        """
            Initializes a ResultFilter with optional filter criteria.

            :param criteria: Optional ResultFilterCriteria instance containing
                             filter parameters. If None, no filtering is applied.
        """
        self._criteria = criteria if criteria is not None else ResultFilterCriteria()
        return

    @property
    def criteria(self) -> ResultFilterCriteria:
        """
            Returns the current filter criteria.

            :returns: The ResultFilterCriteria instance used by this filter.
        """
        return self._criteria

    def filter(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
            Filters a list of result dictionaries based on the configured criteria.

            This method applies all configured filter criteria to the input results
            and returns only those results that match ALL criteria (AND logic).

            :param results: List of result dictionaries to filter. Each dictionary
                            should contain keys like 'name', 'result', 'rtype',
                            'start', 'stop', and optionally 'detail'.

            :returns: List of result dictionaries that match all filter criteria.
        """
        filtered_results = []

        for result in results:
            if self._matches_criteria(result):
                filtered_results.append(result)

        return filtered_results

    def search(self, results: List[Dict[str, Any]], search_text: str,
               case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
            Performs full-text search within result details.

            This method searches for the specified text within result names,
            error messages, failure messages, and warning messages. Results
            that contain the search text in any of these fields are returned.

            :param results: List of result dictionaries to search.
            :param search_text: Text to search for within result details.
            :param case_sensitive: If True, search is case-sensitive. Default is False.

            :returns: List of result dictionaries containing the search text.
        """
        matching_results = []

        for result in results:
            if self._contains_search_text(result, search_text, case_sensitive):
                matching_results.append(result)

        return matching_results

    def filter_and_search(self, results: List[Dict[str, Any]], search_text: Optional[str] = None,
                          case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
            Combines filtering and searching in a single operation.

            This method first applies filter criteria, then performs full-text
            search on the filtered results (if search_text is provided).

            :param results: List of result dictionaries to process.
            :param search_text: Optional text to search for after filtering.
            :param case_sensitive: If True, search is case-sensitive. Default is False.

            :returns: List of result dictionaries matching both filter and search criteria.
        """
        filtered = self.filter(results)

        if search_text:
            filtered = self.search(filtered, search_text, case_sensitive)

        return filtered

    def _matches_criteria(self, result: Dict[str, Any]) -> bool:
        """
            Checks if a single result matches all configured filter criteria.

            :param result: Result dictionary to check.

            :returns: True if the result matches all criteria, False otherwise.
        """
        # Check result type filter
        if self._criteria.result_types is not None:
            result_type = result.get("rtype", "")
            if result_type not in self._criteria.result_types:
                return False

        # Check status code filter
        if self._criteria.status_codes is not None:
            result_code = result.get("result", "")
            if result_code not in self._criteria.status_codes:
                return False

        # Check start time range
        if not self._matches_time_range(result, "start",
                                        self._criteria.start_time_min,
                                        self._criteria.start_time_max):
            return False

        # Check stop time range
        if not self._matches_time_range(result, "stop",
                                        self._criteria.stop_time_min,
                                        self._criteria.stop_time_max):
            return False

        # Check name pattern
        if self._criteria.name_pattern is not None:
            name = result.get("name", "")
            if not re.search(self._criteria.name_pattern, name):
                return False

        # Check metadata filters
        if self._criteria.metadata_filters is not None:
            if not self._matches_metadata(result):
                return False

        return True

    def _matches_time_range(self, result: Dict[str, Any], time_field: str,
                            min_time: Optional[datetime],
                            max_time: Optional[datetime]) -> bool:
        """
            Checks if a result's timestamp falls within the specified range.

            :param result: Result dictionary containing the timestamp.
            :param time_field: Name of the timestamp field ('start' or 'stop').
            :param min_time: Minimum time (inclusive), or None for no minimum.
            :param max_time: Maximum time (inclusive), or None for no maximum.

            :returns: True if the timestamp is within range, False otherwise.
        """
        if min_time is None and max_time is None:
            return True

        time_value = result.get(time_field, "")
        if not time_value:
            # If no time value and we have a filter, exclude the result
            return min_time is None and max_time is None

        # Parse the timestamp if it's a string
        if isinstance(time_value, str):
            try:
                time_value = datetime.fromisoformat(time_value)
            except ValueError:
                return False
        elif not isinstance(time_value, datetime):
            return False

        # Check minimum time
        if min_time is not None and time_value < min_time:
            return False

        # Check maximum time
        if max_time is not None and time_value > max_time:
            return False

        return True

    def _matches_metadata(self, result: Dict[str, Any]) -> bool:
        """
            Checks if a result matches all metadata filter criteria.

            Metadata filters can match against top-level result fields,
            nested detail fields, monikers, and pivots.

            :param result: Result dictionary to check.

            :returns: True if all metadata filters match, False otherwise.
        """
        if self._criteria.metadata_filters is None:
            return True

        for key, expected_value in self._criteria.metadata_filters.items():
            # Check top-level fields
            if key in result:
                if not self._value_matches(result[key], expected_value):
                    return False
                continue

            # Check in detail section
            detail = result.get("detail", {})
            if key in detail:
                if not self._value_matches(detail[key], expected_value):
                    return False
                continue

            # Check in monikers (list membership)
            if key == "moniker":
                monikers = result.get("monikers", [])
                if expected_value not in monikers:
                    return False
                continue

            # Check in pivots
            pivots = result.get("pivots", {})
            if key in pivots:
                if not self._value_matches(pivots[key], expected_value):
                    return False
                continue

            # Key not found in any location - filter fails
            return False

        return True

    def _value_matches(self, actual: Any, expected: Any) -> bool:
        """
            Checks if an actual value matches an expected value.

            Supports exact matching, regex matching for strings, and
            list membership checking.

            :param actual: The actual value from the result.
            :param expected: The expected value from the filter.

            :returns: True if values match, False otherwise.
        """
        # Handle regex patterns for string values
        if isinstance(expected, str) and isinstance(actual, str):
            # Try regex match first
            try:
                if re.search(expected, actual):
                    return True
            except re.error:
                # The expected value is not a valid regex; treat it as a literal and
                # fall through to the exact-match comparison below.
                pass
            # Fall back to exact match
            return actual == expected

        # Handle list membership
        if isinstance(actual, list):
            return expected in actual

        # Exact match for other types
        return actual == expected

    def _contains_search_text(self, result: Dict[str, Any], search_text: str,
                              case_sensitive: bool) -> bool:
        """
            Checks if a result contains the search text in any searchable field.

            Searchable fields include:
            - name: Result name
            - detail.errors: Error messages and tracebacks
            - detail.failures: Failure messages and tracebacks
            - detail.warnings: Warning messages
            - detail.documentation: Documentation string

            :param result: Result dictionary to search.
            :param search_text: Text to search for.
            :param case_sensitive: If True, search is case-sensitive.

            :returns: True if search text is found, False otherwise.
        """
        if not case_sensitive:
            search_text = search_text.lower()

        # Search in name
        name = result.get("name", "")
        if self._text_in_string(name, search_text, case_sensitive):
            return True

        # Search in detail section
        detail = result.get("detail", {})

        # Search in errors
        errors = detail.get("errors", [])
        if self._search_in_traceback_list(errors, search_text, case_sensitive):
            return True

        # Search in failures
        failures = detail.get("failures", [])
        if self._search_in_traceback_list(failures, search_text, case_sensitive):
            return True

        # Search in warnings
        warnings = detail.get("warnings", [])
        if self._search_in_nested_list(warnings, search_text, case_sensitive):
            return True

        # Search in documentation
        documentation = detail.get("documentation", "")
        if documentation and self._text_in_string(documentation, search_text, case_sensitive):
            return True

        return False

    def _text_in_string(self, text: str, search_text: str, case_sensitive: bool) -> bool:
        """
            Checks if search text is contained in a string.

            :param text: String to search in.
            :param search_text: Text to search for.
            :param case_sensitive: If True, search is case-sensitive.

            :returns: True if search text is found, False otherwise.
        """
        if not case_sensitive:
            text = text.lower()
        return search_text in text

    def _search_in_traceback_list(self, traceback_list: List[Any], search_text: str,
                                   case_sensitive: bool) -> bool:
        """
            Searches for text within a list of traceback details.

            Traceback details can be dictionaries with 'extype', 'exargs', and 'traces'
            fields, or simple strings.

            :param traceback_list: List of traceback details to search.
            :param search_text: Text to search for.
            :param case_sensitive: If True, search is case-sensitive.

            :returns: True if search text is found, False otherwise.
        """
        for tb in traceback_list:
            if isinstance(tb, dict):
                # Search in exception type
                extype = tb.get("extype", "")
                if self._text_in_string(str(extype), search_text, case_sensitive):
                    return True

                # Search in exception arguments
                exargs = tb.get("exargs", [])
                for arg in exargs:
                    if self._text_in_string(str(arg), search_text, case_sensitive):
                        return True

                # Search in traces
                traces = tb.get("traces", [])
                for trace in traces:
                    if isinstance(trace, dict):
                        # Search in call
                        call = trace.get("call", "")
                        if self._text_in_string(str(call), search_text, case_sensitive):
                            return True

                        # Search in code lines
                        code = trace.get("code", [])
                        for line in code:
                            if self._text_in_string(str(line), search_text, case_sensitive):
                                return True

                        # Search in origin
                        origin = trace.get("origin", {})
                        if isinstance(origin, dict):
                            for value in origin.values():
                                if self._text_in_string(str(value), search_text, case_sensitive):
                                    return True
            elif isinstance(tb, str):
                if self._text_in_string(tb, search_text, case_sensitive):
                    return True

        return False

    def _search_in_nested_list(self, nested_list: List[Any], search_text: str,
                                case_sensitive: bool) -> bool:
        """
            Searches for text within a nested list structure.

            :param nested_list: Nested list to search.
            :param search_text: Text to search for.
            :param case_sensitive: If True, search is case-sensitive.

            :returns: True if search text is found, False otherwise.
        """
        for item in nested_list:
            if isinstance(item, list):
                if self._search_in_nested_list(item, search_text, case_sensitive):
                    return True
            elif isinstance(item, str):
                if self._text_in_string(item, search_text, case_sensitive):
                    return True

        return False


def filter_results(results: List[Dict[str, Any]],
                   status_codes: Optional[List[str]] = None,
                   start_time_min: Optional[datetime] = None,
                   start_time_max: Optional[datetime] = None,
                   stop_time_min: Optional[datetime] = None,
                   stop_time_max: Optional[datetime] = None,
                   name_pattern: Optional[str] = None,
                   metadata_filters: Optional[Dict[str, Any]] = None,
                   result_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
        Convenience function to filter results with specified criteria.

        This function creates a ResultFilter with the specified criteria and
        applies it to the input results. It provides a simpler interface for
        one-off filtering operations.

        :param results: List of result dictionaries to filter.
        :param status_codes: List of result status codes to include.
        :param start_time_min: Minimum start time for results.
        :param start_time_max: Maximum start time for results.
        :param stop_time_min: Minimum stop time for results.
        :param stop_time_max: Maximum stop time for results.
        :param name_pattern: Regex pattern to match against result names.
        :param metadata_filters: Dictionary of metadata key-value pairs to match.
        :param result_types: List of result types to include.

        :returns: List of result dictionaries matching all criteria.

        Example::

            # Filter for failed tests
            failed_tests = filter_results(results, status_codes=["FAILED"])

            # Filter for tests in a time range
            recent_tests = filter_results(
                results,
                start_time_min=datetime(2025, 2, 1),
                start_time_max=datetime(2025, 2, 28)
            )
    """
    criteria = ResultFilterCriteria(
        status_codes=status_codes,
        start_time_min=start_time_min,
        start_time_max=start_time_max,
        stop_time_min=stop_time_min,
        stop_time_max=stop_time_max,
        name_pattern=name_pattern,
        metadata_filters=metadata_filters,
        result_types=result_types
    )

    result_filter = ResultFilter(criteria)
    return result_filter.filter(results)


def search_results(results: List[Dict[str, Any]], search_text: str,
                   case_sensitive: bool = False) -> List[Dict[str, Any]]:
    """
        Convenience function to search for text within results.

        This function performs full-text search within result names, error messages,
        failure messages, and warning messages.

        :param results: List of result dictionaries to search.
        :param search_text: Text to search for within result details.
        :param case_sensitive: If True, search is case-sensitive. Default is False.

        :returns: List of result dictionaries containing the search text.

        Example::

            # Search for connection errors
            connection_errors = search_results(results, "connection refused")

            # Case-sensitive search
            specific_errors = search_results(results, "ValueError", case_sensitive=True)
    """
    result_filter = ResultFilter()
    return result_filter.search(results, search_text, case_sensitive)
