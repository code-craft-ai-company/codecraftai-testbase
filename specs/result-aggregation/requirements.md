# Result Concentrators - Requirements Document

## Introduction

The Result Concentrators system provides infrastructure for aggregating test execution progress and results from distributed test execution environments. It enables real-time progress collection from remote test workers via HTTP callbacks, centralized progress tracking and status aggregation, periodic forwarding of aggregated summaries to external monitoring services, and thread-safe concurrent progress updates from multiple sources. The system operates as a service layer that sits between distributed test workers and the central ResultRecorder, providing a unified view of test execution progress across multiple processes or machines.

## Glossary

- **ProgressConcentratorServer**: A threaded HTTP server that receives progress callbacks from remote test workers and aggregates them into the central ResultRecorder
- **ProgressCallbackHandler**: An HTTP request handler that processes incoming POST requests containing progress information from remote workers
- **ForwardingInfo**: A dataclass containing configuration for periodic summary forwarding (interval, URL, headers)
- **ProgressInfo**: A dataclass representing a single progress update event with status, position, and metadata
- **ProgressCode**: An enumeration of task progress states (Completed, Errored, Failed, NotStarted, Paused, Running)
- **ProgressType**: An enumeration of progress tracking modes (NumericRange, Sequential, TimeSpan)
- **ResultRecorder**: The central component that maintains running task state and provides thread-safe summary access
- **ThreadingMixIn**: A Python mixin class that enables concurrent request handling in the HTTP server
- **Gate_Pattern**: A thread synchronization pattern using Event objects to ensure proper startup sequencing
- **Running_Tasks**: A dictionary maintained by the ResultRecorder tracking active task progress by task ID
- **Summary**: A thread-safe dictionary containing aggregated test run status and progress information
- **Forwarding_Thread**: A daemon thread that periodically sends summary updates to external monitoring services

## Requirements

### Requirement 1: ProgressConcentratorServer Initialization

**User Story:** As a framework developer, I want to create a progress concentrator server with configurable parameters, so that I can aggregate progress from distributed workers.

#### Acceptance Criteria

1. THE ProgressConcentratorServer class SHALL accept a recorder parameter of type ResultRecorder in its constructor
2. THE ProgressConcentratorServer class SHALL accept a server_address parameter as a tuple of (host, port)
3. THE ProgressConcentratorServer class SHALL accept an optional forwarding_info parameter of type ForwardingInfo
4. THE ProgressConcentratorServer class SHALL accept an optional bind_and_activate parameter defaulting to True
5. THE ProgressConcentratorServer class SHALL inherit from ThreadingMixIn and HTTPServer
6. WHEN the server is initialized, THE System SHALL store the recorder reference for progress aggregation
7. WHEN the server is initialized, THE System SHALL initialize server_running and forwarding_running flags to False

### Requirement 2: ProgressConcentratorServer Startup

**User Story:** As a framework developer, I want to start the concentrator server with proper thread synchronization, so that the server is ready before returning from the start method.

#### Acceptance Criteria

1. THE ProgressConcentratorServer class SHALL provide a start method that initiates the server
2. WHEN start is called, THE System SHALL create and start a server thread as a daemon thread
3. WHEN start is called, THE System SHALL use a gate Event to synchronize startup completion
4. THE start method SHALL NOT return until the server thread signals readiness via the gate
5. WHEN forwarding_info is provided, THE System SHALL create and start a forwarding thread before the server thread
6. WHEN forwarding_info is provided, THE System SHALL use a separate gate Event for forwarding thread synchronization
7. THE start method SHALL NOT return until both threads (if applicable) signal readiness

### Requirement 3: ProgressConcentratorServer Thread Management

**User Story:** As a framework developer, I want the server to manage threads properly, so that resources are cleaned up on shutdown.

#### Acceptance Criteria

1. THE server thread SHALL be created with daemon=True for automatic cleanup on process exit
2. THE forwarding thread SHALL be created with daemon=True for automatic cleanup on process exit
3. THE server thread SHALL be named 'prog-concentrator' for identification
4. THE forwarding thread SHALL be named 'prog-forwarder' for identification
5. THE server thread SHALL call serve_forever to accept incoming connections
6. WHEN the server thread starts, THE System SHALL set server_running to True

### Requirement 4: Progress Update Handling

**User Story:** As a framework developer, I want the server to accept and process progress updates, so that worker progress is aggregated.

#### Acceptance Criteria

1. THE ProgressConcentratorServer class SHALL provide an update_task_progress method accepting a ProgressInfo object
2. WHEN update_task_progress is called, THE System SHALL delegate to the recorder's post_task_progress method
3. THE update_task_progress method SHALL be thread-safe for concurrent calls from multiple request handlers

### Requirement 5: ProgressCallbackHandler Request Processing

**User Story:** As a framework developer, I want an HTTP handler that processes progress POST requests, so that workers can submit progress updates.

#### Acceptance Criteria

1. THE ProgressCallbackHandler class SHALL inherit from SimpleHTTPRequestHandler
2. THE ProgressCallbackHandler class SHALL implement a do_POST method for handling POST requests
3. WHEN a POST request is received with content-length header, THE System SHALL read the request body
4. WHEN the request body is read, THE System SHALL parse it as JSON
5. WHEN JSON parsing succeeds, THE System SHALL create a ProgressInfo object using from_dict
6. WHEN ProgressInfo is created, THE System SHALL call update_task_progress on the server

### Requirement 6: ProgressCallbackHandler Response Handling

**User Story:** As a framework developer, I want the handler to return appropriate HTTP responses, so that workers know if their updates were processed.

#### Acceptance Criteria

1. WHEN progress processing succeeds, THE System SHALL send a 200 OK response
2. WHEN progress processing fails with an exception, THE System SHALL send a 500 error response
3. WHEN a 500 error is sent, THE System SHALL include the exception traceback in the response message
4. THE handler SHALL set Content-Type header to "text/html" for all responses
5. THE handler SHALL call end_headers after setting response headers

### Requirement 7: ProgressCallbackHandler Error Handling

**User Story:** As a framework developer, I want robust error handling in the callback handler, so that malformed requests don't crash the server.

#### Acceptance Criteria

1. WHEN JSON parsing fails, THE System SHALL catch the exception and generate an error message
2. WHEN ProgressInfo creation fails, THE System SHALL catch the exception and generate an error message
3. THE error message SHALL include "Error processing progress postback." as the first line
4. THE error message SHALL include "EXCEPTION:" followed by the traceback
5. WHEN no content-length header is present, THE System SHALL send a 200 OK response without processing

### Requirement 8: Summary Forwarding Configuration

**User Story:** As a framework developer, I want to configure summary forwarding to external services, so that progress can be monitored externally.

#### Acceptance Criteria

1. THE ForwardingInfo dataclass SHALL define a forwarding_interval field for the interval between forwards in seconds
2. THE ForwardingInfo dataclass SHALL define a forwarding_url field for the destination URL
3. THE ForwardingInfo dataclass SHALL define an optional forwarding_headers field for additional HTTP headers
4. WHEN forwarding_headers is None, THE System SHALL use only the default Content-Type header

### Requirement 9: Summary Forwarding Execution

**User Story:** As a framework developer, I want periodic summary forwarding, so that external services receive regular progress updates.

#### Acceptance Criteria

1. THE forwarding thread SHALL run a loop while forwarding_running is True
2. WITHIN each loop iteration, THE System SHALL retrieve the summary from the recorder
3. WITHIN each loop iteration, THE System SHALL POST the summary as JSON to the forwarding_url
4. WITHIN each loop iteration, THE System SHALL sleep for forwarding_interval seconds
5. THE forwarding request SHALL include Content-Type: application/json header
6. WHEN forwarding_headers is provided, THE System SHALL merge them with the default headers

### Requirement 10: Summary Forwarding Error Handling

**User Story:** As a framework developer, I want forwarding errors to be logged without crashing, so that the server continues operating.

#### Acceptance Criteria

1. WHEN a forwarding request fails with an exception, THE System SHALL catch the exception
2. WHEN a forwarding exception is caught, THE System SHALL log the error using the logger
3. WHEN a forwarding exception is caught, THE System SHALL continue the forwarding loop
4. THE forwarding thread SHALL NOT terminate due to network errors or HTTP failures

### Requirement 11: Concurrent Request Handling

**User Story:** As a framework developer, I want concurrent request handling, so that multiple workers can submit progress simultaneously.

#### Acceptance Criteria

1. THE ProgressConcentratorServer SHALL use ThreadingMixIn to enable concurrent request handling
2. WHEN multiple POST requests arrive simultaneously, THE System SHALL handle each in a separate thread
3. THE ResultRecorder's post_task_progress method SHALL be thread-safe for concurrent updates
4. THE ResultRecorder's summary property SHALL return a thread-safe copy of the summary

### Requirement 12: Progress Data Serialization

**User Story:** As a framework developer, I want progress data to serialize and deserialize correctly, so that workers can transmit progress as JSON.

#### Acceptance Criteria

1. THE ProgressInfo class SHALL provide an as_dict method for dictionary serialization
2. THE ProgressInfo class SHALL provide a from_dict class method for deserialization
3. THE as_dict method SHALL include id, category, moniker, ptype, range_min, range_max, position, status, when, and data fields
4. THE from_dict method SHALL reconstruct a ProgressInfo object from a dictionary
5. THE when field SHALL be serialized as an ISO format datetime string

### Requirement 13: Progress Status Tracking

**User Story:** As a framework developer, I want progress status to be tracked in the recorder, so that running task state is maintained.

#### Acceptance Criteria

1. WHEN a progress update with status Completed is received, THE System SHALL remove the task from running_tasks
2. WHEN a progress update with status Running is received, THE System SHALL update the task in running_tasks
3. WHEN a progress update with status Paused is received, THE System SHALL update the task in running_tasks
4. WHEN a progress update with status NotStarted is received, THE System SHALL update the task in running_tasks
5. WHEN a progress update with status Errored is received, THE System SHALL update the task in running_tasks
6. WHEN a progress update with status Failed is received, THE System SHALL update the task in running_tasks

### Requirement 14: Server Address Binding

**User Story:** As a framework developer, I want to specify the server address, so that I can control which interface and port the server listens on.

#### Acceptance Criteria

1. THE server_address parameter SHALL be a tuple of (host, port)
2. WHEN host is "0.0.0.0", THE System SHALL listen on all available interfaces
3. WHEN host is "127.0.0.1", THE System SHALL listen only on the loopback interface
4. THE port SHALL be an integer specifying the TCP port to listen on
5. WHEN bind_and_activate is True, THE System SHALL bind to the address immediately on construction

### Requirement 15: Logger Integration

**User Story:** As a framework developer, I want logging integration, so that server events and errors are recorded.

#### Acceptance Criteria

1. THE ProgressConcentratorServer SHALL initialize an EnhancedLogger instance
2. THE logger SHALL be used for logging forwarding errors
3. THE logger SHALL be obtained using getEnhancedLogger function

