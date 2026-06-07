"""
    Integration tests for the Test Declaration and Registration system.
    
    These tests verify the end-to-end registration flow from decorator to registry lookup
    and scope tree construction with multiple registrations.
    
    Requirements: 8.3, 8.4, 9.1, 9.2, 9.3, 9.4, 9.5
"""

import typing
import unittest

from ccai.errors.exceptions import SemanticError
from ccai.testbase.coupling.integrationcoupling import IntegrationCoupling
from ccai.testbase.coupling.configurationcoupling import ConfigurationCoupling
from ccai.testbase.coupling.validatorcoupling import ValidatorCoupling

from ccai.testbase.declaration import attachments, originations, registrations
from ccai.testbase.injection import injectionregistry
from ccai.testbase.injection.injectionscope import InjectionScope
from ccai.testbase.injection.injectionmoment import InjectionMoment
from ccai.testbase.resourcelifespan import ResourceLifespan
from ccai.testbase.sources.integrationsource import IntegrationSource
from ccai.testbase.sources.resourcesource import ResourceSource
from ccai.testbase.sources.configurationsource import ConfigurationSource
from ccai.testbase.sources.validatorsource import ValidatorSource


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


class TestRegistrySeparateTables(unittest.TestCase):
    """
    Test that InjectionRegistry maintains separate tables for different source types.
    Requirements: 8.3
    """

    def setUp(self):
        self.registry = reset_registry()

    def test_separate_tables_for_all_source_types(self):
        """Verify that each source type is stored in its own table."""
        
        # Create test coupling classes
        class TestIntegration(IntegrationCoupling):
            _name = None
            pass

        class TestConfig(ConfigurationCoupling):
            pass

        class TestValidator(ValidatorCoupling):
            pass

        # Register integration factory
        @registrations.integration_factory()
        def integration_source() -> typing.Generator[TestIntegration, None, None]:
            if False:
                yield TestIntegration()

        # Register resource factory
        @registrations.resource_factory()
        def resource_source() -> int:
            return 42

        # Register configuration factory
        @registrations.configuration_factory()
        def config_source() -> typing.Generator[TestConfig, None, None]:
            if False:
                yield TestConfig()

        # Register validator factory
        @registrations.validator_factory()
        def validator_source() -> TestValidator:
            return TestValidator()

        # Verify each source is in its respective table
        self.assertIn(integration_source, self.registry._integration_source)
        self.assertIn(resource_source, self.registry._resource_source)
        self.assertIn(config_source, self.registry._configuration_source)
        self.assertIn(validator_source, self.registry._validator_source)

        # Verify sources are NOT in wrong tables
        self.assertNotIn(integration_source, self.registry._resource_source)
        self.assertNotIn(resource_source, self.registry._integration_source)
        self.assertNotIn(config_source, self.registry._integration_source)
        self.assertNotIn(validator_source, self.registry._resource_source)


class TestScopeTreeConstruction(unittest.TestCase):
    """
    Test that InjectionRegistry maintains a scope tree for parameter visibility.
    Requirements: 8.4
    """

    def setUp(self):
        self.registry = reset_registry()

    def test_scope_tree_exists(self):
        """Verify that the registry has a scope tree root."""
        self.assertIsInstance(self.registry._scope_tree_root, InjectionScope)

    def test_scope_tree_with_multiple_registrations(self):
        """Test scope tree construction with multiple parameter registrations."""
        
        @registrations.resource_factory()
        def resource_a() -> int:
            return 1

        @registrations.resource_factory()
        def resource_b() -> str:
            return "test"

        # Create parameter origins at different scopes
        originations.parameter(resource_a, identifier="param_a")
        originations.parameter(resource_b, identifier="param_b")

        # Verify both parameters are registered in the scope tree
        module_name = __name__
        self.assertTrue(self.registry._scope_tree_root.has_descendent_resource(module_name, "param_a"))
        self.assertTrue(self.registry._scope_tree_root.has_descendent_resource(module_name, "param_b"))

    def test_scope_tree_with_test_level_parameters(self):
        """Test scope tree construction with test-level parameter attachments."""
        
        @registrations.resource_factory()
        def test_resource() -> int:
            return 100

        @attachments.parameter(test_resource, identifier="test_param")
        def test_function(test_param):
            return test_param

        # Verify the parameter is registered at the test function scope
        scope = f"{test_function.__module__}#{test_function.__name__}"
        self.assertTrue(self.registry._scope_tree_root.has_descendent_resource(scope, "test_param"))


class TestSourceLookup(unittest.TestCase):
    """
    Test source lookup functionality across all source tables.
    Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
    """

    def setUp(self):
        self.registry = reset_registry()

    def test_lookup_integration_source(self):
        """Test that integration sources can be looked up. Requirements: 9.1, 9.2"""
        
        class TestIntegration(IntegrationCoupling):
            _name = None
            pass

        @registrations.integration_factory()
        def my_integration() -> typing.Generator[TestIntegration, None, None]:
            if False:
                yield TestIntegration()

        source = self.registry.lookup_resource_source(my_integration)
        self.assertIsNotNone(source)
        self.assertIsInstance(source, IntegrationSource)

    def test_lookup_resource_source(self):
        """Test that resource sources can be looked up. Requirements: 9.1, 9.2"""
        
        @registrations.resource_factory()
        def my_resource() -> int:
            return 42

        source = self.registry.lookup_resource_source(my_resource)
        self.assertIsNotNone(source)
        self.assertIsInstance(source, ResourceSource)

    def test_lookup_configuration_source(self):
        """Test that configuration sources can be looked up. Requirements: 9.1, 9.2"""
        
        class TestConfig(ConfigurationCoupling):
            pass

        @registrations.configuration_factory()
        def my_config() -> typing.Generator[TestConfig, None, None]:
            if False:
                yield TestConfig()

        source = self.registry.lookup_resource_source(my_config)
        self.assertIsNotNone(source)
        self.assertIsInstance(source, ConfigurationSource)

    def test_lookup_returns_none_for_unregistered(self):
        """Test that lookup returns None for unregistered sources. Requirements: 9.3"""
        
        def unregistered_function():
            return None

        source = self.registry.lookup_resource_source(unregistered_function)
        self.assertIsNone(source)

    def test_lookup_validator_source(self):
        """Test that validator sources can be looked up. Requirements: 9.4, 9.5"""
        
        class TestValidator(ValidatorCoupling):
            pass

        @registrations.validator_factory()
        def my_validator() -> TestValidator:
            return TestValidator()

        source = self.registry.lookup_validator_source(my_validator)
        self.assertIsNotNone(source)
        self.assertIsInstance(source, ValidatorSource)

    def test_lookup_validator_returns_none_for_unregistered(self):
        """Test that validator lookup returns None for unregistered sources."""
        
        def unregistered_validator():
            return None

        source = self.registry.lookup_validator_source(unregistered_validator)
        self.assertIsNone(source)


class TestEndToEndRegistrationFlow(unittest.TestCase):
    """
    Test complete end-to-end registration flow from decorator to registry lookup.
    Requirements: 8.3, 8.4, 9.1, 9.2, 9.3, 9.4, 9.5
    """

    def setUp(self):
        self.registry = reset_registry()

    def test_complete_flow_integration_factory(self):
        """Test complete flow: decorator -> source registration -> lookup -> origin creation."""
        
        class TestIntegration(IntegrationCoupling):
            _name = None
            pass

        # Step 1: Register via decorator
        @registrations.integration_factory()
        def integration_factory_func() -> typing.Generator[TestIntegration, None, None]:
            if False:
                yield TestIntegration()

        # Step 2: Verify source is registered
        source = self.registry.lookup_resource_source(integration_factory_func)
        self.assertIsInstance(source, IntegrationSource)
        self.assertEqual(source.resource_type, TestIntegration)

        # Step 3: Create origin using the source
        originations.parameter(integration_factory_func, identifier="test_integration")

        # Step 4: Verify origin is in scope tree (session scope for integrations)
        self.assertTrue(self.registry._scope_tree_root.has_descendent_resource("<session>", "test_integration"))

    def test_complete_flow_resource_factory(self):
        """Test complete flow for resource factory."""
        
        # Step 1: Register via decorator
        @registrations.resource_factory()
        def resource_factory_func() -> str:
            return "test_value"

        # Step 2: Verify source is registered
        source = self.registry.lookup_resource_source(resource_factory_func)
        self.assertIsInstance(source, ResourceSource)
        self.assertEqual(source.resource_type, str)

        # Step 3: Create origin using the source
        originations.parameter(resource_factory_func, identifier="test_resource")

        # Step 4: Verify origin is in scope tree (package scope for resources)
        module_name = __name__
        self.assertTrue(self.registry._scope_tree_root.has_descendent_resource(module_name, "test_resource"))

    def test_complete_flow_with_attachment(self):
        """Test complete flow with test-level attachment."""
        
        # Step 1: Register via decorator
        @registrations.resource_factory()
        def attached_resource() -> int:
            return 123

        # Step 2: Attach to test function
        @attachments.parameter(attached_resource, identifier="attached_param")
        def test_with_attachment(attached_param):
            return attached_param

        # Step 3: Verify source is registered
        source = self.registry.lookup_resource_source(attached_resource)
        self.assertIsInstance(source, ResourceSource)

        # Step 4: Verify origin is in scope tree at test scope
        scope = f"{test_with_attachment.__module__}#{test_with_attachment.__name__}"
        self.assertTrue(self.registry._scope_tree_root.has_descendent_resource(scope, "attached_param"))

    def test_complete_flow_validator(self):
        """Test complete flow for validator factory with attachment."""
        
        class TestValidator(ValidatorCoupling):
            pass

        # Step 1: Register via decorator
        @registrations.validator_factory()
        def validator_factory_func() -> TestValidator:
            return TestValidator()

        # Step 2: Verify source is registered
        source = self.registry.lookup_validator_source(validator_factory_func)
        self.assertIsInstance(source, ValidatorSource)
        self.assertEqual(source.resource_type, TestValidator)

        # Step 3: Attach to test function
        @attachments.validation(validator_factory_func, suffix="test_suffix", identifier="test_validator")
        def test_with_validator():
            pass

        # Step 4: Verify validator origin is in scope tree
        scope = f"{test_with_validator.__module__}#{test_with_validator.__name__}"
        self.assertTrue(self.registry._scope_tree_root.has_descendent_validator(scope, "test_validator"))


class TestMultipleRegistrationsScoping(unittest.TestCase):
    """
    Test scope tree construction with multiple registrations at different scopes.
    Requirements: 8.4
    """

    def setUp(self):
        self.registry = reset_registry()

    def test_multiple_resources_same_scope(self):
        """Test multiple resources registered at the same scope."""
        
        @registrations.resource_factory()
        def resource_one() -> int:
            return 1

        @registrations.resource_factory()
        def resource_two() -> str:
            return "two"

        @registrations.resource_factory()
        def resource_three() -> float:
            return 3.0

        # Register all at package scope
        originations.parameter(resource_one, identifier="res_one")
        originations.parameter(resource_two, identifier="res_two")
        originations.parameter(resource_three, identifier="res_three")

        # Verify all are in scope tree
        module_name = __name__
        self.assertTrue(self.registry._scope_tree_root.has_descendent_resource(module_name, "res_one"))
        self.assertTrue(self.registry._scope_tree_root.has_descendent_resource(module_name, "res_two"))
        self.assertTrue(self.registry._scope_tree_root.has_descendent_resource(module_name, "res_three"))

    def test_resources_at_different_scopes(self):
        """Test resources registered at different scopes (session vs package vs test)."""
        
        class TestIntegration(IntegrationCoupling):
            _name = None
            pass

        @registrations.integration_factory()
        def session_resource() -> typing.Generator[TestIntegration, None, None]:
            if False:
                yield TestIntegration()

        @registrations.resource_factory()
        def package_resource() -> int:
            return 42

        @registrations.resource_factory()
        def test_resource() -> str:
            return "test"

        # Register at session scope (integration)
        originations.parameter(session_resource, identifier="session_param")

        # Register at package scope
        originations.parameter(package_resource, identifier="package_param")

        # Register at test scope via attachment
        @attachments.parameter(test_resource, identifier="test_param")
        def test_function(test_param):
            return test_param

        # Verify session scope
        self.assertTrue(self.registry._scope_tree_root.has_descendent_resource("<session>", "session_param"))

        # Verify package scope
        module_name = __name__
        self.assertTrue(self.registry._scope_tree_root.has_descendent_resource(module_name, "package_param"))

        # Verify test scope
        test_scope = f"{test_function.__module__}#{test_function.__name__}"
        self.assertTrue(self.registry._scope_tree_root.has_descendent_resource(test_scope, "test_param"))


class TestDuplicateIdentifierValidation(unittest.TestCase):
    """
    Test validation for duplicate identifier registration in the same scope.
    Requirements: 10.2, 10.4
    """

    def setUp(self):
        self.registry = reset_registry()

    def test_duplicate_resource_identifier_same_scope_raises_error(self):
        """
        Test that registering a resource origin with a duplicate identifier in the same scope raises SemanticError.
        Requirements: 10.2
        """
        @registrations.resource_factory()
        def resource_a() -> int:
            return 1

        @registrations.resource_factory()
        def resource_b() -> int:
            return 2

        # Register first resource with identifier "duplicate_id"
        originations.parameter(resource_a, identifier="duplicate_id")

        # Attempt to register second resource with same identifier in same scope
        with self.assertRaises(SemanticError) as context:
            originations.parameter(resource_b, identifier="duplicate_id")

        # Verify error message contains relevant information
        error_msg = str(context.exception)
        self.assertIn("duplicate_id", error_msg)

    def test_duplicate_resource_identifier_different_scope_allowed(self):
        """
        Test that the same identifier can be used in different scopes.
        Requirements: 10.2
        """
        @registrations.resource_factory()
        def resource_a() -> int:
            return 1

        @registrations.resource_factory()
        def resource_b() -> int:
            return 2

        # Register at package scope
        originations.parameter(resource_a, identifier="shared_id")

        # Register at test scope (different scope) - should succeed
        @attachments.parameter(resource_b, identifier="shared_id")
        def test_function(shared_id):
            return shared_id

        # Verify both are registered in their respective scopes
        module_name = __name__
        test_scope = f"{test_function.__module__}#{test_function.__name__}"
        
        self.assertTrue(self.registry._scope_tree_root.has_descendent_resource(module_name, "shared_id"))
        self.assertTrue(self.registry._scope_tree_root.has_descendent_resource(test_scope, "shared_id"))

    def test_duplicate_validator_identifier_same_scope_raises_error(self):
        """
        Test that registering a validator origin with a duplicate identifier in the same scope raises SemanticError.
        Requirements: 10.4
        """
        class TestValidator(ValidatorCoupling):
            pass

        @registrations.validator_factory()
        def validator_a() -> TestValidator:
            return TestValidator()

        @registrations.validator_factory()
        def validator_b() -> TestValidator:
            return TestValidator()

        # Create first test function with validator
        @attachments.validation(validator_a, suffix="suf", identifier="dup_validator")
        def test_func_a():
            pass

        # Attempt to register second validator with same identifier in same scope
        # This requires registering at the same scope, which means same test function
        # Since we can't decorate the same function twice in the same test, we'll
        # directly test the registry's register_validator_origin method
        from ccai.testbase.origins.validatororigin import ValidatorOrigin
        
        source = self.registry.lookup_validator_source(validator_b)
        scope = f"{test_func_a.__module__}#{test_func_a.__name__}"
        
        # Create a duplicate validator origin at the same scope
        # ValidatorOrigin signature: (originating_scope, identifier, suffix, source, implied, constraints)
        duplicate_origin = ValidatorOrigin(scope, "dup_validator", "suf2", source)
        
        with self.assertRaises(SemanticError) as context:
            self.registry.register_validator_origin("dup_validator", duplicate_origin)

        # Verify error message contains relevant information
        error_msg = str(context.exception)
        self.assertIn("dup_validator", error_msg)

    def test_duplicate_validator_identifier_different_scope_allowed(self):
        """
        Test that the same validator identifier can be used in different scopes.
        Requirements: 10.4
        """
        class TestValidator(ValidatorCoupling):
            pass

        @registrations.validator_factory()
        def validator_a() -> TestValidator:
            return TestValidator()

        @registrations.validator_factory()
        def validator_b() -> TestValidator:
            return TestValidator()

        # Register validator at first test scope
        @attachments.validation(validator_a, suffix="suf1", identifier="shared_validator")
        def test_func_one():
            pass

        # Register validator at second test scope (different scope) - should succeed
        @attachments.validation(validator_b, suffix="suf2", identifier="shared_validator")
        def test_func_two():
            pass

        # Verify both are registered in their respective scopes
        scope_one = f"{test_func_one.__module__}#{test_func_one.__name__}"
        scope_two = f"{test_func_two.__module__}#{test_func_two.__name__}"
        
        self.assertTrue(self.registry._scope_tree_root.has_descendent_validator(scope_one, "shared_validator"))
        self.assertTrue(self.registry._scope_tree_root.has_descendent_validator(scope_two, "shared_validator"))

    def test_duplicate_resource_at_session_scope_raises_error(self):
        """
        Test that duplicate resource identifiers at session scope raise SemanticError.
        Requirements: 10.2
        """
        class TestIntegration(IntegrationCoupling):
            _name = None
            pass

        @registrations.integration_factory()
        def integration_a() -> typing.Generator[TestIntegration, None, None]:
            if False:
                yield TestIntegration()

        @registrations.integration_factory()
        def integration_b() -> typing.Generator[TestIntegration, None, None]:
            if False:
                yield TestIntegration()

        # Register first integration at session scope
        originations.parameter(integration_a, identifier="session_dup")

        # Attempt to register second integration with same identifier at session scope
        with self.assertRaises(SemanticError) as context:
            originations.parameter(integration_b, identifier="session_dup")

        # Verify error message contains relevant information
        error_msg = str(context.exception)
        self.assertIn("session_dup", error_msg)

    def test_duplicate_resource_error_message_includes_scope(self):
        """
        Test that the error message for duplicate identifiers includes the scope information.
        Requirements: 10.2
        """
        @registrations.resource_factory()
        def resource_a() -> int:
            return 1

        @registrations.resource_factory()
        def resource_b() -> int:
            return 2

        # Register first resource
        originations.parameter(resource_a, identifier="test_dup_scope")

        # Attempt to register duplicate
        with self.assertRaises(SemanticError) as context:
            originations.parameter(resource_b, identifier="test_dup_scope")

        # Verify error message contains both identifier and scope
        error_msg = str(context.exception)
        self.assertIn("test_dup_scope", error_msg)
        # The scope should be mentioned in the error message
        self.assertIn("scope", error_msg.lower())


if __name__ == "__main__":
    unittest.main()
