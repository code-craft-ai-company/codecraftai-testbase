"""
    .. module:: ccai.testbase.cli.cmdtree.agents.summary.compare
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Agent command for comparing two test summaries.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import json
import sys

from ccai.arcli import decorators as arcli

from ccai.testbase.cli.cmdtree.agents.formatting import (
    format_kv,
    format_section,
    format_error,
)
from ccai.testbase.cli.cmdtree.agents.pathresolver import resolve_file_path


HELP_BASELINE = "Path to the baseline testrun_summary.json file."
HELP_CURRENT = "Path to the current testrun_summary.json file."


def _load_summary(filepath: str) -> dict:
    """
        Resolves, reads, and parses a summary JSON file.

        :param filepath: The file path to load.
        :returns: The parsed JSON data.
    """
    resolved = resolve_file_path(filepath)

    with open(resolved, "r") as fh:
        return json.load(fh)


def _format_delta(value: int) -> str:
    """
        Formats a delta integer with a sign prefix.

        :param value: The delta value.
        :returns: A string like '+2', '-1', or '0'.
    """
    if value > 0:
        return f"+{value}"
    return str(value)


@arcli.option("--current", required=True, help=HELP_CURRENT)
@arcli.option("--baseline", required=True, help=HELP_BASELINE)
@arcli.command("compare")
def command_agents_summary_compare(baseline: str, current: str):
    """
    Compares two test summary files and reports regressions or improvements.
    """

    try:
        baseline_data = _load_summary(baseline)
    except FileNotFoundError as err:
        format_error(str(err))
        sys.exit(1)
    except json.JSONDecodeError:
        format_error(f"Invalid JSON in baseline file")
        sys.exit(1)

    try:
        current_data = _load_summary(current)
    except FileNotFoundError as err:
        format_error(str(err))
        sys.exit(1)
    except json.JSONDecodeError:
        format_error(f"Invalid JSON in current file")
        sys.exit(1)

    lines = []

    # Overall result comparison
    baseline_result = baseline_data.get("result", "UNKNOWN")
    current_result = current_data.get("result", "UNKNOWN")

    if baseline_result == current_result:
        lines.append(format_kv("overall", f"{current_result} (stable)"))
    else:
        # Determine regression or improvement
        classification = _classify_change(baseline_data, current_data)
        lines.append(format_kv("overall", f"{baseline_result}->{current_result} ({classification})"))

    # Detail counter deltas
    baseline_detail = baseline_data.get("detail") or {}
    current_detail = current_data.get("detail") or {}

    counter_fields = ("passed", "failed", "errors", "skipped", "total")
    lines.append(format_section("delta"))
    for field in counter_fields:
        bval = baseline_detail.get(field, 0)
        cval = current_detail.get(field, 0)
        delta = cval - bval
        lines.append(format_kv(field, _format_delta(delta), indent=2))

    print("\n".join(lines))


def _classify_change(baseline_data: dict, current_data: dict) -> str:
    """
        Classifies the change between two runs as regression, improvement, or stable.

        :param baseline_data: The baseline summary data.
        :param current_data: The current summary data.
        :returns: 'regression', 'improvement', or 'stable'.
    """
    baseline_detail = baseline_data.get("detail") or {}
    current_detail = current_data.get("detail") or {}

    baseline_failures = baseline_detail.get("failed", 0) + baseline_detail.get("errors", 0)
    current_failures = current_detail.get("failed", 0) + current_detail.get("errors", 0)

    if current_failures > baseline_failures:
        return "regression"
    elif current_failures < baseline_failures:
        return "improvement"

    return "stable"
