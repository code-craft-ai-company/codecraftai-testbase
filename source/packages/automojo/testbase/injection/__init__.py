"""
    .. module:: automojo.testbase.injection
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for injection.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.testbase.injection.introspection import (
    FactoryType,
    FactoryMetadata,
    FactoryListResult
)

from automojo.testbase.injection.injectionregistry import (
    InjectionRegistry,
    injection_registry
)


