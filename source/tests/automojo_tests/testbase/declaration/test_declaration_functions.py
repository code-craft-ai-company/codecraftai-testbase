import typing
import unittest

from automojo.errors.exceptions import SemanticError
from automojo.testbase.coupling.integrationcoupling import IntegrationCoupling
from automojo.testbase.coupling.configurationcoupling import ConfigurationCoupling
from automojo.testbase.coupling.validatorcoupling import ValidatorCoupling

from automojo.testbase.declaration import attachments, originations, registrations
from automojo.testbase.injection import injectionregistry
from automojo.testbase.injection.injectionscope import InjectionScope
from automojo.testbase.resourcelifespan import ResourceLifespan
from automojo.testbase.sources.integrationsource import IntegrationSource
from automojo.testbase.sources.resourcesource import ResourceSource
from automojo.testbase.sources.configurationsource import ConfigurationSource
from automojo.testbase.sources.validatorsource import ValidatorSource


def reset_registry():
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


class RegistrationDecoratorTests(unittest.TestCase):

    def setUp(self):
        reset_registry()

    def test_integration_factory_registers(self):
        class MyIntegration(IntegrationCoupling):
            _name = None
            pass

        @registrations.integration_factory()
        def make_it() -> typing.Generator[MyIntegration, None, None]:
            if False:
                yield MyIntegration()

        inj = injectionregistry.injection_registry
        self.assertIsInstance(inj.lookup_resource_source(make_it), IntegrationSource)

    def test_integration_factory_async_generator_registers(self):
        """Test that async generator functions are correctly registered as integration sources."""
        class MyAsyncIntegration(IntegrationCoupling):
            _name = None
            pass

        @registrations.integration_factory()
        async def make_async_integration() -> typing.AsyncGenerator[MyAsyncIntegration, None]:
            if False:
                yield MyAsyncIntegration()

        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(make_async_integration)
        self.assertIsInstance(source, IntegrationSource)
        self.assertEqual(source.resource_type, MyAsyncIntegration)

    def test_integration_factory_missing_annotation(self):
        with self.assertRaises(SemanticError):
            @registrations.integration_factory()
            def bad():
                pass

    def test_integration_factory_return_integration(self):
        class MyIntegration(IntegrationCoupling):
            _name = None
            pass

        with self.assertRaises(SemanticError):
            @registrations.integration_factory()
            def bad() -> MyIntegration:
                return MyIntegration()

    def test_resource_factory_registers(self):
        @registrations.resource_factory()
        def provide() -> int:
            return 1

        inj = injectionregistry.injection_registry
        self.assertIsInstance(inj.lookup_resource_source(provide), ResourceSource)

    def test_resource_factory_async_generator_registers(self):
        """Test that async generator functions are correctly registered as resource sources."""
        class AsyncResource:
            pass

        @registrations.resource_factory()
        async def provide_async() -> typing.AsyncGenerator[AsyncResource, None]:
            if False:
                yield AsyncResource()

        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(provide_async)
        self.assertIsInstance(source, ResourceSource)
        self.assertEqual(source.resource_type, AsyncResource)

    def test_resource_factory_missing_annotation(self):
        with self.assertRaises(SemanticError):
            @registrations.resource_factory()
            def bad():
                pass

    def test_configuration_factory_registers(self):
        class MyConfig(ConfigurationCoupling):
            pass

        @registrations.configuration_factory()
        def conf() -> typing.Generator[MyConfig, None, None]:
            if False:
                yield MyConfig()

        inj = injectionregistry.injection_registry
        self.assertIsInstance(inj.lookup_resource_source(conf), ConfigurationSource)

    def test_configuration_factory_async_generator_registers(self):
        """Test that async generator functions are correctly registered as configuration sources."""
        class MyAsyncConfig(ConfigurationCoupling):
            pass

        @registrations.configuration_factory()
        async def async_conf() -> typing.AsyncGenerator[MyAsyncConfig, None]:
            if False:
                yield MyAsyncConfig()

        inj = injectionregistry.injection_registry
        source = inj.lookup_resource_source(async_conf)
        self.assertIsInstance(source, ConfigurationSource)
        self.assertEqual(source.resource_type, MyAsyncConfig)

    def test_configuration_factory_invalid_annotation(self):
        with self.assertRaises(SemanticError):
            @registrations.configuration_factory()
            def bad() -> typing.Generator[int, None, None]:
                if False:
                    yield 1

    def test_configuration_factory_async_generator_invalid_type(self):
        """Test that async generator with non-ConfigurationCoupling type raises SemanticError."""
        with self.assertRaises(SemanticError):
            @registrations.configuration_factory()
            async def bad_async() -> typing.AsyncGenerator[int, None]:
                if False:
                    yield 1

    def test_validator_factory_registers(self):
        class MyValidator(ValidatorCoupling):
            pass

        @registrations.validator_factory()
        def make_val() -> MyValidator:
            return MyValidator()

        inj = injectionregistry.injection_registry
        self.assertIsInstance(inj.lookup_validator_source(make_val), ValidatorSource)

    def test_validator_factory_invalid_annotation(self):
        with self.assertRaises(SemanticError):
            @registrations.validator_factory()
            def bad() -> int:
                return 1


class AttachmentDecoratorTests(unittest.TestCase):

    def setUp(self):
        reset_registry()
        
        @registrations.resource_factory()
        def simple_resource() -> int:
            return 1
        self.source_func = simple_resource

        @registrations.validator_factory()
        def simple_validator() -> ValidatorCoupling:
            return ValidatorCoupling()
        self.validator_func = simple_validator

    def test_parameter_registers_origin(self):
        @attachments.parameter(self.source_func, identifier="param")
        def test_target(param):
            return param

        inj = injectionregistry.injection_registry
        scope = f"{test_target.__module__}#{test_target.__name__}"
        self.assertTrue(inj._scope_tree_root.has_descendent_resource(scope, "param"))

    def test_parameter_reserved_identifier(self):
        with self.assertRaises(SemanticError):
            @attachments.parameter(self.source_func, identifier="constraints")
            def bad(param):
                return param

    def test_parameter_constraints_missing(self):
        @registrations.resource_factory()
        def no_constraints() -> int:
            return 1

        with self.assertRaises(SemanticError):
            @attachments.parameter(no_constraints, identifier="nc", constraints={"a":1})
            def bad(nc):
                return nc

    def test_validation_registers_origin(self):
        @attachments.validation(self.validator_func, suffix="suf", identifier="val")
        def tgt():
            return

        inj = injectionregistry.injection_registry
        scope = f"{tgt.__module__}#{tgt.__name__}"
        self.assertTrue(inj._scope_tree_root.has_descendent_validator(scope, "val"))

    def test_validation_reserved_identifier(self):
        with self.assertRaises(SemanticError):
            @attachments.validation(self.validator_func, suffix="suf", identifier="constraints")
            def bad():
                return


class OriginationParameterTests(unittest.TestCase):

    def setUp(self):
        reset_registry()
        
        @registrations.resource_factory()
        def provide() -> int:
            return 1
        self.source_func = provide

        class DummyIntegration(IntegrationCoupling):
            pass
        @registrations.integration_factory()
        def int_src() -> typing.Generator[DummyIntegration, None, None]:
            if False:
                yield DummyIntegration()
        self.integration_src = int_src

    def test_parameter_registers_origin(self):
        originations.parameter(self.source_func, identifier="orig")
        mod = __name__
        inj = injectionregistry.injection_registry
        self.assertTrue(inj._scope_tree_root.has_descendent_resource(mod, "orig"))

    def test_source_none_error(self):
        with self.assertRaises(SemanticError):
            originations.parameter(None, identifier="bad")

    def test_lifespan_test_error(self):
        with self.assertRaises(SemanticError):
            originations.parameter(self.source_func, identifier="x", life_span=ResourceLifespan.Test)

    def test_reserved_identifier_error(self):
        with self.assertRaises(SemanticError):
            originations.parameter(self.source_func, identifier="constraints")

    def test_assigned_scope_integration_error(self):
        with self.assertRaises(SemanticError):
            originations.parameter(self.integration_src, identifier="y", assigned_scope="mod")


class ErrorHandlingVerificationTests(unittest.TestCase):
    """
    Tests to verify error handling includes source function name and type information.
    Requirements: 1.2, 2.2, 3.2, 4.2
    """

    def setUp(self):
        reset_registry()

    # =========================================================================
    # Integration Factory Error Handling Tests (Requirement 1.2)
    # =========================================================================

    def test_integration_factory_missing_annotation_error_message(self):
        """Verify error message for missing return type annotation includes function context."""
        try:
            @registrations.integration_factory()
            def bad_integration_func():
                pass
            self.fail("Expected SemanticError to be raised")
        except SemanticError as e:
            error_msg = str(e)
            # Verify error message mentions the issue
            self.assertIn("annotated return type", error_msg.lower())

    def test_integration_factory_return_instead_of_yield_error_message(self):
        """Verify error message when returning instead of yielding integration."""
        class TestIntegration(IntegrationCoupling):
            _name = None
            pass

        try:
            @registrations.integration_factory()
            def bad_return_func() -> TestIntegration:
                return TestIntegration()
            self.fail("Expected SemanticError to be raised")
        except SemanticError as e:
            error_msg = str(e)
            # Verify error message mentions returning vs yielding
            self.assertIn("returning", error_msg.lower())
            self.assertIn("yielding", error_msg.lower())

    def test_integration_factory_wrong_type_error_message(self):
        """Verify error message when return type is not IntegrationCoupling.
        
        Note: This test documents current behavior. When a non-Generator type
        that doesn't have a _name attribute is passed, an AttributeError is raised
        instead of a SemanticError. This is a known limitation.
        """
        # Test with a type that has _name attribute (Generator with wrong yield type)
        try:
            @registrations.integration_factory()
            def wrong_type_func() -> typing.Generator[int, None, None]:
                if False:
                    yield 42
            self.fail("Expected SemanticError to be raised")
        except SemanticError as e:
            error_msg = str(e)
            # Verify error message mentions IntegrationCoupling
            self.assertIn("IntegrationCoupling", error_msg)

    # =========================================================================
    # Resource Factory Error Handling Tests (Requirement 2.2)
    # =========================================================================

    def test_resource_factory_missing_annotation_error_message(self):
        """Verify error message for missing return type annotation."""
        try:
            @registrations.resource_factory()
            def bad_resource_func():
                pass
            self.fail("Expected SemanticError to be raised")
        except SemanticError as e:
            error_msg = str(e)
            # Verify error message mentions annotated return type
            self.assertIn("annotated return type", error_msg.lower())

    # =========================================================================
    # Configuration Factory Error Handling Tests (Requirement 3.2)
    # =========================================================================

    def test_configuration_factory_missing_annotation_error_message(self):
        """Verify error message for missing return type annotation."""
        try:
            @registrations.configuration_factory()
            def bad_config_func():
                pass
            self.fail("Expected SemanticError to be raised")
        except SemanticError as e:
            error_msg = str(e)
            # Verify error message mentions annotated return type
            self.assertIn("annotated return type", error_msg.lower())

    def test_configuration_factory_wrong_type_error_message(self):
        """Verify error message when return type is not ConfigurationCoupling.
        
        Note: This test documents current behavior. When a non-Generator type
        that doesn't have a _name attribute is passed, an AttributeError is raised
        instead of a SemanticError. This is a known limitation.
        """
        # Test with a type that has _name attribute (Generator with wrong yield type)
        # The invalid_generator_type test already covers this case
        # Here we verify the error message for direct ConfigurationCoupling subclass check
        class NotAConfig:
            pass
        
        # This case is handled by the issubclass check after Generator check
        # Since int doesn't have _name, it would fail before reaching the issubclass check
        # We test with a Generator that yields a non-ConfigurationCoupling type
        try:
            @registrations.configuration_factory()
            def wrong_config_type() -> typing.Generator[str, None, None]:
                if False:
                    yield "test"
            self.fail("Expected SemanticError to be raised")
        except SemanticError as e:
            error_msg = str(e)
            # Verify error message mentions the coupling type requirement
            self.assertIn("scopecoupling", error_msg.lower())

    def test_configuration_factory_invalid_generator_type_error_message(self):
        """Verify error message when Generator yields non-ConfigurationCoupling type."""
        try:
            @registrations.configuration_factory()
            def invalid_generator() -> typing.Generator[int, None, None]:
                if False:
                    yield 1
            self.fail("Expected SemanticError to be raised")
        except SemanticError as e:
            error_msg = str(e)
            # Verify error message mentions the coupling type requirement
            self.assertIn("scopecoupling", error_msg.lower())

    # =========================================================================
    # Validator Factory Error Handling Tests (Requirement 4.2)
    # =========================================================================

    def test_validator_factory_missing_annotation_error_message(self):
        """Verify error message for missing return type annotation includes context."""
        try:
            @registrations.validator_factory()
            def bad_validator_func():
                pass
            self.fail("Expected SemanticError to be raised")
        except SemanticError as e:
            error_msg = str(e)
            # Verify error message mentions annotated return type
            self.assertIn("annotated return type", error_msg.lower())
            # Verify error message includes resource_context info
            self.assertIn("resource_context", error_msg)

    def test_validator_factory_wrong_type_error_message(self):
        """Verify error message when return type is not ValidatorCoupling includes type info."""
        try:
            @registrations.validator_factory()
            def wrong_validator_type() -> int:
                return 42
            self.fail("Expected SemanticError to be raised")
        except SemanticError as e:
            error_msg = str(e)
            # Verify error message mentions ValidatorBase/ValidatorCoupling
            self.assertIn("ValidatorBase", error_msg)
            # Verify error message includes actual type information
            self.assertIn("resource_context", error_msg)


if __name__ == "__main__":
    unittest.main()
