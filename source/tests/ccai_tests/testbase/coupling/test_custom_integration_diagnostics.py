"""
.. module:: test_custom_integration_diagnostics
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Integration tests for custom integration coupling diagnostic implementations.

.. moduleauthor:: CodeCraftX

These integration tests verify that custom integration couplings can properly
implement the diagnostic method according to the framework requirements.

Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
"""

import json
import os
import tempfile
import unittest

from ccai.testbase.coupling.integrationcoupling import IntegrationCoupling
from ccai.testbase.diagnostics import DiagnosticLabel


class CustomDiagnosticIntegration(IntegrationCoupling):
    """
    A custom integration coupling that implements diagnostic capture for testing.
    
    This class demonstrates proper implementation of the diagnostic method
    according to framework requirements:
    - Creates integration-specific subfolder (Requirement 12.2)
    - Respects diagnostic level parameter (Requirement 12.3)
    - Writes diagnostic files to subfolder (Requirement 12.4)
    - Handles errors internally (Requirement 12.5)
    
    Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
    """
    
    integration_root = "custom"
    integration_section = "diagnostic"
    integration_leaf = "test"
    integration_class = "CustomDiagnosticIntegration"
    
    # Class-level tracking for verification
    diagnostic_calls = []
    files_written = []
    errors_caught = []
    
    @classmethod
    def reset_tracking(cls):
        """Reset all tracking data between tests."""
        cls.diagnostic_calls = []
        cls.files_written = []
        cls.errors_caught = []
    
    @classmethod
    def declare_precedence(cls) -> int:
        return 1
    
    @classmethod
    def attach_to_framework(cls, **kwargs):
        pass
    
    @classmethod
    def attach_to_environment(cls, **kwargs):
        pass
    
    @classmethod
    def collect_resources(cls):
        pass
    
    @classmethod
    def establish_connectivity(cls, allow_missing_devices=False):
        return ([], {})
    
    @classmethod
    def establish_presence(cls):
        return ([], {})
    
    @classmethod
    def validate_item_configuration(cls, item_info):
        return ([], [])
    
    @classmethod
    def diagnostic(cls, label: str, level: int, diag_folder: str):
        """
        Capture diagnostic information for the custom integration.
        
        This implementation demonstrates proper diagnostic capture:
        1. Creates integration-specific subfolder
        2. Respects diagnostic level for verbosity control
        3. Writes diagnostic files to the subfolder
        4. Handles errors internally
        
        :param label: The diagnostic stage label (e.g., "prerun-diagnostic")
        :param level: The diagnostic level (1-9) controlling verbosity
        :param diag_folder: The output folder for diagnostic files
        
        Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
        """
        # Track the call for verification
        cls.diagnostic_calls.append({
            'label': label,
            'level': level,
            'diag_folder': diag_folder
        })
        
        try:
            # Requirement 12.2: Create integration-specific subfolder
            integration_folder = os.path.join(diag_folder, "custom_diagnostic_integration")
            os.makedirs(integration_folder, exist_ok=True)
            
            # Requirement 12.3: Respect diagnostic level parameter
            # Level 1-3: Basic diagnostics
            if level >= 1:
                basic_diag = {
                    'label': label,
                    'level': level,
                    'status': 'active'
                }
                basic_file = os.path.join(integration_folder, "basic_status.json")
                with open(basic_file, 'w') as f:
                    json.dump(basic_diag, f, indent=2)
                cls.files_written.append(basic_file)
            
            # Level 4-6: Standard diagnostics
            if level >= 4:
                standard_diag = {
                    'label': label,
                    'level': level,
                    'configuration': {
                        'integration_root': cls.integration_root,
                        'integration_section': cls.integration_section,
                        'integration_leaf': cls.integration_leaf,
                        'integration_class': cls.integration_class
                    }
                }
                standard_file = os.path.join(integration_folder, "standard_config.json")
                with open(standard_file, 'w') as f:
                    json.dump(standard_diag, f, indent=2)
                cls.files_written.append(standard_file)
            
            # Level 7-9: Detailed diagnostics
            if level >= 7:
                detailed_diag = {
                    'label': label,
                    'level': level,
                    'detailed_info': {
                        'integration_key': cls.get_integration_key(),
                        'precedence': cls.declare_precedence(),
                        'diagnostic_folder': diag_folder
                    }
                }
                detailed_file = os.path.join(integration_folder, "detailed_info.json")
                with open(detailed_file, 'w') as f:
                    json.dump(detailed_diag, f, indent=2)
                cls.files_written.append(detailed_file)
                
        except Exception as err:
            # Requirement 12.5: Handle errors internally
            cls.errors_caught.append(str(err))
            # Do not re-raise - errors should not propagate to test framework


class ErrorHandlingDiagnosticIntegration(IntegrationCoupling):
    """
    A custom integration coupling that tests error handling in diagnostic capture.
    
    This class is designed to trigger errors during diagnostic capture to verify
    that errors are handled internally and do not propagate.
    
    Requirement: 12.5
    """
    
    integration_root = "error"
    integration_section = "handling"
    integration_leaf = "test"
    integration_class = "ErrorHandlingDiagnosticIntegration"
    
    # Control flag to trigger errors
    should_raise_error = False
    errors_caught = []
    
    @classmethod
    def reset_tracking(cls):
        cls.should_raise_error = False
        cls.errors_caught = []
    
    @classmethod
    def declare_precedence(cls) -> int:
        return 1
    
    @classmethod
    def attach_to_framework(cls, **kwargs):
        pass
    
    @classmethod
    def attach_to_environment(cls, **kwargs):
        pass
    
    @classmethod
    def collect_resources(cls):
        pass
    
    @classmethod
    def establish_connectivity(cls, allow_missing_devices=False):
        return ([], {})
    
    @classmethod
    def establish_presence(cls):
        return ([], {})
    
    @classmethod
    def validate_item_configuration(cls, item_info):
        return ([], [])
    
    @classmethod
    def diagnostic(cls, label: str, level: int, diag_folder: str):
        """
        Diagnostic implementation that handles errors internally.
        
        Requirement: 12.5
        """
        try:
            if cls.should_raise_error:
                raise RuntimeError("Simulated diagnostic error")
            
            # Normal diagnostic capture
            integration_folder = os.path.join(diag_folder, "error_handling_integration")
            os.makedirs(integration_folder, exist_ok=True)
            
            diag_file = os.path.join(integration_folder, "diagnostic.txt")
            with open(diag_file, 'w') as f:
                f.write(f"label={label}\nlevel={level}\n")
                
        except Exception as err:
            # Requirement 12.5: Handle errors internally
            cls.errors_caught.append(str(err))
            # Do not re-raise


class CustomIntegrationDiagnosticTests(unittest.TestCase):
    """
    Integration tests for custom integration coupling diagnostic implementations.
    
    These tests verify that custom integration couplings properly implement
    the diagnostic method according to framework requirements.
    
    Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()
        CustomDiagnosticIntegration.reset_tracking()
        ErrorHandlingDiagnosticIntegration.reset_tracking()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()

    def test_custom_integration_overrides_diagnostic_method(self):
        """
        Test that custom integration coupling overrides the diagnostic class method.
        
        Verifies that the custom implementation can be called without raising
        AbstractMethodError, demonstrating proper method override.
        
        Requirement: 12.1
        """
        diag_folder = os.path.join(self.tempdir.name, "diagnostics")
        os.makedirs(diag_folder, exist_ok=True)
        
        # Should not raise AbstractMethodError
        CustomDiagnosticIntegration.diagnostic(
            label=DiagnosticLabel.PRERUN_DIAGNOSTIC,
            level=5,
            diag_folder=diag_folder
        )
        
        # Verify the method was called
        self.assertEqual(len(CustomDiagnosticIntegration.diagnostic_calls), 1)

    def test_custom_integration_creates_subfolder(self):
        """
        Test that custom integration creates an integration-specific subfolder.
        
        Verifies that the diagnostic method creates a subfolder within the
        provided diagnostic folder for storing integration-specific files.
        
        Requirement: 12.2
        """
        diag_folder = os.path.join(self.tempdir.name, "diagnostics", "prerun-diagnostic")
        os.makedirs(diag_folder, exist_ok=True)
        
        CustomDiagnosticIntegration.diagnostic(
            label=DiagnosticLabel.PRERUN_DIAGNOSTIC,
            level=5,
            diag_folder=diag_folder
        )
        
        # Verify integration-specific subfolder was created
        integration_folder = os.path.join(diag_folder, "custom_diagnostic_integration")
        self.assertTrue(os.path.exists(integration_folder))
        self.assertTrue(os.path.isdir(integration_folder))

    def test_custom_integration_respects_level_basic(self):
        """
        Test that custom integration respects diagnostic level 1-3 (basic).
        
        Verifies that at level 1-3, only basic diagnostic information is captured.
        
        Requirement: 12.3
        """
        diag_folder = os.path.join(self.tempdir.name, "diagnostics")
        os.makedirs(diag_folder, exist_ok=True)
        
        CustomDiagnosticIntegration.diagnostic(
            label=DiagnosticLabel.PRERUN_DIAGNOSTIC,
            level=3,
            diag_folder=diag_folder
        )
        
        integration_folder = os.path.join(diag_folder, "custom_diagnostic_integration")
        
        # Basic file should exist
        basic_file = os.path.join(integration_folder, "basic_status.json")
        self.assertTrue(os.path.exists(basic_file))
        
        # Standard and detailed files should NOT exist at level 3
        standard_file = os.path.join(integration_folder, "standard_config.json")
        detailed_file = os.path.join(integration_folder, "detailed_info.json")
        self.assertFalse(os.path.exists(standard_file))
        self.assertFalse(os.path.exists(detailed_file))

    def test_custom_integration_respects_level_standard(self):
        """
        Test that custom integration respects diagnostic level 4-6 (standard).
        
        Verifies that at level 4-6, basic and standard diagnostic information is captured.
        
        Requirement: 12.3
        """
        diag_folder = os.path.join(self.tempdir.name, "diagnostics")
        os.makedirs(diag_folder, exist_ok=True)
        
        CustomDiagnosticIntegration.diagnostic(
            label=DiagnosticLabel.PRERUN_DIAGNOSTIC,
            level=6,
            diag_folder=diag_folder
        )
        
        integration_folder = os.path.join(diag_folder, "custom_diagnostic_integration")
        
        # Basic and standard files should exist
        basic_file = os.path.join(integration_folder, "basic_status.json")
        standard_file = os.path.join(integration_folder, "standard_config.json")
        self.assertTrue(os.path.exists(basic_file))
        self.assertTrue(os.path.exists(standard_file))
        
        # Detailed file should NOT exist at level 6
        detailed_file = os.path.join(integration_folder, "detailed_info.json")
        self.assertFalse(os.path.exists(detailed_file))

    def test_custom_integration_respects_level_detailed(self):
        """
        Test that custom integration respects diagnostic level 7-9 (detailed).
        
        Verifies that at level 7-9, all diagnostic information is captured.
        
        Requirement: 12.3
        """
        diag_folder = os.path.join(self.tempdir.name, "diagnostics")
        os.makedirs(diag_folder, exist_ok=True)
        
        CustomDiagnosticIntegration.diagnostic(
            label=DiagnosticLabel.PRERUN_DIAGNOSTIC,
            level=9,
            diag_folder=diag_folder
        )
        
        integration_folder = os.path.join(diag_folder, "custom_diagnostic_integration")
        
        # All files should exist at level 9
        basic_file = os.path.join(integration_folder, "basic_status.json")
        standard_file = os.path.join(integration_folder, "standard_config.json")
        detailed_file = os.path.join(integration_folder, "detailed_info.json")
        
        self.assertTrue(os.path.exists(basic_file))
        self.assertTrue(os.path.exists(standard_file))
        self.assertTrue(os.path.exists(detailed_file))

    def test_custom_integration_writes_files_to_subfolder(self):
        """
        Test that custom integration writes diagnostic files to the subfolder.
        
        Verifies that diagnostic files are written to the integration-specific
        subfolder with correct content.
        
        Requirement: 12.4
        """
        diag_folder = os.path.join(self.tempdir.name, "diagnostics")
        os.makedirs(diag_folder, exist_ok=True)
        
        CustomDiagnosticIntegration.diagnostic(
            label=DiagnosticLabel.PRERUN_DIAGNOSTIC,
            level=9,
            diag_folder=diag_folder
        )
        
        # Verify files were written
        self.assertGreater(len(CustomDiagnosticIntegration.files_written), 0)
        
        # Verify all files exist and are in the integration subfolder
        integration_folder = os.path.join(diag_folder, "custom_diagnostic_integration")
        for file_path in CustomDiagnosticIntegration.files_written:
            self.assertTrue(os.path.exists(file_path))
            self.assertTrue(file_path.startswith(integration_folder))

    def test_custom_integration_writes_correct_content(self):
        """
        Test that custom integration writes correct content to diagnostic files.
        
        Verifies that the diagnostic files contain the expected information
        including label, level, and integration details.
        
        Requirement: 12.4
        """
        diag_folder = os.path.join(self.tempdir.name, "diagnostics")
        os.makedirs(diag_folder, exist_ok=True)
        
        CustomDiagnosticIntegration.diagnostic(
            label=DiagnosticLabel.PRERUN_DIAGNOSTIC,
            level=9,
            diag_folder=diag_folder
        )
        
        integration_folder = os.path.join(diag_folder, "custom_diagnostic_integration")
        
        # Verify basic status content
        basic_file = os.path.join(integration_folder, "basic_status.json")
        with open(basic_file, 'r') as f:
            basic_data = json.load(f)
        
        self.assertEqual(basic_data['label'], DiagnosticLabel.PRERUN_DIAGNOSTIC)
        self.assertEqual(basic_data['level'], 9)
        self.assertEqual(basic_data['status'], 'active')
        
        # Verify detailed info content
        detailed_file = os.path.join(integration_folder, "detailed_info.json")
        with open(detailed_file, 'r') as f:
            detailed_data = json.load(f)
        
        self.assertEqual(
            detailed_data['detailed_info']['integration_key'],
            CustomDiagnosticIntegration.get_integration_key()
        )

    def test_custom_integration_handles_errors_internally(self):
        """
        Test that custom integration handles errors internally without propagation.
        
        Verifies that errors during diagnostic capture are caught and handled
        internally, preventing propagation to the test framework.
        
        Requirement: 12.5
        """
        diag_folder = os.path.join(self.tempdir.name, "diagnostics")
        os.makedirs(diag_folder, exist_ok=True)
        
        # Enable error triggering
        ErrorHandlingDiagnosticIntegration.should_raise_error = True
        
        # Should not raise exception - error should be handled internally
        ErrorHandlingDiagnosticIntegration.diagnostic(
            label=DiagnosticLabel.PRERUN_DIAGNOSTIC,
            level=5,
            diag_folder=diag_folder
        )
        
        # Verify error was caught internally
        self.assertEqual(len(ErrorHandlingDiagnosticIntegration.errors_caught), 1)
        self.assertIn("Simulated diagnostic error", ErrorHandlingDiagnosticIntegration.errors_caught[0])

    def test_custom_integration_diagnostic_called_with_correct_parameters(self):
        """
        Test that diagnostic method is called with correct parameters.
        
        Verifies that the label, level, and diag_folder parameters are
        correctly passed to the diagnostic method.
        
        Requirements: 12.1, 12.2, 12.3, 12.4
        """
        diag_folder = os.path.join(self.tempdir.name, "diagnostics", "postrun-diagnostic")
        os.makedirs(diag_folder, exist_ok=True)
        
        CustomDiagnosticIntegration.diagnostic(
            label=DiagnosticLabel.POSTRUN_DIAGNOSTIC,
            level=7,
            diag_folder=diag_folder
        )
        
        # Verify call parameters
        self.assertEqual(len(CustomDiagnosticIntegration.diagnostic_calls), 1)
        call = CustomDiagnosticIntegration.diagnostic_calls[0]
        
        self.assertEqual(call['label'], DiagnosticLabel.POSTRUN_DIAGNOSTIC)
        self.assertEqual(call['level'], 7)
        self.assertEqual(call['diag_folder'], diag_folder)

    def test_custom_integration_prerun_and_postrun_labels(self):
        """
        Test that custom integration handles both prerun and postrun labels.
        
        Verifies that the diagnostic method correctly processes both
        PRERUN_DIAGNOSTIC and POSTRUN_DIAGNOSTIC labels.
        
        Requirements: 12.1, 12.4
        """
        prerun_folder = os.path.join(self.tempdir.name, "diagnostics", "prerun-diagnostic")
        postrun_folder = os.path.join(self.tempdir.name, "diagnostics", "postrun-diagnostic")
        os.makedirs(prerun_folder, exist_ok=True)
        os.makedirs(postrun_folder, exist_ok=True)
        
        # Call with prerun label
        CustomDiagnosticIntegration.diagnostic(
            label=DiagnosticLabel.PRERUN_DIAGNOSTIC,
            level=5,
            diag_folder=prerun_folder
        )
        
        # Call with postrun label
        CustomDiagnosticIntegration.diagnostic(
            label=DiagnosticLabel.POSTRUN_DIAGNOSTIC,
            level=5,
            diag_folder=postrun_folder
        )
        
        # Verify both calls were made
        self.assertEqual(len(CustomDiagnosticIntegration.diagnostic_calls), 2)
        
        # Verify files written to correct locations
        prerun_integration_folder = os.path.join(prerun_folder, "custom_diagnostic_integration")
        postrun_integration_folder = os.path.join(postrun_folder, "custom_diagnostic_integration")
        
        self.assertTrue(os.path.exists(prerun_integration_folder))
        self.assertTrue(os.path.exists(postrun_integration_folder))

    def test_custom_integration_multiple_calls_accumulate_files(self):
        """
        Test that multiple diagnostic calls accumulate files correctly.
        
        Verifies that calling diagnostic multiple times creates files
        in the appropriate locations without overwriting issues.
        
        Requirements: 12.2, 12.4
        """
        diag_folder = os.path.join(self.tempdir.name, "diagnostics")
        os.makedirs(diag_folder, exist_ok=True)
        
        # First call
        CustomDiagnosticIntegration.diagnostic(
            label=DiagnosticLabel.PRERUN_DIAGNOSTIC,
            level=9,
            diag_folder=diag_folder
        )
        
        first_call_files = len(CustomDiagnosticIntegration.files_written)
        
        # Second call (simulating postrun)
        CustomDiagnosticIntegration.diagnostic(
            label=DiagnosticLabel.POSTRUN_DIAGNOSTIC,
            level=9,
            diag_folder=diag_folder
        )
        
        # Verify files accumulated
        self.assertGreater(len(CustomDiagnosticIntegration.files_written), first_call_files)


if __name__ == "__main__":
    unittest.main()
