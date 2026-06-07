# Command Line Interface - Design Document

## Overview

The Command Line Interface (CLI) is the primary user-facing entry point for the TestBase framework. It provides a hierarchical command structure for:

- Running test collections with configurable options
- Querying test information and metadata
- Managing test jobs and their execution
- Launching testing services (e.g., result server)
- Providing utility commands for automation pipelines

The CLI is built on the `ccai.arcli` framework, which provides decorator-based command definition, option groups for reusable parameters, and automatic help generation.

## Architecture

### High-Level Component Diagram

```mermaid
graph TB
    subgraph "Entry Layer"
        TB[testbase command]
    end
    
    subgraph "Command Groups"
        TG[testing group]
        SG[services group]
        UG[utilities group]
    end
    
    subgraph "Testing Commands"
        RUN[run command]
        QUERY[query command]
        JOBS[jobs group]
        JLIST[jobs list]
        JSHOW[jobs show]
        JRUN[jobs run]
    end
    
    subgraph "Services Commands"
        RESULTS[results command]
    end
    
    subgraph "Utilities Commands"
        TS[timestamp command]
    end
    
    subgraph "Option Groups"
        ROOT[RootOptionGroup]
        OUTPUT[OutputOptionGroup]
        BUILD[BuildOptionGroup]
        JOB[JobOptionGroup]
        LOG[LoggingOptionGroup]
        DIAG[DiagnosticOptionGroup]
        FILTER[FilteringOptionGroup]
        DEBUG[DebugOptionGroup]
    end
    
    TB --> TG
    TB --> SG
    TB --> UG
    
    TG --> RUN
    TG --> QUERY
    TG --> JOBS
    JOBS --> JLIST
    JOBS --> JSHOW
    JOBS --> JRUN
    
    SG --> RESULTS
    
    UG --> TS
    
    RUN --> ROOT
    RUN --> OUTPUT
    RUN --> BUILD
    RUN --> JOB
    RUN --> LOG
    RUN --> DIAG
    RUN --> FILTER
    
    QUERY --> ROOT
    QUERY --> FILTER
    
    JRUN --> ROOT
    JRUN --> OUTPUT
    JRUN --> BUILD
    JRUN --> LOG
```

### Command Tree Structure

```
testbase
├── testing
│   ├── run          # Execute test collections
│   ├── query        # Query test information
│   └── jobs
│       ├── list     # List available test jobs
│       ├── show     # Show job details
│       └── run      # Execute a specific job
├── services
│   └── results      # Launch test results server
└── utilities
    └── timestamp    # Print current timestamp
```

### Components

#### 1. Root Command (`testbase_command.py`)

The root command initializes the TestBase runtime and sets up global options.

```mermaid
classDiagram
    class testbase_root_command {
        <<decorator>>
        @arcli.entry("testbase")
        @arcli.option('-v', '--verbose')
        <<parameters>>
        +verbose: int
        <<behavior>>
        +initialize_testbase_runtime()
        +configure_console_logging()
        +set_runtime_variables()
    }
```

**Responsibilities:**

| Responsibility | Description |
|----------------|-------------|
| Runtime Initialization | Calls `initialize_testbase_runtime()` to set up the framework |
| Verbosity Control | Maps `-v` counter to log levels (WARNING → INFO → DEBUG → NOTSET) |
| Console Mode | Sets interactive console mode based on verbosity |
| Variable Override | Overrides runtime variables via `ThisApplicationSingleton` |

**Verbosity Mapping:**

| Flag Count | Log Level | Interactive Console |
|------------|-----------|---------------------|
| 0 (default) | WARNING | True |
| 1 (`-v`) | INFO | False |
| 2 (`-vv`) | DEBUG | False |
| 3+ (`-vvv`) | NOTSET | False |

#### 2. Option Groups (`options.py`)

Reusable option groups provide consistent parameter definitions across commands.

```mermaid
classDiagram
    class OptionGroup {
        <<abstract>>
        +name: str
    }
    
    class RootOptionGroup {
        +name = "root"
        +root: OptionField
    }
    
    class OutputOptionGroup {
        +name = "output"
        +output: OptionField
        +start: OptionField
        +runid: OptionField
    }
    
    class BuildOptionGroup {
        +name = "build"
        +branch: OptionField
        +build: OptionField
        +flavor: OptionField
    }
    
    class JobOptionGroup {
        +name = "job"
        +job_id: OptionField
        +job_initiator: OptionField
        +job_label: OptionField
        +job_name: OptionField
        +job_owner: OptionField
    }
    
    class LoggingOptionGroup {
        +name = "logging"
        +console_level: OptionField
        +logfile_level: OptionField
    }
    
    class DiagnosticOptionGroup {
        +name = "diagnostic"
        +debugger: OptionField
        +breakpoints: OptionField
        +prerun_diagnostic: OptionField
        +postrun_diagnostic: OptionField
    }
    
    class FilteringOptionGroup {
        +name = "filtering"
        +includes: OptionField
        +excludes: OptionField
        +include_marker_exp: OptionField
        +exclude_marker_exp: OptionField
    }
    
    class DebugOptionGroup {
        +name = "debug"
        +debug: OptionField
    }
    
    OptionGroup <|-- RootOptionGroup
    OptionGroup <|-- OutputOptionGroup
    OptionGroup <|-- BuildOptionGroup
    OptionGroup <|-- JobOptionGroup
    OptionGroup <|-- LoggingOptionGroup
    OptionGroup <|-- DiagnosticOptionGroup
    OptionGroup <|-- FilteringOptionGroup
    OptionGroup <|-- DebugOptionGroup
```

**Option Group Details:**

| Group | Options | Purpose |
|-------|---------|---------|
| RootOptionGroup | `--root` | Test root directory specification |
| OutputOptionGroup | `--output`, `--start`, `--runid` | Result output configuration |
| BuildOptionGroup | `--branch`, `--build`, `--flavor` | Build metadata association |
| JobOptionGroup | `--job-id`, `--job-initiator`, `--job-label`, `--job-name`, `--job-owner` | Job identification |
| LoggingOptionGroup | `--console-level`, `--logfile-level` | Log level configuration |
| DiagnosticOptionGroup | `--debugger`, `--breakpoint`, `--prerun-diagnostic`, `--postrun-diagnostic` | Debug and diagnostic options |
| FilteringOptionGroup | `--includes`, `--excludes`, `--include-marker-exp`, `--exclude-marker-exp` | Test filtering |
| DebugOptionGroup | `--debug` | Debug output flag |

#### 3. Testing Command Group (`cmdtree/testing/`)

The testing group contains commands for test execution and querying.

##### Run Command (`run.py`)

```mermaid
classDiagram
    class command_testbase_testing_run {
        <<decorators>>
        @RootOptionGroup.attach()
        @FilteringOptionGroup.attach()
        @OutputOptionGroup.attach()
        @BuildOptionGroup.attach()
        @JobOptionGroup.attach()
        @LoggingOptionGroup.attach()
        @DiagnosticOptionGroup.attach()
        @arcli.command("run")
        <<parameters>>
        +root: Optional[str]
        +includes: Optional[List[str]]
        +excludes: Optional[List[str]]
        +output: Optional[str]
        +start: Optional[str]
        +runid: Optional[str]
        +branch: Optional[str]
        +build: Optional[str]
        +flavor: Optional[str]
        +job_id: Optional[str]
        +job_initiator: Optional[str]
        +job_label: Optional[str]
        +job_name: Optional[str]
        +job_owner: Optional[str]
        +console_level: Optional[str]
        +logfile_level: Optional[str]
        +debugger: Optional[str]
        +breakpoints: Optional[List[str]]
        +prerun_diagnostic: bool
        +postrun_diagnostic: bool
        +include_marker_exp: Optional[List[str]]
        +exclude_marker_exp: Optional[List[str]]
    }
```

**Execution Flow:**

```mermaid
flowchart TD
    A[Parse CLI Arguments] --> B[Apply Runtime Option Overrides]
    B --> C[Resolve Test Root]
    C --> D{Root Exists?}
    D -->|No| E[Raise ValueError]
    D -->|Yes| F[Extend Python Path]
    F --> G[Parse Marker Expressions]
    G --> H[Initialize Results]
    H --> I[Get Logger]
    I --> J[Get TestJob Type from Factory]
    J --> K[Create TestJob Context]
    K --> L[Execute Job]
    L --> M[Exit with Result Code]
```

##### Query Command (`query.py`)

```mermaid
classDiagram
    class command_testbase_testing_query {
        <<decorators>>
        @RootOptionGroup.attach()
        @FilteringOptionGroup.attach()
        @arcli.command("query")
        <<parameters>>
        +root: Optional[str]
        +includes: Optional[List[str]]
        +excludes: Optional[List[str]]
        +include_marker_exp: Optional[List[str]]
        +exclude_marker_exp: Optional[List[str]]
    }
```

**Output Format:**

```
Tests:
    package.module@test_function_1
        param1: FactorySource(scope=session)
        param2: FactorySource(scope=module)
    package.module@test_function_2
        ...

IMPORT ERRORS:
    path/to/module.py
```

##### Jobs Group (`jobs.py`)

```mermaid
classDiagram
    class group_testbase_testing_jobs {
        <<decorator>>
        @arcli.group("jobs")
    }
    
    class command_testing_jobs_list {
        <<decorators>>
        @arcli.option("--filter")
        @RootOptionGroup.attach()
        @DebugOptionGroup.attach()
        @arcli.command("list")
        <<parameters>>
        +root: Optional[str]
        +filter: Optional[str]
        +debug: bool
    }
    
    class command_testbase_testing_jobs_show {
        <<decorators>>
        @arcli.option("--job", required=True)
        @RootOptionGroup.attach()
        @DebugOptionGroup.attach()
        @arcli.command("show")
        <<parameters>>
        +root: Optional[str]
        +job: str
        +debug: bool
    }
    
    class command_testbase_testing_jobs_run {
        <<decorators>>
        @arcli.option("--job", required=True)
        @RootOptionGroup.attach()
        @OutputOptionGroup.attach()
        @BuildOptionGroup.attach()
        @LoggingOptionGroup.attach()
        @arcli.command("run")
        <<parameters>>
        +root: Optional[str]
        +job: str
        +output: Optional[str]
        +start: Optional[str]
        +runid: Optional[str]
        +branch: Optional[str]
        +build: Optional[str]
        +flavor: Optional[str]
        +console_level: Optional[str]
        +logfile_level: Optional[str]
    }
    
    group_testbase_testing_jobs --> command_testing_jobs_list
    group_testbase_testing_jobs --> command_testbase_testing_jobs_show
    group_testbase_testing_jobs --> command_testbase_testing_jobs_run
```

**Job Specification Format:**

```
package.module@JobClass
```

#### 4. Services Command Group (`cmdtree/services/`)

##### Results Server Command (`results.py`)

```mermaid
classDiagram
    class command_testbase_services_results {
        <<decorators>>
        @arcli.option("--port", default=8880)
        @arcli.option("--bind", default="")
        @arcli.option("--directory", default=None)
        @arcli.command("results")
        <<parameters>>
        +directory: Optional[str]
        +bind: str
        +port: int
    }
```

**Server Configuration:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--directory` | `<presence_dir>/results` | Root directory for serving results |
| `--bind` | `""` (all interfaces) | IP address to bind to |
| `--port` | `8880` | Port number |

#### 5. Utilities Command Group (`cmdtree/utilities/`)

##### Timestamp Command (`timestamp.py`)

```mermaid
classDiagram
    class command_testbase_utilities_timestamp {
        <<decorator>>
        @arcli.command("timestamp")
        <<output>>
        +prints: "YYYY-MM-DDTHH:MM:SS.ffffff"
    }
```

### Data Flow

#### Command Execution Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as CLI Parser
    participant Root as Root Command
    participant Group as Command Group
    participant Cmd as Command Handler
    participant Runtime as TestBase Runtime
    participant Job as TestJob
    
    User->>CLI: testbase testing run --root ./tests -i "pkg@*"
    CLI->>Root: Parse global options
    Root->>Root: initialize_testbase_runtime()
    Root->>Root: Configure verbosity
    CLI->>Group: Route to 'testing' group
    CLI->>Cmd: Route to 'run' command
    Cmd->>Cmd: Parse command options
    Cmd->>Runtime: Apply option overrides
    Cmd->>Runtime: Initialize results
    Cmd->>Job: Create TestJob
    Job->>Job: execute()
    Job-->>Cmd: result_code
    Cmd->>User: sys.exit(result_code)
```

#### Option Override Flow

```mermaid
flowchart TD
    A[CLI Arguments] --> B{Option Present?}
    B -->|Yes| C[AM_RUNTIME_OPTION_OVERRIDES]
    B -->|No| D[Use Default/Environment]
    
    C --> E[override_build_branch]
    C --> F[override_build_name]
    C --> G[override_build_flavor]
    C --> H[override_job_id]
    C --> I[override_loglevel_console]
    C --> J[override_output_directory]
    C --> K[override_testroot]
    C --> L[override_debug_breakpoints]
    
    E --> M[RuntimeVariables]
    F --> M
    G --> M
    H --> M
    I --> M
    J --> M
    K --> M
    L --> M
```

### Design Patterns

#### 1. Decorator Pattern

Commands and options are defined using decorators from `ccai.arcli`:

```python
@arcli.option('-v', '--verbose', default=0, mode=OptionMode.Counter)
@arcli.entry("testbase")
def testbase_root_command(verbose: int):
    ...
```

#### 2. Composite Pattern

Command groups compose individual commands into a tree structure:

```python
@arcli.group("testing")
def group_testbase_testing():
    ...

group_testbase_testing.add_command(command_testbase_testing_run)
group_testbase_testing.add_command(command_testbase_testing_query)
group_testbase_testing.add_command(group_testbase_testing_jobs)
```

#### 3. Template Method Pattern

Option groups provide reusable templates with customizable help text:

```python
@RootOptionGroup.attach(help_fill={"action": "run"})
@FilteringOptionGroup.attach(help_fill={"action": "run"})
@arcli.command("run")
def command_testbase_testing_run(...):
    ...
```

#### 4. Factory Pattern

Test job types are obtained through the factory protocol:

```python
sfactory = ConfiguredSuperFactorySingleton()
TestJobType = sfactory.get_override_types_by_order(
    TestBaseFactoryProtocol.get_testbase_default_job_type
)
```

#### 5. Context Manager Pattern

Test jobs are executed within context managers for proper lifecycle management:

```python
with TestJobType(logger, test_root, includes=includes, excludes=excludes) as tjob:
    result_code = tjob.execute()
```

## Integration Points

### With Test Execution Engine

The CLI integrates with the execution engine through:

- `TestJob` creation and execution
- Runtime option overrides
- Result initialization

```mermaid
sequenceDiagram
    participant CLI as CLI Command
    participant Override as AM_RUNTIME_OPTION_OVERRIDES
    participant Init as initialize_testbase_results
    participant Factory as ConfiguredSuperFactorySingleton
    participant Job as TestJob
    
    CLI->>Override: Apply CLI options
    CLI->>Init: Initialize results system
    CLI->>Factory: Get TestJob type
    Factory-->>CLI: TestJobType
    CLI->>Job: Create and execute
    Job-->>CLI: result_code
```

### With Runtime System

The CLI configures the runtime through:

- `initialize_testbase_runtime()` - Framework initialization
- `AM_RUNTIME_OPTION_OVERRIDES` - Option value overrides
- `RuntimeVariables` - Environment variable access
- `ThisApplicationSingleton` - Application-wide settings

### With Logging System

The CLI configures logging through:

- Verbosity flag mapping to log levels
- Console and file log level options
- Interactive console mode setting

### With Result Recording System

The CLI integrates with results through:

- `initialize_testbase_results()` - Result system setup
- Output directory configuration
- Run ID and start time specification

### With Dependency Injection System

The CLI uses the factory system to obtain:

- Default test job types
- Extension-provided job types
- Custom job implementations via `--job` parameter

## Configuration

### Environment Variables

The CLI respects these environment variables:

| Variable | CLI Override | Description |
|----------|--------------|-------------|
| `AM_TESTROOT` | `--root` | Default test root directory |
| `AM_OUTPUT` | `--output` | Default output directory |
| `AM_LOG_LEVEL_CONSOLE` | `--console-level` | Console log level |
| `AM_LOG_LEVEL_FILE` | `--logfile-level` | File log level |
| `AM_BUILD_BRANCH` | `--branch` | Build branch name |
| `AM_BUILD_NAME` | `--build` | Build name |
| `AM_BUILD_FLAVOR` | `--flavor` | Build flavor |

### Command Line Precedence

Options are resolved in this order (highest to lowest precedence):

1. Command line arguments
2. Environment variables
3. Configuration files
4. Default values

### Help Text Customization

Option groups support dynamic help text through `help_fill`:

```python
HELP_ROOT = "The root directory to use when scanning for tests to {action}."

@RootOptionGroup.attach(help_fill={"action": "run"})
# Results in: "The root directory to use when scanning for tests to run."
```

## Error Handling

### Validation Errors

| Error Condition | Handling |
|-----------------|----------|
| Invalid root directory | Raise `ValueError` with descriptive message |
| Invalid job specification | Raise `ValueError` with format hint |
| Import failure for job module | Raise `argparse.ArgumentError` |
| Missing job class in module | Raise `argparse.ArgumentError` |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All tests passed |
| 1+ | Number of failed/errored tests |
| -1 | Configuration or setup error |

### Error Messages

Error messages include context for debugging:

```python
errmsg = "The specified root folder does not exist. root=%s" % root
if test_root != root:
    errmsg += " expanded=%s" % test_root
raise ValueError(errmsg)
```

## Testing Strategy

### Unit Testing Focus Areas

1. **Option Parsing**
   - Option group attachment
   - Default value handling
   - Multiple value accumulation
   - Choice validation

2. **Command Routing**
   - Group hierarchy navigation
   - Command dispatch
   - Help generation

3. **Option Override Application**
   - Override method invocation
   - Value propagation to runtime

4. **Path Resolution**
   - Root directory expansion
   - Python path modification
   - Directory existence validation

### Integration Testing

1. **End-to-End Command Execution**
   - `testbase testing run` with sample tests
   - `testbase testing query` output validation
   - `testbase services results` server startup

2. **Option Combination Testing**
   - Multiple include/exclude expressions
   - Marker expression parsing
   - Build metadata propagation

### Test Categories

| Category | Components | Focus |
|----------|------------|-------|
| Parsing | Option groups, decorators | Argument parsing correctness |
| Routing | Command tree | Command dispatch |
| Integration | Run command | Full execution flow |
| Validation | All commands | Error handling |

## Usage Examples

### Running Tests

```bash
# Run all tests in a directory
testbase testing run --root ./tests

# Run specific tests with includes
testbase testing run --root ./tests -i "package.module@test_*"

# Run with exclusions
testbase testing run --root ./tests -i "package@*" -x "package@test_slow_*"

# Run with marker filtering
testbase testing run --root ./tests --include-marker-exp "priority=high"

# Run with verbose output
testbase -vv testing run --root ./tests

# Run with custom output directory
testbase testing run --root ./tests -o ./results

# Run with build metadata
testbase testing run --root ./tests --branch main --build 1.0.0

# Run with debugging
testbase testing run --root ./tests --debugger debugpy --breakpoint test-discovery
```

### Querying Tests

```bash
# List all tests
testbase testing query --root ./tests

# Query with filtering
testbase testing query --root ./tests -i "package.module@*"

# Query with marker filtering
testbase testing query --root ./tests --include-marker-exp "smoke"
```

### Running Jobs

```bash
# Run a specific job class
testbase testing jobs run --root ./tests --job "package.jobs@SmokeTestJob"

# List available jobs
testbase testing jobs list --root ./tests

# Show job details
testbase testing jobs show --root ./tests --job "package.jobs@SmokeTestJob"
```

### Services

```bash
# Start results server on default port
testbase services results

# Start on custom port and directory
testbase services results --port 9000 --directory ./test-results

# Bind to specific interface
testbase services results --bind 127.0.0.1 --port 8880
```

### Utilities

```bash
# Get current timestamp for pipeline use
testbase utilities timestamp
# Output: 2025-01-15T10:30:45.123456
```

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
