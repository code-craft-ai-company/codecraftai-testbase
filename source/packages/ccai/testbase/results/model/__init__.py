"""
    .. module:: ccai.testbase.results.model
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for model.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.testbase.results.model.jobinfo import MissingOptionalFieldWarning
from ccai.testbase.results.model.checkresult import CheckResult
from ccai.testbase.results.model.streaminginfo import (
    StreamingInfo,
    StreamingProtocol,
    StreamingCallback
)
from ccai.testbase.results.model.nestedprogressinfo import NestedProgressInfo
from ccai.testbase.results.model.progressaggregator import ProgressAggregator

__all__ = [
    "CheckResult",
    "MissingOptionalFieldWarning",
    "NestedProgressInfo",
    "ProgressAggregator",
    "StreamingInfo",
    "StreamingProtocol",
    "StreamingCallback"
]
