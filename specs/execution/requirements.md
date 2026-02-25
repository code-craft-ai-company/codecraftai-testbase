# Test Execution Engine - Requirements Document

## Introduction

The Test Execution Engine is the core orchestration system of the TestBase framework responsible for coordinating the complete test run lifecycle from discovery to result recording. It manages hierarchical scope contexts (session, module, test setup, test), generates and executes test sequence documents for reproducible test runs, integrates with the Dependency Injection System for resource provisioning, records test results through the Result Recording System, and supports debugging workflows with breakpoint integration. The engine operates through three primary components: the TestJob (high-level orchestrator), the TestSequencer (execution state machine), and the Scope Context Managers (lifecycle management).

## Glossary

- **TestJob**: The high-level orchestrator class that spans the execution of all test packs and organizes the flow of test execution, serving as the primary entry point for test runs
- **DefaultTestJob**: A default TestJob implementation used when no specific job is specified
- **TestSequencer**: The central state machine that orchestrates test discovery, collection, and execution flow through distinct phases
- **TestCollector**: The component that processes include/exclude expressions to discover and collect test references
- **SequencerScopeBase**: The base context manager class for all sequencer scope implementations providing shared infrastructure for scope management
- **SequencerSessionScope**: The context manager for the root session scope of a test run
- **SequencerModuleScope**: The context manager for module-level test groupings
- **SequencerTestSetupScope**: The context manager for test preparation and test-local parameter creation
- **SequencerTestScope**: The context manager for executing a single test function
- **TestActivity**: A class that records timing information for test activities within a test scope
- **Sequence_Document**: A generated Python module that encodes the test execution order and parameter provisioning
- **Scope_Stack**: A list structure maintained by the sequencer for tracking the current execution context hierarchy
- **Scope_ID**: A unique UUID identifier assigned to each scope instance during execution
- **Context_Identifier**: A string combining test name and parameter monikers to distinguish parameterized test instances
- **ResultRecorder**: The component responsible for recording test results during execution
- **Include_Expression**: A string expression in the format `(scope):(package).(package)@(module)#(testname)` used to specify which tests to include
- **Exclude_Expression**: A string expression used to specify which tests to exclude from the included tests
- **MetaFilter**: An expression used to filter tests by metadata attributes
- **TEST_SEQUENCER_PHASES**: An enumeration defining the sequencer states (Initial, Discovery, Collection, Graph, Traversal)

## Requirements

### Requirement 1: TestJob Lifecycle Management

**User Story:** As a test developer, I want a TestJob class that manages the complete test run lifecycle, so that test execution follows a consistent and predictable flow.

#### Acceptance Criteria

1. THE TestJob class SHALL provide a begin method that initializes test result recording paths and configuration
2. THE TestJob class SHALL provide an execute method that orchestrates the complete test run and returns an integer result code
3. THE TestJob class SHALL provide a finalize method that performs cleanup operations at the end of a test run
4. WHEN the execute method completes successfully with all tests passing, THE System SHALL return a result code of 0
5. WHEN the execute method encounters failures or errors, THE System SHALL return a result code of -1
6. THE TestJob class SHALL implement the context manager protocol (__enter__ and __exit__) for resource management
7. WHEN used as a context manager, THE TestJob SHALL call begin on entry and finalize on exit

### Requirement 2: TestJob Configuration

**User Story:** As a test developer, I want to configure TestJob with include/exclude expressions and metadata filters, so that I can control which tests are executed.

#### Acceptance Criteria

1. THE TestJob class SHALL accept a logger parameter for output logging
2. THE TestJob class SHALL accept a testroot parameter specifying the root directory for test discovery
3. THE TestJob class SHALL accept an optional includes parameter as a list of include expressions
4. THE TestJob class SHALL accept an optional excludes parameter as a list of exclude expressions
5. THE TestJob class SHALL accept an optional metafilters parameter as a list of metadata filters
6. THE TestJob class SHALL accept an optional test_module parameter for single module execution
7. THE TestJob class SHALL accept an optional parser parameter for argument parsing
8. THE TestJob class SHALL support class-level attributes for name, description, owner, includes, excludes, and metafilters

### Requirement 3: TestJob Sequencer and Recorder Creation

**User Story:** As a framework developer, I want TestJob to provide hook methods for creating sequencers and recorders, so that derived classes can customize these components.

#### Acceptance Criteria

1. THE TestJob class SHALL provide a _create_sequencer method that returns a TestSequencer instance
2. THE TestJob class SHALL provide a _create_recorder method that returns a ResultRecorder instance
3. WHEN _create_sequencer is called, THE System SHALL create a TestSequencer with the job's title, testroot, includes, excludes, and metafilters
4. WHEN _create_recorder is called, THE System SHALL create a JsonResultRecorder with the provided run information
5. THE _create_sequencer and _create_recorder methods SHALL be overridable by derived classes

### Requirement 4: TestJob Integration Event Firing

**User Story:** As a test developer, I want TestJob to fire integration lifecycle events, so that couplings can participate in the test run lifecycle.

#### Acceptance Criteria

1. THE TestJob class SHALL provide a fire_attach_to_framework method that invokes attach_to_framework on the sequencer
2. THE TestJob class SHALL provide a fire_attach_to_environment method that invokes attach_to_environment on the sequencer
3. THE TestJob class SHALL provide a fire_establish_presence method that invokes establish_presence on the sequencer
4. THE TestJob class SHALL provide a fire_diagnostic_capture_pre_testrun method that invokes diagnostic_capture_pre_testrun on the sequencer
5. THE TestJob class SHALL provide a fire_diagnostic_capture_post_testrun method that invokes diagnostic_capture_post_testrun on the sequencer
6. THE diagnostic capture methods SHALL accept a level parameter specifying the maximum diagnostic level

### Requirement 5: TestJob Query Support

**User Story:** As a test developer, I want to query the TestJob for test references without executing tests, so that I can inspect the test set before running.

#### Acceptance Criteria

1. THE TestJob class SHALL provide a query method that returns a list of test references
2. WHEN query is called, THE System SHALL create a sequencer and perform discovery without executing tests
3. THE query method SHALL populate the import_errors property with any import errors encountered
4. THE query method SHALL accept an optional format parameter for output formatting

### Requirement 6: TestSequencer State Machine

**User Story:** As a framework developer, I want a TestSequencer that operates as a state machine with distinct phases, so that test execution follows a predictable flow.

#### Acceptance Criteria

1. THE TestSequencer class SHALL define phases: Initial, Discovery, Collection, Graph, and Traversal
2. THE TestSequencer class SHALL implement the context manager protocol for resource management
3. THE TestSequencer class SHALL maintain a scope stack for tracking the current execution context
4. THE TestSequencer class SHALL expose import_errors, references, testnodes, and testtree properties
5. WHEN the sequencer is created, THE System SHALL initialize it in the Initial phase

### Requirement 7: TestSequencer Discovery

**User Story:** As a test developer, I want the TestSequencer to discover tests based on include/exclude expressions, so that the correct tests are collected for execution.

#### Acceptance Criteria

1. THE TestSequencer class SHALL provide a discover method that initiates the discovery phase
2. WHEN discover is called, THE System SHALL create a TestCollector and process include expressions
3. THE discover method SHALL return the count of discovered tests
4. WHEN tests are discovered, THE System SHALL collect integrations and configurations if include_integrations is True
5. THE discover method SHALL populate the import_errors property with any import errors encountered
6. THE discover method SHALL accept an optional test_module parameter for single module discovery

### Requirement 8: TestSequencer Integration Coordination

**User Story:** As a framework developer, I want the TestSequencer to coordinate integration lifecycle methods, so that couplings are properly initialized.

#### Acceptance Criteria

1. THE TestSequencer class SHALL provide an attach_to_framework method that calls attach_to_framework on all integrations
2. THE TestSequencer class SHALL provide an attach_to_environment method that calls attach_to_environment on all integrations and configurations
3. THE TestSequencer class SHALL provide a collect_resources method that calls collect_resources on all integrations
4. THE TestSequencer class SHALL provide an establish_presence method that calls establish_presence on all integrations
5. WHEN attach_to_environment is called, THE System SHALL write startup configuration to a JSON file

### Requirement 9: TestSequencer Diagnostic Capture

**User Story:** As a test developer, I want the TestSequencer to capture diagnostics at pre-run and post-run checkpoints, so that I can troubleshoot issues.

#### Acceptance Criteria

1. THE TestSequencer class SHALL provide a diagnostic_capture_pre_testrun method that captures pre-run diagnostics
2. THE TestSequencer class SHALL provide a diagnostic_capture_post_testrun method that captures post-run diagnostics
3. WHEN AM_DIAGNOSTICS_PRERUN runtime variable is True, THE System SHALL capture pre-run diagnostics from all integrations
4. WHEN AM_DIAGNOSTICS_POSTRUN runtime variable is True, THE System SHALL capture post-run diagnostics from all integrations
5. THE diagnostic methods SHALL accept a level parameter specifying the maximum diagnostic level

### Requirement 10: Sequence Document Generation

**User Story:** As a framework developer, I want the TestSequencer to generate a sequence document, so that test execution order is reproducible and debuggable.

#### Acceptance Criteria

1. THE TestSequencer class SHALL provide a generate_testrun_sequence_document method that creates a Python module
2. THE generated document SHALL contain a session function as the entry point
3. THE generated document SHALL contain scope functions for each module in the test tree
4. THE generated document SHALL include parameter factory imports and constraint imports
5. THE generated document SHALL include debugger breakpoint code when configured
6. WHEN the document is generated, THE System SHALL store the filename in the _sequence_document attribute

### Requirement 11: Test Execution

**User Story:** As a test developer, I want the TestSequencer to execute tests via the sequence document, so that tests run in the correct order with proper parameter provisioning.

#### Acceptance Criteria

1. THE TestSequencer class SHALL provide an execute_tests method that runs the test sequence
2. WHEN execute_tests is called without a sequence document, THE System SHALL raise a SemanticError
3. THE execute_tests method SHALL import and execute the sequence document's session function
4. THE execute_tests method SHALL create a root JobContainer result and record it
5. THE execute_tests method SHALL accept runid and recorder parameters

### Requirement 12: Scope Context Management

**User Story:** As a framework developer, I want the TestSequencer to provide scope context entry methods, so that scope lifecycles are properly managed.

#### Acceptance Criteria

1. THE TestSequencer class SHALL provide an enter_session_scope_context method returning a SequencerSessionScope
2. THE TestSequencer class SHALL provide an enter_module_scope_context method returning a SequencerModuleScope
3. THE TestSequencer class SHALL provide an enter_test_setup_context method returning a SequencerTestSetupScope
4. THE TestSequencer class SHALL provide an enter_test_scope_context method returning a SequencerTestScope
5. THE enter_test_scope_context method SHALL accept an optional notables parameter for parameterized tests

### Requirement 13: Scope ID Management

**User Story:** As a framework developer, I want the TestSequencer to manage scope IDs, so that result hierarchy is properly tracked.

#### Acceptance Criteria

1. THE TestSequencer class SHALL provide a scope_id_create method that generates a new UUID scope ID
2. THE scope_id_create method SHALL return a tuple of (parent_id, scope_id)
3. THE TestSequencer class SHALL provide a scope_id_push method that adds a scope to the stack
4. THE TestSequencer class SHALL provide a scope_id_pop method that removes a scope from the stack
5. WHEN scope_id_pop is called with a mismatched scope name, THE System SHALL raise a RuntimeError
6. THE TestSequencer class SHALL provide a get_top_scope_id method that returns the current top scope ID

### Requirement 14: Result Container Creation

**User Story:** As a framework developer, I want the TestSequencer to provide factory methods for result containers, so that results are consistently created.

#### Acceptance Criteria

1. THE TestSequencer class SHALL provide a create_job_result_container method returning a JobContainer
2. THE TestSequencer class SHALL provide a create_test_result_container method returning a TestContainer
3. THE TestSequencer class SHALL provide a create_test_result_node method returning a TestResult
4. THE TestSequencer class SHALL provide a create_tasking_group method returning a TaskingGroup
5. THE TestSequencer class SHALL provide a create_tasking_result method returning a TaskingResult

### Requirement 15: SequencerScopeBase Foundation

**User Story:** As a framework developer, I want a base class for scope context managers, so that common functionality is shared across all scope types.

#### Acceptance Criteria

1. THE SequencerScopeBase class SHALL accept sequencer and recorder parameters in its constructor
2. THE SequencerScopeBase class SHALL provide a _mark_descendants_as_error method for marking child tests as errored
3. THE SequencerScopeBase class SHALL provide a _mark_descendants_skipped method for marking child tests as skipped
4. THE SequencerScopeBase class SHALL provide a _mark_test_as_error method for marking a single test as errored
5. THE SequencerScopeBase class SHALL provide a _mark_test_as_skip method for marking a single test as skipped

### Requirement 16: SequencerSessionScope Context Manager

**User Story:** As a framework developer, I want a session scope context manager, so that the root scope of a test run is properly managed.

#### Acceptance Criteria

1. THE SequencerSessionScope class SHALL inherit from SequencerScopeBase
2. THE SequencerSessionScope class SHALL implement the context manager protocol
3. WHEN entering the session scope, THE System SHALL push the scope ID onto the sequencer's scope stack
4. WHEN exiting the session scope with a SkipError, THE System SHALL mark all descendants as skipped
5. WHEN exiting the session scope with another exception, THE System SHALL mark all descendants as errored
6. WHEN exiting the session scope, THE System SHALL finalize the scope node and pop the scope ID

### Requirement 17: SequencerModuleScope Context Manager

**User Story:** As a framework developer, I want a module scope context manager, so that module-level test groupings are properly managed.

#### Acceptance Criteria

1. THE SequencerModuleScope class SHALL inherit from SequencerScopeBase
2. THE SequencerModuleScope class SHALL implement the context manager protocol
3. WHEN entering the module scope, THE System SHALL create a scope ID and record a TestContainer result
4. WHEN exiting the module scope with a SkipError, THE System SHALL mark all descendants as skipped
5. WHEN exiting the module scope with another exception, THE System SHALL mark all descendants as errored
6. WHEN exiting the module scope, THE System SHALL finalize the scope node and pop the scope ID

### Requirement 18: SequencerTestSetupScope Context Manager

**User Story:** As a framework developer, I want a test setup scope context manager, so that test-local parameter creation is properly managed.

#### Acceptance Criteria

1. THE SequencerTestSetupScope class SHALL implement the context manager protocol
2. THE SequencerTestSetupScope class SHALL accept a test_name parameter identifying the test being set up
3. WHEN entering the test setup scope, THE System SHALL prepare for test-local parameter creation
4. WHEN exiting the test setup scope with an exception, THE System SHALL handle the exception appropriately

### Requirement 19: SequencerTestScope Context Manager

**User Story:** As a test developer, I want a test scope context manager, so that individual test execution is properly managed with result recording.

#### Acceptance Criteria

1. THE SequencerTestScope class SHALL implement the context manager protocol
2. THE SequencerTestScope class SHALL accept test_name and optional notables parameters
3. WHEN entering the test scope, THE System SHALL create a scope ID and TestResult node
4. WHEN entering the test scope, THE System SHALL preview the result with the recorder
5. WHEN exiting the test scope with a SkipError, THE System SHALL mark the result as skipped
6. WHEN exiting the test scope with an AssertionError, THE System SHALL mark the result as failed
7. WHEN exiting the test scope with another exception, THE System SHALL mark the result as errored
8. WHEN exiting the test scope without an exception, THE System SHALL mark the result as passed
9. WHEN exiting the test scope, THE System SHALL finalize the result and record it

### Requirement 20: SequencerTestScope Activity Tracking

**User Story:** As a test developer, I want to track activities within a test scope, so that I can record timing information for test operations.

#### Acceptance Criteria

1. THE SequencerTestScope class SHALL provide a begin_activity method that returns a TestActivity context manager
2. THE SequencerTestScope class SHALL provide a mark_activity method that records a completed activity
3. THE begin_activity method SHALL accept activity_name, target, and optional detail parameters
4. THE mark_activity method SHALL accept activity_name, target, and optional detail parameters
5. WHEN an activity is created, THE System SHALL create the byproducts folder if it does not exist

### Requirement 21: TestActivity Timing

**User Story:** As a test developer, I want TestActivity to record timing information, so that I can analyze test performance.

#### Acceptance Criteria

1. THE TestActivity class SHALL implement the context manager protocol
2. THE TestActivity class SHALL record begin and end timestamps
3. THE TestActivity class SHALL provide an as_dict method returning activity data as a dictionary
4. THE TestActivity class SHALL provide an as_json method returning activity data as JSON
5. THE TestActivity class SHALL provide a finalize method that records the end timestamp and writes to file

### Requirement 22: TestCollector Discovery

**User Story:** As a framework developer, I want a TestCollector that discovers tests based on expressions, so that the correct tests are collected.

#### Acceptance Criteria

1. THE TestCollector class SHALL accept root, excludes, metafilters, method_prefix, and test_module parameters
2. THE TestCollector class SHALL provide a collect_references method that processes include expressions
3. THE TestCollector class SHALL provide a finalize_collection method that applies metadata filters and builds the test tree
4. THE TestCollector class SHALL expose import_errors, references, and test_tree properties
5. WHEN a test class is specified in an expression, THE System SHALL raise a SemanticError

### Requirement 23: TestCollector Integration Collection

**User Story:** As a framework developer, I want the TestCollector to collect integrations and configurations, so that only necessary couplings are initialized.

#### Acceptance Criteria

1. THE TestCollector class SHALL provide a collect_integrations_and_configurations method
2. WHEN collect_integrations_and_configurations is called, THE System SHALL add implied session resources to the injection registry
3. WHEN collect_integrations_and_configurations is called, THE System SHALL finalize the injection registry startup
4. WHEN unknown parameters are found, THE System SHALL raise an UnknownParameterError
5. THE method SHALL return a tuple of (referenced_integrations, referenced_configurations)

### Requirement 24: Empty Test Set Handling

**User Story:** As a test developer, I want clear error messages when no tests are found, so that I can diagnose configuration issues.

#### Acceptance Criteria

1. WHEN the discovery phase finds zero tests, THE System SHALL log an error message
2. THE error message SHALL include the include expressions that were specified
3. THE error message SHALL include the exclude expressions that were specified
4. WHEN no tests are found, THE execute method SHALL return a result code of -1

### Requirement 25: Import Error Recording

**User Story:** As a test developer, I want import errors to be recorded, so that I can diagnose test file issues.

#### Acceptance Criteria

1. THE TestSequencer class SHALL provide a record_import_errors method that writes errors to a file
2. THE import errors file SHALL be in JSOS format with module, filename, and trace fields
3. THE TestJob class SHALL extend its import_errors list with errors from the sequencer
4. WHEN import errors occur, THE System SHALL log error messages for each failed import

### Requirement 26: Debugger Breakpoint Integration

**User Story:** As a test developer, I want debugger breakpoint support, so that I can debug test execution at specific points.

#### Acceptance Criteria

1. WHEN AM_DEBUG_DEBUGGER and AM_DEBUG_BREAKPOINTS runtime variables are set, THE System SHALL insert breakpoint code
2. THE System SHALL support a TEST_DISCOVERY breakpoint before test discovery
3. THE System SHALL support a TESTRUN_START breakpoint at the beginning of test execution
4. THE breakpoint code SHALL be inserted into the generated sequence document

### Requirement 27: Context Identifier Generation

**User Story:** As a framework developer, I want context identifiers for parameterized tests, so that test instances can be distinguished.

#### Acceptance Criteria

1. THE SequencerTestScope class SHALL generate a context identifier combining test name and monikers
2. THE context identifier format SHALL be `{test_name}:{moniker1},{moniker2},...`
3. WHEN notables have a moniker attribute, THE System SHALL use that attribute value
4. WHEN notables do not have a moniker attribute, THE System SHALL use the string representation
5. THE context identifier SHALL be used as the scope name for scope ID management

### Requirement 28: Password Masking in Environment

**User Story:** As a test developer, I want passwords masked in environment dumps, so that sensitive information is not exposed in logs.

#### Acceptance Criteria

1. THE TestSequencer class SHALL provide a create_password_masked_environment method
2. WHEN an environment variable key contains "PASSWORD", THE System SHALL replace its value with "(hidden)"
3. THE masked environment SHALL be written to the startup-configuration.json file

### Requirement 29: Test Tree Navigation

**User Story:** As a framework developer, I want to navigate the test tree, so that scope nodes can be located during execution.

#### Acceptance Criteria

1. THE TestSequencer class SHALL provide a find_treenode_for_scope method that locates a node by scope name
2. THE TestSequencer class SHALL provide a find_test_scope method that returns the current SequencerTestScope
3. THE find_treenode_for_scope method SHALL recursively search the test tree
4. WHEN the scope is not found, THE find_treenode_for_scope method SHALL return None

### Requirement 30: Activity Marking Through Sequencer

**User Story:** As a test developer, I want to mark activities through the sequencer, so that components with sequencer access can record activities.

#### Acceptance Criteria

1. THE TestSequencer class SHALL provide a mark_activity method that delegates to the current test scope
2. THE mark_activity method SHALL accept activity_name, target, and optional detail parameters
3. WHEN no test scope is active, THE mark_activity method SHALL do nothing
4. THE mark_activity method SHALL locate the test scope using find_test_scope


