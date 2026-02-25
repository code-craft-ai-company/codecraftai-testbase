"""
    .. module:: automojo_tests.testbase.results.test_jobinfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the JobInfo dataclass.

    .. moduleauthor:: AutomationX
"""

import unittest
import warnings
from dataclasses import is_dataclass

from automojo.testbase.results.model.jobinfo import JobInfo, MissingOptionalFieldWarning


class JobInfoInstantiationWithRequiredFieldsTests(unittest.TestCase):
    """Tests for JobInfo dataclass instantiation with required fields only."""

    def test_instantiation_with_required_fields_only(self):
        """Test that JobInfo can be instantiated with only required fields."""
        job_info = JobInfo(
            id="job-uuid-123",
            name="Integration Tests",
            type="TestRun"
        )

        self.assertIsInstance(job_info, JobInfo)

    def test_is_dataclass(self):
        """Test that JobInfo is a dataclass (Requirement 3.10)."""
        self.assertTrue(is_dataclass(JobInfo))


class JobInfoInstantiationWithAllFieldsTests(unittest.TestCase):
    """Tests for JobInfo dataclass instantiation with all fields."""

    def test_instantiation_with_all_fields(self):
        """Test that JobInfo can be instantiated with all fields including optional ones."""
        job_info = JobInfo(
            id="job-uuid-456",
            name="Full Integration Tests",
            type="TestRun",
            owner="QA Team",
            label="nightly",
            initiator="user@example.com",
            venue="staging",
            seed="12345",
            tag="correlation-tag-789"
        )

        self.assertIsInstance(job_info, JobInfo)


class JobInfoDefaultValuesTests(unittest.TestCase):
    """Tests for JobInfo optional field default values."""

    def setUp(self):
        """Set up test fixtures with only required fields."""
        self.job_info = JobInfo(
            id="job-uuid-789",
            name="Default Test Job",
            type="TestRun"
        )

    def test_owner_default_value(self):
        """Test owner field defaults to None (Requirement 3.4)."""
        self.assertIsNone(self.job_info.owner)

    def test_label_default_value(self):
        """Test label field defaults to None (Requirement 3.5)."""
        self.assertIsNone(self.job_info.label)

    def test_initiator_default_value(self):
        """Test initiator field defaults to None (Requirement 3.6)."""
        self.assertIsNone(self.job_info.initiator)

    def test_venue_default_value(self):
        """Test venue field defaults to None (Requirement 3.7)."""
        self.assertIsNone(self.job_info.venue)

    def test_seed_default_value(self):
        """Test seed field defaults to None (Requirement 3.8)."""
        self.assertIsNone(self.job_info.seed)

    def test_tag_default_value(self):
        """Test tag field defaults to None (Requirement 3.9)."""
        self.assertIsNone(self.job_info.tag)


class JobInfoFieldAccessTests(unittest.TestCase):
    """Tests for JobInfo field access and values."""

    def setUp(self):
        """Set up test fixtures with all fields."""
        self.id_value = "job-exec-123"
        self.name_value = "Nightly Integration Tests"
        self.type_value = "TestRun"
        self.owner_value = "QA Team"
        self.label_value = "nightly"
        self.initiator_value = "scheduler@example.com"
        self.venue_value = "production"
        self.seed_value = "98765"
        self.tag_value = "correlation-abc"

        self.job_info = JobInfo(
            id=self.id_value,
            name=self.name_value,
            type=self.type_value,
            owner=self.owner_value,
            label=self.label_value,
            initiator=self.initiator_value,
            venue=self.venue_value,
            seed=self.seed_value,
            tag=self.tag_value
        )

    def test_id_field_access(self):
        """Test id field access (Requirement 3.1)."""
        self.assertEqual(self.job_info.id, self.id_value)
        self.assertIsInstance(self.job_info.id, str)

    def test_name_field_access(self):
        """Test name field access (Requirement 3.2)."""
        self.assertEqual(self.job_info.name, self.name_value)
        self.assertIsInstance(self.job_info.name, str)

    def test_type_field_access(self):
        """Test type field access (Requirement 3.3)."""
        self.assertEqual(self.job_info.type, self.type_value)
        self.assertIsInstance(self.job_info.type, str)

    def test_owner_field_access(self):
        """Test owner field access (Requirement 3.4)."""
        self.assertEqual(self.job_info.owner, self.owner_value)
        self.assertIsInstance(self.job_info.owner, str)

    def test_label_field_access(self):
        """Test label field access (Requirement 3.5)."""
        self.assertEqual(self.job_info.label, self.label_value)
        self.assertIsInstance(self.job_info.label, str)

    def test_initiator_field_access(self):
        """Test initiator field access (Requirement 3.6)."""
        self.assertEqual(self.job_info.initiator, self.initiator_value)
        self.assertIsInstance(self.job_info.initiator, str)

    def test_venue_field_access(self):
        """Test venue field access (Requirement 3.7)."""
        self.assertEqual(self.job_info.venue, self.venue_value)
        self.assertIsInstance(self.job_info.venue, str)

    def test_seed_field_access(self):
        """Test seed field access (Requirement 3.8)."""
        self.assertEqual(self.job_info.seed, self.seed_value)
        self.assertIsInstance(self.job_info.seed, str)

    def test_tag_field_access(self):
        """Test tag field access (Requirement 3.9)."""
        self.assertEqual(self.job_info.tag, self.tag_value)
        self.assertIsInstance(self.job_info.tag, str)


if __name__ == "__main__":
    unittest.main()


class JobInfoRequiredFieldValidationTests(unittest.TestCase):
    """Tests for JobInfo required field validation (Requirements 17.1-17.3)."""

    def test_raises_error_when_id_is_none(self):
        """Test that ValueError is raised when id is None."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", MissingOptionalFieldWarning)
            with self.assertRaises(ValueError) as context:
                JobInfo(
                    id=None,
                    name="Test Job",
                    type="TestRun"
                )
            self.assertIn("id", str(context.exception))
            self.assertIn("required", str(context.exception))

    def test_raises_error_when_id_is_empty(self):
        """Test that ValueError is raised when id is empty string."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", MissingOptionalFieldWarning)
            with self.assertRaises(ValueError) as context:
                JobInfo(
                    id="",
                    name="Test Job",
                    type="TestRun"
                )
            self.assertIn("id", str(context.exception))

    def test_raises_error_when_id_is_whitespace(self):
        """Test that ValueError is raised when id is whitespace only."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", MissingOptionalFieldWarning)
            with self.assertRaises(ValueError) as context:
                JobInfo(
                    id="   ",
                    name="Test Job",
                    type="TestRun"
                )
            self.assertIn("id", str(context.exception))

    def test_raises_error_when_name_is_none(self):
        """Test that ValueError is raised when name is None."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", MissingOptionalFieldWarning)
            with self.assertRaises(ValueError) as context:
                JobInfo(
                    id="job-uuid-123",
                    name=None,
                    type="TestRun"
                )
            self.assertIn("name", str(context.exception))
            self.assertIn("required", str(context.exception))

    def test_raises_error_when_name_is_empty(self):
        """Test that ValueError is raised when name is empty string."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", MissingOptionalFieldWarning)
            with self.assertRaises(ValueError) as context:
                JobInfo(
                    id="job-uuid-123",
                    name="",
                    type="TestRun"
                )
            self.assertIn("name", str(context.exception))

    def test_raises_error_when_type_is_none(self):
        """Test that ValueError is raised when type is None."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", MissingOptionalFieldWarning)
            with self.assertRaises(ValueError) as context:
                JobInfo(
                    id="job-uuid-123",
                    name="Test Job",
                    type=None
                )
            self.assertIn("type", str(context.exception))
            self.assertIn("required", str(context.exception))

    def test_raises_error_when_type_is_empty(self):
        """Test that ValueError is raised when type is empty string."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", MissingOptionalFieldWarning)
            with self.assertRaises(ValueError) as context:
                JobInfo(
                    id="job-uuid-123",
                    name="Test Job",
                    type=""
                )
            self.assertIn("type", str(context.exception))


class JobInfoOptionalFieldWarningTests(unittest.TestCase):
    """Tests for JobInfo optional field warnings (Requirements 17.4-17.9)."""

    def test_warns_when_owner_is_none(self):
        """Test that warning is issued when owner is None."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            JobInfo(
                id="job-uuid-123",
                name="Test Job",
                type="TestRun"
            )
            owner_warnings = [
                warning for warning in w
                if issubclass(warning.category, MissingOptionalFieldWarning)
                and "owner" in str(warning.message)
            ]
            self.assertEqual(len(owner_warnings), 1)

    def test_warns_when_label_is_none(self):
        """Test that warning is issued when label is None."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            JobInfo(
                id="job-uuid-123",
                name="Test Job",
                type="TestRun"
            )
            label_warnings = [
                warning for warning in w
                if issubclass(warning.category, MissingOptionalFieldWarning)
                and "label" in str(warning.message)
            ]
            self.assertEqual(len(label_warnings), 1)

    def test_warns_when_initiator_is_none(self):
        """Test that warning is issued when initiator is None."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            JobInfo(
                id="job-uuid-123",
                name="Test Job",
                type="TestRun"
            )
            initiator_warnings = [
                warning for warning in w
                if issubclass(warning.category, MissingOptionalFieldWarning)
                and "initiator" in str(warning.message)
            ]
            self.assertEqual(len(initiator_warnings), 1)

    def test_warns_when_venue_is_none(self):
        """Test that warning is issued when venue is None."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            JobInfo(
                id="job-uuid-123",
                name="Test Job",
                type="TestRun"
            )
            venue_warnings = [
                warning for warning in w
                if issubclass(warning.category, MissingOptionalFieldWarning)
                and "venue" in str(warning.message)
            ]
            self.assertEqual(len(venue_warnings), 1)

    def test_warns_when_seed_is_none(self):
        """Test that warning is issued when seed is None."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            JobInfo(
                id="job-uuid-123",
                name="Test Job",
                type="TestRun"
            )
            seed_warnings = [
                warning for warning in w
                if issubclass(warning.category, MissingOptionalFieldWarning)
                and "seed" in str(warning.message)
            ]
            self.assertEqual(len(seed_warnings), 1)

    def test_warns_when_tag_is_none(self):
        """Test that warning is issued when tag is None."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            JobInfo(
                id="job-uuid-123",
                name="Test Job",
                type="TestRun"
            )
            tag_warnings = [
                warning for warning in w
                if issubclass(warning.category, MissingOptionalFieldWarning)
                and "tag" in str(warning.message)
            ]
            self.assertEqual(len(tag_warnings), 1)

    def test_warns_about_all_missing_optional_fields(self):
        """Test that warnings are issued for all missing optional fields."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            JobInfo(
                id="job-uuid-123",
                name="Test Job",
                type="TestRun"
            )
            optional_warnings = [
                warning for warning in w
                if issubclass(warning.category, MissingOptionalFieldWarning)
            ]
            # Should have 6 warnings: owner, label, initiator, venue, seed, tag
            self.assertEqual(len(optional_warnings), 6)

    def test_no_warning_when_all_optional_fields_provided(self):
        """Test that no warnings are issued when all optional fields are provided."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            JobInfo(
                id="job-uuid-123",
                name="Test Job",
                type="TestRun",
                owner="QA Team",
                label="nightly",
                initiator="user@example.com",
                venue="staging",
                seed="12345",
                tag="correlation-tag"
            )
            optional_warnings = [
                warning for warning in w
                if issubclass(warning.category, MissingOptionalFieldWarning)
            ]
            self.assertEqual(len(optional_warnings), 0)

    def test_warning_can_be_filtered(self):
        """Test that MissingOptionalFieldWarning can be filtered out."""
        with warnings.catch_warnings(record=True) as w:
            warnings.filterwarnings("ignore", category=MissingOptionalFieldWarning)
            JobInfo(
                id="job-uuid-123",
                name="Test Job",
                type="TestRun"
            )
            optional_warnings = [
                warning for warning in w
                if issubclass(warning.category, MissingOptionalFieldWarning)
            ]
            self.assertEqual(len(optional_warnings), 0)

    def test_partial_optional_fields_warns_only_for_missing(self):
        """Test that warnings are only issued for missing optional fields."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            JobInfo(
                id="job-uuid-123",
                name="Test Job",
                type="TestRun",
                owner="QA Team",
                label="nightly"
                # initiator, venue, seed, tag are missing
            )
            optional_warnings = [
                warning for warning in w
                if issubclass(warning.category, MissingOptionalFieldWarning)
            ]
            # Should have 4 warnings: initiator, venue, seed, tag
            self.assertEqual(len(optional_warnings), 4)
            
            # Verify owner and label are not in warnings
            warning_messages = [str(warning.message) for warning in optional_warnings]
            for msg in warning_messages:
                self.assertNotIn("owner", msg)
                self.assertNotIn("label", msg)
