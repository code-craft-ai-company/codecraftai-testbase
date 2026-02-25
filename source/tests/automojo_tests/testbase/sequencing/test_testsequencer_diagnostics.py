"""
.. module:: test_testsequencer_diagnostics
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for TestSequencer diagnostic capture methods.

.. moduleauthor:: AutomationX
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch, call

from automojo.runtime.enumerations import JobType
from automojo.runtime.runtimevariables import RuntimeVariablesDesc
from automojo.thisapp.persona import APP_PERSONA_ESTABLISHED, establish_app_persona
from automojo.thisapp.wellknown import ThisApplicationSingleton

from automojo.testbase.diagnostics import DiagnosticLabel, DiagnosticLabelRegistry
from automojo.testbase.sequencing.testsequencer import TestSequencer


class TestSequencerDiagnosticCapturePreTestrunTests(unittest.TestCase):
    """
    Unit tests for TestSequencer.diagnostic_capture_pre_testrun method.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """

    def setUp(self):
        """Set up test fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()
        
        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)
        
        # Create a TestSequencer instance with minimal configuration
        self.sequencer = TestSequencer(
            jobtitle="test_job",
            root=self.tempdir.name,
            includes=["automojo"],
            excludes=[],
            metafilters=[]
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_prerun_capture_when_enabled(self, mock_get_path, mock_runtime_vars):
        """
        Test pre-run capture when AM_DIAGNOSTICS_PRERUN is True.
        
        Requirement 5.1: WHEN pre-run diagnostics are enabled and 
        fire_diagnostic_capture_pre_testrun is called, THE TestSequencer 
        SHALL capture diagnostics for all registered integrations.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = True
        mock_get_path.return_value = "/test/diagnostics/prerun-diagnostic"
        
        # Create mock integration couplings
        mock_integration1 = MagicMock()
        mock_integration2 = MagicMock()
        
        self.sequencer._integrations = {
            "integration1": mock_integration1,
            "integration2": mock_integration2
        }
        
        self.sequencer.diagnostic_capture_pre_testrun(level=9)
        
        # Verify diagnostic was called on each integration
        mock_integration1.diagnostic.assert_called_once_with(
            DiagnosticLabel.PRERUN_DIAGNOSTIC,
            9,
            "/test/diagnostics/prerun-diagnostic"
        )
        mock_integration2.diagnostic.assert_called_once_with(
            DiagnosticLabel.PRERUN_DIAGNOSTIC,
            9,
            "/test/diagnostics/prerun-diagnostic"
        )

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_prerun_capture_when_disabled(self, mock_get_path, mock_runtime_vars):
        """
        Test pre-run capture is skipped when AM_DIAGNOSTICS_PRERUN is False.
        
        Requirement 5.5: WHEN pre-run diagnostics are disabled, THE TestSequencer 
        SHALL skip the diagnostic capture process.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = False
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        self.sequencer.diagnostic_capture_pre_testrun(level=9)
        
        # Verify get_path_for_diagnostics was not called
        mock_get_path.assert_not_called()
        # Verify diagnostic was not called on integration
        mock_integration.diagnostic.assert_not_called()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_prerun_capture_when_none(self, mock_get_path, mock_runtime_vars):
        """
        Test pre-run capture is skipped when AM_DIAGNOSTICS_PRERUN is None.
        
        Requirement 5.5: WHEN pre-run diagnostics are disabled, THE TestSequencer 
        SHALL skip the diagnostic capture process.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = None
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        self.sequencer.diagnostic_capture_pre_testrun(level=9)
        
        mock_get_path.assert_not_called()
        mock_integration.diagnostic.assert_not_called()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_prerun_uses_correct_label(self, mock_get_path, mock_runtime_vars):
        """
        Test pre-run capture uses DiagnosticLabel.PRERUN_DIAGNOSTIC label.
        
        Requirement 5.2: THE TestSequencer SHALL use the DiagnosticLabel.PRERUN_DIAGNOSTIC 
        label for pre-run diagnostic capture.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = True
        mock_get_path.return_value = "/test/diagnostics/prerun-diagnostic"
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        self.sequencer.diagnostic_capture_pre_testrun(level=5)
        
        # Verify get_path_for_diagnostics was called with correct label
        mock_get_path.assert_called_once_with(DiagnosticLabel.PRERUN_DIAGNOSTIC)
        
        # Verify integration diagnostic was called with correct label
        call_args = mock_integration.diagnostic.call_args
        self.assertEqual(call_args[0][0], DiagnosticLabel.PRERUN_DIAGNOSTIC)

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_prerun_creates_diagnostic_folder_path(self, mock_get_path, mock_runtime_vars):
        """
        Test pre-run capture creates diagnostic folder path using get_path_for_diagnostics.
        
        Requirement 5.3: THE TestSequencer SHALL create a diagnostic folder path 
        using get_path_for_diagnostics with the prerun-diagnostic label.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = True
        expected_path = "/test/results/diagnostics/prerun-diagnostic"
        mock_get_path.return_value = expected_path
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        self.sequencer.diagnostic_capture_pre_testrun(level=9)
        
        mock_get_path.assert_called_once_with(DiagnosticLabel.PRERUN_DIAGNOSTIC)
        
        # Verify the path was passed to integration diagnostic
        call_args = mock_integration.diagnostic.call_args
        self.assertEqual(call_args[0][2], expected_path)


class TestSequencerDiagnosticCapturePostTestrunTests(unittest.TestCase):
    """
    Unit tests for TestSequencer.diagnostic_capture_post_testrun method.
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """

    def setUp(self):
        """Set up test fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()
        
        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)
        
        self.sequencer = TestSequencer(
            jobtitle="test_job",
            root=self.tempdir.name,
            includes=["automojo"],
            excludes=[],
            metafilters=[]
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_postrun_capture_when_enabled(self, mock_get_path, mock_runtime_vars):
        """
        Test post-run capture when AM_DIAGNOSTICS_POSTRUN is True.
        
        Requirement 6.1: WHEN post-run diagnostics are enabled and 
        fire_diagnostic_capture_post_testrun is called, THE TestSequencer 
        SHALL capture diagnostics for all registered integrations.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_POSTRUN = True
        mock_get_path.return_value = "/test/diagnostics/postrun-diagnostic"
        
        mock_integration1 = MagicMock()
        mock_integration2 = MagicMock()
        
        self.sequencer._integrations = {
            "integration1": mock_integration1,
            "integration2": mock_integration2
        }
        
        self.sequencer.diagnostic_capture_post_testrun(level=9)
        
        mock_integration1.diagnostic.assert_called_once_with(
            DiagnosticLabel.POSTRUN_DIAGNOSTIC,
            9,
            "/test/diagnostics/postrun-diagnostic"
        )
        mock_integration2.diagnostic.assert_called_once_with(
            DiagnosticLabel.POSTRUN_DIAGNOSTIC,
            9,
            "/test/diagnostics/postrun-diagnostic"
        )

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_postrun_capture_when_disabled(self, mock_get_path, mock_runtime_vars):
        """
        Test post-run capture is skipped when AM_DIAGNOSTICS_POSTRUN is False.
        
        Requirement 6.5: WHEN post-run diagnostics are disabled, THE TestSequencer 
        SHALL skip the diagnostic capture process.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_POSTRUN = False
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        self.sequencer.diagnostic_capture_post_testrun(level=9)
        
        mock_get_path.assert_not_called()
        mock_integration.diagnostic.assert_not_called()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_postrun_capture_when_none(self, mock_get_path, mock_runtime_vars):
        """
        Test post-run capture is skipped when AM_DIAGNOSTICS_POSTRUN is None.
        
        Requirement 6.5: WHEN post-run diagnostics are disabled, THE TestSequencer 
        SHALL skip the diagnostic capture process.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_POSTRUN = None
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        self.sequencer.diagnostic_capture_post_testrun(level=9)
        
        mock_get_path.assert_not_called()
        mock_integration.diagnostic.assert_not_called()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_postrun_uses_correct_label(self, mock_get_path, mock_runtime_vars):
        """
        Test post-run capture uses DiagnosticLabel.POSTRUN_DIAGNOSTIC label.
        
        Requirement 6.2: THE TestSequencer SHALL use the DiagnosticLabel.POSTRUN_DIAGNOSTIC 
        label for post-run diagnostic capture.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_POSTRUN = True
        mock_get_path.return_value = "/test/diagnostics/postrun-diagnostic"
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        self.sequencer.diagnostic_capture_post_testrun(level=5)
        
        mock_get_path.assert_called_once_with(DiagnosticLabel.POSTRUN_DIAGNOSTIC)
        
        call_args = mock_integration.diagnostic.call_args
        self.assertEqual(call_args[0][0], DiagnosticLabel.POSTRUN_DIAGNOSTIC)

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_postrun_creates_diagnostic_folder_path(self, mock_get_path, mock_runtime_vars):
        """
        Test post-run capture creates diagnostic folder path using get_path_for_diagnostics.
        
        Requirement 6.3: THE TestSequencer SHALL create a diagnostic folder path 
        using get_path_for_diagnostics with the postrun-diagnostic label.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_POSTRUN = True
        expected_path = "/test/results/diagnostics/postrun-diagnostic"
        mock_get_path.return_value = expected_path
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        self.sequencer.diagnostic_capture_post_testrun(level=9)
        
        mock_get_path.assert_called_once_with(DiagnosticLabel.POSTRUN_DIAGNOSTIC)
        
        call_args = mock_integration.diagnostic.call_args
        self.assertEqual(call_args[0][2], expected_path)


class TestSequencerDiagnosticIntegrationIterationTests(unittest.TestCase):
    """
    Unit tests for verifying integration iteration during diagnostic capture.
    
    Requirements: 5.4, 6.4
    """

    def setUp(self):
        """Set up test fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()
        
        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)
        
        self.sequencer = TestSequencer(
            jobtitle="test_job",
            root=self.tempdir.name,
            includes=["automojo"],
            excludes=[],
            metafilters=[]
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_prerun_iterates_all_integrations(self, mock_get_path, mock_runtime_vars):
        """
        Test pre-run capture iterates over all registered integration couplings.
        
        Requirement 5.4: THE TestSequencer SHALL iterate over all registered 
        integration couplings and call their diagnostic method.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = True
        mock_get_path.return_value = "/test/diagnostics"
        
        # Create multiple mock integrations
        mock_integrations = {}
        for i in range(5):
            mock_integrations[f"integration_{i}"] = MagicMock()
        
        self.sequencer._integrations = mock_integrations
        
        self.sequencer.diagnostic_capture_pre_testrun(level=9)
        
        # Verify all integrations had diagnostic called
        for name, mock_integ in mock_integrations.items():
            mock_integ.diagnostic.assert_called_once()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_postrun_iterates_all_integrations(self, mock_get_path, mock_runtime_vars):
        """
        Test post-run capture iterates over all registered integration couplings.
        
        Requirement 6.4: THE TestSequencer SHALL iterate over all registered 
        integration couplings and call their diagnostic method.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_POSTRUN = True
        mock_get_path.return_value = "/test/diagnostics"
        
        mock_integrations = {}
        for i in range(5):
            mock_integrations[f"integration_{i}"] = MagicMock()
        
        self.sequencer._integrations = mock_integrations
        
        self.sequencer.diagnostic_capture_post_testrun(level=9)
        
        for name, mock_integ in mock_integrations.items():
            mock_integ.diagnostic.assert_called_once()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_prerun_with_empty_integrations(self, mock_get_path, mock_runtime_vars):
        """
        Test pre-run capture handles empty integrations dictionary gracefully.
        
        Requirement 5.4: THE TestSequencer SHALL iterate over all registered 
        integration couplings and call their diagnostic method.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = True
        mock_get_path.return_value = "/test/diagnostics"
        
        self.sequencer._integrations = {}
        
        # Should not raise any exception
        self.sequencer.diagnostic_capture_pre_testrun(level=9)
        
        mock_get_path.assert_called_once()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_postrun_with_empty_integrations(self, mock_get_path, mock_runtime_vars):
        """
        Test post-run capture handles empty integrations dictionary gracefully.
        
        Requirement 6.4: THE TestSequencer SHALL iterate over all registered 
        integration couplings and call their diagnostic method.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_POSTRUN = True
        mock_get_path.return_value = "/test/diagnostics"
        
        self.sequencer._integrations = {}
        
        self.sequencer.diagnostic_capture_post_testrun(level=9)
        
        mock_get_path.assert_called_once()


class TestSequencerDiagnosticLevelPropagationTests(unittest.TestCase):
    """
    Unit tests for verifying diagnostic level propagation.
    
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
    """

    def setUp(self):
        """Set up test fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()
        
        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)
        
        self.sequencer = TestSequencer(
            jobtitle="test_job",
            root=self.tempdir.name,
            includes=["automojo"],
            excludes=[],
            metafilters=[]
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_prerun_default_level_is_9(self, mock_get_path, mock_runtime_vars):
        """
        Test pre-run capture uses default level 9 when not specified.
        
        Requirement 7.5: THE default diagnostic level SHALL be 9 (maximum detail) 
        when not explicitly specified.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = True
        mock_get_path.return_value = "/test/diagnostics"
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        # Call without specifying level
        self.sequencer.diagnostic_capture_pre_testrun()
        
        call_args = mock_integration.diagnostic.call_args
        self.assertEqual(call_args[0][1], 9)

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_postrun_default_level_is_9(self, mock_get_path, mock_runtime_vars):
        """
        Test post-run capture uses default level 9 when not specified.
        
        Requirement 7.5: THE default diagnostic level SHALL be 9 (maximum detail) 
        when not explicitly specified.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_POSTRUN = True
        mock_get_path.return_value = "/test/diagnostics"
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        self.sequencer.diagnostic_capture_post_testrun()
        
        call_args = mock_integration.diagnostic.call_args
        self.assertEqual(call_args[0][1], 9)

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_prerun_propagates_basic_level(self, mock_get_path, mock_runtime_vars):
        """
        Test pre-run capture propagates basic diagnostic level (1-3).
        
        Requirement 7.1: THE diagnostic level parameter SHALL accept integer values from 1 to 9.
        Requirement 7.2: WHEN diagnostic level is 1-3, THE integration coupling 
        SHALL capture basic diagnostic information.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = True
        mock_get_path.return_value = "/test/diagnostics"
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        for level in [1, 2, 3]:
            mock_integration.reset_mock()
            self.sequencer.diagnostic_capture_pre_testrun(level=level)
            
            call_args = mock_integration.diagnostic.call_args
            self.assertEqual(call_args[0][1], level)

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_prerun_propagates_standard_level(self, mock_get_path, mock_runtime_vars):
        """
        Test pre-run capture propagates standard diagnostic level (4-6).
        
        Requirement 7.1: THE diagnostic level parameter SHALL accept integer values from 1 to 9.
        Requirement 7.3: WHEN diagnostic level is 4-6, THE integration coupling 
        SHALL capture standard diagnostic information.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = True
        mock_get_path.return_value = "/test/diagnostics"
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        for level in [4, 5, 6]:
            mock_integration.reset_mock()
            self.sequencer.diagnostic_capture_pre_testrun(level=level)
            
            call_args = mock_integration.diagnostic.call_args
            self.assertEqual(call_args[0][1], level)

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_prerun_propagates_detailed_level(self, mock_get_path, mock_runtime_vars):
        """
        Test pre-run capture propagates detailed diagnostic level (7-9).
        
        Requirement 7.1: THE diagnostic level parameter SHALL accept integer values from 1 to 9.
        Requirement 7.4: WHEN diagnostic level is 7-9, THE integration coupling 
        SHALL capture detailed diagnostic information.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = True
        mock_get_path.return_value = "/test/diagnostics"
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        for level in [7, 8, 9]:
            mock_integration.reset_mock()
            self.sequencer.diagnostic_capture_pre_testrun(level=level)
            
            call_args = mock_integration.diagnostic.call_args
            self.assertEqual(call_args[0][1], level)

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_postrun_propagates_all_levels(self, mock_get_path, mock_runtime_vars):
        """
        Test post-run capture propagates all diagnostic levels (1-9).
        
        Requirement 7.1: THE diagnostic level parameter SHALL accept integer values from 1 to 9.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_POSTRUN = True
        mock_get_path.return_value = "/test/diagnostics"
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        for level in range(1, 10):
            mock_integration.reset_mock()
            self.sequencer.diagnostic_capture_post_testrun(level=level)
            
            call_args = mock_integration.diagnostic.call_args
            self.assertEqual(call_args[0][1], level)

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_level_propagated_to_all_integrations(self, mock_get_path, mock_runtime_vars):
        """
        Test diagnostic level is propagated to all integrations consistently.
        
        Requirement 7.1: THE diagnostic level parameter SHALL accept integer values from 1 to 9.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = True
        mock_get_path.return_value = "/test/diagnostics"
        
        mock_integrations = {
            f"integration_{i}": MagicMock() for i in range(3)
        }
        self.sequencer._integrations = mock_integrations
        
        test_level = 5
        self.sequencer.diagnostic_capture_pre_testrun(level=test_level)
        
        for name, mock_integ in mock_integrations.items():
            call_args = mock_integ.diagnostic.call_args
            self.assertEqual(
                call_args[0][1], 
                test_level,
                f"Level not propagated correctly to {name}"
            )


class TestSequencerDiagnosticCaptureCustomTests(unittest.TestCase):
    """
    Unit tests for TestSequencer.diagnostic_capture_custom method.
    
    Tests custom diagnostic label capture functionality.
    """

    def setUp(self):
        """Set up test fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()
        
        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)
        
        self.sequencer = TestSequencer(
            jobtitle="test_job",
            root=self.tempdir.name,
            includes=["automojo"],
            excludes=[],
            metafilters=[]
        )
        
        # Clear any custom labels from previous tests
        DiagnosticLabelRegistry.clear_custom_labels()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        DiagnosticLabelRegistry.clear_custom_labels()

    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_custom_capture_with_registered_label(self, mock_get_path):
        """Test custom capture with a registered custom label."""
        mock_get_path.return_value = "/test/diagnostics/checkpoint-diagnostic"
        
        # Register a custom label
        DiagnosticLabelRegistry.register("checkpoint-diagnostic", "Test checkpoint")
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        self.sequencer.diagnostic_capture_custom("checkpoint-diagnostic", level=5)
        
        mock_get_path.assert_called_once_with("checkpoint-diagnostic")
        mock_integration.diagnostic.assert_called_once_with(
            "checkpoint-diagnostic",
            5,
            "/test/diagnostics/checkpoint-diagnostic"
        )

    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_custom_capture_with_unregistered_label(self, mock_get_path):
        """Test custom capture works with unregistered labels (no validation)."""
        mock_get_path.return_value = "/test/diagnostics/custom-label"
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        # Should work even without registering the label
        self.sequencer.diagnostic_capture_custom("custom-label", level=7)
        
        mock_get_path.assert_called_once_with("custom-label")
        mock_integration.diagnostic.assert_called_once()

    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_custom_capture_default_level_is_9(self, mock_get_path):
        """Test custom capture uses default level 9 when not specified."""
        mock_get_path.return_value = "/test/diagnostics/custom-label"
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        self.sequencer.diagnostic_capture_custom("custom-label")
        
        call_args = mock_integration.diagnostic.call_args
        self.assertEqual(call_args[0][1], 9)

    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_custom_capture_iterates_all_integrations(self, mock_get_path):
        """Test custom capture iterates over all registered integrations."""
        mock_get_path.return_value = "/test/diagnostics/custom-label"
        
        mock_integrations = {
            f"integration_{i}": MagicMock() for i in range(3)
        }
        self.sequencer._integrations = mock_integrations
        
        self.sequencer.diagnostic_capture_custom("custom-label", level=5)
        
        for name, mock_integ in mock_integrations.items():
            mock_integ.diagnostic.assert_called_once()

    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_custom_capture_with_empty_integrations(self, mock_get_path):
        """Test custom capture handles empty integrations gracefully."""
        mock_get_path.return_value = "/test/diagnostics/custom-label"
        
        self.sequencer._integrations = {}
        
        # Should not raise any exception
        self.sequencer.diagnostic_capture_custom("custom-label", level=5)
        
        mock_get_path.assert_called_once()

    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_custom_capture_propagates_level_to_all_integrations(self, mock_get_path):
        """Test custom capture propagates level to all integrations."""
        mock_get_path.return_value = "/test/diagnostics/custom-label"
        
        mock_integrations = {
            f"integration_{i}": MagicMock() for i in range(3)
        }
        self.sequencer._integrations = mock_integrations
        
        test_level = 4
        self.sequencer.diagnostic_capture_custom("custom-label", level=test_level)
        
        for name, mock_integ in mock_integrations.items():
            call_args = mock_integ.diagnostic.call_args
            self.assertEqual(call_args[0][1], test_level)

    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_custom_capture_with_builtin_label(self, mock_get_path):
        """Test custom capture works with built-in labels."""
        mock_get_path.return_value = "/test/diagnostics/prerun-diagnostic"
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        # Should work with built-in labels too
        self.sequencer.diagnostic_capture_custom(DiagnosticLabel.PRERUN_DIAGNOSTIC, level=5)
        
        mock_get_path.assert_called_once_with(DiagnosticLabel.PRERUN_DIAGNOSTIC)
        mock_integration.diagnostic.assert_called_once()

    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_custom_capture_does_not_check_runtime_variables(self, mock_get_path):
        """Test custom capture does not check runtime variables (always captures)."""
        mock_get_path.return_value = "/test/diagnostics/custom-label"
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        # Custom capture should work regardless of runtime variable state
        # (unlike pre-run and post-run which check AM_DIAGNOSTICS_* variables)
        self.sequencer.diagnostic_capture_custom("custom-label", level=5)
        
        mock_integration.diagnostic.assert_called_once()


class TestSequencerDiagnosticFilteringTests(unittest.TestCase):
    """
    Unit tests for TestSequencer diagnostic filtering functionality.
    
    Tests that DiagnosticFilter is applied correctly during diagnostic capture.
    """

    def setUp(self):
        """Set up test fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()
        
        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)
        
        self.sequencer = TestSequencer(
            jobtitle="test_job",
            root=self.tempdir.name,
            includes=["automojo"],
            excludes=[],
            metafilters=[]
        )
        
        # Import DiagnosticFilter for testing
        from automojo.testbase.diagnostics import DiagnosticFilter
        self.DiagnosticFilter = DiagnosticFilter
        
        # Clear any filters from previous tests
        self.DiagnosticFilter.clear_all_filters()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        self.DiagnosticFilter.clear_all_filters()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_prerun_capture_filters_integrations_by_include_pattern(self, mock_get_path, mock_runtime_vars):
        """
        Test pre-run capture filters integrations using include patterns.
        
        Verifies that only integrations matching include patterns have their
        diagnostic method called.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = True
        mock_get_path.return_value = "/test/diagnostics/prerun-diagnostic"
        
        # Create mock integrations
        mock_device = MagicMock()
        mock_network = MagicMock()
        mock_database = MagicMock()
        
        self.sequencer._integrations = {
            "DeviceCoupling": mock_device,
            "NetworkCoupling": mock_network,
            "DatabaseCoupling": mock_database
        }
        
        # Add include pattern for Device* only
        self.DiagnosticFilter.add_integration_include_pattern("Device*")
        
        self.sequencer.diagnostic_capture_pre_testrun(level=9)
        
        # Only DeviceCoupling should have diagnostic called
        mock_device.diagnostic.assert_called_once()
        mock_network.diagnostic.assert_not_called()
        mock_database.diagnostic.assert_not_called()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_prerun_capture_filters_integrations_by_exclude_pattern(self, mock_get_path, mock_runtime_vars):
        """
        Test pre-run capture filters integrations using exclude patterns.
        
        Verifies that integrations matching exclude patterns are skipped.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = True
        mock_get_path.return_value = "/test/diagnostics/prerun-diagnostic"
        
        mock_device = MagicMock()
        mock_debug = MagicMock()
        mock_network = MagicMock()
        
        self.sequencer._integrations = {
            "DeviceCoupling": mock_device,
            "DebugCoupling": mock_debug,
            "NetworkCoupling": mock_network
        }
        
        # Exclude Debug* integrations
        self.DiagnosticFilter.add_integration_exclude_pattern("Debug*")
        
        self.sequencer.diagnostic_capture_pre_testrun(level=9)
        
        # DebugCoupling should be skipped
        mock_device.diagnostic.assert_called_once()
        mock_debug.diagnostic.assert_not_called()
        mock_network.diagnostic.assert_called_once()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_prerun_capture_skipped_when_label_excluded(self, mock_get_path, mock_runtime_vars):
        """
        Test pre-run capture is skipped when label is excluded by filter.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = True
        mock_get_path.return_value = "/test/diagnostics/prerun-diagnostic"
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        # Exclude prerun-diagnostic label
        self.DiagnosticFilter.add_label_exclude_pattern("prerun-*")
        
        self.sequencer.diagnostic_capture_pre_testrun(level=9)
        
        # No integrations should have diagnostic called
        mock_integration.diagnostic.assert_not_called()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_postrun_capture_filters_integrations_by_include_pattern(self, mock_get_path, mock_runtime_vars):
        """
        Test post-run capture filters integrations using include patterns.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_POSTRUN = True
        mock_get_path.return_value = "/test/diagnostics/postrun-diagnostic"
        
        mock_device = MagicMock()
        mock_network = MagicMock()
        
        self.sequencer._integrations = {
            "DeviceCoupling": mock_device,
            "NetworkCoupling": mock_network
        }
        
        # Add include pattern for Network* only
        self.DiagnosticFilter.add_integration_include_pattern("Network*")
        
        self.sequencer.diagnostic_capture_post_testrun(level=9)
        
        # Only NetworkCoupling should have diagnostic called
        mock_device.diagnostic.assert_not_called()
        mock_network.diagnostic.assert_called_once()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_postrun_capture_skipped_when_label_excluded(self, mock_get_path, mock_runtime_vars):
        """
        Test post-run capture is skipped when label is excluded by filter.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_POSTRUN = True
        mock_get_path.return_value = "/test/diagnostics/postrun-diagnostic"
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        # Exclude postrun-diagnostic label
        self.DiagnosticFilter.add_label_exclude_pattern("postrun-*")
        
        self.sequencer.diagnostic_capture_post_testrun(level=9)
        
        # No integrations should have diagnostic called
        mock_integration.diagnostic.assert_not_called()

    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_custom_capture_filters_integrations_by_include_pattern(self, mock_get_path):
        """
        Test custom capture filters integrations using include patterns.
        """
        mock_get_path.return_value = "/test/diagnostics/custom-label"
        
        mock_device = MagicMock()
        mock_network = MagicMock()
        
        self.sequencer._integrations = {
            "DeviceCoupling": mock_device,
            "NetworkCoupling": mock_network
        }
        
        # Add include pattern for Device* only
        self.DiagnosticFilter.add_integration_include_pattern("Device*")
        
        self.sequencer.diagnostic_capture_custom("custom-label", level=5)
        
        # Only DeviceCoupling should have diagnostic called
        mock_device.diagnostic.assert_called_once()
        mock_network.diagnostic.assert_not_called()

    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_custom_capture_skipped_when_label_excluded(self, mock_get_path):
        """
        Test custom capture is skipped when label is excluded by filter.
        """
        mock_get_path.return_value = "/test/diagnostics/custom-label"
        
        mock_integration = MagicMock()
        self.sequencer._integrations = {"integration1": mock_integration}
        
        # Exclude custom-label
        self.DiagnosticFilter.add_label_exclude_pattern("custom-*")
        
        self.sequencer.diagnostic_capture_custom("custom-label", level=5)
        
        # No integrations should have diagnostic called
        mock_integration.diagnostic.assert_not_called()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_capture_with_no_filters_captures_all(self, mock_get_path, mock_runtime_vars):
        """
        Test that with no filters configured, all integrations are captured.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = True
        mock_get_path.return_value = "/test/diagnostics/prerun-diagnostic"
        
        mock_integrations = {
            f"Integration{i}": MagicMock() for i in range(5)
        }
        self.sequencer._integrations = mock_integrations
        
        # No filters configured
        self.sequencer.diagnostic_capture_pre_testrun(level=9)
        
        # All integrations should have diagnostic called
        for name, mock_integ in mock_integrations.items():
            mock_integ.diagnostic.assert_called_once()

    @patch('automojo.testbase.sequencing.testsequencer.RuntimeVariables')
    @patch('automojo.testbase.sequencing.testsequencer.get_path_for_diagnostics')
    def test_exclude_takes_precedence_over_include(self, mock_get_path, mock_runtime_vars):
        """
        Test that exclude patterns take precedence over include patterns.
        """
        mock_runtime_vars.AM_DIAGNOSTICS_PRERUN = True
        mock_get_path.return_value = "/test/diagnostics/prerun-diagnostic"
        
        mock_device = MagicMock()
        mock_device_debug = MagicMock()
        
        self.sequencer._integrations = {
            "DeviceCoupling": mock_device,
            "DeviceDebugCoupling": mock_device_debug
        }
        
        # Include Device* but exclude *Debug*
        self.DiagnosticFilter.add_integration_include_pattern("Device*")
        self.DiagnosticFilter.add_integration_exclude_pattern("*Debug*")
        
        self.sequencer.diagnostic_capture_pre_testrun(level=9)
        
        # DeviceCoupling should be captured, DeviceDebugCoupling should be excluded
        mock_device.diagnostic.assert_called_once()
        mock_device_debug.diagnostic.assert_not_called()


if __name__ == "__main__":
    unittest.main()
