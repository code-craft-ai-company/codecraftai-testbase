"""
    .. module:: automojo.testbase.results.model
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for model.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.testbase.results.model.jobinfo import MissingOptionalFieldWarning
from automojo.testbase.results.model.checkresult import CheckResult
from automojo.testbase.results.model.streaminginfo import (
    StreamingInfo,
    StreamingProtocol,
    StreamingCallback
)
from automojo.testbase.results.model.nestedprogressinfo import NestedProgressInfo
from automojo.testbase.results.model.progressaggregator import ProgressAggregator

__all__ = [
    "CheckResult",
    "MissingOptionalFieldWarning",
    "NestedProgressInfo",
    "ProgressAggregator",
    "StreamingInfo",
    "StreamingProtocol",
    "StreamingCallback"
]
