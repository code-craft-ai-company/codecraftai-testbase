"""
    .. module:: automojo.testbase.cli.cmdtree.agents.config.extract
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Agent command for extracting test run configuration.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import json
import sys

from typing import Optional

from automojo.arcli import decorators as arcli

from automojo.testbase.cli.cmdtree.agents.formatting import (
    format_kv,
    format_section,
    format_error,
    omit_unset
)
from automojo.testbase.cli.cmdtree.agents.pathresolver import resolve_file_path


HELP_CONFIG_FILE = "Path to a startup-configuration.json file."


@arcli.option("--config-file", required=True, help=HELP_CONFIG_FILE)
@arcli.command("extract")
def command_agents_config_extract(config_file: str):
    """
    Extracts key configuration information from a test run startup-configuration.json file.
    """

    try:
        resolved = resolve_file_path(config_file)
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

    # Extract key configuration fields
    # The configuration structure varies, so we extract known fields safely
    _extract_field(lines, data, "testroot", "testroot")
    _extract_field(lines, data, "output_directory", "output_directory")
    _extract_field(lines, data, "runid", "runid")
    _extract_field(lines, data, "starttime", "starttime")

    # Logging levels
    log_lines = []
    _extract_field(log_lines, data, "console_log_level", "console", indent=2)
    _extract_field(log_lines, data, "file_log_level", "file", indent=2)
    if log_lines:
        lines.append(format_section("logging"))
        lines.extend(log_lines)

    # Debug settings
    debug_lines = []
    _extract_field(debug_lines, data, "debugger", "debugger", indent=2)
    _extract_field(debug_lines, data, "breakpoints", "breakpoints", indent=2)
    if debug_lines:
        lines.append(format_section("debug"))
        lines.extend(debug_lines)

    if lines:
        print("\n".join(lines))
    else:
        print("No configuration data extracted")


def _extract_field(lines: list, data: dict, source_key: str, output_key: str, indent: int = 0):
    """
        Extracts a field from the data dict and appends a formatted line if the value is set.

        :param lines: The list of output lines to append to.
        :param data: The JSON data dictionary.
        :param source_key: The key to look up in the data.
        :param output_key: The key name to use in the output.
        :param indent: Number of spaces to indent.
    """
    val = data.get(source_key)
    clean = omit_unset(val)
    if clean is not None:
        lines.append(format_kv(output_key, clean, indent=indent))
