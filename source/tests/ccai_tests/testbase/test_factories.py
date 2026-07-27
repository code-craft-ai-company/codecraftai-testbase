"""
    Tests for the resource factories testbase provides itself.
"""

import os
import pathlib
import shutil
import unittest

from ccai.testbase.factories import create_temporary_directory


class CreateTemporaryDirectoryTests(unittest.TestCase):
    """
        Verifies the temporary-directory factory.
    """

    def test_yields_a_pathlib_path(self):
        """
            The value is a Path so callers can use `directory / "name"`.
            A str would break that operator with a TypeError naming str
            rather than the factory.
        """
        generator = create_temporary_directory()
        directory = next(generator)
        try:
            self.assertIsInstance(directory, pathlib.Path)
            child = directory / "child.txt"
            child.write_text("content")
            self.assertTrue(child.is_file())
        finally:
            self._exhaust(generator)

    def test_yields_an_empty_existing_directory(self):
        generator = create_temporary_directory()
        directory = next(generator)
        try:
            self.assertTrue(os.path.isdir(directory))
            self.assertEqual(os.listdir(directory), [])
        finally:
            self._exhaust(generator)

    def test_removes_the_directory_and_its_contents_after_the_yield(self):
        generator = create_temporary_directory()
        directory = next(generator)
        with open(os.path.join(directory, "written.txt"), "w") as handle:
            handle.write("content")

        self._exhaust(generator)

        # Cleanup follows the yield, so it runs whether the test passed or
        # failed — and it takes the contents with it.
        self.assertFalse(os.path.exists(directory))

    def test_tolerates_a_directory_the_test_already_removed(self):
        """
            A test that tears down its own workspace must not then fail in
            cleanup for having been tidy.
        """
        generator = create_temporary_directory()
        directory = next(generator)
        shutil.rmtree(directory)

        self._exhaust(generator)

        self.assertFalse(os.path.exists(directory))

    def test_keep_constraint_leaves_the_directory(self):
        generator = create_temporary_directory({"keep": True})
        directory = next(generator)
        self._exhaust(generator)

        try:
            self.assertTrue(os.path.isdir(directory))
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_prefix_constraint_names_the_directory(self):
        """
            The prefix makes a stray directory attributable when one survives.
        """
        generator = create_temporary_directory({"prefix": "named-case-"})
        directory = next(generator)
        try:
            self.assertTrue(os.path.basename(directory).startswith(
                "named-case-"))
        finally:
            self._exhaust(generator)

    def test_each_call_yields_a_distinct_directory(self):
        first_gen = create_temporary_directory()
        second_gen = create_temporary_directory()
        first = next(first_gen)
        second = next(second_gen)
        try:
            self.assertNotEqual(first, second)
        finally:
            self._exhaust(first_gen)
            self._exhaust(second_gen)

    @staticmethod
    def _exhaust(generator):
        try:
            next(generator)
        except StopIteration:
            pass


if __name__ == "__main__":
    unittest.main()
