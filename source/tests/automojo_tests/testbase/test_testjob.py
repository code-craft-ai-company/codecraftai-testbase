import os
import tempfile
import unittest

import automojo.runtime.paths as runtime_paths
from automojo.runtime.enumerations import JobType
from automojo.runtime.runtimevariables import RuntimeVariablesDesc
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

        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

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
                start="s",
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


if __name__ == "__main__":
    unittest.main()
