# Framework Initialization - Requirements Document

## Introduction

The Framework Initialization system provides the bootstrap sequence for the TestBase framework. It establishes the application persona (name, home directory, logger configuration), resolves runtime variables from environment and configuration sources, and configures the results recording system with template paths and static resource locations. Initialization must complete before any other TestBase operations.

## Glossary

- **TestBaseConstants**: Container class providing centralized access to standard directory paths for templates and static resources
- **Application_Persona**: The identity configuration for the application (name, home directory, logger name, log basename)
- **Runtime_Variables**: Environment and configuration variables resolved during initialization
- **Results_Configuration**: Paths for static resources, templates, and result output directories

## Requirements

### Requirement 1: Runtime Initialization

**User Story:** As a framework developer, I want a single initialization function that establishes the application persona and resolves runtime variables, so that the framework is properly configured before use.

#### Acceptance Criteria

1. THE `initialize_testbase_runtime()` function SHALL establish the application persona with name `"automojo"`.
2. THE function SHALL set the home directory to `~/automojo` (user's home directory).
3. THE function SHALL set the logger name prefix to `"TB"`.
4. THE function SHALL set the log basename to `"testrun"`.
5. THE function SHALL call `resolve_runtime_variables()` to resolve all runtime variables from environment and configuration.
6. THE function SHALL be idempotent — calling it multiple times SHALL not cause errors.

### Requirement 2: Results Initialization

**User Story:** As a framework developer, I want the results recording system configured with correct template and resource paths, so that test results can be generated.

#### Acceptance Criteria

1. THE `initialize_testbase_results()` function SHALL compute the static resource destination directory from the presence directory.
2. THE function SHALL set `AM_RESULTS_STATIC_RESOURCE_SRC_DIR` to the templates/v2/static directory if not already set.
3. THE function SHALL set `AM_RESULTS_STATIC_RESOURCE_DEST_DIR` to the computed destination if not already set.
4. THE function SHALL set `AM_RESULTS_STATIC_SUMMARY_TEMPLATE` to the testsummary.html template path if not already set.
5. THE function SHALL activate the TestRun job profile.
6. THE function SHALL NOT override variables that are already set (respecting external configuration).

### Requirement 3: TestBaseConstants

**User Story:** As a framework developer, I want centralized path constants, so that template and resource paths are consistent across the framework.

#### Acceptance Criteria

1. `TESTPLUS_TEMPLATES_DIR` SHALL point to the `templates` directory within the testbase package.
2. `TESTPLUS_RESOURCE_DEST_LEAF` SHALL be `"static/v2"`.
3. `TESTPLUS_RESOURCE_SRC_DIR` SHALL point to `templates/v2/static` within the testbase package.
4. `TESTPLUS_SUMMARY_TEMPLATE` SHALL point to `templates/v2/testsummary.html` within the testbase package.
5. ALL paths SHALL be computed relative to the testbase package installation directory.

### Requirement 4: Initialization Order

**User Story:** As a framework developer, I want a defined initialization order, so that dependencies between initialization steps are respected.

#### Acceptance Criteria

1. `initialize_testbase_runtime()` SHALL be called before `initialize_testbase_results()`.
2. `initialize_testbase_results()` SHALL depend on the presence directory being available (set during runtime initialization).
3. Both functions SHALL be called automatically by `generic_test_entrypoint` and CLI commands.
