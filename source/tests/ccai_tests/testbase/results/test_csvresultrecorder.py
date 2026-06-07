"""
    .. module:: ccai_tests.testbase.results.test_csvresultrecorder
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the CsvResultRecorder class.

    .. moduleauthor:: CodeCraftX
"""

import unittest
import tempfile
import os
import shutil
import csv

from datetime import datetime

from ccai.testbase.results.model.buildinfo import BuildInfo
from ccai.testbase.results.model.pipelineinfo import PipelineInfo
from ccai.testbase.results.model.jobinfo import JobInfo
from ccai.testbase.results.model.renderinfo import RenderInfo
from ccai.testbase.results.model.resultcode import ResultCode
from ccai.testbase.results.model.resulttype import ResultType
from ccai.testbase.results.model.testresult import TestResult

from ccai.testbase.results.recorders.csvresultrecorder import (
    CsvResultRecorder,
    RESULT_CSV_HEADERS,
    SUMMARY_CSV_HEADERS
)


class CsvResultRecorderPreviewTests(unittest.TestCase):
    """Tests for CsvResultRecorder preview method."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="CSV Preview Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.csv"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.csv"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.csv"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "csv-preview-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-csv-preview",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/csv-preview"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-csv-preview-456",
            name="CSV Preview Pipeline",
            instance="csv-preview-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-csv-preview-012",
            name="CSV Preview Tests",
            type="TestRun",
            owner="Test Team",
            label="csv-preview",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="csv-preview-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_entered_recorder(self):
        """Helper to create a recorder that has been entered."""
        recorder = CsvResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        recorder.__enter__()
        return recorder

    def test_preview_writes_csv_row(self):
        """Test that preview writes a CSV row to stream file."""
        recorder = self._create_entered_recorder()
        
        try:
            test_result = TestResult(
                inst_id="test-csv-preview-1",
                name="test_csv_preview_method",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            
            recorder.preview(test_result)
            
            # Read the stream file content
            with open(self.render_info.stream_results_filename, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Should have header row and one data row
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0], RESULT_CSV_HEADERS)
            self.assertIn("test_csv_preview_method", rows[1])
        finally:
            recorder.finalize()

    def test_preview_writes_header_row_first(self):
        """Test that CSV header row is written first."""
        recorder = self._create_entered_recorder()
        
        try:
            # Read the stream file content before any preview
            with open(self.render_info.stream_results_filename, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Should have header row
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0], RESULT_CSV_HEADERS)
        finally:
            recorder.finalize()

    def test_preview_includes_test_name_and_instance(self):
        """Test that preview includes test name and instance in CSV."""
        recorder = self._create_entered_recorder()
        
        try:
            test_result = TestResult(
                inst_id="test-csv-instance-123",
                name="test_csv_name_check",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            
            recorder.preview(test_result)
            
            with open(self.render_info.stream_results_filename, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["name"], "test_csv_name_check")
            self.assertEqual(rows[0]["instance"], "test-csv-instance-123")
        finally:
            recorder.finalize()


class CsvResultRecorderRecordTests(unittest.TestCase):
    """Tests for CsvResultRecorder record method."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="CSV Record Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.csv"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.csv"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.csv"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "csv-record-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-csv-record",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/csv-record"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-csv-record-456",
            name="CSV Record Pipeline",
            instance="csv-record-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-csv-record-012",
            name="CSV Record Tests",
            type="TestRun",
            owner="Test Team",
            label="csv-record",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="csv-record-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_entered_recorder(self):
        """Helper to create a recorder that has been entered."""
        recorder = CsvResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        recorder.__enter__()
        return recorder

    def test_record_writes_csv_row_with_result(self):
        """Test that record writes a CSV row with result code."""
        recorder = self._create_entered_recorder()
        
        try:
            test_result = TestResult(
                inst_id="test-csv-record-1",
                name="test_csv_record_method",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            test_result.mark_passed()
            test_result.finalize()
            
            recorder.record(test_result)
            
            with open(self.render_info.stream_results_filename, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["result"], "PASSED")
        finally:
            recorder.finalize()

    def test_record_increments_pass_count(self):
        """Test that record increments pass_count for PASSED result."""
        recorder = self._create_entered_recorder()
        
        try:
            self.assertEqual(recorder._pass_count, 0)
            
            test_result = TestResult(
                inst_id="test-csv-pass-1",
                name="test_csv_pass_count",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            test_result.mark_passed()
            test_result.finalize()
            
            recorder.record(test_result)
            
            self.assertEqual(recorder._pass_count, 1)
            self.assertEqual(recorder._total_count, 1)
        finally:
            recorder.finalize()

    def test_record_increments_failure_count(self):
        """Test that record increments failure_count for FAILED result."""
        from ccai.errors.xtraceback import OriginDetail, TraceDetail, TracebackDetail
        
        recorder = self._create_entered_recorder()
        
        try:
            self.assertEqual(recorder._failure_count, 0)
            
            test_result = TestResult(
                inst_id="test-csv-fail-1",
                name="test_csv_failure_count",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            origin = OriginDetail(file="test.py", lineno=10, scope="test_fail")
            trace = TraceDetail(origin=origin, call="assert False", code=["assert False"], context={})
            tb = TracebackDetail(extype="AssertionError", exargs=["Test failed"], traces=[trace])
            test_result.add_failure(tb)
            test_result.finalize()
            
            recorder.record(test_result)
            
            self.assertEqual(recorder._failure_count, 1)
        finally:
            recorder.finalize()

    def test_record_increments_skip_count(self):
        """Test that record increments skip_count for SKIPPED result."""
        recorder = self._create_entered_recorder()
        
        try:
            self.assertEqual(recorder._skip_count, 0)
            
            test_result = TestResult(
                inst_id="test-csv-skip-1",
                name="test_csv_skip_count",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.SKIPPED
            )
            
            recorder.record(test_result)
            
            self.assertEqual(recorder._skip_count, 1)
        finally:
            recorder.finalize()


class CsvResultRecorderUpdateSummaryTests(unittest.TestCase):
    """Tests for CsvResultRecorder update_summary method."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="CSV Summary Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.csv"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.csv"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.csv"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "csv-summary-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-csv-summary",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/csv-summary"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-csv-summary-456",
            name="CSV Summary Pipeline",
            instance="csv-summary-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-csv-summary-012",
            name="CSV Summary Tests",
            type="TestRun",
            owner="Test Team",
            label="csv-summary",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="csv-summary-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_update_summary_writes_csv_file(self):
        """Test that update_summary writes CSV to summary file."""
        recorder = CsvResultRecorder(
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
            reader = csv.reader(f)
            rows = list(reader)
        
        # Should have header row and one data row
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], SUMMARY_CSV_HEADERS)

    def test_update_summary_includes_runid(self):
        """Test that update_summary includes runid in CSV."""
        recorder = CsvResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        recorder.update_summary()
        
        with open(self.render_info.summary_filename, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["runid"], self.runid)

    def test_update_summary_includes_build_info(self):
        """Test that update_summary includes build information."""
        recorder = CsvResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        recorder.update_summary()
        
        with open(self.render_info.summary_filename, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(rows[0]["build_branch"], "main")
        self.assertEqual(rows[0]["build_build"], "build-csv-summary")


class CsvResultRecorderWriteConsolidatedResultsTests(unittest.TestCase):
    """Tests for CsvResultRecorder write_consolidated_results method."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="CSV Consolidated Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.csv"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.csv"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.csv"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "csv-consolidated-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-csv-consolidated",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/csv-consolidated"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-csv-consolidated-456",
            name="CSV Consolidated Pipeline",
            instance="csv-consolidated-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-csv-consolidated-012",
            name="CSV Consolidated Tests",
            type="TestRun",
            owner="Test Team",
            label="csv-consolidated",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="csv-consolidated-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_write_consolidated_results_writes_csv_file(self):
        """Test that write_consolidated_results writes CSV to file."""
        recorder = CsvResultRecorder(
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
            reader = csv.reader(f)
            rows = list(reader)
        
        # Should have header row and one data row
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], RESULT_CSV_HEADERS)

    def test_write_consolidated_results_flattens_nested_items(self):
        """Test that write_consolidated_results flattens nested items."""
        recorder = CsvResultRecorder(
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
            "items": [
                {
                    "name": "test_module",
                    "instance": "module-1",
                    "parent": "job-instance-1",
                    "rtype": "TEST_CONTAINER",
                    "items": [
                        {
                            "name": "test_function",
                            "instance": "test-1",
                            "parent": "module-1",
                            "rtype": "TEST",
                            "result": "PASSED"
                        }
                    ]
                }
            ]
        }
        
        recorder.write_consolidated_results(root_node)
        
        with open(self.render_info.consolidated_results_filename, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Should have 3 rows: job, module, test
        self.assertEqual(len(rows), 3)
        names = [row["name"] for row in rows]
        self.assertIn("Test Job", names)
        self.assertIn("test_module", names)
        self.assertIn("test_function", names)

    def test_write_consolidated_results_handles_tasking_groups(self):
        """Test that write_consolidated_results handles tasking groups."""
        recorder = CsvResultRecorder(
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
            "items": [
                {
                    "name": "test_with_tasking",
                    "instance": "test-1",
                    "parent": "job-instance-1",
                    "rtype": "TEST",
                    "tasking_groups": [
                        {
                            "name": "setup_group",
                            "instance": "tg-1",
                            "parent": "test-1",
                            "rtype": "TASKING_GROUP",
                            "taskings": [
                                {
                                    "name": "task_1",
                                    "instance": "task-1",
                                    "parent": "tg-1",
                                    "rtype": "TASKING"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        recorder.write_consolidated_results(root_node)
        
        with open(self.render_info.consolidated_results_filename, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Should have 4 rows: job, test, tasking_group, tasking
        self.assertEqual(len(rows), 4)
        names = [row["name"] for row in rows]
        self.assertIn("setup_group", names)
        self.assertIn("task_1", names)


if __name__ == '__main__':
    unittest.main()
