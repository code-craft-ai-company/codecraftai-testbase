"""
    .. module:: automojo.testbase.results.model.checkresult
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for property test check results.

    This module provides the :class:`CheckResult` class which represents
    the outcome of a single generated example within a property test. Each
    property test produces multiple ``CheckResult`` instances (one per example),
    following the same structural pattern used by ``TaskingResult``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, List, Optional

import collections

from dataclasses import asdict as dataclass_as_dict

from automojo.xmodules.xdatetime import format_datetime_with_fractional

from automojo.testbase.results.model.resultcode import ResultCode
from automojo.testbase.results.model.resultnode import ResultNode
from automojo.testbase.results.model.resulttype import ResultType


class CheckResult(ResultNode):
    """
        Represents the outcome of a single generated example within a property test.

        The :class:`CheckResult` is a leaf node in the result tree that records
        the generated input values, the example index, the seed used for
        generation, and the pass/fail/error status for one example invocation.
        Multiple ``CheckResult`` entries are attached to a single parent
        ``TestResult``, following the same collection pattern used for
        ``TaskingResult`` entries in tasking-based tests.

        :param inst_id: The unique identifier for this check result node.
        :param name: The name of this check (e.g., "check_0042").
        :param parent_inst: The unique identifier of the parent test result.
        :param generated_values: Dictionary mapping parameter names to
            their generated values for this example.
        :param example_index: The zero-based index of this example within
            the property test run.
        :param seed: The seed used to generate this specific example.
        :param result_code: The initial result code for this check.
    """

    def __init__(self, inst_id: str, name: str, parent_inst: str,
                 generated_values: Dict[str, Any], example_index: int,
                 seed: int, result_code: ResultCode = ResultCode.UNSET):
        """
            Initializes an instance of a :class:`CheckResult` object.

            :param inst_id: The unique identifier for this check result node.
            :param name: The name of this check (e.g., "check_0042").
            :param parent_inst: The unique identifier of the parent test result.
            :param generated_values: Dictionary mapping parameter names to
                their generated values for this example.
            :param example_index: The zero-based index of this example within
                the property test run.
            :param seed: The seed used to generate this specific example.
            :param result_code: The initial result code for this check.
        """
        super().__init__(inst_id, name, parent_inst, ResultType.CHECK, result_code=result_code)

        self._generated_values = generated_values
        self._example_index = example_index
        self._seed = seed
        return

    @property
    def generated_values(self) -> Dict[str, Any]:
        """
            The dictionary of generated input values for this example.
        """
        return self._generated_values

    @property
    def example_index(self) -> int:
        """
            The zero-based index of this example in the property test run.
        """
        return self._example_index

    @property
    def seed(self) -> int:
        """
            The seed used to generate this specific example.
        """
        return self._seed

    def as_dict(self, is_preview: bool = False) -> collections.OrderedDict:
        """
            Converts the check result instance to an :class:`collections.OrderedDict`.

            The output follows the same structural pattern as
            :meth:`TaskingResult.as_dict`, with property-specific fields
            (``generated_values``, ``example_index``, ``seed``) included.

            :param is_preview: If ``True``, omit the detail section (errors,
                failures, warnings).
            :returns: An ordered dictionary representing the serialized check result.
        """
        start_datetime = format_datetime_with_fractional(self._start)

        stop_datetime = ""
        if self._stop is not None:
            stop_datetime = format_datetime_with_fractional(self._stop)

        # Safely serialize generated values — convert non-serializable types to repr
        safe_values = {}
        for k, v in self._generated_values.items():
            try:
                # Test that the value is JSON-serializable
                import json
                json.dumps(v)
                safe_values[k] = v
            except (TypeError, ValueError):
                safe_values[k] = repr(v)

        rninfo = collections.OrderedDict([
            ("name", self._name),
            ("instance", self._inst_id),
            ("parent", self._parent_inst),
            ("rtype", self._result_type.name),
            ("result", self._result_code.name),
            ("generated_values", safe_values),
            ("example_index", self._example_index),
            ("seed", self._seed),
            ("start", start_datetime),
            ("stop", stop_datetime)
        ])

        if not is_preview:

            errors = [dataclass_as_dict(e) for e in self._errors]
            failures = [dataclass_as_dict(f) for f in self._failures]

            detail_items = [
                ("errors", errors),
                ("failures", failures),
                ("warnings", self._warnings)
            ]

            detail = collections.OrderedDict(detail_items)

            if self._docstr is not None:
                detail["documentation"] = self._docstr

            rninfo["detail"] = detail

        return rninfo

    def format_result(self) -> List[str]:
        """
            Formats the check result into human-readable lines for console output.

            :returns: A list of formatted strings representing this check result.
        """
        fmt_lines = []

        result_str = self._result_code.name
        gen_vals = ", ".join(f"{k}={v!r}" for k, v in self._generated_values.items())

        fmt_lines.append(f"  [{result_str}] {self._name}: {gen_vals}")

        if self._errors:
            for err in self._errors:
                fmt_lines.append(f"    ERROR: {err}")

        if self._failures:
            for fail in self._failures:
                fmt_lines.append(f"    FAILURE: {fail}")

        return fmt_lines
