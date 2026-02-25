# Result Concentrators - Design Document

## Overview

The Result Concentrators system provides infrastructure for aggregating test execution progress and results from distributed test execution environments. It enables:

- Real-time progress collection from remote test workers via HTTP callbacks
- Centralized progress tracking and status aggregation
- Periodic forwarding of aggregated summaries to external monitoring services
- Thread-safe concurrent progress updates from multiple sources

The system operates as a service layer that sits between distributed test workers and the central `ResultRecorder`, providing a unified view of test execution progress across multiple processes or machines.

## Architecture

### High-Level Component Diagram

```mermaid
graph TB
    subgraph "Remote Workers"
        W1[Worker 1]
        W2[Worker 2]
        W3[Worker N]
    end
    
    subgraph "Concentrator Service"
        PCH[ProgressCallbackHandler]
        PCS[ProgressConcentratorServer]
        FT[Forwarding Thread]
    end
    
    subgraph "Recording Layer"
        RR[ResultRecorder]
        RT[Running Tasks Dict]
        SUM[Summary]
    end
    
    subgraph "External Services"
        EXT[External Monitoring]
        DASH[Dashboard Service]
    end
    
    W1 -->|POST /progress| PCH
    W2 -->|POST /progress| PCH
    W3 -->|POST /progress| PCH
    
    PCH --> PCS
    PCS --> RR
    RR --> RT
    RR --> SUM
    
    FT -->|Periodic| RR
    FT -->|POST summary| EXT
    FT -->|POST summary| DASH
```

### Components

#### 1. ProgressConcentratorServer

The `ProgressConcentratorServer` is a threaded HTTP server that receives progress callbacks from remote test workers and aggregates them into the central `ResultRecorder`.

```mermaid
classDiagram
    class ProgressConcentratorServer {
        <<instance attributes>>
        -_recorder: ResultRecorder
        -_forwarding_info: Optional[ForwardingInfo]
        -_forward_thread: Optional[Thread]
        -_forwarding_running: bool
        -_server_thread: Optional[Thread]
        -_server_running: bool
        -_logger: EnhancedLogger
        <<methods>>
        +__init__(recorder, server_address, forwarding_info, bind_and_activate)
        +start()
        +update_task_progress(progress: ProgressInfo)
        -_forwarding_thread_entry(start_gate: Event)
        -_service_thread_entry(start_gate: Event)
    }
    
    class ThreadingMixIn {
        <<mixin>>
    }
    
    class HTTPServer {
        <<base>>
    }
    
    ThreadingMixIn <|-- ProgressConcentratorServer
    HTTPServer <|-- ProgressConcentratorServer
```

**Key Responsibilities:**

| Responsibility | Description |
|----------------|-------------|
| HTTP Server | Accepts incoming progress POST requests from workers |
| Progress Aggregation | Routes progress updates to the ResultRecorder |
| Summary Forwarding | Periodically forwards aggregated summaries to external services |
| Thread Management | Manages server and forwarding threads with proper lifecycle |
| Concurrent Handling | Uses ThreadingMixIn for concurrent request processing |

#### 2. ProgressCallbackHandler

The `ProgressCallbackHandler` processes incoming HTTP POST requests containing progress information from remote workers.

```mermaid
classDiagram
    class ProgressCallbackHandler {
        <<methods>>
        +do_POST()
    }
    
    class SimpleHTTPRequestHandler {
        <<base>>
    }
    
    SimpleHTTPRequestHandler <|-- ProgressCallbackHandler
```

**Request Processing Flow:**

```mermaid
flowchart TD
    A[Receive POST Request] --> B{Has Content-Length?}
    B -->|No| C[Send 200 OK]
    B -->|Yes| D[Read Content]
    D --> E[Parse JSON]
    E --> F{Parse Success?}
    F -->|No| G[Send 500 Error]
    F -->|Yes| H[Create ProgressInfo]
    H --> I[Update Task Progress]
    I --> J[Send 200 OK]
```

#### 3. Progress Data Model

```mermaid
classDiagram
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
        +from_dict(data: dict) ProgressInfo
        +__repr__() str
    }
    
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
    
    ProgressInfo --> ProgressCode
    ProgressInfo --> ProgressType
```

#### 4. Forwarding Configuration

```mermaid
classDiagram
    class ForwardingInfo {
        <<dataclass>>
        +forwarding_interval: float
        +forwarding_url: str
        +forwarding_headers: Optional[dict]
    }
    
    class SummaryProgressDelivery {
        <<dataclass>>
        +progress_interval: float
        +progress_callback: TaskingProgressCallback
    }
    
    class TaskingProgressCallback {
        <<protocol>>
        +__call__(progress: List[ProgressInfo]) None
    }
    
    SummaryProgressDelivery --> TaskingProgressCallback
```

### Data Flow

#### Progress Collection Flow

```mermaid
sequenceDiagram
    participant W as Remote Worker
    participant PCH as ProgressCallbackHandler
    participant PCS as ProgressConcentratorServer
    participant RR as ResultRecorder
    participant RT as Running Tasks
    
    W->>PCH: POST /progress (JSON)
    PCH->>PCH: Parse content-length
    PCH->>PCH: Read request body
    PCH->>PCH: json.loads(content)
    PCH->>PCH: ProgressInfo.from_dict(data)
    PCH->>PCS: update_task_progress(progress)
    PCS->>RR: post_task_progress(progress)
    
    RR->>RR: Acquire lock
    alt Progress Completed
        RR->>RT: Delete task entry
    else Progress Running
        RR->>RT: Update task entry
    end
    RR->>RR: Release lock
    
    PCH-->>W: 200 OK
```

#### Summary Forwarding Flow

```mermaid
sequenceDiagram
    participant FT as Forwarding Thread
    participant RR as ResultRecorder
    participant EXT as External Service
    
    loop Every forwarding_interval
        FT->>RR: Get summary (thread-safe copy)
        RR-->>FT: summary dict
        FT->>EXT: POST summary (JSON)
        EXT-->>FT: Response
        FT->>FT: Sleep(forwarding_interval)
    end
```

#### Server Startup Flow

```mermaid
sequenceDiagram
    participant C as Caller
    participant PCS as ProgressConcentratorServer
    participant FT as Forwarding Thread
    participant ST as Server Thread
    
    C->>PCS: start()
    
    alt Has ForwardingInfo
        PCS->>PCS: Create forwarding gate
        PCS->>FT: Start thread
        FT->>FT: Set gate
        PCS->>PCS: Wait for gate
    end
    
    PCS->>PCS: Create server gate
    PCS->>ST: Start thread
    ST->>ST: Set gate
    PCS->>PCS: Wait for gate
    
    Note over ST: serve_forever()
    
    PCS-->>C: Return (server running)
```

### Thread Architecture

```mermaid
graph TB
    subgraph "Main Thread"
        MT[Application Code]
    end
    
    subgraph "Server Thread"
        ST[Service Thread Entry]
        SF[serve_forever]
    end
    
    subgraph "Request Threads"
        RT1[Request Handler 1]
        RT2[Request Handler 2]
        RTN[Request Handler N]
    end
    
    subgraph "Forwarding Thread"
        FT[Forwarding Thread Entry]
        FL[Forwarding Loop]
    end
    
    MT -->|start| ST
    ST --> SF
    SF -->|spawn| RT1
    SF -->|spawn| RT2
    SF -->|spawn| RTN
    
    MT -->|start| FT
    FT --> FL
    
    RT1 -->|update| RR[ResultRecorder]
    RT2 -->|update| RR
    RTN -->|update| RR
    FL -->|read| RR
```

### Design Patterns

#### 1. Mixin Pattern

The `ProgressConcentratorServer` uses Python's `ThreadingMixIn` to enable concurrent request handling:

```python
class ProgressConcentratorServer(ThreadingMixIn, HTTPServer):
    """
    Combines threading capability with HTTP server functionality.
    Each incoming request is handled in a separate thread.
    """
```

#### 2. Observer Pattern

The progress forwarding system implements an observer-like pattern where the forwarding thread periodically observes the recorder's summary state:

```python
class TaskingProgressCallback(Protocol):
    def __call__(self, progress: List[ProgressInfo]) -> None: ...

@dataclass
class SummaryProgressDelivery:
    progress_interval: float
    progress_callback: TaskingProgressCallback
```

#### 3. Gate Pattern

Thread synchronization uses gate events to ensure proper startup sequencing:

```python
def start(self):
    svr_gate = threading.Event()
    svr_gate.clear()
    
    self._server_thread = threading.Thread(
        target=self._service_thread_entry,
        args=(svr_gate,),
        daemon=True
    )
    self._server_thread.start()
    
    svr_gate.wait()  # Wait for thread to signal ready
```

#### 4. Thread-Safe State Pattern

The `ResultRecorder` uses lock-based synchronization for thread-safe state updates:

```python
def post_task_progress(self, progress_list: List[ProgressInfo]):
    self._lock.acquire()
    try:
        for progress in progress_list:
            if progress.status == ProgressCode.Completed:
                del self._running_tasks[progress.id]
            else:
                self._running_tasks[progress.id] = progress.as_dict()
    finally:
        self._lock.release()
```

### Progress State Machine

```mermaid
stateDiagram-v2
    [*] --> NotStarted
    NotStarted --> Running: Task begins
    Running --> Paused: Task paused
    Paused --> Running: Task resumed
    Running --> Completed: Task succeeds
    Running --> Failed: Assertion failure
    Running --> Errored: Exception raised
    Completed --> [*]
    Failed --> [*]
    Errored --> [*]
```

### Progress Types

| Type | Description | Use Case |
|------|-------------|----------|
| `NumericRange` | Progress within a numeric range (min to max) | Batch processing with known count |
| `Sequential` | Sequential step progress | Multi-step operations |
| `TimeSpan` | Time-based progress | Duration-based tasks |

## Integration Points

### With ResultRecorder

The concentrator integrates with `ResultRecorder` through:

- `post_task_progress()` - Updates running task state
- `clear_task_progress()` - Removes completed tasks
- `summary` property - Provides thread-safe summary access

```mermaid
classDiagram
    class ResultRecorder {
        -_running_tasks: dict
        -_lock: threading.Lock
        +post_task_progress(progress_list)
        +clear_task_progress(task_ids)
        +summary: dict
    }
    
    class ProgressConcentratorServer {
        -_recorder: ResultRecorder
        +update_task_progress(progress)
    }
    
    ProgressConcentratorServer --> ResultRecorder
```

### With Remote Workers

Workers communicate via HTTP POST with JSON payloads:

```json
{
    "id": "task-uuid-123",
    "category": "test-execution",
    "moniker": "test_module.test_function",
    "ptype": "Sequential",
    "range_min": "0",
    "range_max": "10",
    "position": "5",
    "status": "Running",
    "when": "2025-02-20T10:30:00.000000",
    "data": {
        "worker_id": "worker-1",
        "additional_info": "..."
    }
}
```

### With External Monitoring Services

The forwarding thread sends periodic summary updates:

```python
headers = {
    "Content-Type": "application/json"
}
if forwarding_headers is not None:
    headers.update(forwarding_headers)

requests.post(forwarding_url, json=summary, headers=headers)
```

## Configuration

### Server Configuration

| Parameter | Type | Description |
|-----------|------|-------------|
| `recorder` | `ResultRecorder` | The recorder to aggregate progress into |
| `server_address` | `tuple` | (host, port) for the HTTP server |
| `forwarding_info` | `Optional[ForwardingInfo]` | Configuration for summary forwarding |
| `bind_and_activate` | `bool` | Whether to bind and activate immediately |

### ForwardingInfo Configuration

| Field | Type | Description |
|-------|------|-------------|
| `forwarding_interval` | `float` | Seconds between summary forwards |
| `forwarding_url` | `str` | URL to POST summaries to |
| `forwarding_headers` | `Optional[dict]` | Additional HTTP headers |

### Example Configuration

```python
from automojo.testbase.results.model.forwardinginfo import ForwardingInfo
from automojo.testbase.results.concentrators.progressconcentratorservice import (
    ProgressConcentratorServer
)

# Configure forwarding
forwarding_info = ForwardingInfo(
    forwarding_interval=5.0,  # Forward every 5 seconds
    forwarding_url="https://monitoring.example.com/api/progress",
    forwarding_headers={
        "Authorization": "Bearer token123",
        "X-Job-Id": "job-456"
    }
)

# Create and start concentrator
server = ProgressConcentratorServer(
    recorder=result_recorder,
    server_address=("0.0.0.0", 8080),
    forwarding_info=forwarding_info
)
server.start()
```

## Error Handling

### Request Processing Errors

```mermaid
flowchart TD
    A[Process Request] --> B{Parse JSON?}
    B -->|Success| C{Create ProgressInfo?}
    B -->|Failure| D[Log Error]
    C -->|Success| E{Update Progress?}
    C -->|Failure| D
    E -->|Success| F[Return 200]
    E -->|Failure| D
    D --> G[Return 500 with Error Message]
```

### Error Response Format

```python
def do_POST(self):
    errmsg = None
    
    try:
        # Process request
        ...
    except Exception as perr:
        errmsg_msg_lines = [
            "Error processing progress postback.",
            "EXCEPTION:",
            traceback.format_exc()
        ]
        errmsg = os.linesep.join(errmsg_msg_lines)
    
    if not errmsg:
        self.send_response(200, message=None)
    else:
        self.send_response(500, message=errmsg)
```

### Forwarding Thread Error Handling

The forwarding thread catches and logs exceptions without crashing:

```python
def _forwarding_thread_entry(self, start_gate: threading.Event):
    while self._forwarding_running:
        try:
            summary = self._recorder.summary
            requests.post(forwarding_url, json=summary, headers=headers)
            time.sleep(forwarding_interval)
        except Exception:
            errmsg = traceback.format_exc()
            self._logger.error(errmsg)
```

## Testing Strategy

### Unit Testing Focus Areas

1. **ProgressConcentratorServer**
   - Server startup and shutdown
   - Thread lifecycle management
   - Gate synchronization

2. **ProgressCallbackHandler**
   - JSON parsing
   - ProgressInfo creation
   - Error response generation

3. **Progress Data Model**
   - Serialization/deserialization
   - Status transitions
   - Progress type handling

4. **Integration with ResultRecorder**
   - Thread-safe progress updates
   - Running task management
   - Summary generation

### Test Categories

| Category | Components | Focus |
|----------|------------|-------|
| Lifecycle | ProgressConcentratorServer | Start/stop, thread management |
| HTTP | ProgressCallbackHandler | Request parsing, responses |
| Serialization | ProgressInfo | JSON round-trip |
| Threading | All | Concurrent access, locks |
| Integration | Server + Recorder | End-to-end progress flow |

### Integration Testing

1. **Multi-Worker Simulation**
   - Multiple concurrent progress updates
   - Progress aggregation accuracy
   - Thread safety under load

2. **Forwarding Verification**
   - Summary forwarding timing
   - External service integration
   - Header propagation

3. **Error Recovery**
   - Malformed request handling
   - Network failure resilience
   - Thread crash recovery

## Performance Considerations

### Scalability

- ThreadingMixIn enables concurrent request handling
- Lock contention minimized through short critical sections
- Daemon threads prevent blocking on shutdown

### Resource Management

- Threads are created as daemons for clean shutdown
- HTTP connections are short-lived
- Summary copies prevent lock holding during forwarding

### Bottlenecks

| Potential Bottleneck | Mitigation |
|---------------------|------------|
| Lock contention | Short critical sections, copy-on-read |
| Thread creation | ThreadingMixIn reuses thread pool |
| Network I/O | Async forwarding in separate thread |
| JSON parsing | Efficient stdlib json module |
