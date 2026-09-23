import unittest
import os
import tempfile
from types import ModuleType
import unittest.mock

from ccai.testbase.testcollector import (
    catagorize_exclusions,
    TestCollector,
)
from ccai.testbase.queries import collect_test_references
from ccai.testbase.testref import TestRef
from ccai.testbase.testgroup import TestGroup


class CategorizeExclusionsTests(unittest.TestCase):
    def test_returns_file_exclusions_when_no_at_symbol(self):
        files, specific = catagorize_exclusions(["pkg.module"])
        self.assertEqual(files, ["pkg" + os.sep + "module"])
        self.assertEqual(specific, [])

    def test_with_at_symbol_also_specific(self):
        files, specific = catagorize_exclusions(["pkg.module@Test"])
        self.assertEqual(files, [])
        self.assertEqual(specific, ["pkg.module@Test"])


class CollectReferencesTests(unittest.TestCase):
    def test_collect_references_uses_helpers_and_updates_state(self):
        col = TestCollector(root="/root", excludes=[], metafilters=[])

        def dummy():
            pass
        tref = TestRef(dummy)

        with unittest.mock.patch(
            "ccai.testbase.testcollector.parse_test_include_expression"
        ) as pexp, \
             unittest.mock.patch(
                 "ccai.testbase.testcollector.find_included_modules_under_root"
             ) as finc, \
             unittest.mock.patch(
                 "ccai.testbase.testcollector.collect_test_references"
             ) as crefs:

            pexp.return_value = ("pkg", "mod", None, None)
            finc.return_value = (["f1.py"], ["x.py"])
            crefs.return_value = ({tref.name: tref}, {"err": ("m", "f", "msg")})

            col.collect_references("expr")

            pexp.assert_called_once_with("expr", col._test_module, col._method_prefix)
            finc.assert_called_once_with("/root", "pkg", "mod", excluded_path_prefixes=col._excluded_path_prefixes)
            crefs.assert_called_once()

        self.assertIn(tref.name, col.references)
        self.assertIn("err", col.import_errors)
        self.assertIn("x.py", col._excluded_files)


class FinalizeCollectionTests(unittest.TestCase):
    def test_filters_and_builds_tree(self):
        col = TestCollector(root="/root", excludes=[], metafilters=[object()])

        def f1():
            pass
        def f2():
            pass

        t1 = TestRef(f1)
        t2 = TestRef(f2)
        t1.is_member_of_metaset = unittest.mock.Mock(return_value=True)
        t2.is_member_of_metaset = unittest.mock.Mock(return_value=False)

        col._test_references = {t1.name: t1, t2.name: t2}

        col.finalize_collection()

        self.assertEqual(list(col.references.keys()), [t1.name])
        self.assertIsInstance(col.test_tree, TestGroup)

        node = col.test_tree
        for part in t1.function.__module__.split("."):
            self.assertIn(part, node.children)
            node = node[part]

        self.assertIn(t1.base_name, node.children)
        self.assertIs(node[t1.base_name], t1)


class CollectIntegrationsAndConfigurationsTests(unittest.TestCase):
    class FakeRegistry:
        def __init__(self, unknown=None):
            self.added = []
            self.finalized_with = None
            self.unknown_parameters = unknown or {}
            self.referenced_integrations = {"i": 1}
            self.referenced_configurations = {"c": 2}

        def add_implied_session_resource(self, ident):
            self.added.append(ident)

        def finalize_startup(self, refs):
            self.finalized_with = refs

    def test_returns_registry_values(self):
        col = TestCollector(root="/root", excludes=[], metafilters=[])
        col._test_references = {"a": object()}
        fake = self.FakeRegistry()
        with unittest.mock.patch("ccai.testbase.testcollector.injection_registry", fake):
            integrations, configs = col.collect_integrations_and_configurations()
        self.assertEqual(fake.added, ["sequencer"])
        self.assertIs(fake.finalized_with, col._test_references)
        self.assertEqual(integrations, fake.referenced_integrations)
        self.assertEqual(configs, fake.referenced_configurations)

    def test_raises_on_unknown_parameters(self):
        col = TestCollector(root="/root", excludes=[], metafilters=[])
        col._test_references = {"a": object()}
        fake = self.FakeRegistry({"x": ["p"]})
        with unittest.mock.patch("ccai.testbase.testcollector.injection_registry", fake):
            with self.assertRaises(Exception):
                col.collect_integrations_and_configurations()


class TestRefAsyncFlagTests(unittest.TestCase):
    def test_testref_marks_async_functions(self):
        async def async_test():
            return None

        tref = TestRef(async_test)

        self.assertTrue(tref.is_async)

    def test_testref_marks_sync_functions_as_not_async(self):
        def sync_test():
            return None

        tref = TestRef(sync_test)

        self.assertFalse(tref.is_async)


class QueryCollectionAsyncDetectionTests(unittest.TestCase):
    def test_collect_test_references_marks_async_tests(self):
        async def test_async_example():
            return None

        module_name = 'tests.test_async_module'
        test_async_example.__module__ = module_name

        mod = ModuleType(module_name)
        mod.test_async_example = test_async_example

        with tempfile.TemporaryDirectory() as tempdir:
            root = os.path.join(tempdir, 'tests')
            os.makedirs(root)
            included_file = os.path.join(root, 'test_async_module.py')

            with unittest.mock.patch('ccai.testbase.queries.import_by_name', return_value=mod):
                refs, import_errors = collect_test_references(root, [included_file], None, None, None, 'test')

        self.assertEqual(import_errors, {})
        self.assertIn('tests.test_async_module#test_async_example', refs)
        self.assertTrue(refs['tests.test_async_module#test_async_example'].is_async)


if __name__ == "__main__":
    unittest.main()
