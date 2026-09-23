"""
    Unit tests for the STANDALONE :class:`ccai.testbase.testjob.TestJob` contract.

    After the testbase / integration-runtime refactor, plain ``TestJob`` is decoupled from
    ``codecraftai-runtime`` / ``codecraftai-this-app``: it sources run metadata from
    :class:`StandaloneRunMetadata` (an :class:`IRunMetadata`) and output locations from
    :class:`SimpleOutputContext` (an :class:`IOutputContext`), and records results via
    :class:`StdoutResultRecorder`. The env-sourced knobs it reads (e.g. ``AM_TESTRUN_TIMEOUT``)
    are read directly from ``os.environ`` through :mod:`ccai.testbase.environment`.

    NOTE: Tests of the INTEGRATION contract — metadata sourced from ``RuntimeVariables`` and stored
    on the job, results written under the activated presence folder, and HTML rendering — now belong
    to ``codecraftai-integration-runtime``'s ``IntegratedTestJob`` suite, NOT here. The legacy
    requirement coverage (specs 8.x / 11.x) relocates with that class. See
    ``REFACTOR-TESTBASE-INTEGRATION-RUNTIME-ROADMAP.md`` §11.
"""

import os
import tempfile
import time
import unittest
from datetime import datetime

from ccai.testbase.testjob import TestJob, DefaultTestJob
from ccai.testbase.output.outputcontext import IOutputContext, SimpleOutputContext
from ccai.testbase.output.runmetadata import IRunMetadata, StandaloneRunMetadata
from ccai.testbase.results.model.buildinfo import BuildInfo
from ccai.testbase.results.model.pipelineinfo import PipelineInfo
from ccai.testbase.results.model.renderinfo import RenderInfo
from ccai.testbase.results.model.jobinfo import JobInfo
from ccai.testbase.results.recorders.stdoutresultrecorder import StdoutResultRecorder
from ccai.testbase.sequencing.testsequencer import TestSequencer
from ccai.testbase.errors.testruntimeouterror import TestRunTimeoutError


class DummyLogger:
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


class TestJobLifecycleTests(unittest.TestCase):
    """Lifecycle, sequencer/recorder creation, and query behaviour of the standalone TestJob."""

    def setUp(self):
        # Keep standalone output artefacts inside an isolated temp directory.
        self.tempdir = tempfile.TemporaryDirectory()
        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

    def tearDown(self):
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir
        self.tempdir.cleanup()

    def test_context_manager_calls_begin_and_finalize(self):
        job = DummyJob()
        with job as j:
            self.assertIs(j, job)
            self.assertTrue(job.begin_called)
        self.assertTrue(job.finalize_called)

    def test_internal_sequencer_creation(self):
        job = TestJob(logger=DummyLogger(), testroot="troot")
        seq = job._create_sequencer()
        self.assertIsInstance(seq, TestSequencer)
        self.assertEqual(seq._root, "troot")
        self.assertIsNone(seq._includes)
        # The standalone output context is threaded into the sequencer.
        self.assertIsInstance(seq.output_context, IOutputContext)

    def test_default_recorder_is_stdout_recorder(self):
        job = TestJob(logger=DummyLogger(), testroot="troot")
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
            self.assertIsInstance(rec, StdoutResultRecorder)
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

        self.assertIn("env", seq.calls)
        self.assertIn("framework", seq.calls)
        self.assertIn(("pre", 1), seq.calls)
        self.assertIn(("post", 2), seq.calls)

    def test_no_landscape_lifecycle_hooks_on_standalone_job(self):
        # The standalone TestJob deliberately has NO landscape lifecycle hooks:
        # fire_activate_* and fire_establish_presence belong to the
        # landscaping-tier LandscapeTestJob.  Pin their absence so they are not
        # quietly reintroduced here.
        for hook in ("fire_activate_configuration", "fire_activate_integration",
                     "fire_activate_operations", "fire_establish_presence"):
            self.assertFalse(hasattr(TestJob, hook),
                             "'{}' must not exist on the standalone TestJob.".format(hook))


class TestJobStandaloneMetadataTests(unittest.TestCase):
    """
        The standalone TestJob contract: run metadata comes from a default
        :class:`StandaloneRunMetadata`, not from ``RuntimeVariables``. CI/build/pipeline/job
        fields default to ``(unknown)``; the run id is auto-generated; the title comes from the
        job's ``name`` class attribute.
    """

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

    def tearDown(self):
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir
        self.tempdir.cleanup()

    def test_create_run_metadata_returns_standalone_default(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        metadata = job._create_run_metadata()
        self.assertIsInstance(metadata, IRunMetadata)
        self.assertIsInstance(metadata, StandaloneRunMetadata)

    def test_create_output_context_returns_simple_default(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        context = job._create_output_context()
        self.assertIsInstance(context, IOutputContext)
        self.assertIsInstance(context, SimpleOutputContext)

    def test_run_id_is_auto_generated(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        self.assertIsNotNone(job._run_id)
        self.assertGreater(len(job._run_id), 0)

    def test_run_id_read_from_environment_when_set(self):
        prev = os.environ.get("AM_RUN_ID", None)
        os.environ["AM_RUN_ID"] = "env-run-id"
        try:
            job = TestJob(logger=DummyLogger(), testroot="root")
            self.assertEqual(job._run_id, "env-run-id")
        finally:
            if prev is None:
                os.environ.pop("AM_RUN_ID", None)
            else:
                os.environ["AM_RUN_ID"] = prev

    def test_title_defaults_to_test_run_for_unnamed_job(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        self.assertEqual(job._title, "Test Run")

    def test_title_taken_from_job_name_class_attribute(self):
        job = DefaultTestJob(logger=DummyLogger(), testroot="root")
        self.assertEqual(job._title, "Test Job")

    def test_legacy_runtime_metadata_attributes_are_not_present(self):
        # The old RuntimeVariables-sourced instance attributes are intentionally gone; that
        # metadata now lives behind the IRunMetadata seam (and the integration runtime supplies
        # the RuntimeVariables-backed values).
        job = TestJob(logger=DummyLogger(), testroot="root")
        for legacy_attr in ("_branch", "_build", "_flavor", "_release", "_build_url",
                            "_pipeline_id", "_pipeline_name", "_pipeline_instance",
                            "_job_id", "_job_name", "_job_owner", "_job_type"):
            self.assertFalse(hasattr(job, legacy_attr),
                             "Unexpected legacy metadata attribute: {}".format(legacy_attr))

    def test_standalone_metadata_uses_unknown_placeholders(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        metadata = job._create_run_metadata()

        build_info = metadata.build_info()
        self.assertEqual(build_info.branch, "(unknown)")
        self.assertEqual(build_info.build, "(unknown)")
        self.assertEqual(build_info.flavor, "(unknown)")
        self.assertEqual(build_info.release, "(unknown)")
        self.assertEqual(build_info.url, "(unknown)")

        pipeline_info = metadata.pipeline_info()
        self.assertEqual(pipeline_info.id, "(unknown)")
        self.assertEqual(pipeline_info.name, "(unknown)")
        self.assertEqual(pipeline_info.instance, "(unknown)")

        job_info = metadata.job_info()
        self.assertEqual(job_info.id, "(unknown)")
        self.assertEqual(job_info.owner, "(unknown)")
        self.assertEqual(job_info.venue, "(unknown)")
        # The seed is always a concrete value (auto-generated) for reproducible property testing.
        self.assertIsNotNone(job_info.seed)
        self.assertGreater(len(job_info.seed), 0)

    def test_apod_defaults_to_none(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        self.assertIsNone(job._apod)

    def test_job_seed_is_stable_within_a_job(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        self.assertEqual(job.job_seed, job.job_seed)


class DiagnosticCapturingSequencer:
    """A sequencer that captures diagnostic method calls for testing fire-method delegation."""

    def __init__(self):
        self.diagnostic_pre_calls = []
        self.diagnostic_post_calls = []

    def diagnostic_capture_pre_testrun(self, level):
        self.diagnostic_pre_calls.append(level)

    def diagnostic_capture_post_testrun(self, level):
        self.diagnostic_post_calls.append(level)


class TestJobDiagnosticFireMethodsTests(unittest.TestCase):
    """fire_diagnostic_capture_pre/post_testrun delegate to the sequencer (Requirements 9.x)."""

    def test_fire_pre_testrun_delegates_to_sequencer(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = DiagnosticCapturingSequencer()
        job.fire_diagnostic_capture_pre_testrun(sequencer, level=5)
        self.assertEqual(sequencer.diagnostic_pre_calls, [5])

    def test_fire_post_testrun_delegates_to_sequencer(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = DiagnosticCapturingSequencer()
        job.fire_diagnostic_capture_post_testrun(sequencer, level=7)
        self.assertEqual(sequencer.diagnostic_post_calls, [7])

    def test_fire_pre_testrun_default_level(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = DiagnosticCapturingSequencer()
        job.fire_diagnostic_capture_pre_testrun(sequencer)
        self.assertEqual(sequencer.diagnostic_pre_calls, [9])

    def test_fire_post_testrun_default_level(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = DiagnosticCapturingSequencer()
        job.fire_diagnostic_capture_post_testrun(sequencer)
        self.assertEqual(sequencer.diagnostic_post_calls, [9])

    def test_fire_pre_testrun_accepts_all_levels(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = DiagnosticCapturingSequencer()
        for level in range(1, 10):
            job.fire_diagnostic_capture_pre_testrun(sequencer, level=level)
        self.assertEqual(sequencer.diagnostic_pre_calls, list(range(1, 10)))

    def test_fire_methods_are_independent(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = DiagnosticCapturingSequencer()
        job.fire_diagnostic_capture_pre_testrun(sequencer, level=3)
        job.fire_diagnostic_capture_post_testrun(sequencer, level=6)
        self.assertEqual(sequencer.diagnostic_pre_calls, [3])
        self.assertEqual(sequencer.diagnostic_post_calls, [6])


class ErrorRaisingSequencer:
    """A sequencer that raises during diagnostic capture, for testing error propagation."""

    def __init__(self, raise_on_pre=False, raise_on_post=False, exception_message="Test diagnostic error"):
        self.raise_on_pre = raise_on_pre
        self.raise_on_post = raise_on_post
        self.exception_message = exception_message
        self.pre_called = False
        self.post_called = False

    def diagnostic_capture_pre_testrun(self, level):
        self.pre_called = True
        if self.raise_on_pre:
            raise RuntimeError(self.exception_message)

    def diagnostic_capture_post_testrun(self, level):
        self.post_called = True
        if self.raise_on_post:
            raise RuntimeError(self.exception_message)


class TestJobDiagnosticErrorHandlingTests(unittest.TestCase):
    """The fire_* methods propagate exceptions (Requirements 10.x); execute() is what swallows them."""

    def test_pre_capture_exception_propagates(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = ErrorRaisingSequencer(raise_on_pre=True, exception_message="Pre diagnostic failure")
        with self.assertRaises(RuntimeError) as context:
            job.fire_diagnostic_capture_pre_testrun(sequencer, level=9)
        self.assertIn("Pre diagnostic failure", str(context.exception))
        self.assertTrue(sequencer.pre_called)

    def test_post_capture_exception_propagates(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = ErrorRaisingSequencer(raise_on_post=True, exception_message="Post diagnostic failure")
        with self.assertRaises(RuntimeError) as context:
            job.fire_diagnostic_capture_post_testrun(sequencer, level=9)
        self.assertIn("Post diagnostic failure", str(context.exception))
        self.assertTrue(sequencer.post_called)

    def test_method_called_before_exception(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        sequencer = ErrorRaisingSequencer(raise_on_post=True)
        try:
            job.fire_diagnostic_capture_post_testrun(sequencer, level=5)
        except RuntimeError:
            # Expected: the sequencer raises; this test only checks the method was called first.
            pass
        self.assertTrue(sequencer.post_called)

    def test_successful_capture_logs_no_errors(self):
        logger = DummyLogger()
        job = TestJob(logger=logger, testroot="root")
        sequencer = ErrorRaisingSequencer(raise_on_pre=False, raise_on_post=False)
        job.fire_diagnostic_capture_pre_testrun(sequencer, level=9)
        job.fire_diagnostic_capture_post_testrun(sequencer, level=9)
        self.assertEqual(len(logger.errors), 0)
        self.assertTrue(sequencer.pre_called)
        self.assertTrue(sequencer.post_called)

    def test_exception_message_preserved(self):
        job = TestJob(logger=DummyLogger(), testroot="root")
        custom_message = "Custom diagnostic capture error message for testing"
        sequencer = ErrorRaisingSequencer(raise_on_post=True, exception_message=custom_message)
        with self.assertRaises(RuntimeError) as context:
            job.fire_diagnostic_capture_post_testrun(sequencer, level=9)
        self.assertEqual(str(context.exception), custom_message)


class SlowSequencer:
    """A sequencer that sleeps during execute_tests to simulate a long-running test run."""

    def __init__(self, sleep_seconds=5):
        self.import_errors = []
        self._sleep_seconds = sleep_seconds
        self.execute_tests_called = False

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
        self.execute_tests_called = True
        time.sleep(self._sleep_seconds)

    def diagnostic_capture_post_testrun(self, level):
        pass

    def diagnostic_capture_pre_testrun(self, level):
        pass


class TimeoutTestRecorder:
    """A minimal recorder for timeout testing."""

    def __init__(self, job):
        self._job = job
        self.summary = {"result": "PASSED"}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def finalize(self):
        self._job.recorder_finalized = True

    def format_lines(self):
        return []


class TimeoutTestJob(TestJob):
    """A TestJob subclass that exercises the timeout logic without the full execution flow."""

    def __init__(self, logger, testroot, slow_sequencer):
        super().__init__(logger=logger, testroot=testroot)
        self._slow_sequencer = slow_sequencer
        self.recorder_finalized = False

    def begin(self):
        # Override begin to avoid output-context path resolution for this focused unit test.
        self._starttime = datetime.now()
        self._test_results_dir = tempfile.gettempdir()

    def execute(self):
        import threading

        result_code = 0
        timeout_timer = None
        recorder = TimeoutTestRecorder(self)

        try:
            if self._testrun_timeout is not None:
                main_thread_id = threading.current_thread().ident

                def _timeout_handler():
                    import ctypes
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(
                        ctypes.c_ulong(main_thread_id),
                        ctypes.py_object(TestRunTimeoutError)
                    )

                timeout_timer = threading.Timer(self._testrun_timeout, _timeout_handler)
                timeout_timer.daemon = True
                timeout_timer.start()
                self._logger.section("Timeout configured: %d seconds" % self._testrun_timeout)

            self._slow_sequencer.execute_tests(self._run_id, recorder)

        except TestRunTimeoutError:
            err_msg = "Test run exceeded the configured timeout of %d seconds. Remaining tests have been marked as errored." % self._testrun_timeout
            self._logger.error(err_msg)
            result_code = -1

        finally:
            if timeout_timer is not None:
                timeout_timer.cancel()
            recorder.finalize()

        return result_code

    def _create_sequencer(self):
        return self._slow_sequencer

    def _create_recorder(self, runid, start, render_info, build_info, pipeline_info, job_info):
        return TimeoutTestRecorder(self)


class TestJobTimeoutTests(unittest.TestCase):
    """Timeout enforcement. The timeout is read from ``AM_TESTRUN_TIMEOUT`` via the environment seam."""

    def setUp(self):
        self._prev_timeout = os.environ.get("AM_TESTRUN_TIMEOUT", None)

    def tearDown(self):
        if self._prev_timeout is None:
            os.environ.pop("AM_TESTRUN_TIMEOUT", None)
        else:
            os.environ["AM_TESTRUN_TIMEOUT"] = self._prev_timeout

    def _set_timeout(self, value):
        if value is None:
            os.environ.pop("AM_TESTRUN_TIMEOUT", None)
        else:
            os.environ["AM_TESTRUN_TIMEOUT"] = str(value)

    def test_testrun_timeout_defaults_to_none(self):
        self._set_timeout(None)
        job = TestJob(logger=DummyLogger(), testroot="root")
        self.assertIsNone(job._testrun_timeout)

    def test_testrun_timeout_reads_environment_variable(self):
        self._set_timeout(300)
        job = TestJob(logger=DummyLogger(), testroot="root")
        self.assertEqual(job._testrun_timeout, 300)

    def test_testrun_timeout_reads_large_value(self):
        self._set_timeout(86400)
        job = TestJob(logger=DummyLogger(), testroot="root")
        self.assertEqual(job._testrun_timeout, 86400)

    def test_execute_without_timeout_completes_normally(self):
        self._set_timeout(None)
        slow_seq = SlowSequencer(sleep_seconds=0.1)
        logger = DummyLogger()
        job = TimeoutTestJob(logger=logger, testroot="root", slow_sequencer=slow_seq)
        job.begin()
        result_code = job.execute()
        self.assertEqual(result_code, 0)
        self.assertTrue(slow_seq.execute_tests_called)
        self.assertTrue(job.recorder_finalized)

    def test_execute_with_timeout_exceeding_returns_error(self):
        self._set_timeout(1)
        slow_seq = SlowSequencer(sleep_seconds=10)
        logger = DummyLogger()
        job = TimeoutTestJob(logger=logger, testroot="root", slow_sequencer=slow_seq)
        job.begin()
        result_code = job.execute()
        self.assertEqual(result_code, -1)
        timeout_logged = any("timeout" in msg.lower() for msg in logger.errors)
        self.assertTrue(timeout_logged, "Expected a timeout error message to be logged")

    def test_execute_with_sufficient_timeout_completes_normally(self):
        self._set_timeout(30)
        slow_seq = SlowSequencer(sleep_seconds=0.1)
        logger = DummyLogger()
        job = TimeoutTestJob(logger=logger, testroot="root", slow_sequencer=slow_seq)
        job.begin()
        result_code = job.execute()
        self.assertEqual(result_code, 0)
        self.assertTrue(slow_seq.execute_tests_called)
        self.assertTrue(job.recorder_finalized)

    def test_recorder_finalized_on_timeout(self):
        self._set_timeout(1)
        slow_seq = SlowSequencer(sleep_seconds=10)
        logger = DummyLogger()
        job = TimeoutTestJob(logger=logger, testroot="root", slow_sequencer=slow_seq)
        job.begin()
        job.execute()
        self.assertTrue(job.recorder_finalized, "Recorder should be finalized even on timeout")


if __name__ == "__main__":
    unittest.main()
