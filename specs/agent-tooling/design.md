# Agent Tooling - Design Document

## Overview

The Agent Tooling feature adds a `testbase agents` command group that provides compact, machine-readable
commands for AI coding agents and automation scripts to extract and analyze test result data. These commands
operate on standard TestBase result artifacts without requiring runtime initialization or a test environment.

The design follows two key principles:
- **Offline operation**: Commands read result files directly — no running test session needed
- **Compact output**: Key-value text format optimized for agent context windows, not human readability

## Architecture

### Command Tree Structure

```
testbase
└── agents
    ├── summary
    │   ├── extract      # Extract compact summary from testrun_summary.json
    │   └── compare      # Compare two summary files for regressions
    ├── testresult
    │   ├── extract      # Extract a single test result by name
    │   ├── list         # List all tests and their results
    │   └── failures     # List only failed/errored tests
    └── config
        └── extract      # Extract key config from startup-configuration.json
```

### High-Level Component Diagram

```mermaid
graph TB
    subgraph "Entry Layer"
        TB[testbase command]
    end

    subgraph "Agent Command Group"
        AG[agents group]
    end

    subgraph "Agent Subgroups"
        SG[summary group]
        TG[testresult group]
        CG[config group]
    end

    subgraph "Summary Commands"
        SE[summary extract]
        SC[summary compare]
    end

    subgraph "Test Result Commands"
        TE[testresult extract]
        TL[testresult list]
        TF[testresult failures]
    end

    subgraph "Config Commands"
        CE[config extract]
    end

    subgraph "Shared Utilities"
        JP[JSOS Parser]
        CF[Compact Formatter]
        PR[Path Resolver]
    end

    TB --> AG
    AG --> SG
    AG --> TG
    AG --> CG

    SG --> SE
    SG --> SC

    TG --> TE
    TG --> TL
    TG --> TF

    CG --> CE

    SE --> CF
    SC --> CF
    TE --> JP
    TE --> CF
    TL --> JP
    TL --> CF
    TF --> JP
    TF --> CF
    CE --> CF

    SE --> PR
    SC --> PR
    TE --> PR
    TL --> PR
    TF --> PR
    CE --> PR
```

### Components

#### 1. Agents Command Group (`cmdtree/agents/__init__.py`)

The agents group is a top-level command group registered on the root `testbase` command.
It does **not** call `initialize_testbase_runtime()` because agent commands only read result files.

```mermaid
classDiagram
    class group_testbase_agents {
        <<decorator>>
        @arcli.group("agents")
        <<behavior>>
        +No runtime initialization
    }

    class group_testbase_agents_summary {
        <<decorator>>
        @arcli.group("summary")
    }

    class group_testbase_agents_testresult {
        <<decorator>>
        @arcli.group("testresult")
    }

    class group_testbase_agents_config {
        <<decorator>>
        @arcli.group("config")
    }

    group_testbase_agents --> group_testbase_agents_summary
    group_testbase_agents --> group_testbase_agents_testresult
    group_testbase_agents --> group_testbase_agents_config
```

#### 2. Compact Formatter (`agents/formatting.py`)

A shared utility module that provides consistent compact output formatting across all agent commands.

```mermaid
classDiagram
    class CompactFormatter {
        +format_kv(key: str, value: str) str
        +format_section(name: str) str
        +format_error(message: str) str
        +omit_unset(value: str) Optional[str]
    }
```

**Output Format Rules:**

| Rule | Format | Example |
|------|--------|---------|
| Key-Value | `key: value` | `result: PASSED` |
| Section Header | `section:` | `detail:` |
| Nested Field | `  key: value` (2-space indent) | `  passed: 3` |
| Omitted Field | (not printed) | When value is `None`, `(not-set)`, or `(unknown)` |

**Example compact output for `summary extract`:**

```
result: PASSED
start: 2026-02-24T22:04:46.299524
stop: 2026-02-24 22:04:50.357629
detail:
  passed: 3
  failed: 0
  errors: 0
  skipped: 0
  total: 3
job:
  id: 8344f668-a0e3-4ef6-89ca-acf007fcb3a0
  type: TestRun
```

#### 3. JSOS Parser (`agents/jsosparser.py`)

A shared utility for parsing `testrun_results_stream.jsos` files. JSOS files contain
multiple JSON objects separated by blank lines.

```mermaid
classDiagram
    class JSOSParser {
        +parse_file(filepath: str) List[dict]
        +filter_tests(entries: List[dict]) List[dict]
        +get_final_results(entries: List[dict]) Dict[str, dict]
    }
```

**Parsing Logic:**

```mermaid
flowchart TD
    A[Read JSOS File] --> B[Split on blank lines]
    B --> C[Parse each chunk as JSON]
    C --> D[Collect all entries]
    D --> E{Filter by rtype?}
    E -->|TEST only| F[filter_tests]
    E -->|Final results| G[get_final_results]
    F --> H[Return TEST entries]
    G --> I[Group by name, keep last entry per name]
    I --> J[Return final result dict]
```

**JSOS Entry Structure (rtype=TEST):**

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Fully qualified test name (e.g., `pkg.mod#test_func`) |
| `instance` | `str` | UUID instance identifier |
| `parent` | `str` | Parent container UUID |
| `rtype` | `str` | `TEST`, `TEST_CONTAINER`, or `JOB` |
| `result` | `str` | `PASSED`, `FAILED`, `ERRORED`, `SKIPPED`, or `UNSET` |
| `start` | `str` | ISO timestamp |
| `stop` | `str` | ISO timestamp |
| `detail` | `dict` | Optional — contains `errors` list with error info |

#### 4. Path Resolver (`agents/pathresolver.py`)

A shared utility for resolving and validating file paths.

```python
def resolve_file_path(filepath: str) -> str:
    """Expand vars, expand user, resolve to absolute, validate existence."""
    resolved = os.path.abspath(os.path.expandvars(os.path.expanduser(filepath)))
    if not os.path.isfile(resolved):
        raise FileNotFoundError(f"File not found: {resolved}")
    return resolved
```

#### 5. Summary Extract Command (`agents/summary/extract.py`)

```mermaid
flowchart TD
    A[Parse --summary-file] --> B[Resolve path]
    B --> C{File exists?}
    C -->|No| D[ERROR: file not found]
    C -->|Yes| E[Read and parse JSON]
    E --> F{Valid JSON?}
    F -->|No| G[ERROR: invalid JSON]
    F -->|Yes| H[Extract key fields]
    H --> I[Format with CompactFormatter]
    I --> J[Print to stdout]
```

**Extracted Fields:**

| Source Path | Output Key | Condition |
|-------------|-----------|-----------|
| `$.result` | `result` | Always |
| `$.start` | `start` | Always |
| `$.stop` | `stop` | Always |
| `$.detail.passed` | `detail.passed` | Always |
| `$.detail.failed` | `detail.failed` | Always |
| `$.detail.errors` | `detail.errors` | Always |
| `$.detail.skipped` | `detail.skipped` | Always |
| `$.detail.total` | `detail.total` | Always |
| `$.job.id` | `job.id` | When not `(not-set)` |
| `$.job.name` | `job.name` | When not `(not-set)` |
| `$.job.type` | `job.type` | When not `(not-set)` |
| `$.build.branch` | `build.branch` | When not `(not-set)` |
| `$.build.build` | `build.build` | When not `(not-set)` |

#### 6. Summary Compare Command (`agents/summary/compare.py`)

```mermaid
flowchart TD
    A[Parse --baseline and --current] --> B[Resolve both paths]
    B --> C{Both exist?}
    C -->|No| D[ERROR: file not found]
    C -->|Yes| E[Parse both JSON files]
    E --> F[Compare result fields]
    F --> G[Compute counter deltas]
    G --> H[Classify: regression / improvement / stable]
    H --> I[Format with CompactFormatter]
    I --> J[Print to stdout]
```

**Example output:**

```
overall: PASSED->FAILED (regression)
delta:
  passed: -2
  failed: +2
  errors: 0
  skipped: 0
  total: 0
```

#### 7. Test Result Extract Command (`agents/testresult/extract.py`)

```mermaid
flowchart TD
    A[Parse --results-file and --testname] --> B[Resolve path]
    B --> C{File exists?}
    C -->|No| D[ERROR: file not found]
    C -->|Yes| E[Parse JSOS file]
    E --> F[Get final results]
    F --> G{Test name found?}
    G -->|No| H[ERROR: test not found]
    G -->|Yes| I[Extract test details]
    I --> J[Format with CompactFormatter]
    J --> K[Print to stdout]
```

**Example output:**

```
name: pkg.mod#test_something
result: FAILED
start: 2026-02-24T22:04:46.345818
stop: 2026-02-24T22:04:50.350592
errors:
  - TypeError: expected str, got int
```

#### 8. Test Result List Command (`agents/testresult/list.py`)

Lists all test names and their final results. Supports filtering by result code.

**Example output:**

```
pkg.mod#test_alpha: PASSED
pkg.mod#test_beta: FAILED
pkg.mod#test_gamma: SKIPPED
```

#### 9. Test Result Failures Command (`agents/testresult/failures.py`)

Lists only FAILED and ERRORED tests with brief error summaries.

**Example output:**

```
pkg.mod#test_beta: FAILED
  error: AssertionError: 3 != 4
pkg.mod#test_delta: ERRORED
  error: ConnectionError: connection refused
```

#### 10. Configuration Extract Command (`agents/config/extract.py`)

```mermaid
flowchart TD
    A[Parse --config-file] --> B[Resolve path]
    B --> C{File exists?}
    C -->|No| D[ERROR: file not found]
    C -->|Yes| E[Read and parse JSON]
    E --> F[Extract key settings]
    F --> G[Format with CompactFormatter]
    G --> H[Print to stdout]
```

### Data Flow

#### Agent Command Execution Flow

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant CLI as CLI Parser
    participant Cmd as Agent Command
    participant PR as Path Resolver
    participant Parser as File Parser
    participant CF as Compact Formatter

    Agent->>CLI: testbase agents summary extract --summary-file=path
    CLI->>Cmd: Route to summary extract
    Cmd->>PR: resolve_file_path(path)
    PR-->>Cmd: resolved_path
    Cmd->>Parser: Parse JSON/JSOS file
    Parser-->>Cmd: parsed_data
    Cmd->>CF: Format compact output
    CF-->>Cmd: formatted_text
    Cmd->>Agent: Print to stdout
```

## Integration Points

### With Existing CLI

The `agents` command group integrates with the CLI by registering on the root `testbase` command:

```python
# In testbase_command.py
testbase_root_command.add_command(group_testbase_agents)
```

The agents group intentionally does **not** integrate with:
- Runtime initialization (`initialize_testbase_runtime`)
- Option overrides (`AM_RUNTIME_OPTION_OVERRIDES`)
- Test execution engine

This keeps the agent commands lightweight and fast.

### With Result Artifacts

Agent commands operate on the standard TestBase result artifacts:

| Artifact | Producer | Agent Consumer |
|----------|----------|----------------|
| `testrun_summary.json` | `ResultRecorder.__exit__` | `summary extract`, `summary compare` |
| `testrun_results_stream.jsos` | `ResultRecorder` (streaming) | `testresult extract`, `testresult list`, `testresult failures` |
| `startup-configuration.json` | `initialize_testbase_results` | `config extract` |

## Error Handling

### Error Format

All errors are printed to stderr in the format:

```
ERROR: <description>
```

### Error Conditions

| Condition | Exit Code | Error Message |
|-----------|-----------|---------------|
| File not found | 1 | `ERROR: File not found: <resolved_path>` |
| Invalid JSON | 1 | `ERROR: Invalid JSON in file: <resolved_path>` |
| Test name not found | 1 | `ERROR: Test '<testname>' not found in results file` |
| Invalid JSOS format | 1 | `ERROR: Invalid JSOS format in file: <resolved_path>` |

## Testing Strategy

### Unit Testing Focus Areas

1. **JSOS Parser** — Parsing multi-object JSOS streams, filtering by rtype, deduplicating final results
2. **Compact Formatter** — Key-value formatting, section nesting, omission of unset values
3. **Path Resolver** — Environment variable expansion, home directory expansion, file existence validation
4. **Individual Commands** — Correct extraction of fields, error handling for missing/invalid inputs

### Test Organization

| Test Module | Tests |
|-------------|-------|
| `test_jsosparser.py` | JSOS parsing, filtering, final result deduplication |
| `test_compact_formatter.py` | Output format consistency, indentation, field omission |
| `test_summary_extract.py` | Summary field extraction, error cases |
| `test_summary_compare.py` | Delta computation, regression classification |
| `test_testresult_extract.py` | Single test extraction, UNSET deduplication |
| `test_testresult_list.py` | Full listing, result filtering |
| `test_testresult_failures.py` | Failure collection, error summary extraction |
| `test_config_extract.py` | Configuration field extraction |

## Usage Examples

### Summary Operations

```bash
# Extract summary from a test run
testbase agents summary extract --summary-file=~/ccai/results/testresults/2026-02-24T2204S46/testrun_summary.json

# Compare two runs for regressions
testbase agents summary compare \
    --baseline=~/ccai/results/testresults/run1/testrun_summary.json \
    --current=~/ccai/results/testresults/run2/testrun_summary.json
```

### Test Result Operations

```bash
# Extract a specific test result
testbase agents testresult extract \
    --results-file=./testrun_results_stream.jsos \
    --testname="ccai.tests.testbase.injection.test_constraints#test_activity_logging"

# List all test results
testbase agents testresult list --results-file=./testrun_results_stream.jsos

# List only failed tests
testbase agents testresult list --results-file=./testrun_results_stream.jsos --result-filter=FAILED

# List failures with error summaries
testbase agents testresult failures --results-file=./testrun_results_stream.jsos
```

### Configuration Operations

```bash
# Extract configuration for a test run
testbase agents config extract --config-file=./startup-configuration.json
```

## File Structure

```
source/packages/ccai/testbase/cli/
└── cmdtree/
    └── agents/
        ├── __init__.py              # Agents group definition
        ├── formatting.py            # CompactFormatter utility
        ├── jsosparser.py            # JSOS file parser
        ├── pathresolver.py          # File path resolution utility
        ├── summary/
        │   ├── __init__.py          # Summary subgroup definition
        │   ├── extract.py           # Summary extract command
        │   └── compare.py           # Summary compare command
        ├── testresult/
        │   ├── __init__.py          # Test result subgroup definition
        │   ├── extract.py           # Test result extract command
        │   ├── list.py              # Test result list command
        │   └── failures.py          # Test result failures command
        └── config/
            ├── __init__.py          # Config subgroup definition
            └── extract.py           # Config extract command

source/tests/ccai_tests/testbase/cli/agents/
├── __init__.py
├── test_jsosparser.py
├── test_compact_formatter.py
├── test_summary_extract.py
├── test_summary_compare.py
├── test_testresult_extract.py
├── test_testresult_list.py
├── test_testresult_failures.py
└── test_config_extract.py
```
