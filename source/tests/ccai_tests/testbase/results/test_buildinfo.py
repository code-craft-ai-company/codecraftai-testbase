"""
    .. module:: ccai_tests.testbase.results.test_buildinfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the BuildInfo dataclass.

    .. moduleauthor:: CodeCraftX
"""

import unittest
from dataclasses import is_dataclass

from ccai.testbase.results.model.buildinfo import BuildInfo


class BuildInfoInstantiationTests(unittest.TestCase):
    """Tests for BuildInfo dataclass instantiation with all fields."""

    def test_instantiation_with_all_fields(self):
        """Test that BuildInfo can be instantiated with all required fields."""
        build_info = BuildInfo(
            branch="main",
            build="build-123",
            flavor="release",
            release="1.0.0",
            url="https://ci.example.com/build/123"
        )

        self.assertIsInstance(build_info, BuildInfo)

    def test_is_dataclass(self):
        """Test that BuildInfo is a dataclass (Requirement 1.6)."""
        self.assertTrue(is_dataclass(BuildInfo))


class BuildInfoFieldAccessTests(unittest.TestCase):
    """Tests for BuildInfo field access and values."""

    def setUp(self):
        """Set up test fixtures."""
        self.branch_value = "feature/test-branch"
        self.build_value = "build-456"
        self.flavor_value = "debug"
        self.release_value = "2.0.0-beta"
        self.url_value = "https://ci.example.com/build/456"

        self.build_info = BuildInfo(
            branch=self.branch_value,
            build=self.build_value,
            flavor=self.flavor_value,
            release=self.release_value,
            url=self.url_value
        )

    def test_branch_field_access(self):
        """Test branch field access (Requirement 1.1)."""
        self.assertEqual(self.build_info.branch, self.branch_value)
        self.assertIsInstance(self.build_info.branch, str)

    def test_build_field_access(self):
        """Test build field access (Requirement 1.2)."""
        self.assertEqual(self.build_info.build, self.build_value)
        self.assertIsInstance(self.build_info.build, str)

    def test_flavor_field_access(self):
        """Test flavor field access (Requirement 1.3)."""
        self.assertEqual(self.build_info.flavor, self.flavor_value)
        self.assertIsInstance(self.build_info.flavor, str)

    def test_release_field_access(self):
        """Test release field access (Requirement 1.4)."""
        self.assertEqual(self.build_info.release, self.release_value)
        self.assertIsInstance(self.build_info.release, str)

    def test_url_field_access(self):
        """Test url field access (Requirement 1.5)."""
        self.assertEqual(self.build_info.url, self.url_value)
        self.assertIsInstance(self.build_info.url, str)


if __name__ == "__main__":
    unittest.main()


class BuildInfoValidationTests(unittest.TestCase):
    """Tests for BuildInfo field validation (Requirements 15.1-15.5)."""

    def test_raises_error_when_branch_is_none(self):
        """Test that ValueError is raised when branch is None."""
        with self.assertRaises(ValueError) as context:
            BuildInfo(
                branch=None,
                build="build-123",
                flavor="release",
                release="1.0.0",
                url="https://ci.example.com/build/123"
            )
        self.assertIn("branch", str(context.exception))
        self.assertIn("required", str(context.exception))

    def test_raises_error_when_branch_is_empty(self):
        """Test that ValueError is raised when branch is empty string."""
        with self.assertRaises(ValueError) as context:
            BuildInfo(
                branch="",
                build="build-123",
                flavor="release",
                release="1.0.0",
                url="https://ci.example.com/build/123"
            )
        self.assertIn("branch", str(context.exception))

    def test_raises_error_when_branch_is_whitespace(self):
        """Test that ValueError is raised when branch is whitespace only."""
        with self.assertRaises(ValueError) as context:
            BuildInfo(
                branch="   ",
                build="build-123",
                flavor="release",
                release="1.0.0",
                url="https://ci.example.com/build/123"
            )
        self.assertIn("branch", str(context.exception))

    def test_raises_error_when_build_is_none(self):
        """Test that ValueError is raised when build is None."""
        with self.assertRaises(ValueError) as context:
            BuildInfo(
                branch="main",
                build=None,
                flavor="release",
                release="1.0.0",
                url="https://ci.example.com/build/123"
            )
        self.assertIn("build", str(context.exception))
        self.assertIn("required", str(context.exception))

    def test_raises_error_when_build_is_empty(self):
        """Test that ValueError is raised when build is empty string."""
        with self.assertRaises(ValueError) as context:
            BuildInfo(
                branch="main",
                build="",
                flavor="release",
                release="1.0.0",
                url="https://ci.example.com/build/123"
            )
        self.assertIn("build", str(context.exception))

    def test_raises_error_when_flavor_is_none(self):
        """Test that ValueError is raised when flavor is None."""
        with self.assertRaises(ValueError) as context:
            BuildInfo(
                branch="main",
                build="build-123",
                flavor=None,
                release="1.0.0",
                url="https://ci.example.com/build/123"
            )
        self.assertIn("flavor", str(context.exception))
        self.assertIn("required", str(context.exception))

    def test_raises_error_when_flavor_is_empty(self):
        """Test that ValueError is raised when flavor is empty string."""
        with self.assertRaises(ValueError) as context:
            BuildInfo(
                branch="main",
                build="build-123",
                flavor="",
                release="1.0.0",
                url="https://ci.example.com/build/123"
            )
        self.assertIn("flavor", str(context.exception))

    def test_raises_error_when_release_is_none(self):
        """Test that ValueError is raised when release is None."""
        with self.assertRaises(ValueError) as context:
            BuildInfo(
                branch="main",
                build="build-123",
                flavor="release",
                release=None,
                url="https://ci.example.com/build/123"
            )
        self.assertIn("release", str(context.exception))
        self.assertIn("required", str(context.exception))

    def test_raises_error_when_release_is_empty(self):
        """Test that ValueError is raised when release is empty string."""
        with self.assertRaises(ValueError) as context:
            BuildInfo(
                branch="main",
                build="build-123",
                flavor="release",
                release="",
                url="https://ci.example.com/build/123"
            )
        self.assertIn("release", str(context.exception))

    def test_raises_error_when_url_is_none(self):
        """Test that ValueError is raised when url is None."""
        with self.assertRaises(ValueError) as context:
            BuildInfo(
                branch="main",
                build="build-123",
                flavor="release",
                release="1.0.0",
                url=None
            )
        self.assertIn("url", str(context.exception))
        self.assertIn("required", str(context.exception))

    def test_raises_error_when_url_is_empty(self):
        """Test that ValueError is raised when url is empty string."""
        with self.assertRaises(ValueError) as context:
            BuildInfo(
                branch="main",
                build="build-123",
                flavor="release",
                release="1.0.0",
                url=""
            )
        self.assertIn("url", str(context.exception))

    def test_valid_buildinfo_passes_validation(self):
        """Test that valid BuildInfo passes validation without error."""
        # Should not raise any exception
        build_info = BuildInfo(
            branch="main",
            build="build-123",
            flavor="release",
            release="1.0.0",
            url="https://ci.example.com/build/123"
        )
        self.assertEqual(build_info.branch, "main")
        self.assertEqual(build_info.build, "build-123")
        self.assertEqual(build_info.flavor, "release")
        self.assertEqual(build_info.release, "1.0.0")
        self.assertEqual(build_info.url, "https://ci.example.com/build/123")
