"""
    Integration tests for InjectionRegistry.finalize_startup() flow.
    
    Requirements covered:
    - 7.1: Ensure injection scopes exist for all injection moments
    - 7.2: Mark each scope along the path as relevant
    - 7.3: Prune unreferenced scopes from the scope tree
    - 7.4: Remove non-relevant leaf nodes working backwards toward root
    - 7.5: Resolve resource originations for each injection moment
    - 7.6: Record unknown parameters in unknown_parameters table
    - 7.7: Collect referenced integrations and configurations
    - 9.1: Walk the entire scope tree for collection
    - 9.2: Add IntegrationCoupling subclass to integration table
    - 9.3: Add ConfigurationCoupling subclass to configuration table
    - 9.4: Extract coupling type from generic types containing IntegrationCoupling
    - 9.5: Extract coupling type from generic types containing ConfigurationCoupling
    - 9.6: Skip implied parameter originations when collecting couplings
"""

import unittest
from typing import List

from automojo.testbase.injection.injectionregistry import InjectionRegistry
from automojo.testbase.injection.injectionmoment import InjectionMoment
from automojo.testbase.origins.resourceorigin import ResourceOrigin
from automojo.testbase.resourcelifespan import ResourceLifespan

from automojo.testbase.sources.integrationsource import IntegrationSource
from automojo.testbase.sources.resourcesource import ResourceSource
from automojo.testbase.sources.configurationsource import ConfigurationSource

from automojo.testbase.coupling.integrationcoupling import IntegrationCoupling
from automojo.testbase.coupling.configurationcoupling import ConfigurationCoupling


# Test coupling classes for fixtures
class TestIntegrationCoupling(IntegrationCoupling):
    """Test integration coupling for integration tests."""
    integration_root = "test"
    integration_section = "integration"
    integration_leaf = "mock"
    integration_class = "TestIntegrationCoupling"


class TestConfigurationCoupling(ConfigurationCoupling):
    """Test configuration coupling for integration tests."""
    pass



# Test resource type for fixtures
class TestResource:
    """Test resource type for integration tests."""
    pass


# Factory functions for test fixtures
def integration_factory() -> TestIntegrationCoupling:
    """Factory function that produces an IntegrationCoupling."""
    return TestIntegrationCoupling()


def configuration_factory() -> TestConfigurationCoupling:
    """Factory function that produces a ConfigurationCoupling."""
    return TestConfigurationCoupling()


def resource_factory() -> TestResource:
    """Factory function that produces a TestResource."""
    return TestResource()


def resource_with_dependency(my_integration: TestIntegrationCoupling) -> TestResource:
    """Factory function that depends on an integration resource."""
    return TestResource()


def resource_with_unknown_dependency(unknown_param: str) -> TestResource:
    """Factory function that depends on an unknown parameter."""
    return TestResource()


# Test functions to create injection moments
def test_function_a():
    """Test function for injection moment A."""
    pass


def test_function_b():
    """Test function for injection moment B."""
    pass


def test_function_c():
    """Test function for injection moment C."""
    pass


# Override module names for test functions to simulate different modules
test_function_a.__module__ = "tests.package_a.module_a"
test_function_b.__module__ = "tests.package_a.module_b"
test_function_c.__module__ = "tests.package_b.module_c"



class FinalizeStartupScopeCreationTests(unittest.TestCase):
    """
    Integration tests for finalize_startup scope creation and pruning.
    
    Requirements covered:
    - 7.1: Ensure injection scopes exist for all injection moments
    - 7.2: Mark each scope along the path as relevant
    - 7.3: Prune unreferenced scopes from the scope tree
    - 7.4: Remove non-relevant leaf nodes working backwards toward root
    """

    def setUp(self):
        InjectionRegistry._instance = None
        InjectionRegistry._initialized = False
        self.registry = InjectionRegistry()

    def test_finalize_creates_scopes_for_injection_moments(self):
        """
        WHEN finalize_startup is called, THE System SHALL ensure injection scopes 
        exist for all injection moments.
        Requirements: 7.1
        """
        inj_mom_a = InjectionMoment(test_function_a)
        inj_mom_b = InjectionMoment(test_function_b)
        
        inj_moments = {
            inj_mom_a.name: inj_mom_a,
            inj_mom_b.name: inj_mom_b,
        }
        
        self.registry.finalize_startup(inj_moments)
        
        # Verify scopes were created for both injection moments
        scope_a = self.registry.lookup_resource_scope("tests.package_a.module_a.test_function_a")
        scope_b = self.registry.lookup_resource_scope("tests.package_a.module_b.test_function_b")
        
        self.assertIsNotNone(scope_a)
        self.assertIsNotNone(scope_b)

    def test_finalize_marks_scopes_as_relevant(self):
        """
        WHEN ensuring injection scopes, THE System SHALL mark each scope along 
        the path as relevant.
        Requirements: 7.2
        """
        inj_mom_a = InjectionMoment(test_function_a)
        
        inj_moments = {
            inj_mom_a.name: inj_mom_a,
        }
        
        self.registry.finalize_startup(inj_moments)
        
        # Verify all scopes along the path are marked as relevant
        root = self.registry._scope_tree_root
        self.assertTrue(root.is_relevant)
        
        tests_scope = root.children.get("tests")
        self.assertIsNotNone(tests_scope)
        self.assertTrue(tests_scope.is_relevant)
        
        package_a_scope = tests_scope.children.get("package_a")
        self.assertIsNotNone(package_a_scope)
        self.assertTrue(package_a_scope.is_relevant)



    def test_finalize_prunes_unreferenced_scopes(self):
        """
        AFTER ensuring all injection scopes, THE System SHALL prune unreferenced 
        scopes from the scope tree.
        Requirements: 7.3, 7.4
        """
        # First, add a resource origin at a scope that won't be referenced
        source = ResourceSource(resource_factory, None, TestResource, {})
        self.registry.register_resource_source(source)
        
        origin = ResourceOrigin(
            "tests.unreferenced_package.unreferenced_module#unreferenced_func",
            "unreferenced_resource",
            ResourceLifespan.Test,
            source=source
        )
        self.registry.register_resource_origin("unreferenced_resource", origin)
        
        # Create injection moment that doesn't reference the unreferenced scope
        inj_mom_a = InjectionMoment(test_function_a)
        
        inj_moments = {
            inj_mom_a.name: inj_mom_a,
        }
        
        self.registry.finalize_startup(inj_moments)
        
        # Verify the unreferenced scope was pruned
        unreferenced_scope = self.registry.lookup_resource_scope(
            "tests.unreferenced_package.unreferenced_module.unreferenced_func"
        )
        self.assertIsNone(unreferenced_scope)
        
        # Verify the referenced scope still exists
        referenced_scope = self.registry.lookup_resource_scope(
            "tests.package_a.module_a.test_function_a"
        )
        self.assertIsNotNone(referenced_scope)


class FinalizeStartupParameterResolutionTests(unittest.TestCase):
    """
    Integration tests for finalize_startup parameter resolution.
    
    Requirements covered:
    - 7.5: Resolve resource originations for each injection moment
    - 7.6: Record unknown parameters in unknown_parameters table
    - 7.7: Collect referenced integrations and configurations
    """

    def setUp(self):
        InjectionRegistry._instance = None
        InjectionRegistry._initialized = False
        self.registry = InjectionRegistry()


    def test_finalize_resolves_resource_originations(self):
        """
        AFTER pruning, THE System SHALL resolve resource originations for each 
        injection moment.
        Requirements: 7.5
        """
        # Register an integration source and origin at session scope
        int_source = IntegrationSource(integration_factory, TestIntegrationCoupling, {})
        self.registry.register_integration_source(int_source)
        
        int_origin = ResourceOrigin(
            "<session>",
            "my_integration",
            ResourceLifespan.Session,
            source=int_source
        )
        self.registry.register_resource_origin("my_integration", int_origin)
        
        # Create injection moment
        inj_mom_a = InjectionMoment(test_function_a)
        
        inj_moments = {
            inj_mom_a.name: inj_mom_a,
        }
        
        self.registry.finalize_startup(inj_moments)
        
        # Verify the session scope has the integration origin
        session_scope = self.registry.lookup_resource_scope("<session>")
        self.assertIn("my_integration", session_scope.parameter_originations)

    def test_finalize_tracks_unknown_parameters(self):
        """
        WHEN parameters cannot be resolved, THE System SHALL record them in the 
        unknown_parameters table.
        Requirements: 7.6
        """
        # Register a resource source that has an unknown dependency
        source = ResourceSource(resource_with_unknown_dependency, None, TestResource, {})
        self.registry.register_resource_source(source)
        
        origin = ResourceOrigin(
            "tests.package_a.module_a#test_function_a",
            "resource_with_unknown",
            ResourceLifespan.Test,
            source=source
        )
        self.registry.register_resource_origin("resource_with_unknown", origin)
        
        # Create injection moment
        inj_mom_a = InjectionMoment(test_function_a)
        
        inj_moments = {
            inj_mom_a.name: inj_mom_a,
        }
        
        self.registry.finalize_startup(inj_moments)
        
        # Verify unknown parameters were tracked
        unknown_params = self.registry.unknown_parameters
        self.assertIn(inj_mom_a.name, unknown_params)
        
        # Verify the unknown parameter name is in the list
        param_names = [p[0] for p in unknown_params[inj_mom_a.name]]
        self.assertIn("unknown_param", param_names)



class FinalizeStartupCouplingCollectionTests(unittest.TestCase):
    """
    Integration tests for finalize_startup integration/configuration collection.
    
    Requirements covered:
    - 9.1: Walk the entire scope tree for collection
    - 9.2: Add IntegrationCoupling subclass to integration table
    - 9.3: Add ConfigurationCoupling subclass to configuration table
    - 9.4: Extract coupling type from generic types containing IntegrationCoupling
    - 9.5: Extract coupling type from generic types containing ConfigurationCoupling
    - 9.6: Skip implied parameter originations when collecting couplings
    """

    def setUp(self):
        InjectionRegistry._instance = None
        InjectionRegistry._initialized = False
        self.registry = InjectionRegistry()

    def test_finalize_collects_integration_couplings(self):
        """
        WHEN a parameter origination's resource type is an IntegrationCoupling 
        subclass, THE System SHALL add it to the integration table.
        Requirements: 9.1, 9.2
        """
        # Register an integration source and origin
        int_source = IntegrationSource(integration_factory, TestIntegrationCoupling, {})
        self.registry.register_integration_source(int_source)
        
        int_origin = ResourceOrigin(
            "<session>",
            "my_integration",
            ResourceLifespan.Session,
            source=int_source
        )
        self.registry.register_resource_origin("my_integration", int_origin)
        
        # Create injection moment
        inj_mom_a = InjectionMoment(test_function_a)
        
        inj_moments = {
            inj_mom_a.name: inj_mom_a,
        }
        
        self.registry.finalize_startup(inj_moments)
        
        # Verify integration coupling was collected
        referenced_integrations = self.registry.referenced_integrations
        self.assertIn(integration_factory, referenced_integrations)
        self.assertEqual(referenced_integrations[integration_factory], TestIntegrationCoupling)

    def test_finalize_collects_configuration_couplings(self):
        """
        WHEN a parameter origination's resource type is a ConfigurationCoupling 
        subclass, THE System SHALL add it to the configuration table.
        Requirements: 9.1, 9.3
        """
        # Register a configuration source and origin
        config_source = ConfigurationSource(configuration_factory, None, TestConfigurationCoupling, {})
        self.registry.register_configuration_source(config_source)
        
        config_origin = ResourceOrigin(
            "<session>",
            "my_configuration",
            ResourceLifespan.Session,
            source=config_source
        )
        self.registry.register_resource_origin("my_configuration", config_origin)
        
        # Create injection moment
        inj_mom_a = InjectionMoment(test_function_a)
        
        inj_moments = {
            inj_mom_a.name: inj_mom_a,
        }
        
        self.registry.finalize_startup(inj_moments)
        
        # Verify configuration coupling was collected
        referenced_configurations = self.registry.referenced_configurations
        self.assertIn(configuration_factory, referenced_configurations)
        self.assertEqual(referenced_configurations[configuration_factory], TestConfigurationCoupling)


    def test_finalize_skips_implied_originations_when_collecting(self):
        """
        THE System SHALL skip implied parameter originations when collecting couplings.
        Requirements: 9.6
        """
        # Add an implied session resource
        self.registry.add_implied_session_resource("implied_resource")
        
        # Register a non-implied integration source and origin
        int_source = IntegrationSource(integration_factory, TestIntegrationCoupling, {})
        self.registry.register_integration_source(int_source)
        
        int_origin = ResourceOrigin(
            "<session>",
            "my_integration",
            ResourceLifespan.Session,
            source=int_source
        )
        self.registry.register_resource_origin("my_integration", int_origin)
        
        # Create injection moment
        inj_mom_a = InjectionMoment(test_function_a)
        
        inj_moments = {
            inj_mom_a.name: inj_mom_a,
        }
        
        self.registry.finalize_startup(inj_moments)
        
        # Verify implied resource is in session scope but not in referenced tables
        session_scope = self.registry.lookup_resource_scope("<session>")
        self.assertIn("implied_resource", session_scope.parameter_originations)
        
        # Verify the non-implied integration was collected
        referenced_integrations = self.registry.referenced_integrations
        self.assertIn(integration_factory, referenced_integrations)

    def test_finalize_collects_from_nested_scopes(self):
        """
        WHEN collecting integrations and configurations, THE System SHALL walk 
        the entire scope tree.
        Requirements: 9.1
        """
        # Register integration at session scope
        int_source = IntegrationSource(integration_factory, TestIntegrationCoupling, {})
        self.registry.register_integration_source(int_source)
        
        int_origin = ResourceOrigin(
            "<session>",
            "session_integration",
            ResourceLifespan.Session,
            source=int_source
        )
        self.registry.register_resource_origin("session_integration", int_origin)
        
        # Register configuration at module scope
        config_source = ConfigurationSource(configuration_factory, None, TestConfigurationCoupling, {})
        self.registry.register_configuration_source(config_source)
        
        config_origin = ResourceOrigin(
            "tests.package_a.module_a#test_function_a",
            "module_configuration",
            ResourceLifespan.Test,
            source=config_source
        )
        self.registry.register_resource_origin("module_configuration", config_origin)
        
        # Create injection moment
        inj_mom_a = InjectionMoment(test_function_a)
        
        inj_moments = {
            inj_mom_a.name: inj_mom_a,
        }
        
        self.registry.finalize_startup(inj_moments)
        
        # Verify both couplings were collected from different scope levels
        self.assertIn(integration_factory, self.registry.referenced_integrations)
        self.assertIn(configuration_factory, self.registry.referenced_configurations)



class FinalizeStartupMultipleMomentsTests(unittest.TestCase):
    """
    Integration tests for finalize_startup with multiple injection moments.
    
    Requirements covered:
    - 7.1-7.7: Complete finalization flow with multiple injection moments
    """

    def setUp(self):
        InjectionRegistry._instance = None
        InjectionRegistry._initialized = False
        self.registry = InjectionRegistry()

    def test_finalize_with_multiple_injection_moments(self):
        """
        Test complete finalization with multiple injection moments across 
        different packages and modules.
        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7
        """
        # Register session-level integration
        int_source = IntegrationSource(integration_factory, TestIntegrationCoupling, {})
        self.registry.register_integration_source(int_source)
        
        int_origin = ResourceOrigin(
            "<session>",
            "shared_integration",
            ResourceLifespan.Session,
            source=int_source
        )
        self.registry.register_resource_origin("shared_integration", int_origin)
        
        # Register package-level configuration
        config_source = ConfigurationSource(configuration_factory, None, TestConfigurationCoupling, {})
        self.registry.register_configuration_source(config_source)
        
        config_origin = ResourceOrigin(
            "tests.package_a",
            "package_config",
            ResourceLifespan.Package,
            source=config_source
        )
        self.registry.register_resource_origin("package_config", config_origin)
        
        # Register test-level resource
        res_source = ResourceSource(resource_factory, None, TestResource, {})
        self.registry.register_resource_source(res_source)
        
        res_origin = ResourceOrigin(
            "tests.package_a.module_a#test_function_a",
            "test_resource",
            ResourceLifespan.Test,
            source=res_source
        )
        self.registry.register_resource_origin("test_resource", res_origin)
        
        # Create multiple injection moments
        inj_mom_a = InjectionMoment(test_function_a)
        inj_mom_b = InjectionMoment(test_function_b)
        inj_mom_c = InjectionMoment(test_function_c)
        
        inj_moments = {
            inj_mom_a.name: inj_mom_a,
            inj_mom_b.name: inj_mom_b,
            inj_mom_c.name: inj_mom_c,
        }
        
        self.registry.finalize_startup(inj_moments)
        
        # Verify all injection moment scopes were created
        scope_a = self.registry.lookup_resource_scope("tests.package_a.module_a.test_function_a")
        scope_b = self.registry.lookup_resource_scope("tests.package_a.module_b.test_function_b")
        scope_c = self.registry.lookup_resource_scope("tests.package_b.module_c.test_function_c")
        
        self.assertIsNotNone(scope_a)
        self.assertIsNotNone(scope_b)
        self.assertIsNotNone(scope_c)
        
        # Verify couplings were collected
        self.assertIn(integration_factory, self.registry.referenced_integrations)
        self.assertIn(configuration_factory, self.registry.referenced_configurations)


    def test_finalize_with_shared_parent_scopes(self):
        """
        Test that injection moments sharing parent scopes correctly share 
        scope nodes.
        Requirements: 7.1, 7.2
        """
        # Create injection moments in the same package
        inj_mom_a = InjectionMoment(test_function_a)
        inj_mom_b = InjectionMoment(test_function_b)
        
        inj_moments = {
            inj_mom_a.name: inj_mom_a,
            inj_mom_b.name: inj_mom_b,
        }
        
        self.registry.finalize_startup(inj_moments)
        
        # Verify shared parent scope exists
        root = self.registry._scope_tree_root
        tests_scope = root.children.get("tests")
        self.assertIsNotNone(tests_scope)
        
        package_a_scope = tests_scope.children.get("package_a")
        self.assertIsNotNone(package_a_scope)
        
        # Verify both module scopes exist under the shared package
        module_a_scope = package_a_scope.children.get("module_a")
        module_b_scope = package_a_scope.children.get("module_b")
        
        self.assertIsNotNone(module_a_scope)
        self.assertIsNotNone(module_b_scope)

    def test_finalize_with_empty_injection_moments(self):
        """
        Test finalize_startup with no injection moments.
        Requirements: 7.1, 7.3
        """
        # Register a resource origin that should be pruned
        source = ResourceSource(resource_factory, None, TestResource, {})
        self.registry.register_resource_source(source)
        
        origin = ResourceOrigin(
            "tests.orphan_package.orphan_module#orphan_func",
            "orphan_resource",
            ResourceLifespan.Test,
            source=source
        )
        self.registry.register_resource_origin("orphan_resource", origin)
        
        # Finalize with empty injection moments
        inj_moments = {}
        
        self.registry.finalize_startup(inj_moments)
        
        # Verify the orphan scope was pruned
        orphan_scope = self.registry.lookup_resource_scope(
            "tests.orphan_package.orphan_module.orphan_func"
        )
        self.assertIsNone(orphan_scope)
        
        # Verify no unknown parameters or referenced couplings
        self.assertEqual(len(self.registry.unknown_parameters), 0)


if __name__ == '__main__':
    unittest.main()
