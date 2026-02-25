# Debugging Support - Requirements Document

## Introduction

The Debugging Support system provides infrastructure for interactive debugging of test execution within the TestBase framework. It enables developers to pause test execution at well-known breakpoints using either the built-in Python debugger (pdb) or the remote debugging protocol (debugpy) for IDE integration. The system supports predefined pause points at key stages of test execution, multiple debugger backends, code generation integration for automatic insertion of breakpoint code into generated test sequence documents, and a remote debugging assistant for on-demand remote debugging connections. This debugging capability is essential for troubleshooting test failures, stepping through test execution, and integrating with modern IDEs like VS Code.

## Glossary

- **WELLKNOWN_BREAKPOINTS**: An enumeration class defining predefined breakpoint locations within the test execution lifecycle
- **DEBUGGER**: An enumeration class identifying supported debugger backends (pdb and debugpy)
- **Test_Discovery_Breakpoint**: A breakpoint that pauses execution during the test discovery phase, identified by the value "test-discovery"
- **Testrun_Start_Breakpoint**: A breakpoint that pauses execution at the start of test execution, identified by the value "testrun-start"
- **PDB**: The built-in Python debugger used for local terminal debugging
- **Debugpy**: The remote debugging protocol library used for IDE integration and remote debugging
- **DebugPyAssistant**: A background daemon thread class that exposes a debugpy endpoint for on-demand remote debugging
- **Breakpoint_Entry_Function**: The `debugger_wellknown_breakpoint_entry` function that triggers breakpoints at runtime
- **Breakpoint_Code_Generation_Function**: The `debugger_wellknown_breakpoint_code_append` function that generates breakpoint source code
- **VS_Code_Detection_Function**: The `in_vscode_debugger` function that detects whether the process is running under VS Code's debugger
- **DiagnosticOptionGroup**: A CLI option group providing command-line options for controlling debugger and breakpoint behavior
- **TestSequencer**: The component that integrates breakpoint code generation into test sequence documents
- **Test_Sequence_Document**: The generated Python file containing the test execution sequence with optional breakpoint code
- **Default_Debug_Port**: The standard debugpy listen port (5678)
- **Assistant_Debug_Port**: The dedicated port for DebugPyAssistant (5679)

## Requirements

### Requirement 1: Well-Known Breakpoints Enumeration

**User Story:** As a framework developer, I want well-defined constants for breakpoint locations, so that breakpoint pause points are consistently identified across the framework.

#### Acceptance Criteria

1. THE WELLKNOWN_BREAKPOINTS class SHALL be an enumeration inheriting from both str and Enum
2. THE WELLKNOWN_BREAKPOINTS class SHALL define a TEST_DISCOVERY member with the string value "test-discovery"
3. THE WELLKNOWN_BREAKPOINTS class SHALL define a TESTRUN_START member with the string value "testrun-start"
4. THE enumeration members SHALL be accessible as class attributes without instantiation
5. THE enumeration members SHALL be comparable to string values due to str inheritance

### Requirement 2: Debugger Backend Enumeration

**User Story:** As a framework developer, I want well-defined constants for debugger backends, so that debugger selection is consistent across the framework.

#### Acceptance Criteria

1. THE DEBUGGER class SHALL be an enumeration inheriting from both str and Enum
2. THE DEBUGGER class SHALL define a PDB member with the string value "pdb"
3. THE DEBUGGER class SHALL define a DEBUGPY member with the string value "debugpy"
4. THE enumeration members SHALL be accessible as class attributes without instantiation
5. THE enumeration members SHALL be comparable to string values due to str inheritance

### Requirement 3: CLI Debugging Options

**User Story:** As a test developer, I want command-line options to enable debugging, so that I can control debugger and breakpoint behavior when running tests.

#### Acceptance Criteria

1. THE DiagnosticOptionGroup SHALL provide a `--debugger` option with choices 'pdb' or 'debugpy' for debugger selection
2. THE DiagnosticOptionGroup SHALL provide a `--breakpoint` option for specifying breakpoints to activate
3. THE `--breakpoint` option SHALL support multiple values to enable multiple breakpoints
4. THE `--breakpoint` option SHALL accept choices 'test-discovery' and 'testrun-start'
5. WHEN `--debugger` is specified, THE System SHALL set the AM_DEBUG_DEBUGGER runtime variable
6. WHEN `--breakpoint` is specified, THE System SHALL set the AM_DEBUG_BREAKPOINTS runtime variable

### Requirement 4: VS Code Debugger Detection

**User Story:** As a framework developer, I want to detect when running under VS Code's debugger, so that the system can adjust its behavior accordingly.

#### Acceptance Criteria

1. THE VS_Code_Detection_Function SHALL provide an `in_vscode_debugger` function returning a boolean
2. THE function SHALL iterate through the current stack frames to detect VS Code debugging
3. WHEN a stack frame filename ends with "pydevd.py", THE function SHALL return True
4. WHEN no stack frame filename ends with "pydevd.py", THE function SHALL return False
5. THE function SHALL not require any parameters

### Requirement 5: Runtime Breakpoint Entry

**User Story:** As a framework developer, I want a function to trigger breakpoints at runtime, so that test execution can pause at well-known breakpoints when enabled.

#### Acceptance Criteria

1. THE Breakpoint_Entry_Function SHALL provide a `debugger_wellknown_breakpoint_entry` function
2. THE function SHALL accept a `debugger` parameter specifying the debugger backend to use
3. THE function SHALL accept a `breakpoint_name` parameter identifying the well-known breakpoint
4. THE function SHALL accept a `configured_breakpoints` parameter containing the list of enabled breakpoints
5. WHEN breakpoint_name is not in configured_breakpoints, THE function SHALL return immediately without action
6. WHEN breakpoint_name is in configured_breakpoints AND debugger is 'pdb', THE function SHALL invoke pdb.set_trace()
7. WHEN breakpoint_name is in configured_breakpoints AND debugger is 'debugpy', THE function SHALL invoke debugpy.breakpoint()

### Requirement 6: Debugpy Remote Debugging Setup

**User Story:** As a test developer, I want debugpy to set up remote debugging connections, so that I can attach my IDE to debug test execution.

#### Acceptance Criteria

1. WHEN debugger is 'debugpy' AND running under VS Code debugger, THE Breakpoint_Entry_Function SHALL call debugpy.listen() before breakpoint
2. WHEN debugger is 'debugpy' AND running under VS Code debugger, THE Breakpoint_Entry_Function SHALL call debugpy.wait_for_client() before breakpoint
3. THE debugpy.listen() call SHALL use the address ("0.0.0.0", 5678) to accept connections from any interface
4. THE function SHALL log an informational message indicating it is waiting for a debugger connection
5. WHEN debugger is 'debugpy' AND not running under VS Code debugger, THE function SHALL skip listen and wait_for_client calls

### Requirement 7: Breakpoint Code Generation

**User Story:** As a framework developer, I want a function to generate breakpoint source code, so that breakpoint code can be inserted into generated test sequence documents.

#### Acceptance Criteria

1. THE Breakpoint_Code_Generation_Function SHALL provide a `debugger_wellknown_breakpoint_code_append` function
2. THE function SHALL accept a `debugger` parameter specifying the debugger backend
3. THE function SHALL accept a `breakpoint_name` parameter identifying the well-known breakpoint
4. THE function SHALL accept a `code_lines` parameter as a list to append generated code lines
5. THE function SHALL accept a `current_indent` parameter specifying the indentation prefix
6. THE function SHALL accept a `configured_breakpoints` parameter containing the list of enabled breakpoints
7. WHEN breakpoint_name is not in configured_breakpoints, THE function SHALL not append any code lines

### Requirement 8: PDB Code Generation

**User Story:** As a test developer, I want pdb breakpoint code generated in test sequence documents, so that I can debug tests using the terminal debugger.

#### Acceptance Criteria

1. WHEN debugger is 'pdb' AND breakpoint is enabled, THE function SHALL append a blank line for readability
2. WHEN debugger is 'pdb' AND breakpoint is enabled, THE function SHALL append a comment explaining the breakpoint
3. WHEN debugger is 'pdb' AND breakpoint is enabled, THE function SHALL append an import statement for pdb
4. WHEN debugger is 'pdb' AND breakpoint is enabled, THE function SHALL append a pdb.set_trace() call
5. THE generated code lines SHALL use the provided current_indent for proper indentation

### Requirement 9: Debugpy Code Generation

**User Story:** As a test developer, I want debugpy breakpoint code generated in test sequence documents, so that I can debug tests using remote debugging.

#### Acceptance Criteria

1. WHEN debugger is 'debugpy' AND breakpoint is enabled, THE function SHALL append a blank line for readability
2. WHEN debugger is 'debugpy' AND breakpoint is enabled, THE function SHALL append a comment explaining the breakpoint
3. WHEN debugger is 'debugpy' AND breakpoint is enabled, THE function SHALL append an import statement for debugpy
4. WHEN debugger is 'debugpy' AND running under VS Code debugger, THE function SHALL append debugpy.listen() call
5. WHEN debugger is 'debugpy' AND running under VS Code debugger, THE function SHALL append debugpy.wait_for_client() call
6. WHEN debugger is 'debugpy' AND breakpoint is enabled, THE function SHALL append debugpy.breakpoint() call
7. THE generated code lines SHALL use the provided current_indent for proper indentation

### Requirement 10: DebugPyAssistant Background Thread

**User Story:** As a framework developer, I want a background debug endpoint, so that remote debugging can be connected on-demand without blocking test execution.

#### Acceptance Criteria

1. THE DebugPyAssistant class SHALL create a daemon thread on initialization
2. THE daemon thread SHALL expose a debugpy endpoint for remote debugging connections
3. THE DebugPyAssistant SHALL accept a `name` parameter for the thread name with default "DebugPyAssistant"
4. THE DebugPyAssistant SHALL accept an `endpoint` parameter as a (host, port) tuple
5. THE default endpoint SHALL be ("0.0.0.0", 5679) to avoid conflicts with direct debugging sessions
6. THE daemon thread SHALL terminate automatically when the main program exits

### Requirement 11: DebugPyAssistant Connection Handling

**User Story:** As a test developer, I want the debug assistant to handle multiple debug connections, so that I can connect and disconnect as needed during test execution.

#### Acceptance Criteria

1. THE DebugPyAssistant thread SHALL call debugpy.listen() with the configured endpoint on startup
2. THE DebugPyAssistant thread SHALL loop waiting for client connections using debugpy.wait_for_client()
3. WHEN a client connects, THE thread SHALL trigger a breakpoint using debugpy.breakpoint()
4. WHILE a client is connected, THE thread SHALL poll debugpy.is_client_connected() periodically
5. WHEN a client disconnects, THE thread SHALL return to waiting for new client connections
6. THE polling interval SHALL be 2 seconds between connection status checks

### Requirement 12: DebugPyAssistant Properties

**User Story:** As a framework developer, I want to access debug assistant properties, so that I can inspect the endpoint and thread state.

#### Acceptance Criteria

1. THE DebugPyAssistant SHALL provide an `endpoint` property returning the configured (host, port) tuple
2. THE DebugPyAssistant SHALL provide a `thread` property returning the background Thread object
3. THE properties SHALL be read-only

### Requirement 13: Test Sequencer Breakpoint Integration

**User Story:** As a framework developer, I want the TestSequencer to integrate breakpoint code, so that breakpoints are automatically inserted into generated test sequence documents.

#### Acceptance Criteria

1. THE TestSequencer SHALL read the AM_DEBUG_DEBUGGER runtime variable for debugger selection
2. THE TestSequencer SHALL read the AM_DEBUG_BREAKPOINTS runtime variable for enabled breakpoints
3. WHEN debugger and breakpoints are configured, THE TestSequencer SHALL call debugger_wellknown_breakpoint_code_append
4. THE TestSequencer SHALL insert TESTRUN_START breakpoint code at the beginning of the session() method
5. THE breakpoint code SHALL be inserted before the session scope context is entered

### Requirement 14: Network Configuration

**User Story:** As a test developer, I want consistent network configuration for debugging, so that I can reliably connect my IDE to debug sessions.

#### Acceptance Criteria

1. THE default debug port SHALL be 5678 for direct debugging sessions
2. THE DebugPyAssistant port SHALL be 5679 to avoid conflicts with direct debugging
3. THE listen address SHALL be "0.0.0.0" to accept connections from any network interface
4. THE port values SHALL be defined as module-level constants for consistency

### Requirement 15: Error Handling for Missing Debugger

**User Story:** As a test developer, I want clear errors when a debugger is not installed, so that I can install the required dependencies.

#### Acceptance Criteria

1. WHEN debugpy is selected but not installed, THE System SHALL raise an ImportError
2. WHEN pdb is selected, THE System SHALL not raise an ImportError as pdb is built-in
3. THE error message SHALL indicate which debugger module could not be imported

### Requirement 16: Blocking Behavior Documentation

**User Story:** As a test developer, I want to understand blocking behavior, so that I know when test execution will pause waiting for debugger connections.

#### Acceptance Criteria

1. WHEN debugpy.wait_for_client() is called, THE System SHALL block until a debugger client connects
2. THE System SHALL log an informational message before blocking to indicate it is waiting
3. THE log message SHALL include the port number for the debug connection
4. THE test execution SHALL not proceed until a debugger client attaches

### Requirement 17: VS Code Launch Configuration Support

**User Story:** As a test developer, I want to attach VS Code to debug sessions, so that I can use IDE debugging features during test execution.

#### Acceptance Criteria

1. THE System SHALL support VS Code debugpy attach configurations
2. THE attach configuration SHALL connect to localhost on the configured debug port
3. THE System SHALL support path mappings for source file resolution
4. THE System SHALL be compatible with standard VS Code debugpy extension configurations

