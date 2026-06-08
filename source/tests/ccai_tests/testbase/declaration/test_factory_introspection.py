"""
    Unit tests for factory function introspection utilities.
    
    Tests the API for listing registered factories and querying factory metadata.
"""

import typing
import unittest

from ccai.testbase.coupling.integrationcoupling import IntegrationCoupling
from ccai.testbase.coupling.configurationcoupling import ConfigurationCoupling
from ccai.testbase.coupling.validatorcoupling import ValidatorCoupling

from ccai.testbase.declaration import registrations
from ccai.testbase.injection import injectionregistry
from ccai.testbase.injection.injectionscope import InjectionScope
from ccai.testbase.injection.introspection import (
    FactoryType,
    FactoryMetadata,
    FactoryListResult
)


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


class ListFactoriesTests(unittest.TestCase):
    """Tests for the list_factories API."""

    def setUp(self):
        reset_registry()

    def test_list_factories_empty_registry(self):
        """Test listing factories when registry is empty."""
        inj = injectionregistry.injection_registry
        result = inj.list_factories()
        
        self.assertIsInstance(result, FactoryListResult)
        self.assertEqual(result.total_count, 0)
        self.assertEqual(len(result.integration_factories), 0)
        self.assertEqual(len(result.resource_factories), 0)
        self.assertEqual(len(result.configuration_factories), 0)
        self.assertEqual(len(result.validator_factories), 0)

    def test_list_factories_with_integration(self):
        """Test listing factories with registered integration factory."""
        class TestIntegration(IntegrationCoupling):
            _name = None

        @registrations.integration_factory()
        def make_integration() -> typing.Generator[TestIntegration, None, None]:
            if False:
                yield TestIntegration()

        inj = injectionregistry.injection_registry
        result = inj.list_factories()
        
        self.assertEqual(result.total_count, 1)
        self.assertEqual(len(result.integration_factories), 1)
        self.assertEqual(result.integration_factories[0].factory_type, FactoryType.INTEGRATION)
        self.assertEqual(result.integration_factories[0].function_name, "make_integration")
        self.assertEqual(result.integration_factories[0].resource_type, TestIntegration)

    def test_list_factories_with_resource(self):
        """Test listing factories with registered resource factory."""
        @registrations.resource_factory()
        def provide_resource() -> int:
            return 42

        inj = injectionregistry.injection_registry
        result = inj.list_factories()
        
        self.assertEqual(result.total_count, 1)
        self.assertEqual(len(result.resource_factories), 1)
        self.assertEqual(result.resource_factories[0].factory_type, FactoryType.RESOURCE)
        self.assertEqual(result.resource_factories[0].function_name, "provide_resource")

    def test_list_factories_with_configuration(self):
        """Test listing factories with registered configuration factory."""
        class TestConfig(ConfigurationCoupling):
            pass

        @registrations.configuration_factory()
        def make_config() -> typing.Generator[TestConfig, None, None]:
            if False:
                yield TestConfig()

        inj = injectionregistry.injection_registry
        result = inj.list_factories()
        
        self.assertEqual(result.total_count, 1)
        self.assertEqual(len(result.configuration_factories), 1)
        self.assertEqual(result.configuration_factories[0].factory_type, FactoryType.CONFIGURATION)

    def test_list_factories_with_validator(self):
        """Test listing factories with registered validator factory."""
        class TestValidator(ValidatorCoupling):
            pass

        @registrations.validator_factory()
        def make_validator() -> TestValidator:
            return TestValidator()

        inj = injectionregistry.injection_registry
        result = inj.list_factories()
        
        self.assertEqual(result.total_count, 1)
        self.assertEqual(len(result.validator_factories), 1)
        self.assertEqual(result.validator_factories[0].factory_type, FactoryType.VALIDATOR)

    def test_list_factories_filter_by_type(self):
        """Test filtering factories by type."""
        class TestIntegration(IntegrationCoupling):
            _name = None

        @registrations.integration_factory()
        def make_integration() -> typing.Generator[TestIntegration, None, None]:
            if False:
                yield TestIntegration()

        @registrations.resource_factory()
        def provide_resource() -> str:
            return "test"

        inj = injectionregistry.injection_registry
        
        # Filter for integration only
        result = inj.list_factories(FactoryType.INTEGRATION)
        self.assertEqual(result.total_count, 1)
        self.assertEqual(len(result.integration_factories), 1)
        self.assertEqual(len(result.resource_factories), 0)
        
        # Filter for resource only
        result = inj.list_factories(FactoryType.RESOURCE)
        self.assertEqual(result.total_count, 1)
        self.assertEqual(len(result.resource_factories), 1)
        self.assertEqual(len(result.integration_factories), 0)

    def test_list_factories_multiple_types(self):
        """Test listing factories with multiple types registered."""
        class TestIntegration(IntegrationCoupling):
            _name = None

        class TestConfig(ConfigurationCoupling):
            pass

        class TestValidator(ValidatorCoupling):
            pass

        @registrations.integration_factory()
        def make_integration() -> typing.Generator[TestIntegration, None, None]:
            if False:
                yield TestIntegration()

        @registrations.resource_factory()
        def provide_resource() -> int:
            return 1

        @registrations.configuration_factory()
        def make_config() -> typing.Generator[TestConfig, None, None]:
            if False:
                yield TestConfig()

        @registrations.validator_factory()
        def make_validator() -> TestValidator:
            return TestValidator()

        inj = injectionregistry.injection_registry
        result = inj.list_factories()
        
        self.assertEqual(result.total_count, 4)
        self.assertEqual(len(result.integration_factories), 1)
        self.assertEqual(len(result.resource_factories), 1)
        self.assertEqual(len(result.configuration_factories), 1)
        self.assertEqual(len(result.validator_factories), 1)

    def test_factory_list_result_counts_by_type(self):
        """Test the counts_by_type property of FactoryListResult."""
        @registrations.resource_factory()
        def resource1() -> int:
            return 1

        @registrations.resource_factory()
        def resource2() -> str:
            return "test"

        inj = injectionregistry.injection_registry
        result = inj.list_factories()
        
        counts = result.counts_by_type
        self.assertEqual(counts[FactoryType.RESOURCE], 2)
        self.assertEqual(counts[FactoryType.INTEGRATION], 0)

    def test_factory_list_result_all_factories(self):
        """Test the all_factories method of FactoryListResult."""
        class TestIntegration(IntegrationCoupling):
            _name = None

        @registrations.integration_factory()
        def make_integration() -> typing.Generator[TestIntegration, None, None]:
            if False:
                yield TestIntegration()

        @registrations.resource_factory()
        def provide_resource() -> int:
            return 1

        inj = injectionregistry.injection_registry
        result = inj.list_factories()
        
        all_factories = result.all_factories()
        self.assertEqual(len(all_factories), 2)


class GetFactoryMetadataTests(unittest.TestCase):
    """Tests for the get_factory_metadata API."""

    def setUp(self):
        reset_registry()

    def test_get_metadata_unregistered_function(self):
        """Test getting metadata for an unregistered function."""
        def not_registered():
            pass

        inj = injectionregistry.injection_registry
        metadata = inj.get_factory_metadata(not_registered)
        
        self.assertIsNone(metadata)

    def test_get_metadata_integration_factory(self):
        """Test getting metadata for an integration factory."""
        class TestIntegration(IntegrationCoupling):
            _name = None

        @registrations.integration_factory()
        def make_integration() -> typing.Generator[TestIntegration, None, None]:
            """Creates a test integration."""
            if False:
                yield TestIntegration()

        inj = injectionregistry.injection_registry
        metadata = inj.get_factory_metadata(make_integration)
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.factory_type, FactoryType.INTEGRATION)
        self.assertEqual(metadata.function_name, "make_integration")
        self.assertEqual(metadata.resource_type, TestIntegration)
        self.assertEqual(metadata.docstring, "Creates a test integration.")

    def test_get_metadata_resource_factory(self):
        """Test getting metadata for a resource factory."""
        @registrations.resource_factory()
        def provide_resource() -> int:
            """Provides an integer resource."""
            return 42

        inj = injectionregistry.injection_registry
        metadata = inj.get_factory_metadata(provide_resource)
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.factory_type, FactoryType.RESOURCE)
        self.assertEqual(metadata.function_name, "provide_resource")
        self.assertIsNotNone(metadata.signature)

    def test_get_metadata_with_constraints(self):
        """Test getting metadata for a factory with constraints."""
        @registrations.resource_factory(constraints={"platform": "linux", "version": "1.0"})
        def constrained_resource() -> str:
            return "test"

        inj = injectionregistry.injection_registry
        metadata = inj.get_factory_metadata(constrained_resource)
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.constraints, {"platform": "linux", "version": "1.0"})

    def test_get_metadata_source_id(self):
        """Test that source_id is correctly populated."""
        @registrations.resource_factory()
        def my_resource() -> int:
            return 1

        inj = injectionregistry.injection_registry
        metadata = inj.get_factory_metadata(my_resource)
        
        self.assertIsNotNone(metadata)
        self.assertIn("my_resource", metadata.source_id)
        self.assertIn(__name__, metadata.source_id)


class FindFactoriesByResourceTypeTests(unittest.TestCase):
    """Tests for the find_factories_by_resource_type API."""

    def setUp(self):
        reset_registry()

    def test_find_by_type_no_match(self):
        """Test finding factories when no match exists."""
        @registrations.resource_factory()
        def provide_int() -> int:
            return 1

        inj = injectionregistry.injection_registry
        results = inj.find_factories_by_resource_type(str)
        
        self.assertEqual(len(results), 0)

    def test_find_by_type_single_match(self):
        """Test finding factories with a single match."""
        class CustomResource:
            pass

        @registrations.resource_factory()
        def provide_custom() -> CustomResource:
            return CustomResource()

        inj = injectionregistry.injection_registry
        results = inj.find_factories_by_resource_type(CustomResource)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].resource_type, CustomResource)

    def test_find_by_type_multiple_matches(self):
        """Test finding factories with multiple matches for same type."""
        class SharedResource:
            pass

        @registrations.resource_factory()
        def provide_shared1() -> SharedResource:
            return SharedResource()

        @registrations.resource_factory()
        def provide_shared2() -> SharedResource:
            return SharedResource()

        inj = injectionregistry.injection_registry
        results = inj.find_factories_by_resource_type(SharedResource)
        
        self.assertEqual(len(results), 2)


class FindFactoriesByModuleTests(unittest.TestCase):
    """Tests for the find_factories_by_module API."""

    def setUp(self):
        reset_registry()

    def test_find_by_module_current(self):
        """Test finding factories in the current module."""
        @registrations.resource_factory()
        def module_resource() -> int:
            return 1

        inj = injectionregistry.injection_registry
        results = inj.find_factories_by_module(__name__)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].module_name, __name__)

    def test_find_by_module_no_match(self):
        """Test finding factories when module doesn't match."""
        @registrations.resource_factory()
        def some_resource() -> int:
            return 1

        inj = injectionregistry.injection_registry
        results = inj.find_factories_by_module("nonexistent.module")
        
        self.assertEqual(len(results), 0)


class FindFactoriesWithConstraintsTests(unittest.TestCase):
    """Tests for the find_factories_with_constraints API."""

    def setUp(self):
        reset_registry()

    def test_find_with_constraints_none(self):
        """Test finding factories when none have constraints."""
        @registrations.resource_factory()
        def unconstrained() -> int:
            return 1

        inj = injectionregistry.injection_registry
        results = inj.find_factories_with_constraints()
        
        self.assertEqual(len(results), 0)

    def test_find_with_any_constraints(self):
        """Test finding all factories with any constraints."""
        @registrations.resource_factory(constraints={"env": "test"})
        def constrained1() -> int:
            return 1

        @registrations.resource_factory(constraints={"platform": "linux"})
        def constrained2() -> str:
            return "test"

        @registrations.resource_factory()
        def unconstrained() -> float:
            return 1.0

        inj = injectionregistry.injection_registry
        results = inj.find_factories_with_constraints()
        
        self.assertEqual(len(results), 2)

    def test_find_with_specific_constraint_key(self):
        """Test finding factories with a specific constraint key."""
        @registrations.resource_factory(constraints={"platform": "linux"})
        def linux_resource() -> int:
            return 1

        @registrations.resource_factory(constraints={"env": "test"})
        def test_resource() -> str:
            return "test"

        inj = injectionregistry.injection_registry
        results = inj.find_factories_with_constraints("platform")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].function_name, "linux_resource")


class FactoryMetadataTests(unittest.TestCase):
    """Tests for the FactoryMetadata dataclass."""

    def setUp(self):
        reset_registry()

    def test_metadata_from_source(self):
        """Test creating FactoryMetadata from a source object."""
        @registrations.resource_factory()
        def test_factory() -> int:
            return 1

        inj = injectionregistry.injection_registry
        source = inj._resource_source[test_factory]
        
        metadata = FactoryMetadata.from_source(FactoryType.RESOURCE, source)
        
        self.assertEqual(metadata.factory_type, FactoryType.RESOURCE)
        self.assertEqual(metadata.source_function, test_factory)
        self.assertEqual(metadata.function_name, "test_factory")
        self.assertIsNotNone(metadata.module_name)
        self.assertIsNotNone(metadata.source_id)


if __name__ == "__main__":
    unittest.main()
