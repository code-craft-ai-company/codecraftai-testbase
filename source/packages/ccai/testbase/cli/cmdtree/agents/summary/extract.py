"""
    .. module:: ccai.testbase.cli.cmdtree.agents.summary.extract
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Agent command for extracting compact test summary information.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import json
import sys

from typing import Optional

from ccai.arcli import decorators as arcli

from ccai.testbase.cli.cmdtree.agents.formatting import (
    format_kv,
    format_section,
    format_error,
    omit_unset
)
from ccai.testbase.cli.cmdtree.agents.pathresolver import resolve_file_path


HELP_SUMMARY_FILE = "Path to a testrun_summary.json file."


@arcli.option("--summary-file", required=True, help=HELP_SUMMARY_FILE)
@arcli.command("extract")
def command_agents_summary_extract(summary_file: str):
    """
    Extracts compact test summary information from a testrun_summary.json file.
    """

    try:
        resolved = resolve_file_path(summary_file)
    except FileNotFoundError as err:
        format_error(str(err))
        sys.exit(1)

    try:
        with open(resolved, "r") as fh:
            data = json.load(fh)
    except json.JSONDecodeError:
        format_error(f"Invalid JSON in file: {resolved}")
        sys.exit(1)

    lines = []

    # Overall result and timing
    lines.append(format_kv("result", data.get("result", "UNKNOWN")))
    lines.append(format_kv("start", data.get("start", "")))
    lines.append(format_kv("stop", data.get("stop", "")))

    # Detail counters
    detail = data.get("detail")
    if detail is not None:
        lines.append(format_section("detail"))
        lines.append(format_kv("passed", detail.get("passed", 0), indent=2))
        lines.append(format_kv("failed", detail.get("failed", 0), indent=2))
        lines.append(format_kv("errors", detail.get("errors", 0), indent=2))
        lines.append(format_kv("skipped", detail.get("skipped", 0), indent=2))
        lines.append(format_kv("total", detail.get("total", 0), indent=2))

    # Job metadata (omit unset fields)
    job = data.get("job")
    if job is not None:
        job_lines = []
        for field in ("id", "name", "type"):
            val = omit_unset(job.get(field))
            if val is not None:
                job_lines.append(format_kv(field, val, indent=2))
        if job_lines:
            lines.append(format_section("job"))
            lines.extend(job_lines)

    # Build metadata (omit unset fields)
    build = data.get("build")
    if build is not None:
        build_lines = []
        for field in ("branch", "build"):
            val = omit_unset(build.get(field))
            if val is not None:
                build_lines.append(format_kv(field, val, indent=2))
        if build_lines:
            lines.append(format_section("build"))
            lines.extend(build_lines)

    print("\n".join(lines))
