"""
    .. module:: ccai.testbase.results
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for results.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


# NOTE: the result streaming transport relocated to codecraftai-integration-runtime (Phase 3 results
# split): ccai.integrationruntime.results.streaming (ResultStreamer / RestResultStreamer /
# WebSocketResultStreamer / create_result_streamer). The near-standalone testbase framework keeps
# only the JSOS/JSON serialization core; real-time streaming to external services is an
# integration-tier concern.

# Import filtering module for convenience
from ccai.testbase.results.filtering import (
    ResultFilter,
    ResultFilterCriteria,
    filter_results,
    search_results
)

__all__ = [
    "ResultFilter",
    "ResultFilterCriteria",
    "filter_results",
    "search_results"
]


