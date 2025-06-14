"""
    .. module:: automojo.testbase.testref
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for testref.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Any, List, Optional, OrderedDict

from types import FunctionType

import collections

from automojo.testbase.injection.injectionmoment import InjectionMoment

class TestRef(InjectionMoment):
    """
        The :class:`TestRef` objects are used to refer to a reference to a test.  We use :class:`TestRef` instances
        to reference the tests that are going to be run so we can control the lifespan of test case instances
        and control our memory consumption during test runs with large collections of test cases.

        The :class:`TestRef` object allows us to delay the creation of test runtime instance data and state until it is
        necessary to instantiate it and allows us to cleanup the runtime instance and state as soon as it is no longer
        being used.
    """

    def __init__(self, testfunc: FunctionType, monikers: Optional[List[str]] = None, pivots: Optional[OrderedDict[str, Any]] = None):
        """
            Initializes the test reference object.

            :param FunctionType testfunc: The test function being referenced.
            :param List[str] monikers: Optional list of monikers associated with the test.
            :param OrderedDict[str, Any] pivots: Optional mapping describing pivot variations.

            :returns: ``None``
            :rtype: None
        """
        if monikers is None:
            monikers = []

        if pivots is None:
            pivots = collections.OrderedDict()

        super().__init__(testfunc, monikers=monikers, pivots=pivots)
        return
