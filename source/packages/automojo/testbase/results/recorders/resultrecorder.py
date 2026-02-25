"""
    .. module:: automojo.testbase.results.recorders.resultrecorder
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for resultrecorder.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import List, Optional

from types import TracebackType

import collections
import copy
import os
import shutil
import threading

from datetime import datetime

from automojo.errors.exceptions import AbstractMethodError

from automojo.testbase.results.exceptions import ResultRecordingError
from automojo.testbase.results.model.buildinfo import BuildInfo
from automojo.testbase.results.model.jobinfo import JobInfo
from automojo.testbase.results.model.pipelineinfo import PipelineInfo
from automojo.testbase.results.model.renderinfo import RenderInfo

from automojo.testbase.results.model.resultnode import ResultNode
from automojo.testbase.results.model.resulttype import ResultType

from automojo.testbase.results.utilities import (
    catalog_tree,
    DEFAULT_DO_NOT_CATALOG_DIRS,
    DEFAULT_DO_NOT_DESCEND_DIRS
)

from automojo.testbase.results.model.progresscode import ProgressCode
from automojo.testbase.results.model.progressinfo import ProgressInfo
from automojo.testbase.results.model.forwardinginfo import ForwardingInfo
from automojo.testbase.results.model.nestedprogressinfo import NestedProgressInfo
from automojo.testbase.results.model.progressaggregator import ProgressAggregator


class ResultRecorder:
    """
        The :class:`ResultRecorder` object is the base class that establishes the API patterns
        for recorders of different formats to use when implementing a test result recorder.

        This class provides the foundation for recording test execution results, managing
        the test run lifecycle, tracking result counts, and generating summaries. Derived
        classes (such as :class:`JsonResultRecorder`) implement format-specific serialization.

        Context Manager Lifecycle
        -------------------------
        The ResultRecorder is designed to be used as a context manager to ensure proper
        resource management and lifecycle handling:

        1. **Entry (__enter__)**: Initializes the recording environment by:
           - Calling initialize_report() to set up output directories and static resources
           - Calling update_summary() to write the initial summary file
           - Opening the stream results file for writing

        2. **Active Recording**: While the context is active:
           - Call preview() to write result previews before test execution
           - Call record() to write final results after test completion
           - Call post_task_progress() to update progress from remote workers

        3. **Exit (__exit__)**: Finalizes the recording by:
           - Calling finalize() if not already finalized
           - Updating final counts and result status
           - Closing the stream results file
           - Writing the final summary

        Thread Safety Considerations
        ----------------------------
        The ResultRecorder is designed for concurrent access from multiple threads:

        - **Lock Protection**: A threading.Lock (_lock) protects all shared state mutations
        - **Copy-on-Read**: The summary property returns a deep copy to prevent external
          modification and ensure consistent snapshots for concurrent readers
        - **Atomic Updates**: Counter increments and progress updates are performed
          atomically within lock-protected sections
        - **Safe Finalization**: The finalize() method is lock-protected to prevent
          race conditions during shutdown

        Thread-safe methods:
            - summary (property): Returns a deep copy of the current summary
            - post_task_progress(): Updates running tasks dictionary
            - clear_task_progress(): Removes completed tasks
            - finalize(): Finalizes counts and closes resources
            - record(): Updates result counters (in derived classes)

        Usage Example
        -------------
        Basic usage with context manager::

            from datetime import datetime
            from automojo.testbase.results.recorders.jsonresultrecorder import JsonResultRecorder
            from automojo.testbase.results.model.renderinfo import RenderInfo
            from automojo.testbase.results.model.buildinfo import BuildInfo
            from automojo.testbase.results.model.pipelineinfo import PipelineInfo
            from automojo.testbase.results.model.jobinfo import JobInfo

            # Configure render info
            render_info = RenderInfo(
                title="My Test Run",
                summary_filename="/output/testsummary.json",
                summary_template="/templates/testsummary.html",
                stream_results_filename="/output/testresults_stream.jsos",
                consolidated_results_filename="/output/testresults.json",
                static_resource_source="/templates/static",
                static_resource_destination="/output/static"
            )

            # Configure metadata
            build_info = BuildInfo(branch="main", build="123", flavor="release",
                                   release="1.0.0", url="https://builds.example.com/123")
            pipeline_info = PipelineInfo(id="pipe-1", name="CI Pipeline", instance="run-456")
            job_info = JobInfo(id="job-1", name="Test Job", type="integration",
                               owner="team@example.com")

            # Use as context manager
            with JsonResultRecorder(
                runid="run-uuid-123",
                start=datetime.now(),
                render_info=render_info,
                build_info=build_info,
                pipeline_info=pipeline_info,
                job_info=job_info
            ) as recorder:
                # Record test results
                for test_result in test_results:
                    recorder.preview(test_result)
                    # ... execute test ...
                    recorder.record(test_result)

            # After context exits, results are finalized and files are closed

        Multi-threaded usage with progress tracking::

            import threading
            from automojo.testbase.results.model.progressinfo import ProgressInfo
            from automojo.testbase.results.model.progresscode import ProgressCode

            def worker_thread(recorder, task_id):
                # Report progress from worker thread
                progress = ProgressInfo(
                    id=task_id,
                    category="worker",
                    moniker=f"Task {task_id}",
                    ptype="Sequential",
                    range_min="0",
                    range_max="100",
                    position="50",
                    status=ProgressCode.Running,
                    when=datetime.now()
                )
                recorder.post_task_progress([progress])

            with JsonResultRecorder(...) as recorder:
                threads = []
                for i in range(5):
                    t = threading.Thread(target=worker_thread, args=(recorder, f"task-{i}"))
                    threads.append(t)
                    t.start()

                for t in threads:
                    t.join()

        See Also
        --------
        :class:`JsonResultRecorder` : Concrete implementation for JSON output format
        :class:`ProgressConcentratorServer` : HTTP server for receiving remote progress updates
    """
    def __init__(self, *, runid: str, start: datetime, render_info: RenderInfo,
                 apod: Optional[str] = None, build_info: Optional[BuildInfo] = None,
                 pipeline_info: Optional[PipelineInfo] = None, job_info: Optional[JobInfo] = None,
                 forwarding_info: Optional[ForwardingInfo] = None):
        """
            Initializes an instance of a ResultRecorder with the information about a test run.

            This constructor sets up all internal state required for result recording,
            including counters, summary data structures, and thread synchronization
            primitives. The recorder is not active until used as a context manager.

            :param runid: The uuid string that identifies a set of test results. This ID
                          is used to correlate results across different output files and
                          external systems.
            :param start: The date and time of the start of the test run. Used for timing
                          calculations and included in the summary output.
            :param render_info: A :class:`RenderInfo` instance containing output file paths
                                and rendering configuration. This determines where results
                                are written and what templates are used.
            :param apod: Optional name of an automation pod that the automation run is
                         running on. Useful for distributed test execution environments.
            :param build_info: Optional :class:`BuildInfo` instance containing build metadata
                               (branch, build number, flavor, release, URL) to associate
                               with the test run.
            :param pipeline_info: Optional :class:`PipelineInfo` instance containing CI/CD
                                  pipeline metadata (id, name, instance) to associate with
                                  the test run.
            :param job_info: Optional :class:`JobInfo` instance containing job execution
                             metadata (id, name, type, owner, etc.) to associate with
                             the test run.
            :param forwarding_info: Optional :class:`ForwardingInfo` instance containing
                                    configuration for forwarding progress updates to
                                    external monitoring services.

            :returns: None

            Thread Safety:
                The constructor initializes a threading.Lock that is used by all
                thread-safe methods. The lock is not acquired during construction
                as the object is not yet shared between threads.
        """

        self._runid = runid
        self._start = start
        self._apod = apod

        self._render_info = render_info
        self._build_info = build_info
        self._pipeline_info = pipeline_info
        self._job_info = job_info
        self._forwarding_info = forwarding_info

        self._output_dir = os.path.dirname(self._render_info.summary_filename)

        self._rout = None

        self._running_tasks = {}

        # Progress aggregator for nested progress tracking and aggregation
        self._progress_aggregator = ProgressAggregator()

        self._error_count = 0
        self._failure_count = 0
        self._pass_count = 0
        self._skip_count = 0
        self._unknown_count = 0

        self._total_count = 0

        self._finalized = False

        def _get_val(obj, attr_name):
            if obj is None:
                return "(unknown)"
            val = getattr(obj, attr_name, None)
            if val is None or val == "" or type(val).__name__ == "DefaultValue":
                return "(unknown)"
            return val

        build_info = collections.OrderedDict((
            ("release", _get_val(self._build_info, "release")),
            ("branch", _get_val(self._build_info, "branch")),
            ("build", _get_val(self._build_info, "build")),
            ("flavor", _get_val(self._build_info, "flavor")),
            ("url", _get_val(self._build_info, "url"))
        ))

        pipeline_info = collections.OrderedDict((
            ("id", _get_val(self._pipeline_info, "id")),
            ("name", _get_val(self._pipeline_info, "name")),
            ("instance", _get_val(self._pipeline_info, "instance"))
        ))

        job_info = collections.OrderedDict((
            ("id", _get_val(self._job_info, "id")),
            ("initiator", _get_val(self._job_info, "initiator")),
            ("label", _get_val(self._job_info, "label")),
            ("name", _get_val(self._job_info, "name")),
            ("owner", _get_val(self._job_info, "owner")),
            ("type", _get_val(self._job_info, "type")),
            ("venue", _get_val(self._job_info, "venue")),
            ("seed", _get_val(self._job_info, "seed")),
            ("tag", _get_val(self._job_info, "tag"))
        ))

        self._summary = collections.OrderedDict((
            ("version", "2"),
            ("title", self._render_info.title),
            ("runid", self._runid),
            ("build", build_info),
            ("pipeline", pipeline_info),
            ("job", job_info),
            ("start", self._start),
            ("stop", None),
            ("result", "RUNNING"),
            ("apod", self._apod),
            ("totals", None),
            ("running", self._running_tasks)
        ))

        self._lock = threading.Lock()
        self._next_forward_at = None

        return


    def __enter__(self):
        """
            Starts up the recording process of test results.

            This method is called when entering the context manager (the 'with' statement).
            It performs all necessary initialization to prepare the recorder for accepting
            test results.

            Initialization Steps:
                1. **initialize_report()**: Sets up the output environment by copying
                   static resources and the HTML template to the output directory
                2. **update_summary()**: Writes the initial summary file with run metadata
                3. **Open stream file**: Opens the stream results file for writing result
                   records as they are generated

            Context Manager Pattern:
                The ResultRecorder implements the context manager protocol to ensure
                proper resource management. Using the 'with' statement guarantees that
                finalize() will be called even if an exception occurs during test execution.

            Example::

                with JsonResultRecorder(runid="123", start=datetime.now(), ...) as recorder:
                    # recorder.__enter__() has been called
                    # Stream file is open and ready for writing
                    recorder.preview(test_result)
                    recorder.record(test_result)
                # recorder.__exit__() is called automatically

            :returns: self - The recorder instance for use within the context block.

            :raises: ResultRecordingError if the stream results file cannot be opened
                     for writing. The error includes the file path, operation description,
                     and underlying exception details.
        """
        self.initialize_report()

        self.update_summary()

        stream_filename = self._render_info.stream_results_filename
        try:
            self._rout = open(stream_filename, 'w')
        except OSError as err:
            errmsg = f"Failed to open stream results file '{stream_filename}' for writing."
            raise ResultRecordingError(
                errmsg,
                file_path=stream_filename,
                operation="opening stream results file",
                original_error=err
            ) from err
        return self


    def __exit__(self, ex_type: type, ex_inst: Exception, ex_tb: TracebackType) -> bool:
        """
            Finalizes the recording process when exiting the context manager.

            This method is called when exiting the context manager (leaving the 'with'
            block), whether normally or due to an exception. It ensures that all results
            are properly finalized and resources are released.

            Finalization Steps:
                1. Check if already finalized (prevents duplicate finalization)
                2. Call finalize() to:
                   - Set the stop timestamp
                   - Update final result counts in the summary
                   - Determine overall pass/fail status
                   - Close the stream results file
                   - Write the final summary

            Exception Handling:
                This method does not suppress exceptions. If an exception occurred within
                the context block, it will propagate after __exit__ completes. The
                finalization is performed regardless of whether an exception occurred,
                ensuring results are always properly closed.

            Thread Safety:
                The finalize() method called by __exit__ is thread-safe and uses locking
                to ensure atomic updates to shared state. However, __exit__ itself should
                only be called once (by the context manager machinery).

            :param ex_type: The type associated with the exception being raised, or None
                            if no exception occurred.
            :param ex_inst: The exception instance of the exception being raised, or None
                            if no exception occurred.
            :param ex_tb: The traceback associated with the exception being raised, or None
                          if no exception occurred.

            :returns: None (does not suppress exceptions). Returning None or False allows
                      any exception to propagate; returning True would suppress it.
        """
        if not self._finalized:
            self.finalize()
        return


    @property
    def summary(self):
        """
            Get a thread-safe copy of the result summary.

            This property returns a deep copy of the internal summary dictionary,
            ensuring that callers cannot modify the recorder's internal state and
            that the returned data remains consistent even if other threads update
            the summary after this call returns.

            Thread Safety Implementation:
                The property uses a lock-protected copy-on-read pattern:

                1. Acquire the lock to prevent concurrent modifications
                2. Create a deep copy of the summary dictionary
                3. Release the lock
                4. Return the copy

                This pattern is critical for the forwarding thread, which may be
                serializing the summary while other threads update progress.

            Summary Contents:
                The returned dictionary contains:

                - **version**: Summary format version (currently "2")
                - **title**: Test run title from render_info
                - **runid**: Unique identifier for this test run
                - **build**: Build metadata (release, branch, build, flavor, url)
                - **pipeline**: Pipeline metadata (id, name, instance)
                - **job**: Job metadata (id, name, type, owner, etc.)
                - **start**: Test run start timestamp
                - **stop**: Test run stop timestamp (None until finalized)
                - **result**: Current result status ("RUNNING", "PASSED", or "FAILED")
                - **apod**: Automation pod identifier
                - **totals**: Reserved for future use
                - **running**: Dictionary of currently running tasks
                - **detail**: Final counts (only present after finalization)

            Example::

                with JsonResultRecorder(...) as recorder:
                    # Get current summary for monitoring
                    current_summary = recorder.summary
                    print(f"Status: {current_summary['result']}")
                    print(f"Running tasks: {len(current_summary['running'])}")

            :returns: A deep copy of the summary dictionary. Modifications to the
                      returned dictionary do not affect the recorder's internal state.

            :rtype: dict
        """
        rtnval = None

        # THREAD-SAFE STATE PATTERN - COPY ON READ:
        # Acquire the lock before accessing shared state (_summary).
        # We return a deep copy to prevent callers from modifying the
        # internal state and to ensure the returned data remains consistent
        # even if other threads update the summary after we release the lock.
        self._lock.acquire()
        try:
            # Deep copy ensures the caller gets an immutable snapshot.
            # This is critical for the forwarding thread which may be
            # serializing the summary while other threads update progress.
            rtnval = copy.deepcopy(self._summary)
        finally:
            # Always release the lock in finally block to prevent deadlocks
            # even if an exception occurs during the copy operation.
            self._lock.release()

        return rtnval


    def catalog_output_directory(self):
        """
            Triggers catalog generation for the results output directory.

            This method creates catalog.json files in each directory of the output
            tree, enabling HTML report navigation. The catalog files contain lists
            of files and subdirectories, allowing the HTML report to dynamically
            build navigation menus.

            Catalog Generation Rules:
                - Creates catalog.json in each directory
                - Skips directories in DEFAULT_DO_NOT_CATALOG_DIRS (e.g., "__pycache__")
                - Does not descend into directories in DEFAULT_DO_NOT_DESCEND_DIRS
                  (e.g., "diagnostics")

            This method is called automatically by:
                - initialize_report() during context entry
                - preview() after writing a preview record
                - record() after writing a final result record
                - update_summary() after updating the summary file
                - write_consolidated_results() after writing consolidated results

            :returns: None
        """
        catalog_tree(self._output_dir, dont_catalog_dirs=DEFAULT_DO_NOT_CATALOG_DIRS,
                     dont_descend_dirs=DEFAULT_DO_NOT_DESCEND_DIRS)
        return


    def clear_task_progress(self, task_ids: List[str]):
        """
            Clears progress entries for the specified task IDs from the running tasks dictionary.

            This method removes completed or cancelled tasks from the running_tasks
            dictionary, which is included in the summary for real-time monitoring.
            It is typically called when tasks complete or are explicitly cancelled.

            Thread Safety:
                This method is thread-safe. It acquires the internal lock before
                modifying the running_tasks dictionary, ensuring atomic removal
                of multiple task IDs without interference from concurrent progress
                updates or summary reads.

            Example::

                # Clear completed tasks
                completed_task_ids = ["task-1", "task-2", "task-3"]
                recorder.clear_task_progress(completed_task_ids)

            :param task_ids: A list of task ID strings to remove from running_tasks.
                             Task IDs that don't exist in the dictionary are silently
                             ignored (no KeyError is raised).

            :returns: None
        """

        # THREAD-SAFE STATE PATTERN - LOCK PROTECTED MUTATION:
        # Acquire the lock before modifying shared state (_running_tasks).
        # This ensures atomic removal of multiple task IDs without interference
        # from concurrent progress updates or summary reads.
        self._lock.acquire()
        try:
            for tid in task_ids:
                # Check existence before deletion to avoid KeyError
                if tid in self._running_tasks:
                    del self._running_tasks[tid]
        finally:
            # Always release the lock in finally block to prevent deadlocks
            self._lock.release()

        return


    def consolidate_results(self):
        """
            Process the results stream and roll it up into a consolidated test results document.

            This method reads the streaming results file (JSOS format) and builds a
            hierarchical tree structure that mirrors the test execution hierarchy.
            The consolidated results are then written to a single JSON file for
            easier consumption by reporting tools.

            RESULT CONSOLIDATION ALGORITHM:
            ================================
            The algorithm processes a flat stream of result records and reconstructs
            the hierarchical test execution tree. It uses a node lookup dictionary
            to efficiently find parent nodes when building the tree.

            Algorithm Steps:
                1. Initialize empty node_lookup dictionary and root_node reference
                2. Load all records from the stream results file
                3. For each record, determine its type and process accordingly:
                   - JOB: Set as root node (only one allowed)
                   - TEST_CONTAINER: Add to parent's items list
                   - TEST: Add to parent's items list, initialize tasking_groups
                   - TASKING_GROUP: Add to parent's tasking_groups list
                   - TASKING: Add to parent's taskings list
                4. Handle preview/final record merging for TEST, TASKING_GROUP, TASKING
                5. Write the complete tree to the consolidated results file

            Data Structures:
                - node_lookup: Dict[str, dict] - Maps instance IDs to node dictionaries
                  for O(1) parent lookup during tree construction
                - root_node: dict - The JobContainer that serves as the tree root

            Preview/Final Record Merging:
                The stream contains both preview records (written before test execution)
                and final records (written after execution). When a final record arrives,
                we check if a preview exists in node_lookup and merge the final data
                into the preview record. This preserves the tree structure while updating
                with final results.

            Result Tree Structure::

                JobContainer (root)
                ├── items: [
                │   TestContainer
                │   ├── items: [
                │   │   TestResult
                │   │   ├── tasking_groups: [
                │   │   │   TaskingGroup
                │   │   │   ├── taskings: [TaskingResult, ...]
                │   │   │   ]
                │   │   ]
                │   ]
                ]

            Error Handling:
                - Raises Exception if more than one JOB record is found
                - Raises Exception if a non-JOB record has no parent in the lookup

            :returns: None

            :raises: Exception if the stream contains invalid hierarchy (multiple roots
                     or orphaned nodes).
        """

        # INITIALIZATION:
        # ---------------
        # node_lookup: Dictionary mapping instance IDs to node dictionaries.
        # This enables O(1) lookup when finding parent nodes during tree construction.
        # root_node: Reference to the JobContainer that serves as the tree root.
        node_lookup = {}
        root_node = None

        # STEP 1: LOAD RESULT STREAM
        # --------------------------
        # Load all records from the JSOS (JSON Separated Object Stream) file.
        # Records are returned in the order they were written during test execution.
        result_stream = self.load_result_stream()

        # STEP 2: PROCESS EACH RECORD AND BUILD TREE
        # ------------------------------------------
        # Iterate through records in order, building the hierarchical tree structure.
        # Each record is classified by type and added to the appropriate parent node.
        for ritem in result_stream:

            # Extract key fields for processing
            ritem_inst = ritem["instance"]  # Unique identifier for this node
            ritem_type = ritem["type"]       # ResultType name (JOB, TEST, etc.)

            # CASE: JOB RECORD (ROOT NODE)
            # ----------------------------
            # The JOB record represents the root of the result tree.
            # There should be exactly one JOB record in the stream.
            if ritem_type == ResultType.JOB.name:
                # VALIDATION: Ensure only one root node exists
                if root_node is not None:
                    raise Exception("More than one job node found in results file.")
                root_node = ritem

                # Initialize the items list for child containers (TestContainers)
                root_node["items"] = []
            else:
                # CASE: NON-ROOT RECORD
                # ---------------------
                # All non-JOB records must have a parent in the lookup.
                # This validates the stream contains a valid hierarchy.

                ritem_parent_id = ritem["parent"]
                
                # VALIDATION: Parent must exist in lookup
                # This catches orphaned nodes that would break the tree structure.
                if ritem_parent_id not in node_lookup:
                    errmsg = f"We should never encounter a non-job node that does not have a parent.  Id={ritem_inst} Parent={ritem_parent_id}"
                    raise Exception(errmsg)
                
                # Retrieve parent node for attaching this record
                parent_node = node_lookup[ritem_parent_id]
            
                # CASE: TEST_CONTAINER RECORD
                # ---------------------------
                # TestContainers represent module-level groupings of tests.
                # They are added to their parent's items list and can contain
                # other TestContainers or TestResults.
                if ritem_type == ResultType.TEST_CONTAINER.name:
                    
                    # Add to parent's items list (parent is JobContainer or TestContainer)
                    parent_node_items: list = parent_node["items"]
                    parent_node_items.append(ritem)
                    
                    # Initialize items list for child nodes
                    ritem["items"] = []

                    # Register in lookup for child nodes to find this parent
                    node_lookup[ritem_inst] = ritem

                # CASE: TEST RECORD
                # -----------------
                # TestResults represent individual test execution outcomes.
                # They may have associated TaskingGroups for distributed execution.
                elif ritem_type == ResultType.TEST.name:

                    # Add to parent's items list (parent is TestContainer)
                    parent_node_items: list = parent_node["items"]
                    parent_node_items.append(ritem)
                    
                    # Initialize tasking_groups list if not present
                    # (may already exist from preview record)
                    if "tasking_groups" not in ritem:
                        ritem["tasking_groups"] = []

                    # PREVIEW/FINAL RECORD MERGING:
                    # If a preview record exists in the lookup, merge the final
                    # record data into it. This preserves tree references while
                    # updating with final results (result_code, errors, etc.).
                    if ritem_inst in node_lookup:
                        preview_info: dict = node_lookup[ritem_inst]
                        preview_info.update(ritem)

                    else:
                        # This must be an injected failure that does not have a preview
                        # (e.g., a test that failed during collection/setup)
                        node_lookup[ritem_inst] = ritem

                # CASE: TASKING_GROUP RECORD
                # --------------------------
                # TaskingGroups contain related TaskingResults from distributed
                # task execution within a single test.
                elif ritem_type == ResultType.TASKING_GROUP.name:
                    # Add to parent's tasking_groups list (parent is TestResult)
                    parent_node_taskinggroups: list = parent_node["tasking_groups"]
                    parent_node_taskinggroups.append(ritem)

                    # Initialize taskings list if not present
                    if "taskings" not in ritem:
                        ritem["taskings"] = []

                    # PREVIEW/FINAL RECORD MERGING (same pattern as TEST)
                    if ritem_inst in node_lookup:
                        preview_info: dict = node_lookup[ritem_inst]
                        preview_info.update(ritem)

                    else:
                        # This must be an injected failure that does not have a preview
                        node_lookup[ritem_inst] = ritem

                # CASE: TASKING RECORD
                # --------------------
                # TaskingResults represent individual distributed task outcomes
                # with worker information and return values.
                elif ritem_type == ResultType.TASKING.name:
                    # Add to parent's taskings list (parent is TaskingGroup)
                    parent_node_taskings: list = parent_node["taskings"]
                    parent_node_taskings.append(ritem)

                    # PREVIEW/FINAL RECORD MERGING (same pattern as TEST)
                    if ritem_inst in node_lookup:
                        preview_info: dict = node_lookup[ritem_inst]
                        preview_info.update(ritem)

                    else:
                        # This must be an injected failure that does not have a preview
                        node_lookup[ritem_inst] = ritem

        # STEP 3: WRITE CONSOLIDATED RESULTS
        # ----------------------------------
        # Write the complete hierarchical tree to the consolidated results file.
        # The root_node now contains the entire tree structure with all nested
        # containers and results.
        self.write_consolidated_results(root_node)

        return


    def finalize(self):
        """
            Finalizes the test results counters and status of the test run.

            This method completes the test run by setting the stop timestamp,
            calculating final result counts, determining the overall pass/fail
            status, and closing all output resources. It is automatically called
            by __exit__ when leaving the context manager.

            Finalization Steps:
                1. Acquire the lock for thread-safe state updates
                2. Set the finalized flag to prevent duplicate finalization
                3. Record the stop timestamp
                4. Update the summary with final timing and result details
                5. Determine overall result (PASSED if no errors/failures, else FAILED)
                6. Close the stream results file
                7. Write the final summary to disk
                8. Release the lock

            Thread Safety:
                This method is fully thread-safe. It acquires the internal lock
                before modifying any shared state, ensuring that concurrent calls
                to record(), post_task_progress(), or summary access do not
                interfere with finalization.

            Idempotency:
                The method checks the _finalized flag and only performs finalization
                once. Subsequent calls are no-ops. This prevents issues if finalize()
                is called explicitly and then again by __exit__.

            Result Determination:
                - If error_count > 0 OR failure_count > 0: result = "FAILED"
                - Otherwise: result = "PASSED"

            Example::

                with JsonResultRecorder(...) as recorder:
                    # Record tests...
                    pass
                # finalize() is called automatically here

                # Or call explicitly (not recommended):
                recorder.finalize()  # No-op if already finalized

            :returns: None
        """

        # THREAD-SAFE FINALIZATION:
        # Acquire the lock before modifying shared state during finalization.
        # This ensures the summary is updated atomically and prevents race
        # conditions with concurrent progress updates or summary reads.
        self._lock.acquire()
        try:

            # Mark as finalized to prevent duplicate finalization
            self._finalized = True

            self._stop = datetime.now()

            # Update summary with final timing and result details
            self._summary["stop"] = str(self._stop)

            # Populate the detail section with final test counts
            self._summary["detail"] = {
                "errors": self._error_count,
                "failed": self._failure_count,
                "skipped": self._skip_count,
                "passed": self._pass_count,
                "total": self._total_count
            }

            # Determine final result based on error/failure counts
            if self._error_count > 0 or self._failure_count > 0:
                self._summary["result"] = "FAILED"
            else:
                self._summary["result"] = "PASSED"

            # Close the results output stream
            self._rout.close()

            # Write final summary to disk
            self.update_summary()

        finally:
            # Always release the lock in finally block to prevent deadlocks
            self._lock.release()

        return
    

    def format_lines(self):
        """
            Generates a list of formatted summary lines for console output.

            This method creates a human-readable summary of the test run that can
            be printed to the console or logged. The output includes metadata,
            timing information, result counts, and the overall status.

            Output Format::

                 ============== Test Summary ==============
                   Title: My Test Run
                  Release: 1.0.0
                  Branch: main
                   Build: 123
                  Flavor: release
                   Owner: team@example.com
                   RunId: run-uuid-123
                   Start: 2025-02-20 10:00:00
                    Stop: 2025-02-20 10:30:00
                 ----------------- Detail -----------------
                       Errors: 0
                       Failed: 2
                      Skipped: 1
                       Passed: 97
                        Total: 100
                 ==========================================
                   FAILED
                 ==========================================

                OUTPUT PATH: /path/to/output
                SUMMARY URL: https://results.example.com/run-123

            Environment Variables:
                - AM_SUMMARY_URL: If set, the summary URL is included in the output

            Example::

                with JsonResultRecorder(...) as recorder:
                    # ... record tests ...
                    pass

                # Print summary to console
                for line in recorder.format_lines():
                    print(line)

            :returns: A list of strings, each representing one line of the formatted
                      summary. Lines do not include trailing newlines.

            :rtype: List[str]
        """
        lines = [
            " ============== Test Summary ============== ",
        ]

        if self._render_info.title:
            lines.append("   Title: {}".format(self._render_info.title))

        if self._build_info is not None:
            if self._build_info.release:
                lines.append("  Release: {}".format(self._build_info.release))
            if self._build_info.branch:
                lines.append("  Branch: {}".format(self._build_info.branch))
            if self._build_info.build:
                lines.append("   Build: {}".format(self._build_info.build))
            if self._build_info.flavor:
                lines.append("  Flavor: {}".format(self._build_info.flavor))

        if self._job_info is not None:
            if self._job_info.owner:
                lines.append("   Owner: {}".format(self._job_info.owner))

        lines.extend([
            "   RunId: {}".format(self._runid),
            "   Start: {}".format(self._start),
            "    Stop: {}".format(self._stop),
            " ----------------- Detail ----------------- ",
            "       Errors: {}".format(self._error_count),
            "       Failed: {}".format(self._failure_count),
            "      Skipped: {}".format(self._skip_count),
            "       Passed: {}".format(self._pass_count),
            "        Total: {}".format(self._total_count),
            " ========================================== ",
            "   {}".format(self._summary["result"]),
            " ========================================== ",
            "",
            "OUTPUT PATH: {}".format(self._output_dir)
        ])

        if "AM_SUMMARY_URL" in os.environ:
            summary_url = os.environ["AM_SUMMARY_URL"]
            lines.append("SUMMARY URL: {}".format(summary_url))

        return lines


    def forward_summary_update(self, summary):
        """
            Forwards a summary update to an external monitoring service.

            This method is called by post_task_progress() when forwarding is configured
            and the forwarding interval has elapsed. The base implementation is a no-op;
            derived classes or the ProgressConcentratorServer handle actual forwarding.

            :param summary: A dictionary containing the current summary state to forward.

            :returns: None
        """
        return


    def get_summary_render_file_basename(self):
        """
            Returns the base filename for the HTML summary render file.

            This method provides the filename used when copying the HTML template
            to the output directory. Override this method in derived classes to
            use a different filename.

            :returns: The base filename for the HTML summary file.

            :rtype: str
        """
        return "testsummary.html"


    def initialize_report(self):
        """
            Initializes the report output environment.

            This method is called by __enter__ to set up the output directory
            structure and copy required resources before recording begins.

            Initialization Steps:
                1. Call update_render_environment() to copy static resources
                   (CSS, JavaScript, images) to the output directory
                2. Copy the HTML summary template to the output directory
                3. Call catalog_output_directory() to generate initial catalog files

            :returns: None

            :raises: ResultRecordingError if files cannot be copied or directories
                     cannot be created. The error includes the file path, operation
                     description, and underlying exception details.
        """

        self.update_render_environment()

        summary_html_source = self._render_info.summary_template
        summary_render_html_base = self.get_summary_render_file_basename()
        summary_render_html_dest = os.path.join(self._output_dir, summary_render_html_base)

        try:
            shutil.copy2(summary_html_source, summary_render_html_dest)
        except OSError as err:
            errmsg = f"Failed to copy summary template from '{summary_html_source}' to '{summary_render_html_dest}'."
            raise ResultRecordingError(
                errmsg,
                file_path=summary_render_html_dest,
                operation="copying summary template",
                original_error=err
            ) from err

        self.catalog_output_directory()

        return


    def load_result_stream(self) -> List[dict]:
        """
            Loads and parses the result stream file.

            This method reads the streaming results file (JSOS format) and returns
            a list of result dictionaries. The base implementation returns an empty
            list; derived classes should override to provide actual loading.

            :returns: A list of result dictionaries parsed from the stream file.

            :rtype: List[dict]
        """
        return


    def preview(self, result: ResultNode):
        """
            Writes a preview of a result to the result stream.

            This abstract method must be implemented by derived classes to write
            a preview record to the stream file. A preview is written before test
            execution begins and contains metadata about the test without final
            results. Previews are not included in result totals.

            Preview vs Record:
                - **preview()**: Called before test execution, result_code is UNSET,
                  no detail section, not counted in totals
                - **record()**: Called after test execution, result_code is final,
                  includes detail section with errors/failures, counted in totals

            The preview allows monitoring tools to see which tests are about to run
            and track their progress in real-time.

            :param result: A :class:`ResultNode` object to be previewed. The result's
                           to_json(is_preview=True) method is typically called to
                           generate the preview content.

            :returns: None

            :raises: AbstractMethodError if called on the base ResultRecorder class.
        """
        raise AbstractMethodError("The 'preview' method must be overridden by derived 'ResultRecorder' objects.") from None


    def post_task_progress(self, progress_list: List[ProgressInfo]):
        """
            Posts task progress updates to the running tasks dictionary.

            This method is called by the :class:`ProgressConcentratorServer` when progress
            updates are received from remote workers. It handles thread-safe updates
            to the running_tasks dictionary and optionally triggers summary forwarding.

            Progress Status Handling:
                - **Completed**: Task is removed from running_tasks (task is done)
                - **All other statuses**: Task is added/updated in running_tasks

            Thread Safety:
                This method is fully thread-safe. It acquires the internal lock before
                modifying the running_tasks dictionary, ensuring atomic updates when
                multiple request handler threads submit progress updates concurrently.

            Forwarding Behavior:
                If forwarding_info is configured, this method checks whether the
                forwarding interval has elapsed. If so, it prepares a summary snapshot
                while holding the lock, then forwards it outside the lock to minimize
                lock hold time (network I/O can be slow).

            Example::

                from automojo.testbase.results.model.progressinfo import ProgressInfo
                from automojo.testbase.results.model.progresscode import ProgressCode

                # Create progress update
                progress = ProgressInfo(
                    id="task-123",
                    category="worker",
                    moniker="Processing batch 5",
                    ptype="NumericRange",
                    range_min="0",
                    range_max="100",
                    position="50",
                    status=ProgressCode.Running,
                    when=datetime.now()
                )

                # Post to recorder (thread-safe)
                recorder.post_task_progress([progress])

            :param progress_list: A list of :class:`ProgressInfo` objects to process.
                                  Each object represents a progress update from a
                                  remote worker.

            :returns: None
        """

        fwd_summary = None

        # THREAD-SAFE STATE PATTERN - LOCK PROTECTED MUTATION:
        # Acquire the lock before modifying shared state (_running_tasks).
        # This ensures atomic updates when multiple request handler threads
        # submit progress updates concurrently.
        self._lock.acquire()
        try:

            # PROGRESS STATUS TRACKING:
            # Process each progress update and update the running_tasks dictionary.
            # The status field determines whether to add/update or remove the task.
            for progress in progress_list:

                if hasattr(progress, "status"):
                    # STATUS-BASED STATE MANAGEMENT:
                    # - Completed: Remove task from running_tasks (task is done)
                    # - All other statuses: Update/add task in running_tasks
                    # This maintains an accurate view of currently active tasks.
                    if progress.status == ProgressCode.Completed:
                        # Task completed - remove from running tasks dictionary
                        del self._running_tasks[progress.id]
                    else:
                        # Task still active - update its progress in the dictionary
                        # as_dict() serializes the ProgressInfo for storage
                        self._running_tasks[progress.id] = progress.as_dict()    

            # CONDITIONAL FORWARDING CHECK:
            # If forwarding is configured, check if it's time to forward a summary.
            # We prepare the summary while holding the lock to get a consistent snapshot.
            if self._forwarding_info is not None:
                now_time = datetime.now()
                # Forward if this is the first forward or if the interval has elapsed
                if self._next_forward_at is None or now_time > self._next_forward_at:
                    # Deep copy while holding lock ensures consistent snapshot
                    fwd_summary = copy.deepcopy(self._summary)

        finally:
            # Always release the lock in finally block to prevent deadlocks
            self._lock.release()

        # FORWARDING OUTSIDE LOCK:
        # Perform the actual forwarding outside the lock to minimize lock hold time.
        # Network I/O can be slow, so we don't want to block other threads.
        if fwd_summary is not None:
            self.forward_summary_update(fwd_summary)

        return


    def post_nested_progress(self, progress: NestedProgressInfo) -> NestedProgressInfo:
        """
            Posts a nested progress update to the progress aggregator.

            This method registers or updates a nested progress indicator in the
            progress aggregator, which maintains the hierarchical relationship
            between progress indicators. It also updates the running_tasks
            dictionary for backward compatibility.

            Nested Progress Features:
                - Parent-child relationships between progress indicators
                - Automatic aggregation of child progress into parent metrics
                - Hierarchical progress tree visualization

            Thread Safety:
                This method is thread-safe. The progress aggregator uses internal
                locking, and the running_tasks update is protected by the recorder's
                lock.

            Example::

                # Create a parent progress indicator
                parent_progress = NestedProgressInfo(
                    id="suite-123",
                    category="test-suite",
                    moniker="Integration Tests",
                    ptype=ProgressType.NumericRange,
                    range_min="0",
                    range_max="100",
                    position="0",
                    status=ProgressCode.Running,
                    when=datetime.now(),
                    parent_id=None,
                    depth=0
                )
                recorder.post_nested_progress(parent_progress)

                # Create a child progress indicator
                child_progress = NestedProgressInfo(
                    id="test-456",
                    category="test",
                    moniker="test_login",
                    ptype=ProgressType.Sequential,
                    range_min="0",
                    range_max="1",
                    position="0",
                    status=ProgressCode.Running,
                    when=datetime.now(),
                    parent_id="suite-123",
                    depth=1
                )
                recorder.post_nested_progress(child_progress)

            :param progress: A :class:`NestedProgressInfo` object containing the
                             nested progress update data.

            :returns: The registered NestedProgressInfo instance.

            :rtype: NestedProgressInfo
        """
        # Register with the progress aggregator (handles its own locking)
        registered_progress = self._progress_aggregator.register_progress(progress)

        # Also update running_tasks for backward compatibility
        self._lock.acquire()
        try:
            if progress.status == ProgressCode.Completed:
                if progress.id in self._running_tasks:
                    del self._running_tasks[progress.id]
            else:
                self._running_tasks[progress.id] = progress.as_dict()
        finally:
            self._lock.release()

        return registered_progress


    def get_aggregated_progress(self, progress_id: str) -> Optional[dict]:
        """
            Retrieves aggregated progress metrics for a progress indicator and
            all its descendants.

            This method delegates to the progress aggregator to compute aggregate
            metrics including completion percentage, status counts, and overall
            aggregate status.

            Aggregated Metrics:
                - total_children: Total number of descendant progress indicators
                - completed_count: Number of descendants with Completed status
                - running_count: Number of descendants with Running status
                - pending_count: Number of descendants with NotStarted status
                - errored_count: Number of descendants with Errored status
                - failed_count: Number of descendants with Failed status
                - paused_count: Number of descendants with Paused status
                - completion_percentage: Percentage of completed descendants
                - aggregate_status: Overall status based on child statuses

            Example::

                # Get aggregated progress for a test suite
                aggregated = recorder.get_aggregated_progress("suite-123")
                print(f"Completion: {aggregated['completion_percentage']:.1f}%")
                print(f"Status: {aggregated['aggregate_status']}")

            :param progress_id: The ID of the progress indicator to aggregate.

            :returns: A dictionary containing aggregated metrics, or None if
                      the progress indicator is not found.

            :rtype: Optional[dict]
        """
        return self._progress_aggregator.get_aggregated_progress(progress_id)


    def get_progress_tree(self) -> dict:
        """
            Retrieves the complete progress tree as a nested dictionary structure.

            The returned structure contains root-level progress indicators with
            their children nested recursively. This is useful for visualizing
            the hierarchical progress of distributed tasks.

            Example::

                tree = recorder.get_progress_tree()
                for root in tree["roots"]:
                    print(f"Root: {root['moniker']}")
                    for child in root.get("children", []):
                        print(f"  Child: {child['moniker']}")

            :returns: A dictionary containing the hierarchical progress tree with
                      'roots' (list of root progress nodes) and 'total_count'.

            :rtype: dict
        """
        return self._progress_aggregator.get_progress_tree()


    def get_nested_progress(self, progress_id: str) -> Optional[NestedProgressInfo]:
        """
            Retrieves a nested progress indicator by ID.

            :param progress_id: The ID of the progress indicator to retrieve.

            :returns: The NestedProgressInfo, or None if not found.

            :rtype: Optional[NestedProgressInfo]
        """
        return self._progress_aggregator.get_progress(progress_id)


    def get_child_progress(self, parent_id: str) -> List[NestedProgressInfo]:
        """
            Retrieves all child progress indicators for a given parent.

            :param parent_id: The ID of the parent progress indicator.

            :returns: A list of child NestedProgressInfo objects.

            :rtype: List[NestedProgressInfo]
        """
        return self._progress_aggregator.get_children(parent_id)


    def get_root_progress(self) -> List[NestedProgressInfo]:
        """
            Retrieves all root-level progress indicators (those without parents).

            :returns: A list of root-level NestedProgressInfo objects.

            :rtype: List[NestedProgressInfo]
        """
        return self._progress_aggregator.get_root_progress()


    def clear_nested_progress(self, progress_id: str) -> Optional[NestedProgressInfo]:
        """
            Removes a nested progress indicator and all its descendants.

            This method removes the specified progress indicator from the
            aggregator, along with all its child progress indicators. It also
            removes the progress from the running_tasks dictionary.

            :param progress_id: The ID of the progress indicator to remove.

            :returns: The removed NestedProgressInfo, or None if not found.

            :rtype: Optional[NestedProgressInfo]
        """
        # Remove from aggregator (handles recursive child removal)
        removed = self._progress_aggregator.remove_progress(progress_id)

        # Also remove from running_tasks
        if removed is not None:
            self._lock.acquire()
            try:
                if progress_id in self._running_tasks:
                    del self._running_tasks[progress_id]
            finally:
                self._lock.release()

        return removed


    def record(self, result: ResultNode):
        """
            Records a final result entry for the result object.

            This abstract method must be implemented by derived classes to write
            a final result record to the stream file. A record is written after
            test execution completes and contains the final result code, timing,
            and any errors or failures.

            Record vs Preview:
                - **preview()**: Called before test execution, result_code is UNSET,
                  no detail section, not counted in totals
                - **record()**: Called after test execution, result_code is final,
                  includes detail section with errors/failures, counted in totals

            Thread Safety:
                Derived implementations should use the _lock when updating counters
                to ensure thread-safe operation when multiple tests complete
                concurrently.

            :param result: A :class:`ResultNode` object to be recorded. The result's
                           to_json(is_preview=False) method is typically called to
                           generate the record content.

            :returns: None

            :raises: AbstractMethodError if called on the base ResultRecorder class.
        """
        raise AbstractMethodError("The 'record' method must be overridden by derived 'ResultRecorder' objects.") from None


    def update_render_environment(self):
        """
            Publishes static resources required by the HTML presentation to the results directory.

            This method copies static resources (CSS, JavaScript, images) from the
            configured source directory to the output directory. It only copies files
            that don't already exist in the destination, making it safe to call
            multiple times.

            Resource Copying Behavior:
                - Walks the static_resource_source directory tree
                - For each file, calculates the corresponding destination path
                - Creates destination directories as needed
                - Copies files only if they don't already exist at the destination

            Override Consideration:
                For Jenkins deployments and runs, you might want to override this
                method to not publish resources for each run if they are already
                available at a shared location.

            :returns: None

            :raises: ResultRecordingError if directories cannot be created or files
                     cannot be copied. The error includes the file path, operation
                     description, and underlying exception details.
        """

        if self._render_info.static_resource_source is not None:
            static_resource_dest_dir = self._render_info.static_resource_destination
            static_resource_src_dir = self._render_info.static_resource_source

            for nxt_root, _, nxt_files in os.walk(static_resource_src_dir):
                for nf in nxt_files:
                    res_src_full: str = os.path.join(nxt_root, nf)
                    res_src_leaf = res_src_full[len(static_resource_src_dir):].lstrip(os.sep)
                    res_dest_full = os.path.join(static_resource_dest_dir, res_src_leaf)
                    if not os.path.exists(res_dest_full):
                        dest_dir = os.path.dirname(res_dest_full)
                        if not os.path.exists(dest_dir):
                            try:
                                os.makedirs(dest_dir)
                            except OSError as err:
                                errmsg = f"Failed to create directory '{dest_dir}' for static resources."
                                raise ResultRecordingError(
                                    errmsg,
                                    file_path=dest_dir,
                                    operation="creating static resource directory",
                                    original_error=err
                                ) from err
                        try:
                            shutil.copy2(res_src_full, res_dest_full)
                        except OSError as err:
                            errmsg = f"Failed to copy static resource from '{res_src_full}' to '{res_dest_full}'."
                            raise ResultRecordingError(
                                errmsg,
                                file_path=res_dest_full,
                                operation="copying static resource",
                                original_error=err
                            ) from err

        return


    def update_summary(self): # pylint: disable=no-self-use
        """
            Writes an update to the test run summary file.

            This abstract method must be implemented by derived classes to persist
            the current summary state to the summary file. It is called:

            - During __enter__ to write the initial summary
            - During finalize() to write the final summary
            - Optionally during the test run to provide real-time updates

            The summary file format depends on the derived class implementation
            (e.g., JSON for JsonResultRecorder).

            :returns: None

            :raises: AbstractMethodError if called on the base ResultRecorder class.
        """
        raise AbstractMethodError("The 'update_summary' method must be overridden by derived 'ResultRecorder' objects.") from None


    def write_consolidated_results(self, root_node: dict):
        """
            Writes the consolidated results tree to the output file.

            This abstract method must be implemented by derived classes to persist
            the consolidated result tree to the consolidated results file. It is
            called by consolidate_results() after building the hierarchical tree
            from the stream records.

            :param root_node: A dictionary representing the root of the consolidated
                              result tree (typically a JobContainer with nested
                              TestContainers, TestResults, TaskingGroups, and
                              TaskingResults).

            :returns: None

            :raises: AbstractMethodError if called on the base ResultRecorder class.
        """
        raise AbstractMethodError("The 'write_consolidated_results' method must be overridden by derived 'ResultRecorder' objects.") from None

