"""
    .. module:: ccai.testbase.declaration.registrations
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for registrations.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []



from typing import Callable, Dict, Optional, TypeVar

import inspect
import os

NoneType = type(None)

# Generator type names that are supported for factory functions
# This includes both synchronous and asynchronous generator types
GENERATOR_TYPE_NAMES = ("Generator", "AsyncGenerator")

from ccai.errors.exceptions import SemanticError

from ccai.testbase.coupling.configurationcoupling import ConfigurationCoupling
from ccai.testbase.coupling.integrationcoupling import IntegrationCoupling
from ccai.testbase.coupling.validatorcoupling import ValidatorCoupling

from ccai.testbase.sources.configurationsource import ConfigurationSource
from ccai.testbase.sources.integrationsource import IntegrationSource
from ccai.testbase.sources.resourcesource import ResourceSource
from ccai.testbase.sources.validatorsource import ValidatorSource

from ccai.testbase.injection.injectionregistry import injection_registry


_IntegrationSubscriberType = TypeVar("_IntegrationSubscriberType", bound=Callable[..., object])


def integration_factory(*, constraints: Optional[Dict]=None) -> Callable[[Callable], Callable]:
    """
        Decorator factory for registering integration coupling factory functions.

        The `@integration_factory` decorator is used to declare a function as the source
        of an integration resource. The decorated function must be a generator that yields
        an IntegrationCoupling subclass instance.

        :param constraints: Optional dictionary of key-value pairs used to conditionally
            filter resource creation based on runtime constraints.

        :returns: A decorator function that registers the source function with the
            InjectionRegistry and returns the original function unchanged.

        :raises SemanticError: When the decorated function lacks a return type annotation.
        :raises SemanticError: When the return type is an IntegrationCoupling subclass
            returned directly instead of yielded from a generator.
        :raises SemanticError: When the return type does not inherit from IntegrationCoupling.
        :raises SemanticError: When the resource type cannot be determined from the annotation.

        .. rubric:: Example

        .. code-block:: python

            from typing import Generator, AsyncGenerator
            from ccai.testbase.declaration import integration_factory
            from ccai.testbase.coupling import IntegrationCoupling

            class MyIntegration(IntegrationCoupling):
                pass

            @integration_factory()
            def my_integration_source() -> Generator[MyIntegration, None, None]:
                integration = MyIntegration()
                yield integration
                # cleanup code here

            # Async generator example
            @integration_factory()
            async def async_integration_source() -> AsyncGenerator[MyIntegration, None]:
                integration = MyIntegration()
                yield integration
                # async cleanup code here

            # With constraints
            @integration_factory(constraints={"platform": "linux"})
            def linux_integration() -> Generator[LinuxIntegration, None, None]:
                yield LinuxIntegration()
    """
    def decorator(source_function: Callable) -> Callable:
        nonlocal constraints

        # =====================================================================
        # TYPE EXTRACTION LOGIC FOR INTEGRATION FACTORY
        # =====================================================================
        # Integration factories must be generator functions that yield an
        # IntegrationCoupling subclass. The type extraction process:
        #
        # 1. Inspect the function signature to get the return type annotation
        # 2. Check if the annotation is a Generator or AsyncGenerator type (required for integrations)
        # 3. Extract the resource type from the Generator's type arguments:
        #    - Generator[YieldType, SendType, ReturnType]
        #    - AsyncGenerator[YieldType, SendType]
        #    - YieldType is the primary resource type (what the generator yields)
        #    - ReturnType is the fallback if YieldType is None (Generator only)
        # 4. Validate that the extracted type inherits from IntegrationCoupling
        # =====================================================================

        signature = inspect.signature(source_function)
        integration_context = signature.return_annotation

        resource_type = None

        # Step 1: Verify the function has a return type annotation
        if integration_context == inspect._empty:
            errmsg = "Parameters factories for 'integration' functions must have an annotated return type."
            raise SemanticError(errmsg) from None
        else:
            # Step 2: Check if the return type is a Generator or AsyncGenerator
            # Integration factories MUST be generators to support setup/teardown lifecycle
            if hasattr(integration_context, "_name") and integration_context._name in GENERATOR_TYPE_NAMES:
                # Step 3: Extract type arguments from Generator[YieldType, SendType, ReturnType]
                # or AsyncGenerator[YieldType, SendType]
                # The __args__ tuple contains the type parameters
                type_args = integration_context.__args__
                ra_yield_type = type_args[0]

                # For Generator, we have 3 args; for AsyncGenerator, we have 2 args
                # Prefer the yield type as the resource type (standard pattern)
                if ra_yield_type is not NoneType:
                    resource_type = ra_yield_type
                elif len(type_args) >= 3 and type_args[2] is not NoneType:
                    # Fall back to return type if yield type is None (Generator only)
                    resource_type = type_args[2]
            elif issubclass(integration_context, IntegrationCoupling):
                # Direct return of IntegrationCoupling is not allowed - must yield
                # This ensures proper lifecycle management (setup before yield, teardown after)
                raise SemanticError("Your resource function is returning an integration instead of yielding one.") from None
            else:
                raise SemanticError("You must pass a IntegrationCoupling derived object.") from None

        # Step 4: Validate the extracted resource type and register the source
        if resource_type is not None:

            # Final validation: ensure the resource type inherits from IntegrationCoupling
            if not issubclass(resource_type, IntegrationCoupling):
                raise SemanticError("The 'integration' decorator can only be used on resources that inherit from the 'IntegrationCoupling'.") from None

            # Create and register the IntegrationSource with the injection registry
            isource = IntegrationSource(source_function, resource_type, constraints)
            injection_registry.register_integration_source(isource)
        else:
            errmsg_lines = [
                "Unable to determine the resource type of the function which the 'integration' decorator was applied too.",
                "FUNCTION: {}".format(signature)
            ]
            errmsg = os.linesep.join(errmsg_lines)
            raise SemanticError(errmsg) from None

        return source_function
    return decorator


def resource_factory(*, query_function: Optional[Callable]=None, constraints: Optional[Dict]=None) -> Callable[[Callable], Callable]:
    """
        Decorator factory for registering general resource factory functions.

        The `@resource_factory` decorator is used to declare a function as the source
        of a general resource. The decorated function can be either a generator that
        yields a resource or a function that directly returns a resource.

        :param query_function: Optional callable used to query or filter resource
            instances during injection resolution.
        :param constraints: Optional dictionary of key-value pairs used to conditionally
            filter resource creation based on runtime constraints.

        :returns: A decorator function that registers the source function with the
            InjectionRegistry and returns the original function unchanged.

        :raises SemanticError: When the decorated function lacks a return type annotation.
        :raises SemanticError: When the resource type cannot be determined from the annotation.

        .. rubric:: Example

        .. code-block:: python

            from typing import Generator, AsyncGenerator
            from ccai.testbase.declaration import resource_factory

            class DatabaseConnection:
                pass

            # Generator-style resource factory
            @resource_factory()
            def database_connection() -> Generator[DatabaseConnection, None, None]:
                conn = DatabaseConnection()
                yield conn
                conn.close()

            # Async generator-style resource factory
            @resource_factory()
            async def async_database_connection() -> AsyncGenerator[DatabaseConnection, None]:
                conn = await DatabaseConnection.connect()
                yield conn
                await conn.close()

            # Direct return style
            @resource_factory()
            def simple_resource() -> MyResource:
                return MyResource()

            # With query function and constraints
            @resource_factory(query_function=my_query, constraints={"env": "test"})
            def filtered_resource() -> Generator[FilteredResource, None, None]:
                yield FilteredResource()
    """
    def decorator(source_function: Callable) -> Callable:
        nonlocal constraints

        # =====================================================================
        # TYPE EXTRACTION LOGIC FOR RESOURCE FACTORY
        # =====================================================================
        # Resource factories can be either:
        # - Generator functions that yield a resource (with setup/teardown)
        # - AsyncGenerator functions that yield a resource (async setup/teardown)
        # - Regular functions that directly return a resource (no lifecycle)
        #
        # The type extraction process:
        # 1. Inspect the function signature to get the return type annotation
        # 2. Determine if the annotation is a Generator, AsyncGenerator, or direct type
        # 3. For Generators: extract from Generator[YieldType, SendType, ReturnType]
        # 4. For AsyncGenerators: extract from AsyncGenerator[YieldType, SendType]
        # 5. For direct types: use the annotation as-is
        # =====================================================================

        signature = inspect.signature(source_function)
        resource_context = signature.return_annotation

        resource_type = None

        # Step 1: Verify the function has a return type annotation
        if resource_context == inspect._empty:
            errmsg = "Parameters factories or 'resource' functions must have an annotated return type."
            raise SemanticError(errmsg) from None
        # Step 2: Check if the return type is a Generator or AsyncGenerator
        # Use hasattr check because not all types have _name attribute
        elif hasattr(resource_context, "_name") and resource_context._name in GENERATOR_TYPE_NAMES:
            # Step 3: Extract type arguments from Generator[YieldType, SendType, ReturnType]
            # or AsyncGenerator[YieldType, SendType]
            type_args = resource_context.__args__
            ra_yield_type = type_args[0]

            # Prefer the yield type as the resource type (standard pattern)
            if ra_yield_type is not NoneType:
                resource_type = ra_yield_type
            elif len(type_args) >= 3 and type_args[2] is not NoneType:
                # Fall back to return type if yield type is None (Generator only)
                resource_type = type_args[2]
        elif issubclass(resource_context, IntegrationCoupling):
            # IntegrationCoupling subclasses are valid resource types
            # This allows resource_factory to wrap integration types if needed
            resource_type = resource_context
        else:
            # Step 4: For non-Generator types, use the annotation directly
            # This supports simple factory functions that return resources directly
            resource_type = resource_context
        
        # Register the resource source with the injection registry
        if resource_type is not None:

            # Create ResourceSource with optional query_function for filtering
            sref = ResourceSource(source_function, query_function, resource_type, constraints)
            injection_registry.register_resource_source(sref)
        else:
            errmsg_lines = [
                "Unable to determine the resource type of the function which the 'resource' decorator was applied too.",
                "FUNCTION: {}".format(signature)
            ]
            errmsg = os.linesep.join(errmsg_lines)
            raise SemanticError(errmsg) from None

        return source_function
    return decorator


def configuration_factory(*, query_function: Optional[Callable]=None, constraints: Optional[Dict]=None) -> Callable[[Callable], Callable]:
    """
        Decorator factory for registering configuration coupling factory functions.

        The `@configuration_factory` decorator is used to declare a function as the source
        of a configuration resource. The decorated function must be a generator that yields
        a ConfigurationCoupling subclass instance.

        :param query_function: Optional callable used to query or filter configuration
            instances during injection resolution.
        :param constraints: Optional dictionary of key-value pairs used to conditionally
            filter resource creation based on runtime constraints.

        :returns: A decorator function that registers the source function with the
            InjectionRegistry and returns the original function unchanged.

        :raises SemanticError: When the decorated function lacks a return type annotation.
        :raises SemanticError: When the return type does not inherit from ConfigurationCoupling.
        :raises SemanticError: When the resource type cannot be determined from the annotation.

        .. rubric:: Example

        .. code-block:: python

            from typing import Generator, AsyncGenerator
            from ccai.testbase.declaration import configuration_factory
            from ccai.testbase.coupling import ConfigurationCoupling

            class TestConfiguration(ConfigurationCoupling):
                def __init__(self, settings: dict):
                    self.settings = settings

            @configuration_factory()
            def test_config() -> Generator[TestConfiguration, None, None]:
                config = TestConfiguration({"timeout": 30})
                yield config

            # Async generator example
            @configuration_factory()
            async def async_test_config() -> AsyncGenerator[TestConfiguration, None]:
                config = await TestConfiguration.load({"timeout": 30})
                yield config

            # With query function
            @configuration_factory(query_function=config_query)
            def queried_config() -> Generator[TestConfiguration, None, None]:
                yield TestConfiguration({"timeout": 60})
    """
    def decorator(source_function: Callable) -> Callable:
        nonlocal constraints

        # =====================================================================
        # TYPE EXTRACTION LOGIC FOR CONFIGURATION FACTORY
        # =====================================================================
        # Configuration factories must be generator functions that yield a
        # ConfigurationCoupling subclass. The type extraction process:
        #
        # 1. Inspect the function signature to get the return type annotation
        # 2. Check if the annotation is a Generator or AsyncGenerator type (preferred for configs)
        # 3. Extract the resource type from the Generator's type arguments:
        #    - Generator[YieldType, SendType, ReturnType]
        #    - AsyncGenerator[YieldType, SendType]
        # 4. Validate that the extracted type inherits from ConfigurationCoupling
        # =====================================================================

        signature = inspect.signature(source_function)
        scope_context = signature.return_annotation

        resource_type = None

        # Step 1: Verify the function has a return type annotation
        if scope_context == inspect._empty:
            errmsg = "Parameters factories or 'scope' functions must have an annotated return type."
            raise SemanticError(errmsg) from None
        # Step 2: Check if the return type is a Generator or AsyncGenerator
        elif hasattr(scope_context, "_name") and scope_context._name in GENERATOR_TYPE_NAMES:
            # Step 3: Extract type arguments from Generator[YieldType, SendType, ReturnType]
            # or AsyncGenerator[YieldType, SendType]
            type_args = scope_context.__args__
            ra_yield_type = type_args[0]

            # Prefer the yield type as the resource type (standard pattern)
            if ra_yield_type is not NoneType:
                resource_type = ra_yield_type
            elif len(type_args) >= 3 and type_args[2] is not NoneType:
                # Fall back to return type if yield type is None (Generator only)
                resource_type = type_args[2]
        elif issubclass(scope_context, ConfigurationCoupling):
            # Direct ConfigurationCoupling subclass is also valid
            resource_type = scope_context
        else:
            raise SemanticError("You must pass a ConfigurationCoupling derived object.") from None
        
        # Step 4: Validate the extracted resource type and register the source
        if resource_type is not None:

            # Final validation: ensure the resource type inherits from ConfigurationCoupling
            if not issubclass(resource_type, ConfigurationCoupling):
                raise SemanticError("The 'configuration' decorator can only be used on resources that inherit from the 'scopecoupling'.") from None

            # Create and register the ConfigurationSource with optional query_function
            csource = ConfigurationSource(source_function, query_function, resource_type, constraints)
            injection_registry.register_configuration_source(csource)
        else:
            errmsg_lines = [
                "Unable to determine the resource type of the function which the 'configuration' decorator was applied too.",
                "FUNCTION: {}".format(signature)
            ]
            errmsg = os.linesep.join(errmsg_lines)
            raise SemanticError(errmsg) from None

        return source_function
    return decorator


def validator_factory(*, constraints: Optional[Dict]=None) -> Callable[[Callable], Callable]:
    """
        Decorator factory for registering validator coupling factory functions.

        The `@validator_factory` decorator is used to declare a function as the source
        of a validator resource. The decorated function must return a ValidatorCoupling
        subclass instance directly (not via a generator).

        :param constraints: Optional dictionary of key-value pairs used to conditionally
            filter validator creation based on runtime constraints.

        :returns: A decorator function that registers the source function with the
            InjectionRegistry and returns the original function unchanged.

        :raises SemanticError: When the decorated function lacks a return type annotation.
        :raises SemanticError: When the return type does not inherit from ValidatorCoupling.

        .. rubric:: Example

        .. code-block:: python

            from ccai.testbase.declaration import validator_factory
            from ccai.testbase.coupling import ValidatorCoupling

            class ResponseValidator(ValidatorCoupling):
                def validate(self, response):
                    assert response.status_code == 200

            @validator_factory()
            def response_validator() -> ResponseValidator:
                return ResponseValidator()

            # With constraints
            @validator_factory(constraints={"strict": True})
            def strict_validator() -> StrictValidator:
                return StrictValidator()
    """
    def decorator(source_function: Callable) -> Callable:
        nonlocal constraints

        # =====================================================================
        # TYPE EXTRACTION LOGIC FOR VALIDATOR FACTORY
        # =====================================================================
        # Validator factories are simpler than other factories:
        # - They return ValidatorCoupling subclasses directly (not generators)
        # - No lifecycle management needed (validators are stateless)
        #
        # The type extraction process:
        # 1. Inspect the function signature to get the return type annotation
        # 2. Verify the annotation is a ValidatorCoupling subclass
        # =====================================================================

        signature = inspect.signature(source_function)
        resource_context = signature.return_annotation

        resource_type = None

        # Step 1: Verify the function has a return type annotation
        if resource_context == inspect._empty:
            errmsg = f"Validator factories must have an annotated return type. resource_context={resource_context}"
            raise SemanticError(errmsg) from None
        # Step 2: Verify the return type is a ValidatorCoupling subclass
        elif issubclass(resource_context, ValidatorCoupling):
            # Direct ValidatorCoupling subclass - use as resource type
            resource_type = resource_context
        else:
            errmsg = f"Validator factory functions must have a return type that is subclassed from 'ValidatorBase'. resource_context={resource_context}"
            raise SemanticError(errmsg) from None
        
        # Create and register the ValidatorSource with the injection registry
        sref = ValidatorSource(source_function, resource_type, constraints)
        injection_registry.register_validator_source(sref)
        
        return source_function
    return decorator