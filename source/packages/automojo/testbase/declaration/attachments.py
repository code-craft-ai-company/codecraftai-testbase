"""
    .. module:: automojo.testbase.declaration.attachments
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for attachments.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Any, Callable, Dict, Optional

NoneType = type(None)

from automojo.errors.exceptions import SemanticError

from automojo.testbase.origins.validatororigin import ValidatorOrigin
from automojo.testbase.injection.injectionregistry import injection_registry
from automojo.testbase.origins.resourceorigin import ResourceOrigin
from automojo.testbase.resourcelifespan import ResourceLifespan

def parameter(source: Callable, *, identifier: str, constraints: Optional[Dict[str, Any]]=None) -> Callable[[Callable], Callable]:
    """
        Decorator factory for attaching a resource parameter to a specific test function.

        The `@parameter` decorator creates a ResourceOrigin with Test lifespan, binding
        a resource source to a specific test function. This localizes the resource
        injection to the decorated test, creating a new resource instance for each
        test execution.

        :param source: The factory function that produces the resource. Must be a
            function previously decorated with `@resource_factory`, `@integration_factory`,
            or `@configuration_factory`.
        :param identifier: The name used to identify this parameter origin. If None,
            defaults to the source function's name. Cannot be the reserved word "constraints".
        :param constraints: Optional dictionary of constraint values to pass to the
            source factory function. The source function must have a 'constraints'
            parameter to accept these values.

        :returns: A decorator function that registers the parameter origin with the
            InjectionRegistry and returns the original test function unchanged.

        :raises SemanticError: When the identifier is the reserved word "constraints".
        :raises SemanticError: When constraints are provided but the source function
            has no 'constraints' parameter in its signature.

        .. rubric:: Example

        .. code-block:: python

            from automojo.testbase.declaration import resource_factory, parameter

            @resource_factory()
            def database_connection() -> Generator[DatabaseConnection, None, None]:
                conn = DatabaseConnection()
                yield conn
                conn.close()

            @parameter(database_connection, identifier="db")
            def test_database_query(db: DatabaseConnection):
                result = db.execute("SELECT 1")
                assert result is not None

            # With constraints
            @parameter(database_connection, identifier="db", constraints={"readonly": True})
            def test_readonly_query(db: DatabaseConnection):
                pass
    """

    def decorator(subscriber: Callable) -> Callable:
        nonlocal source
        nonlocal identifier
        nonlocal constraints

        # =====================================================================
        # IDENTIFIER RESOLUTION
        # =====================================================================
        # If no identifier is provided, default to the source function's name.
        # This allows for concise decorator usage while maintaining uniqueness.
        # =====================================================================

        if identifier is None:
            identifier = source.__name__

        # Validate identifier is not the reserved word 'constraints'
        # 'constraints' is reserved for dynamic constraint delivery mechanism
        if identifier == 'constraints':
            errmsg = "Invalid identifier.  The word 'constraints' is reseved for delivering dynamic constraints."
            raise SemanticError(errmsg) from None

        # =====================================================================
        # SCOPE RESOLUTION FOR TEST-ATTACHED PARAMETERS
        # =====================================================================
        # For @parameter attachments, the resource has Test lifespan, meaning
        # a new instance is created for each test execution.
        #
        # The assigned_scope is constructed as "module_name#function_name"
        # which uniquely identifies the test function this parameter is
        # attached to. This scope format allows the injection registry to
        # associate the parameter origin with the specific test.
        # =====================================================================

        life_span = ResourceLifespan.Test

        # Look up the registered source for the factory function
        source_info = injection_registry.lookup_resource_source(source)

        # Validate constraints compatibility with source function signature
        if constraints is not None and 'constraints' not in source_info.source_signature.parameters:
            raise SemanticError("Attempting to pass constraints to a parameter origin with no 'constraints' parameter.") from None

        # Construct the scope identifier: "module_name#function_name"
        # This format uniquely identifies the test function in the scope tree
        assigned_scope = "{}#{}".format(subscriber.__module__, subscriber.__name__)

        # Create and register the ResourceOrigin with the injection registry
        param_origin = ResourceOrigin(assigned_scope, identifier, life_span, source_info, constraints)
        injection_registry.register_resource_origin(identifier, param_origin)

        return subscriber
    
    return decorator


def validation(source: Callable, *, suffix: str, identifier: Optional[str]=None, constraints: Optional[Dict[str, Any]]=None) -> Callable[[Callable], Callable]:
    """
        Decorator factory for attaching a validator to a specific test function.

        The `@validation` decorator creates a ValidatorOrigin, binding a validator
        source to a specific test function. Validators are executed after the test
        completes to perform post-test validation.

        :param source: The factory function that produces the validator. Must be a
            function previously decorated with `@validator_factory`.
        :param suffix: A string suffix used to distinguish this validator instance.
            This is appended to create unique validator identifiers when multiple
            validators of the same type are attached to a test.
        :param identifier: Optional name used to identify this validator origin.
            If None, defaults to the source function's name. Cannot be the reserved
            word "constraints".
        :param constraints: Optional dictionary of constraint values to pass to the
            validator factory function.

        :returns: A decorator function that registers the validator origin with the
            InjectionRegistry and returns the original test function unchanged.

        :raises SemanticError: When the identifier is the reserved word "constraints".

        .. rubric:: Example

        .. code-block:: python

            from automojo.testbase.declaration import validator_factory, validation

            @validator_factory()
            def response_validator() -> ResponseValidator:
                return ResponseValidator()

            @validation(response_validator, suffix="_response")
            def test_api_call():
                response = api.call()
                # Validator runs after test completes

            # With custom identifier
            @validation(response_validator, suffix="_custom", identifier="my_validator")
            def test_another_call():
                pass
    """

    def decorator(subscriber: Callable) -> Callable:
        nonlocal source
        nonlocal identifier
        nonlocal suffix

        # =====================================================================
        # IDENTIFIER RESOLUTION
        # =====================================================================
        # If no identifier is provided, default to the source function's name.
        # The suffix parameter allows multiple validators of the same type
        # to be attached to a single test with unique identifiers.
        # =====================================================================

        if identifier is None:
            identifier = source.__name__

        # Validate identifier is not the reserved word 'constraints'
        if identifier == 'constraints':
            errmsg = "Invalid identifier.  The word 'constraints' is reseved for delivering dynamic constraints."
            raise SemanticError(errmsg) from None

        # =====================================================================
        # SCOPE RESOLUTION FOR VALIDATION ATTACHMENTS
        # =====================================================================
        # For @validation attachments, the scope is constructed as
        # "module_name#function_name" which uniquely identifies the test
        # function this validator is attached to.
        #
        # Validators are executed after the test completes to perform
        # post-test validation (e.g., checking response codes, verifying
        # state changes, etc.).
        # =====================================================================

        # Look up the registered validator source for the factory function
        source_info = injection_registry.lookup_validator_source(source)

        # Construct the scope identifier: "module_name#function_name"
        assigned_scope = "{}#{}".format(subscriber.__module__, subscriber.__name__)

        # Create and register the ValidatorOrigin with the injection registry
        # The suffix is used to create unique validator identifiers when
        # multiple validators of the same type are attached to a test
        validator_origin = ValidatorOrigin(assigned_scope, identifier, suffix, source_info, constraints=constraints)
        injection_registry.register_validator_origin(identifier, validator_origin)

        return subscriber
    
    return decorator