"""
    .. module:: ccai_tests.testbase.results.test_html_report_generation_integration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Integration tests for HTML report generation including catalog file generation
               and static resource deployment.

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
from ccai.testbase.results.model.jobcontainer import JobContainer
from ccai.testbase.results.model.testcontainer import TestContainer

from ccai.testbase.results.recorders.jsonresultrecorder import JsonResultRecorder
from ccai.testbase.results.utilities import catalog_tree


class CatalogFileGenerationIntegrationTests(unittest.TestCase):
    """
    Integration tests for catalog file generation during HTML report generation.
    Requirements: 31.1-31.7
    """

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="Catalog Integration Test",
            summary_filename=os.path.join(self.temp_dir, "testsummary.json"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "testresults_stream.jsos"),
            consolidated_results_filename=os.path.join(self.temp_dir, "testresults.json"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html><body>Test Summary</body></html>")
        
        self.runid = "catalog-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-catalog",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/catalog"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-catalog-456",
            name="Catalog Pipeline",
            instance="catalog-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-catalog-012",
            name="Catalog Tests",
            type="TestRun",
            owner="Test Team",
            label="catalog",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="catalog-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_catalog_output_directory_calls_catalog_tree(self):
        """
        Test that catalog_output_directory method calls catalog_tree on the output directory.
        Requirements: 31.1
        """
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            # Create minimal test run
            job = JobContainer(inst_id="job-cat-1", name="Catalog Test Job")
            recorder.preview(job)
            recorder.record(job)
        
        # Verify catalog.json was created in output directory
        catalog_file = os.path.join(self.temp_dir, "catalog.json")
        self.assertTrue(os.path.exists(catalog_file))

    def test_catalog_json_contains_files_and_folders_arrays(self):
        """
        Test that catalog.json files contain files and folders arrays.
        Requirements: 31.2, 31.3
        """
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            job = JobContainer(inst_id="job-arrays-1", name="Arrays Test Job")
            recorder.preview(job)
            recorder.record(job)
        
        catalog_file = os.path.join(self.temp_dir, "catalog.json")
        with open(catalog_file, 'r') as f:
            catalog = json.load(f)
        
        self.assertIn("files", catalog)
        self.assertIn("folders", catalog)
        self.assertIsInstance(catalog["files"], list)
        self.assertIsInstance(catalog["folders"], list)

    def test_catalog_tree_skips_pycache_directories(self):
        """
        Test that catalog_tree skips __pycache__ directories.
        Requirements: 31.4, 31.6
        """
        # Create __pycache__ directory with files
        pycache_dir = os.path.join(self.temp_dir, "__pycache__")
        os.makedirs(pycache_dir)
        with open(os.path.join(pycache_dir, "module.cpython-312.pyc"), 'w') as f:
            f.write("dummy")
        
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            job = JobContainer(inst_id="job-pycache-1", name="Pycache Test Job")
            recorder.preview(job)
            recorder.record(job)
        
        # Verify __pycache__ is not in the folders list
        catalog_file = os.path.join(self.temp_dir, "catalog.json")
        with open(catalog_file, 'r') as f:
            catalog = json.load(f)
        
        self.assertNotIn("__pycache__", catalog["folders"])

    def test_catalog_tree_does_not_descend_into_diagnostics(self):
        """
        Test that catalog_tree does not descend into diagnostics directories.
        Requirements: 31.5, 31.7
        """
        # Create diagnostics directory with subdirectories
        diagnostics_dir = os.path.join(self.temp_dir, "diagnostics")
        os.makedirs(diagnostics_dir)
        with open(os.path.join(diagnostics_dir, "log.txt"), 'w') as f:
            f.write("diagnostic log")
        
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            job = JobContainer(inst_id="job-diag-1", name="Diagnostics Test Job")
            recorder.preview(job)
            recorder.record(job)
        
        # Verify diagnostics is in folders list (it's cataloged but not descended into)
        catalog_file = os.path.join(self.temp_dir, "catalog.json")
        with open(catalog_file, 'r') as f:
            catalog = json.load(f)
        
        self.assertIn("diagnostics", catalog["folders"])
        
        # Verify no catalog.json was created inside diagnostics
        diagnostics_catalog = os.path.join(diagnostics_dir, "catalog.json")
        self.assertFalse(os.path.exists(diagnostics_catalog))

    def test_catalog_created_in_subdirectories(self):
        """
        Test that catalog.json files are created in subdirectories.
        Requirements: 31.2
        """
        # Create subdirectory structure
        sub_dir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(sub_dir)
        with open(os.path.join(sub_dir, "test_file.txt"), 'w') as f:
            f.write("test content")
        
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            job = JobContainer(inst_id="job-sub-1", name="Subdir Test Job")
            recorder.preview(job)
            recorder.record(job)
        
        # Verify catalog.json exists in subdirectory
        sub_catalog = os.path.join(sub_dir, "catalog.json")
        self.assertTrue(os.path.exists(sub_catalog))
        
        with open(sub_catalog, 'r') as f:
            catalog = json.load(f)
        
        self.assertIn("test_file.txt", catalog["files"])

    def test_catalog_updated_after_each_recording_operation(self):
        """
        Test that catalog is updated after preview, record, and update_summary operations.
        Requirements: 31.1
        """
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            # After __enter__, catalog should exist
            catalog_file = os.path.join(self.temp_dir, "catalog.json")
            self.assertTrue(os.path.exists(catalog_file))
            
            # Record a job
            job = JobContainer(inst_id="job-update-1", name="Update Test Job")
            recorder.preview(job)
            
            # Catalog should still exist and be valid
            with open(catalog_file, 'r') as f:
                catalog = json.load(f)
            self.assertIn("files", catalog)
            
            recorder.record(job)
            
            # Catalog should be updated
            with open(catalog_file, 'r') as f:
                catalog = json.load(f)
            self.assertIn("files", catalog)


class StaticResourceDeploymentIntegrationTests(unittest.TestCase):
    """
    Integration tests for static resource deployment during HTML report generation.
    Requirements: 42.5, 42.6
    """

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.static_src_dir = tempfile.mkdtemp()
        self.static_dest_dir = os.path.join(self.temp_dir, "static")
        
        self.runid = "static-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-static",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/static"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-static-456",
            name="Static Pipeline",
            instance="static-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-static-012",
            name="Static Tests",
            type="TestRun",
            owner="Test Team",
            label="static",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="static-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        if os.path.exists(self.static_src_dir):
            shutil.rmtree(self.static_src_dir)

    def test_static_resources_deployed_to_destination(self):
        """
        Test that static resources are copied from source to destination.
        Requirements: 42.6
        """
        # Create static resource files in source directory
        css_dir = os.path.join(self.static_src_dir, "css")
        os.makedirs(css_dir)
        with open(os.path.join(css_dir, "style.css"), 'w') as f:
            f.write("body { margin: 0; }")
        
        js_dir = os.path.join(self.static_src_dir, "js")
        os.makedirs(js_dir)
        with open(os.path.join(js_dir, "app.js"), 'w') as f:
            f.write("console.log('test');")
        
        # Create template file
        template_file = os.path.join(self.temp_dir, "template.html")
        with open(template_file, 'w') as f:
            f.write("<html><body>Test Summary</body></html>")
        
        render_info = RenderInfo(
            title="Static Resource Test",
            summary_filename=os.path.join(self.temp_dir, "testsummary.json"),
            summary_template=template_file,
            stream_results_filename=os.path.join(self.temp_dir, "testresults_stream.jsos"),
            consolidated_results_filename=os.path.join(self.temp_dir, "testresults.json"),
            static_resource_source=self.static_src_dir,
            static_resource_destination=self.static_dest_dir
        )
        
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            job = JobContainer(inst_id="job-static-1", name="Static Test Job")
            recorder.preview(job)
            recorder.record(job)
        
        # Verify static resources were deployed
        self.assertTrue(os.path.exists(self.static_dest_dir))
        self.assertTrue(os.path.exists(os.path.join(self.static_dest_dir, "css", "style.css")))
        self.assertTrue(os.path.exists(os.path.join(self.static_dest_dir, "js", "app.js")))
        
        # Verify content was copied correctly
        with open(os.path.join(self.static_dest_dir, "css", "style.css"), 'r') as f:
            self.assertEqual(f.read(), "body { margin: 0; }")

    def test_static_subdirectory_created_for_resources(self):
        """
        Test that the static subdirectory is created for static resources.
        Requirements: 42.6
        """
        # Create a simple static resource
        with open(os.path.join(self.static_src_dir, "test.txt"), 'w') as f:
            f.write("test content")
        
        template_file = os.path.join(self.temp_dir, "template.html")
        with open(template_file, 'w') as f:
            f.write("<html><body>Test</body></html>")
        
        render_info = RenderInfo(
            title="Static Subdir Test",
            summary_filename=os.path.join(self.temp_dir, "testsummary.json"),
            summary_template=template_file,
            stream_results_filename=os.path.join(self.temp_dir, "testresults_stream.jsos"),
            consolidated_results_filename=os.path.join(self.temp_dir, "testresults.json"),
            static_resource_source=self.static_src_dir,
            static_resource_destination=self.static_dest_dir
        )
        
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            job = JobContainer(inst_id="job-subdir-1", name="Subdir Test Job")
            recorder.preview(job)
            recorder.record(job)
        
        # Verify static directory was created
        self.assertTrue(os.path.isdir(self.static_dest_dir))

    def test_catalog_json_in_output_directory(self):
        """
        Test that catalog.json is created in the output directory for navigation.
        Requirements: 42.5
        """
        template_file = os.path.join(self.temp_dir, "template.html")
        with open(template_file, 'w') as f:
            f.write("<html><body>Test</body></html>")
        
        render_info = RenderInfo(
            title="Catalog Output Test",
            summary_filename=os.path.join(self.temp_dir, "testsummary.json"),
            summary_template=template_file,
            stream_results_filename=os.path.join(self.temp_dir, "testresults_stream.jsos"),
            consolidated_results_filename=os.path.join(self.temp_dir, "testresults.json"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            job = JobContainer(inst_id="job-catalog-out-1", name="Catalog Output Test Job")
            recorder.preview(job)
            recorder.record(job)
        
        # Verify catalog.json exists in output directory
        catalog_file = os.path.join(self.temp_dir, "catalog.json")
        self.assertTrue(os.path.exists(catalog_file))
        
        with open(catalog_file, 'r') as f:
            catalog = json.load(f)
        
        # Verify catalog contains expected files
        self.assertIn("testsummary.json", catalog["files"])
        self.assertIn("testsummary.html", catalog["files"])

    def test_static_resources_not_overwritten_if_exist(self):
        """
        Test that existing static resources are not overwritten.
        Requirements: 42.6
        """
        # Create static resource in source
        with open(os.path.join(self.static_src_dir, "existing.txt"), 'w') as f:
            f.write("source content")
        
        # Create destination directory with existing file
        os.makedirs(self.static_dest_dir)
        with open(os.path.join(self.static_dest_dir, "existing.txt"), 'w') as f:
            f.write("destination content - should not be overwritten")
        
        template_file = os.path.join(self.temp_dir, "template.html")
        with open(template_file, 'w') as f:
            f.write("<html><body>Test</body></html>")
        
        render_info = RenderInfo(
            title="No Overwrite Test",
            summary_filename=os.path.join(self.temp_dir, "testsummary.json"),
            summary_template=template_file,
            stream_results_filename=os.path.join(self.temp_dir, "testresults_stream.jsos"),
            consolidated_results_filename=os.path.join(self.temp_dir, "testresults.json"),
            static_resource_source=self.static_src_dir,
            static_resource_destination=self.static_dest_dir
        )
        
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            job = JobContainer(inst_id="job-no-overwrite-1", name="No Overwrite Test Job")
            recorder.preview(job)
            recorder.record(job)
        
        # Verify existing file was not overwritten
        with open(os.path.join(self.static_dest_dir, "existing.txt"), 'r') as f:
            content = f.read()
        
        self.assertEqual(content, "destination content - should not be overwritten")

    def test_nested_static_resources_deployed(self):
        """
        Test that nested static resources are properly deployed.
        Requirements: 42.6
        """
        # Create nested directory structure in source
        nested_dir = os.path.join(self.static_src_dir, "css", "themes", "dark")
        os.makedirs(nested_dir)
        with open(os.path.join(nested_dir, "dark.css"), 'w') as f:
            f.write(".dark { background: #000; }")
        
        template_file = os.path.join(self.temp_dir, "template.html")
        with open(template_file, 'w') as f:
            f.write("<html><body>Test</body></html>")
        
        render_info = RenderInfo(
            title="Nested Static Test",
            summary_filename=os.path.join(self.temp_dir, "testsummary.json"),
            summary_template=template_file,
            stream_results_filename=os.path.join(self.temp_dir, "testresults_stream.jsos"),
            consolidated_results_filename=os.path.join(self.temp_dir, "testresults.json"),
            static_resource_source=self.static_src_dir,
            static_resource_destination=self.static_dest_dir
        )
        
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            job = JobContainer(inst_id="job-nested-1", name="Nested Test Job")
            recorder.preview(job)
            recorder.record(job)
        
        # Verify nested structure was created
        nested_dest = os.path.join(self.static_dest_dir, "css", "themes", "dark", "dark.css")
        self.assertTrue(os.path.exists(nested_dest))
        
        with open(nested_dest, 'r') as f:
            self.assertEqual(f.read(), ".dark { background: #000; }")

    def test_no_static_deployment_when_source_is_none(self):
        """
        Test that no static deployment occurs when static_resource_source is None.
        Requirements: 42.6
        """
        template_file = os.path.join(self.temp_dir, "template.html")
        with open(template_file, 'w') as f:
            f.write("<html><body>Test</body></html>")
        
        render_info = RenderInfo(
            title="No Static Test",
            summary_filename=os.path.join(self.temp_dir, "testsummary.json"),
            summary_template=template_file,
            stream_results_filename=os.path.join(self.temp_dir, "testresults_stream.jsos"),
            consolidated_results_filename=os.path.join(self.temp_dir, "testresults.json"),
            static_resource_source=None,
            static_resource_destination=self.static_dest_dir
        )
        
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            job = JobContainer(inst_id="job-no-static-1", name="No Static Test Job")
            recorder.preview(job)
            recorder.record(job)
        
        # Verify static directory was not created
        self.assertFalse(os.path.exists(self.static_dest_dir))


if __name__ == "__main__":
    unittest.main()
