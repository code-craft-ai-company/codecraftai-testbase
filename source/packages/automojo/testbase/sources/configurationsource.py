

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []



from typing import Callable, Union

from automojo.testbase.coupling.configurationcoupling import ConfigurationCoupling

from automojo.testbase.sources.sourcebase import SourceBase

class ConfigurationSource(SourceBase):

    def __init__(self, source_func: Callable, query_func: Union[Callable, None], config_type: ConfigurationCoupling, constraints: dict):
        SourceBase.__init__(self, source_func, query_func, config_type, constraints)
        self._source_func = source_func
        return
