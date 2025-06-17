import unittest

from automojo.testbase.features import (
    FeatureTag,
    FeatureAttachedObject,
    FeatureMask,
    FeatureFilter,
)
from automojo.errors.exceptions import SemanticError


class Alpha(FeatureTag):
    pass


class Beta(FeatureTag):
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


if __name__ == "__main__":
    unittest.main()
