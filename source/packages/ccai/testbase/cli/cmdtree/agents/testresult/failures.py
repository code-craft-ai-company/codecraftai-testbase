"""
    .. module:: ccai.testbase.cli.cmdtree.agents.testresult.failures
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Agent command for listing failed and errored tests.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import sys

from typing import Optional

from ccai.arcli import decorators as arcli

from ccai.testbase.cli.cmdtree.agents.formatting import (
    format_kv,
    format_error,
)
from ccai.testbase.cli.cmdtree.agents.jsosparser import parse_file, get_final_results
from ccai.testbase.cli.cmdtree.agents.pathresolver import resolve_file_path


HELP_RESULTS_FILE = "Path to a testrun_results_stream.jsos file."

FAILURE_RESULTS = {"FAILED", "ERRORED"}


@arcli.option("--results-file", required=True, help=HELP_RESULTS_FILE)
@arcli.command("failures")
def command_agents_testresult_failures(results_file: str):
    """
    Lists all failed and errored tests with error summaries from the results stream.
    """

    try:
        resolved = resolve_file_path(results_file)
    except FileNotFoundError as err:
        format_error(str(err))
        sys.exit(1)

    try:
        entries = parse_file(resolved)
    except ValueError as err:
        format_error(str(err))
        sys.exit(1)

    final_results = get_final_results(entries)

    lines = []
    for name, entry in final_results.items():
        result = entry.get("result", "UNKNOWN")
        if result not in FAILURE_RESULTS:
            continue

        lines.append(f"{name}: {result}")

        # Include brief error summary if available
        detail = entry.get("detail")
        if detail is not None:
            errors = detail.get("errors", [])
            for error_item in errors:
                if isinstance(error_item, dict):
                    msg = error_item.get("message", str(error_item))
                    lines.append(format_kv("error", msg, indent=2))
                elif isinstance(error_item, str):
                    lines.append(format_kv("error", error_item, indent=2))

    if lines:
        print("\n".join(lines))
    else:
        print("All tests passed")
