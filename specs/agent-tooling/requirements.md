# Agent Tooling - Requirements Document

## Introduction

The Agent Tooling feature provides a set of CLI commands under the `testbase agents` command group that are designed
for consumption by AI coding agents and automation scripts. These commands extract, transform, and present test result
data in compact, machine-readable formats that fit within agent context windows. Unlike the human-facing CLI commands,
the agent commands prioritize information density and structured output over visual formatting, making them ideal for
automated analysis, triage, and reporting workflows. The commands operate on the standard TestBase result artifacts
(summary JSON, result stream JSOS) and do not require a running test session.

## Glossary

- **Summary_File**: A `testrun_summary.json` file produced by the ResultRecorder, containing metadata (build, pipeline, job), timing, overall result, and aggregate pass/fail/skip/error counters
- **Results_File**: A `testrun_results_stream.jsos` file containing a sequence of JSON objects (one per line group) that describe the hierarchical test execution tree, including test containers and individual test outcomes
- **JSOS**: JSON Stream of Objects — a file format where each top-level JSON object is separated by a blank line, used for streaming result recording
- **Test_Name**: The fully qualified name of a test in the format `package.module#testname`, uniquely identifying a test within the result tree
- **Result_Code**: One of `PASSED`, `FAILED`, `ERRORED`, `SKIPPED`, or `UNSET` indicating the outcome of a test
- **Compact_Output**: A condensed text representation of structured data optimized for agent consumption, using key-value pairs and concise formatting

## Requirements

### Requirement 1: Agents Command Group

**User Story:** As a framework developer, I want a dedicated `agents` command group, so that agent-oriented commands are organized separately from human-facing commands.

#### Acceptance Criteria

1. THE CLI SHALL provide an `agents` command group under the root `testbase` command
2. THE `agents` command group SHALL contain subgroups for different result artifact types
3. WHEN the `agents` command group is invoked without a subcommand, THE System SHALL display help listing available subgroups
4. THE `agents` command group SHALL not require runtime initialization or test environment activation

### Requirement 2: Summary Extract Command

**User Story:** As an AI agent, I want to extract test summary information from a summary file into a compact form, so that I can quickly understand the outcome of a test run without parsing raw JSON.

#### Acceptance Criteria

1. THE `agents summary extract` command SHALL accept a `--summary-file` option specifying the path to a `testrun_summary.json` file
2. THE command SHALL parse the summary JSON and output a compact representation of key metadata
3. THE compact output SHALL include the overall result (PASSED/FAILED)
4. THE compact output SHALL include the start and stop timestamps
5. THE compact output SHALL include the result detail counters: passed, failed, errors, skipped, and total
6. THE compact output SHALL include the job identifier, name, and type when available
7. THE compact output SHALL include the build branch and build name when available
8. WHEN the summary file does not exist, THE System SHALL print a clear error message and exit with a non-zero code
9. WHEN the summary file contains invalid JSON, THE System SHALL print a clear error message and exit with a non-zero code

### Requirement 3: Test Result Extract Command

**User Story:** As an AI agent, I want to extract the detailed result for a specific test from a results file, so that I can analyze individual test outcomes including errors and timing.

#### Acceptance Criteria

1. THE `agents testresult extract` command SHALL accept a `--results-file` option specifying the path to a `testrun_results_stream.jsos` file
2. THE command SHALL accept a `--testname` option specifying the fully qualified test name to extract
3. THE command SHALL parse the JSOS results stream and locate the final result entry for the specified test
4. THE compact output SHALL include the test name, result code, start time, and stop time
5. THE compact output SHALL include error details and messages when the test result contains them
6. WHEN the test name is not found in the results file, THE System SHALL print a clear error message and exit with a non-zero code
7. WHEN the results file does not exist, THE System SHALL print a clear error message and exit with a non-zero code
8. WHEN multiple result entries exist for the same test (UNSET followed by final), THE command SHALL return only the final result entry

### Requirement 4: Failures List Command

**User Story:** As an AI agent, I want to list all failed and errored tests from a results file, so that I can quickly identify which tests need attention without scanning the entire result set.

#### Acceptance Criteria

1. THE `agents testresult failures` command SHALL accept a `--results-file` option specifying the path to a `testrun_results_stream.jsos` file
2. THE command SHALL parse the JSOS results stream and collect all test entries with a final result of FAILED or ERRORED
3. FOR EACH failed or errored test, THE compact output SHALL include the test name and result code
4. FOR EACH failed or errored test, THE compact output SHALL include a brief error summary when available
5. WHEN no failures or errors are found, THE System SHALL print a message indicating all tests passed
6. THE output SHALL be ordered by the sequence in which the tests appear in the results stream

### Requirement 5: Test Result List Command

**User Story:** As an AI agent, I want to list all tests and their results from a results file, so that I can get a complete overview of the test run outcomes.

#### Acceptance Criteria

1. THE `agents testresult list` command SHALL accept a `--results-file` option specifying the path to a `testrun_results_stream.jsos` file
2. THE command SHALL parse the JSOS results stream and collect the final result for each test entry (rtype TEST)
3. FOR EACH test, THE compact output SHALL include the test name and final result code
4. THE command SHALL accept an optional `--result-filter` option to filter by result code (e.g., `PASSED`, `FAILED`, `SKIPPED`)
5. THE command SHALL exclude test container entries (rtype TEST_CONTAINER and JOB) from the output
6. THE output SHALL be ordered by the sequence in which the tests appear in the results stream

### Requirement 6: Summary Compare Command

**User Story:** As an AI agent, I want to compare two test summary files, so that I can identify regressions or improvements between test runs.

#### Acceptance Criteria

1. THE `agents summary compare` command SHALL accept a `--baseline` option specifying the path to the baseline summary file
2. THE command SHALL accept a `--current` option specifying the path to the current summary file
3. THE compact output SHALL include the overall result change (e.g., PASSED->FAILED, FAILED->PASSED, or no change)
4. THE compact output SHALL include the delta for each result counter (passed, failed, errors, skipped, total)
5. THE compact output SHALL indicate whether the run is a regression (more failures), improvement (fewer failures), or stable
6. WHEN either summary file does not exist or contains invalid JSON, THE System SHALL print a clear error message and exit with a non-zero code

### Requirement 7: Configuration Extract Command

**User Story:** As an AI agent, I want to extract key configuration information from a test run, so that I can understand the environment and settings under which tests were executed.

#### Acceptance Criteria

1. THE `agents config extract` command SHALL accept a `--config-file` option specifying the path to a `startup-configuration.json` file
2. THE command SHALL parse the configuration JSON and output a compact representation of key settings
3. THE compact output SHALL include the test root path
4. THE compact output SHALL include logging levels for console and file
5. THE compact output SHALL include any active debug settings (debugger, breakpoints)
6. WHEN the configuration file does not exist, THE System SHALL print a clear error message and exit with a non-zero code

### Requirement 8: Compact Output Format

**User Story:** As a framework developer, I want agent command output to follow a consistent compact format, so that agents can reliably parse the output across all agent commands.

#### Acceptance Criteria

1. ALL agent commands SHALL output data in a consistent key-value text format
2. THE output format SHALL use one key-value pair per line in the form `key: value`
3. THE output format SHALL use indentation to represent nested sections
4. THE output format SHALL not include decorative elements such as boxes, horizontal rules, or color codes
5. THE output format SHALL be deterministic — the same input SHALL always produce the same output
6. WHEN a field value is not available or not set, THE output SHALL omit that field rather than showing placeholder text

### Requirement 9: File Path Resolution

**User Story:** As an AI agent, I want file paths to be resolved consistently, so that relative and absolute paths both work correctly.

#### Acceptance Criteria

1. ALL file path options SHALL support both absolute and relative paths
2. THE System SHALL expand environment variables in file paths
3. THE System SHALL expand user home directory references in file paths
4. THE System SHALL resolve relative paths against the current working directory
5. WHEN a resolved path does not exist, THE System SHALL include the resolved path in the error message

### Requirement 10: Error Output Convention

**User Story:** As an AI agent, I want errors to be reported in a consistent format, so that I can programmatically detect and handle error conditions.

#### Acceptance Criteria

1. WHEN an error occurs, THE System SHALL print the error message to stderr
2. WHEN an error occurs, THE System SHALL exit with a non-zero exit code
3. THE error output SHALL follow the format `ERROR: <description>`
4. THE error output SHALL not include stack traces or debug information unless a `--verbose` flag is provided
5. WHEN a file is not found, THE error message SHALL include the resolved file path
