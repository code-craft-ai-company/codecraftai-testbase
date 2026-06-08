"""
    .. module:: ccai.testbase.sources.validatorsource
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for validatorsource.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []
__version__ = "1.0.0"


from typing import Callable, Type

from ccai.testbase.sources.sourcebase import SourceBase

class ValidatorSource(SourceBase):
    """
        Source wrapper for validator implementations.
    """

    def __init__(self, source_func: Callable, resource_type: Type, constraints: dict):
        SourceBase.__init__(self, source_func, None, resource_type, constraints)
        return
