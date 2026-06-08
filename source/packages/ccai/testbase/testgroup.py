"""
    .. module:: ccai.testbase.testgroup
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for testgroup.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []



from ccai.xmodules.xlogging.enhancedloggers import getEnhancedLogger

from ccai.testbase.testref import TestRef
from ccai.testbase.injection.injectiongroup import InjectionGroup


logger = getEnhancedLogger()

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
        """
            Initializes the :class:`TestGroup` with the specified name and
            optional package.

            :param name: The name of the group being created.
            :param package: Optional package name associated with the group.
        """
        super().__init__(name, package=package)
        return

    def add_descendent(self, test_ref: TestRef):
        """
            Adds a :class:`TestRef` instance as a descendent of this group.

            :param test_ref: The :class:`TestRef` to add.
        """
        super().add_descendent(test_ref)
        return
