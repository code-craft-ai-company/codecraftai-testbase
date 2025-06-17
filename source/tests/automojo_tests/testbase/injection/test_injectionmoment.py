import collections
import unittest

from automojo.testbase.injection.injectionmoment import InjectionMoment


class DummyFilter:
    def __init__(self, result: bool):
        self._result = result
        self.last_metadata = None

    def should_include(self, metadata):
        self.last_metadata = metadata
        return self._result


def sample_function(a, b):
    return a + b

# Attach some metadata that resolve_metadata will consume
sample_function._metadata_ = {"priority": "high"}


class InjectionMomentTests(unittest.TestCase):

    def test_properties_and_finalize(self):
        im = InjectionMoment(sample_function, monikers=["mon"], pivots=collections.OrderedDict())
        self.assertFalse(im.finalized)
        self.assertEqual(im.base_name, "sample_function")
        self.assertEqual(im.function, sample_function)
        self.assertIn("sample_function", im.name)
        self.assertEqual(im.module_name, sample_function.__module__)

        params = im.function_parameters
        self.assertIn("a", params)
        self.assertIn("b", params)

        im.finalize()
        self.assertTrue(im.finalized)

    def test_metadata_and_membership(self):
        im = InjectionMoment(sample_function)
        im.resolve_metadata()

        true_filter = DummyFilter(True)
        self.assertTrue(im.is_member_of_metaset([true_filter]))
        self.assertIs(true_filter.last_metadata, im._metadata)

        false_filter = DummyFilter(False)
        self.assertFalse(im.is_member_of_metaset([true_filter, false_filter]))


if __name__ == "__main__":
    unittest.main()
