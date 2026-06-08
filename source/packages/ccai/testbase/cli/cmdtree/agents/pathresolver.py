"""
    .. module:: ccai.testbase.cli.cmdtree.agents.pathresolver
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: File path resolution utility for agent commands.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import os


def resolve_file_path(filepath: str) -> str:
    """
        Resolves a file path by expanding environment variables, expanding
        the user home directory, and converting to an absolute path.

        :param filepath: The file path to resolve.
        :returns: The resolved absolute file path.
        :raises FileNotFoundError: If the resolved path does not exist as a file.
    """
    resolved = os.path.abspath(
        os.path.expandvars(
            os.path.expanduser(filepath)
        )
    )

    if not os.path.isfile(resolved):
        raise FileNotFoundError(f"File not found: {resolved}")

    return resolved
