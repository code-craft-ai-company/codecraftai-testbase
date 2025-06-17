import sys
import unittest

from automojo.testbase import markers
from automojo.errors.exceptions import SemanticError


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


if __name__ == "__main__":
    unittest.main()
