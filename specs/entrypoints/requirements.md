# Test Entry Points - Requirements Document

## Introduction

The Test Entry Points system provides standardized mechanisms for initiating test execution in the TestBase framework. The primary entry point, `generic_test_entrypoint`, is the DECOUPLED standalone core that lives in TestBase: it runs individual test modules directly for debugging, performs NO integration/activation initialization and NO this-app environment setup, and lets the test job it builds resolve output through injected seams (`IOutputContext` / recorder) rather than reading `env["output_directory"]` or runtime/this-app well-known paths. The standalone core handles test module name resolution and registration, Python path management for proper module imports, command-line argument parsing for test filtering, and test job creation and execution orchestration; it reads only core test-execution knobs from `os.environ` via the dependency-free `automojo.testbase.environment` module.

The integration counterpart, `integrated_test_entrypoint`, lives in `automojo-integration-runtime` (NOT in TestBase). It performs the this-app activation (persona + runtime-variable resolution + profile activation), then delegates to the same decoupled TestBase core with a `DefaultIntegratedTestJob`. Requirements that describe activation, runtime/results initialization, well-known output paths, or this-app environment context apply to the integration entry point, not the standalone core; they are retained below and explicitly scoped to `integrated_test_entrypoint`.

## Glossary

- **Generic_Test_Entry_Point**: The primary, DECOUPLED standalone entry point function (`generic_test_entrypoint`, in `automojo.testbase.entrypoints`) for running test modules as standalone scripts; performs no activation/this-app setup and resolves output through injected seams
- **Integrated_Test_Entry_Point**: The integration entry point function (`integrated_test_entrypoint`, in `automojo.integrationruntime.entrypoints`, part of `automojo-integration-runtime`) that activates the application then delegates to the standalone core with a `DefaultIntegratedTestJob`
- **Output_Context**: The injected `IOutputContext` seam (default `SimpleOutputContext`) that resolves artefact locations under a single base directory
- **Run_Metadata**: The injected `IRunMetadata` seam (default `StandaloneRunMetadata`) that supplies run identity (run id, title, timeout, start time)
- **Result_Recorder**: The injected recorder (default `StdoutResultRecorder`) that emits a stdout summary, writes JSOS/JSON when an output dir is given, and skips HTML
- **Test_Module**: A Python module containing test containers and test functions decorated with TestBase decorators
- **Test_Root**: The root directory containing test files, marked by a `__testroot__.py` marker file
- **Module_Full_Name**: The fully qualified dotted module name computed from the test root and module file path
- **Test_Job**: A class that orchestrates test execution with specific configuration (e.g., `DefaultTestJob`)
- **Include_Expression**: A string expression used to specify which tests to include in execution
- **Exclude_Expression**: A string expression used to specify which tests to exclude from execution
- **Injection_Registry**: The registry that manages dependency injection resource origins
- **Runtime_Variables**: Configuration values resolved from environment and configuration files
- **Test_Root_Marker**: The `__testroot__.py` file that marks the boundary of a test package namespace

## Requirements

### Requirement 1: Generic Test Entry Point Function

**User Story:** As a test developer, I want a generic entry point function that I can add to test modules, so that I can run individual test files directly for debugging purposes.

#### Acceptance Criteria

1. THE Generic_Test_Entry_Point SHALL be a function named `generic_test_entrypoint` that can be called from a test module's `__main__` block
2. THE Generic_Test_Entry_Point SHALL accept an optional `job_type` parameter defaulting to `DefaultTestJob`
3. THE Generic_Test_Entry_Point SHALL NOT perform any integration/activation initialization (no runtime activation, no profile activation, no result-resource initialization) and SHALL NOT import from `automojo.runtime` or `automojo.thisapp`
4. WHEN the Generic_Test_Entry_Point is invoked, THE System SHALL load default options from configuration files (user-level and project-level) before parsing command-line arguments
5. THE Generic_Test_Entry_Point SHALL rely on the test job's injected `IOutputContext` and Result_Recorder to resolve output location, rather than performing output setup itself
6. WHEN execution completes, THE System SHALL exit with the result code returned by the test job

### Requirement 2: Runtime Initialization (Integrated_Test_Entry_Point only)

**User Story:** As a framework developer, I want the integration entry point to initialize the runtime environment, so that all framework components are properly configured before test execution under the integration runtime.

> Scope: This requirement applies to `integrated_test_entrypoint` in `automojo-integration-runtime`, NOT to the standalone `generic_test_entrypoint`. The standalone core performs none of this initialization.

#### Acceptance Criteria

1. WHEN the Integrated_Test_Entry_Point initializes, THE System SHALL call `initialize_integration_runtime()` to establish the application persona
2. THE runtime initialization SHALL set the application name to "automojo"
3. THE runtime initialization SHALL set the home directory to `~/automojo`
4. THE runtime initialization SHALL set the logger name prefix to "TB"
5. THE runtime initialization SHALL set the log basename to "testrun"
6. THE runtime initialization SHALL resolve all runtime variables from environment and configuration

### Requirement 3: Results Initialization (Integrated_Test_Entry_Point only)

**User Story:** As a test developer, I want the integration entry point to initialize the results system, so that test results are properly recorded and stored under the presence folder.

> Scope: This requirement applies to `integrated_test_entrypoint` in `automojo-integration-runtime`, NOT to the standalone `generic_test_entrypoint`. The standalone core records via `StdoutResultRecorder` and resolves artefacts through its injected `IOutputContext`.

#### Acceptance Criteria

1. WHEN the Integrated_Test_Entry_Point initializes results, THE System SHALL call `initialize_integration_results()` to configure result recording
2. THE results initialization SHALL configure the static resource source directory if not already set
3. THE results initialization SHALL configure the static resource destination directory if not already set
4. THE results initialization SHALL configure the summary template path if not already set
5. THE results initialization SHALL activate the TestRun job profile

### Requirement 4: Command Line Argument Parsing

**User Story:** As a test developer, I want to pass command line arguments when running test modules directly, so that I can filter tests and configure logging.

#### Acceptance Criteria

1. THE Generic_Test_Entry_Point SHALL accept `-i` or `--include` options that can be specified multiple times for include expressions
2. THE Generic_Test_Entry_Point SHALL accept `-x` or `--exclude` options that can be specified multiple times for exclude expressions
3. THE Generic_Test_Entry_Point SHALL accept `--console-level` option for console log level with default "INFO"
4. THE Generic_Test_Entry_Point SHALL accept `--logfile-level` option for file log level with default "DEBUG"
5. THE log level options SHALL validate against allowed log level names
6. WHEN no include expressions are provided, THE System SHALL default to including all tests with "*"

### Requirement 5: Test Root Discovery

**User Story:** As a test developer, I want the entry point to automatically discover the test root directory, so that module names are correctly resolved.

#### Acceptance Criteria

1. THE System SHALL provide a `find_testmodule_root` function that locates the test root for a given module
2. WHEN finding the test root, THE System SHALL walk up the directory tree from the module's location
3. THE System SHALL identify the test root by the presence of a `__testroot__.py` marker file
4. WHEN no `__testroot__.py` marker is found up to the filesystem root, THE System SHALL raise a ConfigurationError
5. THE error message SHALL indicate that test files must exist inside a test root directory marked with `__testroot__.py`

### Requirement 6: Module Full Name Resolution

**User Story:** As a framework developer, I want the entry point to compute the full module name, so that test classes and functions are properly identified.

#### Acceptance Criteria

1. THE System SHALL provide a `find_testmodule_fullname` function that computes the dotted module name
2. THE function SHALL accept a module and an optional testroot parameter
3. WHEN testroot is not provided, THE System SHALL call `find_testmodule_root` to discover it
4. THE full module name SHALL be computed from the relative path between the test root parent and the module file
5. THE path separators SHALL be converted to dots to form the dotted module name

### Requirement 7: Module Registration in sys.modules

**User Story:** As a framework developer, I want the entry point to register the test module under its full name, so that the module loader does not reload it.

#### Acceptance Criteria

1. WHEN the test module is loaded as `__main__`, THE System SHALL register it in `sys.modules` under its full module name
2. WHEN the module has parent modules, THE System SHALL import all parent modules before registration
3. THE System SHALL update the test module's `__name__` attribute to the full module name
4. THE registration SHALL prevent duplicate loading of the test module

### Requirement 8: Class Module Attribute Remapping

**User Story:** As a framework developer, I want class `__module__` attributes to be updated, so that test classes are properly identified by their full module name.

#### Acceptance Criteria

1. WHEN the test module was loaded as `__main__`, THE System SHALL iterate over all classes in the module
2. FOR EACH class with `__module__` equal to `__main__`, THE System SHALL update it to the full module name
3. THE remapping SHALL use `inspect.getmembers` with `inspect.isclass` to find classes
4. THE remapping SHALL only affect classes originally defined in the `__main__` module

### Requirement 9: Function Module Attribute Remapping

**User Story:** As a framework developer, I want function `__module__` attributes to be updated, so that test functions are properly identified by their full module name.

#### Acceptance Criteria

1. WHEN the test module was loaded as `__main__`, THE System SHALL iterate over all functions in the module
2. FOR EACH function with `__module__` equal to `__main__`, THE System SHALL update it to the full module name
3. THE remapping SHALL use `inspect.getmembers` with `inspect.isfunction` to find functions
4. THE remapping SHALL only affect functions originally defined in the `__main__` module

### Requirement 10: Injection Registry Origin Renaming

**User Story:** As a framework developer, I want injection resource origins to be renamed from `__main__`, so that dependency injection works correctly for directly-run modules.

#### Acceptance Criteria

1. WHEN the test module was loaded as `__main__`, THE System SHALL rename resource origins in the InjectionRegistry
2. THE System SHALL call `InjectionRegistry.rename_resource_origins_from_main()` with the full module name
3. THE renaming SHALL update all resource origins that reference `__main__` to use the full module name

### Requirement 11: Test Job Execution

**User Story:** As a test developer, I want the entry point to execute tests through a TestJob, so that tests run with proper lifecycle management.

#### Acceptance Criteria

1. THE Generic_Test_Entry_Point SHALL create a TestJob instance using the specified job_type
2. THE TestJob SHALL be created with the logger, testroot, includes, excludes, and test_module parameters
3. THE TestJob SHALL be used as a context manager for proper resource management
4. THE System SHALL call the TestJob's `execute()` method to run the tests
5. THE result code from `execute()` SHALL be passed to `sys.exit()`

### Requirement 12: Output Resolution via Injected Seams

**User Story:** As a test developer, I want the standalone entry point to resolve output through injected seams, so that the core stays decoupled from runtime/this-app while still storing results in the correct location.

#### Acceptance Criteria

1. THE Generic_Test_Entry_Point SHALL NOT set a "jobtype" or "output_directory" key in any application environment and SHALL NOT call `get_path_for_testresults()` or any other this-app well-known-path helper
2. THE test job SHALL resolve the output location through its injected `IOutputContext` (default `SimpleOutputContext`), which roots artefacts under a single base directory
3. THE `SimpleOutputContext` SHALL derive its base directory from the `AM_OUTPUT_DIRECTORY` core knob read from `os.environ` via `automojo.testbase.environment`
4. WHEN an output directory is resolved, THE Result_Recorder (default `StdoutResultRecorder`) SHALL emit a stdout summary and SHALL write JSOS/JSON artefacts to that directory; the standalone core SHALL skip HTML rendering

### Requirement 13: Logger Configuration

**User Story:** As a test developer, I want the entry point to configure logging, so that test output is properly captured.

#### Acceptance Criteria

1. THE Generic_Test_Entry_Point SHALL obtain an enhanced logger using `getEnhancedLogger()`
2. THE System SHALL assign the logger to the `automojo.testbase` module's logger attribute
3. THE logger SHALL be passed to the TestJob for use during execution

### Requirement 14: Custom Job Type Support

**User Story:** As a test developer, I want to specify a custom TestJob type, so that I can use specialized test execution configurations.

#### Acceptance Criteria

1. THE Generic_Test_Entry_Point SHALL accept an optional `job_type` parameter
2. WHEN job_type is not specified, THE System SHALL use `DefaultTestJob`
3. WHEN a custom job_type is specified, THE System SHALL use that type for test execution
4. THE custom job_type SHALL be a subclass of TestJob

### Requirement 15: Test Root Marker File

**User Story:** As a test developer, I want a marker file to define test root boundaries, so that the framework can correctly identify test package namespaces.

#### Acceptance Criteria

1. THE test root marker file SHALL be named `__testroot__.py`
2. THE marker file SHALL be placed at the root of each test directory hierarchy
3. THE marker file MAY be empty or contain test root configuration
4. THE presence of the marker file SHALL define the boundary of the test package namespace

### Requirement 16: Exit Code Handling

**User Story:** As a CI/CD engineer, I want appropriate exit codes from the entry point, so that automation pipelines can detect test failures.

#### Acceptance Criteria

1. WHEN all tests pass, THE System SHALL exit with code 0
2. WHEN tests fail or error, THE System SHALL exit with a non-zero code
3. THE exit code SHALL be the result code returned by `TestJob.execute()`
4. THE System SHALL call `sys.exit()` with the result code

### Requirement 17: Core Environment Knob Access

**User Story:** As a framework developer, I want the standalone entry point to read only the core test-execution knobs, so that the core stays decoupled from `automojo.thisapp` and the application context.

#### Acceptance Criteria

1. THE Generic_Test_Entry_Point SHALL NOT obtain a `ThisApplicationSingleton()` and SHALL NOT look up an application context "/environment"
2. THE Generic_Test_Entry_Point SHALL read core test-execution knobs (`AM_TESTROOT`, `AM_OUTPUT_DIRECTORY`, `AM_RUN_ID`, `AM_TESTRUN_TIMEOUT`, `AM_DEBUG_*`, `AM_DIAGNOSTICS_PRERUN/POSTRUN`) from `os.environ` through the dependency-free `automojo.testbase.environment` module
3. THE Generic_Test_Entry_Point SHALL NOT set any "jobtype" or "output_directory" key in an application environment
4. WHEN the integration runtime needs presence-folder paths or `RuntimeVariables`-sourced metadata, THOSE SHALL be supplied by `DefaultIntegratedTestJob` in `automojo-integration-runtime`, not by the standalone core

