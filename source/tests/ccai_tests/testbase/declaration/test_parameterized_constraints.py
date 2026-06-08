"""
    Tests for parameterized constraints support in the Test Declaration and Registration system.
    
    This module verifies:
    1. Dynamic constraint evaluation is supported
    2. Constraints can be passed to generators in any scope via the constraint dictionary
    
    Task: Support for parameterized constraints
"""

import typing
import unittest

from ccai.testbase.constraints import (
    Constraints,
    ConstraintsCatalog,
    ConstraintsOrigin,
    FeatureConstraints,
    merge_constraints,
)
from ccai.testbase.coupling.integrationcoupling import IntegrationCoupling
from ccai.testbase.coupling.configurationcoupling import ConfigurationCoupling
from ccai.testbase.coupling.validatorcoupling import ValidatorCoupling

from ccai.testbase.declaration import attachments, originations, registrations
from ccai.testbase.injection import injectionregistry
from ccai.testbase.injection.injectionscope import InjectionScope
from ccai.testbase.resourcelifespan import ResourceLifespan
from ccai.testbase.origins.resourceorigin import ResourceOrigin


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


def reset_constraints_catalog():
    """Reset the constraints catalog to a clean state for testing.
    
    Note: The ConstraintsCatalog is a singleton, but the resourceorigin module
    has its own module-level reference. We need to reset both the singleton
    and the module-level reference to ensure tests are isolated.
    """
    # Reset the singleton
    ConstraintsCatalog._instance = None
    ConstraintsCatalog._initialized = False
    
    # Also reset the module-level catalog in resourceorigin
    from ccai.testbase.origins import resourceorigin
    resourceorigin.constraints_catalog = ConstraintsCatalog()
    
    # Return the same catalog instance that resourceorigin uses
    return resourceorigin.constraints_catalog


class TestDynamicConstraintEvaluation(unittest.TestCase):
    """
    Tests verifying that dynamic constraint evaluation is supported.
    
    Dynamic constraints allow runtime configuration of resource factories
    through the ConstraintsCatalog lookup mechanism.
    """

    def setUp(self):
        reset_registry()
        self.catalog = reset_constraints_catalog()

    def test_constraints_can_be_added_at_runtime(self):
        """Verify constraints can be added dynamically at runtime."""
        constraints = Constraints(host="localhost", port=5432)
        
        key = self.catalog.add_constraints(
            ConstraintsOrigin.SITE_PARAMETER,
            "test.scope",
            "db_config",
            constraints
        )
        
        self.assertEqual(key, "test.scope:db_config")
        looked_up = self.catalog.lookup_constraints(key)
        self.assertEqual(looked_up["host"], "localhost")
        self.assertEqual(looked_up["port"], 5432)

    def test_override_constraints_take_precedence(self):
        """Verify override constraints take precedence over site constraints."""
        site_constraints = Constraints(timeout=30, retries=3)
        override_constraints = Constraints(timeout=60)
        
        key = self.catalog.add_constraints(
            ConstraintsOrigin.SITE_PARAMETER,
            "test.scope",
            "config",
            site_constraints
        )
        self.catalog.add_constraints(
            ConstraintsOrigin.OVERRIDE_PARAMETER,
            "test.scope",
            "config",
            override_constraints
        )
        
        looked_up = self.catalog.lookup_constraints(key)
        # Override should win
        self.assertEqual(looked_up["timeout"], 60)

    def test_constraints_can_be_modified_dynamically(self):
        """Verify constraints can be updated dynamically using the callable interface."""
        base_constraints = Constraints(host="localhost", port=5432)
        
        # Create derived constraints dynamically
        derived = base_constraints(port=5433, debug=True)
        
        self.assertEqual(derived["host"], "localhost")
        self.assertEqual(derived["port"], 5433)
        self.assertEqual(derived["debug"], True)
        # Original unchanged
        self.assertEqual(base_constraints["port"], 5432)
        self.assertNotIn("debug", base_constraints)

    def test_feature_constraints_dynamic_evaluation(self):
        """Verify FeatureConstraints support dynamic evaluation."""
        base_fc = FeatureConstraints(
            required_features=["bluetooth"],
            checkout=True
        )
        
        # Dynamically extend with additional parameters
        extended = base_fc(timeout=30, custom_param="value")
        
        self.assertEqual(extended["required_features"], ["bluetooth"])
        self.assertTrue(extended["checkout"])
        self.assertEqual(extended["timeout"], 30)
        self.assertEqual(extended["custom_param"], "value")

    def test_merge_constraints_for_dynamic_composition(self):
        """Verify constraints can be merged dynamically for composition."""
        base = Constraints(timeout=30, retries=3)
        env = Constraints(host="test-server.local")
        runtime = Constraints(debug=True)
        
        combined = merge_constraints(base, env, runtime)
        
        self.assertEqual(combined["timeout"], 30)
        self.assertEqual(combined["retries"], 3)
        self.assertEqual(combined["host"], "test-server.local")
        self.assertEqual(combined["debug"], True)


class TestConstraintsPassedToGenerators(unittest.TestCase):
    """
    Tests verifying that constraints can be passed to generators in any scope.
    
    This tests the integration between:
    - Factory decorators with constraints parameter
    - ResourceOrigin with constraints_key
    - ConstraintsCatalog lookup during execution
    """

    def setUp(self):
        self.registry = reset_registry()
        self.catalog = reset_constraints_catalog()

    def test_resource_factory_with_constraints_parameter(self):
        """Verify resource factory can accept constraints parameter."""
        received_constraints = {}
        
        @registrations.resource_factory()
        def resource_with_constraints(constraints=None) -> typing.Generator[str, None, None]:
            if constraints:
                received_constraints.update(constraints)
            yield "test_resource"
        
        # Verify source is registered
        source = self.registry.lookup_resource_source(resource_with_constraints)
        self.assertIsNotNone(source)
        
        # Verify source signature includes constraints parameter
        sig = source.source_signature
        self.assertIn("constraints", sig.parameters)

    def test_integration_factory_with_constraints_parameter(self):
        """Verify integration factory can accept constraints parameter."""
        class TestIntegration(IntegrationCoupling):
            _name = None
            received_constraints = None
        
        @registrations.integration_factory()
        def integration_with_constraints(constraints=None) -> typing.Generator[TestIntegration, None, None]:
            integ = TestIntegration()
            integ.received_constraints = constraints
            yield integ
        
        # Verify source is registered
        source = self.registry.lookup_resource_source(integration_with_constraints)
        self.assertIsNotNone(source)
        
        # Verify source signature includes constraints parameter
        sig = source.source_signature
        self.assertIn("constraints", sig.parameters)

    def test_configuration_factory_with_constraints_parameter(self):
        """Verify configuration factory can accept constraints parameter."""
        class TestConfig(ConfigurationCoupling):
            received_constraints = None
        
        @registrations.configuration_factory()
        def config_with_constraints(constraints=None) -> typing.Generator[TestConfig, None, None]:
            config = TestConfig()
            config.received_constraints = constraints
            yield config
        
        # Verify source is registered
        source = self.registry.lookup_resource_source(config_with_constraints)
        self.assertIsNotNone(source)
        
        # Verify source signature includes constraints parameter
        sig = source.source_signature
        self.assertIn("constraints", sig.parameters)

    def test_parameter_attachment_with_constraints(self):
        """Verify @parameter attachment can pass constraints to source."""
        @registrations.resource_factory()
        def resource_accepting_constraints(constraints=None) -> typing.Generator[int, None, None]:
            yield 42
        
        test_constraints = {"env": "test", "timeout": 30}
        
        @attachments.parameter(
            resource_accepting_constraints,
            identifier="constrained_param",
            constraints=test_constraints
        )
        def test_function(constrained_param):
            return constrained_param
        
        # Verify origin is registered with constraints
        scope = f"{test_function.__module__}#{test_function.__name__}"
        self.assertTrue(
            self.registry._scope_tree_root.has_descendent_resource(scope, "constrained_param")
        )

    def test_origination_parameter_with_constraints(self):
        """Verify origination parameter() can pass constraints to source."""
        @registrations.resource_factory()
        def resource_with_constraints(constraints=None) -> typing.Generator[str, None, None]:
            yield "value"
        
        test_constraints = {"pool_size": 5, "timeout": 60}
        
        originations.parameter(
            resource_with_constraints,
            identifier="global_constrained",
            constraints=test_constraints
        )
        
        # Verify origin is registered
        module_name = __name__
        self.assertTrue(
            self.registry._scope_tree_root.has_descendent_resource(module_name, "global_constrained")
        )

    def test_constraints_stored_in_catalog_via_origin(self):
        """Verify constraints are stored in ConstraintsCatalog when origin is created."""
        @registrations.resource_factory()
        def resource_for_catalog_test(constraints=None) -> typing.Generator[int, None, None]:
            yield 100
        
        test_constraints = {"key1": "value1", "key2": 42}
        
        # Get the source and create origin directly to test the catalog storage
        source = self.registry.lookup_resource_source(resource_for_catalog_test)
        
        origin = ResourceOrigin(
            "test.catalog.scope",
            "catalog_test_param",
            ResourceLifespan.Package,
            source,
            constraints=test_constraints
        )
        
        # The constraints should be stored in the catalog
        # The key format is "{scope}:{identifier}"
        expected_key = "test.catalog.scope:catalog_test_param"
        
        looked_up = self.catalog.lookup_constraints(expected_key)
        self.assertIsNotNone(looked_up)
        self.assertEqual(looked_up["key1"], "value1")
        self.assertEqual(looked_up["key2"], 42)


class TestConstraintsAtDifferentScopes(unittest.TestCase):
    """
    Tests verifying constraints work at different scopes (Session, Package, Test).
    """

    def setUp(self):
        self.registry = reset_registry()
        self.catalog = reset_constraints_catalog()

    def test_constraints_at_session_scope(self):
        """Verify constraints work at session scope (IntegrationCoupling)."""
        class SessionIntegration(IntegrationCoupling):
            _name = None
            pass
        
        @registrations.integration_factory()
        def session_integration(constraints=None) -> typing.Generator[SessionIntegration, None, None]:
            yield SessionIntegration()
        
        session_constraints = {"session_key": "session_value"}
        
        # Get the source and create origin directly at session scope
        source = self.registry.lookup_resource_source(session_integration)
        
        origin = ResourceOrigin(
            "<session>",
            "session_param",
            ResourceLifespan.Session,
            source,
            constraints=session_constraints
        )
        
        # Register the origin
        self.registry.register_resource_origin("session_param", origin)
        
        # Verify origin is at session scope
        self.assertTrue(
            self.registry._scope_tree_root.has_descendent_resource("<session>", "session_param")
        )
        
        # Verify constraints are stored
        looked_up = self.catalog.lookup_constraints("<session>:session_param")
        self.assertIsNotNone(looked_up)
        self.assertEqual(looked_up["session_key"], "session_value")

    def test_constraints_at_package_scope(self):
        """Verify constraints work at package scope."""
        @registrations.resource_factory()
        def package_resource(constraints=None) -> typing.Generator[str, None, None]:
            yield "package_value"
        
        package_constraints = {"package_key": "package_value"}
        
        # Get the source and create origin directly at package scope
        source = self.registry.lookup_resource_source(package_resource)
        
        origin = ResourceOrigin(
            "test.package.scope",
            "package_param",
            ResourceLifespan.Package,
            source,
            constraints=package_constraints
        )
        
        # Register the origin
        self.registry.register_resource_origin("package_param", origin)
        
        # Verify origin is at package scope
        self.assertTrue(
            self.registry._scope_tree_root.has_descendent_resource("test.package.scope", "package_param")
        )
        
        # Verify constraints are stored
        looked_up = self.catalog.lookup_constraints("test.package.scope:package_param")
        self.assertIsNotNone(looked_up)
        self.assertEqual(looked_up["package_key"], "package_value")

    def test_constraints_at_test_scope(self):
        """Verify constraints work at test scope (via @parameter attachment)."""
        @registrations.resource_factory()
        def test_resource(constraints=None) -> typing.Generator[int, None, None]:
            yield 42
        
        test_constraints = {"test_key": "test_value"}
        
        # Get the source and create origin directly at test scope
        source = self.registry.lookup_resource_source(test_resource)
        
        test_scope = "test.module#my_test_function"
        origin = ResourceOrigin(
            test_scope,
            "test_param",
            ResourceLifespan.Test,
            source,
            constraints=test_constraints
        )
        
        # Register the origin
        self.registry.register_resource_origin("test_param", origin)
        
        # Verify origin is at test scope
        self.assertTrue(
            self.registry._scope_tree_root.has_descendent_resource(test_scope, "test_param")
        )
        
        # Verify constraints are stored
        looked_up = self.catalog.lookup_constraints(f"{test_scope}:test_param")
        self.assertIsNotNone(looked_up)
        self.assertEqual(looked_up["test_key"], "test_value")


class TestConstraintsValidation(unittest.TestCase):
    """
    Tests verifying constraint validation behavior.
    """

    def setUp(self):
        self.registry = reset_registry()
        self.catalog = reset_constraints_catalog()

    def test_constraints_rejected_when_source_has_no_constraints_param(self):
        """Verify SemanticError when passing constraints to source without constraints param."""
        from ccai.errors.exceptions import SemanticError
        
        @registrations.resource_factory()
        def resource_no_constraints() -> typing.Generator[int, None, None]:
            yield 42
        
        with self.assertRaises(SemanticError):
            @attachments.parameter(
                resource_no_constraints,
                identifier="bad_param",
                constraints={"key": "value"}
            )
            def test_func(bad_param):
                return bad_param

    def test_constraints_accepted_when_source_has_constraints_param(self):
        """Verify constraints are accepted when source has constraints parameter."""
        @registrations.resource_factory()
        def resource_with_constraints(constraints=None) -> typing.Generator[int, None, None]:
            yield 42
        
        # Should not raise
        @attachments.parameter(
            resource_with_constraints,
            identifier="good_param",
            constraints={"key": "value"}
        )
        def test_func(good_param):
            return good_param
        
        # Verify registration succeeded
        scope = f"{test_func.__module__}#{test_func.__name__}"
        self.assertTrue(
            self.registry._scope_tree_root.has_descendent_resource(scope, "good_param")
        )


class TestResourceOriginConstraintsKey(unittest.TestCase):
    """
    Tests verifying ResourceOrigin correctly stores and exposes constraints_key.
    """

    def setUp(self):
        self.registry = reset_registry()
        self.catalog = reset_constraints_catalog()

    def test_resource_origin_has_constraints_key_when_constraints_provided(self):
        """Verify ResourceOrigin has constraints_key when constraints are provided."""
        @registrations.resource_factory()
        def resource_func(constraints=None) -> typing.Generator[str, None, None]:
            yield "test"
        
        source = self.registry.lookup_resource_source(resource_func)
        
        test_constraints = {"key": "value"}
        origin = ResourceOrigin(
            "test.scope",
            "test_id",
            ResourceLifespan.Package,
            source,
            constraints=test_constraints
        )
        
        self.assertIsNotNone(origin.constraints_key)
        self.assertEqual(origin.constraints_key, "test.scope:test_id")

    def test_resource_origin_has_no_constraints_key_when_no_constraints(self):
        """Verify ResourceOrigin has no constraints_key when no constraints provided."""
        @registrations.resource_factory()
        def resource_func(constraints=None) -> typing.Generator[str, None, None]:
            yield "test"
        
        source = self.registry.lookup_resource_source(resource_func)
        
        origin = ResourceOrigin(
            "test.scope",
            "test_id",
            ResourceLifespan.Package,
            source,
            constraints=None
        )
        
        self.assertIsNone(origin.constraints_key)

    def test_resource_origin_describe_source_includes_constraints(self):
        """Verify describe_source includes constraints information."""
        @registrations.resource_factory()
        def resource_func(constraints=None) -> typing.Generator[str, None, None]:
            yield "test"
        
        source = self.registry.lookup_resource_source(resource_func)
        
        test_constraints = {"key": "value"}
        origin = ResourceOrigin(
            "test.scope",
            "test_id",
            ResourceLifespan.Package,
            source,
            constraints=test_constraints
        )
        
        description = origin.describe_source()
        self.assertIn("constraints", description)
        self.assertIn("test.scope:test_id", description)


class TestGenerateCallWithConstraints(unittest.TestCase):
    """
    Tests verifying ResourceOrigin.generate_call correctly handles constraints.
    """

    def setUp(self):
        self.registry = reset_registry()
        self.catalog = reset_constraints_catalog()

    def test_generate_call_includes_constraints_when_provided(self):
        """Verify generate_call includes constraints parameter when constraints exist."""
        @registrations.resource_factory()
        def resource_func(constraints=None) -> typing.Generator[str, None, None]:
            yield "test"
        
        source = self.registry.lookup_resource_source(resource_func)
        
        test_constraints = {"key": "value"}
        origin = ResourceOrigin(
            "test.scope",
            "test_id",
            ResourceLifespan.Package,
            source,
            constraints=test_constraints
        )
        
        call_str = origin.generate_call(constraints=test_constraints)
        self.assertIn("constraints", call_str)

    def test_generate_call_excludes_constraints_when_none(self):
        """Verify generate_call excludes constraints parameter when no constraints."""
        @registrations.resource_factory()
        def resource_func(constraints=None) -> typing.Generator[str, None, None]:
            yield "test"
        
        source = self.registry.lookup_resource_source(resource_func)
        
        origin = ResourceOrigin(
            "test.scope",
            "test_id",
            ResourceLifespan.Package,
            source,
            constraints=None
        )
        
        call_str = origin.generate_call(constraints=None)
        self.assertNotIn("constraints", call_str)


if __name__ == "__main__":
    unittest.main()
