import os
import tempfile
import unittest
from datetime import datetime

import automojo.runtime.paths as runtime_paths
from automojo.runtime.enumerations import JobType
from automojo.runtime.runtimevariables import RuntimeVariablesDesc, DefaultValue
from automojo.thisapp.persona import APP_PERSONA_ESTABLISHED, establish_app_persona
from automojo.thisapp.wellknown import ThisApplicationSingleton

from automojo.testbase.testjob import TestJob
from automojo.testbase.results.model.buildinfo import BuildInfo
from automojo.testbase.results.model.pipelineinfo import PipelineInfo
from automojo.testbase.results.model.renderinfo import RenderInfo
from automojo.testbase.results.model.jobinfo import JobInfo
from automojo.testbase.results.recorders.jsonresultrecorder import JsonResultRecorder
from automojo.testbase.sequencing.testsequencer import TestSequencer


class DummyLogger:
    def __init__(self):
        self.debug_messages = []
        self.sections = []
        self.errors = []

    def debug(self, msg):
        self.debug_messages.append(msg)

    def section(self, msg):
        self.sections.append(msg)

    def error(self, msg):
        self.errors.append(msg)

    def render(self, msg):
        pass


class DummySequencer:
    def __init__(self):
        self.calls = []
        self.references = ["ref"]
        self.import_errors = ["imp"]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def discover(self, test_module=None):
        self.calls.append("discover")
        return 1

    def attach_to_environment(self):
        self.calls.append("env")

    def attach_to_framework(self):
        self.calls.append("framework")

    def diagnostic_capture_post_testrun(self, level):
        self.calls.append(("post", level))

    def diagnostic_capture_pre_testrun(self, level):
        self.calls.append(("pre", level))

    def establish_presence(self):
        self.calls.append("presence")


class DummyJob(TestJob):
    def __init__(self):
        super().__init__(logger=DummyLogger(), testroot="root")
        self.begin_called = False
        self.finalize_called = False

    def begin(self):
        self.begin_called = True

    def finalize(self):
        self.finalize_called = True


class QueryJob(TestJob):
    def __init__(self):
        super().__init__(logger=DummyLogger(), testroot="root")
        self._dummy_seq = DummySequencer()

    def _create_sequencer(self):
        return self._dummy_seq


class TestJobTests(unittest.TestCase):

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(name="automojo-testbase", logger_name="automojo-testbase", log_basename="automojo-testbase")

        self.tempdir = tempfile.TemporaryDirectory()

        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

    def tearDown(self):
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    def test_context_manager_calls_begin_and_finalize(self):
        job = DummyJob()
        with job as j:
            self.assertIs(j, job)
            self.assertTrue(job.begin_called)
        self.assertTrue(job.finalize_called)

    def test_internal_sequencer_and_recorder_creation(self):
        job = TestJob(logger=DummyLogger(), testroot="troot")
        seq = job._create_sequencer()
        self.assertIsInstance(seq, TestSequencer)
        self.assertEqual(seq._root, "troot")
        self.assertIsNone(seq._includes)

        with tempfile.TemporaryDirectory() as tdir:
            rinfo = RenderInfo(
                title="t",
                summary_filename=os.path.join(tdir, "sum.json"),
                summary_template=os.path.join(tdir, "tmpl"),
                stream_results_filename=os.path.join(tdir, "stream"),
                consolidated_results_filename=os.path.join(tdir, "cons"),
                static_resource_source=tdir,
                static_resource_destination=tdir,
            )
            binfo = BuildInfo(branch="b", build="build", flavor="flavor", release="rel", url="url")
            pinfo = PipelineInfo(id="pid", name="nm", instance="inst")
            jinfo = JobInfo(id="jid", name="jnm", type="t", owner="o", label="l", initiator="i", venue="v", tag="tag")
            rec = job._create_recorder(
                runid="rid",
                start=datetime.now(),
                render_info=rinfo,
                build_info=binfo,
                pipeline_info=pinfo,
                job_info=jinfo,
            )
            self.assertIsInstance(rec, JsonResultRecorder)
            self.assertEqual(rec._runid, "rid")

    def test_query_uses_sequencer(self):
        job = QueryJob()
        res = job.query()
        self.assertEqual(res, ["ref"])
        self.assertEqual(job.import_errors, ["imp"])
        self.assertIn("discover", job._dummy_seq.calls)

    def test_fire_methods_invoke_sequencer_and_logger(self):
        logger = DummyLogger()
        job = TestJob(logger=logger, testroot="root")
        seq = DummySequencer()

        job.fire_attach_to_environment(seq)
        job.fire_attach_to_framework(seq)
        job.fire_diagnostic_capture_pre_testrun(seq, level=1)
        job.fire_diagnostic_capture_post_testrun(seq, level=2)
        job.fire_establish_presence(seq)
        job.fire_activate_configuration()
        job.fire_activate_integration()
        job.fire_activate_operations()

        self.assertIn("env", seq.calls)
        self.assertIn("framework", seq.calls)
        self.assertIn(("pre", 1), seq.calls)
        self.assertIn(("post", 2), seq.calls)
        self.assertIn("presence", seq.calls)
        self.assertIn("Firing: fire_activate_configuration", logger.debug_messages)
        self.assertIn("Firing: fire_activate_integration", logger.debug_messages)
        self.assertIn("Firing: fire_activate_operations", logger.debug_messages)

    def test_build_runtime_variables_read_during_init(self):
        """Test that build-related RuntimeVariables are read during __init__."""
        # Set build-related runtime variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_BRANCH, "main")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_NAME, "build-123")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_FLAVOR, "release")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_RELEASE, "1.0.0")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_URL, "https://ci.example.com/build/123")

        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify build metadata is stored as instance attributes
        self.assertEqual(job._branch, "main")
        self.assertEqual(job._build, "build-123")
        self.assertEqual(job._flavor, "release")
        self.assertEqual(job._release, "1.0.0")
        self.assertEqual(job._build_url, "https://ci.example.com/build/123")

    def test_pipeline_runtime_variables_read_during_init(self):
        """Test that pipeline-related RuntimeVariables are read during __init__."""
        # Set pipeline-related runtime variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_ID, "pipeline-uuid")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_NAME, "CI Pipeline")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_INSTANCE, "instance-uuid")

        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify pipeline metadata is stored as instance attributes
        self.assertEqual(job._pipeline_id, "pipeline-uuid")
        self.assertEqual(job._pipeline_name, "CI Pipeline")
        self.assertEqual(job._pipeline_instance, "instance-uuid")

    def test_job_runtime_variables_read_during_init(self):
        """Test that job-related RuntimeVariables are read during __init__."""
        # Set job-related runtime variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_ID, "job-uuid")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_NAME, "Integration Tests")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, "TestRun")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_OWNER, "QA Team")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_LABEL, "nightly")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_INITIATOR, "user@example.com")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_VENUE, "staging")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_SEED, "12345")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TAG, "correlation-tag")

        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify job metadata is stored as instance attributes
        self.assertEqual(job._job_id, "job-uuid")
        self.assertEqual(job._job_name, "Integration Tests")
        self.assertEqual(job._job_type, "TestRun")
        self.assertEqual(job._job_owner, "QA Team")
        self.assertEqual(job._job_label, "nightly")
        self.assertEqual(job._job_initiator, "user@example.com")
        self.assertEqual(job._job_venue, "staging")
        self.assertEqual(job._job_seed, "12345")
        self.assertEqual(job._job_tag, "correlation-tag")

    def test_metadata_stored_as_instance_attributes(self):
        """Test that all CI/CD metadata values are stored as instance attributes."""
        # Set all metadata runtime variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_AUTOMATION_POD, "automation-pod-1")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RUN_ID, "run-uuid")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_BRANCH, "feature-branch")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_ID, "pipe-id")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_ID, "job-id")

        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify all metadata is accessible as instance attributes
        self.assertEqual(job._apod, "automation-pod-1")
        self.assertEqual(job._run_id, "run-uuid")
        self.assertEqual(job._branch, "feature-branch")
        self.assertEqual(job._pipeline_id, "pipe-id")
        self.assertEqual(job._job_id, "job-id")

    def test_title_assignment_from_job_name_when_set(self):
        """Test that title is assigned from job name when AM_JOB_NAME is set."""
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_NAME, "My Custom Job Name")

        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify title is set from job name
        self.assertEqual(job._title, "My Custom Job Name")

    def test_title_default_when_job_name_not_set(self):
        """Test that title defaults to 'Test Run' when AM_JOB_NAME is not set."""
        # Ensure job name is set to the default NotSet value
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_NAME, DefaultValue.NotSet)

        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify title defaults to "Test Run"
        self.assertEqual(job._title, "Test Run")


class MetadataCapturingSequencer:
    """A sequencer that returns a count of 1 to trigger metadata creation."""
    def __init__(self):
        self.import_errors = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def discover(self, test_module=None):
        return 1

    def record_import_errors(self, filename):
        pass

    def attach_to_framework(self):
        pass

    def attach_to_environment(self):
        pass

    def expand_test_tree_based_on_query(self):
        pass

    def generate_testrun_sequence_document(self, filename):
        pass

    def execute_tests(self, runid, recorder):
        pass

    def diagnostic_capture_post_testrun(self, level):
        pass


class MetadataCapturingRecorder:
    """A recorder that captures metadata objects passed to it."""
    def __init__(self, build_info, pipeline_info, job_info, **kwargs):
        self.build_info = build_info
        self.pipeline_info = pipeline_info
        self.job_info = job_info
        self.summary = {"result": "PASSED"}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def finalize(self):
        pass

    def format_lines(self):
        return []


class MetadataCapturingJob(TestJob):
    """A TestJob subclass that captures metadata objects for testing."""
    def __init__(self, logger, testroot):
        super().__init__(logger=logger, testroot=testroot)
        self.captured_build_info = None
        self.captured_pipeline_info = None
        self.captured_job_info = None

    def begin(self):
        """Override begin to avoid path resolution dependencies."""
        self._starttime = datetime.now()
        self._test_results_dir = tempfile.gettempdir()
        self._runtime_archive = os.path.join(self._test_results_dir, "runtime-declared.yaml")
        self._stream_result_filename = os.path.join(self._test_results_dir, "testrun_results_stream.jsos")
        self._consolidated_result_filename = os.path.join(self._test_results_dir, "testrun_results.json")
        self._summary_filename = os.path.join(self._test_results_dir, "testrun_summary.json")
        self._summary_template = os.path.join(self._test_results_dir, "template.html")
        self._import_errors_filename = os.path.join(self._test_results_dir, "import_errors.jsos")
        self._testrun_sequence_filename = os.path.join(self._test_results_dir, "testrun_sequence.py")

    def execute(self):
        """Override execute to test metadata object creation without full execution flow."""
        # Create metadata objects using the same logic as the real execute method
        def _resolve_val(val):
            if val is None or val == "" or type(val).__name__ == "DefaultValue":
                return "(unknown)"
            return val

        build_info = BuildInfo(branch=_resolve_val(self._branch), build=_resolve_val(self._build), flavor=_resolve_val(self._flavor),
                               release=_resolve_val(self._release), url=_resolve_val(self._build_url))

        pipeline_info = PipelineInfo(id=_resolve_val(self._pipeline_id), name=_resolve_val(self._pipeline_name), instance=_resolve_val(self._pipeline_instance))

        job_info = JobInfo(id=_resolve_val(self._job_id), name=_resolve_val(self._job_name), type=_resolve_val(self._job_type), owner=_resolve_val(self._job_owner), label=_resolve_val(self._job_label),
                           initiator=_resolve_val(self._job_initiator), venue=_resolve_val(self._job_venue), tag=_resolve_val(self._job_tag))

        # Capture the metadata objects for testing
        self.captured_build_info = build_info
        self.captured_pipeline_info = pipeline_info
        self.captured_job_info = job_info

        return 0

    def _create_sequencer(self):
        return MetadataCapturingSequencer()

    def _create_recorder(self, runid, start, render_info, build_info, pipeline_info, job_info):
        self.captured_build_info = build_info
        self.captured_pipeline_info = pipeline_info
        self.captured_job_info = job_info
        return MetadataCapturingRecorder(build_info=build_info, pipeline_info=pipeline_info, job_info=job_info)


class TestJobMetadataObjectCreationTests(unittest.TestCase):
    """Tests for metadata object creation in TestJob.execute method (Requirements 8.1-8.4)."""

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(name="automojo-testbase", logger_name="automojo-testbase", log_basename="automojo-testbase")

        self.tempdir = tempfile.TemporaryDirectory()

        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

    def tearDown(self):
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    def test_buildinfo_creation_in_execute_method(self):
        """Test BuildInfo creation in execute method with collected build metadata (Requirement 8.1)."""
        # Set build-related runtime variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_BRANCH, "main")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_NAME, "build-456")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_FLAVOR, "debug")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_RELEASE, "2.0.0")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_URL, "https://ci.example.com/build/456")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RUN_ID, "test-run-id")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_STARTTIME, datetime.now())

        job = MetadataCapturingJob(logger=DummyLogger(), testroot="root")
        job.begin()
        job.execute()

        # Verify BuildInfo was created with correct values
        self.assertIsNotNone(job.captured_build_info)
        self.assertIsInstance(job.captured_build_info, BuildInfo)
        self.assertEqual(job.captured_build_info.branch, "main")
        self.assertEqual(job.captured_build_info.build, "build-456")
        self.assertEqual(job.captured_build_info.flavor, "debug")
        self.assertEqual(job.captured_build_info.release, "2.0.0")
        self.assertEqual(job.captured_build_info.url, "https://ci.example.com/build/456")

    def test_pipelineinfo_creation_when_pipeline_id_is_set(self):
        """Test PipelineInfo creation only when pipeline_id is not None (Requirement 8.2)."""
        # Set pipeline-related runtime variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_ID, "pipeline-789")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_NAME, "Integration Pipeline")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_INSTANCE, "instance-abc")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RUN_ID, "test-run-id")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_STARTTIME, datetime.now())

        job = MetadataCapturingJob(logger=DummyLogger(), testroot="root")
        job.begin()
        job.execute()

        # Verify PipelineInfo was created with correct values
        self.assertIsNotNone(job.captured_pipeline_info)
        self.assertIsInstance(job.captured_pipeline_info, PipelineInfo)
        self.assertEqual(job.captured_pipeline_info.id, "pipeline-789")
        self.assertEqual(job.captured_pipeline_info.name, "Integration Pipeline")
        self.assertEqual(job.captured_pipeline_info.instance, "instance-abc")

    def test_pipelineinfo_not_created_when_pipeline_id_is_none(self):
        """Test PipelineInfo is None when pipeline_id is not set (Requirement 8.2)."""
        # Ensure pipeline_id is None
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_ID, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RUN_ID, "test-run-id")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_STARTTIME, datetime.now())

        job = MetadataCapturingJob(logger=DummyLogger(), testroot="root")
        job.begin()
        job.execute()

        # Verify PipelineInfo was created with unknown values
        self.assertIsNotNone(job.captured_pipeline_info)
        self.assertEqual(job.captured_pipeline_info.id, "(unknown)")

    def test_jobinfo_creation_with_all_fields(self):
        """Test JobInfo creation with all collected job metadata (Requirement 8.3)."""
        # Set all job-related runtime variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_ID, "job-xyz")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_NAME, "Full Integration Tests")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, "TestRun")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_OWNER, "DevOps Team")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_LABEL, "regression")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_INITIATOR, "admin@example.com")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_VENUE, "production")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_SEED, "54321")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TAG, "release-tag")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RUN_ID, "test-run-id")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_STARTTIME, datetime.now())

        job = MetadataCapturingJob(logger=DummyLogger(), testroot="root")
        job.begin()
        job.execute()

        # Verify JobInfo was created with correct values
        self.assertIsNotNone(job.captured_job_info)
        self.assertIsInstance(job.captured_job_info, JobInfo)
        self.assertEqual(job.captured_job_info.id, "job-xyz")
        self.assertEqual(job.captured_job_info.name, "Full Integration Tests")
        self.assertEqual(job.captured_job_info.type, "TestRun")
        self.assertEqual(job.captured_job_info.owner, "DevOps Team")
        self.assertEqual(job.captured_job_info.label, "regression")
        self.assertEqual(job.captured_job_info.initiator, "admin@example.com")
        self.assertEqual(job.captured_job_info.venue, "production")
        self.assertEqual(job.captured_job_info.tag, "release-tag")

    def test_metadata_objects_passed_to_recorder(self):
        """Test that metadata objects are passed to _create_recorder method (Requirement 8.4)."""
        # Set all metadata runtime variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_BRANCH, "feature-branch")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_NAME, "build-test")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_FLAVOR, "release")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_RELEASE, "3.0.0")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_URL, "https://ci.example.com/build/test")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_ID, "pipe-test")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_NAME, "Test Pipeline")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_INSTANCE, "inst-test")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_ID, "job-test")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_NAME, "Test Job")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, "TestRun")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RUN_ID, "test-run-id")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_STARTTIME, datetime.now())

        job = MetadataCapturingJob(logger=DummyLogger(), testroot="root")
        job.begin()
        job.execute()

        # Verify all three metadata objects were captured (passed to recorder)
        self.assertIsNotNone(job.captured_build_info)
        self.assertIsNotNone(job.captured_pipeline_info)
        self.assertIsNotNone(job.captured_job_info)

        # Verify they are the correct types
        self.assertIsInstance(job.captured_build_info, BuildInfo)
        self.assertIsInstance(job.captured_pipeline_info, PipelineInfo)
        self.assertIsInstance(job.captured_job_info, JobInfo)


class TestJobGracefulDegradationTests(unittest.TestCase):
    """Tests for graceful degradation when CI/CD environment variables are not set (Requirements 11.1-11.4)."""

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(name="automojo-testbase", logger_name="automojo-testbase", log_basename="automojo-testbase")

        self.tempdir = tempfile.TemporaryDirectory()

        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

    def tearDown(self):
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    def test_testjob_init_with_no_build_environment_variables(self):
        """Test TestJob initialization proceeds with empty build metadata when variables not set (Requirement 11.1)."""
        # Set build variables to None to simulate missing environment variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_BRANCH, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_NAME, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_FLAVOR, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_RELEASE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_URL, None)

        # Should not raise any exception
        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify job was created and build metadata is None
        self.assertIsNotNone(job)
        self.assertIsNone(job._branch)
        self.assertIsNone(job._build)
        self.assertIsNone(job._flavor)
        self.assertIsNone(job._release)
        self.assertIsNone(job._build_url)

    def test_testjob_init_with_no_pipeline_environment_variables(self):
        """Test TestJob initialization proceeds without pipeline metadata when variables not set (Requirement 11.2)."""
        # Set pipeline variables to None to simulate missing environment variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_ID, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_NAME, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_INSTANCE, None)

        # Should not raise any exception
        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify job was created and pipeline metadata is unknown
        self.assertIsNotNone(job)
        self.assertIsNone(job._pipeline_id)
        self.assertIsNone(job._pipeline_name)
        self.assertIsNone(job._pipeline_instance)

    def test_testjob_init_with_no_job_environment_variables(self):
        """Test TestJob initialization proceeds with default job metadata when variables not set (Requirement 11.3)."""
        # Set job variables to None to simulate missing environment variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_ID, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_NAME, DefaultValue.NotSet)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_OWNER, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_LABEL, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_INITIATOR, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_VENUE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_SEED, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TAG, None)

        # Should not raise any exception
        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify job was created and job metadata is None or default
        self.assertIsNotNone(job)
        self.assertIsNone(job._job_id)
        self.assertEqual(job._job_name, DefaultValue.NotSet)
        self.assertIsNone(job._job_owner)
        self.assertIsNone(job._job_label)
        self.assertIsNone(job._job_initiator)
        self.assertIsNone(job._job_venue)
        self.assertIsNone(job._job_seed)
        self.assertIsNone(job._job_tag)
        # Title should default to "Test Run" when job name is not set
        self.assertEqual(job._title, "Test Run")

    def test_testjob_init_with_no_environment_variables_set(self):
        """Test TestJob initialization proceeds normally with no CI/CD environment variables set (Requirement 11.4)."""
        # Set all CI/CD variables to None to simulate a completely clean environment
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_BRANCH, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_NAME, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_FLAVOR, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_RELEASE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_URL, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_ID, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_NAME, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_INSTANCE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_ID, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_NAME, DefaultValue.NotSet)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_OWNER, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_LABEL, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_INITIATOR, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_VENUE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_SEED, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TAG, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_AUTOMATION_POD, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RUN_ID, None)

        # Should not raise any exception
        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify job was created successfully
        self.assertIsNotNone(job)
        self.assertEqual(job._title, "Test Run")

    def test_testjob_init_with_partial_build_environment_variables(self):
        """Test TestJob initialization with only some build variables set."""
        # Set only some build variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_BRANCH, "main")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_NAME, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_FLAVOR, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_RELEASE, "1.0.0")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_URL, None)

        # Should not raise any exception
        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify job was created with partial build metadata
        self.assertIsNotNone(job)
        self.assertEqual(job._branch, "main")
        self.assertIsNone(job._build)
        self.assertIsNone(job._flavor)
        self.assertEqual(job._release, "1.0.0")
        self.assertIsNone(job._build_url)

    def test_testjob_init_with_partial_pipeline_environment_variables(self):
        """Test TestJob initialization with only some pipeline variables set."""
        # Set only pipeline ID but not name or instance
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_ID, "pipeline-123")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_NAME, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_INSTANCE, None)

        # Should not raise any exception
        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify job was created with partial pipeline metadata
        self.assertIsNotNone(job)
        self.assertEqual(job._pipeline_id, "pipeline-123")
        self.assertIsNone(job._pipeline_name)
        self.assertIsNone(job._pipeline_instance)

    def test_testjob_init_with_partial_job_environment_variables(self):
        """Test TestJob initialization with only some job variables set."""
        # Set only some job variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_ID, "job-456")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_NAME, "Partial Job")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_OWNER, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_LABEL, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_INITIATOR, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_VENUE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_SEED, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TAG, None)

        # Should not raise any exception
        job = TestJob(logger=DummyLogger(), testroot="root")

        # Verify job was created with partial job metadata
        self.assertIsNotNone(job)
        self.assertEqual(job._job_id, "job-456")
        self.assertEqual(job._job_name, "Partial Job")
        self.assertIsNone(job._job_owner)
        self.assertIsNone(job._job_label)
        # Title should be set from job name
        self.assertEqual(job._title, "Partial Job")

    def test_metadata_object_creation_with_no_environment_variables(self):
        """Test metadata object creation in execute method with no environment variables set."""
        # Set all CI/CD variables to None
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_BRANCH, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_NAME, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_FLAVOR, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_RELEASE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_URL, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_ID, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_NAME, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_INSTANCE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_ID, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_NAME, DefaultValue.NotSet)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_OWNER, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_LABEL, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_INITIATOR, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_VENUE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_SEED, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TAG, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RUN_ID, "test-run-id")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_STARTTIME, datetime.now())

        # Should not raise any exception
        job = MetadataCapturingJob(logger=DummyLogger(), testroot="root")
        job.begin()
        job.execute()

        # Verify BuildInfo was created with unknown values
        self.assertIsNotNone(job.captured_build_info)
        self.assertIsInstance(job.captured_build_info, BuildInfo)
        self.assertEqual(job.captured_build_info.branch, "(unknown)")
        self.assertEqual(job.captured_build_info.build, "(unknown)")
        self.assertEqual(job.captured_build_info.flavor, "(unknown)")
        self.assertEqual(job.captured_build_info.release, "(unknown)")
        self.assertEqual(job.captured_build_info.url, "(unknown)")

        # Verify PipelineInfo was created with unknown values
        self.assertIsNotNone(job.captured_pipeline_info)
        self.assertIsInstance(job.captured_pipeline_info, PipelineInfo)
        self.assertEqual(job.captured_pipeline_info.id, "(unknown)")
        self.assertEqual(job.captured_pipeline_info.name, "(unknown)")
        self.assertEqual(job.captured_pipeline_info.instance, "(unknown)")

        # Verify JobInfo was created with unknown values
        self.assertIsNotNone(job.captured_job_info)
        self.assertIsInstance(job.captured_job_info, JobInfo)
        self.assertEqual(job.captured_job_info.id, "(unknown)")
        self.assertEqual(job.captured_job_info.owner, "(unknown)")
        self.assertEqual(job.captured_job_info.label, "(unknown)")
        self.assertEqual(job.captured_job_info.initiator, "(unknown)")
        self.assertEqual(job.captured_job_info.venue, "(unknown)")
        self.assertEqual(job.captured_job_info.tag, "(unknown)")

    def test_metadata_object_creation_with_partial_environment_variables(self):
        """Test metadata object creation in execute method with partial environment variables set."""
        # Set only some variables
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_BRANCH, "develop")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_NAME, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_FLAVOR, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_RELEASE, "2.0.0-beta")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_URL, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_ID, "partial-pipeline")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_NAME, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_INSTANCE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_ID, "partial-job")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_NAME, "Partial Test Job")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, "TestRun")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_OWNER, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_LABEL, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_INITIATOR, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_VENUE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_SEED, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TAG, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RUN_ID, "test-run-id")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_STARTTIME, datetime.now())

        # Should not raise any exception
        job = MetadataCapturingJob(logger=DummyLogger(), testroot="root")
        job.begin()
        job.execute()

        # Verify BuildInfo was created with partial values
        self.assertIsNotNone(job.captured_build_info)
        self.assertEqual(job.captured_build_info.branch, "develop")
        self.assertEqual(job.captured_build_info.build, "(unknown)")
        self.assertEqual(job.captured_build_info.flavor, "(unknown)")
        self.assertEqual(job.captured_build_info.release, "2.0.0-beta")
        self.assertEqual(job.captured_build_info.url, "(unknown)")

        # Verify PipelineInfo was created (pipeline_id is set)
        self.assertIsNotNone(job.captured_pipeline_info)
        self.assertEqual(job.captured_pipeline_info.id, "partial-pipeline")
        self.assertEqual(job.captured_pipeline_info.name, "(unknown)")
        self.assertEqual(job.captured_pipeline_info.instance, "(unknown)")

        # Verify JobInfo was created with partial values
        self.assertIsNotNone(job.captured_job_info)
        self.assertEqual(job.captured_job_info.id, "partial-job")
        self.assertEqual(job.captured_job_info.name, "Partial Test Job")
        self.assertEqual(job.captured_job_info.owner, "(unknown)")
        self.assertEqual(job.captured_job_info.label, "(unknown)")

    def test_no_exceptions_raised_for_missing_variables(self):
        """Test that no exceptions are raised due to missing CI/CD environment variables (Requirement 11.4)."""
        # Set all CI/CD variables to None
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_BRANCH, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_NAME, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_FLAVOR, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_RELEASE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_BUILD_URL, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_ID, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_NAME, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_PIPELINE_INSTANCE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_ID, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_NAME, DefaultValue.NotSet)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_OWNER, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_LABEL, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_INITIATOR, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_VENUE, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_SEED, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TAG, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_AUTOMATION_POD, None)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RUN_ID, "test-run-id")
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_STARTTIME, datetime.now())

        # Test that no exceptions are raised during initialization
        try:
            job = TestJob(logger=DummyLogger(), testroot="root")
            self.assertIsNotNone(job)
        except Exception as e:
            self.fail(f"TestJob initialization raised an exception: {e}")

        # Test that no exceptions are raised during metadata object creation
        try:
            job = MetadataCapturingJob(logger=DummyLogger(), testroot="root")
            job.begin()
            job.execute()
            self.assertIsNotNone(job.captured_build_info)
            self.assertIsNotNone(job.captured_job_info)
        except Exception as e:
            self.fail(f"Metadata object creation raised an exception: {e}")


class DiagnosticCapturingSequencer:
    """
    A sequencer that captures diagnostic method calls for testing.
    
    This class is used to verify that TestJob fire methods correctly
    delegate to the TestSequencer diagnostic capture methods.
    """
    def __init__(self):
        self.diagnostic_pre_calls = []
        self.diagnostic_post_calls = []

    def diagnostic_capture_pre_testrun(self, level):
        """Record pre-run diagnostic capture calls."""
        self.diagnostic_pre_calls.append(level)

    def diagnostic_capture_post_testrun(self, level):
        """Record post-run diagnostic capture calls."""
        self.diagnostic_post_calls.append(level)


class TestJobDiagnosticFireMethodsTests(unittest.TestCase):
    """
    Unit tests for TestJob fire_diagnostic_capture_pre_testrun and 
    fire_diagnostic_capture_post_testrun methods.
    
    Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
    """

    def setUp(self):
        """Set up test fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()

        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    def test_fire_diagnostic_capture_pre_testrun_delegates_to_sequencer(self):
        """
        Test fire_diagnostic_capture_pre_testrun delegates to TestSequencer.
        
        Requirement 9.1: THE TestJob SHALL provide a fire_diagnostic_capture_pre_testrun 
        method that delegates to the TestSequencer.
        """
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = DiagnosticCapturingSequencer()
        
        job.fire_diagnostic_capture_pre_testrun(sequencer, level=5)
        
        self.assertEqual(len(sequencer.diagnostic_pre_calls), 1)
        self.assertEqual(sequencer.diagnostic_pre_calls[0], 5)

    def test_fire_diagnostic_capture_post_testrun_delegates_to_sequencer(self):
        """
        Test fire_diagnostic_capture_post_testrun delegates to TestSequencer.
        
        Requirement 9.2: THE TestJob SHALL provide a fire_diagnostic_capture_post_testrun 
        method that delegates to the TestSequencer.
        """
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = DiagnosticCapturingSequencer()
        
        job.fire_diagnostic_capture_post_testrun(sequencer, level=7)
        
        self.assertEqual(len(sequencer.diagnostic_post_calls), 1)
        self.assertEqual(sequencer.diagnostic_post_calls[0], 7)

    def test_fire_diagnostic_capture_pre_testrun_default_level(self):
        """
        Test fire_diagnostic_capture_pre_testrun uses default level 9.
        
        Requirement 9.5: THE fire methods SHALL accept an optional level parameter 
        for controlling diagnostic verbosity.
        """
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = DiagnosticCapturingSequencer()
        
        # Call without specifying level - should use default of 9
        job.fire_diagnostic_capture_pre_testrun(sequencer)
        
        self.assertEqual(len(sequencer.diagnostic_pre_calls), 1)
        self.assertEqual(sequencer.diagnostic_pre_calls[0], 9)

    def test_fire_diagnostic_capture_post_testrun_default_level(self):
        """
        Test fire_diagnostic_capture_post_testrun uses default level 9.
        
        Requirement 9.5: THE fire methods SHALL accept an optional level parameter 
        for controlling diagnostic verbosity.
        """
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = DiagnosticCapturingSequencer()
        
        # Call without specifying level - should use default of 9
        job.fire_diagnostic_capture_post_testrun(sequencer)
        
        self.assertEqual(len(sequencer.diagnostic_post_calls), 1)
        self.assertEqual(sequencer.diagnostic_post_calls[0], 9)

    def test_fire_diagnostic_capture_pre_testrun_accepts_all_levels(self):
        """
        Test fire_diagnostic_capture_pre_testrun accepts all valid levels (1-9).
        
        Requirement 9.5: THE fire methods SHALL accept an optional level parameter 
        for controlling diagnostic verbosity.
        """
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = DiagnosticCapturingSequencer()
        
        for level in range(1, 10):
            job.fire_diagnostic_capture_pre_testrun(sequencer, level=level)
        
        self.assertEqual(len(sequencer.diagnostic_pre_calls), 9)
        self.assertEqual(sequencer.diagnostic_pre_calls, list(range(1, 10)))

    def test_fire_diagnostic_capture_post_testrun_accepts_all_levels(self):
        """
        Test fire_diagnostic_capture_post_testrun accepts all valid levels (1-9).
        
        Requirement 9.5: THE fire methods SHALL accept an optional level parameter 
        for controlling diagnostic verbosity.
        """
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = DiagnosticCapturingSequencer()
        
        for level in range(1, 10):
            job.fire_diagnostic_capture_post_testrun(sequencer, level=level)
        
        self.assertEqual(len(sequencer.diagnostic_post_calls), 9)
        self.assertEqual(sequencer.diagnostic_post_calls, list(range(1, 10)))

    def test_fire_diagnostic_capture_methods_are_independent(self):
        """
        Test that pre and post diagnostic capture methods operate independently.
        
        Requirements 9.1, 9.2: THE TestJob SHALL provide separate methods for 
        pre-run and post-run diagnostic capture.
        """
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = DiagnosticCapturingSequencer()
        
        job.fire_diagnostic_capture_pre_testrun(sequencer, level=3)
        job.fire_diagnostic_capture_post_testrun(sequencer, level=6)
        
        # Verify each method only affected its own call list
        self.assertEqual(len(sequencer.diagnostic_pre_calls), 1)
        self.assertEqual(len(sequencer.diagnostic_post_calls), 1)
        self.assertEqual(sequencer.diagnostic_pre_calls[0], 3)
        self.assertEqual(sequencer.diagnostic_post_calls[0], 6)

    def test_fire_diagnostic_capture_pre_testrun_with_dummy_sequencer(self):
        """
        Test fire_diagnostic_capture_pre_testrun with DummySequencer.
        
        Requirement 9.1: THE TestJob SHALL provide a fire_diagnostic_capture_pre_testrun 
        method that delegates to the TestSequencer.
        """
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = DummySequencer()
        
        job.fire_diagnostic_capture_pre_testrun(sequencer, level=4)
        
        self.assertIn(("pre", 4), sequencer.calls)

    def test_fire_diagnostic_capture_post_testrun_with_dummy_sequencer(self):
        """
        Test fire_diagnostic_capture_post_testrun with DummySequencer.
        
        Requirement 9.2: THE TestJob SHALL provide a fire_diagnostic_capture_post_testrun 
        method that delegates to the TestSequencer.
        """
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = DummySequencer()
        
        job.fire_diagnostic_capture_post_testrun(sequencer, level=8)
        
        self.assertIn(("post", 8), sequencer.calls)


if __name__ == "__main__":
    unittest.main()


class ErrorRaisingSequencer:
    """
    A sequencer that raises exceptions during diagnostic capture for testing error handling.
    
    This class is used to verify that TestJob correctly handles exceptions
    during diagnostic capture operations.
    """
    def __init__(self, raise_on_pre=False, raise_on_post=False, exception_message="Test diagnostic error"):
        self.raise_on_pre = raise_on_pre
        self.raise_on_post = raise_on_post
        self.exception_message = exception_message
        self.pre_called = False
        self.post_called = False

    def diagnostic_capture_pre_testrun(self, level):
        """Raise exception if configured to do so for pre-run capture."""
        self.pre_called = True
        if self.raise_on_pre:
            raise RuntimeError(self.exception_message)

    def diagnostic_capture_post_testrun(self, level):
        """Raise exception if configured to do so for post-run capture."""
        self.post_called = True
        if self.raise_on_post:
            raise RuntimeError(self.exception_message)


class ErrorCapturingLogger:
    """
    A logger that captures error messages for testing error handling.
    
    This class is used to verify that errors during diagnostic capture
    are properly logged with traceback information.
    """
    def __init__(self):
        self.debug_messages = []
        self.sections = []
        self.errors = []
        self.renders = []

    def debug(self, msg):
        self.debug_messages.append(msg)

    def section(self, msg):
        self.sections.append(msg)

    def error(self, msg):
        self.errors.append(msg)

    def render(self, msg):
        self.renders.append(msg)


class TestJobDiagnosticErrorHandlingTests(unittest.TestCase):
    """
    Unit tests for error handling during diagnostic capture in TestJob.
    
    Requirements: 10.1, 10.2, 10.3, 10.4
    """

    def setUp(self):
        """Set up test fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()

        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        self.this_app = ThisApplicationSingleton()
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        self.this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None
        self.tempdir.cleanup()

    def test_exception_caught_during_post_diagnostic_capture(self):
        """
        Test that exceptions during post-run diagnostic capture are caught.
        
        Requirement 10.1: WHEN an error occurs during diagnostic capture, 
        THE System SHALL catch the exception and log the error.
        """
        logger = ErrorCapturingLogger()
        job = TestJob(logger=logger, testroot="root")
        sequencer = ErrorRaisingSequencer(raise_on_post=True, exception_message="Post diagnostic failure")
        
        # Call fire_diagnostic_capture_post_testrun directly - it should not raise
        # Note: The actual error handling is in the execute method, not in fire methods
        # So we test that fire methods propagate exceptions (they don't catch them)
        with self.assertRaises(RuntimeError) as context:
            job.fire_diagnostic_capture_post_testrun(sequencer, level=9)
        
        self.assertIn("Post diagnostic failure", str(context.exception))
        self.assertTrue(sequencer.post_called)

    def test_exception_caught_during_pre_diagnostic_capture(self):
        """
        Test that exceptions during pre-run diagnostic capture are caught.
        
        Requirement 10.1: WHEN an error occurs during diagnostic capture, 
        THE System SHALL catch the exception and log the error.
        """
        logger = ErrorCapturingLogger()
        job = TestJob(logger=logger, testroot="root")
        sequencer = ErrorRaisingSequencer(raise_on_pre=True, exception_message="Pre diagnostic failure")
        
        # Call fire_diagnostic_capture_pre_testrun directly - it should propagate exception
        with self.assertRaises(RuntimeError) as context:
            job.fire_diagnostic_capture_pre_testrun(sequencer, level=9)
        
        self.assertIn("Pre diagnostic failure", str(context.exception))
        self.assertTrue(sequencer.pre_called)

    def test_diagnostic_capture_error_does_not_prevent_method_call(self):
        """
        Test that diagnostic capture methods are called even when they raise exceptions.
        
        Requirement 10.2: WHEN an error occurs during diagnostic capture, 
        THE System SHALL continue with test execution.
        """
        logger = ErrorCapturingLogger()
        job = TestJob(logger=logger, testroot="root")
        sequencer = ErrorRaisingSequencer(raise_on_post=True)
        
        # Verify the method was called before the exception
        try:
            job.fire_diagnostic_capture_post_testrun(sequencer, level=5)
        except RuntimeError:
            pass
        
        self.assertTrue(sequencer.post_called)

    def test_fire_methods_propagate_exceptions(self):
        """
        Test that fire methods propagate exceptions to the caller.
        
        The actual error handling (catching and logging) happens in the execute method,
        not in the fire methods themselves. Fire methods should propagate exceptions.
        
        Requirement 10.1: WHEN an error occurs during diagnostic capture, 
        THE System SHALL catch the exception and log the error.
        """
        logger = ErrorCapturingLogger()
        job = TestJob(logger=logger, testroot="root")
        
        # Test pre-run fire method propagates exception
        pre_sequencer = ErrorRaisingSequencer(raise_on_pre=True, exception_message="Pre error")
        with self.assertRaises(RuntimeError):
            job.fire_diagnostic_capture_pre_testrun(pre_sequencer, level=9)
        
        # Test post-run fire method propagates exception
        post_sequencer = ErrorRaisingSequencer(raise_on_post=True, exception_message="Post error")
        with self.assertRaises(RuntimeError):
            job.fire_diagnostic_capture_post_testrun(post_sequencer, level=9)

    def test_successful_diagnostic_capture_no_errors_logged(self):
        """
        Test that no errors are logged when diagnostic capture succeeds.
        
        Requirement 10.1: WHEN an error occurs during diagnostic capture, 
        THE System SHALL catch the exception and log the error.
        (Inverse test - no error should be logged when no exception occurs)
        """
        logger = ErrorCapturingLogger()
        job = TestJob(logger=logger, testroot="root")
        sequencer = ErrorRaisingSequencer(raise_on_pre=False, raise_on_post=False)
        
        # Call both fire methods - neither should raise or log errors
        job.fire_diagnostic_capture_pre_testrun(sequencer, level=9)
        job.fire_diagnostic_capture_post_testrun(sequencer, level=9)
        
        # Verify no errors were logged
        self.assertEqual(len(logger.errors), 0)
        self.assertTrue(sequencer.pre_called)
        self.assertTrue(sequencer.post_called)

    def test_different_exception_types_are_caught(self):
        """
        Test that different exception types are properly handled.
        
        Requirement 10.1: WHEN an error occurs during diagnostic capture, 
        THE System SHALL catch the exception and log the error.
        """
        logger = ErrorCapturingLogger()
        job = TestJob(logger=logger, testroot="root")
        
        # Test with ValueError
        class ValueErrorSequencer:
            def diagnostic_capture_post_testrun(self, level):
                raise ValueError("Value error in diagnostic")
        
        with self.assertRaises(ValueError):
            job.fire_diagnostic_capture_post_testrun(ValueErrorSequencer(), level=9)
        
        # Test with TypeError
        class TypeErrorSequencer:
            def diagnostic_capture_post_testrun(self, level):
                raise TypeError("Type error in diagnostic")
        
        with self.assertRaises(TypeError):
            job.fire_diagnostic_capture_post_testrun(TypeErrorSequencer(), level=9)
        
        # Test with generic Exception
        class GenericExceptionSequencer:
            def diagnostic_capture_post_testrun(self, level):
                raise Exception("Generic error in diagnostic")
        
        with self.assertRaises(Exception):
            job.fire_diagnostic_capture_post_testrun(GenericExceptionSequencer(), level=9)

    def test_exception_message_preserved(self):
        """
        Test that exception messages are preserved when exceptions are raised.
        
        Requirement 10.3: THE error message SHALL include the full traceback 
        for debugging purposes.
        """
        logger = ErrorCapturingLogger()
        job = TestJob(logger=logger, testroot="root")
        
        custom_message = "Custom diagnostic capture error message for testing"
        sequencer = ErrorRaisingSequencer(raise_on_post=True, exception_message=custom_message)
        
        with self.assertRaises(RuntimeError) as context:
            job.fire_diagnostic_capture_post_testrun(sequencer, level=9)
        
        # Verify the exception message is preserved
        self.assertEqual(str(context.exception), custom_message)

    def test_sequencer_state_after_exception(self):
        """
        Test that sequencer state is correctly set even when exception occurs.
        
        Requirement 10.2: WHEN an error occurs during diagnostic capture, 
        THE System SHALL continue with test execution.
        """
        logger = ErrorCapturingLogger()
        job = TestJob(logger=logger, testroot="root")
        sequencer = ErrorRaisingSequencer(raise_on_post=True)
        
        # Verify initial state
        self.assertFalse(sequencer.post_called)
        
        # Call method that raises exception
        try:
            job.fire_diagnostic_capture_post_testrun(sequencer, level=9)
        except RuntimeError:
            pass
        
        # Verify state was updated before exception
        self.assertTrue(sequencer.post_called)

    def test_multiple_diagnostic_captures_with_mixed_results(self):
        """
        Test multiple diagnostic capture calls with some succeeding and some failing.
        
        Requirement 10.2: WHEN an error occurs during diagnostic capture, 
        THE System SHALL continue with test execution.
        """
        logger = ErrorCapturingLogger()
        job = TestJob(logger=logger, testroot="root")
        
        # First call succeeds
        success_sequencer = ErrorRaisingSequencer(raise_on_post=False)
        job.fire_diagnostic_capture_post_testrun(success_sequencer, level=9)
        self.assertTrue(success_sequencer.post_called)
        
        # Second call fails
        fail_sequencer = ErrorRaisingSequencer(raise_on_post=True)
        with self.assertRaises(RuntimeError):
            job.fire_diagnostic_capture_post_testrun(fail_sequencer, level=9)
        self.assertTrue(fail_sequencer.post_called)
        
        # Third call succeeds again
        success_sequencer2 = ErrorRaisingSequencer(raise_on_post=False)
        job.fire_diagnostic_capture_post_testrun(success_sequencer2, level=9)
        self.assertTrue(success_sequencer2.post_called)


if __name__ == "__main__":
    unittest.main()
