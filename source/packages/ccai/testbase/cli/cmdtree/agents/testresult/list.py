"""
    .. module:: ccai.testbase.cli.cmdtree.agents.testresult.list
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Agent command for listing all test results.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import sys

from typing import Optional

from ccai.arcli import decorators as arcli

from ccai.testbase.cli.cmdtree.agents.formatting import format_error
from ccai.testbase.cli.cmdtree.agents.jsosparser import parse_file, get_final_results
from ccai.testbase.cli.cmdtree.agents.pathresolver import resolve_file_path


HELP_RESULTS_FILE = "Path to a testrun_results_stream.jsos file."
HELP_RESULT_FILTER = "Filter results by result code (e.g., PASSED, FAILED, SKIPPED)."


@arcli.option("--result-filter", default=None, required=False, help=HELP_RESULT_FILTER)
@arcli.option("--results-file", required=True, help=HELP_RESULTS_FILE)
@arcli.command("list")
def command_agents_testresult_list(results_file: str, result_filter: Optional[str] = None):
    """
    Lists all tests and their final results from the results stream.
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
        if result_filter is not None and result != result_filter:
            continue
        lines.append(f"{name}: {result}")

    if lines:
        print("\n".join(lines))
    else:
        if result_filter is not None:
            print(f"No tests with result '{result_filter}' found")
        else:
            print("No test results found")
