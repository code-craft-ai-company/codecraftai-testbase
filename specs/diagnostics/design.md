# Diagnostics System - Design Document

## Overview

The Diagnostics System provides a framework for capturing diagnostic information at key points during test execution. It enables integration couplings to collect and store diagnostic data about the test environment, devices, and system state at predefined stages of the test run lifecycle.

The system supports two primary diagnostic capture points:
- **Pre-run diagnostics**: Captured before test execution begins
- **Post-run diagnostics**: Captured after test execution completes

This diagnostic capability is essential for:
- Debugging test failures by capturing system state
- Auditing test environment conditions
- Collecting device logs and status information
- Supporting post-mortem analysis of test runs

## Architecture

### High-Level Component Diagram

```mermaid
graph TB
    subgraph "Constants Layer"
        DL[DiagnosticLabel]
        RCP[RuntimeConfigPaths]
    end
    
    subgraph "Configuration Layer"
        RV[RuntimeVariables]
        DOG[DiagnosticOptionGroup]
    end
    
    subgraph "Execution Layer"
        TJ[TestJob]
        TS[TestSequencer]
    end
    
    subgraph "Integration Layer"
        IC[IntegrationCoupling]
        DIC[Derived Integration Couplings]
    end
    
    subgraph "Storage Layer"
        DF[Diagnostic Folder]
        RP[Runtime Paths]
    end
    
    DOG --> RV
    RV --> TS
    DL --> TS
    RCP --> RV
    
    TJ --> TS
    TS --> IC
    IC --> DIC
    
    TS --> RP
    RP --> DF
    DIC --> DF
```

### Components

#### 1. DiagnosticLabel Class

The `DiagnosticLabel` class defines constants that identify well-known diagnostic stages in the test execution lifecycle.

```mermaid
classDiagram
    class DiagnosticLabel {
        <<class>>
        +PRERUN_DIAGNOSTIC: str = "prerun-diagnostic"
        +POSTRUN_DIAGNOSTIC: str = "postrun-diagnostic"
    }
```

**Label Definitions:**

| Label | Value | Description |
|-------|-------|-------------|
| `PRERUN_DIAGNOSTIC` | `"prerun-diagnostic"` | Identifies diagnostics captured before test execution |
| `POSTRUN_DIAGNOSTIC` | `"postrun-diagnostic"` | Identifies diagnostics captured after test execution |

#### 2. RuntimeConfigPaths Class

The `RuntimeConfigPaths` class defines configuration paths for diagnostic runtime information within the application's configuration tree.

```mermaid
classDiagram
    class RuntimeConfigPaths {
        <<class>>
        +DIAGNOSTIC_PRERUN: str
        +DIAGNOSTIC_POSTRUN: str
    }
```

**Path Definitions:**

| Path Constant | Value | Purpose |
|---------------|-------|---------|
| `DIAGNOSTIC_PRERUN` | `/configuration/runtime/diagnostics/prerun-diagnostic` | Configuration path for pre-run diagnostic settings |
| `DIAGNOSTIC_POSTRUN` | `/configuration/runtime/diagnostics/postrun-diagnostic` | Configuration path for post-run diagnostic settings |

#### 3. DiagnosticOptionGroup (CLI Integration)

The `DiagnosticOptionGroup` provides command-line options for controlling diagnostic behavior during test runs.

```mermaid
classDiagram
    class DiagnosticOptionGroup {
        <<OptionGroup>>
        +name: str = "diagnostic"
        +debugger: OptionField
        +breakpoints: OptionField
        +prerun_diagnostic: OptionField
        +postrun_diagnostic: OptionField
    }
```

**CLI Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--debugger` | Choice['pdb', 'debugpy'] | None | Debugger to activate during test run |
| `--breakpoint` | Multiple Choice | None | Breakpoints to activate |
| `--prerun-diagnostic` | Boolean | False | Enable pre-run diagnostic capture |
| `--postrun-diagnostic` | Boolean | False | Enable post-run diagnostic capture |

#### 4. IntegrationCoupling.diagnostic() Method

The abstract `diagnostic()` method on `IntegrationCoupling` defines the contract for diagnostic capture by integration types.

```mermaid
classDiagram
    class IntegrationCoupling {
        <<abstract>>
        +diagnostic(label: str, level: int, diag_folder: str)*
    }
    
    class DerivedCoupling {
        +diagnostic(label: str, level: int, diag_folder: str)
    }
    
    IntegrationCoupling <|-- DerivedCoupling
```

**Method Signature:**

```python
@classmethod
def diagnostic(cls, label: str, level: int, diag_folder: str):
    """
    Capture diagnostic information for the integration.
    
    :param label: The label associated with this diagnostic (e.g., "prerun-diagnostic")
    :param level: The maximum diagnostic level to run diagnostics for (1-9)
    :param diag_folder: The output folder path where diagnostic information should be written
    """
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `label` | `str` | Diagnostic stage identifier from `DiagnosticLabel` |
| `level` | `int` | Maximum diagnostic level (1-9, higher = more detailed) |
| `diag_folder` | `str` | Output directory for diagnostic files |

### Data Flow

#### Diagnostic Capture Flow

```mermaid
sequenceDiagram
    participant CLI as CLI Command
    participant TJ as TestJob
    participant TS as TestSequencer
    participant RV as RuntimeVariables
    participant IC as IntegrationCoupling
    participant FS as File System
    
    Note over CLI,RV: Configuration Phase
    CLI->>RV: Set AM_DIAGNOSTICS_PRERUN/POSTRUN
    
    Note over TJ,TS: Pre-Run Diagnostic Phase
    TJ->>TS: fire_diagnostic_capture_pre_testrun(level)
    TS->>RV: Check AM_DIAGNOSTICS_PRERUN
    alt Prerun enabled
        TS->>FS: get_path_for_diagnostics("prerun-diagnostic")
        FS-->>TS: diagnostic_root path
        loop For each integration
            TS->>IC: diagnostic("prerun-diagnostic", level, diagnostic_root)
            IC->>FS: Write diagnostic files
        end
    end
    
    Note over TJ,TS: Test Execution
    TJ->>TS: execute_tests()
    
    Note over TJ,TS: Post-Run Diagnostic Phase
    TJ->>TS: fire_diagnostic_capture_post_testrun(level)
    TS->>RV: Check AM_DIAGNOSTICS_POSTRUN
    alt Postrun enabled
        TS->>FS: get_path_for_diagnostics("postrun-diagnostic")
        FS-->>TS: diagnostic_root path
        loop For each integration
            TS->>IC: diagnostic("postrun-diagnostic", level, diagnostic_root)
            IC->>FS: Write diagnostic files
        end
    end
```

#### Configuration Flow

```mermaid
flowchart TD
    A[CLI: --prerun-diagnostic] --> B[AM_RUNTIME_OPTION_OVERRIDES]
    B --> C[override_diagnostics_prerun]
    C --> D[RuntimeVariables.AM_DIAGNOSTICS_PRERUN = True]
    
    E[CLI: --postrun-diagnostic] --> F[AM_RUNTIME_OPTION_OVERRIDES]
    F --> G[override_diagnostics_postrun]
    G --> H[RuntimeVariables.AM_DIAGNOSTICS_POSTRUN = True]
    
    D --> I[TestSequencer.diagnostic_capture_pre_testrun]
    H --> J[TestSequencer.diagnostic_capture_post_testrun]
```

### Design Patterns

#### 1. Template Method Pattern

The `IntegrationCoupling.diagnostic()` method defines a template that derived classes must implement:

```python
class IntegrationCoupling:
    @classmethod
    def diagnostic(cls, label: str, level: int, diag_folder: str):
        """Abstract method - must be overloaded by derived types."""
        raise AbstractMethodError(...)

class DeviceIntegrationCoupling(IntegrationCoupling):
    @classmethod
    def diagnostic(cls, label: str, level: int, diag_folder: str):
        # Concrete implementation for device diagnostics
        cls._capture_device_logs(diag_folder)
        cls._capture_device_status(diag_folder)
```

#### 2. Strategy Pattern

Different integration couplings implement different diagnostic strategies based on their resource types:

```mermaid
classDiagram
    class IntegrationCoupling {
        <<abstract>>
        +diagnostic(label, level, diag_folder)*
    }
    
    class NetworkCoupling {
        +diagnostic(label, level, diag_folder)
        -capture_network_state()
        -capture_connection_logs()
    }
    
    class DeviceCoupling {
        +diagnostic(label, level, diag_folder)
        -capture_device_logs()
        -capture_device_status()
    }
    
    class DatabaseCoupling {
        +diagnostic(label, level, diag_folder)
        -capture_query_logs()
        -capture_connection_pool_state()
    }
    
    IntegrationCoupling <|-- NetworkCoupling
    IntegrationCoupling <|-- DeviceCoupling
    IntegrationCoupling <|-- DatabaseCoupling
```

#### 3. Observer Pattern

The TestSequencer acts as an observer coordinator, notifying all registered integrations when diagnostic capture is triggered:

```python
def diagnostic_capture_post_testrun(self, level: int=9):
    if postrun_info is not None and postrun_info == True:
        label = DiagnosticLabel.POSTRUN_DIAGNOSTIC
        diagnostic_root = get_path_for_diagnostics(label)
        
        # Notify all integrations
        for _, integ_type in self._integrations.items():
            integ_type.diagnostic(label, level, diagnostic_root)
```

## Integration Points

### With CLI System

The diagnostics system integrates with the CLI through the `DiagnosticOptionGroup`:

```mermaid
sequenceDiagram
    participant User
    participant CLI as testbase testing run
    participant DOG as DiagnosticOptionGroup
    participant RO as RuntimeOptionOverrides
    participant RV as RuntimeVariables
    
    User->>CLI: --prerun-diagnostic --postrun-diagnostic
    CLI->>DOG: Parse options
    DOG-->>CLI: prerun_diagnostic=True, postrun_diagnostic=True
    CLI->>RO: override_diagnostics_prerun({})
    CLI->>RO: override_diagnostics_postrun({})
    RO->>RV: Set AM_DIAGNOSTICS_PRERUN
    RO->>RV: Set AM_DIAGNOSTICS_POSTRUN
```

### With Test Execution Engine

The TestJob orchestrates diagnostic capture at appropriate points in the test lifecycle:

| Phase | Method | Timing |
|-------|--------|--------|
| Pre-run | `fire_diagnostic_capture_pre_testrun()` | After integration setup, before test execution |
| Post-run | `fire_diagnostic_capture_post_testrun()` | After test execution, before finalization |

### With Integration Coupling System

Each `IntegrationCoupling` subclass implements its own diagnostic capture logic:

```python
class MyDeviceCoupling(IntegrationCoupling):
    @classmethod
    def diagnostic(cls, label: str, level: int, diag_folder: str):
        if level >= 1:
            cls._capture_basic_status(diag_folder)
        if level >= 5:
            cls._capture_detailed_logs(diag_folder)
        if level >= 9:
            cls._capture_full_memory_dump(diag_folder)
```

### With Results System

Diagnostic folders are excluded from result traversal to prevent diagnostic data from being processed as test results:

```python
DEFAULT_DO_NOT_DESCEND_DIRS = [
    "diagnostics"
]
```

## Configuration

### Runtime Variables

| Variable | Type | Description |
|----------|------|-------------|
| `AM_DIAGNOSTICS_PRERUN` | `bool` | Enable pre-run diagnostic capture |
| `AM_DIAGNOSTICS_POSTRUN` | `bool` | Enable post-run diagnostic capture |

### Diagnostic Levels

The diagnostic level parameter controls the verbosity of captured diagnostics:

| Level | Description | Typical Use |
|-------|-------------|-------------|
| 1-3 | Basic diagnostics | Quick status checks |
| 4-6 | Standard diagnostics | Normal debugging |
| 7-9 | Detailed diagnostics | Deep investigation |

### File System Structure

```
<test_results_dir>/
├── diagnostics/
│   ├── prerun-diagnostic/
│   │   ├── <integration_1>/
│   │   │   └── diagnostic_files...
│   │   └── <integration_2>/
│   │       └── diagnostic_files...
│   └── postrun-diagnostic/
│       ├── <integration_1>/
│       │   └── diagnostic_files...
│       └── <integration_2>/
│           └── diagnostic_files...
├── testrun_results.json
└── testrun_summary.json
```

## Error Handling

### Diagnostic Capture Errors

Errors during diagnostic capture are caught and logged but do not fail the test run:

```python
try:
    self.fire_diagnostic_capture_post_testrun(tseq)
except Exception:
    err_msg = traceback.format_exc()
    self._logger.error(err_msg)
```

### Abstract Method Errors

Calling `diagnostic()` on `IntegrationCoupling` directly raises `AbstractMethodError`:

```python
errmsg = "The 'diagnostic' method must be overloaded by derived integration coupling types."
raise AbstractMethodError(errmsg)
```

## Usage Examples

### Enabling Diagnostics via CLI

```bash
# Enable pre-run diagnostics only
testbase testing run --root ./tests --prerun-diagnostic

# Enable post-run diagnostics only
testbase testing run --root ./tests --postrun-diagnostic

# Enable both pre-run and post-run diagnostics
testbase testing run --root ./tests --prerun-diagnostic --postrun-diagnostic
```

### Implementing Custom Diagnostic Capture

```python
from automojo.testbase.coupling.integrationcoupling import IntegrationCoupling
import os
import json

class MyServiceCoupling(IntegrationCoupling):
    
    integration_root = "services"
    integration_section = "api"
    integration_leaf = "myservice"
    integration_class = "MyServiceCoupling"
    
    @classmethod
    def diagnostic(cls, label: str, level: int, diag_folder: str):
        """Capture diagnostic information for MyService."""
        
        # Create integration-specific subfolder
        service_diag_folder = os.path.join(diag_folder, "myservice")
        os.makedirs(service_diag_folder, exist_ok=True)
        
        # Level 1+: Basic status
        if level >= 1:
            status = cls._get_service_status()
            status_file = os.path.join(service_diag_folder, "status.json")
            with open(status_file, 'w') as f:
                json.dump(status, f, indent=2)
        
        # Level 5+: Connection logs
        if level >= 5:
            logs = cls._get_connection_logs()
            logs_file = os.path.join(service_diag_folder, "connection_logs.txt")
            with open(logs_file, 'w') as f:
                f.write(logs)
        
        # Level 9: Full diagnostic dump
        if level >= 9:
            full_dump = cls._get_full_diagnostic_dump()
            dump_file = os.path.join(service_diag_folder, "full_dump.json")
            with open(dump_file, 'w') as f:
                json.dump(full_dump, f, indent=2)
```

### Accessing Diagnostic Labels

```python
from automojo.testbase.diagnostics import DiagnosticLabel

def process_diagnostics(label: str):
    if label == DiagnosticLabel.PRERUN_DIAGNOSTIC:
        print("Processing pre-run diagnostics")
    elif label == DiagnosticLabel.POSTRUN_DIAGNOSTIC:
        print("Processing post-run diagnostics")
```

## File Structure

```
source/packages/automojo/testbase/
├── diagnostics.py              # DiagnosticLabel and RuntimeConfigPaths
├── testjob.py                  # TestJob with diagnostic fire methods
├── cli/
│   └── options.py              # DiagnosticOptionGroup
├── coupling/
│   └── integrationcoupling.py  # IntegrationCoupling.diagnostic()
└── sequencing/
    └── testsequencer.py        # Diagnostic capture implementation
```

## Testing Strategy

### Unit Testing Focus Areas

1. **DiagnosticLabel Constants**
   - Verify constant values are correct
   - Ensure constants are strings

2. **RuntimeConfigPaths Constants**
   - Verify path format is correct
   - Ensure paths follow configuration tree structure

3. **DiagnosticOptionGroup**
   - Test option parsing
   - Verify default values
   - Test boolean parameter handling

4. **TestSequencer Diagnostic Methods**
   - Test `diagnostic_capture_pre_testrun()` with enabled/disabled settings
   - Test `diagnostic_capture_post_testrun()` with enabled/disabled settings
   - Verify integration iteration
   - Test diagnostic level propagation

5. **TestJob Fire Methods**
   - Test `fire_diagnostic_capture_pre_testrun()` delegation
   - Test `fire_diagnostic_capture_post_testrun()` delegation
   - Verify error handling during diagnostic capture

### Integration Testing

1. **End-to-End Diagnostic Capture**
   - Run test with diagnostics enabled
   - Verify diagnostic folders are created
   - Verify integration diagnostic methods are called

2. **CLI Integration**
   - Test `--prerun-diagnostic` flag
   - Test `--postrun-diagnostic` flag
   - Verify runtime variables are set correctly

### Test Categories

| Category | Components | Focus |
|----------|------------|-------|
| Constants | `DiagnosticLabel`, `RuntimeConfigPaths` | Value correctness |
| CLI | `DiagnosticOptionGroup` | Option parsing |
| Execution | `TestSequencer`, `TestJob` | Diagnostic flow |
| Integration | `IntegrationCoupling` | Contract compliance |
