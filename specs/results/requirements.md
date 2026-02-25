# Result Recording and Reporting - Requirements Document

## Introduction

The Result Recording and Reporting system is responsible for capturing, persisting, and organizing test execution outcomes in the TestBase framework. It provides a hierarchical result model that mirrors the test execution structure, streaming result recording for real-time progress tracking, result consolidation for post-run analysis and reporting, progress tracking and forwarding for distributed test execution, and support for multiple output formats through extensible recorder implementations. The system operates through three primary layers: the Data Model (result types and containers), the Recording Layer (result recorders), and the Aggregation Layer (progress concentrators).

## Glossary

- **ResultRecorder**: The base class that establishes the API patterns for recording test results, managing the test run lifecycle, result counting, and summary generation
- **JsonResultRecorder**: A concrete implementation of ResultRecorder that records test results in JSON format
- **ResultNode**: A base class for result nodes that contain actual result data from tasks, tests, or steps in a result tree
- **ResultContainer**: A base class for container nodes that link result nodes in the result tree without containing result data
- **TestResult**: A specialized ResultNode for recording individual test execution outcomes with monikers and pivots
- **TaskingResult**: A specialized ResultNode for recording distributed task execution outcomes with worker information
- **JobContainer**: The root-level ResultContainer for an entire test run session
- **TestContainer**: A ResultContainer for module-level test groupings
- **TaskingGroup**: A ResultContainer for grouping related tasking results within a test
- **ResultCode**: An enumeration summarizing result outcomes (UNSET, PASSED, SKIPPED, ERRORED, FAILED, CANCELLED, UNKNOWN)
- **ResultType**: An enumeration marking the type of result (JOB, PACKAGE, SCOPE, TASK_CONTAINER, TASK, TEST_CONTAINER, TEST, STEP_CONTAINER, STEP, TASKING_GROUP, TASKING)
- **BuildInfo**: A dataclass containing build metadata (branch, build, flavor, release, url)
- **PipelineInfo**: A dataclass containing pipeline metadata (id, name, instance)
- **JobInfo**: A dataclass containing job execution metadata (id, name, type, owner, label, initiator, venue, seed, tag)
- **RenderInfo**: A dataclass containing output file paths and rendering configuration
- **ForwardingInfo**: A dataclass containing progress forwarding configuration (interval, url, headers)
- **ProgressInfo**: A dataclass representing a single progress update event with status and position
- **ProgressCode**: An enumeration of task progress states (Completed, Errored, Failed, NotStarted, Paused, Running)
- **ProgressType**: An enumeration of progress tracking modes (NumericRange, Sequential, TimeSpan)
- **ProgressConcentratorServer**: An HTTP server that receives and concentrates progress callbacks from remote tasks
- **TracebackDetail**: A structured representation of exception traceback information
- **JSOS**: JSON Separated Object Stream format used for streaming results
- **Catalog_Tree**: A utility function that generates JSON catalog files for directory navigation

## Requirements

### Requirement 1: Result Code Enumeration

**User Story:** As a framework developer, I want a standardized set of result codes, so that test outcomes can be consistently categorized.

#### Acceptance Criteria

1. THE ResultCode enumeration SHALL define UNSET with value 0 as the initial state
2. THE ResultCode enumeration SHALL define PASSED with value 1 for successful tests
3. THE ResultCode enumeration SHALL define SKIPPED with value 2 for intentionally skipped tests
4. THE ResultCode enumeration SHALL define ERRORED with value 3 for tests with infrastructure errors
5. THE ResultCode enumeration SHALL define FAILED with value 4 for tests with assertion failures
6. THE ResultCode enumeration SHALL define CANCELLED with value 5 for cancelled tests
7. THE ResultCode enumeration SHALL define UNKNOWN with value 6 for indeterminate outcomes
8. THE ResultCode enumeration SHALL be an IntEnum for numeric comparison support

### Requirement 2: Result Type Enumeration

**User Story:** As a framework developer, I want a standardized set of result types, so that result hierarchy nodes can be properly classified.

#### Acceptance Criteria

1. THE ResultType enumeration SHALL define JOB with value 0 for root-level job containers
2. THE ResultType enumeration SHALL define PACKAGE with value 1 for package-level groupings
3. THE ResultType enumeration SHALL define SCOPE with value 2 for scope-level groupings
4. THE ResultType enumeration SHALL define TASK_CONTAINER with value 3 for task container nodes
5. THE ResultType enumeration SHALL define TASK with value 4 for individual task results
6. THE ResultType enumeration SHALL define TEST_CONTAINER with value 5 for test container nodes
7. THE ResultType enumeration SHALL define TEST with value 6 for individual test results
8. THE ResultType enumeration SHALL define STEP_CONTAINER with value 7 for step container nodes
9. THE ResultType enumeration SHALL define STEP with value 8 for individual step results
10. THE ResultType enumeration SHALL define TASKING_GROUP with value 9 for tasking group containers
11. THE ResultType enumeration SHALL define TASKING with value 10 for individual tasking results
12. THE ResultType enumeration SHALL be an IntEnum for numeric comparison support

### Requirement 3: ResultNode Base Class

**User Story:** As a framework developer, I want a base class for result nodes, so that common result data and behavior is shared across result types.

#### Acceptance Criteria

1. THE ResultNode class SHALL accept inst_id, name, parent_inst, result_type, and optional result_code parameters in its constructor
2. THE ResultNode class SHALL initialize start timestamp to datetime.now() on construction
3. THE ResultNode class SHALL initialize stop timestamp to None on construction
4. THE ResultNode class SHALL initialize empty lists for errors, failures, and warnings
5. THE ResultNode class SHALL initialize docstr to None on construction
6. THE ResultNode class SHALL provide read-only properties for inst_id, name, parent_inst, result_type, result_code, start, stop, errors, failures, warnings, and docstr

### Requirement 4: ResultNode Error and Failure Tracking

**User Story:** As a framework developer, I want to track errors and failures on result nodes, so that test issues are properly recorded.

#### Acceptance Criteria

1. THE ResultNode class SHALL provide an add_error method that accepts a TracebackDetail and appends it to the errors list
2. THE ResultNode class SHALL provide an add_failure method that accepts a TracebackDetail and appends it to the failures list
3. THE ResultNode class SHALL provide an add_warning method that accepts warning lines and appends them to the warnings list
4. WHEN add_warning is called, THE System SHALL trim and normalize line endings in the warning lines
5. WHEN add_warning is called with multi-line strings, THE System SHALL split them into individual lines

### Requirement 5: ResultNode Finalization

**User Story:** As a framework developer, I want result nodes to finalize their result code, so that the final outcome is determined from errors and failures.

#### Acceptance Criteria

1. THE ResultNode class SHALL provide a finalize method that sets the stop timestamp to datetime.now()
2. WHEN finalize is called and failures list is not empty, THE System SHALL set result_code to FAILED
3. WHEN finalize is called and errors list is not empty (but no failures), THE System SHALL set result_code to ERRORED
4. WHEN finalize is called with no errors or failures and result_code is UNSET or PASSED, THE System SHALL set result_code to PASSED
5. WHEN finalize is called with no errors or failures and result_code is neither UNSET nor PASSED, THE System SHALL set result_code to UNKNOWN

### Requirement 6: ResultNode Serialization

**User Story:** As a framework developer, I want result nodes to serialize to dictionary and JSON, so that results can be persisted and transmitted.

#### Acceptance Criteria

1. THE ResultNode class SHALL provide an as_dict method that returns an OrderedDict representation
2. THE as_dict method SHALL include name, instance, parent, rtype, result, start, and stop fields
3. WHEN as_dict is called with is_preview=False, THE System SHALL include a detail section with errors, failures, warnings, and optional documentation
4. WHEN as_dict is called with is_preview=True, THE System SHALL exclude the detail section
5. THE ResultNode class SHALL provide a to_json method that returns a JSON string representation
6. THE to_json method SHALL accept an is_preview parameter to control detail inclusion

### Requirement 7: ResultNode Status Methods

**User Story:** As a framework developer, I want methods to mark result status, so that test outcomes can be explicitly set.

#### Acceptance Criteria

1. THE ResultNode class SHALL provide a mark_passed method that sets result_code to PASSED
2. THE ResultNode class SHALL provide a set_documentation method that sets the docstr property

### Requirement 8: ResultContainer Base Class

**User Story:** As a framework developer, I want a base class for result containers, so that hierarchy nodes can link result nodes without containing result data.

#### Acceptance Criteria

1. THE ResultContainer class SHALL accept inst_id, name, result_type, and optional parent_inst parameters in its constructor
2. THE ResultContainer class SHALL provide read-only properties for inst_id, name, parent_inst, and result_type
3. THE ResultContainer class SHALL provide an as_dict method that returns an OrderedDict with name, instance, parent, and rtype fields
4. THE ResultContainer class SHALL provide a to_json method that returns a JSON string representation

### Requirement 9: JobContainer Implementation

**User Story:** As a framework developer, I want a job container class, so that the root of a result tree can be properly represented.

#### Acceptance Criteria

1. THE JobContainer class SHALL inherit from ResultContainer
2. THE JobContainer class SHALL accept inst_id and name parameters in its constructor
3. THE JobContainer class SHALL set result_type to ResultType.JOB
4. THE JobContainer class SHALL set parent_inst to None (root node has no parent)

### Requirement 10: TestContainer Implementation

**User Story:** As a framework developer, I want a test container class, so that module-level test groupings can be represented.

#### Acceptance Criteria

1. THE TestContainer class SHALL inherit from ResultContainer
2. THE TestContainer class SHALL accept inst_id, name, and parent_inst parameters in its constructor
3. THE TestContainer class SHALL set result_type to ResultType.TEST_CONTAINER

### Requirement 11: TaskingGroup Implementation

**User Story:** As a framework developer, I want a tasking group class, so that related tasking results can be grouped within a test.

#### Acceptance Criteria

1. THE TaskingGroup class SHALL inherit from ResultContainer
2. THE TaskingGroup class SHALL accept inst_id, name, and parent_inst parameters in its constructor
3. THE TaskingGroup class SHALL set result_type to ResultType.TASKING_GROUP
4. THE TaskingGroup class SHALL initialize start timestamp to datetime.now() on construction
5. THE TaskingGroup class SHALL initialize stop timestamp to None on construction
6. THE TaskingGroup class SHALL provide a finalize method that sets stop timestamp to datetime.now()
7. THE TaskingGroup class SHALL override as_dict to include start and stop timestamps

### Requirement 12: TestResult Implementation

**User Story:** As a test developer, I want a test result class, so that individual test execution outcomes can be recorded with parameterization data.

#### Acceptance Criteria

1. THE TestResult class SHALL inherit from ResultNode
2. THE TestResult class SHALL accept inst_id, name, parent_inst, monikers, pivots, and optional result_code parameters
3. THE TestResult class SHALL set result_type to ResultType.TEST
4. THE TestResult class SHALL provide read-only properties for monikers and pivots
5. THE TestResult class SHALL provide a mark_skip method that accepts reason and bug parameters and sets result_code to SKIPPED
6. THE TestResult class SHALL override as_dict to include monikers and pivots fields
7. WHEN as_dict is called with is_preview=False and reason is set, THE System SHALL include reason in the detail section
8. WHEN as_dict is called with is_preview=False and bug is set, THE System SHALL include bug in the detail section

### Requirement 13: TaskingResult Implementation

**User Story:** As a framework developer, I want a tasking result class, so that distributed task execution outcomes can be recorded.

#### Acceptance Criteria

1. THE TaskingResult class SHALL inherit from ResultNode
2. THE TaskingResult class SHALL accept inst_id, name, parent_inst, worker, optional rvalue, optional result_code, and optional prefix parameters
3. THE TaskingResult class SHALL set result_type to ResultType.TASKING
4. THE TaskingResult class SHALL provide read-only properties for worker, prefix, and rvalue
5. THE TaskingResult class SHALL provide an add_return_value method that sets the rvalue property
6. THE TaskingResult class SHALL override as_dict to include prefix, worker, and rvalue fields
7. WHEN rvalue has an as_dict method, THE System SHALL call it for serialization
8. THE TaskingResult class SHALL provide a format_result method that returns formatted output lines

### Requirement 14: Tasking Result Verification

**User Story:** As a framework developer, I want to verify tasking results, so that distributed task failures are properly detected and reported.

#### Acceptance Criteria

1. THE verify_tasking_results function SHALL accept results list, context_message, optional group_name, and optional result_formatter parameters
2. WHEN any tasking has UNKNOWN result code, THE System SHALL raise TaskingGroupRuntimeError
3. WHEN any tasking has CANCELLED result code, THE System SHALL raise TaskingGroupRuntimeError
4. WHEN any tasking has ERRORED result code, THE System SHALL raise TaskingGroupRuntimeError with formatted error details
5. WHEN any tasking has FAILED result code, THE System SHALL raise TaskingGroupAssertionError with formatted failure details
6. WHEN all taskings have PASSED result code, THE System SHALL return without raising an exception

### Requirement 15: Build Information Metadata

**User Story:** As a test developer, I want to associate build information with test results, so that results can be correlated with specific builds.

#### Acceptance Criteria

1. THE BuildInfo dataclass SHALL define branch field for code branch name
2. THE BuildInfo dataclass SHALL define build field for product build identifier
3. THE BuildInfo dataclass SHALL define flavor field for build flavor label
4. THE BuildInfo dataclass SHALL define release field for release name
5. THE BuildInfo dataclass SHALL define url field for build URL

### Requirement 16: Pipeline Information Metadata

**User Story:** As a test developer, I want to associate pipeline information with test results, so that results can be correlated with CI/CD pipelines.

#### Acceptance Criteria

1. THE PipelineInfo dataclass SHALL define id field for pipeline identifier
2. THE PipelineInfo dataclass SHALL define name field for pipeline name
3. THE PipelineInfo dataclass SHALL define instance field for pipeline instance identifier

### Requirement 17: Job Information Metadata

**User Story:** As a test developer, I want to associate job information with test results, so that results can be correlated with specific job executions.

#### Acceptance Criteria

1. THE JobInfo dataclass SHALL define id field for job identifier
2. THE JobInfo dataclass SHALL define name field for job name
3. THE JobInfo dataclass SHALL define type field for job type
4. THE JobInfo dataclass SHALL define optional owner field for job owner
5. THE JobInfo dataclass SHALL define optional label field for job label
6. THE JobInfo dataclass SHALL define optional initiator field for job initiator
7. THE JobInfo dataclass SHALL define optional venue field for execution venue
8. THE JobInfo dataclass SHALL define optional seed field for randomization seed
9. THE JobInfo dataclass SHALL define optional tag field for correlation tag

### Requirement 18: Render Information Configuration

**User Story:** As a framework developer, I want render configuration, so that output file paths and templates can be specified.

#### Acceptance Criteria

1. THE RenderInfo dataclass SHALL define title field for test run summary title
2. THE RenderInfo dataclass SHALL define summary_filename field for summary JSON file path
3. THE RenderInfo dataclass SHALL define summary_template field for HTML template path
4. THE RenderInfo dataclass SHALL define stream_results_filename field for streaming results file path
5. THE RenderInfo dataclass SHALL define consolidated_results_filename field for consolidated results file path
6. THE RenderInfo dataclass SHALL define static_resource_source field for static resource source directory
7. THE RenderInfo dataclass SHALL define static_resource_destination field for static resource destination directory

### Requirement 19: Forwarding Information Configuration

**User Story:** As a framework developer, I want forwarding configuration, so that progress can be forwarded to external services.

#### Acceptance Criteria

1. THE ForwardingInfo dataclass SHALL define forwarding_interval field for forwarding interval in seconds
2. THE ForwardingInfo dataclass SHALL define forwarding_url field for forwarding destination URL
3. THE ForwardingInfo dataclass SHALL define optional forwarding_headers field for HTTP headers

### Requirement 20: Progress Code Enumeration

**User Story:** As a framework developer, I want progress status codes, so that task progress can be consistently categorized.

#### Acceptance Criteria

1. THE ProgressCode enumeration SHALL define Completed for finished tasks
2. THE ProgressCode enumeration SHALL define Errored for tasks with errors
3. THE ProgressCode enumeration SHALL define Failed for tasks with failures
4. THE ProgressCode enumeration SHALL define NotStarted for pending tasks
5. THE ProgressCode enumeration SHALL define Paused for suspended tasks
6. THE ProgressCode enumeration SHALL define Running for active tasks
7. THE ProgressCode enumeration SHALL be a string-based Enum

### Requirement 21: Progress Type Enumeration

**User Story:** As a framework developer, I want progress tracking modes, so that different progress measurement approaches can be used.

#### Acceptance Criteria

1. THE ProgressType enumeration SHALL define NumericRange for numeric progress tracking
2. THE ProgressType enumeration SHALL define Sequential for sequential step tracking
3. THE ProgressType enumeration SHALL define TimeSpan for time-based progress tracking
4. THE ProgressType enumeration SHALL be a string-based Enum

### Requirement 22: Progress Information Data

**User Story:** As a framework developer, I want progress information representation, so that progress updates can be captured and transmitted.

#### Acceptance Criteria

1. THE ProgressInfo dataclass SHALL define id field for progress identifier
2. THE ProgressInfo dataclass SHALL define category field for progress category
3. THE ProgressInfo dataclass SHALL define moniker field for human-readable identifier
4. THE ProgressInfo dataclass SHALL define ptype field for progress type
5. THE ProgressInfo dataclass SHALL define range_min and range_max fields for progress bounds
6. THE ProgressInfo dataclass SHALL define position field for current progress position
7. THE ProgressInfo dataclass SHALL define status field for progress status code
8. THE ProgressInfo dataclass SHALL define when field for timestamp
9. THE ProgressInfo dataclass SHALL define optional data field for additional data
10. THE ProgressInfo class SHALL provide an as_dict method for dictionary serialization
11. THE ProgressInfo class SHALL provide a from_dict class method for deserialization

### Requirement 23: ResultRecorder Base Class

**User Story:** As a framework developer, I want a base recorder class, so that common recording functionality is shared across recorder implementations.

#### Acceptance Criteria

1. THE ResultRecorder class SHALL accept runid, start, render_info, and optional apod, build_info, pipeline_info, job_info, and forwarding_info parameters
2. THE ResultRecorder class SHALL initialize result counters (error_count, failure_count, pass_count, skip_count, unknown_count, total_count) to zero
3. THE ResultRecorder class SHALL initialize a summary OrderedDict with version, title, runid, build, pipeline, job, start, stop, result, apod, totals, and running fields
4. THE ResultRecorder class SHALL initialize a threading lock for thread-safe operations
5. THE ResultRecorder class SHALL provide a summary property that returns a thread-safe copy of the summary

### Requirement 24: ResultRecorder Context Manager

**User Story:** As a framework developer, I want the recorder to work as a context manager, so that recording lifecycle is properly managed.

#### Acceptance Criteria

1. THE ResultRecorder class SHALL implement __enter__ that calls initialize_report, update_summary, and opens the stream results file
2. THE ResultRecorder class SHALL implement __exit__ that calls finalize if not already finalized
3. THE __enter__ method SHALL return self for use in with statements
4. THE __exit__ method SHALL handle exceptions gracefully

### Requirement 25: ResultRecorder Initialization

**User Story:** As a framework developer, I want recorder initialization to set up the output environment, so that results can be properly stored.

#### Acceptance Criteria

1. THE initialize_report method SHALL call update_render_environment to publish static resources
2. THE initialize_report method SHALL copy the summary template to the output directory
3. THE initialize_report method SHALL call catalog_output_directory to generate catalog files
4. THE update_render_environment method SHALL copy static resources from source to destination if configured

### Requirement 26: ResultRecorder Finalization

**User Story:** As a framework developer, I want recorder finalization to complete the test run, so that final results are properly recorded.

#### Acceptance Criteria

1. THE finalize method SHALL set the finalized flag to True
2. THE finalize method SHALL set the stop timestamp to datetime.now()
3. THE finalize method SHALL update the summary with stop time and detail counts
4. THE finalize method SHALL set summary result to "FAILED" if error_count or failure_count is greater than zero
5. THE finalize method SHALL set summary result to "PASSED" if no errors or failures
6. THE finalize method SHALL close the stream results file
7. THE finalize method SHALL call update_summary to persist the final summary
8. THE finalize method SHALL be thread-safe using the lock

### Requirement 27: ResultRecorder Abstract Methods

**User Story:** As a framework developer, I want abstract methods in the base recorder, so that derived classes must implement format-specific behavior.

#### Acceptance Criteria

1. THE ResultRecorder class SHALL define an abstract preview method for writing result previews
2. THE ResultRecorder class SHALL define an abstract record method for writing final results
3. THE ResultRecorder class SHALL define an abstract update_summary method for persisting summary updates
4. THE ResultRecorder class SHALL define an abstract write_consolidated_results method for writing consolidated results
5. WHEN abstract methods are called on the base class, THE System SHALL raise AbstractMethodError

### Requirement 28: ResultRecorder Progress Tracking

**User Story:** As a framework developer, I want progress tracking in the recorder, so that running task status can be monitored.

#### Acceptance Criteria

1. THE ResultRecorder class SHALL maintain a running_tasks dictionary for active task progress
2. THE post_task_progress method SHALL accept a list of ProgressInfo objects
3. WHEN a progress status is Completed, THE System SHALL remove the task from running_tasks
4. WHEN a progress status is not Completed, THE System SHALL update the task in running_tasks
5. THE post_task_progress method SHALL be thread-safe using the lock
6. THE clear_task_progress method SHALL remove specified task IDs from running_tasks

### Requirement 29: ResultRecorder Result Consolidation

**User Story:** As a framework developer, I want result consolidation, so that streaming results can be rolled up into a hierarchical document.

#### Acceptance Criteria

1. THE consolidate_results method SHALL load the result stream using load_result_stream
2. THE consolidate_results method SHALL build a hierarchical tree from the stream records
3. WHEN a JOB record is encountered, THE System SHALL set it as the root node
4. WHEN a TEST_CONTAINER record is encountered, THE System SHALL append it to the parent's items list
5. WHEN a TEST record is encountered, THE System SHALL append it to the parent's items list and initialize tasking_groups
6. WHEN a TASKING_GROUP record is encountered, THE System SHALL append it to the parent's tasking_groups list and initialize taskings
7. WHEN a TASKING record is encountered, THE System SHALL append it to the parent's taskings list
8. THE consolidate_results method SHALL call write_consolidated_results with the root node

### Requirement 30: ResultRecorder Summary Formatting

**User Story:** As a test developer, I want formatted summary output, so that test run results can be displayed in a readable format.

#### Acceptance Criteria

1. THE format_lines method SHALL return a list of formatted summary lines
2. THE format_lines method SHALL include title, release, branch, build, flavor, owner, runid, start, stop
3. THE format_lines method SHALL include detail section with errors, failed, skipped, passed, and total counts
4. THE format_lines method SHALL include the overall result status
5. THE format_lines method SHALL include the output path
6. WHEN AM_SUMMARY_URL environment variable is set, THE format_lines method SHALL include the summary URL

### Requirement 31: ResultRecorder Catalog Generation

**User Story:** As a framework developer, I want catalog generation, so that HTML reports can navigate the output directory structure.

#### Acceptance Criteria

1. THE catalog_output_directory method SHALL call catalog_tree on the output directory
2. THE catalog_tree function SHALL create catalog.json files in each directory
3. THE catalog.json file SHALL contain files and folders arrays
4. THE catalog_tree function SHALL skip directories in the dont_catalog_dirs list
5. THE catalog_tree function SHALL not descend into directories in the dont_descend_dirs list
6. THE default dont_catalog_dirs list SHALL include "__pycache__"
7. THE default dont_descend_dirs list SHALL include "diagnostics"

### Requirement 32: JsonResultRecorder Implementation

**User Story:** As a framework developer, I want a JSON result recorder, so that results can be persisted in JSON format.

#### Acceptance Criteria

1. THE JsonResultRecorder class SHALL inherit from ResultRecorder
2. THE JsonResultRecorder class SHALL implement the preview method to write JSON preview records
3. THE JsonResultRecorder class SHALL implement the record method to write JSON final records
4. THE JsonResultRecorder class SHALL implement the update_summary method to write JSON summary
5. THE JsonResultRecorder class SHALL implement the write_consolidated_results method to write consolidated JSON

### Requirement 33: JsonResultRecorder Preview Recording

**User Story:** As a framework developer, I want preview recording, so that test execution can be tracked before completion.

#### Acceptance Criteria

1. THE preview method SHALL convert the result to JSON using to_json with is_preview=True
2. THE preview method SHALL write a record separator before the JSON content
3. THE preview method SHALL flush the output stream after writing
4. THE preview method SHALL call catalog_output_directory after writing

### Requirement 34: JsonResultRecorder Result Recording

**User Story:** As a framework developer, I want result recording, so that completed test results are persisted.

#### Acceptance Criteria

1. THE record method SHALL convert the result to JSON using to_json with is_preview=False
2. THE record method SHALL write a record separator before the JSON content
3. THE record method SHALL flush the output stream after writing
4. WHEN the result type is TEST, THE System SHALL increment total_count
5. WHEN the result code is PASSED, THE System SHALL increment pass_count
6. WHEN the result code is ERRORED, THE System SHALL increment error_count
7. WHEN the result code is FAILED, THE System SHALL increment failure_count
8. WHEN the result code is SKIPPED, THE System SHALL increment skip_count
9. WHEN the result code is other, THE System SHALL increment unknown_count
10. THE record method SHALL be thread-safe using the lock
11. THE record method SHALL call catalog_output_directory after writing

### Requirement 35: JsonResultRecorder Summary Update

**User Story:** As a framework developer, I want summary updates, so that the current test run status is persisted.

#### Acceptance Criteria

1. THE update_summary method SHALL write the summary to the summary_filename as JSON
2. THE update_summary method SHALL use JsonResultEncoder for datetime serialization
3. THE update_summary method SHALL use indent=4 for readable formatting
4. THE update_summary method SHALL call catalog_output_directory after writing

### Requirement 36: JsonResultRecorder Consolidated Results

**User Story:** As a framework developer, I want consolidated results output, so that the complete result tree is available for reporting.

#### Acceptance Criteria

1. THE write_consolidated_results method SHALL write the root_node to consolidated_results_filename as JSON
2. THE write_consolidated_results method SHALL use JsonResultEncoder for datetime serialization
3. THE write_consolidated_results method SHALL use indent=4 for readable formatting
4. THE write_consolidated_results method SHALL call catalog_output_directory after writing

### Requirement 37: JSON Result Encoder

**User Story:** As a framework developer, I want custom JSON encoding, so that datetime objects are properly serialized.

#### Acceptance Criteria

1. THE JsonResultEncoder class SHALL inherit from json.JSONEncoder
2. THE JsonResultEncoder class SHALL override the default method
3. WHEN encoding a datetime object, THE System SHALL return the ISO format string
4. WHEN encoding other objects, THE System SHALL delegate to the parent encoder

### Requirement 38: Progress Concentrator Server

**User Story:** As a framework developer, I want a progress concentrator server, so that remote tasks can report progress.

#### Acceptance Criteria

1. THE ProgressConcentratorServer class SHALL inherit from ThreadingMixIn and HTTPServer
2. THE ProgressConcentratorServer class SHALL accept recorder, server_address, optional forwarding_info, and bind_and_activate parameters
3. THE ProgressConcentratorServer class SHALL use ProgressCallbackHandler for request handling
4. THE ProgressConcentratorServer class SHALL provide a start method that starts the server thread
5. WHEN forwarding_info is provided, THE start method SHALL also start a forwarding thread

### Requirement 39: Progress Callback Handler

**User Story:** As a framework developer, I want a progress callback handler, so that HTTP POST requests with progress data are processed.

#### Acceptance Criteria

1. THE ProgressCallbackHandler class SHALL inherit from SimpleHTTPRequestHandler
2. THE ProgressCallbackHandler class SHALL implement do_POST to handle progress updates
3. WHEN a POST request is received, THE System SHALL parse the JSON content
4. WHEN a POST request is received, THE System SHALL create a ProgressInfo from the data
5. WHEN a POST request is received, THE System SHALL call update_task_progress on the server
6. WHEN processing succeeds, THE System SHALL return HTTP 200
7. WHEN processing fails, THE System SHALL return HTTP 500 with error message

### Requirement 40: Progress Forwarding Thread

**User Story:** As a framework developer, I want progress forwarding, so that summary updates are sent to external services.

#### Acceptance Criteria

1. THE forwarding thread SHALL run as a daemon thread
2. THE forwarding thread SHALL periodically get the summary from the recorder
3. THE forwarding thread SHALL POST the summary to the forwarding_url
4. THE forwarding thread SHALL use the configured forwarding_interval between posts
5. THE forwarding thread SHALL include forwarding_headers in the POST request if configured
6. THE forwarding thread SHALL log errors and continue on failure

### Requirement 41: Thread Safety

**User Story:** As a framework developer, I want thread-safe operations, so that concurrent test execution does not corrupt results.

#### Acceptance Criteria

1. THE ResultRecorder class SHALL use a threading.Lock for protecting shared state
2. THE summary property SHALL acquire the lock before copying the summary
3. THE post_task_progress method SHALL acquire the lock before updating running_tasks
4. THE clear_task_progress method SHALL acquire the lock before removing tasks
5. THE finalize method SHALL acquire the lock before updating counters and summary
6. THE record method in JsonResultRecorder SHALL acquire the lock before updating counters

### Requirement 42: Output File Structure

**User Story:** As a test developer, I want a consistent output file structure, so that results can be easily located and processed.

#### Acceptance Criteria

1. THE output directory SHALL contain testsummary.html for the HTML summary page
2. THE output directory SHALL contain testsummary.json for the JSON summary data
3. THE output directory SHALL contain testresults_stream.jsos for streaming results
4. THE output directory SHALL contain testresults.json for consolidated results
5. THE output directory SHALL contain catalog.json for directory navigation
6. THE output directory SHALL contain a static subdirectory for static resources

### Requirement 43: Tasking Result Formatter Protocol

**User Story:** As a framework developer, I want a formatter protocol, so that tasking result formatting can be customized.

#### Acceptance Criteria

1. THE TaskingResultFormatter protocol SHALL define a __call__ method accepting a TaskingResult and returning List[str]
2. THE default_tasking_result_formatter function SHALL format task name, worker, instance, parent, rtype, result, start, stop
3. THE default_tasking_result_formatter function SHALL format errors with traceback details
4. THE default_tasking_result_formatter function SHALL format failures with traceback details
5. THE verify_tasking_results function SHALL accept an optional result_formatter parameter

### Requirement 44: Progress Delivery Configuration

**User Story:** As a framework developer, I want progress delivery configuration, so that progress callbacks can be customized.

#### Acceptance Criteria

1. THE ProgressDeliveryMethod class SHALL define SUMMARY_PULL_PROGRESS constant
2. THE TaskingProgressCallback protocol SHALL define a __call__ method accepting List[ProgressInfo]
3. THE SummaryProgressDelivery dataclass SHALL define progress_interval and progress_callback fields
