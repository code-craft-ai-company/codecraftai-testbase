
from typing import Generator

from automojo import testbase
from automojo.testbase.coupling.integrationcoupling import IntegrationCoupling
from automojo.testbase.coupling.configurationcoupling import ConfigurationCoupling


class Landscape:
    """
    Test Landscape class.
    """


class TestConfigurationCoupling(ConfigurationCoupling):
    """
    Test Configuration coupling class.
    """

    attach_to_framework_called = False
    attach_to_environment_called = False

    @classmethod
    def attach_to_framework(cls, **kwargs):
        """
            This API is called so that the ConfigurationCoupling can attach to the test framework and participate with
            registration processes.  This allows the framework to ignore the bringing-up of couplings that are not being
            included by a test.
        """
        cls.attach_to_framework_called = True
        return

    @classmethod
    def attach_to_environment(cls, **kwargs):
        """
            This API is called so that the ConfigurationCoupling can process configuration information.  The :class:`ConfigurationCoupling`
            will verify that it has a valid environment and configuration to run in.

            :raises :class:`automojo.errors.exceptions.AKitMissingConfigError`, :class:`automojo.errors.exceptions.ConfigurationError`:
        """
        cls.attach_to_environment_called = True
        return


class TestIntegrationCoupling(IntegrationCoupling):
    """
    Test Integration coupling class.
    """

    attach_to_framework_called = False
    attach_to_environment_called = False

    @classmethod
    def attach_to_framework(cls, **kwargs):
        """
            This API is called so that the IntegrationCoupling can attach to the test framework and participate with
            registration processes.  This allows the framework to ignore the bringing-up of couplings that are not being
            included by a test.
        """
        cls.attach_to_framework_called = True
        return

    @classmethod
    def attach_to_environment(cls, **kwargs):
        """
            This API is called so that the IntegrationCoupling can process configuration information.  The :class:`IntegrationCoupling`
            will verify that it has a valid environment and configuration to run in.

            :raises :class:`automojo.errors.exceptions.AKitMissingConfigError`, :class:`automojo.errors.exceptions.ConfigurationError`:
        """
        cls.attach_to_environment_called = True
        return


@testbase.register.resource_factory()
def create_landscape(constraints={}) -> Generator[Landscape, None, None]:
    lscape = Landscape()
    yield lscape


@testbase.register.integration_factory()
def create_testintegration_coupling() -> Generator[TestIntegrationCoupling, None, None]:
    test_coupling = TestIntegrationCoupling()
    yield test_coupling


@testbase.factory.resource()
def create_blah(constraints={}):
    yield "blah"

