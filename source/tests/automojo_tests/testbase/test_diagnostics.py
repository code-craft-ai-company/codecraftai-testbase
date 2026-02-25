"""
.. module:: test_diagnostics
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the DiagnosticLabel, RuntimeConfigPaths constants,
        DiagnosticLabelRegistry, and DiagnosticFilter.

.. moduleauthor:: AutomationX
"""

import unittest

from automojo.testbase.diagnostics import (
    DiagnosticLabel,
    RuntimeConfigPaths,
    DiagnosticLabelRegistry,
    DiagnosticFilter
)


class DiagnosticLabelTests(unittest.TestCase):
    """
    Unit tests for the DiagnosticLabel class constants.
    
    Requirements: 1.1, 1.2, 1.3, 1.4
    """

    def test_prerun_diagnostic_value_is_correct(self):
        """
        Verify PRERUN_DIAGNOSTIC value is "prerun-diagnostic".
        
        Requirement 1.1
        """
        self.assertEqual(DiagnosticLabel.PRERUN_DIAGNOSTIC, "prerun-diagnostic")

    def test_postrun_diagnostic_value_is_correct(self):
        """
        Verify POSTRUN_DIAGNOSTIC value is "postrun-diagnostic".
        
        Requirement 1.2
        """
        self.assertEqual(DiagnosticLabel.POSTRUN_DIAGNOSTIC, "postrun-diagnostic")

    def test_prerun_diagnostic_is_string_type(self):
        """
        Verify PRERUN_DIAGNOSTIC constant is string type.
        
        Requirement 1.4
        """
        self.assertIsInstance(DiagnosticLabel.PRERUN_DIAGNOSTIC, str)

    def test_postrun_diagnostic_is_string_type(self):
        """
        Verify POSTRUN_DIAGNOSTIC constant is string type.
        
        Requirement 1.4
        """
        self.assertIsInstance(DiagnosticLabel.POSTRUN_DIAGNOSTIC, str)

    def test_prerun_diagnostic_accessible_without_instantiation(self):
        """
        Verify PRERUN_DIAGNOSTIC is accessible as a class attribute without instantiation.
        
        Requirement 1.3
        """
        self.assertIsNotNone(DiagnosticLabel.PRERUN_DIAGNOSTIC)
        self.assertTrue(hasattr(DiagnosticLabel, 'PRERUN_DIAGNOSTIC'))

    def test_postrun_diagnostic_accessible_without_instantiation(self):
        """
        Verify POSTRUN_DIAGNOSTIC is accessible as a class attribute without instantiation.
        
        Requirement 1.3
        """
        self.assertIsNotNone(DiagnosticLabel.POSTRUN_DIAGNOSTIC)
        self.assertTrue(hasattr(DiagnosticLabel, 'POSTRUN_DIAGNOSTIC'))


class RuntimeConfigPathsTests(unittest.TestCase):
    """
    Unit tests for the RuntimeConfigPaths class constants.
    
    Requirements: 2.1, 2.2, 2.3, 2.4
    """

    def test_diagnostic_prerun_path_value_is_correct(self):
        """
        Verify DIAGNOSTIC_PRERUN path value is correct.
        
        Requirement 2.1
        """
        self.assertEqual(
            RuntimeConfigPaths.DIAGNOSTIC_PRERUN,
            "/configuration/runtime/diagnostics/prerun-diagnostic"
        )

    def test_diagnostic_postrun_path_value_is_correct(self):
        """
        Verify DIAGNOSTIC_POSTRUN path value is correct.
        
        Requirement 2.2
        """
        self.assertEqual(
            RuntimeConfigPaths.DIAGNOSTIC_POSTRUN,
            "/configuration/runtime/diagnostics/postrun-diagnostic"
        )

    def test_diagnostic_prerun_follows_hierarchical_format(self):
        """
        Verify DIAGNOSTIC_PRERUN path follows hierarchical format starting with
        "/configuration/runtime/diagnostics/".
        
        Requirement 2.4
        """
        self.assertTrue(
            RuntimeConfigPaths.DIAGNOSTIC_PRERUN.startswith("/configuration/runtime/diagnostics/")
        )

    def test_diagnostic_postrun_follows_hierarchical_format(self):
        """
        Verify DIAGNOSTIC_POSTRUN path follows hierarchical format starting with
        "/configuration/runtime/diagnostics/".
        
        Requirement 2.4
        """
        self.assertTrue(
            RuntimeConfigPaths.DIAGNOSTIC_POSTRUN.startswith("/configuration/runtime/diagnostics/")
        )

    def test_diagnostic_prerun_accessible_without_instantiation(self):
        """
        Verify DIAGNOSTIC_PRERUN is accessible as a class attribute without instantiation.
        
        Requirement 2.3
        """
        self.assertIsNotNone(RuntimeConfigPaths.DIAGNOSTIC_PRERUN)
        self.assertTrue(hasattr(RuntimeConfigPaths, 'DIAGNOSTIC_PRERUN'))

    def test_diagnostic_postrun_accessible_without_instantiation(self):
        """
        Verify DIAGNOSTIC_POSTRUN is accessible as a class attribute without instantiation.
        
        Requirement 2.3
        """
        self.assertIsNotNone(RuntimeConfigPaths.DIAGNOSTIC_POSTRUN)
        self.assertTrue(hasattr(RuntimeConfigPaths, 'DIAGNOSTIC_POSTRUN'))


class DiagnosticLabelRegistryTests(unittest.TestCase):
    """
    Unit tests for the DiagnosticLabelRegistry class.
    
    Tests custom diagnostic label registration, retrieval, and management.
    """

    def setUp(self):
        """Clear custom labels before each test to ensure isolation."""
        DiagnosticLabelRegistry.clear_custom_labels()

    def tearDown(self):
        """Clear custom labels after each test to ensure isolation."""
        DiagnosticLabelRegistry.clear_custom_labels()

    def test_register_custom_label_succeeds(self):
        """Verify that registering a new custom label succeeds."""
        result = DiagnosticLabelRegistry.register("checkpoint-diagnostic", "Test checkpoint")
        self.assertTrue(result)
        self.assertTrue(DiagnosticLabelRegistry.is_registered("checkpoint-diagnostic"))

    def test_register_duplicate_custom_label_fails(self):
        """Verify that registering a duplicate custom label fails."""
        DiagnosticLabelRegistry.register("checkpoint-diagnostic", "First registration")
        result = DiagnosticLabelRegistry.register("checkpoint-diagnostic", "Second registration")
        self.assertFalse(result)

    def test_register_builtin_label_fails(self):
        """Verify that registering a built-in label fails."""
        result = DiagnosticLabelRegistry.register("prerun-diagnostic", "Attempt to override")
        self.assertFalse(result)
        result = DiagnosticLabelRegistry.register("postrun-diagnostic", "Attempt to override")
        self.assertFalse(result)

    def test_register_empty_label_raises_error(self):
        """Verify that registering an empty label raises ValueError."""
        with self.assertRaises(ValueError):
            DiagnosticLabelRegistry.register("", "Empty label")
        with self.assertRaises(ValueError):
            DiagnosticLabelRegistry.register(None, "None label")

    def test_unregister_custom_label_succeeds(self):
        """Verify that unregistering a custom label succeeds."""
        DiagnosticLabelRegistry.register("checkpoint-diagnostic", "Test checkpoint")
        result = DiagnosticLabelRegistry.unregister("checkpoint-diagnostic")
        self.assertTrue(result)
        self.assertFalse(DiagnosticLabelRegistry.is_registered("checkpoint-diagnostic"))

    def test_unregister_builtin_label_fails(self):
        """Verify that unregistering a built-in label fails."""
        result = DiagnosticLabelRegistry.unregister("prerun-diagnostic")
        self.assertFalse(result)
        self.assertTrue(DiagnosticLabelRegistry.is_registered("prerun-diagnostic"))

    def test_unregister_nonexistent_label_fails(self):
        """Verify that unregistering a non-existent label fails."""
        result = DiagnosticLabelRegistry.unregister("nonexistent-label")
        self.assertFalse(result)

    def test_is_registered_returns_true_for_builtin_labels(self):
        """Verify that is_registered returns True for built-in labels."""
        self.assertTrue(DiagnosticLabelRegistry.is_registered("prerun-diagnostic"))
        self.assertTrue(DiagnosticLabelRegistry.is_registered("postrun-diagnostic"))

    def test_is_registered_returns_true_for_custom_labels(self):
        """Verify that is_registered returns True for custom labels."""
        DiagnosticLabelRegistry.register("checkpoint-diagnostic")
        self.assertTrue(DiagnosticLabelRegistry.is_registered("checkpoint-diagnostic"))

    def test_is_registered_returns_false_for_unknown_labels(self):
        """Verify that is_registered returns False for unknown labels."""
        self.assertFalse(DiagnosticLabelRegistry.is_registered("unknown-label"))

    def test_is_builtin_returns_true_for_builtin_labels(self):
        """Verify that is_builtin returns True for built-in labels."""
        self.assertTrue(DiagnosticLabelRegistry.is_builtin("prerun-diagnostic"))
        self.assertTrue(DiagnosticLabelRegistry.is_builtin("postrun-diagnostic"))

    def test_is_builtin_returns_false_for_custom_labels(self):
        """Verify that is_builtin returns False for custom labels."""
        DiagnosticLabelRegistry.register("checkpoint-diagnostic")
        self.assertFalse(DiagnosticLabelRegistry.is_builtin("checkpoint-diagnostic"))

    def test_get_description_returns_description_for_builtin_labels(self):
        """Verify that get_description returns correct description for built-in labels."""
        desc = DiagnosticLabelRegistry.get_description("prerun-diagnostic")
        self.assertIsNotNone(desc)
        self.assertIn("pre-run", desc.lower())

    def test_get_description_returns_description_for_custom_labels(self):
        """Verify that get_description returns correct description for custom labels."""
        DiagnosticLabelRegistry.register("checkpoint-diagnostic", "Test checkpoint description")
        desc = DiagnosticLabelRegistry.get_description("checkpoint-diagnostic")
        self.assertEqual(desc, "Test checkpoint description")

    def test_get_description_returns_none_for_unknown_labels(self):
        """Verify that get_description returns None for unknown labels."""
        desc = DiagnosticLabelRegistry.get_description("unknown-label")
        self.assertIsNone(desc)

    def test_get_all_labels_includes_builtin_labels(self):
        """Verify that get_all_labels includes built-in labels."""
        all_labels = DiagnosticLabelRegistry.get_all_labels()
        self.assertIn("prerun-diagnostic", all_labels)
        self.assertIn("postrun-diagnostic", all_labels)

    def test_get_all_labels_includes_custom_labels(self):
        """Verify that get_all_labels includes custom labels."""
        DiagnosticLabelRegistry.register("checkpoint-diagnostic", "Test checkpoint")
        all_labels = DiagnosticLabelRegistry.get_all_labels()
        self.assertIn("checkpoint-diagnostic", all_labels)

    def test_get_custom_labels_excludes_builtin_labels(self):
        """Verify that get_custom_labels excludes built-in labels."""
        DiagnosticLabelRegistry.register("checkpoint-diagnostic", "Test checkpoint")
        custom_labels = DiagnosticLabelRegistry.get_custom_labels()
        self.assertIn("checkpoint-diagnostic", custom_labels)
        self.assertNotIn("prerun-diagnostic", custom_labels)
        self.assertNotIn("postrun-diagnostic", custom_labels)

    def test_get_builtin_labels_returns_only_builtin_labels(self):
        """Verify that get_builtin_labels returns only built-in labels."""
        DiagnosticLabelRegistry.register("checkpoint-diagnostic", "Test checkpoint")
        builtin_labels = DiagnosticLabelRegistry.get_builtin_labels()
        self.assertIn("prerun-diagnostic", builtin_labels)
        self.assertIn("postrun-diagnostic", builtin_labels)
        self.assertNotIn("checkpoint-diagnostic", builtin_labels)

    def test_clear_custom_labels_removes_all_custom_labels(self):
        """Verify that clear_custom_labels removes all custom labels."""
        DiagnosticLabelRegistry.register("checkpoint-diagnostic", "Test checkpoint")
        DiagnosticLabelRegistry.register("mid-test-diagnostic", "Mid-test capture")
        DiagnosticLabelRegistry.clear_custom_labels()
        custom_labels = DiagnosticLabelRegistry.get_custom_labels()
        self.assertEqual(len(custom_labels), 0)

    def test_clear_custom_labels_preserves_builtin_labels(self):
        """Verify that clear_custom_labels preserves built-in labels."""
        DiagnosticLabelRegistry.register("checkpoint-diagnostic", "Test checkpoint")
        DiagnosticLabelRegistry.clear_custom_labels()
        self.assertTrue(DiagnosticLabelRegistry.is_registered("prerun-diagnostic"))
        self.assertTrue(DiagnosticLabelRegistry.is_registered("postrun-diagnostic"))

    def test_get_config_path_for_label_generates_correct_path(self):
        """Verify that get_config_path_for_label generates correct configuration path."""
        path = DiagnosticLabelRegistry.get_config_path_for_label("prerun-diagnostic")
        self.assertEqual(path, "/configuration/runtime/diagnostics/prerun-diagnostic")
        
        path = DiagnosticLabelRegistry.get_config_path_for_label("checkpoint-diagnostic")
        self.assertEqual(path, "/configuration/runtime/diagnostics/checkpoint-diagnostic")

    def test_backward_compatibility_with_diagnostic_label_constants(self):
        """Verify backward compatibility with existing DiagnosticLabel constants."""
        # Built-in labels should match DiagnosticLabel constants
        self.assertTrue(DiagnosticLabelRegistry.is_registered(DiagnosticLabel.PRERUN_DIAGNOSTIC))
        self.assertTrue(DiagnosticLabelRegistry.is_registered(DiagnosticLabel.POSTRUN_DIAGNOSTIC))
        
        # Config paths should match RuntimeConfigPaths
        prerun_path = DiagnosticLabelRegistry.get_config_path_for_label(DiagnosticLabel.PRERUN_DIAGNOSTIC)
        self.assertEqual(prerun_path, RuntimeConfigPaths.DIAGNOSTIC_PRERUN)
        
        postrun_path = DiagnosticLabelRegistry.get_config_path_for_label(DiagnosticLabel.POSTRUN_DIAGNOSTIC)
        self.assertEqual(postrun_path, RuntimeConfigPaths.DIAGNOSTIC_POSTRUN)


class DiagnosticFilterIntegrationIncludeTests(unittest.TestCase):
    """
    Unit tests for DiagnosticFilter integration include pattern functionality.
    
    Tests filtering diagnostics by integration type using include patterns.
    """

    def setUp(self):
        """Clear all filters before each test to ensure isolation."""
        DiagnosticFilter.clear_all_filters()

    def tearDown(self):
        """Clear all filters after each test to ensure isolation."""
        DiagnosticFilter.clear_all_filters()

    def test_add_integration_include_pattern_adds_pattern(self):
        """Verify that adding an integration include pattern works."""
        DiagnosticFilter.add_integration_include_pattern("Device*")
        patterns = DiagnosticFilter.get_integration_include_patterns()
        self.assertIn("Device*", patterns)

    def test_add_integration_include_pattern_prevents_duplicates(self):
        """Verify that duplicate patterns are not added."""
        DiagnosticFilter.add_integration_include_pattern("Device*")
        DiagnosticFilter.add_integration_include_pattern("Device*")
        patterns = DiagnosticFilter.get_integration_include_patterns()
        self.assertEqual(patterns.count("Device*"), 1)

    def test_add_integration_include_pattern_ignores_empty(self):
        """Verify that empty patterns are ignored."""
        DiagnosticFilter.add_integration_include_pattern("")
        DiagnosticFilter.add_integration_include_pattern(None)
        patterns = DiagnosticFilter.get_integration_include_patterns()
        self.assertEqual(len(patterns), 0)

    def test_should_capture_integration_with_no_patterns_returns_true(self):
        """Verify that with no patterns, all integrations are captured."""
        self.assertTrue(DiagnosticFilter.should_capture_integration("DeviceCoupling"))
        self.assertTrue(DiagnosticFilter.should_capture_integration("NetworkCoupling"))

    def test_should_capture_integration_with_matching_include_pattern(self):
        """Verify that matching include patterns allow capture."""
        DiagnosticFilter.add_integration_include_pattern("Device*")
        self.assertTrue(DiagnosticFilter.should_capture_integration("DeviceCoupling"))
        self.assertTrue(DiagnosticFilter.should_capture_integration("DeviceManager"))

    def test_should_capture_integration_with_non_matching_include_pattern(self):
        """Verify that non-matching include patterns block capture."""
        DiagnosticFilter.add_integration_include_pattern("Device*")
        self.assertFalse(DiagnosticFilter.should_capture_integration("NetworkCoupling"))
        self.assertFalse(DiagnosticFilter.should_capture_integration("DatabaseCoupling"))

    def test_should_capture_integration_with_multiple_include_patterns(self):
        """Verify that multiple include patterns work correctly."""
        DiagnosticFilter.add_integration_include_pattern("Device*")
        DiagnosticFilter.add_integration_include_pattern("Network*")
        self.assertTrue(DiagnosticFilter.should_capture_integration("DeviceCoupling"))
        self.assertTrue(DiagnosticFilter.should_capture_integration("NetworkCoupling"))
        self.assertFalse(DiagnosticFilter.should_capture_integration("DatabaseCoupling"))

    def test_should_capture_integration_with_exact_match_pattern(self):
        """Verify that exact match patterns work correctly."""
        DiagnosticFilter.add_integration_include_pattern("DeviceCoupling")
        self.assertTrue(DiagnosticFilter.should_capture_integration("DeviceCoupling"))
        self.assertFalse(DiagnosticFilter.should_capture_integration("DeviceManager"))

    def test_should_capture_integration_with_question_mark_wildcard(self):
        """Verify that ? wildcard matches single character."""
        DiagnosticFilter.add_integration_include_pattern("Device?")
        self.assertTrue(DiagnosticFilter.should_capture_integration("Device1"))
        self.assertTrue(DiagnosticFilter.should_capture_integration("DeviceA"))
        self.assertFalse(DiagnosticFilter.should_capture_integration("Device12"))

    def test_should_capture_integration_with_character_class(self):
        """Verify that character class patterns work correctly."""
        DiagnosticFilter.add_integration_include_pattern("Device[123]")
        self.assertTrue(DiagnosticFilter.should_capture_integration("Device1"))
        self.assertTrue(DiagnosticFilter.should_capture_integration("Device2"))
        self.assertFalse(DiagnosticFilter.should_capture_integration("Device4"))


class DiagnosticFilterIntegrationExcludeTests(unittest.TestCase):
    """
    Unit tests for DiagnosticFilter integration exclude pattern functionality.
    
    Tests filtering diagnostics by integration type using exclude patterns.
    """

    def setUp(self):
        """Clear all filters before each test to ensure isolation."""
        DiagnosticFilter.clear_all_filters()

    def tearDown(self):
        """Clear all filters after each test to ensure isolation."""
        DiagnosticFilter.clear_all_filters()

    def test_add_integration_exclude_pattern_adds_pattern(self):
        """Verify that adding an integration exclude pattern works."""
        DiagnosticFilter.add_integration_exclude_pattern("*Debug*")
        patterns = DiagnosticFilter.get_integration_exclude_patterns()
        self.assertIn("*Debug*", patterns)

    def test_should_capture_integration_with_matching_exclude_pattern(self):
        """Verify that matching exclude patterns block capture."""
        DiagnosticFilter.add_integration_exclude_pattern("*Debug*")
        self.assertFalse(DiagnosticFilter.should_capture_integration("DeviceDebugCoupling"))
        self.assertFalse(DiagnosticFilter.should_capture_integration("DebugManager"))

    def test_should_capture_integration_with_non_matching_exclude_pattern(self):
        """Verify that non-matching exclude patterns allow capture."""
        DiagnosticFilter.add_integration_exclude_pattern("*Debug*")
        self.assertTrue(DiagnosticFilter.should_capture_integration("DeviceCoupling"))
        self.assertTrue(DiagnosticFilter.should_capture_integration("NetworkCoupling"))

    def test_exclude_takes_precedence_over_include(self):
        """Verify that exclude patterns take precedence over include patterns."""
        DiagnosticFilter.add_integration_include_pattern("Device*")
        DiagnosticFilter.add_integration_exclude_pattern("*Debug*")
        self.assertTrue(DiagnosticFilter.should_capture_integration("DeviceCoupling"))
        self.assertFalse(DiagnosticFilter.should_capture_integration("DeviceDebugCoupling"))


class DiagnosticFilterLabelIncludeTests(unittest.TestCase):
    """
    Unit tests for DiagnosticFilter label include pattern functionality.
    
    Tests filtering diagnostics by label using include patterns.
    """

    def setUp(self):
        """Clear all filters before each test to ensure isolation."""
        DiagnosticFilter.clear_all_filters()

    def tearDown(self):
        """Clear all filters after each test to ensure isolation."""
        DiagnosticFilter.clear_all_filters()

    def test_add_label_include_pattern_adds_pattern(self):
        """Verify that adding a label include pattern works."""
        DiagnosticFilter.add_label_include_pattern("prerun-*")
        patterns = DiagnosticFilter.get_label_include_patterns()
        self.assertIn("prerun-*", patterns)

    def test_should_capture_label_with_no_patterns_returns_true(self):
        """Verify that with no patterns, all labels are captured."""
        self.assertTrue(DiagnosticFilter.should_capture_label("prerun-diagnostic"))
        self.assertTrue(DiagnosticFilter.should_capture_label("postrun-diagnostic"))

    def test_should_capture_label_with_matching_include_pattern(self):
        """Verify that matching include patterns allow capture."""
        DiagnosticFilter.add_label_include_pattern("prerun-*")
        self.assertTrue(DiagnosticFilter.should_capture_label("prerun-diagnostic"))

    def test_should_capture_label_with_non_matching_include_pattern(self):
        """Verify that non-matching include patterns block capture."""
        DiagnosticFilter.add_label_include_pattern("prerun-*")
        self.assertFalse(DiagnosticFilter.should_capture_label("postrun-diagnostic"))

    def test_should_capture_label_with_exact_match(self):
        """Verify that exact match patterns work correctly."""
        DiagnosticFilter.add_label_include_pattern("prerun-diagnostic")
        self.assertTrue(DiagnosticFilter.should_capture_label("prerun-diagnostic"))
        self.assertFalse(DiagnosticFilter.should_capture_label("prerun-diagnostic-extra"))


class DiagnosticFilterLabelExcludeTests(unittest.TestCase):
    """
    Unit tests for DiagnosticFilter label exclude pattern functionality.
    
    Tests filtering diagnostics by label using exclude patterns.
    """

    def setUp(self):
        """Clear all filters before each test to ensure isolation."""
        DiagnosticFilter.clear_all_filters()

    def tearDown(self):
        """Clear all filters after each test to ensure isolation."""
        DiagnosticFilter.clear_all_filters()

    def test_add_label_exclude_pattern_adds_pattern(self):
        """Verify that adding a label exclude pattern works."""
        DiagnosticFilter.add_label_exclude_pattern("debug-*")
        patterns = DiagnosticFilter.get_label_exclude_patterns()
        self.assertIn("debug-*", patterns)

    def test_should_capture_label_with_matching_exclude_pattern(self):
        """Verify that matching exclude patterns block capture."""
        DiagnosticFilter.add_label_exclude_pattern("debug-*")
        self.assertFalse(DiagnosticFilter.should_capture_label("debug-diagnostic"))

    def test_should_capture_label_with_non_matching_exclude_pattern(self):
        """Verify that non-matching exclude patterns allow capture."""
        DiagnosticFilter.add_label_exclude_pattern("debug-*")
        self.assertTrue(DiagnosticFilter.should_capture_label("prerun-diagnostic"))

    def test_label_exclude_takes_precedence_over_include(self):
        """Verify that exclude patterns take precedence over include patterns."""
        DiagnosticFilter.add_label_include_pattern("*-diagnostic")
        DiagnosticFilter.add_label_exclude_pattern("debug-*")
        self.assertTrue(DiagnosticFilter.should_capture_label("prerun-diagnostic"))
        self.assertFalse(DiagnosticFilter.should_capture_label("debug-diagnostic"))


class DiagnosticFilterCombinedTests(unittest.TestCase):
    """
    Unit tests for DiagnosticFilter combined integration and label filtering.
    
    Tests the should_capture method that combines both filters.
    """

    def setUp(self):
        """Clear all filters before each test to ensure isolation."""
        DiagnosticFilter.clear_all_filters()

    def tearDown(self):
        """Clear all filters after each test to ensure isolation."""
        DiagnosticFilter.clear_all_filters()

    def test_should_capture_with_no_filters_returns_true(self):
        """Verify that with no filters, capture is allowed."""
        self.assertTrue(DiagnosticFilter.should_capture("DeviceCoupling", "prerun-diagnostic"))

    def test_should_capture_with_matching_integration_and_label(self):
        """Verify that matching both filters allows capture."""
        DiagnosticFilter.add_integration_include_pattern("Device*")
        DiagnosticFilter.add_label_include_pattern("prerun-*")
        self.assertTrue(DiagnosticFilter.should_capture("DeviceCoupling", "prerun-diagnostic"))

    def test_should_capture_with_non_matching_integration(self):
        """Verify that non-matching integration blocks capture."""
        DiagnosticFilter.add_integration_include_pattern("Device*")
        self.assertFalse(DiagnosticFilter.should_capture("NetworkCoupling", "prerun-diagnostic"))

    def test_should_capture_with_non_matching_label(self):
        """Verify that non-matching label blocks capture."""
        DiagnosticFilter.add_label_include_pattern("prerun-*")
        self.assertFalse(DiagnosticFilter.should_capture("DeviceCoupling", "postrun-diagnostic"))

    def test_should_capture_with_excluded_integration(self):
        """Verify that excluded integration blocks capture."""
        DiagnosticFilter.add_integration_exclude_pattern("*Debug*")
        self.assertFalse(DiagnosticFilter.should_capture("DeviceDebugCoupling", "prerun-diagnostic"))

    def test_should_capture_with_excluded_label(self):
        """Verify that excluded label blocks capture."""
        DiagnosticFilter.add_label_exclude_pattern("debug-*")
        self.assertFalse(DiagnosticFilter.should_capture("DeviceCoupling", "debug-diagnostic"))


class DiagnosticFilterManagementTests(unittest.TestCase):
    """
    Unit tests for DiagnosticFilter management methods.
    
    Tests pattern removal, clearing, and status methods.
    """

    def setUp(self):
        """Clear all filters before each test to ensure isolation."""
        DiagnosticFilter.clear_all_filters()

    def tearDown(self):
        """Clear all filters after each test to ensure isolation."""
        DiagnosticFilter.clear_all_filters()

    def test_remove_integration_include_pattern_succeeds(self):
        """Verify that removing an existing pattern succeeds."""
        DiagnosticFilter.add_integration_include_pattern("Device*")
        result = DiagnosticFilter.remove_integration_include_pattern("Device*")
        self.assertTrue(result)
        self.assertNotIn("Device*", DiagnosticFilter.get_integration_include_patterns())

    def test_remove_integration_include_pattern_fails_for_nonexistent(self):
        """Verify that removing a non-existent pattern fails."""
        result = DiagnosticFilter.remove_integration_include_pattern("NonExistent*")
        self.assertFalse(result)

    def test_remove_integration_exclude_pattern_succeeds(self):
        """Verify that removing an existing exclude pattern succeeds."""
        DiagnosticFilter.add_integration_exclude_pattern("*Debug*")
        result = DiagnosticFilter.remove_integration_exclude_pattern("*Debug*")
        self.assertTrue(result)
        self.assertNotIn("*Debug*", DiagnosticFilter.get_integration_exclude_patterns())

    def test_remove_label_include_pattern_succeeds(self):
        """Verify that removing an existing label include pattern succeeds."""
        DiagnosticFilter.add_label_include_pattern("prerun-*")
        result = DiagnosticFilter.remove_label_include_pattern("prerun-*")
        self.assertTrue(result)
        self.assertNotIn("prerun-*", DiagnosticFilter.get_label_include_patterns())

    def test_remove_label_exclude_pattern_succeeds(self):
        """Verify that removing an existing label exclude pattern succeeds."""
        DiagnosticFilter.add_label_exclude_pattern("debug-*")
        result = DiagnosticFilter.remove_label_exclude_pattern("debug-*")
        self.assertTrue(result)
        self.assertNotIn("debug-*", DiagnosticFilter.get_label_exclude_patterns())

    def test_clear_integration_filters_clears_both_include_and_exclude(self):
        """Verify that clear_integration_filters clears both include and exclude."""
        DiagnosticFilter.add_integration_include_pattern("Device*")
        DiagnosticFilter.add_integration_exclude_pattern("*Debug*")
        DiagnosticFilter.clear_integration_filters()
        self.assertEqual(len(DiagnosticFilter.get_integration_include_patterns()), 0)
        self.assertEqual(len(DiagnosticFilter.get_integration_exclude_patterns()), 0)

    def test_clear_label_filters_clears_both_include_and_exclude(self):
        """Verify that clear_label_filters clears both include and exclude."""
        DiagnosticFilter.add_label_include_pattern("prerun-*")
        DiagnosticFilter.add_label_exclude_pattern("debug-*")
        DiagnosticFilter.clear_label_filters()
        self.assertEqual(len(DiagnosticFilter.get_label_include_patterns()), 0)
        self.assertEqual(len(DiagnosticFilter.get_label_exclude_patterns()), 0)

    def test_clear_all_filters_clears_everything(self):
        """Verify that clear_all_filters clears all patterns."""
        DiagnosticFilter.add_integration_include_pattern("Device*")
        DiagnosticFilter.add_integration_exclude_pattern("*Debug*")
        DiagnosticFilter.add_label_include_pattern("prerun-*")
        DiagnosticFilter.add_label_exclude_pattern("debug-*")
        DiagnosticFilter.clear_all_filters()
        self.assertEqual(len(DiagnosticFilter.get_integration_include_patterns()), 0)
        self.assertEqual(len(DiagnosticFilter.get_integration_exclude_patterns()), 0)
        self.assertEqual(len(DiagnosticFilter.get_label_include_patterns()), 0)
        self.assertEqual(len(DiagnosticFilter.get_label_exclude_patterns()), 0)

    def test_is_filtering_enabled_returns_false_when_no_filters(self):
        """Verify that is_filtering_enabled returns False when no filters."""
        self.assertFalse(DiagnosticFilter.is_filtering_enabled())

    def test_is_filtering_enabled_returns_true_when_filters_exist(self):
        """Verify that is_filtering_enabled returns True when filters exist."""
        DiagnosticFilter.add_integration_include_pattern("Device*")
        self.assertTrue(DiagnosticFilter.is_filtering_enabled())

    def test_get_filter_summary_returns_all_patterns(self):
        """Verify that get_filter_summary returns all configured patterns."""
        DiagnosticFilter.add_integration_include_pattern("Device*")
        DiagnosticFilter.add_integration_exclude_pattern("*Debug*")
        DiagnosticFilter.add_label_include_pattern("prerun-*")
        DiagnosticFilter.add_label_exclude_pattern("debug-*")
        
        summary = DiagnosticFilter.get_filter_summary()
        
        self.assertIn("Device*", summary["integration_include"])
        self.assertIn("*Debug*", summary["integration_exclude"])
        self.assertIn("prerun-*", summary["label_include"])
        self.assertIn("debug-*", summary["label_exclude"])


if __name__ == "__main__":
    unittest.main()
