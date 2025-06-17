import unittest

from automojo.testbase.coupling.integrationcoupling import (
    IntegrationCoupling,
    is_integration_coupling,
    sort_integration_couplings_by_precedence
)
from automojo.errors.exceptions import AbstractMethodError


class SampleIntegration(IntegrationCoupling):
    """Simple integration class used for testing."""

    integration_root = "iroot"
    integration_section = "isect"
    integration_leaf = "ileaf"
    integration_class = "iclass"

    @classmethod
    def declare_precedence(cls) -> int:
        return 1


class SampleIntegrationB(IntegrationCoupling):
    integration_root = "broot"
    integration_section = "bsect"
    integration_leaf = "bleaf"
    integration_class = "bclass"

    @classmethod
    def declare_precedence(cls) -> int:
        return 2


class IntegrationCouplingTests(unittest.TestCase):

    def test_properties_default_false(self):
        ic = IntegrationCoupling()
        self.assertFalse(ic.connectivity_establish)
        self.assertFalse(ic.presence_establish)

    def test_integration_key_helpers(self):
        expected_key = "iroot:isect:ileaf:iclass"
        self.assertEqual(SampleIntegration.get_integration_key(), expected_key)

        expected_parts = ("iroot", "isect", "ileaf", "iclass")
        self.assertEqual(SampleIntegration.get_integration_key_parts(), expected_parts)

    def test_abstract_methods_raise(self):
        with self.assertRaises(AbstractMethodError):
            IntegrationCoupling.attach_to_framework()

        with self.assertRaises(AbstractMethodError):
            IntegrationCoupling.attach_to_environment()

        with self.assertRaises(AbstractMethodError):
            IntegrationCoupling.collect_resources()

        with self.assertRaises(AbstractMethodError):
            IntegrationCoupling.declare_precedence()

        with self.assertRaises(AbstractMethodError):
            IntegrationCoupling.diagnostic("label", 1, "folder")

        with self.assertRaises(AbstractMethodError):
            IntegrationCoupling.establish_presence()

        with self.assertRaises(AbstractMethodError):
            IntegrationCoupling.validate_item_configuration({})

    def test_is_integration_coupling(self):
        self.assertTrue(is_integration_coupling(SampleIntegration))
        self.assertFalse(is_integration_coupling(IntegrationCoupling))
        self.assertFalse(is_integration_coupling(str))

    def test_sort_integration_couplings_by_precedence(self):
        unordered = [SampleIntegrationB, SampleIntegration]
        ordered = sort_integration_couplings_by_precedence(None, unordered)
        self.assertEqual(ordered, [SampleIntegration, SampleIntegrationB])


if __name__ == "__main__":
    unittest.main()

