# Configuration File Loading - Requirements Document

## Introduction

The Configuration File Loading system provides a hierarchical configuration mechanism for test entry point options. It supports loading default values from YAML configuration files at both user-level and project-level locations, with a defined precedence order. This system reduces command-line verbosity for common test execution scenarios by allowing developers to set default includes, excludes, and logging levels in configuration files.

## Glossary

- **EntryPointConfiguration**: A container class holding configuration values (includes, excludes, console_level, logfile_level)
- **User_Config**: Configuration file located at `~/.automojo/testbase.yaml` or `~/.automojo/testbase.yml`
- **Project_Config**: Configuration file located at `.testbase.yaml` or `.testbase.yml` in the current directory or any parent directory
- **Configuration_Precedence**: The order in which configuration sources override each other: CLI > Project > User > Defaults

## Requirements

### Requirement 1: EntryPointConfiguration Container

**User Story:** As a framework developer, I want a typed container for configuration values, so that configuration data is structured and accessible.

#### Acceptance Criteria

1. THE EntryPointConfiguration class SHALL store `includes` as a `list[string]` (default: empty list).
2. THE EntryPointConfiguration class SHALL store `excludes` as a `list[string]` (default: empty list).
3. THE EntryPointConfiguration class SHALL store `console_level` as an `Option[string]` (default: none).
4. THE EntryPointConfiguration class SHALL store `logfile_level` as an `Option[string]` (default: none).
5. THE EntryPointConfiguration class SHALL provide a `merge(other)` method that overrides values from another configuration only when the other's values are set (non-empty lists, non-none scalars).

### Requirement 2: User-Level Configuration Discovery

**User Story:** As a test developer, I want user-level configuration loaded from my home directory, so that I can set personal defaults across all projects.

#### Acceptance Criteria

1. THE system SHALL search for configuration files at `~/.automojo/testbase.yaml` and `~/.automojo/testbase.yml`.
2. THE system SHALL use the first file found (`.yaml` before `.yml`).
3. IF no user configuration file exists, THE system SHALL return an empty configuration.
4. IF the `.automojo` directory does not exist, THE system SHALL return an empty configuration without error.

### Requirement 3: Project-Level Configuration Discovery

**User Story:** As a test developer, I want project-level configuration loaded from my project directory, so that I can set project-specific defaults.

#### Acceptance Criteria

1. THE system SHALL search for `.testbase.yaml` and `.testbase.yml` starting from the current working directory.
2. THE system SHALL walk up the directory tree toward the filesystem root until a configuration file is found.
3. THE system SHALL use the first file found (closest to the current directory).
4. IF no project configuration file is found, THE system SHALL return an empty configuration.

### Requirement 4: Configuration File Parsing

**User Story:** As a test developer, I want YAML configuration files parsed into structured configuration objects, so that I can use standard YAML syntax for configuration.

#### Acceptance Criteria

1. THE system SHALL parse YAML files using `yaml.safe_load`.
2. THE system SHALL support `includes` as either a list of strings or a single string.
3. THE system SHALL support `excludes` as either a list of strings or a single string.
4. THE system SHALL normalize `console_level` and `logfile_level` to uppercase.
5. IF YAML parsing fails, THE system SHALL silently return an empty configuration (no crash).
6. IF the `yaml` module is not available, THE system SHALL return empty configurations for all file-based loading.

### Requirement 5: Configuration Merging and Precedence

**User Story:** As a test developer, I want configuration sources merged with defined precedence, so that project settings override user settings and CLI arguments override everything.

#### Acceptance Criteria

1. THE `load_entrypoint_configuration` function SHALL load user configuration first, then merge project configuration on top.
2. Project-level values SHALL override user-level values when set.
3. THE merged configuration SHALL be returned for use by the entry point.
4. Command-line arguments (handled by the entry point, not this module) take final precedence over file-based configuration.

### Requirement 6: Configuration File Format

**User Story:** As a test developer, I want a documented configuration file format, so that I can create configuration files correctly.

#### Acceptance Criteria

1. THE configuration file SHALL support the following keys: `includes`, `excludes`, `console_level`, `logfile_level`.
2. THE `includes` key SHALL accept a list of test include expression strings.
3. THE `excludes` key SHALL accept a list of test exclude expression strings.
4. THE `console_level` key SHALL accept a log level string (DEBUG, INFO, WARN, ERROR).
5. THE `logfile_level` key SHALL accept a log level string.
6. Unknown keys in the configuration file SHALL be silently ignored.
