"""
    .. module:: ccai_tests.testbase.output.test_outputcontext
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the SimpleOutputContext directory accessors, and for
               ensure_directory -- the mkdir-based creation helper that must
               keep working while a test has os.path.exists patched.

    .. moduleauthor:: CodeCraftX
"""

import os
import tempfile
import unittest

from unittest import mock

from ccai.testbase.output.outputcontext import SimpleOutputContext, ensure_directory


class EnsureDirectoryTests(unittest.TestCase):
    """
        ensure_directory exists because os.makedirs consults os.path.exists to
        decide whether a parent needs creating, and os.path.exists is one of
        the most commonly patched functions in tests.  The regression case: a
        resource factory patches os.path.exists to return True, the framework
        then creates a test's by-products directory whose parent does not
        exist yet, makedirs believes the lying exists() and skips the parent,
        and the leaf mkdir dies with FileNotFoundError -- failing the run from
        inside the framework.
    """

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.base = self.tempdir.name

    def tearDown(self):
        self.tempdir.cleanup()

    def test_creates_leaf_and_missing_parents(self):
        target = os.path.join(self.base, "a", "b", "c")
        ensure_directory(target)
        self.assertTrue(os.path.isdir(target))

    def test_existing_directory_is_fine(self):
        target = os.path.join(self.base, "already")
        os.mkdir(target)
        ensure_directory(target)
        self.assertTrue(os.path.isdir(target))

    def test_creates_missing_parent_while_exists_is_patched_true(self):
        # THE regression: patched exists says everything exists, parent does
        # not.  os.makedirs fails here; ensure_directory must not.
        target = os.path.join(self.base, "missing_parent", "leaf")
        with mock.patch("os.path.exists", return_value=True):
            ensure_directory(target)
        self.assertTrue(os.path.isdir(target))

    def test_creates_directory_while_exists_is_patched_false(self):
        # The inverse lie: exists says nothing exists, everything does.
        target = os.path.join(self.base, "x", "y")
        os.makedirs(target)
        with mock.patch("os.path.exists", return_value=False):
            ensure_directory(target)
        self.assertTrue(os.path.isdir(target))

    def test_unreachable_root_still_raises(self):
        # When the filesystem genuinely refuses, the error must surface, not
        # loop -- dirname('/') == '/' is the recursion's hard stop.
        with mock.patch("os.mkdir", side_effect=FileNotFoundError(2, "No such file or directory")):
            with self.assertRaises(FileNotFoundError):
                ensure_directory("/")


class SimpleOutputContextDirectoryTests(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.ctx = SimpleOutputContext(base_dir=self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_byproducts_dir_created_under_patched_exists(self):
        # The framework-level statement of the regression: creating a test's
        # by-products directory must survive a test that patches
        # os.path.exists, because the patch is ACTIVE while the framework
        # enters the test scope.
        with mock.patch("os.path.exists", return_value=True):
            byproducts = self.ctx.get_testcase_byproducts_dir("some-test-uuid-1")
        self.assertTrue(os.path.isdir(byproducts))

    def test_byproducts_dir_normalizes_test_id(self):
        byproducts = self.ctx.get_testcase_byproducts_dir("pkg.module#test one")
        self.assertTrue(os.path.isdir(byproducts))
        self.assertNotIn(".", os.path.basename(byproducts))
        self.assertNotIn(" ", os.path.basename(byproducts))

    def test_diagnostics_dir_created(self):
        diagnostics = self.ctx.get_diagnostics_dir("post-run")
        self.assertTrue(os.path.isdir(diagnostics))


if __name__ == "__main__":
    unittest.main()
