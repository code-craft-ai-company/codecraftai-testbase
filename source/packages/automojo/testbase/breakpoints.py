"""
.. module:: breakpoints
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Declares the wellknown breakpoints availabel in the 'testbase' application.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from enum import Enum

class WELLKNOWN_BREAKPOINTS(str, Enum):
    TEST_DISCOVERY = "test-discovery"
    TESTRUN_START = "testrun-start"
