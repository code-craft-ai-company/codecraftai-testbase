"""
    .. module:: automojo.testbase.results.model.progresstype
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for progresstype.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from enum import Enum

class ProgressType(str, Enum):

    NumericRange = "NumericRange"
    Sequential = "Sequential"
    TimeSpan = "TimeSpan"
