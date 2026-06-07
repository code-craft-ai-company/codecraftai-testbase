"""
    .. module:: ccai.testbase.results.model.resultcode
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for resultcode.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from enum import IntEnum

class ResultCode(IntEnum):
    """
        Enumeration that summarizes a result.
    """
    UNSET = 0
    PASSED = 1
    SKIPPED = 2
    ERRORED = 3
    FAILED = 4
    CANCELLED = 5
    UNKOWN = 6
