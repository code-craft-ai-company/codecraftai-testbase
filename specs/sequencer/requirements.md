# Sequencer Scopes - Requirements Document

## Introduction

The Sequencer Scopes system provides hierarchical execution context management for the TestBase framework. It defines a set of scope context managers that control the lifecycle of test execution at different granularity levels: session, module, test setup, and individual test. The system is responsible for managing hierarchical scope contexts during test execution, tracking scope identity through a scope stack mechanism, coordinating result recording at each scope level, handling exceptions and propagating failure states to descendant tests, supporting activity tracking within test scopes, and enabling debuggable, reproducible test execution flows.

## Glossary

- **TestSequencer**: The central state machine that orchestrates test discovery, collection, and execution flow through distinct phases
- **SequencerScopeBase**: The abstract base context manager class for all sequencer scope implementations providing shared infrastructure for scope management
- **SequencerSessionScope**: The context manager for the root session scope of a test run, encompassing the entire test execution
- **SequencerModuleScope**: The context manager for module-level test groupings, managing execution context for a Python test module
- **SequencerTestSetupScope**: The context manager for test preparation and test-local parameter creation
- **SequencerTestScope**: The context manager for executing a single test function with result recording
- **TestActivity**: A class that records timing information for test activities within a test scope
- **Scope_Stack**: A list structure maintained by the sequencer for tracking the current execution context hierarchy
- **Scope_ID**: A unique UUID identifier assigned to each scope instance during execution
- **Scope_Name**: A string identifier for a scope following naming conventions (e.g., `<session>`, `package.module`, `setup:test_name`)
- **Context_Identifier**: A string combining test name and parameter monikers to distinguish parameterized test instances
- **ResultRecorder**: The component responsible for recording test results during execution
- **JobContainer**: The root-level result container for an entire test run session
- **TestContainer**: A result container for module-level test groupings
- **TestResult**: A result node for an individual test execution
- **TestGroup**: A composite node in the test tree representing a collection of tests (module or package)
- **TestRef**: A leaf node in the test tree representing an individual test reference
- **Notables**: A dictionary of parameterized test values used for test identification
- **Monikers**: Human-readable identifiers derived from notables for test instances
- **Pivots**: Structured data representation of parameterized test values
- **SkipError**: An exception type indicating a test should be intentionally skipped
- **TracebackDetail**: A structured representation of exception traceback information
- **JSOS**: JSON Separated Object Stream format used for activity recording
- **IOutputContext**: The injected seam through which the sequencer resolves run artefact locations (test results, diagnostics, per-testcase by-products). The default implementation is `SimpleOutputContext`, which roots artefacts under a single base directory. Replaces the use of `get_path_for_*`, `RuntimeVariables`, and `ThisApplicationSingleton` in the sequencer core.
- **environment**: The dependency-free `ccai.testbase.environment` module that reads core env knobs (including `AM_DIAGNOSTICS_PRERUN` / `AM_DIAGNOSTICS_POSTRUN`) from `os.environ`, providing gating helpers such as `diagnostics_prerun_enabled()` and `diagnostics_postrun_enabled()`.

## Requirements

### Requirement 1: Scope Hierarchy Structure

**User Story:** As a framework developer, I want a hierarchical scope structure, so that test execution contexts are properly nested and managed.

#### Acceptance Criteria

1. THE Sequencer_Scopes_System SHALL support a four-level hierarchy: Session, Module, Test Setup, and Test
2. THE SequencerSessionScope SHALL serve as the root scope encompassing the entire test run
3. THE SequencerModuleScope SHALL be nested within the session scope for each test module
4. THE SequencerTestSetupScope SHALL be optionally nested within a module scope for test-local parameter creation
5. THE SequencerTestScope SHALL be nested within either a module scope or test setup scope for individual test execution
6. WHEN a scope is entered, THE System SHALL establish a parent-child relationship with the enclosing scope

### Requirement 2: SequencerScopeBase Foundation

**User Story:** As a framework developer, I want a base class for scope context managers, so that common functionality is shared across all scope types.

#### Acceptance Criteria

1. THE SequencerScopeBase class SHALL accept sequencer and recorder parameters in its constructor
2. THE SequencerScopeBase class SHALL store references to the sequencer and recorder for use by derived classes
3. THE SequencerScopeBase class SHALL provide a _mark_descendants_as_error method for marking child tests as errored
4. THE SequencerScopeBase class SHALL provide a _mark_descendants_skipped method for marking child tests as skipped
5. THE SequencerScopeBase class SHALL provide a _mark_test_as_error method for marking a single test as errored
6. THE SequencerScopeBase class SHALL provide a _mark_test_as_skip method for marking a single test as skipped

### Requirement 3: Descendant Error Propagation

**User Story:** As a framework developer, I want scope failures to propagate to descendant tests, so that all affected tests are properly marked.

#### Acceptance Criteria

1. WHEN _mark_descendants_as_error is called, THE System SHALL traverse all children of the cursor node
2. WHEN a child is a TestRef and not finalized, THE System SHALL call _mark_test_as_error for that test
3. WHEN a child is a TestGroup and not finalized, THE System SHALL create a TestContainer result and recurse into the group
4. THE _mark_descendants_as_error method SHALL accept cursor, cursor_id, and tbdetail parameters
5. WHEN creating TestContainer results during error propagation, THE System SHALL generate a new UUID for each container

### Requirement 4: Descendant Skip Propagation

**User Story:** As a framework developer, I want skip conditions to propagate to descendant tests, so that all affected tests are properly marked as skipped.

#### Acceptance Criteria

1. WHEN _mark_descendants_skipped is called, THE System SHALL traverse all children of the cursor node
2. WHEN a child is a TestRef and not finalized, THE System SHALL call _mark_test_as_skip for that test
3. WHEN a child is a TestGroup and not finalized, THE System SHALL create a TestContainer result and recurse into the group
4. THE _mark_descendants_skipped method SHALL accept cursor, cursor_id, reason, and bug parameters
5. WHEN creating TestContainer results during skip propagation, THE System SHALL generate a new UUID for each container

### Requirement 5: Individual Test Error Marking

**User Story:** As a framework developer, I want to mark individual tests as errored, so that test results accurately reflect infrastructure failures.

#### Acceptance Criteria

1. THE _mark_test_as_error method SHALL create a new TestResult node with a generated UUID
2. THE _mark_test_as_error method SHALL call add_error on the result with the traceback detail
3. THE _mark_test_as_error method SHALL finalize the result after adding the error
4. THE _mark_test_as_error method SHALL record the result using the recorder
5. THE _mark_test_as_error method SHALL accept testref, parent_id, and tbdetail parameters

### Requirement 6: Individual Test Skip Marking

**User Story:** As a framework developer, I want to mark individual tests as skipped, so that test results accurately reflect intentional skips.

#### Acceptance Criteria

1. THE _mark_test_as_skip method SHALL create a new TestResult node with a generated UUID
2. THE _mark_test_as_skip method SHALL call mark_skip on the result with reason and bug parameters
3. THE _mark_test_as_skip method SHALL finalize the result after marking as skipped
4. THE _mark_test_as_skip method SHALL record the result using the recorder
5. THE _mark_test_as_skip method SHALL accept testref, parent_id, reason, and bug parameters

### Requirement 7: SequencerSessionScope Context Manager

**User Story:** As a framework developer, I want a session scope context manager, so that the root scope of a test run is properly managed.

#### Acceptance Criteria

1. THE SequencerSessionScope class SHALL inherit from SequencerScopeBase
2. THE SequencerSessionScope class SHALL implement the context manager protocol (__enter__ and __exit__)
3. THE SequencerSessionScope class SHALL accept sequencer, recorder, and root_result parameters in its constructor
4. THE SequencerSessionScope class SHALL store the scope_name, scope_id, root_result, and scope_node
5. THE scope_node SHALL be obtained from the sequencer's testtree property

### Requirement 8: SequencerSessionScope Entry

**User Story:** As a framework developer, I want session scope entry to establish the root execution context, so that child scopes have a parent reference.

#### Acceptance Criteria

1. WHEN entering the session scope, THE System SHALL push the scope ID onto the sequencer's scope stack using scope_id_push
2. WHEN entering the session scope, THE System SHALL log an info message indicating session entry with the scope ID
3. THE __enter__ method SHALL return self to allow use in with statements
4. THE scope_name and scope_id SHALL be derived from the root_result parameter

### Requirement 9: SequencerSessionScope Exit

**User Story:** As a framework developer, I want session scope exit to handle exceptions and finalize the scope, so that results are properly recorded.

#### Acceptance Criteria

1. WHEN exiting the session scope with a SkipError, THE System SHALL mark all descendants as skipped with the error's reason and bug
2. WHEN exiting the session scope with another exception, THE System SHALL mark all descendants as errored with the traceback detail
3. WHEN exiting the session scope with an exception, THE System SHALL log an error message with the formatted traceback
4. WHEN exiting the session scope, THE System SHALL finalize the scope node
5. WHEN exiting the session scope, THE System SHALL pop the scope ID from the sequencer's scope stack
6. WHEN exiting the session scope, THE System SHALL log an info message indicating session exit with the scope ID
7. THE __exit__ method SHALL return True when an exception was handled, False otherwise

### Requirement 10: SequencerModuleScope Context Manager

**User Story:** As a framework developer, I want a module scope context manager, so that module-level test groupings are properly managed.

#### Acceptance Criteria

1. THE SequencerModuleScope class SHALL inherit from SequencerScopeBase
2. THE SequencerModuleScope class SHALL implement the context manager protocol (__enter__ and __exit__)
3. THE SequencerModuleScope class SHALL accept sequencer, recorder, scope_name, and optional kwargs in its constructor
4. THE SequencerModuleScope class SHALL store scope_name, scope_args, scope_id, parent_scope_id, and scope_node
5. THE scope_node SHALL be obtained by calling find_treenode_for_scope on the sequencer

### Requirement 11: SequencerModuleScope Entry

**User Story:** As a framework developer, I want module scope entry to create a scope ID and record a container result, so that module results are tracked.

#### Acceptance Criteria

1. WHEN entering the module scope, THE System SHALL call scope_id_create on the sequencer to get parent_scope_id and scope_id
2. WHEN entering the module scope, THE System SHALL create a TestContainer result using create_test_result_container
3. WHEN entering the module scope, THE System SHALL record the TestContainer result using the recorder
4. WHEN entering the module scope, THE System SHALL log an info message indicating module entry with scope_name and scope_id
5. THE __enter__ method SHALL return self to allow use in with statements

### Requirement 12: SequencerModuleScope Exit

**User Story:** As a framework developer, I want module scope exit to handle exceptions and finalize the scope, so that module results are properly recorded.

#### Acceptance Criteria

1. WHEN exiting the module scope with a SkipError, THE System SHALL mark all descendants as skipped with the error's reason and bug
2. WHEN exiting the module scope with another exception, THE System SHALL mark all descendants as errored with the traceback detail
3. WHEN exiting the module scope with an exception, THE System SHALL log an error message with the formatted traceback
4. WHEN exiting the module scope, THE System SHALL finalize the scope node
5. WHEN exiting the module scope, THE System SHALL pop the scope ID from the sequencer's scope stack using scope_id_pop
6. WHEN exiting the module scope, THE System SHALL log an info message indicating module exit with scope_name and scope_id
7. THE __exit__ method SHALL return True when an exception was handled, False otherwise

### Requirement 13: SequencerTestSetupScope Context Manager

**User Story:** As a framework developer, I want a test setup scope context manager, so that test-local parameter creation is properly managed.

#### Acceptance Criteria

1. THE SequencerTestSetupScope class SHALL inherit from SequencerScopeBase
2. THE SequencerTestSetupScope class SHALL implement the context manager protocol (__enter__ and __exit__)
3. THE SequencerTestSetupScope class SHALL accept sequencer, recorder, test_name, and optional kwargs in its constructor
4. THE SequencerTestSetupScope class SHALL derive scope_name as "setup:{test_name}"
5. THE test_scope_node SHALL be obtained by calling find_treenode_for_scope with the test_name

### Requirement 14: SequencerTestSetupScope Entry

**User Story:** As a framework developer, I want test setup scope entry to establish the setup context, so that parameter factories can execute.

#### Acceptance Criteria

1. WHEN entering the test setup scope, THE System SHALL call scope_id_create on the sequencer to get parent_scope_id and scope_id
2. WHEN entering the test setup scope, THE System SHALL log an info message indicating test setup entry with scope_name and scope_id
3. THE __enter__ method SHALL return self to allow use in with statements

### Requirement 15: SequencerTestSetupScope Exit

**User Story:** As a framework developer, I want test setup scope exit to handle exceptions and mark the test appropriately, so that setup failures are recorded.

#### Acceptance Criteria

1. WHEN exiting the test setup scope with a SkipError, THE System SHALL mark the test as skipped using _mark_test_as_skip
2. WHEN exiting the test setup scope with another exception, THE System SHALL mark the test as errored using _mark_test_as_error
3. WHEN exiting the test setup scope with an exception, THE System SHALL log an error message with the formatted traceback
4. WHEN exiting the test setup scope, THE System SHALL finalize the test_scope_node
5. WHEN exiting the test setup scope, THE System SHALL pop the scope ID from the sequencer's scope stack using scope_id_pop
6. WHEN exiting the test setup scope, THE System SHALL log an info message indicating test setup exit with scope_name and scope_id
7. THE __exit__ method SHALL return True when an exception was handled, False otherwise

### Requirement 16: SequencerTestScope Context Manager

**User Story:** As a test developer, I want a test scope context manager, so that individual test execution is properly managed with result recording.

#### Acceptance Criteria

1. THE SequencerTestScope class SHALL implement the context manager protocol (__enter__ and __exit__)
2. THE SequencerTestScope class SHALL accept sequencer, recorder, test_name, and optional notables parameters in its constructor
3. THE SequencerTestScope class SHALL NOT inherit from SequencerScopeBase (standalone implementation)
4. THE SequencerTestScope class SHALL store sequencer, recorder, test_name, scope_id, parent_scope_id, result, scope_node, notables, monikers, pivots, and context_identifier
5. THE scope_node SHALL be obtained by calling find_treenode_for_scope with the test_name

### Requirement 17: SequencerTestScope Properties

**User Story:** As a framework developer, I want SequencerTestScope to expose key properties, so that test execution context is accessible.

#### Acceptance Criteria

1. THE SequencerTestScope class SHALL provide a recorder property returning the ResultRecorder
2. THE SequencerTestScope class SHALL provide a scope_id property returning the scope's UUID
3. THE SequencerTestScope class SHALL provide a test_name property returning the test function name

### Requirement 18: Context Identifier Generation

**User Story:** As a framework developer, I want context identifiers for parameterized tests, so that test instances can be distinguished.

#### Acceptance Criteria

1. THE SequencerTestScope class SHALL generate a context_identifier combining test_name and monikers
2. THE context_identifier format SHALL be "{test_name}:{moniker1},{moniker2},..."
3. WHEN notables is empty, THE context_identifier SHALL be "{test_name}:"
4. THE context_identifier SHALL be used as the scope name for scope ID management

### Requirement 19: Moniker and Pivot Extraction

**User Story:** As a framework developer, I want monikers and pivots extracted from notables, so that parameterized test values are properly identified.

#### Acceptance Criteria

1. THE _get_monikers_and_pivots method SHALL return a tuple of (monikers list, pivots OrderedDict)
2. WHEN a notable has a moniker attribute, THE System SHALL use that attribute value as the moniker
3. WHEN a notable does not have a moniker attribute, THE System SHALL use str(notable) as the moniker
4. WHEN a notable has a pivots attribute, THE System SHALL use that attribute value as the pivot data
5. WHEN a notable does not have a pivots attribute, THE System SHALL use str(notable) as the pivot data
6. WHEN notables is empty, THE System SHALL return empty monikers list and empty pivots OrderedDict

### Requirement 20: SequencerTestScope Entry

**User Story:** As a framework developer, I want test scope entry to create a result and preview it, so that test execution is tracked from the start.

#### Acceptance Criteria

1. WHEN entering the test scope, THE System SHALL call scope_id_create on the sequencer to get parent_scope_id and scope_id
2. WHEN entering the test scope, THE System SHALL log an info message indicating test scope entry with context_identifier and scope_id
3. WHEN entering the test scope, THE System SHALL set up the byproducts folder path through the sequencer's output context via self._sequencer.output_context.get_testcase_byproducts_dir(scope_id)
4. WHEN entering the test scope, THE System SHALL set up the activity stream filename as "activity.jsos" in the byproducts folder
5. WHEN entering the test scope, THE System SHALL create a TestResult node using create_test_result_node
6. WHEN entering the test scope, THE System SHALL preview the result using the recorder's preview method
7. WHEN entering the test scope, THE System SHALL call the _test_scope_enter hook method
8. THE __enter__ method SHALL return self to allow use in with statements

### Requirement 21: SequencerTestScope Exit

**User Story:** As a test developer, I want test scope exit to determine the test result status and record it, so that test outcomes are properly captured.

#### Acceptance Criteria

1. WHEN exiting the test scope with a SkipError, THE System SHALL call mark_skip on the result with reason and bug
2. WHEN exiting the test scope with an AssertionError, THE System SHALL call add_failure on the result with the traceback detail
3. WHEN exiting the test scope with another exception, THE System SHALL call add_error on the result with the traceback detail
4. WHEN exiting the test scope with an exception, THE System SHALL log an error message with the formatted traceback
5. WHEN exiting the test scope without an exception, THE System SHALL call mark_passed on the result
6. WHEN exiting the test scope, THE System SHALL call the _test_scope_exit hook method
7. WHEN exiting the test scope, THE System SHALL finalize the result
8. WHEN exiting the test scope, THE System SHALL record the result using the recorder's record method
9. WHEN exiting the test scope, THE System SHALL finalize the scope_node
10. WHEN exiting the test scope, THE System SHALL pop the scope ID from the sequencer's scope stack using scope_id_pop
11. WHEN exiting the test scope, THE System SHALL log an info message indicating test scope exit with context_identifier and scope_id
12. THE __exit__ method SHALL return True to suppress exception propagation

### Requirement 22: SequencerTestScope Hook Methods

**User Story:** As a framework developer, I want hook methods in SequencerTestScope, so that derived classes can customize enter and exit behavior.

#### Acceptance Criteria

1. THE SequencerTestScope class SHALL provide a _test_scope_enter method that can be overridden by subclasses
2. THE SequencerTestScope class SHALL provide a _test_scope_exit method that can be overridden by subclasses
3. THE default _test_scope_enter implementation SHALL do nothing (return immediately)
4. THE default _test_scope_exit implementation SHALL do nothing (return immediately)
5. THE _test_scope_enter method SHALL be called after result preview during __enter__
6. THE _test_scope_exit method SHALL be called before result finalization during __exit__

### Requirement 23: Test Activity Creation

**User Story:** As a test developer, I want to create test activities, so that I can record timing information for test operations.

#### Acceptance Criteria

1. THE SequencerTestScope class SHALL provide a begin_activity method that returns a TestActivity context manager
2. THE begin_activity method SHALL accept activity_name, optional target (default "NA"), and optional detail parameters
3. WHEN begin_activity is called, THE System SHALL create the byproducts folder if it does not exist
4. WHEN begin_activity is called, THE System SHALL create a TestActivity with the activity stream filename
5. THE returned TestActivity SHALL be usable as a context manager for timed activities

### Requirement 24: Test Activity Marking

**User Story:** As a test developer, I want to mark completed activities, so that I can record point-in-time events during test execution.

#### Acceptance Criteria

1. THE SequencerTestScope class SHALL provide a mark_activity method for recording completed activities
2. THE mark_activity method SHALL accept activity_name, optional target (default "NA"), and optional detail parameters
3. WHEN mark_activity is called, THE System SHALL create the byproducts folder if it does not exist
4. WHEN mark_activity is called, THE System SHALL create a TestActivity and immediately finalize it
5. THE mark_activity method SHALL NOT return the TestActivity (fire-and-forget pattern)

### Requirement 25: TestActivity Context Manager

**User Story:** As a test developer, I want TestActivity to work as a context manager, so that activity timing is automatically captured.

#### Acceptance Criteria

1. THE TestActivity class SHALL implement the context manager protocol (__enter__ and __exit__)
2. THE TestActivity class SHALL accept activity_filename, activity_name, target, and optional detail parameters in its constructor
3. WHEN a TestActivity is created, THE System SHALL record the begin timestamp as datetime.now()
4. THE __enter__ method SHALL return self to allow use in with statements
5. THE __exit__ method SHALL call finalize to record the end timestamp and write to file
6. THE __exit__ method SHALL return False to allow exception propagation

### Requirement 26: TestActivity Properties

**User Story:** As a framework developer, I want TestActivity to expose properties, so that activity data is accessible.

#### Acceptance Criteria

1. THE TestActivity class SHALL provide an activity_name property returning the activity name string
2. THE TestActivity class SHALL provide a begin property returning the begin datetime
3. THE TestActivity class SHALL provide a detail property returning the detail dictionary
4. THE TestActivity class SHALL provide an end property returning the end datetime (None until finalized)
5. THE TestActivity class SHALL provide a target property returning the target string

### Requirement 27: TestActivity Serialization

**User Story:** As a framework developer, I want TestActivity to serialize to dictionary and JSON, so that activity data can be persisted.

#### Acceptance Criteria

1. THE TestActivity class SHALL provide an as_dict method returning activity data as a dictionary
2. THE as_dict method SHALL include activity-name, detail, target, begin, and end fields
3. THE TestActivity class SHALL provide an as_json method returning activity data as a JSON string
4. THE as_json method SHALL accept an optional indent parameter (default 4)
5. THE as_json method SHALL format datetime values using format_datetime_with_fractional

### Requirement 28: TestActivity Finalization

**User Story:** As a test developer, I want TestActivity finalization to record timing and persist data, so that activity records are saved.

#### Acceptance Criteria

1. THE TestActivity class SHALL provide a finalize method that completes the activity recording
2. WHEN finalize is called, THE System SHALL record the end timestamp as datetime.now()
3. WHEN finalize is called, THE System SHALL convert the activity to JSON using as_json
4. WHEN finalize is called, THE System SHALL append the JSON to the activity file with a record separator prefix
5. THE record separator SHALL be the JSOS CHAR_RECORD_SEPERATOR character

### Requirement 29: Scope Naming Conventions

**User Story:** As a framework developer, I want consistent scope naming conventions, so that scopes can be identified and located.

#### Acceptance Criteria

1. THE session scope name SHALL be derived from the root result name (typically "<session>")
2. THE module scope name SHALL follow the format "package.module" (e.g., "tests.unit.test_auth")
3. THE test setup scope name SHALL follow the format "setup:{test_name}" (e.g., "setup:test_login_success")
4. THE test scope name SHALL follow the format "{test_name}:{moniker1},{moniker2}" (e.g., "test_login:admin,valid_creds")
5. WHEN a test has no monikers, THE test scope name SHALL be "{test_name}:"

### Requirement 30: Exception Classification

**User Story:** As a test developer, I want exceptions to be classified correctly, so that test results accurately reflect the type of failure.

#### Acceptance Criteria

1. WHEN a SkipError is raised, THE System SHALL mark the result as SKIPPED
2. WHEN an AssertionError is raised in a test scope, THE System SHALL mark the result as FAILED
3. WHEN any other exception is raised, THE System SHALL mark the result as ERRORED
4. THE FAILED status SHALL indicate a product code issue (expectation not met)
5. THE ERRORED status SHALL indicate a test or infrastructure issue (unexpected error)

### Requirement 31: Traceback Detail Handling

**User Story:** As a framework developer, I want structured traceback information, so that error details are properly captured and formatted.

#### Acceptance Criteria

1. WHEN an exception occurs, THE System SHALL create a TracebackDetail using create_traceback_detail
2. WHEN logging an error, THE System SHALL format the traceback using format_traceback_detail
3. THE formatted traceback SHALL be included in error log messages
4. THE TracebackDetail SHALL be passed to add_error or add_failure methods on results

### Requirement 32: Scope Stack Integrity

**User Story:** As a framework developer, I want scope stack operations to be verified, so that scope nesting errors are detected.

#### Acceptance Criteria

1. WHEN scope_id_pop is called, THE System SHALL verify the scope name matches the top of the stack
2. IF the scope name does not match, THE System SHALL raise a RuntimeError with a descriptive message
3. THE error message SHALL include both the expected scope name and the encountered scope name
4. THE scope stack SHALL maintain proper LIFO (Last In, First Out) ordering

### Requirement 33: Result Recording Timing

**User Story:** As a framework developer, I want results recorded at the correct times, so that result state is properly captured.

#### Acceptance Criteria

1. THE session scope SHALL use a pre-created JobContainer (recorded before scope entry)
2. THE module scope SHALL record a TestContainer on scope entry
3. THE test scope SHALL preview a TestResult on scope entry
4. THE test scope SHALL record the TestResult on scope exit after finalization
5. WHEN marking descendants as error or skip, THE System SHALL record each created result immediately

### Requirement 34: Byproducts Folder Management

**User Story:** As a test developer, I want byproducts folders created on demand, so that test artifacts can be stored.

#### Acceptance Criteria

1. THE byproducts folder path SHALL be determined through the sequencer's injected output context via output_context.get_testcase_byproducts_dir(scope_id), NOT via get_path_for_*, RuntimeVariables, or ThisApplicationSingleton
2. WHEN begin_activity or mark_activity is called, THE System SHALL create the byproducts folder if it does not exist
3. THE activity stream file SHALL be named "activity.jsos" within the byproducts folder
4. THE byproducts folder SHALL be created using os.makedirs

### Requirement 35: Logging Requirements

**User Story:** As a test developer, I want scope transitions logged, so that test execution flow can be traced.

#### Acceptance Criteria

1. WHEN entering a session scope, THE System SHALL log "SESSION ENTER: {scope_id}" at INFO level
2. WHEN exiting a session scope, THE System SHALL log "SESSION EXIT: {scope_id}" at INFO level
3. WHEN entering a module scope, THE System SHALL log "MODULE ENTER: {scope_name}, {scope_id}" at INFO level
4. WHEN exiting a module scope, THE System SHALL log "MODULE EXIT: {scope_name}, {scope_id}" at INFO level
5. WHEN entering a test setup scope, THE System SHALL log "TEST SETUP ENTER: {scope_name}, {scope_id}" at INFO level
6. WHEN exiting a test setup scope, THE System SHALL log "TEST SETUP EXIT: {scope_name}, {scope_id}" at INFO level
7. WHEN entering a test scope, THE System SHALL log "TEST SCOPE ENTER: {context_identifier}, {scope_id}" at INFO level
8. WHEN exiting a test scope, THE System SHALL log "TEST SCOPE EXIT: {context_identifier}, {scope_id}" at INFO level
9. WHEN an exception occurs in any scope, THE System SHALL log the formatted traceback at ERROR level

### Requirement 36: Injected Output Context

**User Story:** As a framework developer, I want the TestSequencer to resolve artefact locations through an injected output context, so that the sequencer core stays decoupled from runtime/this-app well-known-path helpers.

#### Acceptance Criteria

1. THE TestSequencer constructor SHALL accept an optional output_context parameter of type IOutputContext
2. WHEN no output_context is supplied, THE TestSequencer SHALL default to a SimpleOutputContext that roots artefacts under a single base directory
3. THE TestSequencer SHALL expose the injected output context via an output_context property
4. THE TestSequencer SHALL resolve the test results directory through output_context.get_test_results_dir()
5. THE TestSequencer SHALL resolve the diagnostics directory through output_context.get_diagnostics_dir(label)
6. THE TestSequencer SHALL NOT resolve artefact locations via get_path_for_*, RuntimeVariables, or ThisApplicationSingleton
7. THE SequencerTestScope SHALL reach the per-testcase by-products path through self._sequencer.output_context

### Requirement 37: Diagnostics Gating via Environment Module

**User Story:** As a framework developer, I want AM_DIAGNOSTICS_* gating read through the dependency-free environment module, so that diagnostic capture decisions do not depend on RuntimeVariables.

#### Acceptance Criteria

1. WHEN deciding whether to capture pre-run diagnostics, THE System SHALL read AM_DIAGNOSTICS_PRERUN via environment.diagnostics_prerun_enabled()
2. WHEN deciding whether to capture post-run diagnostics, THE System SHALL read AM_DIAGNOSTICS_POSTRUN via environment.diagnostics_postrun_enabled()
3. THE diagnostics gating SHALL NOT be read via RuntimeVariables or ThisApplicationSingleton
4. WHEN diagnostics are enabled, THE System SHALL resolve the diagnostic output folder through output_context.get_diagnostics_dir(label)
