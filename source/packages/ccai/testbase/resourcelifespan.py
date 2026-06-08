"""
    .. module:: ccai.testbase.resourcelifespan
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for resourcelifespan.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""


__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import enum

class ResourceLifespan(str, enum.Enum):
    """
        Enumeration of lifespans for injectable resources.
    """

    Session = "session"
    Package = "package"
    Test = "test"
    Task = "task"
