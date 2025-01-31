
__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from enum import Enum

class ProgressType(str, Enum):

    NumericRange = "NumericRange"
    Sequential = "Sequential"
    TimeSpan = "TimeSpan"
