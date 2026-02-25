# Sequencer Scopes - Tasks Document

## Overview

This document tracks the implementation status of the Sequencer Scopes system and identifies enhancement opportunities for future development. The sequencer scopes system provides hierarchical execution context management for the TestBase framework, controlling the lifecycle of test execution at different granularity levels: session, module, test setup, and individual test.

## Implementation Status

### Completed Tasks

#### SequencerScopeBase (`sequencing/sequencerscopebase.py`)
- [x] Implement SequencerScopeBase foundation class
  - Constructor accepting sequencer and recorder parameters
  - Store references for use by derived classes
  - _Requirements: 2.1, 2.2_

- [x] Implement descendant error propagation
  - _mark_descendants_as_error() method for marking child tests as errored
  - Tree traversal for TestRef and TestGroup nodes
  - TestContainer creation during error propagation with UUID generation
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] Implement descendant skip propagation
  - _mark_descendants_skipped() method for marking child tests as skipped
  - Tree traversal for TestRef and TestGroup nodes
  - TestContainer creation during skip propagation with UUID generation
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] Implement individual test error marking
  - _mark_test_as_error() method creating TestResult with UUID
  - add_error() call with traceback detail
  - Result finalization and recording
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] Implement individual test skip marking
  - _mark_test_as_skip() method creating TestResult with UUID
  - mark_skip() call with reason and bug parameters
  - Result finalization and recording
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

#### SequencerSessionScope (`sequencing/sequencersessionscope.py`)
- [x] Implement SequencerSessionScope context manager
  - Inheritance from SequencerScopeBase
  - Context manager protocol (__enter__ and __exit__)
  - Constructor accepting sequencer, recorder, and root_result parameters
  - Storage of scope_name, scope_id, root_result, and scope_node
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] Implement session scope entry
  - Push scope ID onto sequencer's scope stack using scope_id_push
  - Log info message indicating session entry with scope ID
  - Return self for with statement usage
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] Implement session scope exit
  - SkipError handling with descendant skip marking
  - Exception handling with descendant error marking
  - Error logging with formatted traceback
  - Scope node finalization
  - Scope ID pop from sequencer's scope stack
  - Info logging for session exit
  - Return True when exception handled, False otherwise
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

#### SequencerModuleScope (`sequencing/sequencermodulescope.py`)
- [x] Implement SequencerModuleScope context manager
  - Inheritance from SequencerScopeBase
  - Context manager protocol (__enter__ and __exit__)
  - Constructor accepting sequencer, recorder, scope_name, and optional kwargs
  - Storage of scope_name, scope_args, scope_id, parent_scope_id, and scope_node
  - Tree node lookup via find_treenode_for_scope
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] Implement module scope entry
  - scope_id_create call to get parent_scope_id and scope_id
  - TestContainer result creation using create_test_result_container
  - Result recording using recorder
  - Info logging for module entry with scope_name and scope_id
  - Return self for with statement usage
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] Implement module scope exit
  - SkipError handling with descendant skip marking
  - Exception handling with descendant error marking
  - Error logging with formatted traceback
  - Scope node finalization
  - Scope ID pop using scope_id_pop
  - Info logging for module exit
  - Return True when exception handled, False otherwise
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7_

#### SequencerTestSetupScope (`sequencing/sequencertestsetupscope.py`)
- [x] Implement SequencerTestSetupScope context manager
  - Inheritance from SequencerScopeBase
  - Context manager protocol (__enter__ and __exit__)
  - Constructor accepting sequencer, recorder, test_name, and optional kwargs
  - Scope name derivation as "setup:{test_name}"
  - Test scope node lookup via find_treenode_for_scope with test_name
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] Implement test setup scope entry
  - scope_id_create call to get parent_scope_id and scope_id
  - Info logging for test setup entry with scope_name and scope_id
  - Return self for with statement usage
  - _Requirements: 14.1, 14.2, 14.3_

- [x] Implement test setup scope exit
  - SkipError handling with _mark_test_as_skip
  - Exception handling with _mark_test_as_error
  - Error logging with formatted traceback
  - Test scope node finalization
  - Scope ID pop using scope_id_pop
  - Info logging for test setup exit
  - Return True when exception handled, False otherwise
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7_

#### SequencerTestScope (`sequencing/sequencertestscope.py`)
- [x] Implement SequencerTestScope context manager
  - Context manager protocol (__enter__ and __exit__)
  - Constructor accepting sequencer, recorder, test_name, and optional notables
  - Standalone implementation (not inheriting from SequencerScopeBase)
  - Storage of all required attributes
  - Scope node lookup via find_treenode_for_scope
  - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

- [x] Implement SequencerTestScope properties
  - recorder property returning ResultRecorder
  - scope_id property returning scope's UUID
  - test_name property returning test function name
  - _Requirements: 17.1, 17.2, 17.3_

- [x] Implement context identifier generation
  - context_identifier combining test_name and monikers
  - Format "{test_name}:{moniker1},{moniker2},..."
  - Empty monikers format "{test_name}:"
  - Usage as scope name for scope ID management
  - _Requirements: 18.1, 18.2, 18.3, 18.4_

- [x] Implement moniker and pivot extraction
  - _get_monikers_and_pivots() method returning tuple
  - Moniker attribute extraction when available
  - String representation fallback for monikers
  - Pivots attribute extraction when available
  - String representation fallback for pivots
  - Empty returns for empty notables
  - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6_

- [x] Implement test scope entry
  - scope_id_create call to get parent_scope_id and scope_id
  - Info logging for test scope entry with context_identifier and scope_id
  - Byproducts folder path setup using get_path_for_testcase_by_products
  - Activity stream filename setup as "activity.jsos"
  - TestResult node creation using create_test_result_node
  - Result preview using recorder's preview method
  - _test_scope_enter hook method call
  - Return self for with statement usage
  - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7, 20.8_

- [x] Implement test scope exit
  - SkipError handling with mark_skip on result
  - AssertionError handling with add_failure on result
  - Other exception handling with add_error on result
  - Error logging with formatted traceback
  - Success handling with mark_passed on result
  - _test_scope_exit hook method call
  - Result finalization
  - Result recording using recorder's record method
  - Scope node finalization
  - Scope ID pop using scope_id_pop
  - Info logging for test scope exit
  - Return True to suppress exception propagation
  - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7, 21.8, 21.9, 21.10, 21.11, 21.12_

- [x] Implement hook methods
  - _test_scope_enter method for subclass override
  - _test_scope_exit method for subclass override
  - Default implementations do nothing
  - Correct call timing in __enter__ and __exit__
  - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6_

- [x] Implement test activity creation
  - begin_activity() method returning TestActivity context manager
  - Parameters: activity_name, optional target (default "NA"), optional detail
  - Byproducts folder creation if not exists
  - TestActivity creation with activity stream filename
  - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.5_

- [x] Implement test activity marking
  - mark_activity() method for recording completed activities
  - Parameters: activity_name, optional target (default "NA"), optional detail
  - Byproducts folder creation if not exists
  - TestActivity creation and immediate finalization
  - Fire-and-forget pattern (no return)
  - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5_

#### TestActivity (`sequencing/testactivity.py`)
- [x] Implement TestActivity context manager
  - Context manager protocol (__enter__ and __exit__)
  - Constructor accepting activity_filename, activity_name, target, and optional detail
  - Begin timestamp recording as datetime.now()
  - Return self from __enter__
  - finalize() call from __exit__
  - Return False from __exit__ to allow exception propagation
  - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5, 25.6_

- [x] Implement TestActivity properties
  - activity_name property returning activity name string
  - begin property returning begin datetime
  - detail property returning detail dictionary
  - end property returning end datetime (None until finalized)
  - target property returning target string
  - _Requirements: 26.1, 26.2, 26.3, 26.4, 26.5_

- [x] Implement TestActivity serialization
  - as_dict() method returning activity data as dictionary
  - Dictionary includes activity-name, detail, target, begin, and end fields
  - as_json() method returning activity data as JSON string
  - Optional indent parameter (default 4)
  - Datetime formatting using format_datetime_with_fractional
  - _Requirements: 27.1, 27.2, 27.3, 27.4, 27.5_

- [x] Implement TestActivity finalization
  - finalize() method completing activity recording
  - End timestamp recording as datetime.now()
  - JSON conversion using as_json
  - File append with JSOS CHAR_RECORD_SEPERATOR prefix
  - _Requirements: 28.1, 28.2, 28.3, 28.4, 28.5_

#### Unit Tests
- [x] SequencerTestScope unit tests (`test_sequencing_functions.py`)
  - Moniker and pivot extraction tests
  - Activity marking file creation tests
  - _Requirements: 19.1-19.6, 24.1-24.5_

- [x] SequencerScopeBase unit tests (`test_sequencing_functions.py`)
  - _mark_test_as_error tests
  - _mark_test_as_skip tests
  - _mark_descendants_as_error tests
  - _mark_descendants_skipped tests
  - _Requirements: 3.1-3.5, 4.1-4.5, 5.1-5.5, 6.1-6.5_

---

### In Progress

_No tasks currently in progress._

---

### Planned Tasks

#### Test Coverage Enhancements
- [ ] Add unit tests for SequencerSessionScope
  - Test context manager entry/exit
  - Test scope ID push/pop
  - Test SkipError handling with descendant marking
  - Test exception handling with error marking
  - _Requirements: 7.1-7.5, 8.1-8.4, 9.1-9.7_

- [ ] Add unit tests for SequencerModuleScope
  - Test context manager entry/exit
  - Test TestContainer creation and recording
  - Test parent scope ID linkage
  - Test exception propagation to descendants
  - _Requirements: 10.1-10.5, 11.1-11.5, 12.1-12.7_

- [ ] Add unit tests for SequencerTestSetupScope
  - Test context manager entry/exit
  - Test scope name derivation
  - Test single test error/skip marking
  - _Requirements: 13.1-13.5, 14.1-14.3, 15.1-15.7_

- [ ] Add unit tests for SequencerTestScope entry/exit
  - Test result creation and preview
  - Test exception classification (SkipError, AssertionError, other)
  - Test result status determination
  - Test hook method invocation
  - _Requirements: 20.1-20.8, 21.1-21.12, 22.1-22.6_

- [ ] Add unit tests for TestActivity
  - Test context manager timing capture
  - Test as_dict() output format
  - Test as_json() serialization
  - Test finalize() file append behavior
  - _Requirements: 25.1-25.6, 26.1-26.5, 27.1-27.5, 28.1-28.5_

#### Integration Testing
- [ ] Add integration tests for nested scope execution
  - Test session → module → setup → test nesting
  - Test correct parent-child relationships in results
  - Test scope stack integrity throughout execution
  - _Requirements: 1.1-1.6, 32.1-32.4_

- [ ] Add integration tests for failure propagation
  - Test module-level failure marks all tests
  - Test setup failure marks single test
  - Test session failure marks entire run
  - _Requirements: 3.1-3.5, 4.1-4.5, 9.1-9.7, 12.1-12.7_

- [ ] Add integration tests for parameterized tests
  - Test correct moniker generation
  - Test pivot data preservation
  - Test multiple instances of same test
  - _Requirements: 18.1-18.4, 19.1-19.6_

#### Documentation Enhancements
- [ ] Add comprehensive docstrings to scope classes
  - Document context manager lifecycle
  - Document exception handling behavior
  - Include usage examples

- [ ] Add inline code comments for complex logic
  - Document tree traversal in descendant marking
  - Document scope stack management
  - Document activity file format

#### Error Handling Improvements
- [ ] Improve error messages for scope stack mismatches
  - Include full stack trace in error message
  - Include expected vs actual scope names
  - _Requirements: 32.1-32.4_

- [ ] Add validation for scope nesting rules
  - Detect invalid scope nesting (e.g., test inside test)
  - Warn on unusual scope patterns
  - _Requirements: 1.1-1.6_

#### Feature Enhancements
- [ ] Support for custom scope types
  - Allow registration of custom scope implementations
  - Support for scope-specific result types
  - _Requirements: 1.1-1.6_

- [ ] Support for scope-level timeouts
  - Configurable timeout per scope type
  - Automatic test failure on timeout
  - _Requirements: 21.1-21.12_

- [ ] Support for scope-level resource cleanup
  - Automatic resource cleanup on scope exit
  - Cleanup ordering based on scope hierarchy
  - _Requirements: 9.4, 12.4, 15.4_

- [ ] Enhanced activity tracking
  - Support for nested activities
  - Activity duration aggregation
  - Activity filtering and search
  - _Requirements: 23.1-23.5, 24.1-24.5_

---

## Enhancement Opportunities

### Short-term Improvements

1. **Scope Validation**
   - Add runtime validation for scope nesting rules
   - Detect and report invalid scope transitions
   - Provide helpful error messages for common mistakes

2. **Activity Tracking Enhancements**
   - Add support for activity categories
   - Add support for activity metadata
   - Improve activity file rotation for long-running tests

3. **Logging Improvements**
   - Add configurable log levels per scope type
   - Add structured logging support
   - Add log correlation IDs for distributed tracing

### Medium-term Improvements

1. **Scope Lifecycle Hooks**
   - Add pre-enter and post-exit hooks for all scope types
   - Support for scope-level setup and teardown
   - Support for scope-level fixtures

2. **Result Recording Optimization**
   - Batch result writes for performance
   - Async result recording option
   - Result compression for large test runs

3. **Scope Metrics**
   - Track scope entry/exit timing
   - Track scope nesting depth
   - Track scope failure rates

### Long-term Improvements

1. **Parallel Scope Execution**
   - Thread-safe scope management
   - Concurrent result recording
   - Resource isolation between parallel scopes

2. **Distributed Scope Management**
   - Scope coordination across nodes
   - Result aggregation from remote scopes
   - Scope state synchronization

3. **Scope Visualization**
   - Real-time scope hierarchy display
   - Scope timeline visualization
   - Interactive scope debugging

---

## Requirements Traceability

| Requirement | Status | Implementation Location |
|-------------|--------|------------------------|
| 1.1-1.6 | ✅ Complete | Scope hierarchy structure |
| 2.1-2.2 | ✅ Complete | `sequencerscopebase.py::SequencerScopeBase.__init__` |
| 3.1-3.5 | ✅ Complete | `sequencerscopebase.py::SequencerScopeBase._mark_descendants_as_error` |
| 4.1-4.5 | ✅ Complete | `sequencerscopebase.py::SequencerScopeBase._mark_descendants_skipped` |
| 5.1-5.5 | ✅ Complete | `sequencerscopebase.py::SequencerScopeBase._mark_test_as_error` |
| 6.1-6.5 | ✅ Complete | `sequencerscopebase.py::SequencerScopeBase._mark_test_as_skip` |
| 7.1-7.5 | ✅ Complete | `sequencersessionscope.py::SequencerSessionScope` |
| 8.1-8.4 | ✅ Complete | `sequencersessionscope.py::SequencerSessionScope.__enter__` |
| 9.1-9.7 | ✅ Complete | `sequencersessionscope.py::SequencerSessionScope.__exit__` |
| 10.1-10.5 | ✅ Complete | `sequencermodulescope.py::SequencerModuleScope` |
| 11.1-11.5 | ✅ Complete | `sequencermodulescope.py::SequencerModuleScope.__enter__` |
| 12.1-12.7 | ✅ Complete | `sequencermodulescope.py::SequencerModuleScope.__exit__` |
| 13.1-13.5 | ✅ Complete | `sequencertestsetupscope.py::SequencerTestSetupScope` |
| 14.1-14.3 | ✅ Complete | `sequencertestsetupscope.py::SequencerTestSetupScope.__enter__` |
| 15.1-15.7 | ✅ Complete | `sequencertestsetupscope.py::SequencerTestSetupScope.__exit__` |
| 16.1-16.5 | ✅ Complete | `sequencertestscope.py::SequencerTestScope` |
| 17.1-17.3 | ✅ Complete | `sequencertestscope.py::SequencerTestScope` properties |
| 18.1-18.4 | ✅ Complete | `sequencertestscope.py::SequencerTestScope` context identifier |
| 19.1-19.6 | ✅ Complete | `sequencertestscope.py::SequencerTestScope._get_monikers_and_pivots` |
| 20.1-20.8 | ✅ Complete | `sequencertestscope.py::SequencerTestScope.__enter__` |
| 21.1-21.12 | ✅ Complete | `sequencertestscope.py::SequencerTestScope.__exit__` |
| 22.1-22.6 | ✅ Complete | `sequencertestscope.py::SequencerTestScope._test_scope_*` |
| 23.1-23.5 | ✅ Complete | `sequencertestscope.py::SequencerTestScope.begin_activity` |
| 24.1-24.5 | ✅ Complete | `sequencertestscope.py::SequencerTestScope.mark_activity` |
| 25.1-25.6 | ✅ Complete | `testactivity.py::TestActivity` context manager |
| 26.1-26.5 | ✅ Complete | `testactivity.py::TestActivity` properties |
| 27.1-27.5 | ✅ Complete | `testactivity.py::TestActivity.as_dict`, `as_json` |
| 28.1-28.5 | ✅ Complete | `testactivity.py::TestActivity.finalize` |
| 29.1-29.5 | ✅ Complete | Scope naming conventions |
| 30.1-30.5 | ✅ Complete | Exception classification |
| 31.1-31.4 | ✅ Complete | Traceback detail handling |
| 32.1-32.4 | ✅ Complete | Scope stack integrity |
| 33.1-33.5 | ✅ Complete | Result recording timing |
| 34.1-34.4 | ✅ Complete | Byproducts folder management |
| 35.1-35.9 | ✅ Complete | Logging requirements |

---

## Test Coverage Summary

| Component | Unit Tests | Integration Tests | Property Tests |
|-----------|------------|-------------------|----------------|
| `SequencerScopeBase` | ✅ | ⬜ | ⬜ |
| `SequencerSessionScope` | ⚠️ Partial | ⬜ | ⬜ |
| `SequencerModuleScope` | ⚠️ Partial | ⬜ | ⬜ |
| `SequencerTestSetupScope` | ⚠️ Partial | ⬜ | ⬜ |
| `SequencerTestScope` | ✅ | ⬜ | ⬜ |
| `TestActivity` | ✅ | ⬜ | ⬜ |
| Scope Hierarchy | ⬜ | ⬜ | ⬜ |
| Failure Propagation | ⬜ | ⬜ | ⬜ |

**Legend:** ✅ = Complete, ⚠️ = Partial, ⬜ = Not Started

---

## Known Limitations

1. **Sequential Scope Execution**: Scopes execute sequentially; parallel scope execution not supported
2. **Fixed Scope Hierarchy**: Four-level hierarchy is fixed; custom scope types not supported
3. **No Scope Timeouts**: No built-in timeout mechanism for scope execution
4. **Limited Activity Nesting**: Activities cannot be nested within other activities
5. **Single Activity File**: All activities for a test written to single file; no rotation support
6. **No Scope State Persistence**: Scope state not persisted across test run restarts

