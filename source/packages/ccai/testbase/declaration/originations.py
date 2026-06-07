"""
    .. module:: ccai.testbase.declaration.originations
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for originations.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""


__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Callable, Dict, Optional

import inspect

from ccai.errors.exceptions import SemanticError

from ccai.xmodules.xinspect import is_typed_from_type


from ccai.testbase.origins.resourceorigin import ResourceOrigin
from ccai.testbase.injection.injectionregistry import injection_registry
from ccai.testbase.coupling.integrationcoupling import IntegrationCoupling
from ccai.testbase.sources.integrationsource import IntegrationSource
from ccai.testbase.resourcelifespan import ResourceLifespan


def parameter(source_func: Callable, *, identifier: str, life_span: ResourceLifespan=None, assigned_scope: Optional[str]=None, constraints: Optional[Dict]=None) -> Callable[[Callable], Callable]:
    """
        Creates a global parameter origin for sharing resources across multiple tests.

        The `parameter()` origination function creates a ResourceOrigin with Package
        or Session lifespan, allowing resources to be shared across multiple tests
        within a scope. Unlike the `@parameter` attachment decorator which creates
        Test-scoped resources, this function creates longer-lived resources.

        This function is NOT a decorator. To attach a parameter to a specific test,
        use `@testbase.attach.parameter()` instead.

        :param source_func: The factory function that produces the resource. Must be a
            function previously decorated with `@resource_factory`, `@integration_factory`,
            or `@configuration_factory`. Cannot be None.
        :param identifier: The name used to identify this parameter origin. If None,
            defaults to the source function's name. Cannot be the reserved word "constraints".
        :param life_span: The ResourceLifespan for the resource. Cannot be ResourceLifespan.Test.
            If None, defaults to Session for IntegrationCoupling resources and Package
            for all other resource types.
        :param assigned_scope: Optional scope path to assign the resource origin to.
            Cannot be specified for IntegrationSource resources. For Package lifespan,
            defaults to the calling module's name.
        :param constraints: Optional dictionary of constraint values to pass to the
            source factory function. The source function must have a 'constraints'
            parameter to accept these values.

        :returns: A decorator function (for error trapping purposes only - this function
            should not be used as a decorator).

        :raises SemanticError: When source_func is None.
        :raises SemanticError: When life_span is ResourceLifespan.Test.
        :raises SemanticError: When the identifier is the reserved word "constraints".
        :raises SemanticError: When assigned_scope is specified for an IntegrationSource.
        :raises SemanticError: When constraints are provided but the source function
            has no 'constraints' parameter in its signature.
        :raises SemanticError: When mistakenly used as a decorator (provides guidance
            to use `@testbase.attach.parameter()` instead).

        .. rubric:: Example

        .. code-block:: python

            from ccai.testbase.declaration import resource_factory
            from ccai.testbase.declaration.originations import parameter
            from ccai.testbase.resourcelifespan import ResourceLifespan

            @resource_factory()
            def shared_database() -> Generator[DatabaseConnection, None, None]:
                conn = DatabaseConnection()
                yield conn
                conn.close()

            # Create a package-scoped parameter (default for non-integration resources)
            parameter(shared_database, identifier="shared_db")

            # Create a session-scoped parameter
            parameter(shared_database, identifier="session_db", life_span=ResourceLifespan.Session)

            # With constraints
            parameter(shared_database, identifier="test_db", constraints={"pool_size": 5})
    """

    # =========================================================================
    # DECORATOR TRAP FOR MISUSE DETECTION
    # =========================================================================
    # This function is NOT a decorator, but users may mistakenly try to use it
    # as one. We define a decorator function that raises a helpful error message
    # guiding users to the correct API (@testbase.attach.parameter()).
    # =========================================================================
    def decorator(subscriber: Callable) -> Callable:
        errmsg = "The '@testbase.originate.parameter()' function is not a decorator.  Use '@testbase.attach.parameter()' to localize a parameter to a specific test."
        raise SemanticError(errmsg)

    # =========================================================================
    # INPUT VALIDATION
    # =========================================================================
    # Validate all input parameters before proceeding with scope resolution
    # =========================================================================

    # Validate source_func is provided
    if source_func is None:
        errmsg = "The 'source_func' parameter cannot be 'None'."
        raise SemanticError(errmsg) from None

    # Validate life_span is not Test (use @parameter attachment for Test scope)
    if life_span == ResourceLifespan.Test:
        errmsg = "The 'life_span' parameter cannot be 'ResourceLifespan.Test'."
        raise SemanticError(errmsg) from None

    # Default identifier to the source function's name if not provided
    if identifier is None:
        identifier = source_func.__name__

    # Validate identifier is not the reserved word 'constraints'
    # 'constraints' is reserved for dynamic constraint delivery mechanism
    if identifier == 'constraints':
        errmsg = "Invalid identifier.  The word 'constraints' is reseved for delivering dynamic constraints."
        raise SemanticError(errmsg) from None

    # =========================================================================
    # SOURCE LOOKUP AND VALIDATION
    # =========================================================================
    # Look up the source information from the injection registry and validate
    # that the source is compatible with the requested configuration
    # =========================================================================

    # Look up the registered source for the factory function
    source_info = injection_registry.lookup_resource_source(source_func)

    # Validate assigned_scope is not used with IntegrationSource
    # IntegrationSource resources have fixed Session scope and cannot be reassigned
    if assigned_scope is not None:
        if isinstance(source_info, IntegrationSource):
            errmsg = "The 'assigned_scope' parameter should not be specified unless the source of the resource is of type 'scope' or 'resource'."
            raise SemanticError(errmsg) from None

    # Validate constraints compatibility with source function signature
    # The source function must have a 'constraints' parameter to accept constraint values
    if constraints is not None and 'constraints' not in source_info.source_signature.parameters:
            raise SemanticError("Attempting to pass constraints to a parameter origin with no 'constraints' parameter.") from None

    # =========================================================================
    # SCOPE RESOLUTION LOGIC
    # =========================================================================
    # Determine the appropriate scope and lifespan for the resource origin.
    # The scope resolution follows these rules:
    #
    # 1. LIFESPAN DETERMINATION (if not explicitly provided):
    #    - IntegrationCoupling resources default to Session lifespan
    #      (integrations are expensive, shared across all tests)
    #    - All other resources default to Package lifespan
    #      (shared within a module hierarchy)
    #
    # 2. SCOPE ASSIGNMENT (based on lifespan):
    #    - Package lifespan: scope defaults to the calling module's name
    #      (e.g., "mypackage.tests.test_module")
    #    - Session lifespan: scope is always "<session>" (global singleton)
    #
    # The scope determines where in the injection scope tree the resource
    # origin is registered, which affects parameter visibility and resolution.
    # =========================================================================

    # Get the calling module to determine default scope for Package lifespan
    caller_frame = inspect.stack()[1]
    calling_module = inspect.getmodule(caller_frame[0])
    
    # Step 1: Determine lifespan if not explicitly provided
    if life_span is None:
        res_type = source_info.resource_type
        # Check if the resource type is a proper type (not a generic or special form)
        if is_typed_from_type(res_type):
            # IntegrationCoupling resources default to Session lifespan
            # because integrations are typically expensive to create and
            # should be shared across all tests in the session
            if issubclass(res_type, IntegrationCoupling):
                life_span = ResourceLifespan.Session
            else:
                # All other resources default to Package lifespan
                # allowing sharing within a module hierarchy
                life_span = ResourceLifespan.Package
        else:
            # For non-standard types (generics, etc.), default to Package
            life_span = ResourceLifespan.Package

    # Step 2: Determine the assigned scope based on lifespan
    if life_span == ResourceLifespan.Package:
        # For Package lifespan, default scope to the calling module's name
        # This makes the resource visible to all tests in that module and submodules
        if assigned_scope is None:
            assigned_scope = calling_module.__name__
    elif life_span == ResourceLifespan.Session:
        # For Session lifespan, always use the special "<session>" scope
        # This makes the resource globally visible to all tests
        assigned_scope = "<session>"

    # =========================================================================
    # ORIGIN REGISTRATION
    # =========================================================================
    # Create the ResourceOrigin and register it with the injection registry
    # =========================================================================

    param_origin = ResourceOrigin(assigned_scope, identifier, life_span, source_info, constraints)
    injection_registry.register_resource_origin(identifier, param_origin)

    return decorator

