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

    def test_get_integration_key(self):
        expected_key = "iroot:isect:ileaf:iclass"
        self.assertEqual(SampleIntegration.get_integration_key(), expected_key)

    def test_get_integration_key_parts(self):
        expected_parts = ("iroot", "isect", "ileaf", "iclass")
        self.assertEqual(
            SampleIntegration.get_integration_key_parts(),
            expected_parts,
        )

    def test_abstract_methods_raise(self):
        """Ensure each abstract method raises ``AbstractMethodError``."""

        methods = [
            IntegrationCoupling.attach_to_framework,
            IntegrationCoupling.attach_to_environment,
            IntegrationCoupling.collect_resources,
            IntegrationCoupling.declare_precedence,
            lambda: IntegrationCoupling.diagnostic("label", 1, "folder"),
            IntegrationCoupling.establish_presence,
            lambda: IntegrationCoupling.validate_item_configuration({}),
        ]

        for method in methods:
            with self.subTest(method=method):
                with self.assertRaises(AbstractMethodError):
                    method()

    def test_is_integration_coupling_true(self):
        self.assertTrue(is_integration_coupling(SampleIntegration))

    def test_is_integration_coupling_false(self):
        for obj in (IntegrationCoupling, str):
            with self.subTest(obj=obj):
                self.assertFalse(is_integration_coupling(obj))

    def test_sort_integration_couplings_by_precedence(self):
        unordered = [SampleIntegrationB, SampleIntegration]
        ordered = sort_integration_couplings_by_precedence(None, unordered)
        self.assertEqual(ordered, [SampleIntegration, SampleIntegrationB])


if __name__ == "__main__":
    unittest.main()

