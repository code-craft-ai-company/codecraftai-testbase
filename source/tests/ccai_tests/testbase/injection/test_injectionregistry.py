import unittest

from ccai.testbase.injection.injectionregistry import InjectionRegistry
from ccai.testbase.origins.resourceorigin import ResourceOrigin
from ccai.testbase.resourcelifespan import ResourceLifespan

from ccai.testbase.sources.integrationsource import IntegrationSource
from ccai.testbase.sources.resourcesource import ResourceSource
from ccai.testbase.sources.configurationsource import ConfigurationSource
from ccai.testbase.sources.validatorsource import ValidatorSource

from ccai.testbase.coupling.integrationcoupling import IntegrationCoupling
from ccai.testbase.coupling.configurationcoupling import ConfigurationCoupling


# Test coupling classes for fixtures
class TestIntegrationCoupling(IntegrationCoupling):
    """Test integration coupling for unit tests."""
    integration_root = "test"
    integration_section = "unit"
    integration_leaf = "mock"
    integration_class = "TestIntegrationCoupling"


class TestConfigurationCoupling(ConfigurationCoupling):
    """Test configuration coupling for unit tests."""
    pass


# Test resource type for fixtures
class TestResource:
    """Test resource type for unit tests."""
    pass


# Test validator type for fixtures
class TestValidator:
    """Test validator type for unit tests."""
    pass


# Factory functions for test fixtures
def integration_factory() -> TestIntegrationCoupling:
    return TestIntegrationCoupling()


def resource_factory() -> TestResource:
    return TestResource()


def configuration_factory() -> TestConfigurationCoupling:
    return TestConfigurationCoupling()


def validator_factory() -> TestValidator:
    return TestValidator()


def another_integration_factory() -> TestIntegrationCoupling:
    return TestIntegrationCoupling()


def another_resource_factory() -> TestResource:
    return TestResource()


class InjectionRegistryTests(unittest.TestCase):

    def setUp(self):
        InjectionRegistry._instance = None
        InjectionRegistry._initialized = False
        self.registry = InjectionRegistry()

    def test_add_implied_session_resource(self):
        self.registry.add_implied_session_resource('myres')
        scope = self.registry.lookup_resource_scope('<session>')
        self.assertIn('myres', scope.parameter_originations)
        origin = scope.parameter_originations['myres']
        self.assertEqual(origin.originating_scope, '<session>')
        self.assertTrue(origin.implied)

    def test_rename_resource_origins_from_main(self):
        origin = ResourceOrigin('__main__#func', 'id', ResourceLifespan.Test)
        self.registry.register_resource_origin('id', origin)
        self.registry.rename_resource_origins_from_main('pkg.mod')

        self.assertEqual(origin.originating_scope, 'pkg.mod#func')
        scope = self.registry.lookup_resource_scope('pkg.mod')
        self.assertIsNotNone(scope)
        self.assertIn('func', scope.children)
        self.assertIn('id', scope.children['func'].parameter_originations)
        self.assertIs(scope.children['func'].parameter_originations['id'], origin)
        self.assertIsNone(self.registry.lookup_resource_scope('__main'))


class InjectionRegistrySourceRegistrationTests(unittest.TestCase):
    """
    Tests for InjectionRegistry source registration functionality.
    
    Requirements covered:
    - 2.1: IntegrationSource registration in integration source table
    - 2.2: ResourceSource registration in resource source table
    - 2.3: ConfigurationSource registration in configuration source table
    - 2.4: ValidatorSource registration in validator source table
    - 2.5: Duplicate registration prevention (retains first registration)
    """

    def setUp(self):
        InjectionRegistry._instance = None
        InjectionRegistry._initialized = False
        self.registry = InjectionRegistry()

    # Requirement 2.1: IntegrationSource registration
    def test_register_integration_source_stores_in_integration_table(self):
        """WHEN an IntegrationSource is registered, THE InjectionRegistry SHALL store it in the integration source table keyed by source function."""
        source = IntegrationSource(integration_factory, TestIntegrationCoupling, {})
        
        self.registry.register_integration_source(source)
        
        self.assertIn(integration_factory, self.registry._integration_source)
        self.assertIs(self.registry._integration_source[integration_factory], source)

    # Requirement 2.2: ResourceSource registration
    def test_register_resource_source_stores_in_resource_table(self):
        """WHEN a ResourceSource is registered, THE InjectionRegistry SHALL store it in the resource source table keyed by source function."""
        source = ResourceSource(resource_factory, None, TestResource, {})
        
        self.registry.register_resource_source(source)
        
        self.assertIn(resource_factory, self.registry._resource_source)
        self.assertIs(self.registry._resource_source[resource_factory], source)

    # Requirement 2.3: ConfigurationSource registration
    def test_register_configuration_source_stores_in_configuration_table(self):
        """WHEN a ConfigurationSource is registered, THE InjectionRegistry SHALL store it in the configuration source table keyed by source function."""
        source = ConfigurationSource(configuration_factory, None, TestConfigurationCoupling, {})
        
        self.registry.register_configuration_source(source)
        
        self.assertIn(configuration_factory, self.registry._configuration_source)
        self.assertIs(self.registry._configuration_source[configuration_factory], source)

    # Requirement 2.4: ValidatorSource registration
    def test_register_validator_source_stores_in_validator_table(self):
        """WHEN a ValidatorSource is registered, THE InjectionRegistry SHALL store it in the validator source table keyed by source function."""
        source = ValidatorSource(validator_factory, TestValidator, {})
        
        self.registry.register_validator_source(source)
        
        self.assertIn(validator_factory, self.registry._validator_source)
        self.assertIs(self.registry._validator_source[validator_factory], source)

    # Requirement 2.5: Duplicate registration prevention
    def test_register_integration_source_duplicate_retains_first(self):
        """WHEN a source with the same source function is registered multiple times, THE InjectionRegistry SHALL retain only the first registration."""
        first_source = IntegrationSource(integration_factory, TestIntegrationCoupling, {"first": True})
        second_source = IntegrationSource(integration_factory, TestIntegrationCoupling, {"second": True})
        
        self.registry.register_integration_source(first_source)
        self.registry.register_integration_source(second_source)
        
        self.assertIs(self.registry._integration_source[integration_factory], first_source)
        self.assertEqual(self.registry._integration_source[integration_factory].constraints, {"first": True})

    def test_register_resource_source_duplicate_retains_first(self):
        """WHEN a source with the same source function is registered multiple times, THE InjectionRegistry SHALL retain only the first registration."""
        first_source = ResourceSource(resource_factory, None, TestResource, {"first": True})
        second_source = ResourceSource(resource_factory, None, TestResource, {"second": True})
        
        self.registry.register_resource_source(first_source)
        self.registry.register_resource_source(second_source)
        
        self.assertIs(self.registry._resource_source[resource_factory], first_source)
        self.assertEqual(self.registry._resource_source[resource_factory].constraints, {"first": True})

    def test_register_configuration_source_duplicate_retains_first(self):
        """WHEN a source with the same source function is registered multiple times, THE InjectionRegistry SHALL retain only the first registration."""
        first_source = ConfigurationSource(configuration_factory, None, TestConfigurationCoupling, {"first": True})
        second_source = ConfigurationSource(configuration_factory, None, TestConfigurationCoupling, {"second": True})
        
        self.registry.register_configuration_source(first_source)
        self.registry.register_configuration_source(second_source)
        
        self.assertIs(self.registry._configuration_source[configuration_factory], first_source)
        self.assertEqual(self.registry._configuration_source[configuration_factory].constraints, {"first": True})

    def test_register_validator_source_duplicate_retains_first(self):
        """WHEN a source with the same source function is registered multiple times, THE InjectionRegistry SHALL retain only the first registration."""
        first_source = ValidatorSource(validator_factory, TestValidator, {"first": True})
        second_source = ValidatorSource(validator_factory, TestValidator, {"second": True})
        
        self.registry.register_validator_source(first_source)
        self.registry.register_validator_source(second_source)
        
        self.assertIs(self.registry._validator_source[validator_factory], first_source)
        self.assertEqual(self.registry._validator_source[validator_factory].constraints, {"first": True})


class InjectionRegistrySourceLookupTests(unittest.TestCase):
    """
    Tests for InjectionRegistry source lookup functionality.
    
    Requirements covered:
    - 3.1: Resource source lookup searches integration, configuration, resource tables in order
    - 3.2: Returns corresponding source object when found
    - 3.3: Returns None when source not found
    - 3.4: Validator source lookup searches only validator source table
    - 3.5: Returns ValidatorSource when found
    - 3.6: Returns None when validator source not found
    """

    def setUp(self):
        InjectionRegistry._instance = None
        InjectionRegistry._initialized = False
        self.registry = InjectionRegistry()

    # Requirement 3.1 & 3.2: Resource source lookup order and return
    def test_lookup_resource_source_finds_integration_source(self):
        """WHEN looking up a resource source, THE InjectionRegistry SHALL search integration table first and return the source."""
        source = IntegrationSource(integration_factory, TestIntegrationCoupling, {})
        self.registry.register_integration_source(source)
        
        result = self.registry.lookup_resource_source(integration_factory)
        
        self.assertIs(result, source)

    def test_lookup_resource_source_finds_configuration_source(self):
        """WHEN looking up a resource source, THE InjectionRegistry SHALL search configuration table and return the source."""
        source = ConfigurationSource(configuration_factory, None, TestConfigurationCoupling, {})
        self.registry.register_configuration_source(source)
        
        result = self.registry.lookup_resource_source(configuration_factory)
        
        self.assertIs(result, source)

    def test_lookup_resource_source_finds_resource_source(self):
        """WHEN looking up a resource source, THE InjectionRegistry SHALL search resource table and return the source."""
        source = ResourceSource(resource_factory, None, TestResource, {})
        self.registry.register_resource_source(source)
        
        result = self.registry.lookup_resource_source(resource_factory)
        
        self.assertIs(result, source)

    def test_lookup_resource_source_searches_integration_before_configuration(self):
        """WHEN looking up a resource source, THE InjectionRegistry SHALL search integration table before configuration table."""
        # Register same function in both tables (simulating edge case)
        int_source = IntegrationSource(integration_factory, TestIntegrationCoupling, {"type": "integration"})
        self.registry.register_integration_source(int_source)
        
        # Manually add to configuration table to test priority
        config_source = ConfigurationSource(integration_factory, None, TestConfigurationCoupling, {"type": "configuration"})
        self.registry._configuration_source[integration_factory] = config_source
        
        result = self.registry.lookup_resource_source(integration_factory)
        
        # Should return integration source (searched first)
        self.assertIs(result, int_source)
        self.assertEqual(result.constraints, {"type": "integration"})

    def test_lookup_resource_source_searches_configuration_before_resource(self):
        """WHEN looking up a resource source, THE InjectionRegistry SHALL search configuration table before resource table."""
        # Register same function in both tables (simulating edge case)
        config_source = ConfigurationSource(configuration_factory, None, TestConfigurationCoupling, {"type": "configuration"})
        self.registry.register_configuration_source(config_source)
        
        # Manually add to resource table to test priority
        res_source = ResourceSource(configuration_factory, None, TestResource, {"type": "resource"})
        self.registry._resource_source[configuration_factory] = res_source
        
        result = self.registry.lookup_resource_source(configuration_factory)
        
        # Should return configuration source (searched before resource)
        self.assertIs(result, config_source)
        self.assertEqual(result.constraints, {"type": "configuration"})

    # Requirement 3.3: Returns None when not found
    def test_lookup_resource_source_returns_none_when_not_found(self):
        """WHEN the source function is not found in any table, THE System SHALL return None."""
        result = self.registry.lookup_resource_source(resource_factory)
        
        self.assertIsNone(result)

    # Requirement 3.4 & 3.5: Validator source lookup
    def test_lookup_validator_source_finds_validator_source(self):
        """WHEN looking up a validator source, THE InjectionRegistry SHALL search only the validator source table and return the ValidatorSource."""
        source = ValidatorSource(validator_factory, TestValidator, {})
        self.registry.register_validator_source(source)
        
        result = self.registry.lookup_validator_source(validator_factory)
        
        self.assertIs(result, source)

    def test_lookup_validator_source_only_searches_validator_table(self):
        """WHEN looking up a validator source, THE InjectionRegistry SHALL search only the validator source table."""
        # Register in other tables but not validator table
        int_source = IntegrationSource(integration_factory, TestIntegrationCoupling, {})
        self.registry.register_integration_source(int_source)
        
        res_source = ResourceSource(resource_factory, None, TestResource, {})
        self.registry.register_resource_source(res_source)
        
        # Lookup should not find these in validator lookup
        result_int = self.registry.lookup_validator_source(integration_factory)
        result_res = self.registry.lookup_validator_source(resource_factory)
        
        self.assertIsNone(result_int)
        self.assertIsNone(result_res)

    # Requirement 3.6: Returns None when validator not found
    def test_lookup_validator_source_returns_none_when_not_found(self):
        """WHEN the validator source function is not found, THE System SHALL return None."""
        result = self.registry.lookup_validator_source(validator_factory)
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
