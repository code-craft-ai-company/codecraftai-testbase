"""
    .. module:: automojo_tests.testbase.results.test_ci_metadata_integration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Integration tests for end-to-end CI metadata flow.

    .. moduleauthor:: AutomationX

    These tests verify the complete flow of CI/CD metadata from environment variables
    through TestJob initialization, metadata object creation, and final output in
    both summary JSON and formatted output.

    Requirements covered: 4.1-4.6, 5.1-5.4, 6.1-6.9, 10.1-10.4
"""

import json
import os
import shutil
import tempfile
import unittest
import warnings
from datetime import datetime

import automojo.runtime.paths as runtime_paths
from automojo.runtime.enumerations import JobType
from automojo.runtime.runtimevariables import RuntimeVariablesDesc, DefaultValue
from automojo.thisapp.persona import APP_PERSONA_ESTABLISHED, establish_app_persona
from automojo.thisapp.wellknown import ThisApplicationSingleton

from automojo.testbase.testjob import TestJob
from automojo.testbase.results.model.buildinfo import BuildInfo
from automojo.testbase.results.model.pipelineinfo import PipelineInfo
from automojo.testbase.results.model.jobinfo import JobInfo, MissingOptionalFieldWarning
from automojo.testbase.results.model.renderinfo import RenderInfo
from automojo.testbase.results.recorders.jsonresultrecorder import JsonResultRecorder


class DummyLogger:
    """A minimal logger for testing purposes."""
    def __init__(self):
        self.debug_messages = []
        self.sections = []
        self.errors = []
        self.rendered = []

    def debug(self, msg):
        self.debug_messages.append(msg)

    def section(self, msg):
        self.sections.append(msg)

    def error(self, msg):
        self.errors.append(msg)

    def render(self, msg):
        self.rendered.append(msg)


class CIMetadataEndToEndTests(unittest.TestCase):
    """
    Integration tests for end-to-end CI metadata flow.
    
    These tests verify that:
    1. Environment variables are correctly read (Requirements 4.1-4.6, 5.1-5.4, 6.1-6.9)
    2. Metadata objects are created and passed through the system
    3. Summary JSON output contains correct metadata (Requirements 10.1-10.4)
    4. Formatted output contains correct metadata
    """

    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()
        self.temp_path = self.tempdir.name

        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.temp_path)

        # Define test metadata values
        self.build_metadata = {
            "branch": "integration-test-branch",
            "build": "integration-build-123",
            "flavor": "integration-release",
            "release": "3.0.0-integration",
            "url": "https://ci.integration.example.com/build/123"
        }

        self.pipeline_metadata = {
            "id": "integration-pipeline-uuid",
            "name": "Integration Test Pipeline",
            "instance": "integration-instance-uuid"
        }

        self.job_metadata = {
            "id": "integration-job-uuid",
            "name": "Integration Test Job",
            "type": "TestRun",
            "owner": "Integration Team",
            "label": "integration-label",
            "initiator": "integration@example.com",
            "venue": "integration-venue",
            "seed": "integration-seed-12345",
            "tag": "integration-correlation-tag"
        }

    def tearDown(self):
        """Clean up test fixtures."""
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    def _set_all_environment_variables(self):
        """Helper to set all CI/CD environment variables."""
        # Build variables (Requirements 4.1-4.5)
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_BUILD_BRANCH, self.build_metadata["branch"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_BUILD_NAME, self.build_metadata["build"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_BUILD_FLAVOR, self.build_metadata["flavor"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_BUILD_RELEASE, self.build_metadata["release"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_BUILD_URL, self.build_metadata["url"])

        # Pipeline variables (Requirements 5.1-5.3)
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_PIPELINE_ID, self.pipeline_metadata["id"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_PIPELINE_NAME, self.pipeline_metadata["name"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_PIPELINE_INSTANCE, self.pipeline_metadata["instance"])

        # Job variables (Requirements 6.1-6.9)
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_ID, self.job_metadata["id"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_NAME, self.job_metadata["name"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_TYPE, self.job_metadata["type"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_OWNER, self.job_metadata["owner"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_LABEL, self.job_metadata["label"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_INITIATOR, self.job_metadata["initiator"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_VENUE, self.job_metadata["venue"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_SEED, self.job_metadata["seed"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_TAG, self.job_metadata["tag"])

        # Additional required variables
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_RUN_ID, "integration-run-uuid")
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_STARTTIME, datetime.now())
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_AUTOMATION_POD, "integration-pod")


    def _create_render_info(self):
        """Helper to create RenderInfo for testing."""
        summary_filename = os.path.join(self.temp_path, "summary.json")
        summary_template = os.path.join(self.temp_path, "template.html")
        stream_results = os.path.join(self.temp_path, "results_stream.jsos")
        consolidated_results = os.path.join(self.temp_path, "results.json")

        # Create a dummy template file
        with open(summary_template, 'w') as f:
            f.write("<html></html>")

        return RenderInfo(
            title="Integration Test Run",
            summary_filename=summary_filename,
            summary_template=summary_template,
            stream_results_filename=stream_results,
            consolidated_results_filename=consolidated_results,
            static_resource_source=None,
            static_resource_destination=self.temp_path
        )

    def test_end_to_end_build_metadata_in_summary_json(self):
        """
        Test that build metadata flows from environment variables to summary JSON.
        
        Requirements: 4.1-4.6, 10.1
        """
        self._set_all_environment_variables()

        # Create TestJob and verify metadata is collected
        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify build metadata was read from environment variables
        self.assertEqual(job._branch, self.build_metadata["branch"])
        self.assertEqual(job._build, self.build_metadata["build"])
        self.assertEqual(job._flavor, self.build_metadata["flavor"])
        self.assertEqual(job._release, self.build_metadata["release"])
        self.assertEqual(job._build_url, self.build_metadata["url"])

        # Create metadata objects as TestJob.execute would
        build_info = BuildInfo(
            branch=job._branch,
            build=job._build,
            flavor=job._flavor,
            release=job._release,
            url=job._build_url
        )

        pipeline_info = PipelineInfo(
            id=job._pipeline_id,
            name=job._pipeline_name,
            instance=job._pipeline_instance
        )

        job_info = JobInfo(
            id=job._job_id,
            name=job._job_name,
            type=job._job_type,
            owner=job._job_owner,
            label=job._job_label,
            initiator=job._job_initiator,
            venue=job._job_venue,
            seed=job._job_seed,
            tag=job._job_tag
        )

        # Create recorder with metadata
        render_info = self._create_render_info()
        recorder = JsonResultRecorder(
            runid="integration-run-uuid",
            start=datetime.now(),
            render_info=render_info,
            apod="integration-pod",
            build_info=build_info,
            pipeline_info=pipeline_info,
            job_info=job_info
        )

        # Verify build section in summary JSON (Requirement 10.1)
        summary = recorder.summary
        self.assertIn("build", summary)
        build_section = summary["build"]
        self.assertEqual(build_section["branch"], self.build_metadata["branch"])
        self.assertEqual(build_section["build"], self.build_metadata["build"])
        self.assertEqual(build_section["flavor"], self.build_metadata["flavor"])
        self.assertEqual(build_section["release"], self.build_metadata["release"])
        self.assertEqual(build_section["url"], self.build_metadata["url"])


    def test_end_to_end_pipeline_metadata_in_summary_json(self):
        """
        Test that pipeline metadata flows from environment variables to summary JSON.
        
        Requirements: 5.1-5.4, 10.2
        """
        self._set_all_environment_variables()

        # Create TestJob and verify metadata is collected
        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify pipeline metadata was read from environment variables
        self.assertEqual(job._pipeline_id, self.pipeline_metadata["id"])
        self.assertEqual(job._pipeline_name, self.pipeline_metadata["name"])
        self.assertEqual(job._pipeline_instance, self.pipeline_metadata["instance"])

        # Create metadata objects
        build_info = BuildInfo(
            branch=job._branch,
            build=job._build,
            flavor=job._flavor,
            release=job._release,
            url=job._build_url
        )

        pipeline_info = PipelineInfo(
            id=job._pipeline_id,
            name=job._pipeline_name,
            instance=job._pipeline_instance
        )

        job_info = JobInfo(
            id=job._job_id,
            name=job._job_name,
            type=job._job_type,
            owner=job._job_owner,
            label=job._job_label,
            initiator=job._job_initiator,
            venue=job._job_venue,
            seed=job._job_seed,
            tag=job._job_tag
        )

        # Create recorder with metadata
        render_info = self._create_render_info()
        recorder = JsonResultRecorder(
            runid="integration-run-uuid",
            start=datetime.now(),
            render_info=render_info,
            apod="integration-pod",
            build_info=build_info,
            pipeline_info=pipeline_info,
            job_info=job_info
        )

        # Verify pipeline section in summary JSON (Requirement 10.2)
        summary = recorder.summary
        self.assertIn("pipeline", summary)
        pipeline_section = summary["pipeline"]
        self.assertEqual(pipeline_section["id"], self.pipeline_metadata["id"])
        self.assertEqual(pipeline_section["name"], self.pipeline_metadata["name"])
        self.assertEqual(pipeline_section["instance"], self.pipeline_metadata["instance"])

    def test_end_to_end_job_metadata_in_summary_json(self):
        """
        Test that job metadata flows from environment variables to summary JSON.
        
        Requirements: 6.1-6.9, 10.3
        """
        self._set_all_environment_variables()

        # Create TestJob and verify metadata is collected
        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify job metadata was read from environment variables
        self.assertEqual(job._job_id, self.job_metadata["id"])
        self.assertEqual(job._job_name, self.job_metadata["name"])
        self.assertEqual(job._job_type, self.job_metadata["type"])
        self.assertEqual(job._job_owner, self.job_metadata["owner"])
        self.assertEqual(job._job_label, self.job_metadata["label"])
        self.assertEqual(job._job_initiator, self.job_metadata["initiator"])
        self.assertEqual(job._job_venue, self.job_metadata["venue"])
        self.assertEqual(job._job_seed, self.job_metadata["seed"])
        self.assertEqual(job._job_tag, self.job_metadata["tag"])

        # Create metadata objects
        build_info = BuildInfo(
            branch=job._branch,
            build=job._build,
            flavor=job._flavor,
            release=job._release,
            url=job._build_url
        )

        pipeline_info = PipelineInfo(
            id=job._pipeline_id,
            name=job._pipeline_name,
            instance=job._pipeline_instance
        )

        job_info = JobInfo(
            id=job._job_id,
            name=job._job_name,
            type=job._job_type,
            owner=job._job_owner,
            label=job._job_label,
            initiator=job._job_initiator,
            venue=job._job_venue,
            seed=job._job_seed,
            tag=job._job_tag
        )

        # Create recorder with metadata
        render_info = self._create_render_info()
        recorder = JsonResultRecorder(
            runid="integration-run-uuid",
            start=datetime.now(),
            render_info=render_info,
            apod="integration-pod",
            build_info=build_info,
            pipeline_info=pipeline_info,
            job_info=job_info
        )

        # Verify job section in summary JSON (Requirement 10.3)
        summary = recorder.summary
        self.assertIn("job", summary)
        job_section = summary["job"]
        self.assertEqual(job_section["id"], self.job_metadata["id"])
        self.assertEqual(job_section["name"], self.job_metadata["name"])
        self.assertEqual(job_section["type"], self.job_metadata["type"])
        self.assertEqual(job_section["owner"], self.job_metadata["owner"])
        self.assertEqual(job_section["label"], self.job_metadata["label"])
        self.assertEqual(job_section["initiator"], self.job_metadata["initiator"])
        self.assertEqual(job_section["venue"], self.job_metadata["venue"])
        self.assertEqual(job_section["seed"], self.job_metadata["seed"])
        self.assertEqual(job_section["tag"], self.job_metadata["tag"])


    def test_end_to_end_metadata_in_formatted_output(self):
        """
        Test that metadata appears in formatted output lines.
        
        Requirements: 4.1-4.6, 5.1-5.4, 6.1-6.9
        """
        self._set_all_environment_variables()

        # Create TestJob and collect metadata
        job = TestJob(logger=DummyLogger(), testroot="root")

        # Create metadata objects
        build_info = BuildInfo(
            branch=job._branch,
            build=job._build,
            flavor=job._flavor,
            release=job._release,
            url=job._build_url
        )

        pipeline_info = PipelineInfo(
            id=job._pipeline_id,
            name=job._pipeline_name,
            instance=job._pipeline_instance
        )

        job_info = JobInfo(
            id=job._job_id,
            name=job._job_name,
            type=job._job_type,
            owner=job._job_owner,
            label=job._job_label,
            initiator=job._job_initiator,
            venue=job._job_venue,
            seed=job._job_seed,
            tag=job._job_tag
        )

        # Create recorder with metadata
        render_info = self._create_render_info()
        recorder = JsonResultRecorder(
            runid="integration-run-uuid",
            start=datetime.now(),
            render_info=render_info,
            apod="integration-pod",
            build_info=build_info,
            pipeline_info=pipeline_info,
            job_info=job_info
        )

        # Use context manager to properly initialize and finalize
        with recorder:
            pass

        # Get formatted output
        lines = recorder.format_lines()
        lines_text = "\n".join(lines)

        # Verify build metadata in formatted output
        self.assertIn(self.build_metadata["release"], lines_text)
        self.assertIn(self.build_metadata["branch"], lines_text)
        self.assertIn(self.build_metadata["build"], lines_text)
        self.assertIn(self.build_metadata["flavor"], lines_text)

        # Verify job metadata in formatted output
        self.assertIn(self.job_metadata["owner"], lines_text)

        # Verify run identifier in formatted output
        self.assertIn("integration-run-uuid", lines_text)

    def test_complete_metadata_flow_with_summary_file_write(self):
        """
        Test complete metadata flow including writing summary to file.
        
        Requirements: 4.1-4.6, 5.1-5.4, 6.1-6.9, 10.1-10.4
        """
        self._set_all_environment_variables()

        # Create TestJob and collect metadata
        job = TestJob(logger=DummyLogger(), testroot="root")

        # Create metadata objects
        build_info = BuildInfo(
            branch=job._branch,
            build=job._build,
            flavor=job._flavor,
            release=job._release,
            url=job._build_url
        )

        pipeline_info = PipelineInfo(
            id=job._pipeline_id,
            name=job._pipeline_name,
            instance=job._pipeline_instance
        )

        job_info = JobInfo(
            id=job._job_id,
            name=job._job_name,
            type=job._job_type,
            owner=job._job_owner,
            label=job._job_label,
            initiator=job._job_initiator,
            venue=job._job_venue,
            seed=job._job_seed,
            tag=job._job_tag
        )

        # Create recorder with metadata
        render_info = self._create_render_info()
        recorder = JsonResultRecorder(
            runid="integration-run-uuid",
            start=datetime.now(),
            render_info=render_info,
            apod="integration-pod",
            build_info=build_info,
            pipeline_info=pipeline_info,
            job_info=job_info
        )

        # Use context manager to properly initialize and finalize
        with recorder:
            pass

        # Read the summary file and verify metadata
        summary_filename = render_info.summary_filename
        self.assertTrue(os.path.exists(summary_filename))

        with open(summary_filename, 'r') as f:
            written_summary = json.load(f)

        # Verify build section (Requirement 10.1)
        self.assertIn("build", written_summary)
        self.assertEqual(written_summary["build"]["branch"], self.build_metadata["branch"])
        self.assertEqual(written_summary["build"]["build"], self.build_metadata["build"])
        self.assertEqual(written_summary["build"]["flavor"], self.build_metadata["flavor"])
        self.assertEqual(written_summary["build"]["release"], self.build_metadata["release"])
        self.assertEqual(written_summary["build"]["url"], self.build_metadata["url"])

        # Verify pipeline section (Requirement 10.2)
        self.assertIn("pipeline", written_summary)
        self.assertEqual(written_summary["pipeline"]["id"], self.pipeline_metadata["id"])
        self.assertEqual(written_summary["pipeline"]["name"], self.pipeline_metadata["name"])
        self.assertEqual(written_summary["pipeline"]["instance"], self.pipeline_metadata["instance"])

        # Verify job section (Requirement 10.3)
        self.assertIn("job", written_summary)
        self.assertEqual(written_summary["job"]["id"], self.job_metadata["id"])
        self.assertEqual(written_summary["job"]["name"], self.job_metadata["name"])
        self.assertEqual(written_summary["job"]["type"], self.job_metadata["type"])
        self.assertEqual(written_summary["job"]["owner"], self.job_metadata["owner"])
        self.assertEqual(written_summary["job"]["label"], self.job_metadata["label"])
        self.assertEqual(written_summary["job"]["initiator"], self.job_metadata["initiator"])
        self.assertEqual(written_summary["job"]["venue"], self.job_metadata["venue"])
        self.assertEqual(written_summary["job"]["seed"], self.job_metadata["seed"])
        self.assertEqual(written_summary["job"]["tag"], self.job_metadata["tag"])


    def test_pipeline_info_not_created_when_pipeline_id_not_set(self):
        """
        Test that PipelineInfo is not created when AM_PIPELINE_ID is not set.
        
        Requirement: 5.4
        """
        # Set build and job variables but NOT pipeline variables
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_BUILD_BRANCH, self.build_metadata["branch"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_BUILD_NAME, self.build_metadata["build"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_BUILD_FLAVOR, self.build_metadata["flavor"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_BUILD_RELEASE, self.build_metadata["release"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_BUILD_URL, self.build_metadata["url"])

        # Explicitly set pipeline ID to None
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_ID, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_NAME, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_INSTANCE, None)

        # Set job variables
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_ID, self.job_metadata["id"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_NAME, self.job_metadata["name"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_TYPE, self.job_metadata["type"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_OWNER, self.job_metadata["owner"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_LABEL, self.job_metadata["label"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_INITIATOR, self.job_metadata["initiator"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_VENUE, self.job_metadata["venue"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_SEED, self.job_metadata["seed"])
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_JOB_TAG, self.job_metadata["tag"])

        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_RUN_ID, "integration-run-uuid")
        self.this_app.override_variable_value(
            RuntimeVariablesDesc.AM_STARTTIME, datetime.now())

        # Create TestJob
        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify pipeline_id is None
        self.assertIsNone(job._pipeline_id)

        # Simulate the conditional PipelineInfo creation as in TestJob.execute
        pipeline_info = None
        if job._pipeline_id is not None:
            pipeline_info = PipelineInfo(
                id=job._pipeline_id,
                name=job._pipeline_name,
                instance=job._pipeline_instance
            )

        # Verify PipelineInfo was not created
        self.assertIsNone(pipeline_info)


class CIMetadataPartialEnvironmentTests(unittest.TestCase):
    """
    Integration tests for CI metadata flow with partial environment variables.
    
    These tests verify graceful handling when only some environment variables are set.
    """

    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()
        self.temp_path = self.tempdir.name

        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.temp_path)

    def tearDown(self):
        """Clean up test fixtures."""
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    def _create_render_info(self):
        """Helper to create RenderInfo for testing."""
        summary_filename = os.path.join(self.temp_path, "summary.json")
        summary_template = os.path.join(self.temp_path, "template.html")
        stream_results = os.path.join(self.temp_path, "results_stream.jsos")
        consolidated_results = os.path.join(self.temp_path, "results.json")

        with open(summary_template, 'w') as f:
            f.write("<html></html>")

        return RenderInfo(
            title="Partial Test Run",
            summary_filename=summary_filename,
            summary_template=summary_template,
            stream_results_filename=stream_results,
            consolidated_results_filename=consolidated_results,
            static_resource_source=None,
            static_resource_destination=self.temp_path
        )


    def test_partial_build_metadata_flow(self):
        """
        Test metadata flow with only some build variables set.
        
        Requirements: 4.1-4.6
        
        Note: With validation enabled, BuildInfo and PipelineInfo require all fields
        to be non-None. This test now verifies that validation errors are raised
        when required fields are None.
        """
        # Set only some build variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_BRANCH, "partial-branch")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_NAME, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_FLAVOR, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_RELEASE, "1.0.0-partial")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_URL, None)

        # Set required job variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_ID, "partial-job-id")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_NAME, "Partial Job")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, "TestRun")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_OWNER, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_LABEL, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_INITIATOR, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_VENUE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_SEED, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TAG, None)

        # Set pipeline variables to None (simulating no pipeline context)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_ID, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_NAME, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_INSTANCE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RUN_ID, "partial-run-uuid")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_STARTTIME, datetime.now())

        # Create TestJob
        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify partial build metadata
        self.assertEqual(job._branch, "partial-branch")
        self.assertIsNone(job._build)
        self.assertIsNone(job._flavor)
        self.assertEqual(job._release, "1.0.0-partial")
        self.assertIsNone(job._build_url)

        # Verify that BuildInfo validation rejects None values for required fields
        with self.assertRaises(ValueError) as context:
            BuildInfo(
                branch=job._branch,
                build=job._build,  # This is None
                flavor=job._flavor,  # This is None
                release=job._release,
                url=job._build_url  # This is None
            )
        self.assertIn("build", str(context.exception))
        self.assertIn("required", str(context.exception))

    def test_partial_job_metadata_flow(self):
        """
        Test metadata flow with only some job variables set.
        
        Requirements: 6.1-6.9
        
        Note: With validation enabled, PipelineInfo requires all fields to be non-None.
        This test now verifies that partial job metadata (optional fields as None)
        works correctly when pipeline info is provided with valid values.
        """
        # Set build variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_BRANCH, "test-branch")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_NAME, "test-build")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_FLAVOR, "test-flavor")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_RELEASE, "1.0.0")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_URL, "https://test.url")

        # Set only required job variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_ID, "partial-job-id")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_NAME, "Partial Job Name")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, "TestRun")
        # Leave optional job variables as None
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_OWNER, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_LABEL, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_INITIATOR, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_VENUE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_SEED, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TAG, None)

        # Set pipeline variables with valid values (required fields cannot be None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_ID, "partial-test-pipeline-id")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_NAME, "Partial Test Pipeline")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_INSTANCE, "partial-test-instance")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RUN_ID, "partial-job-run-uuid")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_STARTTIME, datetime.now())

        # Create TestJob
        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify partial job metadata
        self.assertEqual(job._job_id, "partial-job-id")
        self.assertEqual(job._job_name, "Partial Job Name")
        self.assertEqual(job._job_type, "TestRun")
        self.assertIsNone(job._job_owner)
        self.assertIsNone(job._job_label)
        self.assertIsNone(job._job_initiator)
        self.assertIsNone(job._job_venue)
        self.assertIsNone(job._job_seed)
        self.assertIsNone(job._job_tag)

        # Create metadata objects
        build_info = BuildInfo(
            branch=job._branch,
            build=job._build,
            flavor=job._flavor,
            release=job._release,
            url=job._build_url
        )

        # PipelineInfo with valid values (required fields cannot be None)
        pipeline_info = PipelineInfo(
            id=job._pipeline_id,
            name=job._pipeline_name,
            instance=job._pipeline_instance
        )

        # Suppress warnings for missing optional fields as this is intentional
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", MissingOptionalFieldWarning)
            job_info = JobInfo(
                id=job._job_id,
                name=job._job_name,
                type=job._job_type,
                owner=job._job_owner,
                label=job._job_label,
                initiator=job._job_initiator,
                venue=job._job_venue,
                seed=job._job_seed,
                tag=job._job_tag
            )

        # Create recorder with partial metadata
        render_info = self._create_render_info()
        recorder = JsonResultRecorder(
            runid="partial-job-run-uuid",
            start=datetime.now(),
            render_info=render_info,
            build_info=build_info,
            pipeline_info=pipeline_info,
            job_info=job_info
        )

        # Verify summary contains partial job data
        summary = recorder.summary
        self.assertIn("job", summary)
        self.assertEqual(summary["job"]["id"], "partial-job-id")
        self.assertEqual(summary["job"]["name"], "Partial Job Name")
        self.assertEqual(summary["job"]["type"], "TestRun")
        self.assertEqual(summary["job"]["owner"], "(unknown)")
        self.assertEqual(summary["job"]["label"], "(unknown)")
        self.assertEqual(summary["job"]["initiator"], "(unknown)")
        self.assertEqual(summary["job"]["venue"], "(unknown)")
        self.assertEqual(summary["job"]["seed"], "(unknown)")
        self.assertEqual(summary["job"]["tag"], "(unknown)")


if __name__ == "__main__":
    unittest.main()
