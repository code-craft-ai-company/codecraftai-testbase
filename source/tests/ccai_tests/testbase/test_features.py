import unittest

from ccai.testbase.features import (
    FeatureTag,
    FeatureAttachedObject,
    FeatureMask,
    FeatureFilter,
)
from ccai.errors.exceptions import SemanticError


class Alpha(FeatureTag):
    pass


class Beta(FeatureTag):
    pass


# Nested FeatureTag hierarchies for testing ID generation
class Network(FeatureTag):
    """Top-level network feature tag."""

    class Wifi(FeatureTag):
        """Second-level wifi feature tag."""

        class Band5GHz(FeatureTag):
            """Third-level 5GHz band feature tag."""
            pass

        class Band2_4GHz(FeatureTag):
            """Third-level 2.4GHz band feature tag."""
            pass

    class Bluetooth(FeatureTag):
        """Second-level bluetooth feature tag."""

        class BLE(FeatureTag):
            """Third-level BLE feature tag."""

            class Version5(FeatureTag):
                """Fourth-level BLE version 5 feature tag."""
                pass

        class Classic(FeatureTag):
            """Third-level classic bluetooth feature tag."""
            pass


class MyObject(FeatureAttachedObject):
    FEATURE_TAGS = [Alpha]


def create_beta_object():
    class BetaObject(FeatureAttachedObject):
        FEATURE_TAGS = [Beta]
    return BetaObject()


class FeatureTagMetaTests(unittest.TestCase):
    def test_meta_assigns_id_and_string(self):
        self.assertEqual(Alpha.ID, "alpha")
        self.assertEqual(repr(Alpha), "'alpha'")
        self.assertEqual(str(Alpha), "alpha")


class NestedFeatureTagHierarchyTests(unittest.TestCase):
    """Tests for nested FeatureTag hierarchies and ID generation."""

    def test_top_level_tag_id_generation(self):
        """Test that top-level FeatureTag generates simple lowercase ID."""
        self.assertEqual(Network.ID, "network")

    def test_two_level_nested_tag_id_generation(self):
        """Test that second-level nested FeatureTag generates ID with forward slash."""
        self.assertEqual(Network.Wifi.ID, "network/wifi")
        self.assertEqual(Network.Bluetooth.ID, "network/bluetooth")

    def test_three_level_nested_tag_id_generation(self):
        """Test that third-level nested FeatureTag generates ID with two forward slashes."""
        self.assertEqual(Network.Wifi.Band5GHz.ID, "network/wifi/band5ghz")
        self.assertEqual(Network.Wifi.Band2_4GHz.ID, "network/wifi/band2_4ghz")
        self.assertEqual(Network.Bluetooth.BLE.ID, "network/bluetooth/ble")
        self.assertEqual(Network.Bluetooth.Classic.ID, "network/bluetooth/classic")

    def test_four_level_nested_tag_id_generation(self):
        """Test that fourth-level nested FeatureTag generates ID with three forward slashes."""
        self.assertEqual(Network.Bluetooth.BLE.Version5.ID, "network/bluetooth/ble/version5")

    def test_nested_tag_repr_format(self):
        """Test that nested FeatureTag __repr__ returns ID wrapped in single quotes."""
        self.assertEqual(repr(Network.Wifi), "'network/wifi'")
        self.assertEqual(repr(Network.Wifi.Band5GHz), "'network/wifi/band5ghz'")
        self.assertEqual(repr(Network.Bluetooth.BLE.Version5), "'network/bluetooth/ble/version5'")

    def test_nested_tag_str_format(self):
        """Test that nested FeatureTag __str__ returns ID without quotes."""
        self.assertEqual(str(Network.Wifi), "network/wifi")
        self.assertEqual(str(Network.Wifi.Band5GHz), "network/wifi/band5ghz")
        self.assertEqual(str(Network.Bluetooth.BLE.Version5), "network/bluetooth/ble/version5")

    def test_nested_tags_usable_with_feature_attached_object(self):
        """Test that nested FeatureTags can be used with FeatureAttachedObject."""
        obj = FeatureAttachedObject()
        obj.extend_features([Network.Wifi.Band5GHz, Network.Bluetooth.BLE])

        self.assertTrue(obj.has_feature(Network.Wifi.Band5GHz))
        self.assertTrue(obj.has_feature(Network.Bluetooth.BLE))
        self.assertTrue(obj.has_feature("network/wifi/band5ghz"))
        self.assertTrue(obj.has_feature("network/bluetooth/ble"))

    def test_nested_tags_in_has_all_features(self):
        """Test that nested FeatureTags work with has_all_features."""
        obj = FeatureAttachedObject()
        obj.extend_features([Network.Wifi.Band5GHz, Network.Bluetooth.BLE.Version5])

        self.assertTrue(obj.has_all_features([Network.Wifi.Band5GHz, Network.Bluetooth.BLE.Version5]))
        self.assertFalse(obj.has_all_features([Network.Wifi.Band5GHz, Network.Wifi.Band2_4GHz]))

    def test_nested_tags_in_has_any_feature(self):
        """Test that nested FeatureTags work with has_any_feature."""
        obj = FeatureAttachedObject()
        obj.extend_features([Network.Wifi.Band5GHz])

        self.assertTrue(obj.has_any_feature([Network.Wifi.Band5GHz, Network.Bluetooth.BLE]))
        self.assertFalse(obj.has_any_feature([Network.Bluetooth.BLE, Network.Bluetooth.Classic]))


class FeatureAttachedObjectTests(unittest.TestCase):
    def setUp(self):
        self.obj = MyObject()

    def test_constructor_populates_feature_tags(self):
        self.assertIn("alpha", self.obj.feature_tags)

    def test_extend_features_with_classes_and_strings(self):
        self.obj.extend_features([Beta])
        self.obj.extend_features(["gamma", "beta"])
        self.assertEqual(
            list(self.obj._feature_tags),
            sorted(["alpha", "beta", "beta", "gamma"]),
        )

    def test_extend_features_invalid_type(self):
        with self.assertRaises(SemanticError):
            self.obj.extend_features([object])

    def test_extend_features_type_error(self):
        with self.assertRaises(TypeError):
            self.obj.extend_features([1])

    def test_has_all_features(self):
        self.obj.extend_features([Beta])
        self.assertTrue(self.obj.has_all_features([Alpha, Beta]))
        self.assertTrue(self.obj.has_all_features(["alpha", "beta"]))
        self.assertFalse(self.obj.has_all_features(["alpha", "z"]))
        with self.assertRaises(SemanticError):
            self.obj.has_all_features([])
        with self.assertRaises(TypeError):
            self.obj.has_all_features([1])

    def test_has_any_feature(self):
        self.obj.extend_features([Beta])
        self.assertTrue(self.obj.has_any_feature([Beta]))
        self.assertTrue(self.obj.has_any_feature(["beta", "z"]))
        self.assertFalse(self.obj.has_any_feature(["gamma"]))
        with self.assertRaises(SemanticError):
            self.obj.has_any_feature([])
        with self.assertRaises(TypeError):
            self.obj.has_any_feature([1])

    def test_has_feature(self):
        self.assertTrue(self.obj.has_feature(Alpha))
        self.assertTrue(self.obj.has_feature("alpha"))
        self.assertFalse(self.obj.has_feature("beta"))
        with self.assertRaises(TypeError):
            self.obj.has_feature(1)


class DuplicateFeatureHandlingTests(unittest.TestCase):
    """Tests for duplicate feature handling in FeatureAttachedObject."""

    def test_extend_features_with_duplicate_feature_tag_classes(self):
        """Test that adding the same FeatureTag class multiple times results in duplicates in the internal list."""
        obj = FeatureAttachedObject()
        obj.extend_features([Alpha])
        obj.extend_features([Alpha])
        obj.extend_features([Alpha])

        # The internal list should contain duplicates
        self.assertEqual(obj._feature_tags.count("alpha"), 3)

    def test_extend_features_with_duplicate_string_identifiers(self):
        """Test that adding the same string identifier multiple times results in duplicates in the internal list."""
        obj = FeatureAttachedObject()
        obj.extend_features(["feature_a"])
        obj.extend_features(["feature_a"])
        obj.extend_features(["feature_a", "feature_a"])

        # The internal list should contain duplicates
        self.assertEqual(obj._feature_tags.count("feature_a"), 4)

    def test_sorted_list_maintains_duplicates_in_order(self):
        """Test that the sorted list maintains duplicates in sorted order."""
        obj = FeatureAttachedObject()
        obj.extend_features(["zebra", "alpha", "alpha", "beta", "alpha"])

        # Verify the list is sorted and contains all duplicates
        expected = ["alpha", "alpha", "alpha", "beta", "zebra"]
        self.assertEqual(obj._feature_tags, expected)

    def test_feature_tags_property_deduplicates_via_frozenset(self):
        """Test that the feature_tags property returns a frozenset which naturally deduplicates."""
        obj = FeatureAttachedObject()
        obj.extend_features([Alpha, Alpha, Alpha])
        obj.extend_features(["beta", "beta"])

        # The frozenset should deduplicate
        self.assertEqual(obj.feature_tags, frozenset(["alpha", "beta"]))

    def test_has_feature_works_with_duplicates(self):
        """Test that has_feature returns True when feature exists (regardless of duplicates)."""
        obj = FeatureAttachedObject()
        obj.extend_features([Alpha, Alpha])

        self.assertTrue(obj.has_feature(Alpha))
        self.assertTrue(obj.has_feature("alpha"))

    def test_has_all_features_works_with_duplicates(self):
        """Test that has_all_features works correctly when features have duplicates."""
        obj = FeatureAttachedObject()
        obj.extend_features([Alpha, Alpha, Beta])

        self.assertTrue(obj.has_all_features([Alpha, Beta]))
        self.assertTrue(obj.has_all_features(["alpha", "beta"]))

    def test_has_any_feature_works_with_duplicates(self):
        """Test that has_any_feature works correctly when features have duplicates."""
        obj = FeatureAttachedObject()
        obj.extend_features([Alpha, Alpha])

        self.assertTrue(obj.has_any_feature([Alpha]))
        self.assertTrue(obj.has_any_feature(["alpha", "gamma"]))

    def test_mixed_duplicate_additions_maintain_sorted_order(self):
        """Test that mixed additions of FeatureTag classes and strings maintain sorted order with duplicates."""
        obj = FeatureAttachedObject()
        obj.extend_features([Beta])  # "beta"
        obj.extend_features(["alpha"])
        obj.extend_features([Alpha])  # "alpha" again
        obj.extend_features(["beta"])  # "beta" again

        # Verify sorted order with duplicates
        expected = ["alpha", "alpha", "beta", "beta"]
        self.assertEqual(obj._feature_tags, expected)


class FeatureMaskAndFilterTests(unittest.TestCase):
    def test_feature_mask_initialization(self):
        mask = FeatureMask(required_features=[Alpha], excluded_features=[Beta])
        self.assertEqual(mask["required_features"], [Alpha])
        self.assertEqual(mask["excluded_features"], [Beta])

    def test_filter(self):
        a = MyObject()
        b = create_beta_object()

        filt = FeatureFilter(required_features=[Alpha], excluded_features=[Beta])
        result = filt.filter([a, b])
        self.assertEqual(result, [a])

        filt2 = FeatureFilter(required_features=["beta"])
        result2 = filt2.filter([a, b])
        self.assertEqual(result2, [b])


class FeatureTagsPropertyImmutabilityTests(unittest.TestCase):
    """Tests for feature_tags property immutability (Requirements 7.3)."""

    def test_feature_tags_returns_frozenset(self):
        """Test that feature_tags property returns a frozenset type."""
        obj = FeatureAttachedObject()
        obj.extend_features([Alpha, Beta])

        result = obj.feature_tags

        self.assertIsInstance(result, frozenset)

    def test_frozenset_cannot_be_modified_with_add(self):
        """Test that the returned frozenset cannot be modified using add method."""
        obj = FeatureAttachedObject()
        obj.extend_features([Alpha])

        result = obj.feature_tags

        # frozenset does not have an add method, attempting to call it should raise AttributeError
        with self.assertRaises(AttributeError):
            result.add("gamma")

    def test_frozenset_cannot_be_modified_with_remove(self):
        """Test that the returned frozenset cannot be modified using remove method."""
        obj = FeatureAttachedObject()
        obj.extend_features([Alpha])

        result = obj.feature_tags

        # frozenset does not have a remove method, attempting to call it should raise AttributeError
        with self.assertRaises(AttributeError):
            result.remove("alpha")

    def test_frozenset_cannot_be_modified_with_discard(self):
        """Test that the returned frozenset cannot be modified using discard method."""
        obj = FeatureAttachedObject()
        obj.extend_features([Alpha])

        result = obj.feature_tags

        # frozenset does not have a discard method, attempting to call it should raise AttributeError
        with self.assertRaises(AttributeError):
            result.discard("alpha")

    def test_frozenset_cannot_be_modified_with_update(self):
        """Test that the returned frozenset cannot be modified using update method."""
        obj = FeatureAttachedObject()
        obj.extend_features([Alpha])

        result = obj.feature_tags

        # frozenset does not have an update method, attempting to call it should raise AttributeError
        with self.assertRaises(AttributeError):
            result.update(["gamma"])

    def test_modifications_to_returned_frozenset_do_not_affect_internal_state(self):
        """Test that creating a new set from the frozenset and modifying it does not affect internal state."""
        obj = FeatureAttachedObject()
        obj.extend_features([Alpha, Beta])

        # Get the frozenset and convert to a mutable set
        result = obj.feature_tags
        mutable_copy = set(result)
        mutable_copy.add("gamma")
        mutable_copy.remove("alpha")

        # Verify internal state is unchanged
        self.assertIn("alpha", obj._feature_tags)
        self.assertNotIn("gamma", obj._feature_tags)
        self.assertEqual(obj.feature_tags, frozenset(["alpha", "beta"]))

    def test_multiple_calls_return_independent_frozensets(self):
        """Test that multiple calls to feature_tags return independent frozenset instances."""
        obj = FeatureAttachedObject()
        obj.extend_features([Alpha])

        result1 = obj.feature_tags
        result2 = obj.feature_tags

        # Both should have the same content
        self.assertEqual(result1, result2)

        # Modifying internal state should reflect in new calls but not affect previously returned frozensets
        obj.extend_features([Beta])
        result3 = obj.feature_tags

        # result1 and result2 should still only have alpha (frozensets are immutable)
        self.assertEqual(result1, frozenset(["alpha"]))
        self.assertEqual(result2, frozenset(["alpha"]))
        # result3 should have both alpha and beta
        self.assertEqual(result3, frozenset(["alpha", "beta"]))

    def test_internal_list_modification_does_not_affect_previously_returned_frozenset(self):
        """Test that modifying internal _feature_tags list does not affect previously returned frozenset."""
        obj = FeatureAttachedObject()
        obj.extend_features([Alpha])

        # Get the frozenset before modification
        before_modification = obj.feature_tags

        # Modify internal state
        obj.extend_features([Beta])

        # The previously returned frozenset should be unchanged
        self.assertEqual(before_modification, frozenset(["alpha"]))
        self.assertNotIn("beta", before_modification)


class MixedTypeValidationTests(unittest.TestCase):
    """Tests for mixed type validation in feature methods (Requirements 6.2, 6.3).
    
    These tests document the current behavior when mixed lists (containing both
    strings and FeatureTag subclasses) are passed to feature methods. The current
    implementation only checks the first item's type and assumes all items are
    the same type, which can lead to unexpected behavior with mixed lists.
    """

    def setUp(self):
        """Set up test object for mixed type validation tests."""
        self.obj = FeatureAttachedObject()

    def test_extend_features_mixed_list_string_first_then_feature_tag(self):
        """Test extend_features with mixed list starting with string then FeatureTag.
        
        When the first item is a string, subsequent FeatureTag items will cause
        a TypeError because bisect.insort tries to compare string with FeatureTag class.
        Requirements: 6.2, 6.3
        """
        # When first item is string, the code tries to insert all items as strings
        # FeatureTag classes are not strings, so bisect.insort will fail with TypeError
        with self.assertRaises(TypeError):
            self.obj.extend_features(["alpha", Alpha])

    def test_extend_features_mixed_list_feature_tag_first_then_string(self):
        """Test extend_features with mixed list starting with FeatureTag then string.
        
        When the first item is a FeatureTag, subsequent string items will cause
        an AttributeError because the code tries to access .ID on a string.
        Requirements: 6.2, 6.3
        """
        # When first item is FeatureTag, the code tries to access .ID on all items
        # Strings don't have .ID attribute, so it will fail with AttributeError
        with self.assertRaises(AttributeError):
            self.obj.extend_features([Alpha, "beta"])

    def test_has_all_features_mixed_list_string_first_then_feature_tag(self):
        """Test has_all_features with mixed list starting with string then FeatureTag.
        
        When the first item is a string, subsequent FeatureTag items will cause
        unexpected behavior because the code checks if FeatureTag class is in the list.
        Requirements: 6.2, 6.3
        """
        self.obj.extend_features([Alpha, Beta])
        
        # When first item is string, the code treats all items as strings
        # FeatureTag class objects are not in _feature_tags (only their IDs are)
        # This will return False because Alpha class is not in the string list
        result = self.obj.has_all_features(["alpha", Alpha])
        self.assertFalse(result)

    def test_has_all_features_mixed_list_feature_tag_first_then_string(self):
        """Test has_all_features with mixed list starting with FeatureTag then string.
        
        When the first item is a FeatureTag, subsequent string items will cause
        an AttributeError because the code tries to access .ID on a string.
        Requirements: 6.2, 6.3
        """
        self.obj.extend_features([Alpha, Beta])
        
        # When first item is FeatureTag, the code tries to access .ID on all items
        # Strings don't have .ID attribute, so it will fail with AttributeError
        with self.assertRaises(AttributeError):
            self.obj.has_all_features([Alpha, "beta"])

    def test_has_any_feature_mixed_list_string_first_then_feature_tag(self):
        """Test has_any_feature with mixed list starting with string then FeatureTag.
        
        When the first item is a string, subsequent FeatureTag items will cause
        unexpected behavior because the code checks if FeatureTag class is in the list.
        Requirements: 6.2, 6.3
        """
        self.obj.extend_features([Alpha])
        
        # When first item is string, the code treats all items as strings
        # If "alpha" is found first, it returns True without checking Beta
        result = self.obj.has_any_feature(["alpha", Beta])
        self.assertTrue(result)
        
        # If the string is not found, it will check Beta class which won't be found
        # because FeatureTag class objects are not in _feature_tags
        result2 = self.obj.has_any_feature(["gamma", Beta])
        self.assertFalse(result2)

    def test_has_any_feature_mixed_list_feature_tag_first_then_string(self):
        """Test has_any_feature with mixed list starting with FeatureTag then string.
        
        When the first item is a FeatureTag, subsequent string items will cause
        an AttributeError because the code tries to access .ID on a string.
        Requirements: 6.2, 6.3
        """
        self.obj.extend_features([Alpha])
        
        # When first item is FeatureTag, the code tries to access .ID on all items
        # Strings don't have .ID attribute, so it will fail with AttributeError
        with self.assertRaises(AttributeError):
            self.obj.has_any_feature([Beta, "alpha"])


class FeatureFilterNoneParameterTests(unittest.TestCase):
    """Tests for FeatureFilter with None parameters (Requirements 13.5, 13.6)."""

    def setUp(self):
        """Set up test objects with different feature tags."""
        self.alpha_obj = MyObject()  # Has Alpha feature
        self.beta_obj = create_beta_object()  # Has Beta feature
        
        # Create an object with both Alpha and Beta features
        self.alpha_beta_obj = MyObject()
        self.alpha_beta_obj.extend_features([Beta])

    def test_filter_with_only_required_features_set(self):
        """Test filtering with only required_features set (excluded_features is None).
        
        Requirements: 13.5 - WHEN required features are None, THE System SHALL not filter based on required features
        """
        # Filter with only required_features, excluded_features defaults to None
        filt = FeatureFilter(required_features=[Alpha])
        
        result = filt.filter([self.alpha_obj, self.beta_obj, self.alpha_beta_obj])
        
        # Should include objects with Alpha feature (alpha_obj and alpha_beta_obj)
        self.assertEqual(len(result), 2)
        self.assertIn(self.alpha_obj, result)
        self.assertIn(self.alpha_beta_obj, result)
        self.assertNotIn(self.beta_obj, result)

    def test_filter_with_only_excluded_features_set(self):
        """Test filtering with only excluded_features set (required_features is None).
        
        Requirements: 13.6 - WHEN excluded features are None, THE System SHALL not filter based on excluded features
        """
        # Filter with only excluded_features, required_features defaults to None
        filt = FeatureFilter(excluded_features=[Beta])
        
        result = filt.filter([self.alpha_obj, self.beta_obj, self.alpha_beta_obj])
        
        # Should exclude objects with Beta feature (beta_obj and alpha_beta_obj)
        # Should include only alpha_obj
        self.assertEqual(len(result), 1)
        self.assertIn(self.alpha_obj, result)
        self.assertNotIn(self.beta_obj, result)
        self.assertNotIn(self.alpha_beta_obj, result)

    def test_filter_with_both_parameters_as_none(self):
        """Test filtering with both required_features and excluded_features as None.
        
        Requirements: 13.5, 13.6 - When both are None, all objects should pass through
        """
        # Filter with both parameters as None (default)
        filt = FeatureFilter()
        
        result = filt.filter([self.alpha_obj, self.beta_obj, self.alpha_beta_obj])
        
        # Should include all objects since no filtering criteria is applied
        self.assertEqual(len(result), 3)
        self.assertIn(self.alpha_obj, result)
        self.assertIn(self.beta_obj, result)
        self.assertIn(self.alpha_beta_obj, result)

    def test_filter_with_none_preserves_order(self):
        """Test that filtering with None parameters preserves original order."""
        filt = FeatureFilter()
        
        input_list = [self.beta_obj, self.alpha_obj, self.alpha_beta_obj]
        result = filt.filter(input_list)
        
        # Order should be preserved
        self.assertEqual(result, input_list)

    def test_filter_with_empty_list_and_none_parameters(self):
        """Test filtering an empty list with None parameters."""
        filt = FeatureFilter()
        
        result = filt.filter([])
        
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
