import typing
import unittest

from automojo.errors.exceptions import SemanticError
from automojo.testbase.coupling.integrationcoupling import IntegrationCoupling
from automojo.testbase.coupling.configurationcoupling import ConfigurationCoupling
from automojo.testbase.coupling.validatorcoupling import ValidatorCoupling

from automojo.testbase.declaration import attachments, originiations, registrations
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

    def test_configuration_factory_invalid_annotation(self):
        with self.assertRaises(SemanticError):
            @registrations.configuration_factory()
            def bad() -> typing.Generator[int, None, None]:
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
        originiations.parameter(self.source_func, identifier="orig")
        mod = __name__
        inj = injectionregistry.injection_registry
        self.assertTrue(inj._scope_tree_root.has_descendent_resource(mod, "orig"))

    def test_source_none_error(self):
        with self.assertRaises(SemanticError):
            originiations.parameter(None, identifier="bad")

    def test_lifespan_test_error(self):
        with self.assertRaises(SemanticError):
            originiations.parameter(self.source_func, identifier="x", life_span=ResourceLifespan.Test)

    def test_reserved_identifier_error(self):
        with self.assertRaises(SemanticError):
            originiations.parameter(self.source_func, identifier="constraints")

    def test_assigned_scope_integration_error(self):
        with self.assertRaises(SemanticError):
            originiations.parameter(self.integration_src, identifier="y", assigned_scope="mod")


if __name__ == "__main__":
    unittest.main()
