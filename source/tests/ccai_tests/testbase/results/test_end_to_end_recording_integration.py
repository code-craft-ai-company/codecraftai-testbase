"""
    .. module:: ccai_tests.testbase.results.test_end_to_end_recording_integration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Integration tests for end-to-end result recording.

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
from ccai.testbase.results.model.resulttype import ResultType
from ccai.testbase.results.model.testresult import TestResult
from ccai.testbase.results.model.jobcontainer import JobContainer
from ccai.testbase.results.model.testcontainer import TestContainer
from ccai.testbase.results.model.taskinggroup import TaskingGroup
from ccai.testbase.results.model.taskingresult import TaskingResult

from ccai.testbase.results.recorders.jsonresultrecorder import JsonResultRecorder

from ccai.xmodules.jsos import CHAR_RECORD_SEPERATOR, load_jsos_stream_from_file
from ccai.errors.xtraceback import OriginDetail, TraceDetail, TracebackDetail


class EndToEndRecordingIntegrationTests(unittest.TestCase):
    """
    Integration tests for complete test run with result recording.
    Requirements: 29.1-29.8, 42.1-42.6
    """

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

        self.render_info = RenderInfo(
            title="Integration Test Run",
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
        
        self.runid = "integration-test-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-integration",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/integration"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-integration-456",
            name="Integration Pipeline",
            instance="integration-instance-789"
        )
        
        self.job_info = JobInfo(
            id="job-integration-012",
            name="Integration Tests",
            type="TestRun",
            owner="Test Team",
            label="integration",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="integration-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


    def test_complete_test_run_with_result_recording(self):
        """
        Test a complete test run with result recording.
        Validates that all result types are properly recorded and files are created.
        Requirements: 29.1-29.8, 42.1-42.6
        """
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            # Create job container (root)
            job = JobContainer(inst_id="job-1", name="Test Job")
            recorder.preview(job)
            recorder.record(job)
            
            # Create test container
            test_container = TestContainer(
                inst_id="tc-1",
                name="test_module",
                parent_inst="job-1"
            )
            recorder.preview(test_container)
            recorder.record(test_container)
            
            # Create and record passing test
            test1 = TestResult(
                inst_id="test-1",
                name="test_passing",
                parent_inst="tc-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            recorder.preview(test1)
            test1.mark_passed()
            test1.finalize()
            recorder.record(test1)
            
            # Create and record failing test
            test2 = TestResult(
                inst_id="test-2",
                name="test_failing",
                parent_inst="tc-1",
                monikers=["param1"],
                pivots={"key": "value"},
                result_code=ResultCode.UNSET
            )
            recorder.preview(test2)
            origin = OriginDetail(file="test.py", lineno=10, scope="test_failing")
            trace = TraceDetail(origin=origin, call="assert False", code=["assert False"], context={})
            tb = TracebackDetail(extype="AssertionError", exargs=["Test failed"], traces=[trace])
            test2.add_failure(tb)
            test2.finalize()
            recorder.record(test2)
            
            # Create and record skipped test
            test3 = TestResult(
                inst_id="test-3",
                name="test_skipped",
                parent_inst="tc-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.SKIPPED
            )
            recorder.preview(test3)
            recorder.record(test3)
        
        # Verify summary file exists and has correct content
        self.assertTrue(os.path.exists(self.render_info.summary_filename))
        with open(self.render_info.summary_filename, 'r') as f:
            summary = json.load(f)
        
        self.assertEqual(summary["runid"], self.runid)
        self.assertEqual(summary["result"], "FAILED")  # Has failures
        self.assertIn("detail", summary)
        self.assertEqual(summary["detail"]["passed"], 1)
        self.assertEqual(summary["detail"]["failed"], 1)
        self.assertEqual(summary["detail"]["skipped"], 1)
        self.assertEqual(summary["detail"]["total"], 3)
        
        # Verify stream file exists
        self.assertTrue(os.path.exists(self.render_info.stream_results_filename))
        
        # Verify catalog file exists
        catalog_file = os.path.join(self.temp_dir, "catalog.json")
        self.assertTrue(os.path.exists(catalog_file))


    def test_stream_file_output_validation(self):
        """
        Test that the stream file contains valid JSOS format with all recorded results.
        Requirements: 42.1-42.6
        """
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            # Create job container
            job = JobContainer(inst_id="job-stream-1", name="Stream Test Job")
            recorder.preview(job)
            recorder.record(job)
            
            # Create test container
            test_container = TestContainer(
                inst_id="tc-stream-1",
                name="stream_test_module",
                parent_inst="job-stream-1"
            )
            recorder.preview(test_container)
            recorder.record(test_container)
            
            # Create test result
            test1 = TestResult(
                inst_id="test-stream-1",
                name="test_stream_validation",
                parent_inst="tc-stream-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            recorder.preview(test1)
            test1.mark_passed()
            test1.finalize()
            recorder.record(test1)
        
        # Read and validate stream file
        stream_items = load_jsos_stream_from_file(self.render_info.stream_results_filename)
        
        # Should have 6 items: preview + record for each of job, container, test
        self.assertEqual(len(stream_items), 6)
        
        # Validate job container records
        job_records = [r for r in stream_items if r.get("rtype") == "JOB"]
        self.assertEqual(len(job_records), 2)  # preview + record
        
        # Validate test container records
        tc_records = [r for r in stream_items if r.get("rtype") == "TEST_CONTAINER"]
        self.assertEqual(len(tc_records), 2)  # preview + record
        
        # Validate test records
        test_records = [r for r in stream_items if r.get("rtype") == "TEST"]
        self.assertEqual(len(test_records), 2)  # preview + record
        
        # For TEST type records, verify preview has no detail section and final has detail
        test_preview = [r for r in test_records if "detail" not in r]
        test_final = [r for r in test_records if "detail" in r]
        self.assertEqual(len(test_preview), 1)  # 1 preview
        self.assertEqual(len(test_final), 1)  # 1 final record
        
        # Verify the final test record has the expected detail structure
        self.assertIn("errors", test_final[0]["detail"])
        self.assertIn("failures", test_final[0]["detail"])
        self.assertIn("warnings", test_final[0]["detail"])

    def test_all_passed_tests_result_in_passed_summary(self):
        """
        Test that when all tests pass, the summary result is PASSED.
        Requirements: 26.4, 26.5
        """
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            # Create job container
            job = JobContainer(inst_id="job-pass-1", name="Pass Test Job")
            recorder.preview(job)
            recorder.record(job)
            
            # Create test container
            test_container = TestContainer(
                inst_id="tc-pass-1",
                name="pass_test_module",
                parent_inst="job-pass-1"
            )
            recorder.preview(test_container)
            recorder.record(test_container)
            
            # Create multiple passing tests
            for i in range(3):
                test = TestResult(
                    inst_id=f"test-pass-{i}",
                    name=f"test_passing_{i}",
                    parent_inst="tc-pass-1",
                    monikers=[],
                    pivots={},
                    result_code=ResultCode.UNSET
                )
                recorder.preview(test)
                test.mark_passed()
                test.finalize()
                recorder.record(test)
        
        # Verify summary shows PASSED
        with open(self.render_info.summary_filename, 'r') as f:
            summary = json.load(f)
        
        self.assertEqual(summary["result"], "PASSED")
        self.assertEqual(summary["detail"]["passed"], 3)
        self.assertEqual(summary["detail"]["failed"], 0)
        self.assertEqual(summary["detail"]["errors"], 0)
        self.assertEqual(summary["detail"]["total"], 3)

    def test_error_in_test_results_in_failed_summary(self):
        """
        Test that when a test has errors, the summary result is FAILED.
        Requirements: 26.4
        """
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            # Create job container
            job = JobContainer(inst_id="job-err-1", name="Error Test Job")
            recorder.preview(job)
            recorder.record(job)
            
            # Create test container
            test_container = TestContainer(
                inst_id="tc-err-1",
                name="error_test_module",
                parent_inst="job-err-1"
            )
            recorder.preview(test_container)
            recorder.record(test_container)
            
            # Create test with error
            test = TestResult(
                inst_id="test-err-1",
                name="test_with_error",
                parent_inst="tc-err-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            recorder.preview(test)
            origin = OriginDetail(file="test.py", lineno=10, scope="test_with_error")
            trace = TraceDetail(origin=origin, call="raise RuntimeError", code=["raise RuntimeError"], context={})
            tb = TracebackDetail(extype="RuntimeError", exargs=["Test error"], traces=[trace])
            test.add_error(tb)
            test.finalize()
            recorder.record(test)
        
        # Verify summary shows FAILED
        with open(self.render_info.summary_filename, 'r') as f:
            summary = json.load(f)
        
        self.assertEqual(summary["result"], "FAILED")
        self.assertEqual(summary["detail"]["errors"], 1)
        self.assertEqual(summary["detail"]["total"], 1)


    def test_tasking_results_recording(self):
        """
        Test recording of tasking groups and tasking results.
        Requirements: 29.6, 29.7
        """
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            # Create job container
            job = JobContainer(inst_id="job-task-1", name="Tasking Test Job")
            recorder.preview(job)
            recorder.record(job)
            
            # Create test container
            test_container = TestContainer(
                inst_id="tc-task-1",
                name="tasking_test_module",
                parent_inst="job-task-1"
            )
            recorder.preview(test_container)
            recorder.record(test_container)
            
            # Create test result
            test = TestResult(
                inst_id="test-task-1",
                name="test_with_tasking",
                parent_inst="tc-task-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            recorder.preview(test)
            
            # Create tasking group
            tasking_group = TaskingGroup(
                inst_id="tg-1",
                name="setup_group",
                parent_inst="test-task-1"
            )
            recorder.preview(tasking_group)
            
            # Create tasking results
            tasking1 = TaskingResult(
                inst_id="tasking-1",
                name="setup_task_1",
                parent_inst="tg-1",
                worker="worker-1",
                result_code=ResultCode.UNSET
            )
            recorder.preview(tasking1)
            tasking1.mark_passed()
            tasking1.finalize()
            recorder.record(tasking1)
            
            tasking2 = TaskingResult(
                inst_id="tasking-2",
                name="setup_task_2",
                parent_inst="tg-1",
                worker="worker-2",
                result_code=ResultCode.UNSET
            )
            recorder.preview(tasking2)
            tasking2.mark_passed()
            tasking2.finalize()
            recorder.record(tasking2)
            
            # Finalize tasking group
            tasking_group.finalize()
            recorder.record(tasking_group)
            
            # Finalize test
            test.mark_passed()
            test.finalize()
            recorder.record(test)
        
        # Read and validate stream file
        stream_items = load_jsos_stream_from_file(self.render_info.stream_results_filename)
        
        # Validate tasking group records
        tg_records = [r for r in stream_items if r.get("rtype") == "TASKING_GROUP"]
        self.assertEqual(len(tg_records), 2)  # preview + record
        
        # Validate tasking records
        tasking_records = [r for r in stream_items if r.get("rtype") == "TASKING"]
        self.assertEqual(len(tasking_records), 4)  # 2 taskings * (preview + record)


    def test_output_file_structure(self):
        """
        Test that all expected output files are created with correct structure.
        Requirements: 42.1-42.6
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
            job = JobContainer(inst_id="job-struct-1", name="Structure Test Job")
            recorder.preview(job)
            recorder.record(job)
            
            test_container = TestContainer(
                inst_id="tc-struct-1",
                name="structure_test_module",
                parent_inst="job-struct-1"
            )
            recorder.preview(test_container)
            recorder.record(test_container)
            
            test = TestResult(
                inst_id="test-struct-1",
                name="test_structure",
                parent_inst="tc-struct-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            recorder.preview(test)
            test.mark_passed()
            test.finalize()
            recorder.record(test)
        
        # Verify summary file structure
        self.assertTrue(os.path.exists(self.render_info.summary_filename))
        with open(self.render_info.summary_filename, 'r') as f:
            summary = json.load(f)
        
        # Check required summary fields
        self.assertIn("version", summary)
        self.assertIn("title", summary)
        self.assertIn("runid", summary)
        self.assertIn("build", summary)
        self.assertIn("pipeline", summary)
        self.assertIn("job", summary)
        self.assertIn("start", summary)
        self.assertIn("stop", summary)
        self.assertIn("result", summary)
        self.assertIn("detail", summary)
        
        # Verify stream file exists and is valid JSOS
        self.assertTrue(os.path.exists(self.render_info.stream_results_filename))
        stream_items = load_jsos_stream_from_file(self.render_info.stream_results_filename)
        self.assertGreater(len(stream_items), 0)
        
        # Verify catalog file exists
        catalog_file = os.path.join(self.temp_dir, "catalog.json")
        self.assertTrue(os.path.exists(catalog_file))
        with open(catalog_file, 'r') as f:
            catalog = json.load(f)
        self.assertIn("files", catalog)
        self.assertIn("folders", catalog)
        
        # The HTML summary template is deliberately NOT copied by the
        # near-standalone recorder -- publishing the HTML presentation is
        # IntegrationJsonResultRecorder behaviour (codecraftai-integration-runtime).
        html_file = os.path.join(self.temp_dir, "testsummary.html")
        self.assertFalse(os.path.exists(html_file))

    def test_context_manager_handles_exception_gracefully(self):
        """
        Test that the context manager properly finalizes even when an exception occurs.
        Requirements: 24.2, 24.4
        """
        try:
            with JsonResultRecorder(
                runid=self.runid,
                start=self.start,
                render_info=self.render_info,
                build_info=self.build_info,
                pipeline_info=self.pipeline_info,
                job_info=self.job_info
            ) as recorder:
                # Create job container
                job = JobContainer(inst_id="job-exc-1", name="Exception Test Job")
                recorder.preview(job)
                recorder.record(job)
                
                # Simulate an exception during test execution
                raise ValueError("Simulated test execution error")
        except ValueError:
            pass  # Expected exception
        
        # Verify summary file was still created and finalized
        self.assertTrue(os.path.exists(self.render_info.summary_filename))
        with open(self.render_info.summary_filename, 'r') as f:
            summary = json.load(f)
        
        # Summary should have stop time (indicating finalization occurred)
        self.assertIsNotNone(summary["stop"])


    def test_multiple_test_containers_recording(self):
        """
        Test recording results across multiple test containers (modules).
        Requirements: 29.4
        """
        with JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        ) as recorder:
            # Create job container
            job = JobContainer(inst_id="job-multi-1", name="Multi Container Test Job")
            recorder.preview(job)
            recorder.record(job)
            
            # Create first test container
            tc1 = TestContainer(
                inst_id="tc-multi-1",
                name="module_one",
                parent_inst="job-multi-1"
            )
            recorder.preview(tc1)
            recorder.record(tc1)
            
            # Create test in first container
            test1 = TestResult(
                inst_id="test-multi-1",
                name="test_in_module_one",
                parent_inst="tc-multi-1",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            recorder.preview(test1)
            test1.mark_passed()
            test1.finalize()
            recorder.record(test1)
            
            # Create second test container
            tc2 = TestContainer(
                inst_id="tc-multi-2",
                name="module_two",
                parent_inst="job-multi-1"
            )
            recorder.preview(tc2)
            recorder.record(tc2)
            
            # Create test in second container
            test2 = TestResult(
                inst_id="test-multi-2",
                name="test_in_module_two",
                parent_inst="tc-multi-2",
                monikers=[],
                pivots={},
                result_code=ResultCode.UNSET
            )
            recorder.preview(test2)
            test2.mark_passed()
            test2.finalize()
            recorder.record(test2)
        
        # Read and validate stream file
        stream_items = load_jsos_stream_from_file(self.render_info.stream_results_filename)
        
        # Validate test container records
        tc_records = [r for r in stream_items if r.get("rtype") == "TEST_CONTAINER"]
        self.assertEqual(len(tc_records), 4)  # 2 containers * (preview + record)
        
        # Verify parent relationships
        tc_names = set(r["name"] for r in tc_records)
        self.assertIn("module_one", tc_names)
        self.assertIn("module_two", tc_names)
        
        # Verify summary counts
        with open(self.render_info.summary_filename, 'r') as f:
            summary = json.load(f)
        
        self.assertEqual(summary["detail"]["passed"], 2)
        self.assertEqual(summary["detail"]["total"], 2)


if __name__ == "__main__":
    unittest.main()
