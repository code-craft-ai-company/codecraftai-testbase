# Test Entry Points - Tasks Document

## Overview

This document tracks the implementation status of the Test Entry Points system and identifies enhancement opportunities for future development. The entry point system provides standardized mechanisms for initiating test execution, handling critical initialization tasks including runtime environment setup, test module name resolution and registration, Python path management, command-line argument parsing, and test job creation and execution orchestration.

## Implementation Status

### Completed Tasks

#### Generic Test Entry Point (`entrypoints.py`)
- [x] Implement `generic_test_entrypoint` function
  - Accept optional `job_type` parameter defaulting to `DefaultTestJob`
  - Call `initialize_testbase_runtime()` for runtime setup
  - Call `activate_profile_job()` with `JobType.TestRun`
  - Call `initialize_testbase_results()` for results configuration
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] Implement command-line argument parsing
  - Define `-i`/`--include` option with `action="append"` for include expressions
  - Define `-x`/`--exclude` option with `action="append"` for exclude expressions
  - Define `--console-level` option with `LOG_LEVEL_NAMES` choices (default: "INFO")
  - Define `--logfile-level` option with `LOG_LEVEL_NAMES` choices (default: "DEBUG")
  - Default includes to `["*"]` when no include expressions provided
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] Implement environment context configuration
  - Obtain `ThisApplicationSingleton()` for application context
  - Access environment through context lookup at "/environment"
  - Set "jobtype" key to "testrun"
  - Set "output_directory" key to test results path
  - _Requirements: 17.1, 17.2, 17.3, 17.4_

- [x] Implement output directory configuration
  - Call `get_path_for_testresults()` to obtain results directory
  - Create results directory if it does not exist
  - _Requirements: 12.1, 12.2, 12.3, 12.4_

- [x] Implement logger configuration
  - Obtain enhanced logger using `getEnhancedLogger()`
  - Assign logger to `automojo.testbase` module's logger attribute
  - _Requirements: 13.1, 13.2_

- [x] Implement test job execution
  - Create TestJob instance using specified `job_type`
  - Use TestJob as context manager for resource management
  - Call `execute()` method to run tests
  - Pass result code to `sys.exit()`
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 16.1, 16.2, 16.3, 16.4_

#### Module Resolution (`utilities.py`)
- [x] Implement `find_testmodule_root` function
  - Walk up directory tree from module's location
  - Identify test root by presence of `__testroot__.py` marker file
  - Raise `ConfigurationError` when no marker found up to filesystem root
  - Include descriptive error message about test root requirement
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] Implement `find_testmodule_fullname` function
  - Accept module and optional testroot parameter
  - Call `find_testmodule_root` when testroot not provided
  - Compute relative path from test root parent to module file
  - Convert path separators to dots for dotted module name
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

#### Module Registration (`entrypoints.py`)
- [x] Implement module registration in sys.modules
  - Import parent modules before registration using `import_by_name`
  - Register test module under full module name in `sys.modules`
  - Update test module's `__name__` attribute to full module name
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] Implement class module attribute remapping
  - Iterate over classes using `inspect.getmembers` with `inspect.isclass`
  - Update `__module__` attribute for classes with `__module__ == "__main__"`
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] Implement function module attribute remapping
  - Iterate over functions using `inspect.getmembers` with `inspect.isfunction`
  - Update `__module__` attribute for functions with `__module__ == "__main__"`
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] Implement injection registry origin renaming
  - Call `InjectionRegistry.rename_resource_origins_from_main()` with full module name
  - Update resource origins referencing `__main__` to use full module name
  - _Requirements: 10.1, 10.2, 10.3_

#### Runtime Initialization (`initialize.py`)
- [x] Implement `initialize_testbase_runtime` function
  - Establish application persona with name "automojo"
  - Set home directory to `~/automojo`
  - Set logger name prefix to "TB"
  - Set log basename to "testrun"
  - Resolve runtime variables from environment and configuration
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] Implement `initialize_testbase_results` function
  - Configure static resource source directory
  - Configure static resource destination directory
  - Configure summary template path
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

#### Unit Tests (`test_utilities_module.py`)
- [x] Test `find_testmodule_root` with valid test hierarchy
  - Create temporary directory structure with `__testroot__.py` marker
  - Verify correct root directory is returned
  - _Requirements: 5.1, 5.2, 5.3_

- [x] Test `find_testmodule_root` with missing marker
  - Create temporary directory structure without marker
  - Verify `ConfigurationError` is raised
  - _Requirements: 5.4, 5.5_

- [x] Test `find_testmodule_fullname` path to module name conversion
  - Verify correct dotted module name is computed
  - _Requirements: 6.4, 6.5_

---

### In Progress

_No tasks currently in progress._

---

### Planned Tasks

#### Test Coverage Enhancements
- [x] Add unit tests for `generic_test_entrypoint` function
  - Test runtime initialization is called
  - Test profile activation is called
  - Test results initialization is called
  - Test argument parsing with various options
  - _Requirements: 1.3, 1.4, 1.5, 4.1-4.6_

- [x] Add unit tests for module registration
  - Test parent module import
  - Test sys.modules registration
  - Test `__name__` attribute update
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] Add unit tests for class/function remapping
  - Test class `__module__` attribute update
  - Test function `__module__` attribute update
  - Test only `__main__` modules are remapped
  - _Requirements: 8.1-8.4, 9.1-9.4_

- [x] Add unit tests for injection registry renaming
  - Test resource origins are renamed from `__main__`
  - _Requirements: 10.1, 10.2, 10.3_

- [x] Add unit tests for environment configuration
  - Test jobtype is set correctly
  - Test output_directory is set correctly
  - _Requirements: 17.1-17.4_

- [x] Add unit tests for exit code handling
  - Test exit code 0 for passing tests
  - Test non-zero exit code for failing tests
  - _Requirements: 16.1, 16.2, 16.3, 16.4_

#### Integration Testing
- [x] Add integration tests for end-to-end entry point execution
  - Test complete flow from entry point to result recording
  - Test with sample test module
  - Verify result code reflects test outcomes
  - _Requirements: 1.1-1.6, 11.1-11.5_

- [x] Add integration tests for CLI integration
  - Verify shared initialization behavior with CLI
  - Compare entry point vs CLI execution results
  - _Requirements: 1.3, 1.4, 1.5_

- [x] Add integration tests for custom job types
  - Test with custom TestJob subclass
  - Verify custom job is used for execution
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

#### Documentation Enhancements
- [x] Add comprehensive docstrings to entry point functions
  - Document all parameters and return values
  - Include usage examples
  - Document exception conditions

- [x] Add inline code comments for complex logic
  - Document module resolution algorithm
  - Document class/function remapping logic
  - Document injection registry renaming

#### Error Handling Improvements
- [ ] Improve error messages for module resolution failures
  - Include module file path in error message
  - Include search path information
  - _Requirements: 5.4, 5.5_

- [x] Add validation for command-line arguments
  - Validate log level values
  - Provide helpful error messages for invalid options
  - _Requirements: 4.5_

#### Feature Enhancements
- [ ] Support for additional command-line options
  - Add `--debug` option for debug mode
  - Add `--timeout` option for test timeout
  - Add `--parallel` option for parallel execution

- [x] Support for configuration file loading
  - Load default options from configuration file
  - Support project-level configuration
  - Support user-level configuration

- [x] Support for test filtering by markers
  - Add `--include-marker` option
  - Add `--exclude-marker` option
  - Support marker expression parsing

- [ ] Support for result output format options
  - Add `--output-format` option (json, xml, html)
  - Support custom result formatters

---

## Enhancement Opportunities

### Short-term Improvements

1. **Argument Validation**
   - Add validation for include/exclude expressions
   - Validate log level values before use
   - Provide helpful error messages for invalid arguments

2. **Error Message Enhancement**
   - Include more context in ConfigurationError messages
   - Add suggestions for common configuration issues
   - Include file paths in error messages

3. **Logging Improvements**
   - Add debug logging for module resolution steps
   - Log entry point initialization progress
   - Add timing information for initialization phases

### Medium-term Improvements

1. **Configuration File Support**
   - Load default options from `.testbase.yaml` or similar
   - Support project and user-level configuration
   - Reduce command-line verbosity for common scenarios

2. **Marker-based Filtering**
   - Support filtering tests by markers
   - Add marker expression parsing
   - Support complex marker expressions

3. **Progress Reporting**
   - Add progress output during initialization
   - Report module resolution progress
   - Show test discovery progress

### Long-term Improvements

1. **Parallel Execution Support**
   - Add parallel test execution options
   - Support worker pool configuration
   - Add timeout and retry options

2. **Remote Execution**
   - Support remote test execution
   - Add distributed test coordination
   - Support cloud-based test runners

3. **Plugin System**
   - Support custom entry point plugins
   - Allow third-party initialization extensions
   - Provide plugin discovery mechanism

---

## Requirements Traceability

| Requirement | Status | Implementation Location |
|-------------|--------|------------------------|
| 1.1-1.2 | ✅ Complete | `entrypoints.py::generic_test_entrypoint` |
| 1.3-1.6 | ✅ Complete | `entrypoints.py::generic_test_entrypoint` (initialization) |
| 2.1-2.6 | ✅ Complete | `initialize.py::initialize_testbase_runtime` |
| 3.1-3.5 | ✅ Complete | `initialize.py::initialize_testbase_results` |
| 4.1-4.6 | ✅ Complete | `entrypoints.py::generic_test_entrypoint` (argument parsing) |
| 5.1-5.5 | ✅ Complete | `utilities.py::find_testmodule_root` |
| 6.1-6.5 | ✅ Complete | `utilities.py::find_testmodule_fullname` |
| 7.1-7.4 | ✅ Complete | `entrypoints.py::generic_test_entrypoint` (module registration) |
| 8.1-8.4 | ✅ Complete | `entrypoints.py::generic_test_entrypoint` (class remapping) |
| 9.1-9.4 | ✅ Complete | `entrypoints.py::generic_test_entrypoint` (function remapping) |
| 10.1-10.3 | ✅ Complete | `entrypoints.py::generic_test_entrypoint` (injection renaming) |
| 11.1-11.5 | ✅ Complete | `entrypoints.py::generic_test_entrypoint` (job execution) |
| 12.1-12.4 | ✅ Complete | `entrypoints.py::generic_test_entrypoint` (output directory) |
| 13.1-13.2 | ✅ Complete | `entrypoints.py::generic_test_entrypoint` (logger config) |
| 14.1-14.4 | ✅ Complete | `entrypoints.py::generic_test_entrypoint` (custom job type) |
| 15.1-15.3 | ✅ Complete | Test root marker file convention |
| 16.1-16.4 | ✅ Complete | `entrypoints.py::generic_test_entrypoint` (exit codes) |
| 17.1-17.4 | ✅ Complete | `entrypoints.py::generic_test_entrypoint` (environment context) |

---

## Test Coverage Summary

| Component | Unit Tests | Integration Tests |
|-----------|------------|-------------------|
| `generic_test_entrypoint` | ✅ | ✅ |
| `find_testmodule_root` | ✅ | ⬜ |
| `find_testmodule_fullname` | ✅ | ⬜ |
| Module Registration | ✅ | ⬜ |
| Class/Function Remapping | ✅ | ⬜ |
| Injection Registry Renaming | ✅ | ⬜ |
| Argument Parsing | ✅ | ✅ |
| Environment Configuration | ✅ | ⬜ |
| Exit Code Handling | ✅ | ✅ |
| Runtime Initialization | ✅ | ✅ |
| Results Initialization | ✅ | ✅ |
| Custom Job Types | ✅ | ✅ |
| CLI Integration | ⬜ | ✅ |

**Legend:** ✅ = Complete, ⚠️ = Partial, ⬜ = Not Started

---

## Known Limitations

1. **No Configuration File Support**: Users must specify all options via command line
2. **No Marker-based Filtering**: Entry point does not support marker expressions (CLI does)
3. **No Parallel Execution**: Tests execute sequentially through the entry point
4. **No Progress Reporting**: No visual feedback during initialization
5. **Limited Error Context**: Some error messages could provide more debugging context
6. **No Remote Execution**: Entry point only supports local test execution
7. **No Plugin System**: No mechanism for extending entry point behavior

---

## File Structure

```
source/packages/automojo/testbase/
├── entrypoints.py          # Generic test entry point function
├── initialize.py           # Runtime and results initialization
├── utilities.py            # Module resolution utilities (find_testmodule_root, find_testmodule_fullname)
├── testjob.py              # TestJob base class and DefaultTestJob
└── injection/
    └── injectionregistry.py  # Resource origin management
```
