"""
    .. module:: automojo.testbase.results.model.progresscode
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for progresscode.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from enum import Enum


class ProgressCode(str, Enum):
    """
        Enumeration of task progress states.
    """

    Completed = "Completed"
    Errored = "Errored"
    Failed = "Failed"
    NotStarted = "NotStarted"
    Paused = "Paused"
    Running = "Running"
