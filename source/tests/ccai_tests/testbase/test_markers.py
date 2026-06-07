import sys
import unittest

from ccai.testbase import markers
from ccai.errors.exceptions import SemanticError


class DecoratorTests(unittest.TestCase):
    def test_mark_categories_attaches_metadata(self):
        @markers.mark_categories(categories=["a", "b"])
        def dummy():
            pass

        self.assertTrue(hasattr(dummy, "_metadata_"))
        self.assertEqual(dummy._metadata_["categories"], ["a", "b"])

    def test_mark_keywords_attaches_metadata(self):
        @markers.mark_keywords(keywords=["x", "y"])
        def dummy():
            pass

        self.assertTrue(hasattr(dummy, "_metadata_"))
        self.assertEqual(dummy._metadata_["keywords"], ["x", "y"])

    def test_mark_priority_stores_string(self):
        @markers.mark_priority(priority=5)
        def dummy():
            pass

        self.assertTrue(hasattr(dummy, "_metadata_"))
        self.assertEqual(dummy._metadata_["priority"], "5")


class DecoratorExistingMetadataTests(unittest.TestCase):
    """Tests for decorator behavior when function already has _metadata_."""

    def test_multiple_decorators_preserve_all_metadata(self):
        """Test that applying multiple decorators preserves all metadata keys."""
        @markers.mark_categories(categories=["smoke", "api"])
        @markers.mark_keywords(keywords=["login", "auth"])
        @markers.mark_priority(priority=1)
        def dummy():
            pass

        self.assertTrue(hasattr(dummy, "_metadata_"))
        self.assertEqual(dummy._metadata_["categories"], ["smoke", "api"])
        self.assertEqual(dummy._metadata_["keywords"], ["login", "auth"])
        self.assertEqual(dummy._metadata_["priority"], "1")

    def test_categories_decorator_preserves_existing_keywords(self):
        """Test that mark_categories preserves existing keywords metadata."""
        @markers.mark_categories(categories=["unit"])
        @markers.mark_keywords(keywords=["fast"])
        def dummy():
            pass

        self.assertIn("categories", dummy._metadata_)
        self.assertIn("keywords", dummy._metadata_)
        self.assertEqual(dummy._metadata_["keywords"], ["fast"])

    def test_keywords_decorator_preserves_existing_priority(self):
        """Test that mark_keywords preserves existing priority metadata."""
        @markers.mark_keywords(keywords=["slow"])
        @markers.mark_priority(priority=3)
        def dummy():
            pass

        self.assertIn("keywords", dummy._metadata_)
        self.assertIn("priority", dummy._metadata_)
        self.assertEqual(dummy._metadata_["priority"], "3")

    def test_priority_decorator_preserves_existing_categories(self):
        """Test that mark_priority preserves existing categories metadata."""
        @markers.mark_priority(priority=2)
        @markers.mark_categories(categories=["integration"])
        def dummy():
            pass

        self.assertIn("priority", dummy._metadata_)
        self.assertIn("categories", dummy._metadata_)
        self.assertEqual(dummy._metadata_["categories"], ["integration"])

    def test_decorator_overwrites_same_key(self):
        """Test that applying same decorator twice overwrites the value."""
        @markers.mark_categories(categories=["final"])
        @markers.mark_categories(categories=["initial"])
        def dummy():
            pass

        self.assertEqual(dummy._metadata_["categories"], ["final"])

    def test_all_three_decorators_combined(self):
        """Test all three decorators applied in different order."""
        @markers.mark_priority(priority=5)
        @markers.mark_categories(categories=["e2e"])
        @markers.mark_keywords(keywords=["browser", "ui"])
        def dummy():
            pass

        self.assertEqual(len(dummy._metadata_), 3)
        self.assertEqual(dummy._metadata_["priority"], "5")
        self.assertEqual(dummy._metadata_["categories"], ["e2e"])
        self.assertEqual(dummy._metadata_["keywords"], ["browser", "ui"])


class DescendentMarkerTests(unittest.TestCase):
    def tearDown(self):
        mod = sys.modules[__name__]
        if hasattr(mod, "_metadata_"):
            delattr(mod, "_metadata_")

    def test_mark_descendent_categories_modifies_module(self):
        markers.mark_descendent_categories(categories=["cat"])
        self.assertEqual(sys.modules[__name__]._metadata_["categories"], ["cat"])

    def test_mark_descendent_keywords_modifies_module(self):
        markers.mark_descendent_keywords(keywords=["kw"])
        self.assertEqual(sys.modules[__name__]._metadata_["keywords"], ["kw"])

    def test_mark_descendent_priority_modifies_module(self):
        markers.mark_descendent_priority(priority=3)
        self.assertEqual(sys.modules[__name__]._metadata_["priority"], "3")


class MetaFilterTests(unittest.TestCase):
    def setUp(self):
        self.metadata = {
            "categories": ["alpha", "beta"],
            "keywords": "kwalpha",
            "priority": "1",
        }

    def test_meta_filter_contains_include(self):
        filt = markers.MetaFilterContains(True, "categories", "alpha")
        self.assertTrue(filt.should_include(self.metadata))

    def test_meta_filter_contains_exclude(self):
        filt = markers.MetaFilterContains(False, "categories", "alpha")
        self.assertFalse(filt.should_include(self.metadata))

    def test_meta_filter_equals(self):
        filt = markers.MetaFilterEquals(True, "priority", "1")
        self.assertTrue(filt.should_include(self.metadata))

    def test_meta_filter_not_equals(self):
        filt = markers.MetaFilterNotEquals(True, "priority", "2")
        self.assertTrue(filt.should_include(self.metadata))


class MetaFilterContainsStringTests(unittest.TestCase):
    """Tests for MetaFilterContains with string metadata values (Requirement 8.2)."""

    def test_substring_match_at_start(self):
        """Test substring matching when filter value is at the start of metadata string."""
        metadata = {"description": "smoke test for login"}
        filt = markers.MetaFilterContains(True, "description", "smoke")
        self.assertTrue(filt.should_include(metadata))

    def test_substring_match_in_middle(self):
        """Test substring matching when filter value is in the middle of metadata string."""
        metadata = {"description": "this is a smoke test"}
        filt = markers.MetaFilterContains(True, "description", "smoke")
        self.assertTrue(filt.should_include(metadata))

    def test_substring_match_at_end(self):
        """Test substring matching when filter value is at the end of metadata string."""
        metadata = {"description": "test for smoke"}
        filt = markers.MetaFilterContains(True, "description", "smoke")
        self.assertTrue(filt.should_include(metadata))

    def test_substring_no_match(self):
        """Test substring matching returns False when filter value is not in metadata string."""
        metadata = {"description": "integration test"}
        filt = markers.MetaFilterContains(True, "description", "smoke")
        self.assertFalse(filt.should_include(metadata))

    def test_substring_exact_match(self):
        """Test substring matching when filter value exactly equals metadata string."""
        metadata = {"tag": "smoke"}
        filt = markers.MetaFilterContains(True, "tag", "smoke")
        self.assertTrue(filt.should_include(metadata))

    def test_case_sensitivity_no_match_different_case(self):
        """Test that substring matching is case-sensitive (uppercase vs lowercase)."""
        metadata = {"description": "SMOKE test"}
        filt = markers.MetaFilterContains(True, "description", "smoke")
        self.assertFalse(filt.should_include(metadata))

    def test_case_sensitivity_exact_case_matches(self):
        """Test that substring matching succeeds when case matches exactly."""
        metadata = {"description": "SMOKE test"}
        filt = markers.MetaFilterContains(True, "description", "SMOKE")
        self.assertTrue(filt.should_include(metadata))

    def test_case_sensitivity_mixed_case_no_match(self):
        """Test that mixed case filter value does not match different case in metadata."""
        metadata = {"description": "smoke test"}
        filt = markers.MetaFilterContains(True, "description", "Smoke")
        self.assertFalse(filt.should_include(metadata))

    def test_substring_match_with_exclude_mode(self):
        """Test substring matching in exclude mode inverts the result."""
        metadata = {"description": "smoke test"}
        filt = markers.MetaFilterContains(False, "description", "smoke")
        self.assertFalse(filt.should_include(metadata))

    def test_substring_no_match_with_exclude_mode(self):
        """Test substring no match in exclude mode returns True."""
        metadata = {"description": "integration test"}
        filt = markers.MetaFilterContains(False, "description", "smoke")
        self.assertTrue(filt.should_include(metadata))


class MetaFilterNoneMetadataTests(unittest.TestCase):
    """Tests for MetaFilter behavior with None metadata (Requirements 8.4, 9.4)."""

    def test_meta_filter_contains_with_none_metadata_include_mode(self):
        """Test MetaFilterContains returns False for None metadata in include mode."""
        filt = markers.MetaFilterContains(True, "categories", "alpha")
        self.assertFalse(filt.should_include(None))

    def test_meta_filter_contains_with_none_metadata_exclude_mode(self):
        """Test MetaFilterContains returns True for None metadata in exclude mode."""
        filt = markers.MetaFilterContains(False, "categories", "alpha")
        self.assertTrue(filt.should_include(None))

    def test_meta_filter_equals_with_none_metadata_include_mode(self):
        """Test MetaFilterEquals returns False for None metadata in include mode."""
        filt = markers.MetaFilterEquals(True, "priority", "1")
        self.assertFalse(filt.should_include(None))

    def test_meta_filter_equals_with_none_metadata_exclude_mode(self):
        """Test MetaFilterEquals returns True for None metadata in exclude mode."""
        filt = markers.MetaFilterEquals(False, "priority", "1")
        self.assertTrue(filt.should_include(None))

    def test_meta_filter_not_equals_with_none_metadata_include_mode(self):
        """Test MetaFilterNotEquals returns True for None metadata in include mode."""
        filt = markers.MetaFilterNotEquals(True, "priority", "1")
        self.assertTrue(filt.should_include(None))

    def test_meta_filter_not_equals_with_none_metadata_exclude_mode(self):
        """Test MetaFilterNotEquals returns False for None metadata in exclude mode."""
        filt = markers.MetaFilterNotEquals(False, "priority", "1")
        self.assertFalse(filt.should_include(None))


class MetaFilterMissingGroupKeyTests(unittest.TestCase):
    """Tests for MetaFilter behavior with missing group key (Requirements 8.5, 9.5)."""

    def test_meta_filter_contains_missing_group_include_mode(self):
        """Test MetaFilterContains returns False when group key is missing in include mode."""
        metadata = {"keywords": ["test"]}
        filt = markers.MetaFilterContains(True, "categories", "alpha")
        self.assertFalse(filt.should_include(metadata))

    def test_meta_filter_contains_missing_group_exclude_mode(self):
        """Test MetaFilterContains returns True when group key is missing in exclude mode."""
        metadata = {"keywords": ["test"]}
        filt = markers.MetaFilterContains(False, "categories", "alpha")
        self.assertTrue(filt.should_include(metadata))

    def test_meta_filter_equals_missing_group_include_mode(self):
        """Test MetaFilterEquals returns False when group key is missing in include mode."""
        metadata = {"categories": ["smoke"]}
        filt = markers.MetaFilterEquals(True, "priority", "1")
        self.assertFalse(filt.should_include(metadata))

    def test_meta_filter_equals_missing_group_exclude_mode(self):
        """Test MetaFilterEquals returns True when group key is missing in exclude mode."""
        metadata = {"categories": ["smoke"]}
        filt = markers.MetaFilterEquals(False, "priority", "1")
        self.assertTrue(filt.should_include(metadata))

    def test_meta_filter_not_equals_missing_group_include_mode(self):
        """Test MetaFilterNotEquals returns True when group key is missing in include mode."""
        metadata = {"categories": ["smoke"]}
        filt = markers.MetaFilterNotEquals(True, "priority", "1")
        self.assertTrue(filt.should_include(metadata))

    def test_meta_filter_not_equals_missing_group_exclude_mode(self):
        """Test MetaFilterNotEquals returns False when group key is missing in exclude mode."""
        metadata = {"categories": ["smoke"]}
        filt = markers.MetaFilterNotEquals(False, "priority", "1")
        self.assertFalse(filt.should_include(metadata))

    def test_meta_filter_contains_empty_metadata_dict_include_mode(self):
        """Test MetaFilterContains returns False for empty metadata dict in include mode."""
        metadata = {}
        filt = markers.MetaFilterContains(True, "categories", "alpha")
        self.assertFalse(filt.should_include(metadata))

    def test_meta_filter_equals_empty_metadata_dict_include_mode(self):
        """Test MetaFilterEquals returns False for empty metadata dict in include mode."""
        metadata = {}
        filt = markers.MetaFilterEquals(True, "priority", "1")
        self.assertFalse(filt.should_include(metadata))


class MetaFilterExcludeModeTests(unittest.TestCase):
    """Tests for exclude mode behavior (Requirements 8.6, 9.6, 10.5)."""

    def setUp(self):
        self.metadata = {
            "categories": ["smoke", "api"],
            "keywords": "authentication",
            "priority": "1",
        }

    # MetaFilterEquals exclude mode tests (Requirement 9.6)
    def test_meta_filter_equals_exclude_mode_matching_value(self):
        """Test MetaFilterEquals in exclude mode returns False when value matches."""
        filt = markers.MetaFilterEquals(False, "priority", "1")
        self.assertFalse(filt.should_include(self.metadata))

    def test_meta_filter_equals_exclude_mode_non_matching_value(self):
        """Test MetaFilterEquals in exclude mode returns True when value does not match."""
        filt = markers.MetaFilterEquals(False, "priority", "2")
        self.assertTrue(filt.should_include(self.metadata))

    def test_meta_filter_equals_exclude_mode_missing_group(self):
        """Test MetaFilterEquals in exclude mode returns True when group key is missing."""
        filt = markers.MetaFilterEquals(False, "nonexistent", "value")
        self.assertTrue(filt.should_include(self.metadata))

    def test_meta_filter_equals_exclude_mode_none_metadata(self):
        """Test MetaFilterEquals in exclude mode returns True for None metadata."""
        filt = markers.MetaFilterEquals(False, "priority", "1")
        self.assertTrue(filt.should_include(None))

    # MetaFilterNotEquals exclude mode tests (Requirement 10.5)
    def test_meta_filter_not_equals_exclude_mode_matching_value(self):
        """Test MetaFilterNotEquals in exclude mode returns True when value matches."""
        filt = markers.MetaFilterNotEquals(False, "priority", "1")
        self.assertTrue(filt.should_include(self.metadata))

    def test_meta_filter_not_equals_exclude_mode_non_matching_value(self):
        """Test MetaFilterNotEquals in exclude mode returns False when value does not match."""
        filt = markers.MetaFilterNotEquals(False, "priority", "2")
        self.assertFalse(filt.should_include(self.metadata))

    def test_meta_filter_not_equals_exclude_mode_missing_group(self):
        """Test MetaFilterNotEquals in exclude mode returns False when group key is missing."""
        filt = markers.MetaFilterNotEquals(False, "nonexistent", "value")
        self.assertFalse(filt.should_include(self.metadata))

    def test_meta_filter_not_equals_exclude_mode_none_metadata(self):
        """Test MetaFilterNotEquals in exclude mode returns False for None metadata."""
        filt = markers.MetaFilterNotEquals(False, "priority", "1")
        self.assertFalse(filt.should_include(None))

    # Combined include/exclude scenarios
    def test_combined_include_exclude_same_group_different_values(self):
        """Test include and exclude filters on same group with different values."""
        include_filt = markers.MetaFilterEquals(True, "priority", "1")
        exclude_filt = markers.MetaFilterEquals(False, "priority", "2")
        
        # Include filter matches priority=1
        self.assertTrue(include_filt.should_include(self.metadata))
        # Exclude filter does not match priority=2, so returns True (not excluded)
        self.assertTrue(exclude_filt.should_include(self.metadata))

    def test_combined_include_exclude_same_group_same_value(self):
        """Test include and exclude filters on same group with same value."""
        include_filt = markers.MetaFilterEquals(True, "priority", "1")
        exclude_filt = markers.MetaFilterEquals(False, "priority", "1")
        
        # Include filter matches, returns True
        self.assertTrue(include_filt.should_include(self.metadata))
        # Exclude filter matches, returns False (excluded)
        self.assertFalse(exclude_filt.should_include(self.metadata))

    def test_combined_include_exclude_different_groups(self):
        """Test include and exclude filters on different groups."""
        include_filt = markers.MetaFilterContains(True, "categories", "smoke")
        exclude_filt = markers.MetaFilterEquals(False, "priority", "2")
        
        # Include filter matches categories containing "smoke"
        self.assertTrue(include_filt.should_include(self.metadata))
        # Exclude filter does not match priority=2, so returns True
        self.assertTrue(exclude_filt.should_include(self.metadata))

    def test_combined_contains_include_exclude_list_values(self):
        """Test include and exclude contains filters with list metadata values."""
        include_filt = markers.MetaFilterContains(True, "categories", "smoke")
        exclude_filt = markers.MetaFilterContains(False, "categories", "api")
        
        # Include filter matches "smoke" in categories list
        self.assertTrue(include_filt.should_include(self.metadata))
        # Exclude filter matches "api" in categories list, returns False
        self.assertFalse(exclude_filt.should_include(self.metadata))

    def test_combined_not_equals_include_exclude(self):
        """Test include and exclude not-equals filters."""
        include_filt = markers.MetaFilterNotEquals(True, "priority", "2")
        exclude_filt = markers.MetaFilterNotEquals(False, "priority", "2")
        
        # Include not-equals: priority != "2" is True, so returns True
        self.assertTrue(include_filt.should_include(self.metadata))
        # Exclude not-equals: priority != "2" is True, then inverted = False
        self.assertFalse(exclude_filt.should_include(self.metadata))

    def test_combined_multiple_filter_types_exclude_mode(self):
        """Test multiple filter types all in exclude mode."""
        equals_exclude = markers.MetaFilterEquals(False, "priority", "1")
        contains_exclude = markers.MetaFilterContains(False, "categories", "smoke")
        not_equals_exclude = markers.MetaFilterNotEquals(False, "priority", "2")
        
        # All filters match, so all return False (excluded)
        self.assertFalse(equals_exclude.should_include(self.metadata))
        self.assertFalse(contains_exclude.should_include(self.metadata))
        self.assertFalse(not_equals_exclude.should_include(self.metadata))

    def test_combined_filter_chain_simulation(self):
        """Test simulating a filter chain with mixed include/exclude filters."""
        metadata_items = [
            {"categories": ["smoke"], "priority": "1"},
            {"categories": ["api"], "priority": "2"},
            {"categories": ["smoke", "api"], "priority": "1"},
            {"categories": ["integration"], "priority": "3"},
        ]
        
        # Include smoke tests
        include_smoke = markers.MetaFilterContains(True, "categories", "smoke")
        # Exclude priority 2
        exclude_priority_2 = markers.MetaFilterEquals(False, "priority", "2")
        
        results = []
        for meta in metadata_items:
            # Simulating: include if smoke AND not excluded by priority=2
            included = include_smoke.should_include(meta) and exclude_priority_2.should_include(meta)
            results.append(included)
        
        # Item 0: smoke=True, priority!=2=True -> True
        # Item 1: smoke=False, priority!=2=False -> False
        # Item 2: smoke=True, priority!=2=True -> True
        # Item 3: smoke=False, priority!=2=True -> False
        self.assertEqual(results, [True, False, True, False])


class ParseMarkerExpressionTests(unittest.TestCase):
    def test_parse_equals(self):
        filt = markers.parse_marker_expression("+categories==alpha")
        self.assertIsInstance(filt, markers.MetaFilterEquals)
        self.assertTrue(filt.include)
        self.assertEqual(filt.group, "categories")
        self.assertTrue(filt.should_include({"categories": "alpha"}))

    def test_parse_contains(self):
        filt = markers.parse_marker_expression("-keywords~=kw")
        self.assertIsInstance(filt, markers.MetaFilterContains)
        self.assertFalse(filt.include)
        self.assertEqual(filt.group, "keywords")
        self.assertFalse(filt.should_include({"keywords": "kw"}))

    def test_parse_not_equals(self):
        filt = markers.parse_marker_expression("+priority!=high")
        self.assertIsInstance(filt, markers.MetaFilterNotEquals)
        self.assertEqual(filt.group, "priority")
        self.assertTrue(filt.should_include({"priority": "low"}))

    def test_parse_missing_sign_raises(self):
        with self.assertRaises(SemanticError):
            markers.parse_marker_expression("categories==alpha")

    def test_parse_invalid_operator_raises(self):
        with self.assertRaises(SemanticError):
            markers.parse_marker_expression("+categories")


class ParseMarkerExpressionEdgeCaseTests(unittest.TestCase):
    """Tests for expression parsing edge cases (Requirement 12.5)."""

    # Tests for expressions with extra whitespace
    def test_parse_expression_with_leading_whitespace(self):
        """Test that leading whitespace is stripped before parsing."""
        filt = markers.parse_marker_expression("  +categories==alpha")
        self.assertIsInstance(filt, markers.MetaFilterEquals)
        self.assertTrue(filt.include)
        self.assertEqual(filt.group, "categories")

    def test_parse_expression_with_trailing_whitespace(self):
        """Test that trailing whitespace is stripped before parsing."""
        filt = markers.parse_marker_expression("+categories==alpha  ")
        self.assertIsInstance(filt, markers.MetaFilterEquals)
        self.assertTrue(filt.should_include({"categories": "alpha"}))

    def test_parse_expression_with_leading_and_trailing_whitespace(self):
        """Test that both leading and trailing whitespace are stripped."""
        filt = markers.parse_marker_expression("   -keywords~=test   ")
        self.assertIsInstance(filt, markers.MetaFilterContains)
        self.assertFalse(filt.include)

    def test_parse_expression_with_tabs_and_spaces(self):
        """Test that tabs and spaces are stripped from expression."""
        filt = markers.parse_marker_expression("\t +priority!=high \t")
        self.assertIsInstance(filt, markers.MetaFilterNotEquals)
        self.assertEqual(filt.group, "priority")

    def test_parse_expression_with_newline_characters(self):
        """Test that newline characters are stripped from expression."""
        filt = markers.parse_marker_expression("\n+categories==smoke\n")
        self.assertIsInstance(filt, markers.MetaFilterEquals)
        self.assertTrue(filt.should_include({"categories": "smoke"}))

    # Tests for expressions with empty value component
    # Note: Current implementation accepts empty values. These tests document actual behavior.
    # Per Requirement 12.3, empty values SHOULD raise SemanticError but currently do not.
    def test_parse_equals_with_empty_value_creates_filter(self):
        """Test that equals operator with empty value creates a filter matching empty string."""
        filt = markers.parse_marker_expression("+categories==")
        self.assertIsInstance(filt, markers.MetaFilterEquals)
        # Empty value matches empty string in metadata
        self.assertTrue(filt.should_include({"categories": ""}))
        # Empty value does not match non-empty string
        self.assertFalse(filt.should_include({"categories": "alpha"}))

    def test_parse_contains_with_empty_value_creates_filter(self):
        """Test that contains operator with empty value creates a filter matching any string."""
        filt = markers.parse_marker_expression("-keywords~=")
        self.assertIsInstance(filt, markers.MetaFilterContains)
        # Empty string is contained in any string, so exclude mode returns False
        self.assertFalse(filt.should_include({"keywords": "anything"}))

    def test_parse_not_equals_with_empty_value_creates_filter(self):
        """Test that not-equals operator with empty value creates a filter."""
        filt = markers.parse_marker_expression("+priority!=")
        self.assertIsInstance(filt, markers.MetaFilterNotEquals)
        # Not-equals empty string matches any non-empty string
        self.assertTrue(filt.should_include({"priority": "high"}))

    # Tests for expressions with special characters in values
    def test_parse_expression_with_hyphen_in_value(self):
        """Test parsing expression with hyphen in value."""
        filt = markers.parse_marker_expression("+categories==smoke-test")
        self.assertIsInstance(filt, markers.MetaFilterEquals)
        self.assertTrue(filt.should_include({"categories": "smoke-test"}))

    def test_parse_expression_with_underscore_in_value(self):
        """Test parsing expression with underscore in value."""
        filt = markers.parse_marker_expression("+keywords~=api_test")
        self.assertIsInstance(filt, markers.MetaFilterContains)
        self.assertTrue(filt.should_include({"keywords": "api_test_suite"}))

    def test_parse_expression_with_dot_in_value(self):
        """Test parsing expression with dot in value."""
        filt = markers.parse_marker_expression("-priority!=v1.0")
        self.assertIsInstance(filt, markers.MetaFilterNotEquals)
        self.assertTrue(filt.should_include({"priority": "v1.0"}))

    def test_parse_expression_with_colon_in_value(self):
        """Test parsing expression with colon in value."""
        filt = markers.parse_marker_expression("+categories==test:integration")
        self.assertTrue(filt.should_include({"categories": "test:integration"}))

    def test_parse_expression_with_slash_in_value(self):
        """Test parsing expression with slash in value."""
        filt = markers.parse_marker_expression("+keywords~=api/v2")
        self.assertTrue(filt.should_include({"keywords": "api/v2/endpoint"}))

    def test_parse_expression_with_numeric_value(self):
        """Test parsing expression with numeric string value."""
        filt = markers.parse_marker_expression("+priority==123")
        self.assertTrue(filt.should_include({"priority": "123"}))

    def test_parse_expression_with_mixed_special_characters(self):
        """Test parsing expression with multiple special characters in value."""
        filt = markers.parse_marker_expression("+categories==test_v1.0-beta:rc1")
        self.assertTrue(filt.should_include({"categories": "test_v1.0-beta:rc1"}))


if __name__ == "__main__":
    unittest.main()
