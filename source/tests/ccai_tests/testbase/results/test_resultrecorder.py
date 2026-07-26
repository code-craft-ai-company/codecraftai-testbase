"""
    .. module:: ccai_tests.testbase.results.test_resultrecorder
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the ResultRecorder metadata integration and lifecycle.

    .. moduleauthor:: CodeCraftX
"""

import unittest
import tempfile
import os
import shutil
import threading
import json

from datetime import datetime

from ccai.testbase.results.model.buildinfo import BuildInfo
from ccai.testbase.results.model.pipelineinfo import PipelineInfo
from ccai.testbase.results.model.jobinfo import JobInfo
from ccai.testbase.results.model.renderinfo import RenderInfo
from ccai.testbase.results.model.resultcode import ResultCode
from ccai.testbase.results.model.resulttype import ResultType
from ccai.testbase.results.model.testresult import TestResult

from ccai.testbase.results.recorders.jsonresultrecorder import JsonResultRecorder
from ccai.testbase.results.recorders.resultrecorder import ResultRecorder
from ccai.errors.exceptions import AbstractMethodError


class ResultRecorderConstructorMetadataTests(unittest.TestCase):
    """Tests for ResultRecorder constructor with metadata parameters (Requirements 9.1-9.4)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.json"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.json"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.json"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "test-run-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-123",
            flavor="release",
            release="1.0.0",
            url="https://ci.example.com/build/123"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-uuid-456",
            name="CI Pipeline",
            instance="instance-uuid-789"
        )
        
        self.job_info = JobInfo(
            id="job-uuid-012",
            name="Integration Tests",
            type="TestRun",
            owner="QA Team",
            label="nightly",
            initiator="user@example.com",
            venue="staging",
            seed="12345",
            tag="correlation-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_constructor_accepts_build_info_parameter(self):
        """Test that ResultRecorder constructor accepts build_info parameter (Requirement 9.1)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        self.assertIsNotNone(recorder._build_info)
        self.assertEqual(recorder._build_info, self.build_info)

    def test_constructor_accepts_pipeline_info_parameter(self):
        """Test that ResultRecorder constructor accepts pipeline_info parameter (Requirement 9.2)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        self.assertIsNotNone(recorder._pipeline_info)
        self.assertEqual(recorder._pipeline_info, self.pipeline_info)

    def test_constructor_accepts_job_info_parameter(self):
        """Test that ResultRecorder constructor accepts job_info parameter (Requirement 9.3)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        self.assertIsNotNone(recorder._job_info)
        self.assertEqual(recorder._job_info, self.job_info)

    def test_constructor_stores_metadata_references(self):
        """Test that ResultRecorder stores metadata references for use during recording (Requirement 9.4)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        # Verify all metadata references are stored
        self.assertIs(recorder._build_info, self.build_info)
        self.assertIs(recorder._pipeline_info, self.pipeline_info)
        self.assertIs(recorder._job_info, self.job_info)


class ResultRecorderSummaryDictionaryTests(unittest.TestCase):
    """Tests for ResultRecorder summary dictionary structure (Requirements 10.1-10.4)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.json"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.json"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.json"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "test-run-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="feature/test",
            build="build-456",
            flavor="debug",
            release="2.0.0",
            url="https://ci.example.com/build/456"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-def-789",
            name="Integration Pipeline",
            instance="run-instance-012"
        )
        
        self.job_info = JobInfo(
            id="job-exec-345",
            name="Nightly Tests",
            type="TestRun",
            owner="Dev Team",
            label="regression",
            initiator="scheduler@example.com",
            venue="production",
            seed="67890",
            tag="nightly-run"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_summary_includes_build_section(self):
        """Test that summary JSON includes build section with BuildInfo fields (Requirement 10.1)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        summary = recorder.summary
        
        self.assertIn("build", summary)
        build_section = summary["build"]
        self.assertEqual(build_section["branch"], self.build_info.branch)
        self.assertEqual(build_section["build"], self.build_info.build)
        self.assertEqual(build_section["flavor"], self.build_info.flavor)
        self.assertEqual(build_section["release"], self.build_info.release)
        self.assertEqual(build_section["url"], self.build_info.url)

    def test_summary_includes_pipeline_section(self):
        """Test that summary JSON includes pipeline section with PipelineInfo fields (Requirement 10.2)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        summary = recorder.summary
        
        self.assertIn("pipeline", summary)
        pipeline_section = summary["pipeline"]
        self.assertEqual(pipeline_section["id"], self.pipeline_info.id)
        self.assertEqual(pipeline_section["name"], self.pipeline_info.name)
        self.assertEqual(pipeline_section["instance"], self.pipeline_info.instance)

    def test_summary_includes_job_section(self):
        """Test that summary JSON includes job section with JobInfo fields (Requirement 10.3)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        summary = recorder.summary
        
        self.assertIn("job", summary)
        job_section = summary["job"]
        self.assertEqual(job_section["id"], self.job_info.id)
        self.assertEqual(job_section["name"], self.job_info.name)
        self.assertEqual(job_section["type"], self.job_info.type)
        self.assertEqual(job_section["owner"], self.job_info.owner)
        self.assertEqual(job_section["label"], self.job_info.label)
        self.assertEqual(job_section["initiator"], self.job_info.initiator)
        self.assertEqual(job_section["venue"], self.job_info.venue)
        self.assertEqual(job_section["seed"], self.job_info.seed)
        self.assertEqual(job_section["tag"], self.job_info.tag)


class ResultRecorderFormatLinesTests(unittest.TestCase):
    """Tests for ResultRecorder format_lines output with metadata (Requirements 14.1-14.6)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="Test Run Title",
            summary_filename=os.path.join(self.temp_dir, "summary.json"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.json"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.json"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "format-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="release/v3",
            build="build-789",
            flavor="production",
            release="3.0.0",
            url="https://ci.example.com/build/789"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-format-456",
            name="Format Test Pipeline",
            instance="format-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-format-012",
            name="Format Tests",
            type="TestRun",
            owner="Release Team",
            label="release",
            initiator="release@example.com",
            venue="release-env",
            seed="11111",
            tag="release-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_finalized_recorder(self):
        """Helper to create a recorder and finalize it for format_lines testing."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        # Use context manager to properly initialize and finalize
        with recorder:
            pass  # This will call __enter__ and __exit__, which calls finalize()
        return recorder

    def test_format_lines_includes_release_version(self):
        """Test that format_lines includes release version (Requirement 14.1)."""
        recorder = self._create_finalized_recorder()
        
        lines = recorder.format_lines()
        lines_text = "\n".join(lines)
        
        self.assertIn(self.build_info.release, lines_text)

    def test_format_lines_includes_branch_name(self):
        """Test that format_lines includes branch name (Requirement 14.2)."""
        recorder = self._create_finalized_recorder()
        
        lines = recorder.format_lines()
        lines_text = "\n".join(lines)
        
        self.assertIn(self.build_info.branch, lines_text)

    def test_format_lines_includes_build_identifier(self):
        """Test that format_lines includes build identifier (Requirement 14.3)."""
        recorder = self._create_finalized_recorder()
        
        lines = recorder.format_lines()
        lines_text = "\n".join(lines)
        
        self.assertIn(self.build_info.build, lines_text)

    def test_format_lines_includes_build_flavor(self):
        """Test that format_lines includes build flavor (Requirement 14.4)."""
        recorder = self._create_finalized_recorder()
        
        lines = recorder.format_lines()
        lines_text = "\n".join(lines)
        
        self.assertIn(self.build_info.flavor, lines_text)

    def test_format_lines_includes_job_owner(self):
        """Test that format_lines includes job owner (Requirement 14.5)."""
        recorder = self._create_finalized_recorder()
        
        lines = recorder.format_lines()
        lines_text = "\n".join(lines)
        
        self.assertIn(self.job_info.owner, lines_text)

    def test_format_lines_includes_run_identifier(self):
        """Test that format_lines includes run identifier (Requirement 14.6)."""
        recorder = self._create_finalized_recorder()
        
        lines = recorder.format_lines()
        lines_text = "\n".join(lines)
        
        self.assertIn(self.runid, lines_text)


class ResultRecorderLifecycleContextManagerTests(unittest.TestCase):
    """Tests for ResultRecorder context manager lifecycle (Requirements 24.1-24.4)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="Lifecycle Test Run",
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
        
        self.runid = "lifecycle-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-lifecycle",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/lifecycle"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-lifecycle-456",
            name="Lifecycle Pipeline",
            instance="lifecycle-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-lifecycle-012",
            name="Lifecycle Tests",
            type="TestRun",
            owner="Test Team",
            label="lifecycle",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="lifecycle-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_enter_calls_initialize_report(self):
        """Test that __enter__ calls initialize_report (Requirement 24.1)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )

        # In the near-standalone testbase framework, initialize_report's
        # observable effect is the output-directory catalog.  (Publishing the
        # HTML summary template is an integration-tier concern -- see
        # IntegrationJsonResultRecorder in codecraftai-integration-runtime.)
        catalog_file = os.path.join(self.temp_dir, "catalog.json")
        self.assertFalse(os.path.exists(catalog_file))

        with recorder:
            # After entering, initialize_report should have written the catalog
            self.assertTrue(os.path.exists(catalog_file))

    def test_enter_calls_update_summary(self):
        """Test that __enter__ calls update_summary (Requirement 24.1)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        with recorder:
            # After entering, summary file should exist
            self.assertTrue(os.path.exists(self.render_info.summary_filename))
            
            # Verify summary content
            with open(self.render_info.summary_filename, 'r') as f:
                summary = json.load(f)
            self.assertEqual(summary["runid"], self.runid)
            self.assertEqual(summary["result"], "RUNNING")

    def test_enter_opens_stream_results_file(self):
        """Test that __enter__ opens the stream results file (Requirement 24.1)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        with recorder:
            # Stream file should be open and writable
            self.assertIsNotNone(recorder._rout)
            self.assertFalse(recorder._rout.closed)

    def test_enter_returns_self(self):
        """Test that __enter__ returns self for use in with statements (Requirement 24.3)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        with recorder as ctx:
            self.assertIs(ctx, recorder)

    def test_exit_calls_finalize_if_not_finalized(self):
        """Test that __exit__ calls finalize if not already finalized (Requirement 24.2)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        with recorder:
            self.assertFalse(recorder._finalized)
        
        # After exiting, finalize should have been called
        self.assertTrue(recorder._finalized)

    def test_exit_does_not_double_finalize(self):
        """Test that __exit__ does not call finalize if already finalized (Requirement 24.2)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        with recorder:
            # Manually finalize before exit
            recorder.finalize()
            first_stop = recorder._stop
        
        # Stop time should not have changed (no double finalization)
        self.assertEqual(recorder._stop, first_stop)

    def test_exit_handles_exceptions_gracefully(self):
        """Test that __exit__ handles exceptions gracefully (Requirement 24.4)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        try:
            with recorder:
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected exception
        
        # Recorder should still be finalized despite exception
        self.assertTrue(recorder._finalized)


class ResultRecorderInitializationTests(unittest.TestCase):
    """Tests for ResultRecorder initialization (Requirements 23.1-23.5, 25.1-25.4)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.static_src_dir = os.path.join(self.temp_dir, "static_src")
        self.static_dest_dir = os.path.join(self.temp_dir, "static_dest")
        os.makedirs(self.static_src_dir)
        os.makedirs(self.static_dest_dir)
        
        # Create a static resource file
        with open(os.path.join(self.static_src_dir, "style.css"), 'w') as f:
            f.write("body { color: black; }")
        
        self.render_info = RenderInfo(
            title="Init Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.json"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.jsos"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.json"),
            static_resource_source=self.static_src_dir,
            static_resource_destination=self.static_dest_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "init-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-init",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/init"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-init-456",
            name="Init Pipeline",
            instance="init-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-init-012",
            name="Init Tests",
            type="TestRun",
            owner="Test Team",
            label="init",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="init-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_constructor_initializes_counters_to_zero(self):
        """Test that constructor initializes result counters to zero (Requirement 23.2)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        self.assertEqual(recorder._error_count, 0)
        self.assertEqual(recorder._failure_count, 0)
        self.assertEqual(recorder._pass_count, 0)
        self.assertEqual(recorder._skip_count, 0)
        self.assertEqual(recorder._unknown_count, 0)
        self.assertEqual(recorder._total_count, 0)

    def test_constructor_initializes_summary_ordered_dict(self):
        """Test that constructor initializes summary OrderedDict (Requirement 23.3)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        summary = recorder._summary
        
        # Verify all required fields exist
        self.assertIn("version", summary)
        self.assertIn("title", summary)
        self.assertIn("runid", summary)
        self.assertIn("build", summary)
        self.assertIn("pipeline", summary)
        self.assertIn("job", summary)
        self.assertIn("start", summary)
        self.assertIn("stop", summary)
        self.assertIn("result", summary)
        self.assertIn("apod", summary)
        self.assertIn("totals", summary)
        self.assertIn("running", summary)
        
        # Verify initial values
        self.assertEqual(summary["version"], "2")
        self.assertEqual(summary["runid"], self.runid)
        self.assertEqual(summary["result"], "RUNNING")
        self.assertIsNone(summary["stop"])

    def test_constructor_initializes_threading_lock(self):
        """Test that constructor initializes a threading lock (Requirement 23.4)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        self.assertIsInstance(recorder._lock, type(threading.Lock()))

    def test_summary_property_returns_thread_safe_copy(self):
        """Test that summary property returns a thread-safe copy (Requirement 23.5)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        summary1 = recorder.summary
        summary2 = recorder.summary
        
        # Should be different objects (copies)
        self.assertIsNot(summary1, summary2)
        self.assertIsNot(summary1, recorder._summary)
        
        # But should have same content
        self.assertEqual(summary1["runid"], summary2["runid"])

    def test_initialize_report_does_not_publish_html(self):
        """
        Pin the near-standalone contract: initialize_report does NOT copy the
        HTML summary template.  That behaviour was deliberately relocated to
        IntegrationJsonResultRecorder in codecraftai-integration-runtime,
        which overrides initialize_report to publish the HTML presentation
        before delegating here for the catalog.
        """
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )

        recorder.initialize_report()

        summary_html_dest = os.path.join(self.temp_dir, "testsummary.html")
        self.assertFalse(os.path.exists(summary_html_dest),
                         "The base recorder must not publish HTML; that is integration-tier behaviour.")

    def test_initialize_report_calls_catalog_output_directory(self):
        """Test that initialize_report calls catalog_output_directory (Requirement 25.3)."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        recorder.initialize_report()
        
        # Catalog file should exist in output directory
        catalog_file = os.path.join(self.temp_dir, "catalog.json")
        self.assertTrue(os.path.exists(catalog_file))

    def test_update_render_environment_is_a_noop(self):
        """
        Pin the near-standalone contract: update_render_environment copies
        nothing.  Static-resource publishing was deliberately relocated to
        IntegrationJsonResultRecorder in codecraftai-integration-runtime.
        """
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )

        dest_css = os.path.join(self.static_dest_dir, "style.css")
        self.assertFalse(os.path.exists(dest_css))

        recorder.update_render_environment()

        self.assertFalse(os.path.exists(dest_css),
                         "The base recorder must not deploy static resources; that is integration-tier behaviour.")


class ResultRecorderFinalizationTests(unittest.TestCase):
    """Tests for ResultRecorder finalization (Requirements 26.1-26.8)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="Finalize Test Run",
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
        
        self.runid = "finalize-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-finalize",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/finalize"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-finalize-456",
            name="Finalize Pipeline",
            instance="finalize-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-finalize-012",
            name="Finalize Tests",
            type="TestRun",
            owner="Test Team",
            label="finalize",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="finalize-tag"
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

    def test_finalize_sets_finalized_flag(self):
        """Test that finalize sets the finalized flag to True (Requirement 26.1)."""
        recorder = self._create_entered_recorder()
        
        self.assertFalse(recorder._finalized)
        
        recorder.finalize()
        
        self.assertTrue(recorder._finalized)

    def test_finalize_sets_stop_timestamp(self):
        """Test that finalize sets the stop timestamp (Requirement 26.2)."""
        recorder = self._create_entered_recorder()
        
        before_finalize = datetime.now()
        recorder.finalize()
        after_finalize = datetime.now()
        
        self.assertIsNotNone(recorder._stop)
        self.assertGreaterEqual(recorder._stop, before_finalize)
        self.assertLessEqual(recorder._stop, after_finalize)

    def test_finalize_updates_summary_with_stop_time(self):
        """Test that finalize updates summary with stop time (Requirement 26.3)."""
        recorder = self._create_entered_recorder()
        
        recorder.finalize()
        
        self.assertIsNotNone(recorder._summary["stop"])

    def test_finalize_updates_summary_with_detail_counts(self):
        """Test that finalize updates summary with detail counts (Requirement 26.3)."""
        recorder = self._create_entered_recorder()
        
        # Set some counts
        recorder._error_count = 1
        recorder._failure_count = 2
        recorder._skip_count = 3
        recorder._pass_count = 4
        recorder._total_count = 10
        
        recorder.finalize()
        
        detail = recorder._summary["detail"]
        self.assertEqual(detail["errors"], 1)
        self.assertEqual(detail["failed"], 2)
        self.assertEqual(detail["skipped"], 3)
        self.assertEqual(detail["passed"], 4)
        self.assertEqual(detail["total"], 10)

    def test_finalize_sets_result_failed_on_errors(self):
        """Test that finalize sets result to FAILED if error_count > 0 (Requirement 26.4)."""
        recorder = self._create_entered_recorder()
        
        recorder._error_count = 1
        recorder.finalize()
        
        self.assertEqual(recorder._summary["result"], "FAILED")

    def test_finalize_sets_result_failed_on_failures(self):
        """Test that finalize sets result to FAILED if failure_count > 0 (Requirement 26.4)."""
        recorder = self._create_entered_recorder()
        
        recorder._failure_count = 1
        recorder.finalize()
        
        self.assertEqual(recorder._summary["result"], "FAILED")

    def test_finalize_sets_result_passed_on_no_errors_or_failures(self):
        """Test that finalize sets result to PASSED if no errors or failures (Requirement 26.5)."""
        recorder = self._create_entered_recorder()
        
        recorder._pass_count = 5
        recorder._total_count = 5
        recorder.finalize()
        
        self.assertEqual(recorder._summary["result"], "PASSED")

    def test_finalize_closes_stream_file(self):
        """Test that finalize closes the stream results file (Requirement 26.6)."""
        recorder = self._create_entered_recorder()
        
        self.assertFalse(recorder._rout.closed)
        
        recorder.finalize()
        
        self.assertTrue(recorder._rout.closed)

    def test_finalize_calls_update_summary(self):
        """Test that finalize calls update_summary (Requirement 26.7)."""
        recorder = self._create_entered_recorder()
        
        recorder.finalize()
        
        # Summary file should be updated with final result
        with open(self.render_info.summary_filename, 'r') as f:
            summary = json.load(f)
        
        self.assertIn("detail", summary)
        self.assertIn("stop", summary)


class ResultRecorderSummaryGenerationTests(unittest.TestCase):
    """Tests for ResultRecorder summary generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="Summary Test Run",
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
        
        self.runid = "summary-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-summary",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/summary"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-summary-456",
            name="Summary Pipeline",
            instance="summary-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-summary-012",
            name="Summary Tests",
            type="TestRun",
            owner="Test Team",
            label="summary",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="summary-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_summary_file_written_on_enter(self):
        """Test that summary file is written when entering context."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        with recorder:
            self.assertTrue(os.path.exists(self.render_info.summary_filename))
            
            with open(self.render_info.summary_filename, 'r') as f:
                summary = json.load(f)
            
            self.assertEqual(summary["result"], "RUNNING")

    def test_summary_file_updated_on_exit(self):
        """Test that summary file is updated when exiting context."""
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        with recorder:
            pass
        
        with open(self.render_info.summary_filename, 'r') as f:
            summary = json.load(f)
        
        self.assertEqual(summary["result"], "PASSED")
        self.assertIsNotNone(summary["stop"])
        self.assertIn("detail", summary)

    def test_summary_reflects_recorded_results(self):
        """Test that summary reflects recorded test results."""
        from ccai.errors.xtraceback import OriginDetail, TraceDetail, TracebackDetail
        
        recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )
        
        with recorder:
            # Record a passing test
            test_result = TestResult(
                inst_id="test-1",
                name="test_pass",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            test_result.mark_passed()
            test_result.finalize()
            recorder.record(test_result)
            
            # Record a failing test - must add a failure for finalize to set FAILED
            test_result2 = TestResult(
                inst_id="test-2",
                name="test_fail",
                parent_inst="parent-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            # Add a failure to make finalize set result_code to FAILED
            origin = OriginDetail(file="test.py", lineno=10, scope="test_fail")
            trace = TraceDetail(origin=origin, call="assert False", code=["assert False"], context={})
            tb = TracebackDetail(extype="AssertionError", exargs=["Test failed"], traces=[trace])
            test_result2.add_failure(tb)
            test_result2.finalize()
            recorder.record(test_result2)
        
        with open(self.render_info.summary_filename, 'r') as f:
            summary = json.load(f)
        
        self.assertEqual(summary["result"], "FAILED")
        self.assertEqual(summary["detail"]["passed"], 1)
        self.assertEqual(summary["detail"]["failed"], 1)
        self.assertEqual(summary["detail"]["total"], 2)



if __name__ == "__main__":
    unittest.main()
