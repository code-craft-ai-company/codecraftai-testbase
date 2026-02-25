"""
    .. module:: automojo_tests.testbase.results.test_xmlresultrecorder
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the XmlResultRecorder class.

    .. moduleauthor:: AutomationX
"""

import unittest
import tempfile
import os
import shutil
import xml.etree.ElementTree as ET

from datetime import datetime

from automojo.testbase.results.model.buildinfo import BuildInfo
from automojo.testbase.results.model.pipelineinfo import PipelineInfo
from automojo.testbase.results.model.jobinfo import JobInfo
from automojo.testbase.results.model.renderinfo import RenderInfo
from automojo.testbase.results.model.resultcode import ResultCode
from automojo.testbase.results.model.resulttype import ResultType
from automojo.testbase.results.model.testresult import TestResult

from automojo.testbase.results.recorders.xmlresultrecorder import XmlResultRecorder

from automojo.xmodules.jsos import CHAR_RECORD_SEPERATOR


class XmlResultRecorderPreviewTests(unittest.TestCase):
    """Tests for XmlResultRecorder preview method."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="XML Preview Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.xml"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.xml"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.xml"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "xml-preview-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-xml-preview",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/xml-preview"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-xml-preview-456",
            name="XML Preview Pipeline",
            instance="xml-preview-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-xml-preview-012",
            name="XML Preview Tests",
            type="TestRun",
            owner="Test Team",
            label="xml-preview",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="xml-preview-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_entered_recorder(self):
        """Helper to create a recorder that has been entered."""
        recorder = XmlResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        recorder.__enter__()
        return recorder

    def test_preview_writes_xml_content(self):
        """Test that preview writes XML content to stream file."""
        recorder = self._create_entered_recorder()
        
        try:
            test_result = TestResult(
                inst_id="test-xml-preview-1",
                name="test_xml_preview_method",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            
            recorder.preview(test_result)
            
            # Read the stream file content
            with open(self.render_info.stream_results_filename, 'r') as f:
                content = f.read()
            
            # Content should contain XML
            self.assertIn("<result>", content)
            self.assertIn("<name>test_xml_preview_method</name>", content)
            self.assertIn("<instance>test-xml-preview-1</instance>", content)
        finally:
            recorder.finalize()

    def test_preview_writes_record_separator_before_xml(self):
        """Test that preview writes record separator before XML content."""
        recorder = self._create_entered_recorder()
        
        try:
            test_result = TestResult(
                inst_id="test-xml-sep-1",
                name="test_xml_separator",
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

    def test_preview_does_not_include_detail_section(self):
        """Test that preview does not include detail section in XML."""
        recorder = self._create_entered_recorder()
        
        try:
            test_result = TestResult(
                inst_id="test-xml-no-detail-1",
                name="test_xml_no_detail",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            
            recorder.preview(test_result)
            
            # Read the stream file content
            with open(self.render_info.stream_results_filename, 'r') as f:
                content = f.read()
            
            # Preview should NOT include detail section
            self.assertNotIn("<detail>", content)
        finally:
            recorder.finalize()


class XmlResultRecorderRecordTests(unittest.TestCase):
    """Tests for XmlResultRecorder record method."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="XML Record Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.xml"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.xml"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.xml"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "xml-record-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-xml-record",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/xml-record"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-xml-record-456",
            name="XML Record Pipeline",
            instance="xml-record-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-xml-record-012",
            name="XML Record Tests",
            type="TestRun",
            owner="Test Team",
            label="xml-record",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="xml-record-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_entered_recorder(self):
        """Helper to create a recorder that has been entered."""
        recorder = XmlResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        recorder.__enter__()
        return recorder

    def test_record_writes_xml_with_detail_section(self):
        """Test that record writes XML with detail section."""
        recorder = self._create_entered_recorder()
        
        try:
            test_result = TestResult(
                inst_id="test-xml-record-1",
                name="test_xml_record_method",
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
            
            # Record should include detail section
            self.assertIn("<detail>", content)
            self.assertIn("<errors>", content)
            self.assertIn("<failures>", content)
        finally:
            recorder.finalize()

    def test_record_increments_pass_count(self):
        """Test that record increments pass_count for PASSED result."""
        recorder = self._create_entered_recorder()
        
        try:
            self.assertEqual(recorder._pass_count, 0)
            
            test_result = TestResult(
                inst_id="test-xml-pass-1",
                name="test_xml_pass_count",
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
        from automojo.errors.xtraceback import OriginDetail, TraceDetail, TracebackDetail
        
        recorder = self._create_entered_recorder()
        
        try:
            self.assertEqual(recorder._failure_count, 0)
            
            test_result = TestResult(
                inst_id="test-xml-fail-1",
                name="test_xml_failure_count",
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


class XmlResultRecorderUpdateSummaryTests(unittest.TestCase):
    """Tests for XmlResultRecorder update_summary method."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="XML Summary Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.xml"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.xml"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.xml"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "xml-summary-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-xml-summary",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/xml-summary"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-xml-summary-456",
            name="XML Summary Pipeline",
            instance="xml-summary-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-xml-summary-012",
            name="XML Summary Tests",
            type="TestRun",
            owner="Test Team",
            label="xml-summary",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="xml-summary-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_update_summary_writes_xml_file(self):
        """Test that update_summary writes XML to summary file."""
        recorder = XmlResultRecorder(
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
            content = f.read()
        
        self.assertIn("<summary>", content)
        self.assertIn("<runid>", content)
        self.assertIn(self.runid, content)

    def test_update_summary_includes_build_info(self):
        """Test that update_summary includes build information."""
        recorder = XmlResultRecorder(
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
        
        self.assertIn("<build>", content)
        self.assertIn("<branch>main</branch>", content)


class XmlResultRecorderWriteConsolidatedResultsTests(unittest.TestCase):
    """Tests for XmlResultRecorder write_consolidated_results method."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="XML Consolidated Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.xml"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.xml"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.xml"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "xml-consolidated-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-xml-consolidated",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/xml-consolidated"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-xml-consolidated-456",
            name="XML Consolidated Pipeline",
            instance="xml-consolidated-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-xml-consolidated-012",
            name="XML Consolidated Tests",
            type="TestRun",
            owner="Test Team",
            label="xml-consolidated",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="xml-consolidated-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_write_consolidated_results_writes_xml_file(self):
        """Test that write_consolidated_results writes XML to file."""
        recorder = XmlResultRecorder(
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
            content = f.read()
        
        self.assertIn("<testresults>", content)
        self.assertIn("<name>Test Job</name>", content)

    def test_write_consolidated_results_handles_nested_items(self):
        """Test that write_consolidated_results handles nested items."""
        recorder = XmlResultRecorder(
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
                    "rtype": "TEST_CONTAINER"
                }
            ]
        }
        
        recorder.write_consolidated_results(root_node)
        
        with open(self.render_info.consolidated_results_filename, 'r') as f:
            content = f.read()
        
        self.assertIn("<items>", content)
        self.assertIn("test_module", content)


if __name__ == '__main__':
    unittest.main()
