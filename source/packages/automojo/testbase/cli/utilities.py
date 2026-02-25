"""
    .. module:: automojo.testbase.cli.utilities
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Utility functions for the CLI.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

import os
from typing import Optional

from automojo.runtime.runtimevariables import RuntimeVariables

def resolve_test_root(root: Optional[str]) -> str:
    """
    Resolves the test root directory, falling back to RuntimeVariables or '.' if not provided.
    Raises ValueError if the directory does not exist.
    """
    if root is None:
        if RuntimeVariables.AM_TESTROOT is not None:
            root = RuntimeVariables.AM_TESTROOT
        else:
            root = "."

    test_root = os.path.abspath(os.path.expandvars(os.path.expanduser(root)))
    if not os.path.isdir(test_root):
        errmsg = "The specified root folder does not exist. root=%s" % root
        if test_root != root:
            errmsg += " expanded=%s" % test_root
        raise ValueError(errmsg)
        
    return test_root
