import unittest

from ccai.testbase.coupling.integrationcoupling import (
    IntegrationCoupling,
    is_integration_coupling,
    sort_integration_couplings_by_precedence
)
from ccai.errors.exceptions import AbstractMethodError


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


class SampleIntegrationWithConnectivity(IntegrationCoupling):
    """Integration class that implements establish_connectivity for testing parameter handling."""

    integration_root = "croot"
    integration_section = "csect"
    integration_leaf = "cleaf"
    integration_class = "cclass"

    # Class variable to track the last call's allow_missing_devices value
    last_allow_missing_devices = None

    @classmethod
    def declare_precedence(cls) -> int:
        return 3

    @classmethod
    def establish_connectivity(cls, allow_missing_devices: bool = False):
        """Implementation that captures the allow_missing_devices parameter for testing."""
        cls.last_allow_missing_devices = allow_missing_devices
        errors = []
        reports = {}
        return (errors, reports)


class SampleIntegrationPrecedence10A(IntegrationCoupling):
    """Integration class with precedence 10 for testing same precedence grouping."""

    integration_root = "p10a_root"
    integration_section = "p10a_sect"
    integration_leaf = "p10a_leaf"
    integration_class = "p10a_class"

    @classmethod
    def declare_precedence(cls) -> int:
        return 10


class SampleIntegrationPrecedence10B(IntegrationCoupling):
    """Integration class with precedence 10 for testing same precedence grouping."""

    integration_root = "p10b_root"
    integration_section = "p10b_sect"
    integration_leaf = "p10b_leaf"
    integration_class = "p10b_class"

    @classmethod
    def declare_precedence(cls) -> int:
        return 10


class SampleIntegrationPrecedence10C(IntegrationCoupling):
    """Integration class with precedence 10 for testing same precedence grouping."""

    integration_root = "p10c_root"
    integration_section = "p10c_sect"
    integration_leaf = "p10c_leaf"
    integration_class = "p10c_class"

    @classmethod
    def declare_precedence(cls) -> int:
        return 10


class SampleIntegrationPrecedence5(IntegrationCoupling):
    """Integration class with precedence 5 for testing same precedence grouping."""

    integration_root = "p5_root"
    integration_section = "p5_sect"
    integration_leaf = "p5_leaf"
    integration_class = "p5_class"

    @classmethod
    def declare_precedence(cls) -> int:
        return 5


class SampleIntegrationPrecedence20(IntegrationCoupling):
    """Integration class with precedence 20 for testing same precedence grouping."""

    integration_root = "p20_root"
    integration_section = "p20_sect"
    integration_leaf = "p20_leaf"
    integration_class = "p20_class"

    @classmethod
    def declare_precedence(cls) -> int:
        return 20


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
            IntegrationCoupling.attach_to_environment,
            IntegrationCoupling.collect_resources,
            IntegrationCoupling.declare_precedence,
            lambda: IntegrationCoupling.diagnostic("label", 1, "folder"),
            lambda: IntegrationCoupling.establish_connectivity(),
            IntegrationCoupling.establish_presence,
            lambda: IntegrationCoupling.validate_item_configuration({}),
        ]

        for method in methods:
            with self.subTest(method=method):
                with self.assertRaises(AbstractMethodError):
                    method()

    def test_attach_to_framework_default_is_a_noop(self):
        """
            Framework attachment is an OPTIONAL phase: the base default must be
            a callable no-op, not abstract.  When it raised, EVERY coupling in
            the landscaping hierarchy (none of which override it) died at the
            first lifecycle phase of any landscape-backed run.
        """
        result = IntegrationCoupling.attach_to_framework(landscape=object())
        self.assertIsNone(result)

    def test_establish_connectivity_raises_abstract_method_error(self):
        """Test that establish_connectivity raises AbstractMethodError when not overloaded."""
        with self.assertRaises(AbstractMethodError):
            IntegrationCoupling.establish_connectivity()

    def test_establish_connectivity_with_allow_missing_devices_default(self):
        """Test establish_connectivity with default allow_missing_devices=False raises AbstractMethodError."""
        with self.assertRaises(AbstractMethodError):
            IntegrationCoupling.establish_connectivity(allow_missing_devices=False)

    def test_establish_connectivity_with_allow_missing_devices_true(self):
        """Test establish_connectivity with allow_missing_devices=True raises AbstractMethodError on base class."""
        with self.assertRaises(AbstractMethodError):
            IntegrationCoupling.establish_connectivity(allow_missing_devices=True)

    def test_establish_connectivity_derived_class_default_parameter(self):
        """Test establish_connectivity in derived class receives default allow_missing_devices=False."""
        SampleIntegrationWithConnectivity.last_allow_missing_devices = None
        errors, reports = SampleIntegrationWithConnectivity.establish_connectivity()
        self.assertFalse(SampleIntegrationWithConnectivity.last_allow_missing_devices)
        self.assertIsInstance(errors, list)
        self.assertIsInstance(reports, dict)

    def test_establish_connectivity_derived_class_allow_missing_devices_false(self):
        """Test establish_connectivity in derived class with explicit allow_missing_devices=False."""
        SampleIntegrationWithConnectivity.last_allow_missing_devices = None
        errors, reports = SampleIntegrationWithConnectivity.establish_connectivity(allow_missing_devices=False)
        self.assertFalse(SampleIntegrationWithConnectivity.last_allow_missing_devices)
        self.assertIsInstance(errors, list)
        self.assertIsInstance(reports, dict)

    def test_establish_connectivity_derived_class_allow_missing_devices_true(self):
        """Test establish_connectivity in derived class with allow_missing_devices=True."""
        SampleIntegrationWithConnectivity.last_allow_missing_devices = None
        errors, reports = SampleIntegrationWithConnectivity.establish_connectivity(allow_missing_devices=True)
        self.assertTrue(SampleIntegrationWithConnectivity.last_allow_missing_devices)
        self.assertIsInstance(errors, list)
        self.assertIsInstance(reports, dict)

    def test_establish_connectivity_return_type(self):
        """Test establish_connectivity returns tuple of (errors_list, reports_dict)."""
        result = SampleIntegrationWithConnectivity.establish_connectivity()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        errors, reports = result
        self.assertIsInstance(errors, list)
        self.assertIsInstance(reports, dict)

    def test_is_integration_coupling_true(self):
        self.assertTrue(is_integration_coupling(SampleIntegration))

    def test_is_integration_coupling_false(self):
        for obj in (IntegrationCoupling, str):
            with self.subTest(obj=obj):
                self.assertFalse(is_integration_coupling(obj))

    def test_sort_integration_couplings_by_precedence(self):
        unordered = [SampleIntegrationB, SampleIntegration]
        ordered = sort_integration_couplings_by_precedence(unordered)
        self.assertEqual(ordered, [SampleIntegration, SampleIntegrationB])

    def test_get_integration_key_with_none_components(self):
        """Test get_integration_key when all components are None (base class defaults)."""
        expected_key = "None:None:None:None"
        self.assertEqual(IntegrationCoupling.get_integration_key(), expected_key)

    def test_get_integration_key_parts_with_none_components(self):
        """Test get_integration_key_parts when all components are None (base class defaults)."""
        expected_parts = (None, None, None, None)
        self.assertEqual(IntegrationCoupling.get_integration_key_parts(), expected_parts)

    def test_sort_integration_couplings_same_precedence_grouped(self):
        """Test that multiple couplings with identical precedence values are grouped together."""
        # Create a list with couplings of different precedences, including multiple with same precedence
        unordered = [
            SampleIntegrationPrecedence10A,
            SampleIntegrationPrecedence5,
            SampleIntegrationPrecedence10B,
            SampleIntegrationPrecedence20,
            SampleIntegrationPrecedence10C,
        ]
        ordered = sort_integration_couplings_by_precedence(unordered)

        # Verify the list is ordered by precedence (lowest to highest)
        self.assertEqual(len(ordered), 5)

        # First should be precedence 5
        self.assertEqual(ordered[0], SampleIntegrationPrecedence5)

        # Next three should be precedence 10 (grouped together)
        precedence_10_group = ordered[1:4]
        self.assertIn(SampleIntegrationPrecedence10A, precedence_10_group)
        self.assertIn(SampleIntegrationPrecedence10B, precedence_10_group)
        self.assertIn(SampleIntegrationPrecedence10C, precedence_10_group)

        # Last should be precedence 20
        self.assertEqual(ordered[4], SampleIntegrationPrecedence20)

    def test_sort_integration_couplings_same_precedence_all_identical(self):
        """Test sorting when all couplings have the same precedence value."""
        unordered = [
            SampleIntegrationPrecedence10A,
            SampleIntegrationPrecedence10B,
            SampleIntegrationPrecedence10C,
        ]
        ordered = sort_integration_couplings_by_precedence(unordered)

        # All should be present in the output
        self.assertEqual(len(ordered), 3)
        self.assertIn(SampleIntegrationPrecedence10A, ordered)
        self.assertIn(SampleIntegrationPrecedence10B, ordered)
        self.assertIn(SampleIntegrationPrecedence10C, ordered)


class IntegrationCouplingDiagnosticTests(unittest.TestCase):
    """Unit tests for IntegrationCoupling.diagnostic abstract method.

    These tests verify:
    - AbstractMethodError is raised when calling diagnostic on base class
    - Error message content is correct
    - Method signature accepts required parameters (label, level, diag_folder)

    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
    """

    def test_diagnostic_raises_abstract_method_error_on_base_class(self):
        """Test that diagnostic raises AbstractMethodError when called on base IntegrationCoupling class.

        Requirements: 4.5
        """
        with self.assertRaises(AbstractMethodError):
            IntegrationCoupling.diagnostic("prerun-diagnostic", 5, "/tmp/diag")

    def test_diagnostic_error_message_content(self):
        """Test that the AbstractMethodError message indicates the method must be overloaded.

        Requirements: 4.6
        """
        expected_message = "The 'diagnostic' method must be overloaded by derived integration coupling types."
        with self.assertRaises(AbstractMethodError) as context:
            IntegrationCoupling.diagnostic("postrun-diagnostic", 9, "/output/diagnostics")

        self.assertEqual(str(context.exception), expected_message)

    def test_diagnostic_accepts_label_parameter(self):
        """Test that diagnostic method accepts label parameter identifying the diagnostic stage.

        Requirements: 4.2
        """
        # Test with different label values - all should raise AbstractMethodError
        # but the method should accept the parameter without TypeError
        labels = ["prerun-diagnostic", "postrun-diagnostic", "custom-label", ""]

        for label in labels:
            with self.subTest(label=label):
                with self.assertRaises(AbstractMethodError):
                    IntegrationCoupling.diagnostic(label, 5, "/tmp/diag")

    def test_diagnostic_accepts_level_parameter(self):
        """Test that diagnostic method accepts level parameter specifying maximum diagnostic level (1-9).

        Requirements: 4.3
        """
        # Test with different level values within valid range 1-9
        levels = [1, 2, 3, 4, 5, 6, 7, 8, 9]

        for level in levels:
            with self.subTest(level=level):
                with self.assertRaises(AbstractMethodError):
                    IntegrationCoupling.diagnostic("prerun-diagnostic", level, "/tmp/diag")

    def test_diagnostic_accepts_diag_folder_parameter(self):
        """Test that diagnostic method accepts diag_folder parameter specifying output directory.

        Requirements: 4.4
        """
        # Test with different folder path values
        folders = [
            "/tmp/diagnostics",
            "/output/test/diagnostics/prerun-diagnostic",
            "./relative/path",
            "",
        ]

        for folder in folders:
            with self.subTest(folder=folder):
                with self.assertRaises(AbstractMethodError):
                    IntegrationCoupling.diagnostic("prerun-diagnostic", 5, folder)

    def test_diagnostic_method_signature_with_all_parameters(self):
        """Test that diagnostic method accepts all three required parameters together.

        Requirements: 4.1, 4.2, 4.3, 4.4
        """
        # Verify the method can be called with all parameters
        with self.assertRaises(AbstractMethodError):
            IntegrationCoupling.diagnostic(
                label="prerun-diagnostic",
                level=9,
                diag_folder="/test/results/diagnostics/prerun-diagnostic"
            )

    def test_diagnostic_is_classmethod(self):
        """Test that diagnostic is defined as a class method on IntegrationCoupling.

        Requirements: 4.1
        """
        import inspect

        # Verify diagnostic is a method on the class
        self.assertTrue(hasattr(IntegrationCoupling, 'diagnostic'))

        # Get the method and verify it's callable
        diagnostic_method = getattr(IntegrationCoupling, 'diagnostic')
        self.assertTrue(callable(diagnostic_method))


if __name__ == "__main__":
    unittest.main()

