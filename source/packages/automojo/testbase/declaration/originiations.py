"""
    .. module:: automojo.testbase.declaration.originiations
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for originiations.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""


__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Callable, Dict, Optional

import inspect

from automojo.errors.exceptions import SemanticError

from automojo.foundation.xinspect import is_typed_from_type


from automojo.testbase.origins.resourceorigin import ResourceOrigin
from automojo.testbase.injection.injectionregistry import injection_registry
from automojo.testbase.coupling.integrationcoupling import IntegrationCoupling
from automojo.testbase.sources.integrationsource import IntegrationSource
from automojo.testbase.resourcelifespan import ResourceLifespan


def parameter(source_func, *, identifier: str, life_span: ResourceLifespan=None, assigned_scope: Optional[str]=None, constraints: Optional[Dict]=None):

    # Trap for the use of this version of 'parameter' as a decorator and provide a more explicit error message if it gets misused.
    def decorator(subscriber: Callable) -> Callable:
        errmsg = "The '@testbase.originate.parameter()' function is not a decorator.  Use '@testbase.attach.parameter()' to localize a parameter to a specific test."
        raise SemanticError(errmsg)

    if source_func is None:
        errmsg = "The 'source_func' parameter cannot be 'None'."
        raise SemanticError(errmsg) from None

    if life_span == ResourceLifespan.Test:
        errmsg = "The 'life_span' parameter cannot be 'ResourceLifespan.Test'."
        raise SemanticError(errmsg) from None

    if identifier is None:
        identifier = source_func.__name__

    if identifier == 'constraints':
        errmsg = "Invalid identifier.  The word 'constraints' is reseved for delivering dynamic constraints."
        raise SemanticError(errmsg) from None

    source_info = injection_registry.lookup_resource_source(source_func)
    if assigned_scope is not None:
        if isinstance(source_info, IntegrationSource):
            errmsg = "The 'assigned_scope' parameter should not be specified unless the source of the resource is of type 'scope' or 'resource'."
            raise SemanticError(errmsg) from None

    if constraints is not None and 'constraints' not in source_info.source_signature.parameters:
            raise SemanticError("Attempting to pass constraints to a parameter origin with no 'constraints' parameter.") from None

    caller_frame = inspect.stack()[1]
    calling_module = inspect.getmodule(caller_frame[0])
    
    if life_span is None:
        res_type = source_info.resource_type
        if is_typed_from_type(res_type):
            if issubclass(res_type, IntegrationCoupling):
                life_span = ResourceLifespan.Session
            else:
                life_span = ResourceLifespan.Package
        else:
            life_span = ResourceLifespan.Package

    if life_span == ResourceLifespan.Package:
        if assigned_scope is None:
            assigned_scope = calling_module.__name__
    elif life_span == ResourceLifespan.Session:
        assigned_scope = "<session>"

    param_origin = ResourceOrigin(assigned_scope, identifier, life_span, source_info, constraints)
    injection_registry.register_resource_origin(identifier, param_origin)

    return decorator

