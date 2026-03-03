"""
    .. module:: automojo.testbase.cli.cmdtree.agents.testresult.extract
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Agent command for extracting a single test result by name.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import sys

from typing import Optional

from automojo.arcli import decorators as arcli

from automojo.testbase.cli.cmdtree.agents.formatting import (
    format_kv,
    format_section,
    format_error,
)
from automojo.testbase.cli.cmdtree.agents.jsosparser import parse_file, get_final_results
from automojo.testbase.cli.cmdtree.agents.pathresolver import resolve_file_path


HELP_RESULTS_FILE = "Path to a testrun_results_stream.jsos file."
HELP_TESTNAME = "Fully qualified test name to extract (e.g., package.module#test_name)."


@arcli.option("--testname", required=True, help=HELP_TESTNAME)
@arcli.option("--results-file", required=True, help=HELP_RESULTS_FILE)
@arcli.command("extract")
def command_agents_testresult_extract(results_file: str, testname: str):
    """
    Extracts detailed result information for a specific test from the results stream.
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

    if testname not in final_results:
        format_error(f"Test '{testname}' not found in results file")
        sys.exit(1)

    entry = final_results[testname]

    lines = []
    lines.append(format_kv("name", entry.get("name", "")))
    lines.append(format_kv("result", entry.get("result", "UNKNOWN")))
    lines.append(format_kv("start", entry.get("start", "")))
    lines.append(format_kv("stop", entry.get("stop", "")))

    # Extract error details if present
    detail = entry.get("detail")
    if detail is not None:
        errors = detail.get("errors", [])
        if errors:
            lines.append(format_section("errors"))
            for error_item in errors:
                if isinstance(error_item, dict):
                    msg = error_item.get("message", str(error_item))
                    lines.append(format_kv("-", msg, indent=2))
                elif isinstance(error_item, str):
                    lines.append(format_kv("-", error_item, indent=2))

    print("\n".join(lines))
