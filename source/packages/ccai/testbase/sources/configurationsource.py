"""
    .. module:: ccai.testbase.sources.configurationsource
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for configurationsource.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""




__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []



from typing import Callable, Union

from ccai.testbase.coupling.configurationcoupling import ConfigurationCoupling

from ccai.testbase.sources.sourcebase import SourceBase

class ConfigurationSource(SourceBase):
    """
        Source wrapper for configuration resources.
    """

    def __init__(self, source_func: Callable, query_func: Union[Callable, None], config_type: ConfigurationCoupling, constraints: dict):
        SourceBase.__init__(self, source_func, query_func, config_type, constraints)
        self._source_func = source_func
        return
