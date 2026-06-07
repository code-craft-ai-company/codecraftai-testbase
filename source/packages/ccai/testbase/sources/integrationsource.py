"""
    .. module:: ccai.testbase.sources.integrationsource
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for integrationsource.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Callable

from ccai.testbase.coupling.integrationcoupling import IntegrationCoupling

from ccai.testbase.sources.sourcebase import SourceBase

class IntegrationSource(SourceBase):
    """
        Source wrapper for integration resources.
    """

    def __init__(self, source_func: Callable, integration_type: IntegrationCoupling, constraints: dict):
        SourceBase.__init__(self, source_func, None, integration_type, constraints)
        return
