# Diagnostics System - Requirements Document

## Introduction

The Diagnostics System provides a framework for capturing diagnostic information at key points during test execution. It enables integration couplings to collect and store diagnostic data about the test environment, devices, and system state at predefined stages of the test run lifecycle. The system supports pre-run diagnostics (captured before test execution begins) and post-run diagnostics (captured after test execution completes). This diagnostic capability is essential for debugging test failures, auditing test environment conditions, collecting device logs and status information, and supporting post-mortem analysis of test runs.

## Glossary

- **DiagnosticLabel**: A class containing constants that identify well-known diagnostic stages in the test execution lifecycle
- **RuntimeConfigPaths**: A class containing configuration paths for diagnostic runtime information within the application's configuration tree
- **Prerun_Diagnostic**: A diagnostic capture point that occurs before test execution begins, identified by the label "prerun-diagnostic"
- **Postrun_Diagnostic**: A diagnostic capture point that occurs after test execution completes, identified by the label "postrun-diagnostic"
- **Diagnostic_Level**: An integer value (1-9) controlling the verbosity of captured diagnostics, where higher values indicate more detailed capture
- **Diagnostic_Folder**: The output directory path where diagnostic information is written by integration couplings
- **IntegrationCoupling**: A base class for integration types that provides the abstract diagnostic capture interface
- **DiagnosticOptionGroup**: A CLI option group providing command-line options for controlling diagnostic behavior during test runs
- **TestSequencer**: The component that orchestrates diagnostic capture by iterating over registered integrations
- **TestJob**: The component that fires diagnostic capture events at appropriate points in the test lifecycle

## Requirements

### Requirement 1: Diagnostic Label Constants

**User Story:** As a framework developer, I want well-defined constants for diagnostic stages, so that diagnostic capture points are consistently identified across the framework.

#### Acceptance Criteria

1. THE DiagnosticLabel class SHALL define a PRERUN_DIAGNOSTIC constant with the string value "prerun-diagnostic"
2. THE DiagnosticLabel class SHALL define a POSTRUN_DIAGNOSTIC constant with the string value "postrun-diagnostic"
3. THE diagnostic label constants SHALL be accessible as class attributes without instantiation
4. THE diagnostic label constants SHALL be string type values

### Requirement 2: Runtime Configuration Paths

**User Story:** As a framework developer, I want well-defined configuration paths for diagnostic settings, so that diagnostic runtime information can be stored and retrieved consistently.

#### Acceptance Criteria

1. THE RuntimeConfigPaths class SHALL define a DIAGNOSTIC_PRERUN constant with the path "/configuration/runtime/diagnostics/prerun-diagnostic"
2. THE RuntimeConfigPaths class SHALL define a DIAGNOSTIC_POSTRUN constant with the path "/configuration/runtime/diagnostics/postrun-diagnostic"
3. THE configuration path constants SHALL be accessible as class attributes without instantiation
4. THE configuration path constants SHALL follow the hierarchical path format starting with "/configuration/runtime/diagnostics/"

### Requirement 3: CLI Diagnostic Options

**User Story:** As a test developer, I want command-line options to enable diagnostic capture, so that I can control diagnostic behavior when running tests.

#### Acceptance Criteria

1. THE DiagnosticOptionGroup SHALL provide a `--prerun-diagnostic` boolean option for enabling pre-run diagnostic capture
2. THE DiagnosticOptionGroup SHALL provide a `--postrun-diagnostic` boolean option for enabling post-run diagnostic capture
3. THE DiagnosticOptionGroup SHALL provide a `--debugger` option with choices 'pdb' or 'debugpy' for debugger selection
4. THE DiagnosticOptionGroup SHALL provide a `--breakpoint` option for specifying breakpoints to activate
5. WHEN `--prerun-diagnostic` is specified, THE System SHALL set the AM_DIAGNOSTICS_PRERUN environment knob (in `os.environ`) to a truthy value
6. WHEN `--postrun-diagnostic` is specified, THE System SHALL set the AM_DIAGNOSTICS_POSTRUN environment knob (in `os.environ`) to a truthy value

### Requirement 4: Integration Coupling Diagnostic Interface

**User Story:** As a framework developer, I want an abstract diagnostic method on integration couplings, so that each integration type can implement its own diagnostic capture logic.

#### Acceptance Criteria

1. THE IntegrationCoupling class SHALL define an abstract `diagnostic` class method
2. THE `diagnostic` method SHALL accept a `label` parameter identifying the diagnostic stage
3. THE `diagnostic` method SHALL accept a `level` parameter specifying the maximum diagnostic level (1-9)
4. THE `diagnostic` method SHALL accept a `diag_folder` parameter specifying the output directory for diagnostic files
5. WHEN `diagnostic` is called on the base IntegrationCoupling class, THE System SHALL raise an AbstractMethodError
6. THE error message SHALL indicate that the method must be overloaded by derived integration coupling types

### Requirement 5: Pre-Run Diagnostic Capture

**User Story:** As a test developer, I want diagnostic information captured before test execution, so that I can understand the initial state of the test environment.

#### Acceptance Criteria

1. WHEN pre-run diagnostics are enabled and `fire_diagnostic_capture_pre_testrun` is called, THE TestSequencer SHALL capture diagnostics for all registered integrations
2. THE TestSequencer SHALL use the DiagnosticLabel.PRERUN_DIAGNOSTIC label for pre-run diagnostic capture
3. THE TestSequencer SHALL resolve the diagnostic folder path through the injected IOutputContext (`get_diagnostics_dir`) with the prerun-diagnostic label
4. THE TestSequencer SHALL iterate over all registered integration couplings and call their `diagnostic` method
5. WHEN pre-run diagnostics are disabled, THE TestSequencer SHALL skip the diagnostic capture process

### Requirement 6: Post-Run Diagnostic Capture

**User Story:** As a test developer, I want diagnostic information captured after test execution, so that I can analyze the final state of the test environment.

#### Acceptance Criteria

1. WHEN post-run diagnostics are enabled and `fire_diagnostic_capture_post_testrun` is called, THE TestSequencer SHALL capture diagnostics for all registered integrations
2. THE TestSequencer SHALL use the DiagnosticLabel.POSTRUN_DIAGNOSTIC label for post-run diagnostic capture
3. THE TestSequencer SHALL resolve the diagnostic folder path through the injected IOutputContext (`get_diagnostics_dir`) with the postrun-diagnostic label
4. THE TestSequencer SHALL iterate over all registered integration couplings and call their `diagnostic` method
5. WHEN post-run diagnostics are disabled, THE TestSequencer SHALL skip the diagnostic capture process

### Requirement 7: Diagnostic Level Control

**User Story:** As a test developer, I want to control the verbosity of diagnostic capture, so that I can balance detail against performance and storage requirements.

#### Acceptance Criteria

1. THE diagnostic level parameter SHALL accept integer values from 1 to 9
2. WHEN diagnostic level is 1-3, THE integration coupling SHALL capture basic diagnostic information
3. WHEN diagnostic level is 4-6, THE integration coupling SHALL capture standard diagnostic information
4. WHEN diagnostic level is 7-9, THE integration coupling SHALL capture detailed diagnostic information
5. THE default diagnostic level SHALL be 9 (maximum detail) when not explicitly specified

### Requirement 8: Diagnostic Folder Structure

**User Story:** As a test developer, I want diagnostic files organized in a consistent folder structure, so that I can easily locate and analyze diagnostic information.

#### Acceptance Criteria

1. THE diagnostic folder structure SHALL be located under `<test_results_dir>/diagnostics/`
2. THE pre-run diagnostics SHALL be stored under `diagnostics/prerun-diagnostic/`
3. THE post-run diagnostics SHALL be stored under `diagnostics/postrun-diagnostic/`
4. EACH integration coupling SHALL create its own subfolder within the diagnostic folder
5. THE diagnostics folder SHALL be excluded from result traversal to prevent diagnostic data from being processed as test results

### Requirement 9: TestJob Diagnostic Fire Methods

**User Story:** As a framework developer, I want TestJob to orchestrate diagnostic capture at appropriate lifecycle points, so that diagnostics are captured at the correct times.

#### Acceptance Criteria

1. THE TestJob SHALL provide a `fire_diagnostic_capture_pre_testrun` method that delegates to the TestSequencer
2. THE TestJob SHALL provide a `fire_diagnostic_capture_post_testrun` method that delegates to the TestSequencer
3. THE `fire_diagnostic_capture_pre_testrun` method SHALL be called after integration setup and before test execution
4. THE `fire_diagnostic_capture_post_testrun` method SHALL be called after test execution and before finalization
5. THE fire methods SHALL accept an optional level parameter for controlling diagnostic verbosity

### Requirement 10: Diagnostic Capture Error Handling

**User Story:** As a test developer, I want diagnostic capture errors to be handled gracefully, so that diagnostic failures do not cause test runs to fail.

#### Acceptance Criteria

1. WHEN an error occurs during diagnostic capture, THE System SHALL catch the exception and log the error
2. WHEN an error occurs during diagnostic capture, THE System SHALL continue with test execution
3. THE error message SHALL include the full traceback for debugging purposes
4. THE diagnostic capture failure SHALL NOT cause the test run to fail or return a non-zero exit code

### Requirement 11: Environment Variable Integration

**User Story:** As a framework developer, I want diagnostic settings controlled via environment knobs read through the dependency-free `automojo.testbase.environment` module, so that diagnostic behavior can be configured programmatically without coupling the core to RuntimeVariables.

#### Acceptance Criteria

1. THE System SHALL read the AM_DIAGNOSTICS_PRERUN knob via `environment.diagnostics_prerun_enabled()` to control pre-run diagnostic capture
2. THE System SHALL read the AM_DIAGNOSTICS_POSTRUN knob via `environment.diagnostics_postrun_enabled()` to control post-run diagnostic capture
3. WHEN AM_DIAGNOSTICS_PRERUN resolves truthy, THE System SHALL enable pre-run diagnostic capture
4. WHEN AM_DIAGNOSTICS_POSTRUN resolves truthy, THE System SHALL enable post-run diagnostic capture
5. THE AM_DIAGNOSTICS_PRERUN / AM_DIAGNOSTICS_POSTRUN knobs SHALL be settable via CLI options through the runtime option override mechanism, which writes their string values into `os.environ` for the environment module to read

### Requirement 12: Custom Integration Diagnostic Implementation

**User Story:** As an integration developer, I want to implement custom diagnostic capture logic, so that my integration can capture relevant diagnostic information.

#### Acceptance Criteria

1. WHEN implementing a custom integration coupling, THE developer SHALL override the `diagnostic` class method
2. THE custom implementation SHALL create an integration-specific subfolder within the provided diagnostic folder
3. THE custom implementation SHALL respect the diagnostic level parameter to control capture verbosity
4. THE custom implementation SHALL write diagnostic files to the integration-specific subfolder
5. THE custom implementation SHALL handle any errors internally to prevent propagation to the test framework
