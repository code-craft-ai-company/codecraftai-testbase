"""
    .. module:: ccai.testbase.results.model.progressdelivery
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for progressdelivery.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import List, Protocol

from dataclasses import dataclass

from ccai.testbase.results.model.progressinfo import ProgressInfo


class ProgressDeliveryMethod:
    """
        Well-known progress delivery methods.
    """
    SUMMARY_PULL_PROGRESS = "summary-pull-progress"



class TaskingProgressCallback(Protocol):
    """
        Callable protocol for receiving task progress updates.
    """

    def __call__(self, progress: List[ProgressInfo]) -> None: ...


@dataclass
class SummaryProgressDelivery:
    """
        Configuration for periodic progress callbacks.
    """
    progress_interval: float
    progress_callback: TaskingProgressCallback

