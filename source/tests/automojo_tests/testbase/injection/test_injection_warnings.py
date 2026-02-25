"""
    Unit tests for injection system warnings.
    
    This module tests the warning functionality added to the dependency injection
    system to help developers identify potential configuration issues:
    
    - Unused registered sources: Sources that were registered but never used
    - Shadowed parameters: Parameters that hide parent scope parameters
    
    These warnings help catch configuration errors without failing the test run.
"""

import unittest
import warnings

from automojo.testbase.injection.injectionregistry import InjectionRegistry
from automojo.testbase.injection.injectionmoment import InjectionMoment
from automojo.testbase.origins.resourceorigin import ResourceOrigin
from automojo.testbase.resourcelifespan import ResourceLifespan

from automojo.testbase.sources.integrationsource import IntegrationSource
from automojo.testbase.sources.resourcesource import ResourceSource
from automojo.testbase.sources.configurationsource import ConfigurationSource
from automojo.testbase.sources.validatorsource import ValidatorSource

from automojo.testbase.coupling.integrationcoupling import IntegrationCoupling
from automojo.testbase.coupling.configurationcoupling import ConfigurationCoupling


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


def unused_integration_factory() -> TestIntegrationCoupling:
    return TestIntegrationCoupling()


def unused_resource_factory() -> TestResource:
    return TestResource()


def unused_configuration_factory() -> TestConfigurationCoupling:
    return TestConfigurationCoupling()


def unused_validator_factory() -> TestValidator:
    return TestValidator()


# Test functions to create injection moments
def test_function_a():
    """Test function for injection moment A."""
    pass


def test_function_b():
    """Test function for injection moment B."""
    pass


# Override module names for test functions to simulate different modules
test_function_a.__module__ = "tests.package_a.module_a"
test_function_b.__module__ = "tests.package_a.module_b"


class UnusedSourceWarningTests(unittest.TestCase):
    """
    Tests for warnings about unused registered sources.
    
    These tests verify that the system warns when sources are registered
    but not used by any parameter origination.
    """

    def setUp(self):
        InjectionRegistry._instance = None
        InjectionRegistry._initialized = False
        self.registry = InjectionRegistry()

    def test_warns_about_unused_integration_source(self):
        """Verify warning is issued for unused integration source."""
        # Register an integration source but don't use it
        source = IntegrationSource(unused_integration_factory, TestIntegrationCoupling, {})
        self.registry.register_integration_source(source)
        
        # Create injection moment without using the source
        inj_mom = InjectionMoment(test_function_a)
        inj_moments = {inj_mom.name: inj_mom}
        
        # Capture warnings during finalize_startup
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.registry.finalize_startup(inj_moments)
            
            # Verify warning was issued
            unused_warnings = [
                warning for warning in w 
                if issubclass(warning.category, InjectionRegistry.UnusedSourceWarning)
            ]
            self.assertEqual(len(unused_warnings), 1)
            self.assertIn("unused_integration_factory", str(unused_warnings[0].message))

    def test_warns_about_unused_resource_source(self):
        """Verify warning is issued for unused resource source."""
        # Register a resource source but don't use it
        source = ResourceSource(unused_resource_factory, None, TestResource, {})
        self.registry.register_resource_source(source)
        
        # Create injection moment without using the source
        inj_mom = InjectionMoment(test_function_a)
        inj_moments = {inj_mom.name: inj_mom}
        
        # Capture warnings during finalize_startup
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.registry.finalize_startup(inj_moments)
            
            # Verify warning was issued
            unused_warnings = [
                warning for warning in w 
                if issubclass(warning.category, InjectionRegistry.UnusedSourceWarning)
            ]
            self.assertEqual(len(unused_warnings), 1)
            self.assertIn("unused_resource_factory", str(unused_warnings[0].message))

    def test_warns_about_unused_configuration_source(self):
        """Verify warning is issued for unused configuration source."""
        # Register a configuration source but don't use it
        source = ConfigurationSource(unused_configuration_factory, None, TestConfigurationCoupling, {})
        self.registry.register_configuration_source(source)
        
        # Create injection moment without using the source
        inj_mom = InjectionMoment(test_function_a)
        inj_moments = {inj_mom.name: inj_mom}
        
        # Capture warnings during finalize_startup
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.registry.finalize_startup(inj_moments)
            
            # Verify warning was issued
            unused_warnings = [
                warning for warning in w 
                if issubclass(warning.category, InjectionRegistry.UnusedSourceWarning)
            ]
            self.assertEqual(len(unused_warnings), 1)
            self.assertIn("unused_configuration_factory", str(unused_warnings[0].message))

    def test_warns_about_unused_validator_source(self):
        """Verify warning is issued for unused validator source."""
        # Register a validator source but don't use it
        source = ValidatorSource(unused_validator_factory, TestValidator, {})
        self.registry.register_validator_source(source)
        
        # Create injection moment without using the source
        inj_mom = InjectionMoment(test_function_a)
        inj_moments = {inj_mom.name: inj_mom}
        
        # Capture warnings during finalize_startup
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.registry.finalize_startup(inj_moments)
            
            # Verify warning was issued
            unused_warnings = [
                warning for warning in w 
                if issubclass(warning.category, InjectionRegistry.UnusedSourceWarning)
            ]
            self.assertEqual(len(unused_warnings), 1)
            self.assertIn("unused_validator_factory", str(unused_warnings[0].message))

    def test_no_warning_for_used_source(self):
        """Verify no warning is issued when source is used."""
        # Register and use an integration source
        source = IntegrationSource(integration_factory, TestIntegrationCoupling, {})
        self.registry.register_integration_source(source)
        
        # Create origin that uses the source
        origin = ResourceOrigin(
            "<session>",
            "my_integration",
            ResourceLifespan.Session,
            source=source
        )
        self.registry.register_resource_origin("my_integration", origin)
        
        # Create injection moment
        inj_mom = InjectionMoment(test_function_a)
        inj_moments = {inj_mom.name: inj_mom}
        
        # Capture warnings during finalize_startup
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.registry.finalize_startup(inj_moments)
            
            # Verify no unused source warnings were issued
            unused_warnings = [
                warning for warning in w 
                if issubclass(warning.category, InjectionRegistry.UnusedSourceWarning)
            ]
            self.assertEqual(len(unused_warnings), 0)

    def test_warns_about_multiple_unused_sources(self):
        """Verify warnings are issued for multiple unused sources."""
        # Register multiple unused sources
        int_source = IntegrationSource(unused_integration_factory, TestIntegrationCoupling, {})
        res_source = ResourceSource(unused_resource_factory, None, TestResource, {})
        self.registry.register_integration_source(int_source)
        self.registry.register_resource_source(res_source)
        
        # Create injection moment without using any sources
        inj_mom = InjectionMoment(test_function_a)
        inj_moments = {inj_mom.name: inj_mom}
        
        # Capture warnings during finalize_startup
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.registry.finalize_startup(inj_moments)
            
            # Verify warnings were issued for both unused sources
            unused_warnings = [
                warning for warning in w 
                if issubclass(warning.category, InjectionRegistry.UnusedSourceWarning)
            ]
            self.assertEqual(len(unused_warnings), 2)


class ShadowedParameterWarningTests(unittest.TestCase):
    """
    Tests for warnings about shadowed parameters in nested scopes.
    
    These tests verify that the system warns when a parameter at a child
    scope has the same identifier as a parameter in a parent scope.
    """

    def setUp(self):
        InjectionRegistry._instance = None
        InjectionRegistry._initialized = False
        self.registry = InjectionRegistry()

    def test_warns_about_shadowed_parameter(self):
        """Verify warning is issued when parameter shadows parent scope parameter."""
        # Register a source
        source = ResourceSource(resource_factory, None, TestResource, {})
        self.registry.register_resource_source(source)
        
        # Create origin at session scope
        session_origin = ResourceOrigin(
            "<session>",
            "shared_resource",
            ResourceLifespan.Session,
            source=source
        )
        self.registry.register_resource_origin("shared_resource", session_origin)
        
        # Create origin with same identifier at test scope (shadows session)
        test_origin = ResourceOrigin(
            "tests.package_a.module_a#test_function_a",
            "shared_resource",
            ResourceLifespan.Test,
            source=source
        )
        self.registry.register_resource_origin("shared_resource", test_origin)
        
        # Create injection moment
        inj_mom = InjectionMoment(test_function_a)
        inj_moments = {inj_mom.name: inj_mom}
        
        # Capture warnings during finalize_startup
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.registry.finalize_startup(inj_moments)
            
            # Verify shadowed parameter warning was issued
            shadow_warnings = [
                warning for warning in w 
                if issubclass(warning.category, InjectionRegistry.ShadowedParameterWarning)
            ]
            self.assertEqual(len(shadow_warnings), 1)
            self.assertIn("shared_resource", str(shadow_warnings[0].message))
            self.assertIn("shadows", str(shadow_warnings[0].message))

    def test_no_warning_for_unique_parameters(self):
        """Verify no warning when parameters have unique identifiers."""
        # Register a source
        source = ResourceSource(resource_factory, None, TestResource, {})
        self.registry.register_resource_source(source)
        
        # Create origin at session scope
        session_origin = ResourceOrigin(
            "<session>",
            "session_resource",
            ResourceLifespan.Session,
            source=source
        )
        self.registry.register_resource_origin("session_resource", session_origin)
        
        # Create origin with different identifier at test scope
        test_origin = ResourceOrigin(
            "tests.package_a.module_a#test_function_a",
            "test_resource",
            ResourceLifespan.Test,
            source=source
        )
        self.registry.register_resource_origin("test_resource", test_origin)
        
        # Create injection moment
        inj_mom = InjectionMoment(test_function_a)
        inj_moments = {inj_mom.name: inj_mom}
        
        # Capture warnings during finalize_startup
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.registry.finalize_startup(inj_moments)
            
            # Verify no shadowed parameter warnings were issued
            shadow_warnings = [
                warning for warning in w 
                if issubclass(warning.category, InjectionRegistry.ShadowedParameterWarning)
            ]
            self.assertEqual(len(shadow_warnings), 0)

    def test_warns_about_multiple_shadowed_parameters(self):
        """Verify warnings are issued for multiple shadowed parameters."""
        # Register sources
        source1 = ResourceSource(resource_factory, None, TestResource, {})
        source2 = IntegrationSource(integration_factory, TestIntegrationCoupling, {})
        self.registry.register_resource_source(source1)
        self.registry.register_integration_source(source2)
        
        # Create origins at session scope
        session_origin1 = ResourceOrigin(
            "<session>",
            "resource_a",
            ResourceLifespan.Session,
            source=source1
        )
        session_origin2 = ResourceOrigin(
            "<session>",
            "resource_b",
            ResourceLifespan.Session,
            source=source2
        )
        self.registry.register_resource_origin("resource_a", session_origin1)
        self.registry.register_resource_origin("resource_b", session_origin2)
        
        # Create origins with same identifiers at test scope (both shadow session)
        test_origin1 = ResourceOrigin(
            "tests.package_a.module_a#test_function_a",
            "resource_a",
            ResourceLifespan.Test,
            source=source1
        )
        test_origin2 = ResourceOrigin(
            "tests.package_a.module_a#test_function_a",
            "resource_b",
            ResourceLifespan.Test,
            source=source2
        )
        self.registry.register_resource_origin("resource_a", test_origin1)
        self.registry.register_resource_origin("resource_b", test_origin2)
        
        # Create injection moment
        inj_mom = InjectionMoment(test_function_a)
        inj_moments = {inj_mom.name: inj_mom}
        
        # Capture warnings during finalize_startup
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.registry.finalize_startup(inj_moments)
            
            # Verify warnings were issued for both shadowed parameters
            shadow_warnings = [
                warning for warning in w 
                if issubclass(warning.category, InjectionRegistry.ShadowedParameterWarning)
            ]
            self.assertEqual(len(shadow_warnings), 2)


class WarningFilteringTests(unittest.TestCase):
    """
    Tests for warning filtering capabilities.
    
    These tests verify that warnings can be filtered using Python's
    standard warning filtering mechanisms.
    """

    def setUp(self):
        InjectionRegistry._instance = None
        InjectionRegistry._initialized = False
        self.registry = InjectionRegistry()

    def test_unused_source_warning_can_be_filtered(self):
        """Verify UnusedSourceWarning can be filtered out."""
        # Register an unused source
        source = ResourceSource(unused_resource_factory, None, TestResource, {})
        self.registry.register_resource_source(source)
        
        # Create injection moment
        inj_mom = InjectionMoment(test_function_a)
        inj_moments = {inj_mom.name: inj_mom}
        
        # Filter out UnusedSourceWarning
        with warnings.catch_warnings(record=True) as w:
            warnings.filterwarnings("ignore", category=InjectionRegistry.UnusedSourceWarning)
            self.registry.finalize_startup(inj_moments)
            
            # Verify no warnings were captured
            unused_warnings = [
                warning for warning in w 
                if issubclass(warning.category, InjectionRegistry.UnusedSourceWarning)
            ]
            self.assertEqual(len(unused_warnings), 0)

    def test_shadowed_parameter_warning_can_be_filtered(self):
        """Verify ShadowedParameterWarning can be filtered out."""
        # Register a source
        source = ResourceSource(resource_factory, None, TestResource, {})
        self.registry.register_resource_source(source)
        
        # Create shadowing origins
        session_origin = ResourceOrigin(
            "<session>",
            "shared_resource",
            ResourceLifespan.Session,
            source=source
        )
        test_origin = ResourceOrigin(
            "tests.package_a.module_a#test_function_a",
            "shared_resource",
            ResourceLifespan.Test,
            source=source
        )
        self.registry.register_resource_origin("shared_resource", session_origin)
        self.registry.register_resource_origin("shared_resource", test_origin)
        
        # Create injection moment
        inj_mom = InjectionMoment(test_function_a)
        inj_moments = {inj_mom.name: inj_mom}
        
        # Filter out ShadowedParameterWarning
        with warnings.catch_warnings(record=True) as w:
            warnings.filterwarnings("ignore", category=InjectionRegistry.ShadowedParameterWarning)
            self.registry.finalize_startup(inj_moments)
            
            # Verify no shadowed parameter warnings were captured
            shadow_warnings = [
                warning for warning in w 
                if issubclass(warning.category, InjectionRegistry.ShadowedParameterWarning)
            ]
            self.assertEqual(len(shadow_warnings), 0)


if __name__ == '__main__':
    unittest.main()
