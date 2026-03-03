"""
    .. module:: automojo.testbase.results.model.resulttype
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for resulttype.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []



from enum import IntEnum

class ResultType(IntEnum):
    """
        Enumeration to mark the type of result.
    """
    JOB = 0
    PACKAGE = 1
    SCOPE = 2
    TASK_CONTAINER = 3
    TASK = 4
    TEST_CONTAINER = 5
    TEST = 6
    STEP_CONATINER = 7
    STEP = 8
    TASKING_GROUP = 9
    TASKING = 10
    CHECK = 11
