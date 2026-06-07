# Command Line Interface - Tasks Document

## Overview

This document tracks the implementation status of the Command Line Interface (CLI) system and identifies enhancement opportunities for future development. The CLI provides a hierarchical command structure for running test collections, querying test information, managing test jobs, launching testing services, and providing utility commands for automation pipelines. It is built on the `ccai.arcli` framework with decorator-based command definition and reusable option groups.

## Implementation Status

### Completed Tasks

#### Root Command Entry Point (`testbase_command.py`)
- [x] Implement root command with `testbase` entry point
  - Define `@arcli.entry("testbase")` decorator for entry point
  - Call `initialize_testbase_runtime()` on invocation
  - _Requirements: 1.1, 1.2_

- [x] Implement verbosity option handling
  - Define `-v`/`--verbose` option with `OptionMode.Counter`
  - Map verbose=0 to WARNING level with interactive console enabled
  - Map verbose=1 to INFO level with interactive console disabled
  - Map verbose=2 to DEBUG level with interactive console disabled
  - Map verbose>=3 to NOTSET level with interactive console disabled
  - Override `AM_INTERACTIVE_CONSOLE` and `AM_LOG_LEVEL_CONSOLE` via `ThisApplicationSingleton`
  - _Requirements: 1.3, 1.4, 1.5, 1.6, 1.7_

- [x] Implement command group registration
  - Add `group_testbase_services` to root command
  - Add `group_testbase_testing` to root command
  - Add `group_testbase_utilities` to root command
  - _Requirements: 2.1, 2.2, 2.3_

#### Option Groups (`options.py`)
- [x] Implement RootOptionGroup
  - Define `--root` option with default=None
  - Support `help_fill` for action-specific help text
  - _Requirements: 18.1, 19.1, 19.3_

- [x] Implement OutputOptionGroup
  - Define `-o`/`--output` option for output directory
  - Define `--start` option for start timestamp
  - Define `--runid` option for run identifier
  - _Requirements: 18.2, 4.1, 4.2, 4.3_

- [x] Implement BuildOptionGroup
  - Define `--branch` option for build branch name
  - Define `--build` option for build name
  - Define `--flavor` option for build flavor
  - _Requirements: 18.3, 5.1, 5.2, 5.3_

- [x] Implement JobOptionGroup
  - Define `--job-id` option for job identifier
  - Define `--job-initiator` option for job initiator
  - Define `--job-label` option for job label
  - Define `--job-name` option for job name
  - Define `--job-owner` option for job owner
  - _Requirements: 18.4, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] Implement LoggingOptionGroup
  - Define `--console-level` option with Choice validator for log levels
  - Define `--logfile-level` option with Choice validator for log levels
  - _Requirements: 18.5, 7.1, 7.2, 7.3_

- [x] Implement DiagnosticOptionGroup
  - Define `--debugger` option with choices `pdb` or `debugpy`
  - Define `--breakpoint` option with choices `test-discovery` or `testrun-start`
  - Define `--prerun-diagnostic` boolean option
  - Define `--postrun-diagnostic` boolean option
  - _Requirements: 18.6, 8.1, 8.2, 8.3, 8.4_

- [x] Implement FilteringOptionGroup
  - Define `-i`/`--includes` option with `OptionMode.Multiple`
  - Define `-x`/`--excludes` option with `OptionMode.Multiple`
  - Define `--include-marker-exp` option with `OptionMode.Multiple`
  - Define `--exclude-marker-exp` option with `OptionMode.Multiple`
  - _Requirements: 18.7, 3.3, 3.4, 3.5, 3.6_

- [x] Implement DebugOptionGroup
  - Define `--debug` boolean option
  - _Requirements: 18.8_

#### Testing Run Command (`cmdtree/testing/run.py`)
- [x] Implement run command with option group attachments
  - Attach RootOptionGroup with help_fill for "run" action
  - Attach FilteringOptionGroup with help_fill for "run" action
  - Attach OutputOptionGroup, BuildOptionGroup, JobOptionGroup
  - Attach LoggingOptionGroup, DiagnosticOptionGroup
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] Implement runtime option overrides
  - Override build branch, name, flavor when provided
  - Override job id, initiator, label, name, owner when provided
  - Override console and logfile log levels when provided
  - Override output directory, start time, run id when provided
  - Override debug breakpoints and debugger when provided
  - Override prerun/postrun diagnostics when provided
  - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7_

- [x] Implement path resolution and validation
  - Expand environment variables with `os.path.expandvars`
  - Expand user home with `os.path.expanduser`
  - Convert to absolute path with `os.path.abspath`
  - Raise ValueError when path does not exist
  - Include original and expanded paths in error message
  - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 3.7_

- [x] Implement default root handling
  - Use AM_TESTROOT environment variable when root not specified
  - Default to current directory when neither specified
  - _Requirements: 3.8_

- [x] Implement Python path extension
  - Prepend test root parent directory to Python path
  - _Requirements: 3.9_

- [x] Implement marker expression parsing
  - Prefix include expressions with "+" and parse
  - Prefix exclude expressions with "-" and parse
  - Strip surrounding quotes from expressions
  - Pass parsed expressions as metafilters to TestJob
  - _Requirements: 22.1, 22.2, 22.3_

- [x] Implement test execution flow
  - Initialize test results recording
  - Obtain TestJob type from ConfiguredSuperFactorySingleton
  - Create TestJob context manager with configured options
  - Execute TestJob and capture result code
  - Exit with result code from TestJob
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 23.1, 23.2, 24.1, 24.2, 24.4_

#### Testing Query Command (`cmdtree/testing/query.py`)
- [x] Implement query command with option group attachments
  - Attach RootOptionGroup with help_fill for "query" action
  - Attach FilteringOptionGroup with help_fill for "query" action
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [x] Implement path resolution and validation
  - Same path resolution logic as run command
  - Raise ValueError when path does not exist
  - _Requirements: 10.7_

- [x] Implement query output format
  - Print "Tests:" header followed by test names
  - Print test names indented with 4 spaces
  - Print parameter subscriptions indented with 8 spaces
  - Print "IMPORT ERRORS:" header to stderr when errors occur
  - Print import error filenames indented with 4 spaces to stderr
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

#### Testing Jobs Group (`cmdtree/testing/jobs.py`)
- [x] Implement jobs group container
  - Define `@arcli.group("jobs")` decorator
  - _Requirements: 12.1_

- [x] Implement jobs list command
  - Accept `--root` option for test root directory
  - Accept `-f`/`--filter` option for filtering jobs
  - Accept `--debug` boolean option
  - _Requirements: 12.2, 13.1, 13.2, 13.3_

- [x] Implement jobs show command
  - Accept `--root` option for test root directory
  - Require `-j`/`--job` option for job identifier
  - Accept `--debug` boolean option
  - _Requirements: 12.3, 14.1, 14.2, 14.3_

- [x] Implement jobs run command
  - Require `-j`/`--job` option for job identifier
  - Validate job format as `package.module@JobClass`
  - Raise ValueError for invalid job format
  - Raise ArgumentError when job module cannot be imported
  - Raise ArgumentError when job class does not exist
  - Accept `--root`, output, build, and logging options
  - Exit with result code from TestJob
  - _Requirements: 12.4, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 23.3, 23.4_

#### Services Results Command (`cmdtree/services/results.py`)
- [x] Implement results server command
  - Accept `--directory` option for results directory
  - Accept `--bind` option for IP address (default: all interfaces)
  - Accept `--port` option for port number (default: 8880)
  - Use `<presence_dir>/results` as default directory
  - Print startup message with port and directory
  - Run server indefinitely until terminated
  - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7_

#### Utilities Timestamp Command (`cmdtree/utilities/timestamp.py`)
- [x] Implement timestamp command
  - Print current timestamp in `YYYY-MM-DDTHH:MM:SS.ffffff` format
  - Require no options
  - _Requirements: 17.1, 17.2, 17.3_

#### Help Generation
- [x] Implement automatic help generation
  - Generate help text for all commands and groups via arcli framework
  - Display help when `--help` is specified
  - Include descriptions for all options
  - Include default values where applicable
  - _Requirements: 25.1, 25.2, 25.3, 25.4_

---

### In Progress

_No tasks currently in progress._

---

### Planned Tasks

#### Jobs List Command Implementation
- [ ] Complete jobs list command functionality
  - Implement job discovery from test root
  - Implement filter expression matching
  - Display job names and descriptions
  - Support debug output mode
  - _Requirements: 13.1, 13.2, 13.3_

#### Jobs Show Command Implementation
- [ ] Complete jobs show command functionality
  - Load and display job configuration details
  - Show job includes/excludes patterns
  - Show job metadata and options
  - Support debug output mode
  - _Requirements: 14.1, 14.2, 14.3_

#### Test Coverage
- [x] Add unit tests for option groups
  - Test RootOptionGroup field definitions
  - Test OutputOptionGroup field definitions
  - Test BuildOptionGroup field definitions
  - Test JobOptionGroup field definitions
  - Test LoggingOptionGroup field definitions
  - Test DiagnosticOptionGroup field definitions
  - Test FilteringOptionGroup field definitions
  - Test DebugOptionGroup field definitions
  - _Requirements: 18.1-18.8_

- [x] Add unit tests for root command
  - Test verbosity level mapping
  - Test runtime initialization call
  - Test variable override application
  - _Requirements: 1.1-1.7_

- [x] Add unit tests for run command
  - Test option override application
  - Test path resolution and validation
  - Test marker expression parsing
  - Test default root handling
  - _Requirements: 3.1-3.9, 20.1-20.7, 21.1-21.5, 22.1-22.3_

- [x] Add unit tests for query command
  - Test output format structure
  - Test import error reporting
  - Test path validation
  - _Requirements: 10.1-10.7, 11.1-11.5_

- [ ] Add unit tests for jobs commands
  - Test job format validation
  - Test import error handling
  - Test class existence validation
  - _Requirements: 15.1-15.7_

- [x] Add unit tests for services results command
  - Test default directory resolution
  - Test server configuration
  - _Requirements: 16.1-16.7_

- [ ] Add unit tests for utilities timestamp command
  - Test timestamp format
  - _Requirements: 17.1-17.3_

#### Integration Testing
- [ ] Add integration tests for end-to-end command execution
  - Test `testbase testing run` with sample tests
  - Test `testbase testing query` output validation
  - Test `testbase testing jobs run` with sample job
  - Test `testbase services results` server startup
  - _Requirements: 9.1-9.5, 11.1-11.5, 15.7, 16.6-16.7_

- [ ] Add integration tests for option combinations
  - Test multiple include/exclude expressions
  - Test marker expression parsing
  - Test build metadata propagation
  - Test job identification propagation
  - _Requirements: 3.3-3.6, 5.1-5.3, 6.1-6.5_

#### Documentation Enhancements
- [ ] Add comprehensive docstrings
  - Document all option groups and their fields
  - Document command functions and parameters
  - Document help text customization mechanism

- [ ] Add usage examples to command help
  - Add examples for common run scenarios
  - Add examples for query filtering
  - Add examples for job execution

#### Feature Enhancements
- [ ] Support for configuration file loading
  - Load default options from configuration file
  - Support project-level configuration
  - Support user-level configuration

- [ ] Support for output format options
  - Add JSON output format for query command
  - Add YAML output format for query command
  - Add machine-readable output for automation

- [ ] Support for parallel test execution options
  - Add `--parallel` option for parallel execution
  - Add `--workers` option for worker count
  - Add `--timeout` option for test timeout

---

## Enhancement Opportunities

### Short-term Improvements

1. **Complete Jobs List/Show Commands**
   - Implement job discovery mechanism
   - Display job configuration details
   - Support filtering and debug output

2. **Output Format Options**
   - Add JSON/YAML output for query command
   - Support machine-readable formats for CI/CD integration
   - Add `--format` option to relevant commands

3. **Configuration File Support**
   - Load default options from `.testbase.yaml` or similar
   - Support project and user-level configuration
   - Reduce command-line verbosity for common scenarios

### Medium-term Improvements

1. **Parallel Execution Support**
   - Add parallel test execution options
   - Support worker pool configuration
   - Add timeout and retry options

2. **Progress Reporting**
   - Add progress bar for long-running operations
   - Support quiet mode for CI/CD environments
   - Add summary statistics output

3. **Shell Completion**
   - Generate shell completion scripts
   - Support bash, zsh, and fish shells
   - Auto-complete test names and job identifiers

### Long-term Improvements

1. **Interactive Mode**
   - Add interactive test selection
   - Support test re-run on failure
   - Add watch mode for continuous testing

2. **Remote Execution**
   - Support remote test execution
   - Add distributed test coordination
   - Support cloud-based test runners

3. **Plugin System**
   - Support custom command plugins
   - Allow third-party command extensions
   - Provide plugin discovery mechanism

---

## Requirements Traceability

| Requirement | Status | Implementation Location |
|-------------|--------|------------------------|
| 1.1-1.2 | ✅ Complete | `testbase_command.py::testbase_root_command` |
| 1.3-1.7 | ✅ Complete | `testbase_command.py::testbase_root_command` (verbosity) |
| 2.1-2.4 | ✅ Complete | `testbase_command.py` (group registration) |
| 3.1-3.9 | ✅ Complete | `cmdtree/testing/run.py::command_testbase_testing_run` |
| 4.1-4.4 | ✅ Complete | `options.py::OutputOptionGroup`, `run.py` (overrides) |
| 5.1-5.4 | ✅ Complete | `options.py::BuildOptionGroup`, `run.py` (overrides) |
| 6.1-6.6 | ✅ Complete | `options.py::JobOptionGroup`, `run.py` (overrides) |
| 7.1-7.4 | ✅ Complete | `options.py::LoggingOptionGroup`, `run.py` (overrides) |
| 8.1-8.6 | ✅ Complete | `options.py::DiagnosticOptionGroup`, `run.py` (overrides) |
| 9.1-9.5 | ✅ Complete | `cmdtree/testing/run.py` (execution flow) |
| 10.1-10.7 | ✅ Complete | `cmdtree/testing/query.py::command_testbase_testing_query` |
| 11.1-11.5 | ✅ Complete | `cmdtree/testing/query.py` (output format) |
| 12.1-12.4 | ✅ Complete | `cmdtree/testing/jobs.py` (group and commands) |
| 13.1-13.3 | ⚠️ Partial | `cmdtree/testing/jobs.py::command_testing_jobs_list` (stub) |
| 14.1-14.3 | ⚠️ Partial | `cmdtree/testing/jobs.py::command_testbase_testing_jobs_show` (stub) |
| 15.1-15.7 | ✅ Complete | `cmdtree/testing/jobs.py::command_testbase_testing_jobs_run` |
| 16.1-16.7 | ✅ Complete | `cmdtree/services/results.py::command_testbase_services_results` |
| 17.1-17.3 | ✅ Complete | `cmdtree/utilities/timestamp.py::command_testbase_utilities_timestamp` |
| 18.1-18.8 | ✅ Complete | `options.py` (all option groups) |
| 19.1-19.4 | ✅ Complete | `options.py` (help_fill support) |
| 20.1-20.7 | ✅ Complete | `cmdtree/testing/run.py` (runtime overrides) |
| 21.1-21.5 | ✅ Complete | `cmdtree/testing/run.py` (path resolution) |
| 22.1-22.3 | ✅ Complete | `cmdtree/testing/run.py` (marker parsing) |
| 23.1-23.4 | ✅ Complete | `cmdtree/testing/run.py`, `jobs.py` (factory integration) |
| 24.1-24.4 | ✅ Complete | `cmdtree/testing/run.py`, `jobs.py` (exit codes) |
| 25.1-25.4 | ✅ Complete | arcli framework (help generation) |

---

## Test Coverage Summary

| Component | Unit Tests | Integration Tests |
|-----------|------------|-------------------|
| Root Command | ✅ | ⬜ |
| Option Groups | ✅ | ⬜ |
| Testing Run Command | ✅ | ⬜ |
| Testing Query Command | ⬜ | ⬜ |
| Testing Jobs Group | ⬜ | ⬜ |
| Services Results Command | ⬜ | ⬜ |
| Utilities Timestamp Command | ⬜ | ⬜ |
| Path Resolution | ✅ | ⬜ |
| Marker Expression Parsing | ✅ | ⬜ |
| Runtime Option Overrides | ✅ | ⬜ |

**Legend:** ✅ = Complete, ⚠️ = Partial, ⬜ = Not Started

---

## Known Limitations

1. **Jobs List/Show Incomplete**: The `jobs list` and `jobs show` commands are defined but not fully implemented
2. **No Configuration File Support**: Users must specify all options via command line or environment variables
3. **No Output Format Options**: Query command only supports text output, no JSON/YAML
4. **No Parallel Execution**: Tests run sequentially, no built-in parallel execution support
5. **No Shell Completion**: No auto-completion scripts for shell environments
6. **No Interactive Mode**: No interactive test selection or watch mode
7. **Limited Error Context**: Some error messages could provide more context for debugging

---

## File Structure

```
source/packages/ccai/testbase/cli/
├── __init__.py                    # Package initialization
├── options.py                     # Reusable option groups
├── testbase_command.py            # Root command entry point
└── cmdtree/
    ├── testing/
    │   ├── __init__.py            # Testing group definition
    │   ├── run.py                 # Run command
    │   ├── query.py               # Query command
    │   └── jobs.py                # Jobs subgroup
    ├── services/
    │   ├── __init__.py            # Services group definition
    │   └── results.py             # Results server command
    └── utilities/
        ├── __init__.py            # Utilities group definition
        └── timestamp.py           # Timestamp command
```
