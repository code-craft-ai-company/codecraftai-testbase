"""
    .. module:: ccai.testbase.results.filtering
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for result filtering and search functionality.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.testbase.results.filtering.resultfilter import (
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
