# Diagnostics System - Tasks Document

## Overview

This document tracks the implementation status of the Diagnostics System and identifies enhancement opportunities for future development. The diagnostics system provides a framework for capturing diagnostic information at key points during test execution. It enables integration couplings to collect and store diagnostic data about the test environment, devices, and system state at predefined stages of the test run lifecycle.

## Implementation Status

### Completed Tasks

#### DiagnosticLabel Class (`diagnostics.py`)
- [x] Implement `DiagnosticLabel` class
  - Define `PRERUN_DIAGNOSTIC` constant with value "prerun-diagnostic"
  - Define `POSTRUN_DIAGNOSTIC` constant with value "postrun-diagnostic"
  - Constants accessible as class attributes without instantiation
  - Constants are string type values
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

#### RuntimeConfigPaths Class (`diagnostics.py`)
- [x] Implement `RuntimeConfigPaths` class
  - Define `DIAGNOSTIC_PRERUN` constant with path "/configuration/runtime/diagnostics/prerun-diagnostic"
  - Define `DIAGNOSTIC_POSTRUN` constant with path "/configuration/runtime/diagnostics/postrun-diagnostic"
  - Constants accessible as class attributes without instantiation
  - Constants follow hierarchical path format
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

#### DiagnosticOptionGroup (`cli/options.py`)
- [x] Implement `DiagnosticOptionGroup` CLI option group
  - Provide `--prerun-diagnostic` boolean option for enabling pre-run diagnostic capture
  - Provide `--postrun-diagnostic` boolean option for enabling post-run diagnostic capture
  - Provide `--debugger` option with choices 'pdb' or 'debugpy'
  - Provide `--breakpoint` option for specifying breakpoints
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

#### Environment Knob Integration
- [x] Implement environment knob setting from CLI options
  - Set AM_DIAGNOSTICS_PRERUN (in `os.environ`) when `--prerun-diagnostic` is specified
  - Set AM_DIAGNOSTICS_POSTRUN (in `os.environ`) when `--postrun-diagnostic` is specified
  - Flags read back via `ccai.testbase.environment` (NOT RuntimeVariables)
  - _Requirements: 3.5, 3.6, 11.1, 11.2, 11.3, 11.4, 11.5_

#### IntegrationCoupling Diagnostic Interface (`coupling/integrationcoupling.py`)
- [x] Implement abstract `diagnostic` class method on IntegrationCoupling
  - Accept `label` parameter identifying the diagnostic stage
  - Accept `level` parameter specifying maximum diagnostic level (1-9)
  - Accept `diag_folder` parameter specifying output directory
  - Raise AbstractMethodError when called on base class
  - Error message indicates method must be overloaded
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

#### TestSequencer Diagnostic Capture (`sequencing/testsequencer.py`)
- [x] Implement `diagnostic_capture_pre_testrun` method
  - Check AM_DIAGNOSTICS_PRERUN via `environment.diagnostics_prerun_enabled()`
  - Use DiagnosticLabel.PRERUN_DIAGNOSTIC label
  - Resolve diagnostic folder path via injected IOutputContext (`get_diagnostics_dir`)
  - Iterate over registered integration couplings
  - Call `diagnostic` method on each integration
  - Skip capture when pre-run diagnostics disabled
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] Implement `diagnostic_capture_post_testrun` method
  - Check AM_DIAGNOSTICS_POSTRUN via `environment.diagnostics_postrun_enabled()`
  - Use DiagnosticLabel.POSTRUN_DIAGNOSTIC label
  - Resolve diagnostic folder path via injected IOutputContext (`get_diagnostics_dir`)
  - Iterate over registered integration couplings
  - Call `diagnostic` method on each integration
  - Skip capture when post-run diagnostics disabled
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

#### TestJob Fire Methods (`testjob.py`)
- [x] Implement `fire_diagnostic_capture_pre_testrun` method
  - Delegate to TestSequencer diagnostic capture
  - Accept optional level parameter
  - Call after integration setup, before test execution
  - _Requirements: 9.1, 9.3, 9.5_

- [x] Implement `fire_diagnostic_capture_post_testrun` method
  - Delegate to TestSequencer diagnostic capture
  - Accept optional level parameter
  - Call after test execution, before finalization
  - _Requirements: 9.2, 9.4, 9.5_

#### Error Handling
- [x] Implement diagnostic capture error handling
  - Catch exceptions during diagnostic capture
  - Log error with full traceback
  - Continue with test execution
  - Do not fail test run on diagnostic errors
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

#### Diagnostic Folder Structure
- [x] Implement diagnostic folder organization
  - Create folders under `<test_results_dir>/diagnostics/`
  - Pre-run diagnostics stored under `diagnostics/prerun-diagnostic/`
  - Post-run diagnostics stored under `diagnostics/postrun-diagnostic/`
  - Exclude diagnostics folder from result traversal
  - _Requirements: 8.1, 8.2, 8.3, 8.5_

---

### In Progress

_No tasks currently in progress._

---

### Planned Tasks

#### Test Coverage
- [x] Add unit tests for `DiagnosticLabel` constants
  - Verify PRERUN_DIAGNOSTIC value is "prerun-diagnostic"
  - Verify POSTRUN_DIAGNOSTIC value is "postrun-diagnostic"
  - Verify constants are string type
  - Verify constants accessible without instantiation
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] Add unit tests for `RuntimeConfigPaths` constants
  - Verify DIAGNOSTIC_PRERUN path value
  - Verify DIAGNOSTIC_POSTRUN path value
  - Verify paths follow hierarchical format
  - Verify constants accessible without instantiation
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] Add unit tests for `DiagnosticOptionGroup`
  - Test `--prerun-diagnostic` option parsing
  - Test `--postrun-diagnostic` option parsing
  - Test `--debugger` option with valid choices
  - Test `--breakpoint` option parsing
  - Test default values for all options
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] Add unit tests for `IntegrationCoupling.diagnostic` abstract method
  - Verify AbstractMethodError raised on base class
  - Verify error message content
  - Test method signature accepts required parameters
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] Add unit tests for TestSequencer diagnostic capture
  - Test pre-run capture when enabled
  - Test pre-run capture when disabled (skipped)
  - Test post-run capture when enabled
  - Test post-run capture when disabled (skipped)
  - Verify integration iteration
  - Verify diagnostic level propagation
  - _Requirements: 5.1-5.5, 6.1-6.5, 7.1-7.5_

- [x] Add unit tests for TestJob fire methods
  - Test `fire_diagnostic_capture_pre_testrun` delegation
  - Test `fire_diagnostic_capture_post_testrun` delegation
  - Test optional level parameter handling
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] Add unit tests for error handling
  - Test exception caught during diagnostic capture
  - Verify error logged with traceback
  - Verify test execution continues after error
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

#### Integration Testing
- [x] Add integration tests for end-to-end diagnostic capture
  - Run test with pre-run diagnostics enabled
  - Run test with post-run diagnostics enabled
  - Verify diagnostic folders created
  - Verify integration diagnostic methods called
  - _Requirements: 5.1-5.5, 6.1-6.5_

- [x] Add integration tests for CLI diagnostic options
  - Test `--prerun-diagnostic` flag sets AM_DIAGNOSTICS_PRERUN knob (in `os.environ`)
  - Test `--postrun-diagnostic` flag sets AM_DIAGNOSTICS_POSTRUN knob (in `os.environ`)
  - Test combined flags
  - _Requirements: 3.5, 3.6, 11.1-11.5_

- [x] Add integration tests for custom integration diagnostics
  - Create test integration coupling with diagnostic implementation
  - Verify diagnostic method called with correct parameters
  - Verify diagnostic files written to correct location
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

#### Documentation Enhancements
- [x] Add comprehensive docstrings to all public classes and methods
  - Document DiagnosticLabel constants
  - Document RuntimeConfigPaths constants
  - Document diagnostic method parameters and behavior
  - Include usage examples

- [x] Add inline code comments for complex logic
  - Document diagnostic capture flow
  - Document error handling strategy
  - Document folder structure creation

- [x] Create usage examples in `source/examples/`
  - Basic diagnostic capture usage
  - Custom integration diagnostic implementation
  - CLI diagnostic options usage
  - Diagnostic level usage patterns

#### Feature Enhancements
- [x] Support for custom diagnostic labels
  - Allow registration of custom diagnostic stages
  - Support custom diagnostic capture points
  - Maintain backward compatibility with existing labels

- [x] Support for diagnostic level configuration via CLI
  - Add `--diagnostic-level` CLI option
  - Allow per-integration level configuration
  - Default to level 9 when not specified
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] Support for diagnostic filtering
  - Filter diagnostics by integration type
  - Filter diagnostics by label
  - Support include/exclude patterns

- [x] Support for diagnostic compression
  - Compress diagnostic output files
  - Support configurable compression formats
  - Reduce storage requirements for large diagnostics
  - _Implementation: `diagnostics.py::CompressionFormat`, `diagnostics.py::DiagnosticCompression`_

- [x] Support for diagnostic streaming
  - Stream diagnostics to external systems
  - Support real-time diagnostic monitoring
  - Enable remote diagnostic collection
  - _Implementation: `diagnostic_streaming.py::DiagnosticStreamManager`, `diagnostic_streaming.py::DiagnosticStreamConfig`, `diagnostic_streaming.py::DiagnosticStreamProtocol`_

---

## Enhancement Opportunities

### Short-term Improvements

1. **Diagnostic Level CLI Option**
   - Add `--diagnostic-level` option to control verbosity
   - Allow fine-grained control over diagnostic detail
   - Document level meanings (1-3 basic, 4-6 standard, 7-9 detailed)

2. **Diagnostic Summary Report**
   - Generate summary of captured diagnostics
   - Include file counts and sizes per integration
   - Report any errors during capture

3. **Logging Improvements**
   - Add debug logging for diagnostic operations
   - Log diagnostic capture start/end times
   - Log per-integration diagnostic status

### Medium-term Improvements

1. **Selective Diagnostic Capture**
   - Enable/disable diagnostics per integration
   - Support integration-specific diagnostic levels
   - Allow runtime diagnostic configuration

2. **Diagnostic Metadata**
   - Capture metadata about diagnostic files
   - Include timestamps and capture duration
   - Track diagnostic file relationships

3. **Diagnostic Validation**
   - Validate diagnostic output format
   - Verify required diagnostic files present
   - Report missing or incomplete diagnostics

### Long-term Improvements

1. **Diagnostic Analysis Tools**
   - Provide tools for analyzing diagnostic data
   - Support comparison between diagnostic captures
   - Enable trend analysis across test runs

2. **Distributed Diagnostic Collection**
   - Support diagnostic capture from remote systems
   - Aggregate diagnostics from distributed test runs
   - Enable centralized diagnostic storage

3. **Diagnostic Visualization**
   - Generate visual representations of diagnostic data
   - Support timeline views of diagnostic events
   - Enable interactive diagnostic exploration

---

## Requirements Traceability

| Requirement | Status | Implementation Location |
|-------------|--------|------------------------|
| 1.1-1.4 | ✅ Complete | `diagnostics.py::DiagnosticLabel` |
| 2.1-2.4 | ✅ Complete | `diagnostics.py::RuntimeConfigPaths` |
| 3.1-3.4 | ✅ Complete | `cli/options.py::DiagnosticOptionGroup` |
| 3.5-3.6 | ✅ Complete | Runtime option override mechanism |
| 4.1-4.6 | ✅ Complete | `coupling/integrationcoupling.py::IntegrationCoupling.diagnostic` |
| 5.1-5.5 | ✅ Complete | `sequencing/testsequencer.py::diagnostic_capture_pre_testrun` |
| 6.1-6.5 | ✅ Complete | `sequencing/testsequencer.py::diagnostic_capture_post_testrun` |
| 7.1-7.5 | ✅ Complete | Diagnostic level parameter support |
| 8.1-8.3, 8.5 | ✅ Complete | Diagnostic folder structure |
| 8.4 | ⬜ Planned | Integration subfolder creation (per-integration) |
| 9.1-9.5 | ✅ Complete | `testjob.py::fire_diagnostic_capture_*` methods |
| 10.1-10.4 | ✅ Complete | Error handling in diagnostic capture |
| 11.1-11.5 | ✅ Complete | `environment.diagnostics_prerun_enabled` / `diagnostics_postrun_enabled` |
| 12.1-12.5 | ⬜ Planned | Custom integration diagnostic implementation guidance |

---

## Test Coverage Summary

| Component | Unit Tests | Integration Tests |
|-----------|------------|-------------------|
| `DiagnosticLabel` constants | ⬜ | N/A |
| `RuntimeConfigPaths` constants | ⬜ | N/A |
| `DiagnosticOptionGroup` | ⬜ | ⬜ |
| `IntegrationCoupling.diagnostic` | ⬜ | ⬜ |
| `TestSequencer.diagnostic_capture_pre_testrun` | ⬜ | ⬜ |
| `TestSequencer.diagnostic_capture_post_testrun` | ⬜ | ⬜ |
| `TestJob.fire_diagnostic_capture_pre_testrun` | ⬜ | ⬜ |
| `TestJob.fire_diagnostic_capture_post_testrun` | ⬜ | ⬜ |
| Error handling | ⬜ | ⬜ |
| CLI integration | ⬜ | ⬜ |
| Diagnostic folder structure | ⬜ | ⬜ |

**Legend:** ✅ = Complete, ⚠️ = Partial, ⬜ = Not Started

---

## Known Limitations

1. **No Diagnostic Level CLI Option**: Cannot specify diagnostic level from command line (defaults to 9)
2. **No Per-Integration Configuration**: Cannot enable/disable diagnostics per integration type
3. **No Diagnostic Validation**: No verification of diagnostic output completeness
4. **No Diagnostic Analysis Tools**: Manual analysis of diagnostic files required
5. **Limited Test Coverage**: Unit and integration tests not yet implemented

---

## File Structure

```
source/packages/ccai/testbase/
├── diagnostics.py              # DiagnosticLabel and RuntimeConfigPaths constants
├── diagnostic_streaming.py     # Diagnostic streaming to external systems
├── environment.py              # AM_DIAGNOSTICS_PRERUN/POSTRUN enable-flag accessors (os.environ)
├── testjob.py                  # TestJob with fire_diagnostic_capture_* methods
├── cli/
│   └── options.py              # DiagnosticOptionGroup CLI options
├── coupling/
│   └── integrationcoupling.py  # IntegrationCoupling.diagnostic() abstract method
├── output/
│   └── outputcontext.py        # IOutputContext / SimpleOutputContext.get_diagnostics_dir
└── sequencing/
    └── testsequencer.py        # Diagnostic capture implementation

source/tests/ccai_tests/testbase/
├── test_diagnostics.py         # Unit tests for diagnostics (planned)
└── test_diagnostic_streaming.py # Unit tests for diagnostic streaming

source/examples/
├── debug_diagnostics.py        # Example usage of diagnostics (planned)
└── debug_diagnostics_streaming.py # Example usage of diagnostic streaming
```

> The presence-folder-rooted diagnostics path is an integration concern, not a testbase-core concern. It is provided by `RuntimeOutputContext.get_diagnostics_dir` in `codecraftai-integration-runtime` (wired through `IntegratedTestJob`), which delegates to the well-known presence-folder paths. The testbase core only knows the injected `IOutputContext` seam.
