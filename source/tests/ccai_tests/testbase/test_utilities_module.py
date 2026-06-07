import importlib
import json
import os
import sys
import tempfile
import unittest

from ccai.errors.exceptions import ConfigurationError
from ccai.testbase.utilities import (
    catalog_tree,
    create_testpack_key,
    find_included_modules_under_root,
    find_testmodule_root,
    find_testmodule_fullname,
)


class CatalogTreeTests(unittest.TestCase):
    def test_catalog_tree_writes_catalogs_and_respects_ignore(self):
        with tempfile.TemporaryDirectory() as root:
            os.mkdir(os.path.join(root, "sub"))
            os.mkdir(os.path.join(root, "skip"))
            open(os.path.join(root, "root.txt"), "w").close()
            open(os.path.join(root, "sub", "child.txt"), "w").close()
            open(os.path.join(root, "skip", "ignored.txt"), "w").close()

            catalog_tree(root, ignore_dirs=["skip"])

            with open(os.path.join(root, "catalog.json")) as fh:
                cat = json.load(fh)
            self.assertIn("root.txt", cat["files"])
            self.assertIn("sub", cat["folders"])
            self.assertNotIn("skip", cat["folders"])

            with open(os.path.join(root, "sub", "catalog.json")) as fh:
                subcat = json.load(fh)
            self.assertEqual(subcat["files"], ["child.txt"])
            self.assertEqual(subcat["folders"], [])

            self.assertFalse(os.path.exists(os.path.join(root, "skip", "catalog.json")))


class CreateTestpackKeyTests(unittest.TestCase):
    def test_returns_module_and_name(self):
        class Dummy:
            pass

        key = create_testpack_key(Dummy)
        expected = f"{Dummy.__module__}@{Dummy.__name__}"
        self.assertEqual(key, expected)


class FindIncludedModulesTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tempdir.name, "mypkg")
        os.mkdir(self.root)
        open(os.path.join(self.root, "__init__.py"), "w").close()
        with open(os.path.join(self.root, "mod1.py"), "w") as f:
            f.write("# mod1")
        pkg = os.path.join(self.root, "pkg")
        os.mkdir(pkg)
        open(os.path.join(pkg, "__init__.py"), "w").close()
        with open(os.path.join(pkg, "mod2.py"), "w") as f:
            f.write("# mod2")
        sub = os.path.join(pkg, "sub")
        os.mkdir(sub)
        open(os.path.join(sub, "__init__.py"), "w").close()
        with open(os.path.join(sub, "mod3.py"), "w") as f:
            f.write("# mod3")

    def tearDown(self):
        self.tempdir.cleanup()

    def test_package_none_collects_and_excludes(self):
        excl_prefix = os.path.join(self.root, "pkg", "sub")
        included, excluded = find_included_modules_under_root(
            self.root,
            None,
            "mypkg.pkg",
            [excl_prefix],
        )
        self.assertIn(os.path.join(self.root, "pkg", "mod2.py"), included)
        self.assertIn(os.path.join(excl_prefix, "mod3.py"), excluded)

    def test_package_specific_module(self):
        included, _ = find_included_modules_under_root(
            self.root,
            "mypkg.pkg",
            "mod2",
        )
        self.assertEqual(included, [os.path.join(self.root, "pkg", "mod2.py")])

    def test_package_directory(self):
        included, _ = find_included_modules_under_root(
            self.root,
            "mypkg.pkg",
            "sub",
        )
        self.assertIn(os.path.join(self.root, "pkg", "sub", "mod3.py"), included)


class TestModuleFunctions(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.testroot = os.path.join(self.tempdir.name, "tests")
        os.makedirs(os.path.join(self.testroot, "sub"))
        for path in [self.testroot, os.path.join(self.testroot, "sub")]:
            open(os.path.join(path, "__init__.py"), "w").close()
        open(os.path.join(self.testroot, "__testroot__.py"), "w").close()
        with open(os.path.join(self.testroot, "sub", "mymod.py"), "w") as f:
            f.write("VALUE = 1")

        sys.path.insert(0, self.tempdir.name)
        self.module = importlib.import_module("tests.sub.mymod")

    def tearDown(self):
        sys.path.remove(self.tempdir.name)
        for mod in ["tests.sub.mymod", "tests.sub", "tests"]:
            if mod in sys.modules:
                del sys.modules[mod]
        self.tempdir.cleanup()

    def test_find_testmodule_root(self):
        root = find_testmodule_root(self.module)
        self.assertEqual(root, self.testroot)

    def test_find_testmodule_fullname(self):
        fullname = find_testmodule_fullname(self.module)
        self.assertEqual(fullname, "tests.sub.mymod")

    def test_find_testmodule_root_missing_raises(self):
        with tempfile.TemporaryDirectory() as tdir:
            pkg = os.path.join(tdir, "pkg")
            os.mkdir(pkg)
            open(os.path.join(pkg, "__init__.py"), "w").close()
            modpath = os.path.join(pkg, "mod.py")
            open(modpath, "w").close()
            sys.path.insert(0, tdir)
            try:
                mod = importlib.import_module("pkg.mod")
                with self.assertRaises(ConfigurationError):
                    find_testmodule_root(mod)
            finally:
                sys.path.remove(tdir)
                for m in ["pkg.mod", "pkg"]:
                    sys.modules.pop(m, None)


if __name__ == "__main__":
    unittest.main()
