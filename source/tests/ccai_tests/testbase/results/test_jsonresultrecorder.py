"""
    .. module:: ccai_tests.testbase.results.test_jsonresultrecorder
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the JsonResultRecorder class.

    .. moduleauthor:: CodeCraftX
"""

import unittest
import tempfile
import os
import shutil
import json

from datetime import datetime

from ccai.testbase.results.model.buildinfo import BuildInfo
from ccai.testbase.results.model.pipelineinfo import PipelineInfo
from ccai.testbase.results.model.jobinfo import JobInfo
from ccai.testbase.results.model.renderinfo import RenderInfo
from ccai.testbase.results.model.resultcode import ResultCode
from ccai.testbase.results.model.testresult import TestResult

from ccai.testbase.results.recorders.jsonresultrecorder import JsonResultRecorder

from ccai.xmodules.jsos import CHAR_RECORD_SEPERATOR


class JsonResultRecorderPreviewTests(unittest.TestCase):
    """Tests for JsonResultRecorder preview method (Requirements 33.1-33.4)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="Preview Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.json"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.jsos"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.json"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "preview-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-preview",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/preview"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-preview-456",
            name="Preview Pipeline",
            instance="preview-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-preview-012",
            name="Preview Tests",
            type="TestRun",
            owner="Test Team",
            label="preview",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="preview-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_entered_recorder(self):
        """Helper to create a recorder that has been entered."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        recorder.__enter__()
        return recorder

    def test_preview_converts_result_to_json_with_is_preview_true(self):
        """Test that preview converts result to JSON with is_preview=True (Requirement 33.1)."""
        recorder = self._create_entered_recorder()
        
        try:
            test_result = TestResult(
                inst_id="test-preview-1",
                name="test_preview_method",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            
            recorder.preview(test_result)
            
            # Read the stream file content
            with open(self.render_info.stream_results_filename, 'r') as f:
                content = f.read()
            
            # Parse the JSON (skip the record separator)
            json_content = content.lstrip(CHAR_RECORD_SEPERATOR)
            result_dict = json.loads(json_content)
            
            # Preview should NOT include detail section
            self.assertNotIn("detail", result_dict)
            self.assertEqual(result_dict["name"], "test_preview_method")
            self.assertEqual(result_dict["instance"], "test-preview-1")
        finally:
            recorder.finalize()

    def test_preview_writes_record_separator_before_json(self):
        """Test that preview writes record separator before JSON content (Requirement 33.2)."""
        recorder = self._create_entered_recorder()
        
        try:
            test_result = TestResult(
                inst_id="test-sep-1",
                name="test_separator",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            
            recorder.preview(test_result)
            
            # Read the stream file content
            with open(self.render_info.stream_results_filename, 'r') as f:
                content = f.read()
            
            # Content should start with record separator
            self.assertTrue(content.startswith(CHAR_RECORD_SEPERATOR))
        finally:
            recorder.finalize()

    def test_preview_flushes_output_stream(self):
        """Test that preview flushes the output stream after writing (Requirement 33.3)."""
        recorder = self._create_entered_recorder()
        
        try:
            test_result = TestResult(
                inst_id="test-flush-1",
                name="test_flush",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            
            recorder.preview(test_result)
            
            # After preview, content should be immediately readable from file
            # (not buffered in memory)
            with open(self.render_info.stream_results_filename, 'r') as f:
                content = f.read()
            
            self.assertIn("test_flush", content)
        finally:
            recorder.finalize()

    def test_preview_calls_catalog_output_directory(self):
        """Test that preview calls catalog_output_directory after writing (Requirement 33.4)."""
        recorder = self._create_entered_recorder()
        
        try:
            test_result = TestResult(
                inst_id="test-catalog-1",
                name="test_catalog",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            
            recorder.preview(test_result)
            
            # Catalog file should exist after preview
            catalog_file = os.path.join(self.temp_dir, "catalog.json")
            self.assertTrue(os.path.exists(catalog_file))
        finally:
            recorder.finalize()


class JsonResultRecorderRecordTests(unittest.TestCase):
    """Tests for JsonResultRecorder record method (Requirements 34.1-34.11)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="Record Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.json"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.jsos"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.json"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "record-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-record",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/record"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-record-456",
            name="Record Pipeline",
            instance="record-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-record-012",
            name="Record Tests",
            type="TestRun",
            owner="Test Team",
            label="record",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="record-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_entered_recorder(self):
        """Helper to create a recorder that has been entered."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        recorder.__enter__()
        return recorder

    def test_record_converts_result_to_json_with_is_preview_false(self):
        """Test that record converts result to JSON with is_preview=False (Requirement 34.1)."""
        recorder = self._create_entered_recorder()
        
        try:
            test_result = TestResult(
                inst_id="test-record-1",
                name="test_record_method",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            test_result.mark_passed()
            test_result.finalize()
            
            recorder.record(test_result)
            
            # Read the stream file content
            with open(self.render_info.stream_results_filename, 'r') as f:
                content = f.read()
            
            # Parse the JSON (skip the record separator)
            json_content = content.lstrip(CHAR_RECORD_SEPERATOR)
            result_dict = json.loads(json_content)
            
            # Record should include detail section (is_preview=False)
            self.assertIn("detail", result_dict)
            self.assertEqual(result_dict["name"], "test_record_method")
        finally:
            recorder.finalize()

    def test_record_writes_record_separator_before_json(self):
        """Test that record writes record separator before JSON content (Requirement 34.2)."""
        recorder = self._create_entered_recorder()
        
        try:
            test_result = TestResult(
                inst_id="test-sep-record-1",
                name="test_separator_record",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            test_result.mark_passed()
            test_result.finalize()
            
            recorder.record(test_result)
            
            # Read the stream file content
            with open(self.render_info.stream_results_filename, 'r') as f:
                content = f.read()
            
            # Content should start with record separator
            self.assertTrue(content.startswith(CHAR_RECORD_SEPERATOR))
        finally:
            recorder.finalize()

    def test_record_flushes_output_stream(self):
        """Test that record flushes the output stream after writing (Requirement 34.3)."""
        recorder = self._create_entered_recorder()
        
        try:
            test_result = TestResult(
                inst_id="test-flush-record-1",
                name="test_flush_record",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            test_result.mark_passed()
            test_result.finalize()
            
            recorder.record(test_result)
            
            # After record, content should be immediately readable from file
            with open(self.render_info.stream_results_filename, 'r') as f:
                content = f.read()
            
            self.assertIn("test_flush_record", content)
        finally:
            recorder.finalize()

    def test_record_increments_total_count_for_test_type(self):
        """Test that record increments total_count for TEST result type (Requirement 34.4)."""
        recorder = self._create_entered_recorder()
        
        try:
            self.assertEqual(recorder._total_count, 0)
            
            test_result = TestResult(
                inst_id="test-total-1",
                name="test_total_count",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            test_result.mark_passed()
            test_result.finalize()
            
            recorder.record(test_result)
            
            self.assertEqual(recorder._total_count, 1)
        finally:
            recorder.finalize()

    def test_record_increments_pass_count_for_passed_result(self):
        """Test that record increments pass_count for PASSED result code (Requirement 34.5)."""
        recorder = self._create_entered_recorder()
        
        try:
            self.assertEqual(recorder._pass_count, 0)
            
            test_result = TestResult(
                inst_id="test-pass-1",
                name="test_pass_count",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            test_result.mark_passed()
            test_result.finalize()
            
            recorder.record(test_result)
            
            self.assertEqual(recorder._pass_count, 1)
        finally:
            recorder.finalize()

    def test_record_increments_error_count_for_errored_result(self):
        """Test that record increments error_count for ERRORED result code (Requirement 34.6)."""
        from ccai.errors.xtraceback import OriginDetail, TraceDetail, TracebackDetail
        
        recorder = self._create_entered_recorder()
        
        try:
            self.assertEqual(recorder._error_count, 0)
            
            test_result = TestResult(
                inst_id="test-error-1",
                name="test_error_count",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            # Add an error to make finalize set result_code to ERRORED
            origin = OriginDetail(file="test.py", lineno=10, scope="test_error")
            trace = TraceDetail(origin=origin, call="raise Exception", code=["raise Exception"], context={})
            tb = TracebackDetail(extype="RuntimeError", exargs=["Test error"], traces=[trace])
            test_result.add_error(tb)
            test_result.finalize()
            
            recorder.record(test_result)
            
            self.assertEqual(recorder._error_count, 1)
        finally:
            recorder.finalize()

    def test_record_increments_failure_count_for_failed_result(self):
        """Test that record increments failure_count for FAILED result code (Requirement 34.7)."""
        from ccai.errors.xtraceback import OriginDetail, TraceDetail, TracebackDetail
        
        recorder = self._create_entered_recorder()
        
        try:
            self.assertEqual(recorder._failure_count, 0)
            
            test_result = TestResult(
                inst_id="test-fail-1",
                name="test_failure_count",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            # Add a failure to make finalize set result_code to FAILED
            origin = OriginDetail(file="test.py", lineno=10, scope="test_fail")
            trace = TraceDetail(origin=origin, call="assert False", code=["assert False"], context={})
            tb = TracebackDetail(extype="AssertionError", exargs=["Test failed"], traces=[trace])
            test_result.add_failure(tb)
            test_result.finalize()
            
            recorder.record(test_result)
            
            self.assertEqual(recorder._failure_count, 1)
        finally:
            recorder.finalize()

    def test_record_increments_skip_count_for_skipped_result(self):
        """Test that record increments skip_count for SKIPPED result code (Requirement 34.8)."""
        recorder = self._create_entered_recorder()
        
        try:
            self.assertEqual(recorder._skip_count, 0)
            
            # Create a test result with SKIPPED result code directly
            # Note: mark_skip sets result_code to SKIPPED, but finalize() would
            # override it to UNKNOWN since SKIPPED is not UNSET or PASSED.
            # So we set the result_code directly to SKIPPED.
            test_result = TestResult(
                inst_id="test-skip-1",
                name="test_skip_count",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.SKIPPED
            )
            
            recorder.record(test_result)
            
            self.assertEqual(recorder._skip_count, 1)
        finally:
            recorder.finalize()

    def test_record_increments_unknown_count_for_other_result(self):
        """Test that record increments unknown_count for other result codes (Requirement 34.9)."""
        recorder = self._create_entered_recorder()
        
        try:
            self.assertEqual(recorder._unknown_count, 0)
            
            test_result = TestResult(
                inst_id="test-unknown-1",
                name="test_unknown_count",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.CANCELLED  # Not PASSED, ERRORED, FAILED, or SKIPPED
            )
            test_result.finalize()
            
            recorder.record(test_result)
            
            self.assertEqual(recorder._unknown_count, 1)
        finally:
            recorder.finalize()

    def test_record_calls_catalog_output_directory(self):
        """Test that record calls catalog_output_directory after writing (Requirement 34.11)."""
        recorder = self._create_entered_recorder()
        
        try:
            test_result = TestResult(
                inst_id="test-catalog-record-1",
                name="test_catalog_record",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            test_result.mark_passed()
            test_result.finalize()
            
            recorder.record(test_result)
            
            # Catalog file should exist after record
            catalog_file = os.path.join(self.temp_dir, "catalog.json")
            self.assertTrue(os.path.exists(catalog_file))
        finally:
            recorder.finalize()


class JsonResultRecorderUpdateSummaryTests(unittest.TestCase):
    """Tests for JsonResultRecorder update_summary method (Requirements 35.1-35.4)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="Summary Update Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.json"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.jsos"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.json"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "summary-update-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-summary-update",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/summary-update"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-summary-update-456",
            name="Summary Update Pipeline",
            instance="summary-update-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-summary-update-012",
            name="Summary Update Tests",
            type="TestRun",
            owner="Test Team",
            label="summary-update",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="summary-update-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_update_summary_writes_to_summary_filename(self):
        """Test that update_summary writes summary to summary_filename (Requirement 35.1)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        recorder.update_summary()
        
        self.assertTrue(os.path.exists(self.render_info.summary_filename))
        
        with open(self.render_info.summary_filename, 'r') as f:
            summary = json.load(f)
        
        self.assertEqual(summary["runid"], self.runid)

    def test_update_summary_uses_json_result_encoder_for_datetime(self):
        """Test that update_summary uses JsonResultEncoder for datetime serialization (Requirement 35.2)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        recorder.update_summary()
        
        with open(self.render_info.summary_filename, 'r') as f:
            summary = json.load(f)
        
        # Start should be serialized as ISO format string
        start_str = summary["start"]
        self.assertIsInstance(start_str, str)
        # Should be parseable as datetime
        datetime.fromisoformat(start_str)

    def test_update_summary_uses_indent_4_for_formatting(self):
        """Test that update_summary uses indent=4 for readable formatting (Requirement 35.3)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        recorder.update_summary()
        
        with open(self.render_info.summary_filename, 'r') as f:
            content = f.read()
        
        # Check for indentation (4 spaces)
        self.assertIn('    "', content)

    def test_update_summary_calls_catalog_output_directory(self):
        """Test that update_summary calls catalog_output_directory (Requirement 35.4)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        recorder.update_summary()
        
        # Catalog file should exist after update_summary
        catalog_file = os.path.join(self.temp_dir, "catalog.json")
        self.assertTrue(os.path.exists(catalog_file))


class JsonResultRecorderWriteConsolidatedResultsTests(unittest.TestCase):
    """Tests for JsonResultRecorder write_consolidated_results method (Requirements 36.1-36.4)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="Consolidated Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.json"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.jsos"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.json"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "consolidated-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-consolidated",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/consolidated"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-consolidated-456",
            name="Consolidated Pipeline",
            instance="consolidated-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-consolidated-012",
            name="Consolidated Tests",
            type="TestRun",
            owner="Test Team",
            label="consolidated",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="consolidated-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_write_consolidated_results_writes_to_consolidated_filename(self):
        """Test that write_consolidated_results writes to consolidated_results_filename (Requirement 36.1)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        root_node = {
            "name": "Test Job",
            "instance": "job-instance-1",
            "parent": None,
            "rtype": "JOB",
            "items": []
        }
        
        recorder.write_consolidated_results(root_node)
        
        self.assertTrue(os.path.exists(self.render_info.consolidated_results_filename))
        
        with open(self.render_info.consolidated_results_filename, 'r') as f:
            consolidated = json.load(f)
        
        self.assertEqual(consolidated["name"], "Test Job")

    def test_write_consolidated_results_uses_json_result_encoder(self):
        """Test that write_consolidated_results uses JsonResultEncoder for datetime (Requirement 36.2)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        test_datetime = datetime(2024, 1, 15, 10, 30, 45)
        root_node = {
            "name": "Test Job",
            "instance": "job-instance-1",
            "parent": None,
            "rtype": "JOB",
            "start": test_datetime,
            "items": []
        }
        
        recorder.write_consolidated_results(root_node)
        
        with open(self.render_info.consolidated_results_filename, 'r') as f:
            consolidated = json.load(f)
        
        # Datetime should be serialized as ISO format string
        self.assertEqual(consolidated["start"], test_datetime.isoformat())

    def test_write_consolidated_results_uses_indent_4(self):
        """Test that write_consolidated_results uses indent=4 for formatting (Requirement 36.3)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        root_node = {
            "name": "Test Job",
            "instance": "job-instance-1",
            "parent": None,
            "rtype": "JOB",
            "items": []
        }
        
        recorder.write_consolidated_results(root_node)
        
        with open(self.render_info.consolidated_results_filename, 'r') as f:
            content = f.read()
        
        # Check for indentation (4 spaces)
        self.assertIn('    "', content)

    def test_write_consolidated_results_calls_catalog_output_directory(self):
        """Test that write_consolidated_results calls catalog_output_directory (Requirement 36.4)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        root_node = {
            "name": "Test Job",
            "instance": "job-instance-1",
            "parent": None,
            "rtype": "JOB",
            "items": []
        }
        
        recorder.write_consolidated_results(root_node)
        
        # Catalog file should exist after write_consolidated_results
        catalog_file = os.path.join(self.temp_dir, "catalog.json")
        self.assertTrue(os.path.exists(catalog_file))


if __name__ == "__main__":
    unittest.main()
