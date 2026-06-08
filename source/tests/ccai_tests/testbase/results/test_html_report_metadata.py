"""
    .. module:: ccai_tests.testbase.results.test_html_report_metadata
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Integration tests for HTML report metadata display.

    .. moduleauthor:: CodeCraftX

    These tests verify that CI/CD metadata is correctly included in the HTML report
    output files, ensuring the JavaScript components can properly display build,
    pipeline, and job information.

    Requirements covered: 15.1-15.4
"""

import json
import os
import tempfile
import unittest
import warnings
from datetime import datetime

import ccai.runtime.paths as runtime_paths
from ccai.runtime.enumerations import JobType
from ccai.runtime.runtimevariables import RuntimeVariablesDesc
from ccai.thisapp.persona import APP_PERSONA_ESTABLISHED, establish_app_persona
from ccai.thisapp.wellknown import ThisApplicationSingleton

from ccai.testbase.results.model.buildinfo import BuildInfo
from ccai.testbase.results.model.pipelineinfo import PipelineInfo
from ccai.testbase.results.model.jobinfo import JobInfo, MissingOptionalFieldWarning
from ccai.testbase.results.model.renderinfo import RenderInfo
from ccai.testbase.results.recorders.jsonresultrecorder import JsonResultRecorder


class HTMLReportMetadataIntegrationTests(unittest.TestCase):
    """
    Integration tests for HTML report metadata display.
    
    These tests verify that:
    1. Build information is included in summary JSON for HTML display (Requirement 15.1)
    2. Pipeline information is included in summary JSON for HTML display (Requirement 15.2)
    3. Job information is included in summary JSON for HTML display (Requirement 15.3)
    4. Missing metadata is gracefully handled in summary JSON (Requirement 15.4)
    """

    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="codecraftai-testbase",
                logger_name="codecraftai-testbase",
                log_basename="codecraftai-testbase"
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

        # Define test metadata values for HTML display
        self.build_metadata = {
            "branch": "html-test-branch",
            "build": "html-build-456",
            "flavor": "html-release",
            "release": "4.0.0-html",
            "url": "https://ci.html.example.com/build/456"
        }

        self.pipeline_metadata = {
            "id": "html-pipeline-uuid",
            "name": "HTML Test Pipeline",
            "instance": "html-instance-uuid"
        }

        self.job_metadata = {
            "id": "html-job-uuid",
            "name": "HTML Test Job",
            "type": "TestRun",
            "owner": "HTML Team",
            "label": "html-label",
            "initiator": "html@example.com",
            "venue": "html-venue",
            "seed": "html-seed-67890",
            "tag": "html-correlation-tag"
        }

    def tearDown(self):
        """Clean up test fixtures."""
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    def _create_render_info(self):
        """Helper to create RenderInfo for testing."""
        summary_filename = os.path.join(self.temp_path, "testrun_summary.json")
        summary_template = os.path.join(self.temp_path, "template.html")
        stream_results = os.path.join(self.temp_path, "testrun_results_stream.jsos")
        consolidated_results = os.path.join(self.temp_path, "testrun_results.json")

        # Create a dummy template file
        with open(summary_template, 'w') as f:
            f.write("<!DOCTYPE html><html><body></body></html>")

        return RenderInfo(
            title="HTML Report Test Run",
            summary_filename=summary_filename,
            summary_template=summary_template,
            stream_results_filename=stream_results,
            consolidated_results_filename=consolidated_results,
            static_resource_source=None,
            static_resource_destination=self.temp_path
        )

    def _create_metadata_objects(self):
        """Helper to create metadata objects for testing."""
        build_info = BuildInfo(
            branch=self.build_metadata["branch"],
            build=self.build_metadata["build"],
            flavor=self.build_metadata["flavor"],
            release=self.build_metadata["release"],
            url=self.build_metadata["url"]
        )

        pipeline_info = PipelineInfo(
            id=self.pipeline_metadata["id"],
            name=self.pipeline_metadata["name"],
            instance=self.pipeline_metadata["instance"]
        )

        job_info = JobInfo(
            id=self.job_metadata["id"],
            name=self.job_metadata["name"],
            type=self.job_metadata["type"],
            owner=self.job_metadata["owner"],
            label=self.job_metadata["label"],
            initiator=self.job_metadata["initiator"],
            venue=self.job_metadata["venue"],
            seed=self.job_metadata["seed"],
            tag=self.job_metadata["tag"]
        )

        return build_info, pipeline_info, job_info

    def test_html_report_build_information_display(self):
        """
        Test that build information is correctly structured for HTML report display.
        
        Requirement 15.1: THE HTML report template SHALL display build information 
        when available.
        
        This test verifies that the summary JSON contains build metadata in the
        format expected by the TestSummaryBanner JavaScript component.
        """
        build_info, pipeline_info, job_info = self._create_metadata_objects()
        render_info = self._create_render_info()

        recorder = JsonResultRecorder(
            runid="html-build-test-uuid",
            start=datetime.now(),
            render_info=render_info,
            apod="html-test-pod",
            build_info=build_info,
            pipeline_info=pipeline_info,
            job_info=job_info
        )

        # Use context manager to initialize and finalize
        with recorder:
            pass

        # Read the summary JSON file
        summary_filename = render_info.summary_filename
        self.assertTrue(os.path.exists(summary_filename))

        with open(summary_filename, 'r') as f:
            written_summary = json.load(f)

        # Verify build section exists and has correct structure for HTML display
        self.assertIn("build", written_summary)
        build_section = written_summary["build"]

        # Verify all build fields expected by TestSummaryBanner.syncData()
        self.assertIn("branch", build_section)
        self.assertIn("build", build_section)
        self.assertIn("flavor", build_section)
        self.assertIn("release", build_section)
        self.assertIn("url", build_section)

        # Verify values match
        self.assertEqual(build_section["branch"], self.build_metadata["branch"])
        self.assertEqual(build_section["build"], self.build_metadata["build"])
        self.assertEqual(build_section["flavor"], self.build_metadata["flavor"])
        self.assertEqual(build_section["release"], self.build_metadata["release"])
        self.assertEqual(build_section["url"], self.build_metadata["url"])

    def test_html_report_pipeline_information_display(self):
        """
        Test that pipeline information is correctly structured for HTML report display.
        
        Requirement 15.2: THE HTML report template SHALL display pipeline information 
        when available.
        
        This test verifies that the summary JSON contains pipeline metadata in the
        format expected by the HTML report JavaScript components.
        """
        build_info, pipeline_info, job_info = self._create_metadata_objects()
        render_info = self._create_render_info()

        recorder = JsonResultRecorder(
            runid="html-pipeline-test-uuid",
            start=datetime.now(),
            render_info=render_info,
            apod="html-test-pod",
            build_info=build_info,
            pipeline_info=pipeline_info,
            job_info=job_info
        )

        with recorder:
            pass

        # Read the summary JSON file
        summary_filename = render_info.summary_filename
        self.assertTrue(os.path.exists(summary_filename))

        with open(summary_filename, 'r') as f:
            written_summary = json.load(f)

        # Verify pipeline section exists and has correct structure
        self.assertIn("pipeline", written_summary)
        pipeline_section = written_summary["pipeline"]

        # Verify all pipeline fields
        self.assertIn("id", pipeline_section)
        self.assertIn("name", pipeline_section)
        self.assertIn("instance", pipeline_section)

        # Verify values match
        self.assertEqual(pipeline_section["id"], self.pipeline_metadata["id"])
        self.assertEqual(pipeline_section["name"], self.pipeline_metadata["name"])
        self.assertEqual(pipeline_section["instance"], self.pipeline_metadata["instance"])

    def test_html_report_job_information_display(self):
        """
        Test that job information is correctly structured for HTML report display.
        
        Requirement 15.3: THE HTML report template SHALL display job information 
        when available.
        
        This test verifies that the summary JSON contains job metadata in the
        format expected by the HTML report JavaScript components.
        """
        build_info, pipeline_info, job_info = self._create_metadata_objects()
        render_info = self._create_render_info()

        recorder = JsonResultRecorder(
            runid="html-job-test-uuid",
            start=datetime.now(),
            render_info=render_info,
            apod="html-test-pod",
            build_info=build_info,
            pipeline_info=pipeline_info,
            job_info=job_info
        )

        with recorder:
            pass

        # Read the summary JSON file
        summary_filename = render_info.summary_filename
        self.assertTrue(os.path.exists(summary_filename))

        with open(summary_filename, 'r') as f:
            written_summary = json.load(f)

        # Verify job section exists and has correct structure
        self.assertIn("job", written_summary)
        job_section = written_summary["job"]

        # Verify all job fields
        self.assertIn("id", job_section)
        self.assertIn("name", job_section)
        self.assertIn("type", job_section)
        self.assertIn("owner", job_section)
        self.assertIn("label", job_section)
        self.assertIn("initiator", job_section)
        self.assertIn("venue", job_section)
        self.assertIn("seed", job_section)
        self.assertIn("tag", job_section)

        # Verify values match
        self.assertEqual(job_section["id"], self.job_metadata["id"])
        self.assertEqual(job_section["name"], self.job_metadata["name"])
        self.assertEqual(job_section["type"], self.job_metadata["type"])
        self.assertEqual(job_section["owner"], self.job_metadata["owner"])
        self.assertEqual(job_section["label"], self.job_metadata["label"])
        self.assertEqual(job_section["initiator"], self.job_metadata["initiator"])
        self.assertEqual(job_section["venue"], self.job_metadata["venue"])
        self.assertEqual(job_section["seed"], self.job_metadata["seed"])
        self.assertEqual(job_section["tag"], self.job_metadata["tag"])

    def test_buildinfo_validation_rejects_none_values(self):
        """
        Test that BuildInfo validation rejects None values for required fields.
        
        Requirement 15.1-15.5: All BuildInfo fields are required and must be non-empty.
        
        This test verifies that when build metadata fields are None, a ValueError
        is raised during BuildInfo construction.
        """
        # Verify that None values for required fields raise ValueError
        with self.assertRaises(ValueError) as context:
            BuildInfo(
                branch=None,
                build="test-build",
                flavor="test-flavor",
                release="1.0.0",
                url="https://test.url"
            )
        self.assertIn("branch", str(context.exception))
        self.assertIn("required", str(context.exception))

    def test_pipelineinfo_validation_rejects_none_values(self):
        """
        Test that PipelineInfo validation rejects None values for required fields.
        
        Requirement 16.1-16.3: All PipelineInfo fields are required and must be non-empty.
        
        This test verifies that when pipeline metadata fields are None, a ValueError
        is raised during PipelineInfo construction.
        """
        # Verify that None values for required fields raise ValueError
        with self.assertRaises(ValueError) as context:
            PipelineInfo(
                id=None,
                name="Test Pipeline",
                instance="test-instance"
            )
        self.assertIn("id", str(context.exception))
        self.assertIn("required", str(context.exception))

    def test_html_report_graceful_handling_missing_job_metadata(self):
        """
        Test that HTML report gracefully handles missing optional job metadata.
        
        Requirement 15.4: THE HTML report template SHALL gracefully handle missing 
        metadata sections.
        """
        build_info = BuildInfo(
            branch="test-branch",
            build="test-build",
            flavor="test-flavor",
            release="1.0.0",
            url="https://test.url"
        )

        pipeline_info = PipelineInfo(
            id="test-pipeline-id",
            name="Test Pipeline",
            instance="test-instance"
        )

        # Create job info with only required fields, optional fields as None
        # Suppress warnings for missing optional fields as this is intentional
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", MissingOptionalFieldWarning)
            job_info = JobInfo(
                id="minimal-job-id",
                name="Minimal Job",
                type="TestRun",
                owner=None,
                label=None,
                initiator=None,
                venue=None,
                seed=None,
                tag=None
            )

        render_info = self._create_render_info()

        recorder = JsonResultRecorder(
            runid="html-missing-job-test-uuid",
            start=datetime.now(),
            render_info=render_info,
            build_info=build_info,
            pipeline_info=pipeline_info,
            job_info=job_info
        )

        with recorder:
            pass

        # Read the summary JSON file
        summary_filename = render_info.summary_filename
        self.assertTrue(os.path.exists(summary_filename))

        with open(summary_filename, 'r') as f:
            written_summary = json.load(f)

        # Verify job section exists
        self.assertIn("job", written_summary)
        job_section = written_summary["job"]

        # Verify required fields have values
        self.assertEqual(job_section["id"], "minimal-job-id")
        self.assertEqual(job_section["name"], "Minimal Job")
        self.assertEqual(job_section["type"], "TestRun")

        # Verify optional fields are "(unknown)"
        self.assertEqual(job_section["owner"], "(unknown)")
        self.assertEqual(job_section["label"], "(unknown)")
        self.assertEqual(job_section["initiator"], "(unknown)")
        self.assertEqual(job_section["venue"], "(unknown)")
        self.assertEqual(job_section["seed"], "(unknown)")
        self.assertEqual(job_section["tag"], "(unknown)")

    def test_html_report_summary_json_structure_for_javascript(self):
        """
        Test that the summary JSON structure matches what the JavaScript expects.
        
        This test verifies the complete structure of the summary JSON file
        to ensure compatibility with the TestSummaryBanner and other JavaScript
        components that read and display the metadata.
        """
        build_info, pipeline_info, job_info = self._create_metadata_objects()
        render_info = self._create_render_info()

        recorder = JsonResultRecorder(
            runid="html-structure-test-uuid",
            start=datetime.now(),
            render_info=render_info,
            apod="html-test-pod",
            build_info=build_info,
            pipeline_info=pipeline_info,
            job_info=job_info
        )

        with recorder:
            pass

        # Read the summary JSON file
        summary_filename = render_info.summary_filename
        with open(summary_filename, 'r') as f:
            written_summary = json.load(f)

        # Verify top-level structure expected by JavaScript
        expected_keys = ["version", "title", "runid", "build", "pipeline", "job",
                         "start", "stop", "result", "apod"]
        for key in expected_keys:
            self.assertIn(key, written_summary,
                          f"Missing expected key '{key}' in summary JSON")

        # Verify version is "2" as expected by JavaScript
        self.assertEqual(written_summary["version"], "2")

        # Verify result is set after finalization
        self.assertIn(written_summary["result"], ["PASSED", "FAILED", "RUNNING"])

        # Verify apod is included
        self.assertEqual(written_summary["apod"], "html-test-pod")

    def test_html_report_all_metadata_sections_present(self):
        """
        Test that all metadata sections are present in the summary JSON.
        
        This comprehensive test verifies that build, pipeline, and job sections
        are all present and correctly populated for HTML report display.
        """
        build_info, pipeline_info, job_info = self._create_metadata_objects()
        render_info = self._create_render_info()

        recorder = JsonResultRecorder(
            runid="html-all-metadata-test-uuid",
            start=datetime.now(),
            render_info=render_info,
            apod="html-test-pod",
            build_info=build_info,
            pipeline_info=pipeline_info,
            job_info=job_info
        )

        with recorder:
            pass

        # Read the summary JSON file
        summary_filename = render_info.summary_filename
        with open(summary_filename, 'r') as f:
            written_summary = json.load(f)

        # Verify all three metadata sections are present
        self.assertIn("build", written_summary)
        self.assertIn("pipeline", written_summary)
        self.assertIn("job", written_summary)

        # Verify build section is complete
        build_section = written_summary["build"]
        self.assertEqual(len(build_section), 5)  # branch, build, flavor, release, url

        # Verify pipeline section is complete
        pipeline_section = written_summary["pipeline"]
        self.assertEqual(len(pipeline_section), 3)  # id, name, instance

        # Verify job section is complete
        job_section = written_summary["job"]
        self.assertEqual(len(job_section), 9)  # id, name, type, owner, label, initiator, venue, seed, tag


if __name__ == "__main__":
    unittest.main()
