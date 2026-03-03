"""
    .. module:: automojo.testbase.cli.cmdtree.agents.jsosparser
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Parser for JSOS (JSON Stream of Objects) result files.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from typing import Dict, List
from collections import OrderedDict

import json


def parse_file(filepath: str) -> List[dict]:
    """
        Parses a JSOS file into a list of dictionaries.

        JSOS files use ASCII Record Separator (0x1e) to delimit JSON objects.
        Falls back to blank-line splitting when no RS characters are found.

        :param filepath: Path to the JSOS file.
        :returns: A list of parsed JSON objects.
        :raises ValueError: If a chunk contains invalid JSON.
    """
    entries = []

    with open(filepath, "r") as fh:
        content = fh.read()

    chunks = _split_chunks(content)

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            entry = json.loads(chunk)
            entries.append(entry)
        except json.JSONDecodeError as err:
            raise ValueError(
                f"Invalid JSON in JSOS file '{filepath}': {err}"
            )

    return entries


def filter_tests(entries: List[dict]) -> List[dict]:
    """
        Filters a list of JSOS entries to include only test entries (rtype=TEST).

        :param entries: List of parsed JSOS entries.
        :returns: List of entries where rtype is 'TEST'.
    """
    return [e for e in entries if e.get("rtype") == "TEST"]


def get_final_results(entries: List[dict]) -> OrderedDict:
    """
        Deduplicates test entries by name and returns only the final result
        for each test, preserving the order in which tests first appear.

        When a test has multiple entries (e.g., UNSET followed by PASSED),
        the last entry wins.

        :param entries: List of parsed JSOS entries.
        :returns: An OrderedDict mapping test name to its final result entry.
    """
    test_entries = filter_tests(entries)
    results = OrderedDict()

    for entry in test_entries:
        name = entry.get("name", "")
        results[name] = entry

    return results


# ASCII Record Separator character used as JSOS object delimiter
_RS = "\x1e"


def _split_chunks(content: str) -> List[str]:
    """
        Splits JSOS content into individual JSON object chunks.

        The primary delimiter is the ASCII Record Separator (0x1e) character,
        which TestBase uses to separate streaming JSON objects. If no RS
        characters are found, falls back to blank-line splitting for
        compatibility with test data.

        :param content: The raw JSOS file content.
        :returns: A list of chunk strings.
    """
    if _RS in content:
        # Primary format: RS-delimited
        return [chunk for chunk in content.split(_RS) if chunk.strip()]

    # Fallback: blank-line-delimited (for test data)
    chunks = []
    current_lines = []

    for line in content.split("\n"):
        stripped = line.strip()
        if stripped == "" and current_lines:
            chunks.append("\n".join(current_lines))
            current_lines = []
        else:
            if stripped:
                current_lines.append(line)

    if current_lines:
        chunks.append("\n".join(current_lines))

    return chunks
