"""
    .. module:: ccai.testbase.injection
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for injection.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.testbase.injection.introspection import (
    FactoryType,
    FactoryMetadata,
    FactoryListResult
)

from ccai.testbase.injection.injectionregistry import (
    InjectionRegistry,
    injection_registry
)


