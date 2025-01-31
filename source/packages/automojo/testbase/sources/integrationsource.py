
__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Callable

from automojo.testbase.coupling.integrationcoupling import IntegrationCoupling

from automojo.testbase.sources.sourcebase import SourceBase

class IntegrationSource(SourceBase):

    def __init__(self, source_func: Callable, integration_type: IntegrationCoupling, constraints: dict):
        SourceBase.__init__(self, source_func, None, integration_type, constraints)
        return
