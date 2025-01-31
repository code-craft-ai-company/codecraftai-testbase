
__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from enum import Enum


class ProgressCode(str, Enum):

    Completed = "Completed"
    Errored = "Errored"
    Failed = "Failed"
    NotStarted = "NotStarted"
    Paused = "Paused"
    Running = "Running"
