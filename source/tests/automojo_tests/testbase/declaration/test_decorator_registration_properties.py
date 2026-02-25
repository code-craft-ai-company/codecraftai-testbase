"""
    Property-based tests for decorator registration.
    
    These tests verify that arbitrary valid factory functions are correctly registered
    and that constraints are properly associated with sources.
    
    **Validates: Requirements 1.6, 2.6, 3.6, 4.4**
"""

import typing
import unittest

from automojo.testbase.coupling.integrationcoupling import IntegrationCoupling
from automojo.testbase.coupling.configurationcoupling import ConfigurationCoupling
from automojo.testbase.coupling.validatorcoupling import ValidatorCoupling

from automojo.testbase.declaration import registrations
from automojo.testbase.injection import injectionregistry
from automojo.testbase.injection.injectionscope import InjectionScope
from automojo.testbase.sources.integrationsource import IntegrationSource
from automojo.testbase.sources.resourcesource import ResourceSource
from automojo.testbase.sources.configurationsource import ConfigurationSource
from automojo.testbase.sources.validatorsource import ValidatorSource


def reset_registry():
    """Reset the injection registry to a clean state for testing."""
    inj = injectionregistry.injection_registry
    inj._integration_source.clear()
    inj._resource_source.clear()
    inj._configuration_source.clear()
    inj._validator_source.clear()
    inj._unknown_parameters.clear()
    inj._identifier_subscription_table.clear()
    inj._scope_tree_root = InjectionScope()
    inj._referenced_integrations.clear()
    inj._referenced_configurations.clear()
    return inj


class IntegrationFactoryConstraintsPropertyTests(unittest.TestCase):
    """
    Property tests for integration_factory decorator constraint handling.
    
    **Feature: declaration, Property 1: Integration factory constraints association**
    **Validates: Requirements 1.6**
    
    For any valid IntegrationCoupling subclass and any constraints dictionary,
    when decorated with @integration_factory(constraints=...), the constraints
    SHALL be properly associated with the registered IntegrationSource.
    """

    def setUp(self):
        reset_registry()

    def _create_integration_class(self, name: str) -> type:
        """Create a unique IntegrationCoupling subclass for testing."""
        return type(name, (IntegrationCoupling,), {'_name': None})

    def _create_factory_with_constraints(self, integration_class: type, constraints: dict):
        """Create and register a factory function with the given constraints."""
        @registrations.integration_factory(constraints=constraints)
        def factory_func() -> typing.Generator[integration_class, None, None]:
            if False:
                yield integration_class()
        return factory_func

    def test_none_constraints_associated_correctly(self):
        """Verify None constraints are properly stored."""
        IntClass = self._create_integration_class("TestIntegrationNone")
        factory = self._create_factory_with_constraints(IntClass, None)
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(factory)
        
        self.assertIsInstance(source, IntegrationSource)
        self.assertIsNone(source.constraints)

    def test_empty_constraints_associated_correctly(self):
        """Verify empty constraints dict is properly stored."""
        IntClass = self._create_integration_class("TestIntegrationEmpty")
        factory = self._create_factory_with_constraints(IntClass, {})
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(factory)
        
        self.assertIsInstance(source, IntegrationSource)
        self.assertEqual(source.constraints, {})

    def test_single_constraint_associated_correctly(self):
        """Verify single key-value constraint is properly stored."""
        IntClass = self._create_integration_class("TestIntegrationSingle")
        constraints = {"platform": "linux"}
        factory = self._create_factory_with_constraints(IntClass, constraints)
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(factory)
        
        self.assertIsInstance(source, IntegrationSource)
        self.assertEqual(source.constraints, constraints)
        self.assertEqual(source.constraints["platform"], "linux")

    def test_multiple_constraints_associated_correctly(self):
        """Verify multiple constraints are properly stored."""
        IntClass = self._create_integration_class("TestIntegrationMultiple")
        constraints = {
            "platform": "linux",
            "version": "3.10",
            "feature_enabled": True,
            "max_connections": 100
        }
        factory = self._create_factory_with_constraints(IntClass, constraints)
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(factory)
        
        self.assertIsInstance(source, IntegrationSource)
        self.assertEqual(source.constraints, constraints)
        self.assertEqual(len(source.constraints), 4)

    def test_nested_constraints_associated_correctly(self):
        """Verify nested dict constraints are properly stored."""
        IntClass = self._create_integration_class("TestIntegrationNested")
        constraints = {
            "config": {
                "host": "localhost",
                "port": 8080
            },
            "options": ["opt1", "opt2"]
        }
        factory = self._create_factory_with_constraints(IntClass, constraints)
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(factory)
        
        self.assertIsInstance(source, IntegrationSource)
        self.assertEqual(source.constraints, constraints)
        self.assertEqual(source.constraints["config"]["host"], "localhost")


class ResourceFactoryConstraintsPropertyTests(unittest.TestCase):
    """
    Property tests for resource_factory decorator constraint handling.
    
    **Feature: declaration, Property 2: Resource factory constraints association**
    **Validates: Requirements 2.6**
    
    For any valid resource type and any constraints dictionary,
    when decorated with @resource_factory(constraints=...), the constraints
    SHALL be properly associated with the registered ResourceSource.
    """

    def setUp(self):
        reset_registry()

    def test_none_constraints_associated_correctly(self):
        """Verify None constraints are properly stored for resource factory."""
        @registrations.resource_factory(constraints=None)
        def provide_int() -> int:
            return 42
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(provide_int)
        
        self.assertIsInstance(source, ResourceSource)
        self.assertIsNone(source.constraints)

    def test_empty_constraints_associated_correctly(self):
        """Verify empty constraints dict is properly stored for resource factory."""
        @registrations.resource_factory(constraints={})
        def provide_str() -> str:
            return "test"
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(provide_str)
        
        self.assertIsInstance(source, ResourceSource)
        self.assertEqual(source.constraints, {})

    def test_single_constraint_associated_correctly(self):
        """Verify single constraint is properly stored for resource factory."""
        constraints = {"env": "production"}
        
        @registrations.resource_factory(constraints=constraints)
        def provide_float() -> float:
            return 3.14
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(provide_float)
        
        self.assertIsInstance(source, ResourceSource)
        self.assertEqual(source.constraints, constraints)

    def test_multiple_constraints_associated_correctly(self):
        """Verify multiple constraints are properly stored for resource factory."""
        constraints = {
            "env": "staging",
            "region": "us-west-2",
            "debug": False
        }
        
        @registrations.resource_factory(constraints=constraints)
        def provide_list() -> list:
            return [1, 2, 3]
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(provide_list)
        
        self.assertIsInstance(source, ResourceSource)
        self.assertEqual(source.constraints, constraints)
        self.assertEqual(len(source.constraints), 3)

    def test_generator_resource_constraints_associated_correctly(self):
        """Verify constraints work with generator-style resource factories."""
        constraints = {"cleanup": True}
        
        @registrations.resource_factory(constraints=constraints)
        def provide_with_cleanup() -> typing.Generator[dict, None, None]:
            resource = {"data": "test"}
            yield resource
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(provide_with_cleanup)
        
        self.assertIsInstance(source, ResourceSource)
        self.assertEqual(source.constraints, constraints)


class ConfigurationFactoryConstraintsPropertyTests(unittest.TestCase):
    """
    Property tests for configuration_factory decorator constraint handling.
    
    **Feature: declaration, Property 3: Configuration factory constraints association**
    **Validates: Requirements 3.6**
    
    For any valid ConfigurationCoupling subclass and any constraints dictionary,
    when decorated with @configuration_factory(constraints=...), the constraints
    SHALL be properly associated with the registered ConfigurationSource.
    """

    def setUp(self):
        reset_registry()

    def _create_config_class(self, name: str) -> type:
        """Create a unique ConfigurationCoupling subclass for testing."""
        return type(name, (ConfigurationCoupling,), {})

    def _create_factory_with_constraints(self, config_class: type, constraints: dict):
        """Create and register a configuration factory with the given constraints."""
        @registrations.configuration_factory(constraints=constraints)
        def factory_func() -> typing.Generator[config_class, None, None]:
            if False:
                yield config_class()
        return factory_func

    def test_none_constraints_associated_correctly(self):
        """Verify None constraints are properly stored for configuration factory."""
        ConfigClass = self._create_config_class("TestConfigNone")
        factory = self._create_factory_with_constraints(ConfigClass, None)
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(factory)
        
        self.assertIsInstance(source, ConfigurationSource)
        self.assertIsNone(source.constraints)

    def test_empty_constraints_associated_correctly(self):
        """Verify empty constraints dict is properly stored for configuration factory."""
        ConfigClass = self._create_config_class("TestConfigEmpty")
        factory = self._create_factory_with_constraints(ConfigClass, {})
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(factory)
        
        self.assertIsInstance(source, ConfigurationSource)
        self.assertEqual(source.constraints, {})

    def test_single_constraint_associated_correctly(self):
        """Verify single constraint is properly stored for configuration factory."""
        ConfigClass = self._create_config_class("TestConfigSingle")
        constraints = {"database": "postgresql"}
        factory = self._create_factory_with_constraints(ConfigClass, constraints)
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(factory)
        
        self.assertIsInstance(source, ConfigurationSource)
        self.assertEqual(source.constraints, constraints)

    def test_multiple_constraints_associated_correctly(self):
        """Verify multiple constraints are properly stored for configuration factory."""
        ConfigClass = self._create_config_class("TestConfigMultiple")
        constraints = {
            "database": "mysql",
            "cache": "redis",
            "timeout": 30,
            "retry": True
        }
        factory = self._create_factory_with_constraints(ConfigClass, constraints)
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(factory)
        
        self.assertIsInstance(source, ConfigurationSource)
        self.assertEqual(source.constraints, constraints)
        self.assertEqual(len(source.constraints), 4)


class ValidatorFactoryConstraintsPropertyTests(unittest.TestCase):
    """
    Property tests for validator_factory decorator constraint handling.
    
    **Feature: declaration, Property 4: Validator factory constraints association**
    **Validates: Requirements 4.4**
    
    For any valid ValidatorCoupling subclass and any constraints dictionary,
    when decorated with @validator_factory(constraints=...), the constraints
    SHALL be properly associated with the registered ValidatorSource.
    """

    def setUp(self):
        reset_registry()

    def _create_validator_class(self, name: str) -> type:
        """Create a unique ValidatorCoupling subclass for testing."""
        def attach_to_test(self, testscope, suffix):
            self._testscope = testscope
            self._suffix = suffix
        return type(name, (ValidatorCoupling,), {'attach_to_test': attach_to_test})

    def _create_factory_with_constraints(self, validator_class: type, constraints: dict):
        """Create and register a validator factory with the given constraints."""
        @registrations.validator_factory(constraints=constraints)
        def factory_func() -> validator_class:
            return validator_class()
        return factory_func

    def test_none_constraints_associated_correctly(self):
        """Verify None constraints are properly stored for validator factory."""
        ValidatorClass = self._create_validator_class("TestValidatorNone")
        factory = self._create_factory_with_constraints(ValidatorClass, None)
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_validator_source(factory)
        
        self.assertIsInstance(source, ValidatorSource)
        self.assertIsNone(source.constraints)

    def test_empty_constraints_associated_correctly(self):
        """Verify empty constraints dict is properly stored for validator factory."""
        ValidatorClass = self._create_validator_class("TestValidatorEmpty")
        factory = self._create_factory_with_constraints(ValidatorClass, {})
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_validator_source(factory)
        
        self.assertIsInstance(source, ValidatorSource)
        self.assertEqual(source.constraints, {})

    def test_single_constraint_associated_correctly(self):
        """Verify single constraint is properly stored for validator factory."""
        ValidatorClass = self._create_validator_class("TestValidatorSingle")
        constraints = {"strict": True}
        factory = self._create_factory_with_constraints(ValidatorClass, constraints)
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_validator_source(factory)
        
        self.assertIsInstance(source, ValidatorSource)
        self.assertEqual(source.constraints, constraints)

    def test_multiple_constraints_associated_correctly(self):
        """Verify multiple constraints are properly stored for validator factory."""
        ValidatorClass = self._create_validator_class("TestValidatorMultiple")
        constraints = {
            "strict": True,
            "timeout": 60,
            "retry_count": 3,
            "log_failures": True
        }
        factory = self._create_factory_with_constraints(ValidatorClass, constraints)
        
        inj = injectionregistry.injection_registry
        source = inj.lookup_validator_source(factory)
        
        self.assertIsInstance(source, ValidatorSource)
        self.assertEqual(source.constraints, constraints)
        self.assertEqual(len(source.constraints), 4)


class FactoryRegistrationPropertyTests(unittest.TestCase):
    """
    Property tests verifying that arbitrary valid factory functions are correctly registered.
    
    **Feature: declaration, Property 5: Factory function registration correctness**
    **Validates: Requirements 1.6, 2.6, 3.6, 4.4**
    
    For any valid factory function with proper type annotations,
    the decorator SHALL register the function and preserve its original behavior.
    """

    def setUp(self):
        reset_registry()

    def test_integration_factory_preserves_function_identity(self):
        """Verify integration_factory preserves the original function."""
        class TestIntegration(IntegrationCoupling):
            _name = None

        @registrations.integration_factory()
        def original_func() -> typing.Generator[TestIntegration, None, None]:
            if False:
                yield TestIntegration()

        # The decorated function should be the same object
        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(original_func)
        self.assertEqual(source.source_function, original_func)

    def test_resource_factory_preserves_function_identity(self):
        """Verify resource_factory preserves the original function."""
        @registrations.resource_factory()
        def original_func() -> int:
            return 42

        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(original_func)
        self.assertEqual(source.source_function, original_func)

    def test_configuration_factory_preserves_function_identity(self):
        """Verify configuration_factory preserves the original function."""
        class TestConfig(ConfigurationCoupling):
            pass

        @registrations.configuration_factory()
        def original_func() -> typing.Generator[TestConfig, None, None]:
            if False:
                yield TestConfig()

        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(original_func)
        self.assertEqual(source.source_function, original_func)

    def test_validator_factory_preserves_function_identity(self):
        """Verify validator_factory preserves the original function."""
        class TestValidator(ValidatorCoupling):
            def attach_to_test(self, testscope, suffix):
                pass

        @registrations.validator_factory()
        def original_func() -> TestValidator:
            return TestValidator()

        inj = injectionregistry.injection_registry
        source = inj.lookup_validator_source(original_func)
        self.assertEqual(source.source_function, original_func)

    def test_multiple_factories_registered_independently(self):
        """Verify multiple factories can be registered without interference."""
        class Int1(IntegrationCoupling):
            _name = None
        class Int2(IntegrationCoupling):
            _name = None
        class Config1(ConfigurationCoupling):
            pass

        @registrations.integration_factory(constraints={"type": "int1"})
        def int_factory1() -> typing.Generator[Int1, None, None]:
            if False:
                yield Int1()

        @registrations.integration_factory(constraints={"type": "int2"})
        def int_factory2() -> typing.Generator[Int2, None, None]:
            if False:
                yield Int2()

        @registrations.resource_factory(constraints={"type": "resource"})
        def res_factory() -> str:
            return "test"

        @registrations.configuration_factory(constraints={"type": "config"})
        def config_factory() -> typing.Generator[Config1, None, None]:
            if False:
                yield Config1()

        inj = injectionregistry.injection_registry
        
        # Verify each factory is registered with correct constraints
        source1 = inj.lookup_resource_source(int_factory1)
        source2 = inj.lookup_resource_source(int_factory2)
        source3 = inj.lookup_resource_source(res_factory)
        source4 = inj.lookup_resource_source(config_factory)

        self.assertEqual(source1.constraints["type"], "int1")
        self.assertEqual(source2.constraints["type"], "int2")
        self.assertEqual(source3.constraints["type"], "resource")
        self.assertEqual(source4.constraints["type"], "config")

    def test_resource_type_correctly_extracted(self):
        """Verify resource type is correctly extracted from annotations."""
        class CustomResource:
            pass

        @registrations.resource_factory()
        def provide_custom() -> CustomResource:
            return CustomResource()

        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(provide_custom)
        
        self.assertEqual(source.resource_type, CustomResource)


if __name__ == "__main__":
    unittest.main()
