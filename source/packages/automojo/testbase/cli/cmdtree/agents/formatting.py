"""
    .. module:: automojo.testbase.cli.cmdtree.agents.formatting
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Compact output formatting utilities for agent commands.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import sys

from typing import Optional


# Placeholder values that indicate "not set" in TestBase result artifacts
UNSET_PLACEHOLDERS = {"(not-set)", "(unknown)", "null", "", None}


def omit_unset(value) -> Optional[str]:
    """
        Returns the value as a string if it is a meaningful value, or None
        if it matches a known placeholder.

        :param value: The value to check.
        :returns: The string value, or None if it should be omitted.
    """
    if value is None:
        return None

    sval = str(value)
    if sval in UNSET_PLACEHOLDERS:
        return None

    return sval


def format_kv(key: str, value: str, indent: int = 0) -> str:
    """
        Formats a key-value pair as a compact output line.

        :param key: The key name.
        :param value: The value.
        :param indent: Number of spaces to indent.
        :returns: A formatted string in the form 'key: value'.
    """
    prefix = " " * indent
    return f"{prefix}{key}: {value}"


def format_section(name: str, indent: int = 0) -> str:
    """
        Formats a section header line.

        :param name: The section name.
        :param indent: Number of spaces to indent.
        :returns: A formatted section header string.
    """
    prefix = " " * indent
    return f"{prefix}{name}:"


def format_error(message: str) -> None:
    """
        Prints an error message to stderr in the standard agent error format.

        :param message: The error description.
    """
    print(f"ERROR: {message}", file=sys.stderr)
