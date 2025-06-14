"""
    .. module:: automojo.testbase.results.model.progressdelivery
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for progressdelivery.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import List, Protocol

from dataclasses import dataclass

from automojo.testbase.results.model.progressinfo import ProgressInfo


class ProgressDeliveryMethod:
    SUMMARY_PULL_PROGRESS = "summary-pull-progress"



class TaskingProgressCallback(Protocol):

    def __call__(self, progress: List[ProgressInfo]) -> None: ...


@dataclass
class SummaryProgressDelivery:
    progress_interval: float
    progress_callback: TaskingProgressCallback

