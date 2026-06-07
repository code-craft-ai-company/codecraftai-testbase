# Command Line Interface - Requirements Document

## Introduction

The Command Line Interface (CLI) is the primary user-facing entry point for the TestBase framework. It provides a hierarchical command structure for running test collections, querying test information, managing test jobs, launching testing services, and providing utility commands for automation pipelines. The CLI is built on the `ccai.arcli` framework, which provides decorator-based command definition, reusable option groups, and automatic help generation. The CLI integrates with the TestBase runtime system, result recording, and dependency injection to provide a complete test execution experience from the command line.

## Glossary

- **Root_Command**: The top-level `testbase` command that initializes the runtime and provides global options
- **Command_Group**: A container for related commands organized hierarchically (e.g., `testing`, `services`, `utilities`)
- **Option_Group**: A reusable collection of CLI options that can be attached to multiple commands
- **Include_Expression**: A string expression in the format `(scope):(package).(package)@(module)#(testname)` used to specify which tests to include
- **Exclude_Expression**: A string expression used to specify which tests to exclude from the included tests
- **Marker_Expression**: An expression used to filter tests by marker metadata attributes
- **Test_Root**: The root directory containing test files for discovery and execution
- **Test_Job**: A class that orchestrates test execution with specific configuration
- **Job_Specification**: A string in the format `package.module@JobClass` identifying a test job type
- **Verbosity_Level**: An integer counter controlling the amount of output detail (0=WARNING, 1=INFO, 2=DEBUG, 3+=NOTSET)
- **Runtime_Option_Override**: A mechanism for CLI arguments to override runtime configuration values
- **Results_Server**: An HTTP server that serves test result files for viewing

## Requirements

### Requirement 1: Root Command Entry Point

**User Story:** As a test developer, I want a `testbase` command as the entry point, so that I can access all TestBase functionality from the command line.

#### Acceptance Criteria

1. THE Root_Command SHALL be named `testbase` and serve as the entry point for all CLI operations
2. WHEN the Root_Command is invoked, THE System SHALL call `initialize_testbase_runtime()` to set up the framework
3. THE Root_Command SHALL accept a `-v` or `--verbose` option that can be specified multiple times
4. WHEN verbose is 0 (default), THE System SHALL set console log level to WARNING and enable interactive console mode
5. WHEN verbose is 1, THE System SHALL set console log level to INFO and disable interactive console mode
6. WHEN verbose is 2, THE System SHALL set console log level to DEBUG and disable interactive console mode
7. WHEN verbose is 3 or greater, THE System SHALL set console log level to NOTSET and disable interactive console mode

### Requirement 2: Command Group Organization

**User Story:** As a test developer, I want commands organized into logical groups, so that I can easily find and use related functionality.

#### Acceptance Criteria

1. THE CLI SHALL provide a `testing` command group for test execution and query commands
2. THE CLI SHALL provide a `services` command group for launching testing services
3. THE CLI SHALL provide a `utilities` command group for automation pipeline utilities
4. WHEN a command group is invoked without a subcommand, THE System SHALL display help for that group

### Requirement 3: Testing Run Command

**User Story:** As a test developer, I want a `run` command to execute test collections, so that I can run tests with configurable options.

#### Acceptance Criteria

1. THE `testing run` command SHALL execute test collections based on include and exclude expressions
2. THE command SHALL accept a `--root` option specifying the test root directory
3. THE command SHALL accept `-i` or `--includes` options that can be specified multiple times for include expressions
4. THE command SHALL accept `-x` or `--excludes` options that can be specified multiple times for exclude expressions
5. THE command SHALL accept `--include-marker-exp` options for marker-based inclusion filtering
6. THE command SHALL accept `--exclude-marker-exp` options for marker-based exclusion filtering
7. WHEN the root directory does not exist, THE System SHALL raise a ValueError with a descriptive message
8. WHEN the root is not specified, THE System SHALL use the AM_TESTROOT environment variable or default to current directory
9. THE command SHALL extend the Python path to include the test root's parent directory

### Requirement 4: Testing Run Output Options

**User Story:** As a test developer, I want to configure output settings for test runs, so that results are stored in the desired location.

#### Acceptance Criteria

1. THE `testing run` command SHALL accept `-o` or `--output` option for the output directory
2. THE command SHALL accept `--start` option for specifying a start timestamp
3. THE command SHALL accept `--runid` option for specifying a unique run identifier
4. WHEN output options are provided, THE System SHALL apply them as runtime option overrides

### Requirement 5: Testing Run Build Metadata Options

**User Story:** As a CI/CD engineer, I want to associate build metadata with test runs, so that results can be correlated with specific builds.

#### Acceptance Criteria

1. THE `testing run` command SHALL accept `--branch` option for the build branch name
2. THE command SHALL accept `--build` option for the build name
3. THE command SHALL accept `--flavor` option for the build flavor
4. WHEN build options are provided, THE System SHALL apply them as runtime option overrides

### Requirement 6: Testing Run Job Identification Options

**User Story:** As a CI/CD engineer, I want to identify test jobs with metadata, so that results can be tracked and attributed.

#### Acceptance Criteria

1. THE `testing run` command SHALL accept `--job-id` option for a unique job identifier
2. THE command SHALL accept `--job-initiator` option for the job initiator name
3. THE command SHALL accept `--job-label` option for the job label
4. THE command SHALL accept `--job-name` option for the job name
5. THE command SHALL accept `--job-owner` option for the job owner identifier
6. WHEN job options are provided, THE System SHALL apply them as runtime option overrides

### Requirement 7: Testing Run Logging Options

**User Story:** As a test developer, I want to configure logging levels, so that I can control the verbosity of console and file output.

#### Acceptance Criteria

1. THE `testing run` command SHALL accept `--console-level` option for console log level
2. THE command SHALL accept `--logfile-level` option for file log level
3. THE log level options SHALL validate against allowed log level names
4. WHEN logging options are provided, THE System SHALL apply them as runtime option overrides

### Requirement 8: Testing Run Diagnostic Options

**User Story:** As a test developer, I want diagnostic and debugging options, so that I can troubleshoot test execution issues.

#### Acceptance Criteria

1. THE `testing run` command SHALL accept `--debugger` option with choices `pdb` or `debugpy`
2. THE command SHALL accept `--breakpoint` options with choices `test-discovery` or `testrun-start`
3. THE command SHALL accept `--prerun-diagnostic` boolean option for pre-run diagnostics
4. THE command SHALL accept `--postrun-diagnostic` boolean option for post-run diagnostics
5. WHEN breakpoints are specified without a debugger, THE System SHALL default to `debugpy`
6. WHEN diagnostic options are provided, THE System SHALL apply them as runtime option overrides

### Requirement 9: Testing Run Execution Flow

**User Story:** As a test developer, I want the run command to execute tests and return appropriate exit codes, so that CI/CD pipelines can detect failures.

#### Acceptance Criteria

1. WHEN the run command executes, THE System SHALL initialize test results recording
2. THE System SHALL obtain the TestJob type from the configured factory
3. THE System SHALL create a TestJob context manager with the configured options
4. THE System SHALL execute the TestJob and capture the result code
5. WHEN execution completes, THE System SHALL exit with the result code from the TestJob

### Requirement 10: Testing Query Command

**User Story:** As a test developer, I want a `query` command to inspect tests without executing them, so that I can verify test discovery.

#### Acceptance Criteria

1. THE `testing query` command SHALL discover and list tests without executing them
2. THE command SHALL accept `--root` option specifying the test root directory
3. THE command SHALL accept `-i` or `--includes` options for include expressions
4. THE command SHALL accept `-x` or `--excludes` options for exclude expressions
5. THE command SHALL accept `--include-marker-exp` options for marker-based inclusion filtering
6. THE command SHALL accept `--exclude-marker-exp` options for marker-based exclusion filtering
7. WHEN the root directory does not exist, THE System SHALL raise a ValueError with a descriptive message

### Requirement 11: Testing Query Output Format

**User Story:** As a test developer, I want query output to show test names and their parameter subscriptions, so that I can understand test dependencies.

#### Acceptance Criteria

1. WHEN query executes, THE System SHALL print a "Tests:" header followed by test names
2. FOR EACH test, THE System SHALL print the test name indented with 4 spaces
3. FOR EACH parameter subscription, THE System SHALL print the parameter name and source description indented with 8 spaces
4. WHEN import errors occur, THE System SHALL print an "IMPORT ERRORS:" header to stderr
5. FOR EACH import error, THE System SHALL print the filename indented with 4 spaces to stderr

### Requirement 12: Testing Jobs Group

**User Story:** As a test developer, I want a `jobs` subgroup for managing test jobs, so that I can work with predefined job configurations.

#### Acceptance Criteria

1. THE `testing jobs` group SHALL contain commands for listing, showing, and running test jobs
2. THE group SHALL provide a `list` command for listing available jobs
3. THE group SHALL provide a `show` command for displaying job details
4. THE group SHALL provide a `run` command for executing a specific job

### Requirement 13: Testing Jobs List Command

**User Story:** As a test developer, I want to list available test jobs, so that I can see what predefined jobs exist.

#### Acceptance Criteria

1. THE `testing jobs list` command SHALL accept `--root` option for the test root directory
2. THE command SHALL accept `-f` or `--filter` option for filtering jobs
3. THE command SHALL accept `--debug` boolean option for debug output

### Requirement 14: Testing Jobs Show Command

**User Story:** As a test developer, I want to view details of a specific test job, so that I can understand its configuration.

#### Acceptance Criteria

1. THE `testing jobs show` command SHALL accept `--root` option for the test root directory
2. THE command SHALL require `-j` or `--job` option specifying the job identifier
3. THE command SHALL accept `--debug` boolean option for debug output

### Requirement 15: Testing Jobs Run Command

**User Story:** As a test developer, I want to run a specific test job, so that I can execute predefined test configurations.

#### Acceptance Criteria

1. THE `testing jobs run` command SHALL require `-j` or `--job` option specifying the job identifier
2. THE job identifier SHALL be in the format `package.module@JobClass`
3. WHEN the job format is invalid, THE System SHALL raise a ValueError with format hint
4. WHEN the job module cannot be imported, THE System SHALL raise an ArgumentError with the import error
5. WHEN the job class does not exist in the module, THE System SHALL raise an ArgumentError
6. THE command SHALL accept `--root`, output, build, and logging options
7. WHEN execution completes, THE System SHALL exit with the result code from the TestJob

### Requirement 16: Services Results Command

**User Story:** As a test developer, I want to launch a results server, so that I can view test results in a web browser.

#### Acceptance Criteria

1. THE `services results` command SHALL launch an HTTP server for viewing test results
2. THE command SHALL accept `--directory` option for the results directory
3. THE command SHALL accept `--bind` option for the IP address to bind to (default: all interfaces)
4. THE command SHALL accept `--port` option for the port number (default: 8880)
5. WHEN directory is not specified, THE System SHALL use `<presence_dir>/results` as the default
6. WHEN the server starts, THE System SHALL print a message indicating the port and directory
7. THE server SHALL run indefinitely until terminated

### Requirement 17: Utilities Timestamp Command

**User Story:** As a CI/CD engineer, I want a timestamp command, so that I can generate consistent timestamps for automation pipelines.

#### Acceptance Criteria

1. THE `utilities timestamp` command SHALL print the current timestamp
2. THE timestamp format SHALL be `YYYY-MM-DDTHH:MM:SS.ffffff`
3. THE command SHALL not require any options

### Requirement 18: Option Group Reusability

**User Story:** As a framework developer, I want reusable option groups, so that common options are consistent across commands.

#### Acceptance Criteria

1. THE CLI SHALL define a RootOptionGroup containing the `--root` option
2. THE CLI SHALL define an OutputOptionGroup containing `--output`, `--start`, and `--runid` options
3. THE CLI SHALL define a BuildOptionGroup containing `--branch`, `--build`, and `--flavor` options
4. THE CLI SHALL define a JobOptionGroup containing job identification options
5. THE CLI SHALL define a LoggingOptionGroup containing `--console-level` and `--logfile-level` options
6. THE CLI SHALL define a DiagnosticOptionGroup containing debugger and diagnostic options
7. THE CLI SHALL define a FilteringOptionGroup containing include and exclude options
8. THE CLI SHALL define a DebugOptionGroup containing the `--debug` option

### Requirement 19: Option Group Help Text Customization

**User Story:** As a framework developer, I want customizable help text for option groups, so that help messages are context-appropriate.

#### Acceptance Criteria

1. THE Option_Group attachment mechanism SHALL support a `help_fill` parameter
2. WHEN help_fill is provided, THE System SHALL substitute placeholders in help text
3. THE help text for `--root` SHALL include the action being performed (e.g., "run", "query")
4. THE help text for include/exclude options SHALL include the action being performed

### Requirement 20: Runtime Option Override Integration

**User Story:** As a framework developer, I want CLI options to override runtime configuration, so that command-line arguments take precedence.

#### Acceptance Criteria

1. WHEN CLI options are provided, THE System SHALL apply them through AM_RUNTIME_OPTION_OVERRIDES
2. THE override mechanism SHALL support build branch, name, and flavor
3. THE override mechanism SHALL support job identification fields
4. THE override mechanism SHALL support logging levels
5. THE override mechanism SHALL support output directory and timing
6. THE override mechanism SHALL support test root directory
7. THE override mechanism SHALL support debug breakpoints and debugger selection

### Requirement 21: Path Resolution and Validation

**User Story:** As a test developer, I want paths to be properly resolved and validated, so that errors are caught early with clear messages.

#### Acceptance Criteria

1. WHEN a root path is provided, THE System SHALL expand environment variables using `os.path.expandvars`
2. THE System SHALL expand user home directory using `os.path.expanduser`
3. THE System SHALL convert to absolute path using `os.path.abspath`
4. WHEN the resolved path does not exist, THE System SHALL raise a ValueError
5. THE error message SHALL include both the original and expanded paths if they differ

### Requirement 22: Marker Expression Parsing

**User Story:** As a test developer, I want marker expressions to be properly parsed, so that tests can be filtered by metadata.

#### Acceptance Criteria

1. WHEN include marker expressions are provided, THE System SHALL prefix them with "+" and parse them
2. WHEN exclude marker expressions are provided, THE System SHALL prefix them with "-" and parse them
3. THE System SHALL strip surrounding quotes from marker expressions
4. THE parsed expressions SHALL be passed to the TestJob as metafilters

### Requirement 23: Factory Protocol Integration

**User Story:** As a framework developer, I want the CLI to use factory protocols for TestJob creation, so that custom job types can be used.

#### Acceptance Criteria

1. THE CLI SHALL obtain TestJob types through ConfiguredSuperFactorySingleton
2. THE CLI SHALL use TestBaseFactoryProtocol.get_testbase_default_job_type for default jobs
3. THE CLI SHALL support custom job types specified via the `--job` option
4. WHEN a custom job is specified, THE System SHALL import and use that job class

### Requirement 24: Exit Code Handling

**User Story:** As a CI/CD engineer, I want appropriate exit codes, so that automation pipelines can detect test failures.

#### Acceptance Criteria

1. WHEN all tests pass, THE System SHALL exit with code 0
2. WHEN tests fail or error, THE System SHALL exit with a non-zero code
3. WHEN configuration errors occur, THE System SHALL raise appropriate exceptions
4. THE exit code from TestJob.execute() SHALL be passed to sys.exit()

### Requirement 25: Help Generation

**User Story:** As a test developer, I want automatic help generation, so that I can discover available commands and options.

#### Acceptance Criteria

1. THE CLI SHALL generate help text for all commands and groups
2. WHEN `--help` is specified, THE System SHALL display help for the current command or group
3. THE help text SHALL include descriptions for all options
4. THE help text SHALL include default values where applicable

