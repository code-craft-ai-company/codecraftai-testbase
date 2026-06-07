"""
    .. module:: ccai_tests.testbase.results.test_progressinfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for ProgressInfo serialization.

    .. moduleauthor:: CodeCraftX
"""

import unittest
from datetime import datetime
from dataclasses import is_dataclass

from ccai.testbase.results.model.progressinfo import ProgressInfo
from ccai.testbase.results.model.progresscode import ProgressCode
from ccai.testbase.results.model.progresstype import ProgressType


class ProgressInfoAsDictTests(unittest.TestCase):
    """Tests for ProgressInfo.as_dict method (Requirement 12.1, 12.3, 12.5)."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_datetime = datetime(2025, 2, 20, 10, 30, 0, 123456)
        self.test_data = {"worker_id": "worker-1", "additional_info": "test"}
        
        self.progress_info = ProgressInfo(
            id="task-uuid-123",
            category="test-execution",
            moniker="test_module.test_function",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="10",
            position="5",
            status=ProgressCode.Running,
            when=self.test_datetime,
            data=self.test_data
        )

    def test_as_dict_returns_dictionary(self):
        """Test that as_dict returns a dictionary (Requirement 12.1)."""
        result = self.progress_info.as_dict()
        
        self.assertIsInstance(result, dict)

    def test_as_dict_includes_id_field(self):
        """Test that as_dict includes id field (Requirement 12.3)."""
        result = self.progress_info.as_dict()
        
        self.assertIn("id", result)
        self.assertEqual(result["id"], "task-uuid-123")

    def test_as_dict_includes_category_field(self):
        """Test that as_dict includes category field (Requirement 12.3)."""
        result = self.progress_info.as_dict()
        
        self.assertIn("category", result)
        self.assertEqual(result["category"], "test-execution")

    def test_as_dict_includes_moniker_field(self):
        """Test that as_dict includes moniker field (Requirement 12.3)."""
        result = self.progress_info.as_dict()
        
        self.assertIn("moniker", result)
        self.assertEqual(result["moniker"], "test_module.test_function")

    def test_as_dict_includes_ptype_field_as_string(self):
        """Test that as_dict includes ptype field as string name (Requirement 12.3)."""
        result = self.progress_info.as_dict()
        
        self.assertIn("ptype", result)
        self.assertEqual(result["ptype"], "Sequential")
        self.assertIsInstance(result["ptype"], str)

    def test_as_dict_includes_range_min_field(self):
        """Test that as_dict includes range_min field (Requirement 12.3)."""
        result = self.progress_info.as_dict()
        
        self.assertIn("range_min", result)
        self.assertEqual(result["range_min"], "0")

    def test_as_dict_includes_range_max_field(self):
        """Test that as_dict includes range_max field (Requirement 12.3)."""
        result = self.progress_info.as_dict()
        
        self.assertIn("range_max", result)
        self.assertEqual(result["range_max"], "10")

    def test_as_dict_includes_position_field(self):
        """Test that as_dict includes position field (Requirement 12.3)."""
        result = self.progress_info.as_dict()
        
        self.assertIn("position", result)
        self.assertEqual(result["position"], "5")

    def test_as_dict_includes_status_field_as_string(self):
        """Test that as_dict includes status field as string name (Requirement 12.3)."""
        result = self.progress_info.as_dict()
        
        self.assertIn("status", result)
        self.assertEqual(result["status"], "Running")
        self.assertIsInstance(result["status"], str)

    def test_as_dict_includes_when_field_as_iso_format(self):
        """Test that as_dict serializes when field as ISO format datetime string (Requirement 12.5)."""
        result = self.progress_info.as_dict()
        
        self.assertIn("when", result)
        self.assertEqual(result["when"], "2025-02-20T10:30:00.123456")
        self.assertIsInstance(result["when"], str)

    def test_as_dict_includes_data_field(self):
        """Test that as_dict includes data field (Requirement 12.3)."""
        result = self.progress_info.as_dict()
        
        self.assertIn("data", result)
        self.assertEqual(result["data"], self.test_data)

    def test_as_dict_with_none_data_returns_empty_dict(self):
        """Test that as_dict returns empty dict when data is None (Requirement 12.3)."""
        progress_info = ProgressInfo(
            id="task-uuid-456",
            category="test-execution",
            moniker="test_module.test_function",
            ptype=ProgressType.NumericRange,
            range_min="0",
            range_max="100",
            position="50",
            status=ProgressCode.Completed,
            when=self.test_datetime,
            data=None
        )
        
        result = progress_info.as_dict()
        
        self.assertIn("data", result)
        self.assertEqual(result["data"], {})


class ProgressInfoFromDictTests(unittest.TestCase):
    """Tests for ProgressInfo.from_dict method (Requirement 12.2, 12.4)."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dict = {
            "id": "task-uuid-789",
            "category": "integration-test",
            "moniker": "integration.test_suite",
            "ptype": "TimeSpan",
            "range_min": "0",
            "range_max": "3600",
            "position": "1800",
            "status": "Paused",
            "when": "2025-02-20T15:45:30.654321",
            "data": {"key": "value"}
        }

    def test_from_dict_returns_progressinfo_instance(self):
        """Test that from_dict returns a ProgressInfo instance (Requirement 12.2)."""
        result = ProgressInfo.from_dict(self.test_dict)
        
        self.assertIsInstance(result, ProgressInfo)

    def test_from_dict_reconstructs_id_field(self):
        """Test that from_dict reconstructs id field correctly (Requirement 12.4)."""
        result = ProgressInfo.from_dict(self.test_dict)
        
        self.assertEqual(result.id, "task-uuid-789")

    def test_from_dict_reconstructs_category_field(self):
        """Test that from_dict reconstructs category field correctly (Requirement 12.4)."""
        result = ProgressInfo.from_dict(self.test_dict)
        
        self.assertEqual(result.category, "integration-test")

    def test_from_dict_reconstructs_moniker_field(self):
        """Test that from_dict reconstructs moniker field correctly (Requirement 12.4)."""
        result = ProgressInfo.from_dict(self.test_dict)
        
        self.assertEqual(result.moniker, "integration.test_suite")

    def test_from_dict_reconstructs_ptype_as_enum(self):
        """Test that from_dict reconstructs ptype as ProgressType enum (Requirement 12.4)."""
        result = ProgressInfo.from_dict(self.test_dict)
        
        self.assertIsInstance(result.ptype, ProgressType)
        self.assertEqual(result.ptype, ProgressType.TimeSpan)

    def test_from_dict_reconstructs_range_min_field(self):
        """Test that from_dict reconstructs range_min field correctly (Requirement 12.4)."""
        result = ProgressInfo.from_dict(self.test_dict)
        
        self.assertEqual(result.range_min, "0")

    def test_from_dict_reconstructs_range_max_field(self):
        """Test that from_dict reconstructs range_max field correctly (Requirement 12.4)."""
        result = ProgressInfo.from_dict(self.test_dict)
        
        self.assertEqual(result.range_max, "3600")

    def test_from_dict_reconstructs_position_field(self):
        """Test that from_dict reconstructs position field correctly (Requirement 12.4)."""
        result = ProgressInfo.from_dict(self.test_dict)
        
        self.assertEqual(result.position, "1800")

    def test_from_dict_reconstructs_status_as_enum(self):
        """Test that from_dict reconstructs status as ProgressCode enum (Requirement 12.4)."""
        result = ProgressInfo.from_dict(self.test_dict)
        
        self.assertIsInstance(result.status, ProgressCode)
        self.assertEqual(result.status, ProgressCode.Paused)

    def test_from_dict_reconstructs_data_field(self):
        """Test that from_dict reconstructs data field correctly (Requirement 12.4)."""
        result = ProgressInfo.from_dict(self.test_dict)
        
        self.assertEqual(result.data, {"key": "value"})

    def test_from_dict_handles_missing_data_field(self):
        """Test that from_dict handles missing data field (Requirement 12.4)."""
        test_dict_no_data = {
            "id": "task-uuid-000",
            "category": "test",
            "moniker": "test.moniker",
            "ptype": "Sequential",
            "range_min": "0",
            "range_max": "5",
            "position": "2",
            "status": "Running",
            "when": "2025-02-20T12:00:00"
        }
        
        result = ProgressInfo.from_dict(test_dict_no_data)
        
        self.assertIsNone(result.data)


class ProgressInfoDatetimeSerializationTests(unittest.TestCase):
    """Tests for ProgressInfo datetime serialization/deserialization (Requirement 12.5)."""

    def test_datetime_serializes_to_iso_format(self):
        """Test that datetime is serialized to ISO format string (Requirement 12.5)."""
        test_datetime = datetime(2025, 6, 15, 8, 30, 45, 123456)
        
        progress_info = ProgressInfo(
            id="datetime-test",
            category="test",
            moniker="test.datetime",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="1",
            position="0",
            status=ProgressCode.NotStarted,
            when=test_datetime,
            data=None
        )
        
        result = progress_info.as_dict()
        
        self.assertEqual(result["when"], "2025-06-15T08:30:45.123456")

    def test_datetime_deserializes_from_iso_format(self):
        """Test that datetime is deserialized from ISO format string (Requirement 12.5)."""
        test_dict = {
            "id": "datetime-test",
            "category": "test",
            "moniker": "test.datetime",
            "ptype": "Sequential",
            "range_min": "0",
            "range_max": "1",
            "position": "0",
            "status": "NotStarted",
            "when": "2025-06-15T08:30:45.123456"
        }
        
        result = ProgressInfo.from_dict(test_dict)
        
        self.assertIsInstance(result.when, datetime)
        self.assertEqual(result.when.year, 2025)
        self.assertEqual(result.when.month, 6)
        self.assertEqual(result.when.day, 15)
        self.assertEqual(result.when.hour, 8)
        self.assertEqual(result.when.minute, 30)
        self.assertEqual(result.when.second, 45)
        self.assertEqual(result.when.microsecond, 123456)

    def test_datetime_without_microseconds(self):
        """Test datetime serialization/deserialization without microseconds."""
        test_datetime = datetime(2025, 1, 1, 0, 0, 0)
        
        progress_info = ProgressInfo(
            id="no-microseconds",
            category="test",
            moniker="test.no_microseconds",
            ptype=ProgressType.NumericRange,
            range_min="0",
            range_max="100",
            position="0",
            status=ProgressCode.Running,
            when=test_datetime,
            data=None
        )
        
        result_dict = progress_info.as_dict()
        reconstructed = ProgressInfo.from_dict(result_dict)
        
        self.assertEqual(reconstructed.when, test_datetime)


class ProgressInfoRoundTripTests(unittest.TestCase):
    """Tests for ProgressInfo round-trip serialization (Requirements 12.1-12.5)."""

    def test_round_trip_preserves_all_fields(self):
        """Test that as_dict followed by from_dict preserves all fields."""
        original = ProgressInfo(
            id="round-trip-test",
            category="round-trip-category",
            moniker="round.trip.moniker",
            ptype=ProgressType.NumericRange,
            range_min="100",
            range_max="500",
            position="250",
            status=ProgressCode.Running,
            when=datetime(2025, 3, 10, 14, 25, 30, 999999),
            data={"nested": {"key": "value"}, "list": [1, 2, 3]}
        )
        
        serialized = original.as_dict()
        reconstructed = ProgressInfo.from_dict(serialized)
        
        self.assertEqual(reconstructed.id, original.id)
        self.assertEqual(reconstructed.category, original.category)
        self.assertEqual(reconstructed.moniker, original.moniker)
        self.assertEqual(reconstructed.ptype, original.ptype)
        self.assertEqual(reconstructed.range_min, original.range_min)
        self.assertEqual(reconstructed.range_max, original.range_max)
        self.assertEqual(reconstructed.position, original.position)
        self.assertEqual(reconstructed.status, original.status)
        self.assertEqual(reconstructed.when, original.when)
        self.assertEqual(reconstructed.data, original.data)

    def test_round_trip_with_all_progress_codes(self):
        """Test round-trip with all ProgressCode values."""
        for status in ProgressCode:
            progress_info = ProgressInfo(
                id=f"status-{status.name}",
                category="test",
                moniker="test.status",
                ptype=ProgressType.Sequential,
                range_min="0",
                range_max="1",
                position="0",
                status=status,
                when=datetime(2025, 1, 1, 12, 0, 0),
                data=None
            )
            
            serialized = progress_info.as_dict()
            reconstructed = ProgressInfo.from_dict(serialized)
            
            self.assertEqual(reconstructed.status, status)

    def test_round_trip_with_all_progress_types(self):
        """Test round-trip with all ProgressType values."""
        for ptype in ProgressType:
            progress_info = ProgressInfo(
                id=f"ptype-{ptype.name}",
                category="test",
                moniker="test.ptype",
                ptype=ptype,
                range_min="0",
                range_max="100",
                position="50",
                status=ProgressCode.Running,
                when=datetime(2025, 1, 1, 12, 0, 0),
                data=None
            )
            
            serialized = progress_info.as_dict()
            reconstructed = ProgressInfo.from_dict(serialized)
            
            self.assertEqual(reconstructed.ptype, ptype)


if __name__ == "__main__":
    unittest.main()
