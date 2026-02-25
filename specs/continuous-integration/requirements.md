# Build and Pipeline Integration - Requirements Document

## Introduction

The Build and Pipeline Integration system provides a standardized mechanism for capturing and associating CI/CD metadata with test execution results in the TestBase framework. It enables extraction of build information from environment variables, association of pipeline and job metadata with test runs, traceability between test results and source code builds, and integration with various CI/CD platforms (Jenkins, GitHub Actions, GitLab CI, Azure DevOps, etc.). The system operates through three primary data models: BuildInfo (build metadata), PipelineInfo (pipeline context), and JobInfo (job execution details). These models are populated from runtime variables and attached to result recorders for inclusion in test reports.

## Glossary

- **BuildInfo**: A dataclass containing build metadata including branch, build identifier, flavor, release version, and build URL
- **PipelineInfo**: A dataclass containing pipeline metadata including pipeline identifier, name, and instance identifier
- **JobInfo**: A dataclass containing job execution metadata including job identifier, name, type, owner, label, initiator, venue, seed, and correlation tag
- **RuntimeVariables**: A class that provides access to environment variables through a standardized interface with default value handling
- **DefaultValue.NotSet**: A sentinel value indicating that an environment variable has not been set
- **TestJob**: The orchestration class that spans test execution and manages the flow of test packs, including CI/CD metadata collection
- **ResultRecorder**: The base class for recording test results that accepts CI/CD metadata for inclusion in reports
- **JsonResultRecorder**: A concrete implementation of ResultRecorder that persists results and metadata in JSON format
- **AM_BUILD_***: Environment variable prefix for build-related metadata
- **AM_PIPELINE_***: Environment variable prefix for pipeline-related metadata
- **AM_JOB_***: Environment variable prefix for job-related metadata

## Requirements

### Requirement 1: BuildInfo Data Model

**User Story:** As a test developer, I want to associate build information with test results, so that results can be correlated with specific software builds.

#### Acceptance Criteria

1. THE BuildInfo dataclass SHALL define a branch field of type str for the source code branch name
2. THE BuildInfo dataclass SHALL define a build field of type str for the product build identifier
3. THE BuildInfo dataclass SHALL define a flavor field of type str for the build flavor label (e.g., debug, release)
4. THE BuildInfo dataclass SHALL define a release field of type str for the release version name
5. THE BuildInfo dataclass SHALL define a url field of type str for the build artifacts URL
6. THE BuildInfo dataclass SHALL use the @dataclass decorator for automatic initialization

### Requirement 2: PipelineInfo Data Model

**User Story:** As a test developer, I want to associate pipeline information with test results, so that results can be correlated with CI/CD pipeline executions.

#### Acceptance Criteria

1. THE PipelineInfo dataclass SHALL define an id field of type str for the pipeline definition identifier
2. THE PipelineInfo dataclass SHALL define a name field of type str for the pipeline display name
3. THE PipelineInfo dataclass SHALL define an instance field of type str for the pipeline execution instance identifier
4. THE PipelineInfo dataclass SHALL use the @dataclass decorator for automatic initialization

### Requirement 3: JobInfo Data Model

**User Story:** As a test developer, I want to associate job execution information with test results, so that results can be correlated with specific job runs.

#### Acceptance Criteria

1. THE JobInfo dataclass SHALL define an id field of type str for the job execution identifier
2. THE JobInfo dataclass SHALL define a name field of type str for the job display name
3. THE JobInfo dataclass SHALL define a type field of type str for the job type classification
4. THE JobInfo dataclass SHALL define an optional owner field of type Optional[str] for the job owner or team
5. THE JobInfo dataclass SHALL define an optional label field of type Optional[str] for job categorization
6. THE JobInfo dataclass SHALL define an optional initiator field of type Optional[str] for the trigger source
7. THE JobInfo dataclass SHALL define an optional venue field of type Optional[str] for the execution environment
8. THE JobInfo dataclass SHALL define an optional seed field of type Optional[str] for randomization reproducibility
9. THE JobInfo dataclass SHALL define an optional tag field of type Optional[str] for correlation tracking
10. THE JobInfo dataclass SHALL use the @dataclass decorator with default values for optional fields

### Requirement 4: Build Environment Variable Resolution

**User Story:** As a CI/CD engineer, I want build metadata to be extracted from environment variables, so that CI/CD platforms can provide build context to test runs.

#### Acceptance Criteria

1. THE System SHALL read the AM_BUILD_BRANCH environment variable for the branch field
2. THE System SHALL read the AM_BUILD_NAME environment variable for the build field
3. THE System SHALL read the AM_BUILD_FLAVOR environment variable for the flavor field
4. THE System SHALL read the AM_BUILD_RELEASE environment variable for the release field
5. THE System SHALL read the AM_BUILD_URL environment variable for the url field
6. WHEN an environment variable is not set, THE System SHALL use DefaultValue.NotSet or None as the field value

### Requirement 5: Pipeline Environment Variable Resolution

**User Story:** As a CI/CD engineer, I want pipeline metadata to be extracted from environment variables, so that CI/CD platforms can provide pipeline context to test runs.

#### Acceptance Criteria

1. THE System SHALL read the AM_PIPELINE_ID environment variable for the pipeline id field
2. THE System SHALL read the AM_PIPELINE_NAME environment variable for the pipeline name field
3. THE System SHALL read the AM_PIPELINE_INSTANCE environment variable for the pipeline instance field
4. WHEN the AM_PIPELINE_ID environment variable is not set, THE System SHALL not create a PipelineInfo object

### Requirement 6: Job Environment Variable Resolution

**User Story:** As a CI/CD engineer, I want job metadata to be extracted from environment variables, so that CI/CD platforms can provide job context to test runs.

#### Acceptance Criteria

1. THE System SHALL read the AM_JOB_ID environment variable for the job id field
2. THE System SHALL read the AM_JOB_NAME environment variable for the job name field
3. THE System SHALL read the AM_JOB_TYPE environment variable for the job type field
4. THE System SHALL read the AM_JOB_OWNER environment variable for the optional owner field
5. THE System SHALL read the AM_JOB_LABEL environment variable for the optional label field
6. THE System SHALL read the AM_JOB_INITIATOR environment variable for the optional initiator field
7. THE System SHALL read the AM_JOB_VENUE environment variable for the optional venue field
8. THE System SHALL read the AM_JOB_SEED environment variable for the optional seed field
9. THE System SHALL read the AM_JOB_TAG environment variable for the optional tag field

### Requirement 7: TestJob Metadata Collection

**User Story:** As a framework developer, I want the TestJob class to collect CI/CD metadata during initialization, so that metadata is available throughout test execution.

#### Acceptance Criteria

1. THE TestJob class SHALL read build-related RuntimeVariables during __init__
2. THE TestJob class SHALL read pipeline-related RuntimeVariables during __init__
3. THE TestJob class SHALL read job-related RuntimeVariables during __init__
4. THE TestJob class SHALL store metadata values as instance attributes for later use
5. THE TestJob class SHALL use the job name as the test run title when AM_JOB_NAME is set

### Requirement 8: Metadata Object Creation

**User Story:** As a framework developer, I want CI/CD metadata objects to be created before test execution, so that they can be passed to the result recorder.

#### Acceptance Criteria

1. THE TestJob.execute method SHALL create a BuildInfo object with collected build metadata
2. THE TestJob.execute method SHALL create a PipelineInfo object only when pipeline_id is not None
3. THE TestJob.execute method SHALL create a JobInfo object with collected job metadata
4. THE TestJob.execute method SHALL pass metadata objects to the _create_recorder method

### Requirement 9: ResultRecorder Metadata Integration

**User Story:** As a framework developer, I want the ResultRecorder to accept CI/CD metadata, so that metadata is included in test result output.

#### Acceptance Criteria

1. THE ResultRecorder constructor SHALL accept an optional build_info parameter of type BuildInfo
2. THE ResultRecorder constructor SHALL accept an optional pipeline_info parameter of type PipelineInfo
3. THE ResultRecorder constructor SHALL accept an optional job_info parameter of type JobInfo
4. THE ResultRecorder SHALL store metadata references for use during result recording

### Requirement 10: Summary JSON Metadata Inclusion

**User Story:** As a test developer, I want CI/CD metadata to be included in the test summary JSON, so that results can be traced back to their source.

#### Acceptance Criteria

1. THE summary JSON SHALL include a "build" section with BuildInfo fields when build_info is provided
2. THE summary JSON SHALL include a "pipeline" section with PipelineInfo fields when pipeline_info is provided
3. THE summary JSON SHALL include a "job" section with JobInfo fields when job_info is provided
4. WHEN metadata is not provided, THE corresponding section SHALL be null or omitted

### Requirement 11: Graceful Degradation

**User Story:** As a test developer, I want test execution to proceed normally without CI/CD metadata, so that tests can run in any environment.

#### Acceptance Criteria

1. WHEN build environment variables are not set, THE System SHALL proceed with empty or default build metadata
2. WHEN pipeline environment variables are not set, THE System SHALL proceed without pipeline metadata
3. WHEN job environment variables are not set, THE System SHALL proceed with default job metadata
4. THE System SHALL not raise exceptions due to missing CI/CD environment variables

### Requirement 12: Additional Runtime Variables

**User Story:** As a framework developer, I want additional runtime variables for test run identification, so that test runs can be uniquely identified and tracked.

#### Acceptance Criteria

1. THE System SHALL read the AM_RUN_ID environment variable for unique test run identification
2. THE System SHALL read the AM_AUTOMATION_POD environment variable for automation pod identification
3. THE System SHALL read the AM_STARTTIME environment variable for test run start time
4. WHEN AM_RUN_ID is not set, THE System SHALL generate or use a default run identifier

### Requirement 13: CI/CD Platform Compatibility

**User Story:** As a CI/CD engineer, I want to map platform-specific variables to TestBase variables, so that any CI/CD platform can integrate with TestBase.

#### Acceptance Criteria

1. THE System SHALL document the mapping from Jenkins environment variables to AM_* variables
2. THE System SHALL document the mapping from GitHub Actions environment variables to AM_* variables
3. THE System SHALL document the mapping from GitLab CI environment variables to AM_* variables
4. THE System SHALL document the mapping from Azure DevOps environment variables to AM_* variables
5. THE documentation SHALL provide example CI configuration snippets for each platform

### Requirement 14: Summary Output Formatting

**User Story:** As a test developer, I want CI/CD metadata to be displayed in formatted summary output, so that build context is visible in test reports.

#### Acceptance Criteria

1. THE format_lines method SHALL include the release version in the formatted output
2. THE format_lines method SHALL include the branch name in the formatted output
3. THE format_lines method SHALL include the build identifier in the formatted output
4. THE format_lines method SHALL include the build flavor in the formatted output
5. THE format_lines method SHALL include the job owner in the formatted output
6. THE format_lines method SHALL include the run identifier in the formatted output

### Requirement 15: HTML Report Metadata Display

**User Story:** As a test developer, I want CI/CD metadata to be displayed in HTML test reports, so that build context is visible in the web interface.

#### Acceptance Criteria

1. THE HTML report template SHALL display build information when available
2. THE HTML report template SHALL display pipeline information when available
3. THE HTML report template SHALL display job information when available
4. THE HTML report template SHALL gracefully handle missing metadata sections

