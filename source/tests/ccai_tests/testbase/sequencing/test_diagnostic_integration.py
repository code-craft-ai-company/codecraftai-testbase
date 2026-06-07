"""
.. module:: test_diagnostic_integration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Integration tests for end-to-end diagnostic capture functionality.

.. moduleauthor:: CodeCraftX

These integration tests verify the complete diagnostic capture flow from
TestJob through TestSequencer to IntegrationCoupling implementations.

Requirements: 5.1-5.5, 6.1-6.5
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from ccai.testbase.diagnostics import DiagnosticLabel
from ccai.testbase.coupling.integrationcoupling import IntegrationCoupling
from ccai.testbase.sequencing.testsequencer import TestSequencer
from ccai.testbase.testjob import TestJob


class TestIntegrationCoupling(IntegrationCoupling):
    """
    A test integration coupling that tracks diagnostic calls for verification.
    
    This class implements the diagnostic method to capture call information
    for integration testing purposes.
    """
    
    integration_root = "test"
    integration_section = "diagnostic"
    integration_leaf = "integration"
    integration_class = "TestIntegrationCoupling"
    
    # Class-level tracking for diagnostic calls
    diagnostic_calls = []
    diagnostic_files_written = []
    
    @classmethod
    def reset_tracking(cls):
        """Reset all tracking data between tests."""
        cls.diagnostic_calls = []
        cls.diagnostic_files_written = []
    
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
        Capture diagnostic information and track the call.
        
        :param label: The diagnostic stage label
        :param level: The diagnostic level (1-9)
        :param diag_folder: The output folder for diagnostics
        """
        cls.diagnostic_calls.append({
            'label': label,
            'level': level,
            'diag_folder': diag_folder
        })
        
        # Create integration-specific subfolder and write a diagnostic file
        if diag_folder and os.path.exists(os.path.dirname(diag_folder)):
            integration_folder = os.path.join(diag_folder, "test_integration")
            os.makedirs(integration_folder, exist_ok=True)
            
            diag_file = os.path.join(integration_folder, f"diagnostic_{label}.txt")
            with open(diag_file, 'w') as f:
                f.write(f"label={label}\nlevel={level}\n")
            
            cls.diagnostic_files_written.append(diag_file)


class SecondTestIntegrationCoupling(IntegrationCoupling):
    """
    A second test integration coupling to verify iteration over multiple integrations.
    """
    
    integration_root = "test"
    integration_section = "diagnostic"
    integration_leaf = "second"
    integration_class = "SecondTestIntegrationCoupling"
    
    diagnostic_calls = []
    
    @classmethod
    def reset_tracking(cls):
        cls.diagnostic_calls = []
    
    @classmethod
    def declare_precedence(cls) -> int:
        return 2
    
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
        cls.diagnostic_calls.append({
            'label': label,
            'level': level,
            'diag_folder': diag_folder
        })


class DiagnosticCaptureIntegrationTests(unittest.TestCase):
    """
    Integration tests for end-to-end diagnostic capture.
    
    These tests verify the complete flow from enabling diagnostics through
    runtime variables to the actual diagnostic method calls on integrations.
    
    Requirements: 5.1-5.5, 6.1-6.5
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        # Reset tracking data
        TestIntegrationCoupling.reset_tracking()
        SecondTestIntegrationCoupling.reset_tracking()

        # Create a TestSequencer instance
        self.sequencer = TestSequencer(
            jobtitle="integration_test_job",
            root=self.tempdir.name,
            includes=["ccai"],
            excludes=[],
            metafilters=[]
        )

        # Give the sequencer a controllable output context so diagnostic-dir
        # resolution is mockable and inspectable.
        self._diag_dir = os.path.join(self.tempdir.name, "diagnostics")
        os.makedirs(self._diag_dir, exist_ok=True)
        self.sequencer._output_context = MagicMock()
        self.sequencer._output_context.get_diagnostics_dir.return_value = self._diag_dir

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()

    @patch('ccai.testbase.sequencing.testsequencer.environment')
    def test_prerun_diagnostic_capture_end_to_end(self, mock_env):
        """
        Test end-to-end pre-run diagnostic capture with enabled diagnostics.

        Verifies that when pre-run diagnostics are enabled:
        1. The diagnostic method is called on all registered integrations
        2. The correct label (PRERUN_DIAGNOSTIC) is passed
        3. The diagnostic folder path is passed correctly

        Requirements: 5.1, 5.2, 5.3, 5.4
        """
        # Setup: Enable pre-run diagnostics
        mock_env.diagnostics_prerun_enabled.return_value = True
        diagnostic_path = os.path.join(self.tempdir.name, "diagnostics", "prerun-diagnostic")
        os.makedirs(diagnostic_path, exist_ok=True)
        self.sequencer.output_context.get_diagnostics_dir.return_value = diagnostic_path

        # Register test integrations
        self.sequencer._integrations = {
            "test_integration": TestIntegrationCoupling,
            "second_integration": SecondTestIntegrationCoupling
        }
        
        # Execute pre-run diagnostic capture
        self.sequencer.diagnostic_capture_pre_testrun(level=9)
        
        # Verify diagnostic was called on first integration
        self.assertEqual(len(TestIntegrationCoupling.diagnostic_calls), 1)
        call = TestIntegrationCoupling.diagnostic_calls[0]
        self.assertEqual(call['label'], DiagnosticLabel.PRERUN_DIAGNOSTIC)
        self.assertEqual(call['level'], 9)
        self.assertEqual(call['diag_folder'], diagnostic_path)
        
        # Verify diagnostic was called on second integration
        self.assertEqual(len(SecondTestIntegrationCoupling.diagnostic_calls), 1)
        call = SecondTestIntegrationCoupling.diagnostic_calls[0]
        self.assertEqual(call['label'], DiagnosticLabel.PRERUN_DIAGNOSTIC)
        self.assertEqual(call['level'], 9)
        self.assertEqual(call['diag_folder'], diagnostic_path)

    @patch('ccai.testbase.sequencing.testsequencer.environment')
    def test_postrun_diagnostic_capture_end_to_end(self, mock_env):
        """
        Test end-to-end post-run diagnostic capture with enabled diagnostics.

        Verifies that when post-run diagnostics are enabled:
        1. The diagnostic method is called on all registered integrations
        2. The correct label (POSTRUN_DIAGNOSTIC) is passed
        3. The diagnostic folder path is passed correctly

        Requirements: 6.1, 6.2, 6.3, 6.4
        """
        # Setup: Enable post-run diagnostics
        mock_env.diagnostics_postrun_enabled.return_value = True
        diagnostic_path = os.path.join(self.tempdir.name, "diagnostics", "postrun-diagnostic")
        os.makedirs(diagnostic_path, exist_ok=True)
        self.sequencer.output_context.get_diagnostics_dir.return_value = diagnostic_path

        # Register test integrations
        self.sequencer._integrations = {
            "test_integration": TestIntegrationCoupling,
            "second_integration": SecondTestIntegrationCoupling
        }
        
        # Execute post-run diagnostic capture
        self.sequencer.diagnostic_capture_post_testrun(level=9)
        
        # Verify diagnostic was called on first integration
        self.assertEqual(len(TestIntegrationCoupling.diagnostic_calls), 1)
        call = TestIntegrationCoupling.diagnostic_calls[0]
        self.assertEqual(call['label'], DiagnosticLabel.POSTRUN_DIAGNOSTIC)
        self.assertEqual(call['level'], 9)
        self.assertEqual(call['diag_folder'], diagnostic_path)
        
        # Verify diagnostic was called on second integration
        self.assertEqual(len(SecondTestIntegrationCoupling.diagnostic_calls), 1)
        call = SecondTestIntegrationCoupling.diagnostic_calls[0]
        self.assertEqual(call['label'], DiagnosticLabel.POSTRUN_DIAGNOSTIC)
        self.assertEqual(call['level'], 9)
        self.assertEqual(call['diag_folder'], diagnostic_path)

    @patch('ccai.testbase.sequencing.testsequencer.environment')
    def test_diagnostic_folders_created_by_integration(self, mock_env):
        """
        Test that diagnostic folders are created by integration couplings.

        Verifies that when diagnostics are captured:
        1. Integration-specific subfolders are created
        2. Diagnostic files are written to the correct location

        Requirements: 5.1, 5.3, 6.1, 6.3
        """
        # Setup: Enable pre-run diagnostics
        mock_env.diagnostics_prerun_enabled.return_value = True
        diagnostic_path = os.path.join(self.tempdir.name, "diagnostics", "prerun-diagnostic")
        os.makedirs(diagnostic_path, exist_ok=True)
        self.sequencer.output_context.get_diagnostics_dir.return_value = diagnostic_path

        # Register test integration
        self.sequencer._integrations = {
            "test_integration": TestIntegrationCoupling
        }
        
        # Execute pre-run diagnostic capture
        self.sequencer.diagnostic_capture_pre_testrun(level=9)
        
        # Verify integration subfolder was created
        integration_folder = os.path.join(diagnostic_path, "test_integration")
        self.assertTrue(os.path.exists(integration_folder))
        
        # Verify diagnostic file was written
        self.assertEqual(len(TestIntegrationCoupling.diagnostic_files_written), 1)
        diag_file = TestIntegrationCoupling.diagnostic_files_written[0]
        self.assertTrue(os.path.exists(diag_file))
        
        # Verify file content
        with open(diag_file, 'r') as f:
            content = f.read()
        self.assertIn("label=prerun-diagnostic", content)
        self.assertIn("level=9", content)

    @patch('ccai.testbase.sequencing.testsequencer.environment')
    def test_prerun_diagnostic_skipped_when_disabled(self, mock_env):
        """
        Test that pre-run diagnostic capture is skipped when disabled.

        Requirements: 5.5
        """
        # Setup: Disable pre-run diagnostics
        mock_env.diagnostics_prerun_enabled.return_value = False

        # Register test integration
        self.sequencer._integrations = {
            "test_integration": TestIntegrationCoupling
        }

        # Execute pre-run diagnostic capture
        self.sequencer.diagnostic_capture_pre_testrun(level=9)

        # Verify diagnostic was NOT called
        self.assertEqual(len(TestIntegrationCoupling.diagnostic_calls), 0)
        self.sequencer.output_context.get_diagnostics_dir.assert_not_called()

    @patch('ccai.testbase.sequencing.testsequencer.environment')
    def test_postrun_diagnostic_skipped_when_disabled(self, mock_env):
        """
        Test that post-run diagnostic capture is skipped when disabled.

        Requirements: 6.5
        """
        # Setup: Disable post-run diagnostics
        mock_env.diagnostics_postrun_enabled.return_value = False

        # Register test integration
        self.sequencer._integrations = {
            "test_integration": TestIntegrationCoupling
        }

        # Execute post-run diagnostic capture
        self.sequencer.diagnostic_capture_post_testrun(level=9)

        # Verify diagnostic was NOT called
        self.assertEqual(len(TestIntegrationCoupling.diagnostic_calls), 0)
        self.sequencer.output_context.get_diagnostics_dir.assert_not_called()

    @patch('ccai.testbase.sequencing.testsequencer.environment')
    def test_diagnostic_level_propagated_to_integrations(self, mock_env):
        """
        Test that diagnostic level is correctly propagated to all integrations.

        Requirements: 5.4, 6.4
        """
        # Setup: Enable both pre-run and post-run diagnostics
        mock_env.diagnostics_prerun_enabled.return_value = True
        mock_env.diagnostics_postrun_enabled.return_value = True
        diagnostic_path = os.path.join(self.tempdir.name, "diagnostics")
        os.makedirs(diagnostic_path, exist_ok=True)
        self.sequencer.output_context.get_diagnostics_dir.return_value = diagnostic_path

        # Register test integration
        self.sequencer._integrations = {
            "test_integration": TestIntegrationCoupling
        }
        
        # Test with different levels
        for level in [1, 5, 9]:
            TestIntegrationCoupling.reset_tracking()
            
            self.sequencer.diagnostic_capture_pre_testrun(level=level)
            
            self.assertEqual(len(TestIntegrationCoupling.diagnostic_calls), 1)
            self.assertEqual(TestIntegrationCoupling.diagnostic_calls[0]['level'], level)


class TestJobDiagnosticIntegrationTests(unittest.TestCase):
    """
    Integration tests for TestJob diagnostic fire methods.
    
    These tests verify that TestJob correctly delegates diagnostic capture
    to the TestSequencer.
    
    Requirements: 5.1-5.5, 6.1-6.5
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        # Reset tracking data
        TestIntegrationCoupling.reset_tracking()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()

    def test_fire_diagnostic_capture_pre_testrun_delegates_to_sequencer(self):
        """
        Test that fire_diagnostic_capture_pre_testrun delegates to TestSequencer.
        
        Requirements: 5.1
        """
        # Create a mock logger
        mock_logger = MagicMock()
        
        # Create TestJob
        job = TestJob(logger=mock_logger, testroot=self.tempdir.name)
        
        # Create a mock sequencer
        mock_sequencer = MagicMock()
        
        # Call fire method
        job.fire_diagnostic_capture_pre_testrun(mock_sequencer, level=5)
        
        # Verify sequencer method was called with correct level
        mock_sequencer.diagnostic_capture_pre_testrun.assert_called_once_with(5)

    def test_fire_diagnostic_capture_post_testrun_delegates_to_sequencer(self):
        """
        Test that fire_diagnostic_capture_post_testrun delegates to TestSequencer.
        
        Requirements: 6.1
        """
        # Create a mock logger
        mock_logger = MagicMock()
        
        # Create TestJob
        job = TestJob(logger=mock_logger, testroot=self.tempdir.name)
        
        # Create a mock sequencer
        mock_sequencer = MagicMock()
        
        # Call fire method
        job.fire_diagnostic_capture_post_testrun(mock_sequencer, level=7)
        
        # Verify sequencer method was called with correct level
        mock_sequencer.diagnostic_capture_post_testrun.assert_called_once_with(7)

    def test_fire_diagnostic_capture_with_default_level(self):
        """
        Test that fire methods work with default level parameter.
        
        Requirements: 5.1, 6.1
        """
        mock_logger = MagicMock()
        job = TestJob(logger=mock_logger, testroot=self.tempdir.name)
        mock_sequencer = MagicMock()
        
        # Call without specifying level
        job.fire_diagnostic_capture_pre_testrun(mock_sequencer)
        job.fire_diagnostic_capture_post_testrun(mock_sequencer)
        
        # Verify calls were made (level defaults handled by sequencer)
        self.assertEqual(mock_sequencer.diagnostic_capture_pre_testrun.call_count, 1)
        self.assertEqual(mock_sequencer.diagnostic_capture_post_testrun.call_count, 1)


class DiagnosticCaptureWithMultipleIntegrationsTests(unittest.TestCase):
    """
    Integration tests verifying diagnostic capture with multiple integrations.
    
    Requirements: 5.4, 6.4
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        # Reset tracking data
        TestIntegrationCoupling.reset_tracking()
        SecondTestIntegrationCoupling.reset_tracking()

        self.sequencer = TestSequencer(
            jobtitle="multi_integration_test",
            root=self.tempdir.name,
            includes=["ccai"],
            excludes=[],
            metafilters=[]
        )

        # Give the sequencer a controllable output context so diagnostic-dir
        # resolution is mockable and inspectable.
        self._diag_dir = os.path.join(self.tempdir.name, "diagnostics")
        os.makedirs(self._diag_dir, exist_ok=True)
        self.sequencer._output_context = MagicMock()
        self.sequencer._output_context.get_diagnostics_dir.return_value = self._diag_dir

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()

    @patch('ccai.testbase.sequencing.testsequencer.environment')
    def test_all_integrations_receive_diagnostic_call(self, mock_env):
        """
        Test that all registered integrations receive diagnostic calls.

        Requirements: 5.4, 6.4
        """
        mock_env.diagnostics_prerun_enabled.return_value = True
        diagnostic_path = os.path.join(self.tempdir.name, "diagnostics")
        os.makedirs(diagnostic_path, exist_ok=True)
        self.sequencer.output_context.get_diagnostics_dir.return_value = diagnostic_path

        # Register multiple integrations
        self.sequencer._integrations = {
            "first": TestIntegrationCoupling,
            "second": SecondTestIntegrationCoupling
        }
        
        # Execute diagnostic capture
        self.sequencer.diagnostic_capture_pre_testrun(level=9)
        
        # Verify both integrations received calls
        self.assertEqual(len(TestIntegrationCoupling.diagnostic_calls), 1)
        self.assertEqual(len(SecondTestIntegrationCoupling.diagnostic_calls), 1)

    @patch('ccai.testbase.sequencing.testsequencer.environment')
    def test_integrations_receive_same_parameters(self, mock_env):
        """
        Test that all integrations receive the same diagnostic parameters.

        Requirements: 5.2, 5.3, 5.4
        """
        mock_env.diagnostics_prerun_enabled.return_value = True
        diagnostic_path = "/test/diagnostics/prerun"
        self.sequencer.output_context.get_diagnostics_dir.return_value = diagnostic_path

        self.sequencer._integrations = {
            "first": TestIntegrationCoupling,
            "second": SecondTestIntegrationCoupling
        }
        
        self.sequencer.diagnostic_capture_pre_testrun(level=7)
        
        # Verify both received same parameters
        first_call = TestIntegrationCoupling.diagnostic_calls[0]
        second_call = SecondTestIntegrationCoupling.diagnostic_calls[0]
        
        self.assertEqual(first_call['label'], second_call['label'])
        self.assertEqual(first_call['level'], second_call['level'])
        self.assertEqual(first_call['diag_folder'], second_call['diag_folder'])
        
        # Verify correct values
        self.assertEqual(first_call['label'], DiagnosticLabel.PRERUN_DIAGNOSTIC)
        self.assertEqual(first_call['level'], 7)
        self.assertEqual(first_call['diag_folder'], diagnostic_path)


if __name__ == "__main__":
    unittest.main()
