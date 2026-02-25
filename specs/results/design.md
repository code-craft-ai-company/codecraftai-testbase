# Result Recording and Reporting - Design Document

## Overview

The Result Recording and Reporting system is responsible for capturing, persisting, and organizing test execution outcomes in the TestBase framework. It provides:

- A hierarchical result model that mirrors the test execution structure
- Streaming result recording for real-time progress tracking
- Result consolidation for post-run analysis and reporting
- Progress tracking and forwarding for distributed test execution
- Support for multiple output formats through extensible recorder implementations

The system operates through three primary layers: the Data Model (result types and containers), the Recording Layer (result recorders), and the Aggregation Layer (progress concentrators).

## Architecture

### High-Level Component Diagram

```mermaid
graph TB
    subgraph "Execution Layer"
        TS[TestSequencer]
        STS[SequencerTestScope]
        TG[TaskingGroup]
    end
    
    subgraph "Recording Layer"
        RR[ResultRecorder]
        JRR[JsonResultRecorder]
    end
    
    subgraph "Data Model Layer"
        subgraph "Containers"
            RC[ResultContainer]
            JC[JobContainer]
            TC[TestContainer]
            TGC[TaskingGroup]
        end
        
        subgraph "Result Nodes"
            RN[ResultNode]
            TR[TestResult]
            TKR[TaskingResult]
        end
        
        subgraph "Metadata"
            BI[BuildInfo]
            PI[PipelineInfo]
            JI[JobInfo]
            RI[RenderInfo]
            FI[ForwardingInfo]
        end
        
        subgraph "Enumerations"
            RCode[ResultCode]
            RType[ResultType]
            PCode[ProgressCode]
            PType[ProgressType]
        end
    end
    
    subgraph "Progress Layer"
        PInfo[ProgressInfo]
        PCS[ProgressConcentratorServer]
        PCH[ProgressCallbackHandler]
    end
    
    subgraph "Output Layer"
        SF[Summary File]
        SRF[Stream Results File]
        CRF[Consolidated Results File]
        CAT[Catalog Files]
    end
    
    TS --> RR
    STS --> RR
    TG --> RR
    
    RR --> JRR
    RR --> RC
    RR --> RN
    
    RC --> JC
    RC --> TC
    RC --> TGC
    
    RN --> TR
    RN --> TKR
    
    RR --> BI
    RR --> PI
    RR --> JI
    RR --> RI
    
    JRR --> SF
    JRR --> SRF
    JRR --> CRF
    
    PCS --> PCH
    PCS --> RR
    PCH --> PInfo
    
    RR --> CAT
```

### Components

#### 1. ResultRecorder (Base Recorder)

The `ResultRecorder` class establishes the API patterns for recording test results. It manages the test run lifecycle, result counting, and summary generation.

```mermaid
classDiagram
    class ResultRecorder {
        <<instance attributes>>
        -_runid: str
        -_start: datetime
        -_apod: Optional[str]
        -_render_info: RenderInfo
        -_build_info: BuildInfo
        -_pipeline_info: PipelineInfo
        -_job_info: JobInfo
        -_forwarding_info: ForwardingInfo
        -_output_dir: str
        -_rout: file
        -_running_tasks: dict
        -_error_count: int
        -_failure_count: int
        -_pass_count: int
        -_skip_count: int
        -_unknown_count: int
        -_total_count: int
        -_finalized: bool
        -_summary: OrderedDict
        -_lock: threading.Lock
        <<properties>>
        +summary: dict
        <<methods>>
        +__enter__()
        +__exit__(ex_type, ex_inst, ex_tb) bool
        +catalog_output_directory()
        +clear_task_progress(task_ids)
        +consolidate_results()
        +finalize()
        +format_lines() List[str]
        +forward_summary_update(summary)
        +get_summary_render_file_basename() str
        +initialize_report()
        +load_result_stream() List[dict]
        +preview(result: ResultNode)*
        +post_task_progress(progress_list)
        +record(result: ResultNode)*
        +update_render_environment()
        +update_summary()*
        +write_consolidated_results(root_node)*
    }
    
    class JsonResultRecorder {
        +preview(result: ResultNode)
        +record(result: ResultNode)
        +update_summary()
        +write_consolidated_results(root_node)
    }
    
    ResultRecorder <|-- JsonResultRecorder
```

**Key Responsibilities:**

| Responsibility | Description |
|----------------|-------------|
| Lifecycle Management | Manages recording start/stop via context manager |
| Result Counting | Tracks pass/fail/error/skip counts |
| Summary Generation | Maintains and updates test run summary |
| Progress Tracking | Tracks running tasks for real-time status |
| Output Management | Manages output directory and file generation |
| Catalog Generation | Creates directory catalogs for HTML navigation |

#### 2. Result Data Model

The result data model consists of containers (for hierarchy) and nodes (for actual results).

```mermaid
classDiagram
    class ResultContainer {
        -_inst_id: str
        -_name: str
        -_result_type: ResultType
        -_parent_inst: Optional[str]
        <<properties>>
        +inst_id: str
        +name: str
        +parent_inst: str
        +result_type: ResultType
        <<methods>>
        +as_dict(is_preview) OrderedDict
        +to_json(is_preview) str
    }
    
    class JobContainer {
        +__init__(inst_id, name)
    }
    
    class TestContainer {
        +__init__(inst_id, name, parent_inst)
    }
    
    class TaskingGroup {
        -_start: datetime
        -_stop: datetime
        <<properties>>
        +start: datetime
        +stop: datetime
        <<methods>>
        +finalize()
        +as_dict(is_preview) OrderedDict
    }
    
    ResultContainer <|-- JobContainer
    ResultContainer <|-- TestContainer
    ResultContainer <|-- TaskingGroup
```

```mermaid
classDiagram
    class ResultNode {
        -_inst_id: str
        -_name: str
        -_parent_inst: str
        -_result_type: ResultType
        -_result_code: ResultCode
        -_start: datetime
        -_stop: datetime
        -_errors: List[TracebackDetail]
        -_failures: List[TracebackDetail]
        -_warnings: List[List[str]]
        -_docstr: str
        <<properties>>
        +docstr: str
        +errors: List[str]
        +failures: List[str]
        +inst_id: str
        +name: str
        +parent_inst: str
        +result_code: ResultCode
        +result_type: ResultType
        +start: datetime
        +stop: datetime
        +warnings: List[str]
        <<methods>>
        +add_error(trace_detail)
        +add_failure(trace_detail)
        +add_warning(warn_lines)
        +finalize()
        +mark_passed()
        +set_documentation(docstr)
        +as_dict(is_preview) OrderedDict
        +to_json(is_preview) str
    }
    
    class TestResult {
        -_monikers: List[str]
        -_pivots: Dict[str, Any]
        -_reason: str
        -_bug: str
        <<properties>>
        +monikers: List[str]
        +pivots: Dict[str, Any]
        <<methods>>
        +mark_skip(reason, bug)
        +as_dict(is_preview) OrderedDict
    }
    
    class TaskingResult {
        -_worker: str
        -_prefix: str
        -_rvalue: Any
        <<properties>>
        +prefix: str
        +rvalue: Any
        +worker: str
        <<methods>>
        +add_return_value(rvalue)
        +as_dict(is_preview) OrderedDict
        +format_result() List[str]
    }
    
    ResultNode <|-- TestResult
    ResultNode <|-- TaskingResult
```

#### 3. Result Type Enumerations

```mermaid
classDiagram
    class ResultCode {
        <<enumeration>>
        UNSET = 0
        PASSED = 1
        SKIPPED = 2
        ERRORED = 3
        FAILED = 4
        CANCELLED = 5
        UNKNOWN = 6
    }
    
    class ResultType {
        <<enumeration>>
        JOB = 0
        PACKAGE = 1
        SCOPE = 2
        TASK_CONTAINER = 3
        TASK = 4
        TEST_CONTAINER = 5
        TEST = 6
        STEP_CONTAINER = 7
        STEP = 8
        TASKING_GROUP = 9
        TASKING = 10
    }
```

#### 4. Metadata Classes

```mermaid
classDiagram
    class BuildInfo {
        <<dataclass>>
        +branch: str
        +build: str
        +flavor: str
        +release: str
        +url: str
    }
    
    class PipelineInfo {
        <<dataclass>>
        +id: str
        +name: str
        +instance: str
    }
    
    class JobInfo {
        <<dataclass>>
        +id: str
        +name: str
        +type: str
        +owner: Optional[str]
        +label: Optional[str]
        +initiator: Optional[str]
        +venue: Optional[str]
        +seed: Optional[str]
        +tag: Optional[str]
    }
    
    class RenderInfo {
        <<dataclass>>
        +title: str
        +summary_filename: str
        +summary_template: str
        +stream_results_filename: str
        +consolidated_results_filename: str
        +static_resource_source: str
        +static_resource_destination: str
    }
    
    class ForwardingInfo {
        <<dataclass>>
        +forwarding_interval: float
        +forwarding_url: str
        +forwarding_headers: Optional[dict]
    }
```

#### 5. Progress Tracking

```mermaid
classDiagram
    class ProgressCode {
        <<enumeration>>
        Completed = "Completed"
        Errored = "Errored"
        Failed = "Failed"
        NotStarted = "NotStarted"
        Paused = "Paused"
        Running = "Running"
    }
    
    class ProgressType {
        <<enumeration>>
        NumericRange = "NumericRange"
        Sequential = "Sequential"
        TimeSpan = "TimeSpan"
    }
    
    class ProgressInfo {
        <<dataclass>>
        +id: str
        +category: str
        +moniker: str
        +ptype: ProgressType
        +range_min: str
        +range_max: str
        +position: str
        +status: ProgressCode
        +when: datetime
        +data: Optional[dict]
        <<methods>>
        +as_dict() dict
        +from_dict(data) ProgressInfo
    }
```

#### 6. Progress Concentrator Service

```mermaid
classDiagram
    class ProgressConcentratorServer {
        -_recorder: ResultRecorder
        -_forwarding_info: ForwardingInfo
        -_forward_thread: Thread
        -_forwarding_running: bool
        -_server_thread: Thread
        -_server_running: bool
        -_logger: EnhancedLogger
        <<methods>>
        +start()
        +update_task_progress(progress)
        -_forwarding_thread_entry(start_gate)
        -_service_thread_entry(start_gate)
    }
    
    class ProgressCallbackHandler {
        <<methods>>
        +do_POST()
    }
    
    HTTPServer <|-- ProgressConcentratorServer
    SimpleHTTPRequestHandler <|-- ProgressCallbackHandler
```

### Data Flow

#### Result Recording Flow

```mermaid
sequenceDiagram
    participant TS as TestSequencer
    participant STS as TestScope
    participant RR as ResultRecorder
    participant RN as ResultNode
    participant SF as Stream File
    participant SUM as Summary File
    
    TS->>RR: __enter__()
    RR->>RR: initialize_report()
    RR->>SUM: update_summary()
    RR->>SF: Open stream file
    
    loop For each test
        STS->>RN: Create TestResult
        STS->>RR: preview(result)
        RR->>SF: Write preview record
        
        Note over STS: Execute test
        
        alt Test Passed
            STS->>RN: mark_passed()
        else Test Failed
            STS->>RN: add_failure(tb_detail)
        else Test Errored
            STS->>RN: add_error(tb_detail)
        else Test Skipped
            STS->>RN: mark_skip(reason, bug)
        end
        
        STS->>RN: finalize()
        STS->>RR: record(result)
        RR->>RR: Update counts
        RR->>SF: Write final record
        RR->>RR: catalog_output_directory()
    end
    
    TS->>RR: __exit__()
    RR->>RR: finalize()
    RR->>SUM: update_summary()
    RR->>SF: Close stream file
```

#### Result Consolidation Flow

```mermaid
flowchart TD
    A[consolidate_results] --> B[load_result_stream]
    B --> C[Parse stream records]
    
    C --> D{Record Type?}
    
    D -->|JOB| E[Set as root_node]
    E --> F[Initialize items list]
    
    D -->|TEST_CONTAINER| G[Find parent in lookup]
    G --> H[Append to parent items]
    H --> I[Add to node_lookup]
    
    D -->|TEST| J[Find parent in lookup]
    J --> K[Append to parent items]
    K --> L[Initialize tasking_groups]
    L --> M[Add to node_lookup]
    
    D -->|TASKING_GROUP| N[Find parent in lookup]
    N --> O[Append to parent tasking_groups]
    O --> P[Initialize taskings]
    P --> Q[Add to node_lookup]
    
    D -->|TASKING| R[Find parent in lookup]
    R --> S[Append to parent taskings]
    S --> T[Add to node_lookup]
    
    F --> U{More records?}
    I --> U
    M --> U
    Q --> U
    T --> U
    
    U -->|Yes| C
    U -->|No| V[write_consolidated_results]
    V --> W[Output consolidated JSON]
```

#### Progress Forwarding Flow

```mermaid
sequenceDiagram
    participant RT as Remote Task
    participant PCH as ProgressCallbackHandler
    participant PCS as ProgressConcentratorServer
    participant RR as ResultRecorder
    participant FWD as Forwarding Thread
    participant EXT as External Service
    
    RT->>PCH: POST /progress
    PCH->>PCH: Parse JSON content
    PCH->>PCS: update_task_progress(progress)
    PCS->>RR: post_task_progress(progress)
    RR->>RR: Update running_tasks
    PCH-->>RT: 200 OK
    
    loop Every forwarding_interval
        FWD->>RR: Get summary
        RR-->>FWD: summary copy
        FWD->>EXT: POST summary
    end
```

### Result Tree Structure

```
JobContainer (root)
├── TestContainer (package.module1)
│   ├── TestResult (test_function_1)
│   │   ├── TaskingGroup (setup_group)
│   │   │   ├── TaskingResult (task_1)
│   │   │   └── TaskingResult (task_2)
│   │   └── TaskingGroup (teardown_group)
│   │       └── TaskingResult (cleanup_task)
│   └── TestResult (test_function_2)
├── TestContainer (package.module2)
│   └── TestResult (test_function_3)
└── ...
```

### Design Patterns

#### 1. Context Manager Pattern

The `ResultRecorder` implements the context manager protocol for lifecycle management:

```python
class ResultRecorder:
    def __enter__(self):
        self.initialize_report()
        self.update_summary()
        self._rout = open(self._render_info.stream_results_filename, 'w')
        return self

    def __exit__(self, ex_type, ex_inst, ex_tb):
        if not self._finalized:
            self.finalize()
        return
```

#### 2. Template Method Pattern

The `ResultRecorder` base class defines abstract methods that derived classes must implement:

```python
class ResultRecorder:
    def preview(self, result: ResultNode):
        raise AbstractMethodError("...")
    
    def record(self, result: ResultNode):
        raise AbstractMethodError("...")
    
    def update_summary(self):
        raise AbstractMethodError("...")
    
    def write_consolidated_results(self, root_node: dict):
        raise AbstractMethodError("...")
```

#### 3. Observer Pattern

The progress tracking system uses callbacks for progress updates:

```python
class TaskingProgressCallback(Protocol):
    def __call__(self, progress: List[ProgressInfo]) -> None: ...

@dataclass
class SummaryProgressDelivery:
    progress_interval: float
    progress_callback: TaskingProgressCallback
```

#### 4. Composite Pattern

The result tree uses a composite structure with containers and nodes:

- `ResultContainer` - composite nodes (JobContainer, TestContainer, TaskingGroup)
- `ResultNode` - leaf nodes with actual result data (TestResult, TaskingResult)

#### 5. Strategy Pattern

The `TaskingResultFormatter` protocol allows customizable result formatting:

```python
class TaskingResultFormatter(Protocol):
    def __call__(self, result: TaskingResult) -> List[str]: ...

def default_tasking_result_formatter(result: TaskingResult) -> List[str]:
    # Default formatting implementation
    ...
```

### Output File Structure

```
output_directory/
├── testsummary.html          # HTML summary page
├── testsummary.json          # JSON summary data
├── testresults_stream.jsos   # Streaming results (JSOS format)
├── testresults.json          # Consolidated results
├── catalog.json              # Directory catalog
├── static/                   # Static resources
│   ├── css/
│   ├── js/
│   └── images/
└── diagnostics/              # Diagnostic captures
    ├── pre-run/
    └── post-run/
```

## Integration Points

### With Test Execution Engine

The Result Recording system integrates with the execution engine through:

- `TestSequencer` creates result containers and nodes
- `SequencerTestScope` records test results via the recorder
- `TaskingGroup` records tasking results for distributed tasks

### With HTML Report Templates

The system provides data for HTML rendering:

- Summary JSON for dashboard display
- Consolidated results for detailed views
- Catalog files for directory navigation
- Static resources for styling and interactivity

### With Progress Concentrators

The system supports distributed execution through:

- `ProgressConcentratorServer` receives progress callbacks
- `ForwardingInfo` configures external progress forwarding
- Real-time summary updates for monitoring

## Configuration

### ResultRecorder Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `runid` | `str` | Unique identifier for the test run |
| `start` | `datetime` | Start time of the test run |
| `render_info` | `RenderInfo` | Output file paths and templates |
| `apod` | `Optional[str]` | Automation pod identifier |
| `build_info` | `Optional[BuildInfo]` | Build metadata |
| `pipeline_info` | `Optional[PipelineInfo]` | Pipeline metadata |
| `job_info` | `Optional[JobInfo]` | Job metadata |
| `forwarding_info` | `Optional[ForwardingInfo]` | Progress forwarding config |

### RenderInfo Configuration

| Field | Description |
|-------|-------------|
| `title` | Title for the test run summary |
| `summary_filename` | Path to summary JSON file |
| `summary_template` | Path to HTML template |
| `stream_results_filename` | Path to streaming results file |
| `consolidated_results_filename` | Path to consolidated results |
| `static_resource_source` | Source directory for static files |
| `static_resource_destination` | Destination for static files |

## Error Handling

### Result Code Determination

```python
def finalize(self):
    if len(self._failures) > 0:
        self._result_code = ResultCode.FAILED
    elif len(self._errors) > 0:
        self._result_code = ResultCode.ERRORED
    elif self._result_code == ResultCode.UNSET or self._result_code == ResultCode.PASSED:
        self._result_code = ResultCode.PASSED
    else:
        self._result_code = ResultCode.UNKNOWN
```

### Tasking Result Verification

The `verify_tasking_results` function validates tasking outcomes:

| Condition | Exception Type |
|-----------|----------------|
| Unknown result codes | `TaskingGroupRuntimeError` |
| Cancelled taskings | `TaskingGroupRuntimeError` |
| Errored taskings | `TaskingGroupRuntimeError` |
| Failed taskings | `TaskingGroupAssertionError` |

### Thread Safety

The `ResultRecorder` uses a lock for thread-safe operations:

```python
self._lock.acquire()
try:
    # Update shared state
    self._running_tasks[progress.id] = progress.as_dict()
finally:
    self._lock.release()
```

## Testing Strategy

### Unit Testing Focus Areas

1. **ResultRecorder**
   - Context manager lifecycle
   - Result counting accuracy
   - Summary generation
   - Thread safety

2. **Result Data Model**
   - Serialization/deserialization
   - Result code finalization
   - Error/failure tracking

3. **Progress Tracking**
   - Progress info serialization
   - Concentrator server operation
   - Forwarding thread behavior

4. **Utilities**
   - Catalog tree generation
   - Directory traversal

### Test Categories

| Category | Components | Focus |
|----------|------------|-------|
| Lifecycle | ResultRecorder | Context manager, finalization |
| Serialization | ResultNode, ResultContainer | JSON output, as_dict |
| Counting | ResultRecorder | Pass/fail/error/skip counts |
| Progress | ProgressInfo, Concentrator | Real-time tracking |
| Threading | ResultRecorder, Concentrator | Thread safety |

### Integration Testing

1. **End-to-End Recording**
   - Complete test run with result recording
   - File output validation
   - Consolidation correctness

2. **Progress Forwarding**
   - Remote task progress reception
   - Summary forwarding to external services

3. **HTML Report Generation**
   - Catalog file generation
   - Static resource deployment
