"""
    .. module:: automojo.testbase.testgroup
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for testgroup.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []



import logging

from automojo.testbase.testref import TestRef

from automojo.testbase.injection.injectiongroup import InjectionGroup

logger = logging.getLogger()

class TestGroup(InjectionGroup):
    """
              -------------
              |  Group A  |
        ---------------------------
        |  Group AA  |  Scope AB  |
        -------------------------------
        |         Scope AAA/ABA       |
        -------------------------------
    """

    def __init__(self, name, package=None):
        super().__init__(name, package=package)
        return

    def add_descendent(self, test_ref: TestRef):
        super().add_descendent(test_ref)
        return
