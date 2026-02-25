"""
    .. module:: automojo_tests.testbase.results.test_pipelineinfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the PipelineInfo dataclass.

    .. moduleauthor:: AutomationX
"""

import unittest
from dataclasses import is_dataclass

from automojo.testbase.results.model.pipelineinfo import PipelineInfo


class PipelineInfoInstantiationTests(unittest.TestCase):
    """Tests for PipelineInfo dataclass instantiation with all fields."""

    def test_instantiation_with_all_fields(self):
        """Test that PipelineInfo can be instantiated with all required fields."""
        pipeline_info = PipelineInfo(
            id="pipeline-uuid-123",
            name="CI Pipeline",
            instance="instance-uuid-456"
        )

        self.assertIsInstance(pipeline_info, PipelineInfo)

    def test_is_dataclass(self):
        """Test that PipelineInfo is a dataclass (Requirement 2.4)."""
        self.assertTrue(is_dataclass(PipelineInfo))


class PipelineInfoFieldAccessTests(unittest.TestCase):
    """Tests for PipelineInfo field access and values."""

    def setUp(self):
        """Set up test fixtures."""
        self.id_value = "pipeline-def-789"
        self.name_value = "Integration Test Pipeline"
        self.instance_value = "run-instance-012"

        self.pipeline_info = PipelineInfo(
            id=self.id_value,
            name=self.name_value,
            instance=self.instance_value
        )

    def test_id_field_access(self):
        """Test id field access (Requirement 2.1)."""
        self.assertEqual(self.pipeline_info.id, self.id_value)
        self.assertIsInstance(self.pipeline_info.id, str)

    def test_name_field_access(self):
        """Test name field access (Requirement 2.2)."""
        self.assertEqual(self.pipeline_info.name, self.name_value)
        self.assertIsInstance(self.pipeline_info.name, str)

    def test_instance_field_access(self):
        """Test instance field access (Requirement 2.3)."""
        self.assertEqual(self.pipeline_info.instance, self.instance_value)
        self.assertIsInstance(self.pipeline_info.instance, str)


if __name__ == "__main__":
    unittest.main()


class PipelineInfoValidationTests(unittest.TestCase):
    """Tests for PipelineInfo field validation (Requirements 16.1-16.3)."""

    def test_raises_error_when_id_is_none(self):
        """Test that ValueError is raised when id is None."""
        with self.assertRaises(ValueError) as context:
            PipelineInfo(
                id=None,
                name="CI Pipeline",
                instance="instance-uuid-456"
            )
        self.assertIn("id", str(context.exception))
        self.assertIn("required", str(context.exception))

    def test_raises_error_when_id_is_empty(self):
        """Test that ValueError is raised when id is empty string."""
        with self.assertRaises(ValueError) as context:
            PipelineInfo(
                id="",
                name="CI Pipeline",
                instance="instance-uuid-456"
            )
        self.assertIn("id", str(context.exception))

    def test_raises_error_when_id_is_whitespace(self):
        """Test that ValueError is raised when id is whitespace only."""
        with self.assertRaises(ValueError) as context:
            PipelineInfo(
                id="   ",
                name="CI Pipeline",
                instance="instance-uuid-456"
            )
        self.assertIn("id", str(context.exception))

    def test_raises_error_when_name_is_none(self):
        """Test that ValueError is raised when name is None."""
        with self.assertRaises(ValueError) as context:
            PipelineInfo(
                id="pipeline-uuid-123",
                name=None,
                instance="instance-uuid-456"
            )
        self.assertIn("name", str(context.exception))
        self.assertIn("required", str(context.exception))

    def test_raises_error_when_name_is_empty(self):
        """Test that ValueError is raised when name is empty string."""
        with self.assertRaises(ValueError) as context:
            PipelineInfo(
                id="pipeline-uuid-123",
                name="",
                instance="instance-uuid-456"
            )
        self.assertIn("name", str(context.exception))

    def test_raises_error_when_instance_is_none(self):
        """Test that ValueError is raised when instance is None."""
        with self.assertRaises(ValueError) as context:
            PipelineInfo(
                id="pipeline-uuid-123",
                name="CI Pipeline",
                instance=None
            )
        self.assertIn("instance", str(context.exception))
        self.assertIn("required", str(context.exception))

    def test_raises_error_when_instance_is_empty(self):
        """Test that ValueError is raised when instance is empty string."""
        with self.assertRaises(ValueError) as context:
            PipelineInfo(
                id="pipeline-uuid-123",
                name="CI Pipeline",
                instance=""
            )
        self.assertIn("instance", str(context.exception))

    def test_valid_pipelineinfo_passes_validation(self):
        """Test that valid PipelineInfo passes validation without error."""
        # Should not raise any exception
        pipeline_info = PipelineInfo(
            id="pipeline-uuid-123",
            name="CI Pipeline",
            instance="instance-uuid-456"
        )
        self.assertEqual(pipeline_info.id, "pipeline-uuid-123")
        self.assertEqual(pipeline_info.name, "CI Pipeline")
        self.assertEqual(pipeline_info.instance, "instance-uuid-456")
