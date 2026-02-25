"""
    .. module:: automojo.testbase.results
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for results.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


# Import streaming module for convenience
from automojo.testbase.results.streaming import (
    ResultStreamer,
    RestResultStreamer,
    WebSocketResultStreamer,
    create_result_streamer
)

# Import filtering module for convenience
from automojo.testbase.results.filtering import (
    ResultFilter,
    ResultFilterCriteria,
    filter_results,
    search_results
)

__all__ = [
    "ResultStreamer",
    "RestResultStreamer",
    "WebSocketResultStreamer",
    "create_result_streamer",
    "ResultFilter",
    "ResultFilterCriteria",
    "filter_results",
    "search_results"
]


