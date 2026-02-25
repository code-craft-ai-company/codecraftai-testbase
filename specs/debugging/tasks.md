# Debugging Support - Tasks Document

## Overview

This document tracks the implementation status of the Debugging Support system and identifies enhancement opportunities for future development. The debugging system provides infrastructure for interactive debugging of test execution within the TestBase framework. It enables developers to pause test execution at well-known breakpoints using either the built-in Python debugger (pdb) or the remote debugging protocol (debugpy) for IDE integration.

## Implementation Status

### Completed Tasks

#### WELLKNOWN_BREAKPOINTS Enum (`breakpoints.py`)
- [x] Implement `WELLKNOWN_BREAKPOINTS` enumeration class
  - Inherit from both `str` and `Enum` for string comparison support
  - Define `TEST_DISCOVERY` member with value "test-discovery"
  - Define `TESTRUN_START` member with value "testrun-start"
  - Members accessible as class attributes without instantiation
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

#### DEBUGGER Enum (`automojo.xmodules.debugging`)
- [x] Implement `DEBUGGER` enumeration class
  - Inherit from both `str` and `Enum` for string comparison support
  - Define `PDB` member with value "pdb"
  - Define `DEBUGPY` member with value "debugpy"
  - Members accessible as class attributes without instantiation
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

#### DiagnosticOptionGroup CLI Options (`cli/options.py`)
- [x] Implement `--debugger` CLI option
  - Provide choice parameter with options 'pdb' or 'debugpy'
  - Default to None when not specified
  - _Requirements: 3.1_

- [x] Implement `--breakpoint` CLI option
  - Support multiple values for enabling multiple breakpoints
  - Provide choices 'test-discovery' and 'testrun-start'
  - Default to None when not specified
  - _Requirements: 3.2, 3.3, 3.4_

#### Runtime Variable Integration
- [x] Set AM_DEBUG_DEBUGGER runtime variable from CLI
  - Variable set when `--debugger` option is specified
  - _Requirements: 3.5_

- [x] Set AM_DEBUG_BREAKPOINTS runtime variable from CLI
  - Variable set when `--breakpoint` option is specified
  - _Requirements: 3.6_

#### VS Code Debugger Detection (`automojo.xmodules.debugging`)
- [x] Implement `in_vscode_debugger` function
  - Return boolean indicating VS Code debugger presence
  - Iterate through stack frames to detect pydevd.py
  - Return True when pydevd.py found in stack
  - Return False when pydevd.py not found
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

#### Runtime Breakpoint Entry Function (`automojo.xmodules.debugging`)
- [x] Implement `debugger_wellknown_breakpoint_entry` function
  - Accept `debugger` parameter for backend selection
  - Accept `breakpoint_name` parameter for breakpoint identification
  - Accept `configured_breakpoints` parameter for enabled breakpoints list
  - Return immediately when breakpoint not in configured list
  - Invoke pdb.set_trace() for pdb debugger
  - Invoke debugpy.breakpoint() for debugpy debugger
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

#### Debugpy Remote Debugging Setup (`automojo.xmodules.debugging`)
- [x] Implement debugpy listen and wait functionality
  - Call debugpy.listen() when running under VS Code debugger
  - Call debugpy.wait_for_client() before breakpoint
  - Use address ("0.0.0.0", 5678) for listen
  - Log informational message when waiting for connection
  - Skip listen/wait when not under VS Code debugger
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

#### Breakpoint Code Generation Function (`automojo.xmodules.debugging`)
- [x] Implement `debugger_wellknown_breakpoint_code_append` function
  - Accept `debugger` parameter for backend selection
  - Accept `breakpoint_name` parameter for breakpoint identification
  - Accept `code_lines` parameter as list for appending generated code
  - Accept `current_indent` parameter for indentation prefix
  - Accept `configured_breakpoints` parameter for enabled breakpoints list
  - Do not append code when breakpoint not in configured list
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

#### PDB Code Generation (`automojo.xmodules.debugging`)
- [x] Generate pdb breakpoint code
  - Append blank line for readability
  - Append comment explaining the breakpoint
  - Append import statement for pdb
  - Append pdb.set_trace() call
  - Use provided indentation for all lines
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

#### Debugpy Code Generation (`automojo.xmodules.debugging`)
- [x] Generate debugpy breakpoint code
  - Append blank line for readability
  - Append comment explaining the breakpoint
  - Append import statement for debugpy
  - Conditionally append debugpy.listen() call
  - Conditionally append debugpy.wait_for_client() call
  - Append debugpy.breakpoint() call
  - Use provided indentation for all lines
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

#### DebugPyAssistant Background Thread (`automojo.xmodules.debugging`)
- [x] Implement `DebugPyAssistant` class
  - Create daemon thread on initialization
  - Expose debugpy endpoint for remote debugging
  - Accept `name` parameter with default "DebugPyAssistant"
  - Accept `endpoint` parameter as (host, port) tuple
  - Use default endpoint ("0.0.0.0", 5679)
  - Daemon thread terminates with main program
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

#### DebugPyAssistant Connection Handling (`automojo.xmodules.debugging`)
- [x] Implement connection handling loop
  - Call debugpy.listen() on startup
  - Loop waiting for client connections
  - Trigger breakpoint on client connect
  - Poll is_client_connected() periodically
  - Return to waiting on client disconnect
  - Use 2 second polling interval
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

#### DebugPyAssistant Properties (`automojo.xmodules.debugging`)
- [x] Implement read-only properties
  - Provide `endpoint` property returning (host, port) tuple
  - Provide `thread` property returning Thread object
  - Properties are read-only
  - _Requirements: 12.1, 12.2, 12.3_

#### TestSequencer Breakpoint Integration (`sequencing/testsequencer.py`)
- [x] Integrate breakpoint code generation
  - Read AM_DEBUG_DEBUGGER runtime variable
  - Read AM_DEBUG_BREAKPOINTS runtime variable
  - Call debugger_wellknown_breakpoint_code_append when configured
  - Insert TESTRUN_START breakpoint at session() method start
  - Insert breakpoint before session scope context entry
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

#### TestJob Breakpoint Integration (`testjob.py`)
- [x] Integrate runtime breakpoint entry
  - Read AM_DEBUG_DEBUGGER runtime variable
  - Read AM_DEBUG_BREAKPOINTS runtime variable
  - Call debugger_wellknown_breakpoint_entry for TEST_DISCOVERY
  - Trigger breakpoint before test discovery begins
  - _Requirements: 13.1, 13.2_

#### Network Configuration
- [x] Define network constants
  - Default debug port is 5678
  - DebugPyAssistant port is 5679
  - Listen address is "0.0.0.0"
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

---

### In Progress

_No tasks currently in progress._

---

### Planned Tasks

#### Test Coverage
- [x] Add unit tests for `WELLKNOWN_BREAKPOINTS` enum
  - Verify TEST_DISCOVERY value is "test-discovery"
  - Verify TESTRUN_START value is "testrun-start"
  - Verify enum inherits from str and Enum
  - Verify string comparison works correctly
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] Add unit tests for `DEBUGGER` enum
  - Verify PDB value is "pdb"
  - Verify DEBUGPY value is "debugpy"
  - Verify enum inherits from str and Enum
  - Verify string comparison works correctly
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] Add unit tests for `DiagnosticOptionGroup` debugger options
  - Test `--debugger` option with 'pdb' choice
  - Test `--debugger` option with 'debugpy' choice
  - Test `--breakpoint` option with single value
  - Test `--breakpoint` option with multiple values
  - Test default values when options not specified
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] Add unit tests for `in_vscode_debugger` function
  - Test detection when running under VS Code
  - Test detection when running standalone
  - Verify stack frame iteration logic
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] Add unit tests for `debugger_wellknown_breakpoint_entry` function
  - Test with breakpoint not in configured list (returns immediately)
  - Test with pdb debugger (mock pdb.set_trace)
  - Test with debugpy debugger (mock debugpy functions)
  - Verify parameter handling
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [x] Add unit tests for `debugger_wellknown_breakpoint_code_append` function
  - Test code generation for pdb backend
  - Test code generation for debugpy backend
  - Test when breakpoint not in configured list
  - Verify correct indentation in generated code
  - Verify generated code is syntactically correct
  - _Requirements: 7.1-7.7, 8.1-8.5, 9.1-9.7_

- [x] Add unit tests for `DebugPyAssistant` class
  - Test initialization creates daemon thread
  - Test endpoint property returns correct value
  - Test thread property returns Thread object
  - Verify daemon flag is set
  - _Requirements: 10.1-10.6, 11.1-11.6, 12.1-12.3_

#### Integration Testing
- [x] Add integration tests for CLI debugging options
  - Test `--debugger pdb` sets runtime variable
  - Test `--debugger debugpy` sets runtime variable
  - Test `--breakpoint test-discovery` sets runtime variable
  - Test `--breakpoint testrun-start` sets runtime variable
  - Test combined debugger and breakpoint options
  - _Requirements: 3.5, 3.6_

- [x] Add integration tests for sequence document generation
  - Generate sequence document with pdb breakpoint enabled
  - Generate sequence document with debugpy breakpoint enabled
  - Verify breakpoint code inserted at correct location
  - Verify generated code is syntactically correct
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ] Add integration tests for runtime breakpoint triggering
  - Test TEST_DISCOVERY breakpoint triggers at correct point
  - Test TESTRUN_START breakpoint triggers at correct point
  - Verify breakpoint only triggers when enabled
  - _Requirements: 5.5, 5.6, 5.7_

#### Documentation Enhancements
- [x] Add comprehensive docstrings to all public classes and methods
  - Document WELLKNOWN_BREAKPOINTS enum members
  - Document DEBUGGER enum members
  - Document breakpoint entry function parameters
  - Document code generation function parameters
  - Document DebugPyAssistant class and methods
  - Include usage examples in docstrings

- [x] Add inline code comments for complex logic
  - Document VS Code detection algorithm
  - Document breakpoint triggering flow
  - Document code generation patterns
  - Document connection handling loop

- [x] Create usage examples in `source/examples/`
  - Basic pdb debugging example
  - Remote debugpy debugging example
  - DebugPyAssistant usage example
  - VS Code launch configuration example

- [x] Update user documentation
  - Document CLI debugging options
  - Document VS Code integration setup
  - Document breakpoint locations and purposes
  - Include troubleshooting guide

#### Feature Enhancements
- [ ] Support for custom breakpoint locations
  - Allow registration of custom breakpoints
  - Support breakpoints at test setup/teardown
  - Support breakpoints at scope entry/exit
  - Maintain backward compatibility

- [ ] Support for conditional breakpoints
  - Add condition parameter to breakpoint entry
  - Support expression-based conditions
  - Support test name pattern conditions

- [x] Support for breakpoint logging
  - Log when breakpoints are triggered
  - Log debugger connection events
  - Support configurable log levels
  - Implementation in `debuglogging.py` module
  - CLI option `--debug-log-level` added to `DiagnosticOptionGroup`

- [x] Support for multiple debug ports
  - Allow port configuration via CLI (`--debug-port` option)
  - Support port range for multiple sessions (`--debug-port-range` option)
  - Add port conflict detection (`PortConflictError`, `is_port_available()`)
  - Implementation in `debugports.py` and `debuggingext.py` modules

- [ ] Support for debug session timeout
  - Add timeout for wait_for_client
  - Support configurable timeout values
  - Continue execution on timeout

---

## Enhancement Opportunities

### Short-term Improvements

1. **Debug Port CLI Option** ✅ COMPLETED
   - Add `--debug-port` option to specify custom port
   - Allow override of default 5678 port
   - Document port configuration

2. **Breakpoint Logging** ✅ COMPLETED
   - Log when breakpoints are hit
   - Log debugger connection status
   - Include timestamps in log messages
   - Support configurable log levels via `--debug-log-level`

3. **Error Messages**
   - Improve error message when debugpy not installed
   - Add helpful installation instructions
   - Suggest pip install command

### Medium-term Improvements

1. **Conditional Breakpoints**
   - Support conditions for breakpoint activation
   - Allow test name patterns
   - Support expression evaluation

2. **Debug Session Management**
   - Track active debug sessions
   - Support session timeout
   - Allow session termination

3. **IDE Integration Improvements**
   - Auto-generate VS Code launch.json
   - Support PyCharm remote debugging
   - Document IDE-specific setup

### Long-term Improvements

1. **Distributed Debugging**
   - Support debugging across multiple processes
   - Enable remote debugging over network
   - Support container debugging

2. **Debug Recording**
   - Record debug sessions for replay
   - Capture variable states at breakpoints
   - Support session sharing

3. **Visual Debugging Tools**
   - Provide web-based debug interface
   - Support variable inspection
   - Enable step-through visualization

---

## Requirements Traceability

| Requirement | Status | Implementation Location |
|-------------|--------|------------------------|
| 1.1-1.5 | ✅ Complete | `breakpoints.py::WELLKNOWN_BREAKPOINTS` |
| 2.1-2.5 | ✅ Complete | `automojo.xmodules.debugging::DEBUGGER` |
| 3.1-3.4 | ✅ Complete | `cli/options.py::DiagnosticOptionGroup` |
| 3.5-3.6 | ✅ Complete | Runtime variable setting mechanism |
| 4.1-4.5 | ✅ Complete | `automojo.xmodules.debugging::in_vscode_debugger` |
| 5.1-5.7 | ✅ Complete | `automojo.xmodules.debugging::debugger_wellknown_breakpoint_entry` |
| 6.1-6.5 | ✅ Complete | Debugpy listen/wait implementation |
| 7.1-7.7 | ✅ Complete | `automojo.xmodules.debugging::debugger_wellknown_breakpoint_code_append` |
| 8.1-8.5 | ✅ Complete | PDB code generation |
| 9.1-9.7 | ✅ Complete | Debugpy code generation |
| 10.1-10.6 | ✅ Complete | `automojo.xmodules.debugging::DebugPyAssistant` |
| 11.1-11.6 | ✅ Complete | DebugPyAssistant connection handling |
| 12.1-12.3 | ✅ Complete | DebugPyAssistant properties |
| 13.1-13.5 | ✅ Complete | `sequencing/testsequencer.py` integration |
| 14.1-14.4 | ✅ Complete | Network configuration constants |
| 15.1-15.3 | ✅ Complete | Error handling for missing debugger |
| 16.1-16.4 | ✅ Complete | Blocking behavior documentation |
| 17.1-17.4 | ✅ Complete | VS Code launch configuration support |

---

## Test Coverage Summary

| Component | Unit Tests | Integration Tests |
|-----------|------------|-------------------|
| `WELLKNOWN_BREAKPOINTS` enum | ⬜ | N/A |
| `DEBUGGER` enum | ⬜ | N/A |
| `DiagnosticOptionGroup` debugger options | ⬜ | ⬜ |
| `in_vscode_debugger` function | ⬜ | N/A |
| `debugger_wellknown_breakpoint_entry` | ⬜ | ⬜ |
| `debugger_wellknown_breakpoint_code_append` | ⬜ | ⬜ |
| `DebugPyAssistant` class | ⬜ | ⬜ |
| TestSequencer integration | ⬜ | ⬜ |
| TestJob integration | ⬜ | ⬜ |
| CLI option parsing | ⬜ | ⬜ |

**Legend:** ✅ = Complete, ⚠️ = Partial, ⬜ = Not Started

---

## Known Limitations

1. **No Custom Breakpoint Locations**: Only TEST_DISCOVERY and TESTRUN_START breakpoints supported
2. **No Conditional Breakpoints**: Cannot specify conditions for breakpoint activation
3. **No Session Timeout**: wait_for_client() blocks indefinitely
4. **No Multi-Process Debugging**: Single process debugging only
5. **No Debug Session Recording**: Cannot record and replay debug sessions
6. **Limited IDE Support**: Only VS Code integration documented

---

## File Structure

```
source/packages/automojo/testbase/
├── breakpoints.py              # WELLKNOWN_BREAKPOINTS enum
├── debuglogging.py             # Breakpoint logging infrastructure
│                               # - DEBUG_LOG_LEVEL enum
│                               # - log_breakpoint_triggered()
│                               # - log_debugger_connection()
│                               # - log_debug_session_start()
│                               # - log_debug_session_end()
│                               # - log_debug_error()
│                               # - log_debug_warning()
│                               # - get/set_debug_log_level()
├── debugports.py               # Port utilities for debugging support
│                               # - is_port_available()
│                               # - find_available_port()
│                               # - parse_port_range()
│                               # - resolve_debug_port()
│                               # - PortConflictError, PortRangeError
│                               # - get/set_configured_debug_port()
├── debuggingext.py             # Extended debugging with port configuration
│                               # - debugger_wellknown_breakpoint_entry_with_port()
│                               # - debugger_wellknown_breakpoint_code_append_with_port()
├── testjob.py                  # TestJob with breakpoint entry integration
├── cli/
│   ├── options.py              # DiagnosticOptionGroup with debugger options
│   │                           # - --debugger, --breakpoint
│   │                           # - --debug-port, --debug-port-range
│   │                           # - --debug-log-level
│   └── cmdtree/testing/run.py  # Run command with debug port handling
└── sequencing/
    └── testsequencer.py        # Breakpoint code generation integration

.venv/src/automojo-xmodules/source/packages/automojo/xmodules/
└── debugging.py                # Core debugging infrastructure
                                # - DEBUGGER enum
                                # - debugger_wellknown_breakpoint_entry()
                                # - debugger_wellknown_breakpoint_code_append()
                                # - DebugPyAssistant class
                                # - in_vscode_debugger()

source/tests/automojo_tests/testbase/
├── test_debugging.py           # Unit tests for debugging (planned)
├── test_debuglogging.py        # Unit tests for debug logging
└── test_debugports.py          # Unit tests for debug port utilities

source/examples/
└── debug_example.py            # Example usage of debugging (planned)
```

---

## VS Code Configuration Example

Example `.vscode/launch.json` for attaching to TestBase debug sessions:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "TestBase: Attach",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "."
                }
            ]
        },
        {
            "name": "TestBase: Attach to Assistant",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5679
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "."
                }
            ]
        }
    ]
}
```

---

## CLI Usage Examples

```bash
# Enable testrun-start breakpoint with pdb (terminal debugging)
testbase testing run --root ./tests --debugger pdb --breakpoint testrun-start

# Enable testrun-start breakpoint with debugpy (remote/IDE debugging)
testbase testing run --root ./tests --debugger debugpy --breakpoint testrun-start

# Enable debugpy with custom port
testbase testing run --root ./tests --debugger debugpy --breakpoint testrun-start --debug-port 5680

# Enable debugpy with port range (auto-select available port)
testbase testing run --root ./tests --debugger debugpy --breakpoint testrun-start --debug-port-range 5678-5688

# Enable verbose debug logging
testbase testing run --root ./tests --debugger debugpy --breakpoint testrun-start --debug-log-level debug

# Disable debug logging
testbase testing run --root ./tests --debugger debugpy --breakpoint testrun-start --debug-log-level disabled

# Enable test-discovery breakpoint with debugpy
testbase testing run --root ./tests --debugger debugpy --breakpoint test-discovery

# Enable multiple breakpoints
testbase testing run --root ./tests --debugger debugpy \
    --breakpoint test-discovery \
    --breakpoint testrun-start

# Enable multiple breakpoints with port range for multi-session support
testbase testing run --root ./tests --debugger debugpy \
    --breakpoint test-discovery \
    --breakpoint testrun-start \
    --debug-port-range 5678-5698

# Enable multiple breakpoints with verbose logging
testbase testing run --root ./tests --debugger debugpy \
    --breakpoint test-discovery \
    --breakpoint testrun-start \
    --debug-log-level debug
```
