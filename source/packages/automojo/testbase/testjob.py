"""
    .. module:: automojo.testbase.testjob
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for testjob.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []



from typing import List, Optional
from datetime import datetime

import os
import threading
import traceback

from automojo.xmodules.xformatting import CommandOutputFormat
from automojo.xmodules.debugging import debugger_wellknown_breakpoint_entry
from automojo.xmodules.xlogging.enhancedloggers import EnhancedLogger

from automojo.thisapp.wellknown import ThisApplicationSingleton

from automojo.runtime.runtimevariables import RuntimeVariables, DefaultValue
from automojo.runtime.paths import (
    get_summary_html_template_source,
    get_summary_static_resource_dest_dir,
    get_summary_static_resource_src_dir,
    get_path_for_testresults
)

from automojo.testbase.breakpoints import WELLKNOWN_BREAKPOINTS
from automojo.testbase.results.model.buildinfo import BuildInfo
from automojo.testbase.results.model.jobinfo import JobInfo
from automojo.testbase.results.model.pipelineinfo import PipelineInfo
from automojo.testbase.results.model.renderinfo import RenderInfo

from automojo.testbase.results.recorders.jsonresultrecorder import ResultRecorder, JsonResultRecorder

from automojo.testbase.sequencing.testsequencer import TestSequencer
from automojo.testbase.errors.testruntimeouterror import TestRunTimeoutError
from automojo.interfaces.itestjob import ITestJob

class TestJob(ITestJob):
    """
        The :class:`TestJob` spans the execution of all :class:`TestPack` and organizes the
        flow of execution of test packs.  It allows for the sequencing of the execution of test
        packs so as to optimize the time test runs spend performing setup and tearnown tasks.  This
        allows for the optimization of infrastructure resources.

        * Single Instance
        * Setup Test Landscape
        * Jobs have an expected number of tests based
        * Collects and organizes results from all the :class:`TestPack` runs

        * Can be used to customize the sequencing of :class:`TestPack` runs.
    """

    name = "" # Friendly name for the test job
    description = "" # Description of the job
    owner = "" # The owning individual or team

    includes = None # The test packs or tests that are included in this TestJob
    excludes = None # The tests that are to be excluded from this TestJob
    metafilters = None

    def __init__(self, logger: EnhancedLogger, testroot: str, includes: Optional[List[str]]=None, excludes: Optional[List[str]]=None,
                 metafilters: Optional[List[str]]=None, test_module: Optional[str]=None, parser=None):
        """
            Constructor for a :class:`TestJob`.  It initializes the member variables based on the parameters passed
            from the entry point function and the class member data declared on :class:`TestJob` derived classes.
        """
        self._logger = logger
        self._testroot = testroot

        if self.includes is None:
            self.includes = includes
            self.excludes = excludes

        self.metafilters = metafilters

        self._test_module = test_module
        self._parser = parser
        self._starttime = None

        self._test_results_dir = None
        self._stream_result_filename = None
        self._summary_filename = None
        self._summary_template = None
        self._import_errors_filename = None

        self._testpacks = None

        self._apod = RuntimeVariables.AM_AUTOMATION_POD
        self._release = RuntimeVariables.AM_BUILD_RELEASE
        self._branch = RuntimeVariables.AM_BUILD_BRANCH
        self._build = RuntimeVariables.AM_BUILD_NAME
        self._flavor = RuntimeVariables.AM_BUILD_FLAVOR
        self._build_url = RuntimeVariables.AM_BUILD_URL

        self._run_id = RuntimeVariables.AM_RUN_ID

        self._pipeline_id = RuntimeVariables.AM_PIPELINE_ID
        self._pipeline_name = RuntimeVariables.AM_PIPELINE_NAME
        self._pipeline_instance = RuntimeVariables.AM_PIPELINE_INSTANCE

        self._job_initiator = RuntimeVariables.AM_JOB_INITIATOR
        self._job_id = RuntimeVariables.AM_JOB_ID
        self._job_label = RuntimeVariables.AM_JOB_LABEL
        self._job_name = RuntimeVariables.AM_JOB_NAME
        self._job_owner = RuntimeVariables.AM_JOB_OWNER
        self._job_seed = RuntimeVariables.AM_JOB_SEED
        self._job_type = RuntimeVariables.AM_JOB_TYPE
        self._job_venue = RuntimeVariables.AM_JOB_VENUE
        self._job_tag = RuntimeVariables.AM_JOB_TAG
        
        self._import_errors = []

        self._testrun_timeout = RuntimeVariables.AM_TESTRUN_TIMEOUT

        self._title = "Test Run"
        if self._job_name != DefaultValue.NotSet:
            self._title = self._job_name

        return

    def __enter__(self):
        self.begin()
        return self

    def __exit__(self, ex_type, ex_inst, ex_tb):
        self.finalize()
        return False

    @property
    def import_errors(self):
        return self._import_errors

    @property
    def job_seed(self) -> str:
        """
            Returns the job-level seed for reproducible property testing.

            The seed is a string (typically a UUID) read from ``AM_JOB_SEED``.
            If no seed was set, a random UUID is generated on first access
            and cached for the duration of the job.

            :returns: A string seed value (UUID).
        """
        import uuid

        if self._job_seed is None or self._job_seed == DefaultValue.NotSet:
            self._job_seed = str(uuid.uuid4())
        return str(self._job_seed)

    def begin(self):
        """
            Called at the beginning of a test job in order to setup the recording of test results.
        """

        self._starttime = RuntimeVariables.AM_STARTTIME

        self._test_results_dir = get_path_for_testresults()
        
        # Dump out a flattened copy of the runtime file to the test output folder so we have a copy
        # of the inputs to the automation run.
        self._runtime_archive = os.path.join(self._test_results_dir, "runtime-declared.yaml")

        self._stream_result_filename = os.path.join(self._test_results_dir, "testrun_results_stream.jsos")
        self._consolidated_result_filename = os.path.join(self._test_results_dir, "testrun_results.json")
        self._summary_filename = os.path.join(self._test_results_dir, "testrun_summary.json")
        self._summary_template = get_summary_html_template_source()
        self._import_errors_filename = os.path.join(self._test_results_dir, "import_errors.jsos")
        self._testrun_sequence_filename = os.path.join(self._test_results_dir, "testrun_sequence.py")
        
        return

    def execute(self) -> int:
        """
            Runs the tests that are included in the given :class:'TestPack'.
        """
        result_code = 0

        with self._create_sequencer() as tseq:
            # IMPORTANT: The ordering of the automation sequence is extremely important.  Proper
            # ordering of these steps ensures that the correct things are happening in the correct
            # order in the automation code and that we provide the ability for configuration
            # issues to be discovered as early as possible.

            this_app = ThisApplicationSingleton()

            debugger_name = RuntimeVariables.AM_DEBUG_DEBUGGER
            configured_breakpoints = RuntimeVariables.AM_DEBUG_BREAKPOINTS
            if debugger_name is not None and configured_breakpoints is not None:
                debugger_wellknown_breakpoint_entry(debugger_name, WELLKNOWN_BREAKPOINTS.TEST_DISCOVERY, configured_breakpoints)

            # STEP 1: We discover the tests first so we can build a listing of the
            # Integration and Scope couplings.  We don't want to execute any test code, setup,
            # or teardown code at this point.  We want to seperate out the integration
            # code from the test code and run the integration code first so we can discover
            # integration issues independant of the test code itself.
            self._logger.section("Discovery")
            count = tseq.discover(test_module=self._test_module)

            # STEP 2: Tell the sequencer to record any import errors that happened during discovery
            # of tests.  If a test file or dependent file failed to import then the test
            # will just not be included in a run and this is a type of invisible error
            # that we must plan for and highlight.
            self._import_errors.extend(tseq.import_errors)
            tseq.record_import_errors(self._import_errors_filename)

            if count > 0:

                self._logger.section("Integration Publishing")

                # STEP 1: Call attach_to_framework on the sequencer to give all the couplings a chance
                # to plug themselves into the automation framework.  This allows us to only integrate
                # couplings that are being consumed by the tests AND also to only include couplings that
                # are included in the test framework.  This give the opportunity for the couplings to trigger
                # the startup of the coordinators that inter-operate with the test landscape and the
                # associated devices.
                self.fire_attach_to_framework(tseq)

                # STEP 2: Now that we have collected all the couplings and have a preview of
                # the complexity of the automation run encoded into the coupling types collected.
                # Allow the couplings to attach to the automation environment so they can get
                # a preview of the parameters and configuration and provide us with an early
                # indicator of any parameter or configuration issues.
                #
                # This is the final step of validating all the input information to the run and
                # we are able to perform this step in the context of the integration code and
                # outside of the execution of any test code
                self.fire_attach_to_environment(tseq)

                # STEP 8: Capture pre-run diagnostics
                # This captures the initial state of the test environment before test execution
                # begins, useful for understanding the starting conditions.
                try:
                    from automojo.testbase.diagnostic_level import get_diagnostic_level
                    self.fire_diagnostic_capture_pre_testrun(tseq, level=get_diagnostic_level())
                except Exception:
                    # Log the error with full traceback but do not re-raise
                    # This ensures the test run continues even if diagnostic capture fails
                    err_msg = traceback.format_exc()
                    self._logger.error(err_msg)

                self._logger.section("Expanding Test Tree Based on Query")
                tseq.expand_test_tree_based_on_query()

                self._logger.section("Generating Test Run Sequence")
                # STEP 10: Generate the test run sequence document that will be used or the run.
                tseq.generate_testrun_sequence_document(self._testrun_sequence_filename)

                title = self.name
                runid = self._run_id
                start = self._starttime

                static_resource_source = get_summary_static_resource_src_dir()
                static_resource_destination = get_summary_static_resource_dest_dir()
                
                render_info = RenderInfo(title=title, summary_filename=self._summary_filename, summary_template=self._summary_template,
                                         stream_results_filename=self._stream_result_filename, consolidated_results_filename=self._consolidated_result_filename, static_resource_source=static_resource_source,
                                         static_resource_destination=static_resource_destination)

                def _resolve_val(val):
                    if val is None or val == "" or type(val).__name__ == "DefaultValue":
                        return "(unknown)"
                    return val

                build_info = BuildInfo(branch=_resolve_val(self._branch), build=_resolve_val(self._build), flavor=_resolve_val(self._flavor),
                                       release=_resolve_val(self._release), url=_resolve_val(self._build_url))

                pipeline_info = PipelineInfo(id=_resolve_val(self._pipeline_id), name=_resolve_val(self._pipeline_name), instance=_resolve_val(self._pipeline_instance))

                job_info = JobInfo(id=_resolve_val(self._job_id), name=_resolve_val(self._job_name), type=_resolve_val(self._job_type), owner=_resolve_val(self._job_owner), label=_resolve_val(self._job_label),
                                   initiator=_resolve_val(self._job_initiator), venue=_resolve_val(self._job_venue), seed=self.job_seed, tag=_resolve_val(self._job_tag))
                
                self._logger.section("Running Tests")

                # STEP 11: The startup phase is over, up to this point we have mostly been executing
                # integration code and configuration analysis code that is embedded into mostly class
                # level methods.
                #
                # Now we start going through all the test testpacks and tests and start instantiating
                # test scopes and instances and start executing setup, teardown and test level code
                with self._create_recorder(runid=runid, start=start, render_info=render_info,
                                        build_info=build_info, pipeline_info=pipeline_info, job_info=job_info) as recorder:

                    timeout_timer = None

                    try:
                        # Start timeout guard if configured
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

                        # Traverse the execution graph
                        tseq.execute_tests(runid, recorder)

                        # ============================================================================
                        # ERROR HANDLING STRATEGY - DIAGNOSTIC CAPTURE
                        # ============================================================================
                        # Diagnostic capture is wrapped in its own try/except block to ensure that
                        # diagnostic failures do NOT cause the test run to fail. This is a critical
                        # design decision based on the following principles:
                        #
                        # 1. ISOLATION: Diagnostic capture is a secondary concern - the primary goal
                        #    is test execution. Diagnostic failures should not impact test results.
                        #
                        # 2. GRACEFUL DEGRADATION: If diagnostic capture fails, we log the error
                        #    with full traceback for debugging but continue with finalization.
                        #
                        # 3. NON-BLOCKING: The test run should complete and report results even if
                        #    diagnostic capture encounters issues (e.g., disk full, permission errors,
                        #    integration coupling errors).
                        #
                        # 4. FULL TRACEBACK: We capture the complete traceback using traceback.format_exc()
                        #    to provide maximum debugging information for diagnosing capture failures.
                        #
                        # This pattern ensures that test results are always available, even when
                        # diagnostic capture encounters unexpected errors.
                        # ============================================================================
                        try:
                            # STEP 12: Capture a post-testrun diagnostic capture
                            # This captures the final state of the test environment after all tests
                            # have completed, useful for post-mortem analysis and debugging.
                            from automojo.testbase.diagnostic_level import get_diagnostic_level
                            self.fire_diagnostic_capture_post_testrun(tseq, level=get_diagnostic_level())
                        except Exception:
                            # Log the error with full traceback but do not re-raise
                            # This ensures the test run continues to finalization
                            err_msg = traceback.format_exc()
                            self._logger.error(err_msg)

                    except TestRunTimeoutError:
                        err_msg = "Test run exceeded the configured timeout of %d seconds. Remaining tests have been marked as errored." % self._testrun_timeout
                        self._logger.error(err_msg)
                        result_code = -1

                    finally:
                        # Cancel timeout timer if it is still active
                        if timeout_timer is not None:
                            timeout_timer.cancel()

                        recorder.finalize()

                        recorded_sumary = recorder.summary
                        if "result" in recorded_sumary:
                            if recorded_sumary["result"] != "PASSED":
                                result_code = -1
                        else:
                            self._logger.error("The 'result' field was not found in the recorded summary report.")
                            result_code = -1

                        # STEP 13: This is where we do any final processing and or publishing of results.
                        # We might also want to add automated bug filing here later.
                        self._logger.section("Completed Tests")

                        # Write out the test results
                        results_msg_lines = [""]
                        results_msg_lines.extend(recorder.format_lines())
                        results_msg_lines.append("")

                        results_msg = os.linesep.join(results_msg_lines)

                        self._logger.render(results_msg)

            else:
                # We didn't find any tests so display a message, and set the return code to
                # indicate an error condition
                err_msg_lines = [
                    "The include and exclude parameters specified resulted in an empty test set."
                ]

                if self.includes is not None:
                    err_msg_lines.append("INCLUDES:")
                    for nxtitem in self.includes:
                        err_msg_lines.append("    %s" % nxtitem)
                    err_msg_lines.append("")
                else:
                    err_msg_lines.append("INCLUDES: None")

                if self.excludes is not None:
                    err_msg_lines.append("EXCLUDES:")
                    for nxtitem in self.excludes:
                        err_msg_lines.append("    %s" % nxtitem)
                    err_msg_lines.append("")
                else:
                    err_msg_lines.append("EXCLUDES: None")

                err_msg = os.linesep.join(err_msg_lines)
                self._logger.error(err_msg)

                result_code = -1

        return result_code

    def fire_attach_to_environment(self, tseq: TestSequencer):
        """
            Goes through all the integrations and provides them with an opportunity to
            attach to the test environment.
        """

        tseq.attach_to_environment()

        return

    def fire_attach_to_framework(self, tseq: TestSequencer):
        """
            Goes through all the integrations and provides them with an opportunity to
            attach to the test environment.
        """

        tseq.attach_to_framework()

        return

    def fire_activate_configuration(self):
        self._logger.debug("Firing: fire_activate_configuration")
        return
    
    def fire_activate_integration(self):
        self._logger.debug("Firing: fire_activate_integration")
        return
    
    def fire_activate_operations(self):
        self._logger.debug("Firing: fire_activate_operations")
        return

    def fire_diagnostic_capture_post_testrun(self, tseq: TestSequencer, level: int=9):
        """
        Fires the post-run diagnostic capture event, delegating to the TestSequencer.

        This method is called after test execution completes but before finalization to
        capture diagnostic information about the final state of the test environment.
        It delegates the actual diagnostic capture to the TestSequencer's
        :meth:`diagnostic_capture_post_testrun` method.

        The diagnostic capture is wrapped in error handling at the call site to ensure
        that diagnostic failures do not cause the test run to fail.

        :param tseq: The :class:`TestSequencer` instance managing the test execution.
            The sequencer contains the registered integration couplings that will
            perform the actual diagnostic capture.
        :param level: The maximum diagnostic level to capture (1-9). Higher levels
            indicate more detailed diagnostic information. Defaults to 9 (maximum detail).

            * Levels 1-3: Basic diagnostic information
            * Levels 4-6: Standard diagnostic information
            * Levels 7-9: Detailed diagnostic information

        :returns: None. Diagnostic files are written by integration couplings.

        Lifecycle Position:
            This method is called at STEP 12 in the test execution lifecycle::

                STEP 11: Test execution completes
                STEP 12: fire_diagnostic_capture_post_testrun (this method)
                STEP 13: Finalization begins

        Example Usage::

            # Called internally during test execution
            try:
                self.fire_diagnostic_capture_post_testrun(tseq)
            except Exception:
                err_msg = traceback.format_exc()
                self._logger.error(err_msg)

        Note:
            Errors during diagnostic capture are caught and logged but do not fail
            the test run. This ensures that diagnostic issues do not impact test
            results.

        See Also:
            - :meth:`fire_diagnostic_capture_pre_testrun`: Fires pre-run diagnostics
            - :meth:`TestSequencer.diagnostic_capture_post_testrun`: Performs the capture
        """
        tseq.diagnostic_capture_post_testrun(level)
        return

    def fire_diagnostic_capture_pre_testrun(self, tseq: TestSequencer, level: int=9):
        """
        Fires the pre-run diagnostic capture event, delegating to the TestSequencer.

        This method is called after integration setup completes but before test execution
        begins to capture diagnostic information about the initial state of the test
        environment. It delegates the actual diagnostic capture to the TestSequencer's
        :meth:`diagnostic_capture_pre_testrun` method.

        The diagnostic capture is wrapped in error handling at the call site to ensure
        that diagnostic failures do not cause the test run to fail.

        :param tseq: The :class:`TestSequencer` instance managing the test execution.
            The sequencer contains the registered integration couplings that will
            perform the actual diagnostic capture.
        :param level: The maximum diagnostic level to capture (1-9). Higher levels
            indicate more detailed diagnostic information. Defaults to 9 (maximum detail).

            * Levels 1-3: Basic diagnostic information
            * Levels 4-6: Standard diagnostic information
            * Levels 7-9: Detailed diagnostic information

        :returns: None. Diagnostic files are written by integration couplings.

        Lifecycle Position:
            This method is called at STEP 8 in the test execution lifecycle::

                STEP 7: Integration setup completes
                STEP 8: fire_diagnostic_capture_pre_testrun (this method)
                STEP 9: Test execution begins

        Example Usage::

            # Called internally during test execution
            try:
                self.fire_diagnostic_capture_pre_testrun(tseq)
            except Exception:
                err_msg = traceback.format_exc()
                self._logger.error(err_msg)

        Note:
            Errors during diagnostic capture are caught and logged but do not fail
            the test run. This ensures that diagnostic issues do not impact test
            results.

        See Also:
            - :meth:`fire_diagnostic_capture_post_testrun`: Fires post-run diagnostics
            - :meth:`TestSequencer.diagnostic_capture_pre_testrun`: Performs the capture
        """
        tseq.diagnostic_capture_pre_testrun(level)
        return

    def fire_establish_presence(self, tseq: TestSequencer):

        tseq.establish_presence()

        return

    def finalize(self): # pylint: disable=no-self-use
        """
            Called at the end of a test job in order to flush the results of the test run, copy
            the report template to the output directory.
        """
        return

    def query(self, format: CommandOutputFormat=CommandOutputFormat.DISPLAY):
        
        query_results = []

        with self._create_sequencer() as tseq:
            
            count = tseq.discover(test_module=self._test_module)

            query_results = tseq.references

            self._import_errors.extend(tseq.import_errors)

        return query_results

    @classmethod
    def user_interface_display_options(cls):
        """
            Overridden by derived TestJob classes in order to return a configuration user interface
            description that provides information about a vue javascript component that meets the
            interface requirements and will allow a user to display job configuration information that
            can be packaged stored in a data store as a json object and later passed to a job in order
            to configure the job.
        """
        return

    @classmethod
    def user_interface_edit_options(cls):
        """
            Overridden by derived TestJob classes in order to return a configuration user interface
            description that provides information about a vue javascript component that meets the
            interface requirements and will allow a user to input job configuration information that
            can be packaged stored in a data store as a json object and later passed to a job in order
            to configure the job.
        """
        return

    def _create_recorder(self, runid: str, start: datetime, render_info: RenderInfo, build_info: BuildInfo,
                         pipeline_info: PipelineInfo, job_info: JobInfo) -> ResultRecorder:
        """
            Simple hook function to make it possible to overload the type of ResultRecorder that is created for
            any given job.
        """

        inst = JsonResultRecorder(runid=runid, start=start, render_info=render_info, apod=self._apod,
                                        build_info=build_info, pipeline_info=pipeline_info, job_info=job_info)
        return inst

    def _create_sequencer(self):
        """
            Simple hook function to make it possible to overload the type of the TestSequencer that is created
            for jobs.
        """
        inst = TestSequencer(self._title, self._testroot, includes=self.includes, excludes=self.excludes, metafilters=self.metafilters, job_seed=self.job_seed)
        return inst



class DefaultTestJob(TestJob):
    """
        The :class:`DefautTestJob` is utilized as a job container when a job was not specified.
    """
    name = "Test Job"
    description = "Unspecified test job."
