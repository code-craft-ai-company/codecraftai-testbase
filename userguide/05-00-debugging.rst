.. _05-00-debugging:

*********
Debugging
*********

The TestBase framework provides comprehensive debugging support that enables developers
to pause test execution at well-known breakpoints using either the built-in Python
debugger (pdb) or the remote debugging protocol (debugpy) for IDE integration.

This chapter covers:

- CLI debugging options
- VS Code integration setup
- Breakpoint locations and purposes
- Troubleshooting common issues


CLI Debugging Options
=====================

TestBase provides command-line options for controlling debugger behavior and breakpoint
activation during test execution. These options are part of the ``DiagnosticOptionGroup``
and are available on the ``testbase testing run`` command.


Debugger Selection (--debugger)
-------------------------------

The ``--debugger`` option specifies which debugger backend to use when breakpoints are hit.

**Choices:**

- ``pdb`` - The built-in Python debugger for local terminal debugging
- ``debugpy`` - The remote debugging protocol for IDE integration (VS Code)

**Example:**

.. code-block:: bash

    # Use pdb for terminal debugging
    testbase testing run --root ./tests --debugger pdb --breakpoint testrun-start

    # Use debugpy for IDE debugging
    testbase testing run --root ./tests --debugger debugpy --breakpoint testrun-start


Breakpoint Selection (--breakpoint)
-----------------------------------

The ``--breakpoint`` option specifies which breakpoints to activate during test execution.
This option can be specified multiple times to enable multiple breakpoints.

**Choices:**

- ``test-discovery`` - Pause during the test discovery phase
- ``testrun-start`` - Pause at the start of test execution

**Example:**

.. code-block:: bash

    # Enable a single breakpoint
    testbase testing run --root ./tests --debugger pdb --breakpoint testrun-start

    # Enable multiple breakpoints
    testbase testing run --root ./tests --debugger debugpy \
        --breakpoint test-discovery \
        --breakpoint testrun-start


Complete CLI Examples
---------------------

.. code-block:: bash

    # Terminal debugging at test run start
    testbase testing run --root ./tests --debugger pdb --breakpoint testrun-start

    # Remote debugging at test discovery
    testbase testing run --root ./tests --debugger debugpy --breakpoint test-discovery

    # Remote debugging with multiple breakpoints
    testbase testing run --root ./tests --debugger debugpy \
        --breakpoint test-discovery \
        --breakpoint testrun-start


Breakpoint Locations and Purposes
=================================

TestBase defines well-known breakpoint locations at key stages of the test execution
lifecycle. Understanding these locations helps you choose the right breakpoint for
your debugging needs.


TEST_DISCOVERY Breakpoint
-------------------------

**Value:** ``test-discovery``

**Location:** Before test collection begins

**Purpose:** This breakpoint pauses execution during the test discovery phase, before
tests are collected and registered. Use this breakpoint when you need to debug:

- Test collection issues
- Module loading problems
- Test registration errors
- Import failures during discovery

**When to Use:**

- Tests are not being discovered as expected
- Import errors occur during test collection
- You need to inspect the test discovery process

**Example:**

.. code-block:: bash

    testbase testing run --root ./tests --debugger pdb --breakpoint test-discovery


TESTRUN_START Breakpoint
------------------------

**Value:** ``testrun-start``

**Location:** Entry point of the session() method in the generated test sequence document

**Purpose:** This breakpoint pauses execution at the start of test execution, before
the session scope context is entered. Use this breakpoint when you need to debug:

- Test initialization and setup
- Session-level configuration
- Pre-test environment state
- Fixture initialization

**When to Use:**

- Tests fail during setup
- You need to inspect the test environment before execution
- Session-level fixtures are not working correctly
- You want to step through test execution from the beginning

**Example:**

.. code-block:: bash

    testbase testing run --root ./tests --debugger debugpy --breakpoint testrun-start


VS Code Integration Setup
=========================

TestBase integrates with VS Code through the debugpy remote debugging protocol. This
section explains how to configure VS Code for debugging TestBase test runs.


Prerequisites
-------------

1. Install the Python extension for VS Code
2. Install debugpy in your Python environment:

   .. code-block:: bash

       pip install debugpy


Launch Configuration
--------------------

Create or update your ``.vscode/launch.json`` file with the following configurations:

.. code-block:: json

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


Configuration Details
~~~~~~~~~~~~~~~~~~~~~

**TestBase: Attach**

- **Port 5678**: Standard debugpy port for direct debugging sessions
- **Use Case**: Attach when using ``--debugger debugpy`` with breakpoints

**TestBase: Attach to Assistant**

- **Port 5679**: Dedicated port for DebugPyAssistant
- **Use Case**: Attach to the background debug assistant for on-demand debugging


Debugging Workflow
------------------

Follow these steps to debug a TestBase test run with VS Code:

1. **Start the test run with debugging enabled:**

   .. code-block:: bash

       testbase testing run --root ./tests --debugger debugpy --breakpoint testrun-start

2. **Wait for the "Waiting for debugger" message:**

   The console will display:

   .. code-block:: text

       INFO:root:Waiting for debugger on port=5678

3. **Attach VS Code debugger:**

   - Open the Run and Debug view (Ctrl+Shift+D / Cmd+Shift+D)
   - Select "TestBase: Attach" from the dropdown
   - Click the green play button or press F5

4. **Debug your tests:**

   - Execution will pause at the breakpoint
   - Use VS Code's debugging features (step, inspect variables, etc.)
   - Continue execution when ready


Network Configuration
---------------------

TestBase uses the following network configuration for debugging:

.. list-table:: Debug Ports
   :header-rows: 1
   :widths: 30 20 50

   * - Purpose
     - Port
     - Description
   * - Direct Debugging
     - 5678
     - Standard debugpy port for breakpoint debugging
   * - DebugPyAssistant
     - 5679
     - Background debug endpoint for on-demand debugging
   * - Listen Address
     - 0.0.0.0
     - Accepts connections from any network interface


Remote Debugging
----------------

For remote debugging (e.g., debugging tests running in a container or remote machine):

1. Ensure the debug port (5678 or 5679) is accessible through firewalls
2. Update the ``host`` in your launch configuration to the remote machine's address
3. Ensure path mappings are correctly configured for source file resolution


DebugPyAssistant
================

The DebugPyAssistant provides a background daemon thread that exposes a debugpy endpoint
for on-demand remote debugging. Unlike direct breakpoint debugging, the assistant allows
you to attach a debugger at any time during test execution without blocking the main process.


Features
--------

- **Non-blocking**: Tests continue running while the debug endpoint is available
- **On-demand**: Attach your debugger whenever you need to inspect state
- **Reconnectable**: Disconnect and reconnect as needed during a test run
- **Daemon thread**: Automatically terminates when the main program exits


Usage
-----

The DebugPyAssistant is typically used programmatically:

.. code-block:: python

    from automojo.xmodules.debugging import DebugPyAssistant

    # Create the assistant with default settings
    # Default endpoint: ("0.0.0.0", 5679)
    assistant = DebugPyAssistant()

    # Or with custom settings
    assistant = DebugPyAssistant(
        name="CustomDebugAssistant",
        endpoint=("0.0.0.0", 5680)
    )

    # Access properties
    print(f"Endpoint: {assistant.endpoint}")
    print(f"Thread: {assistant.thread.name}")


Attaching to the Assistant
--------------------------

1. Use the "TestBase: Attach to Assistant" launch configuration in VS Code
2. Or manually attach to ``localhost:5679``
3. The assistant triggers a breakpoint when you connect
4. Debug as needed, then disconnect to continue execution
5. Reconnect anytime to debug again


Troubleshooting
===============

This section covers common issues and their solutions when debugging with TestBase.


Debugger Not Attaching
----------------------

**Symptom:** The test run waits indefinitely with "Waiting for debugger on port=5678"

**Solutions:**

1. Verify VS Code is using the correct launch configuration
2. Check that the port is not blocked by a firewall
3. Ensure debugpy is installed: ``pip install debugpy``
4. Verify no other process is using port 5678


Port Already in Use
-------------------

**Symptom:** Error message indicating the debug port is already in use

**Solutions:**

1. Check for other running debug sessions
2. Kill any orphaned Python processes using the port
3. Use a different port by modifying the launch configuration

.. code-block:: bash

    # Find processes using port 5678
    lsof -i :5678

    # Kill the process if needed
    kill -9 <PID>


Breakpoint Not Triggering
-------------------------

**Symptom:** Test execution continues without pausing at the breakpoint

**Solutions:**

1. Verify both ``--debugger`` and ``--breakpoint`` options are specified
2. Check that the breakpoint name is spelled correctly
3. Ensure the debugger is attached before the breakpoint is reached


Path Mapping Issues
-------------------

**Symptom:** VS Code cannot find source files or shows wrong file locations

**Solutions:**

1. Verify ``pathMappings`` in launch.json are correct
2. Ensure ``localRoot`` points to your workspace folder
3. For remote debugging, ensure ``remoteRoot`` matches the remote path


debugpy Not Installed
---------------------

**Symptom:** ImportError when using ``--debugger debugpy``

**Solution:**

.. code-block:: bash

    pip install debugpy


pdb Debugging Tips
------------------

When using pdb for terminal debugging:

**Common pdb Commands:**

- ``n`` (next): Execute the next line
- ``s`` (step): Step into a function call
- ``c`` (continue): Continue execution until next breakpoint
- ``l`` (list): Show current code context
- ``p <expr>`` (print): Print the value of an expression
- ``q`` (quit): Quit the debugger

**Example Session:**

.. code-block:: text

    > /path/to/test.py(10)test_function()
    -> result = calculate_value()
    (Pdb) n
    > /path/to/test.py(11)test_function()
    -> assert result == expected
    (Pdb) p result
    42
    (Pdb) c


Best Practices
==============

1. **Use debugpy for complex debugging**: When you need IDE features like variable
   inspection, watch expressions, and call stack navigation.

2. **Use pdb for quick debugging**: When you need a quick look at a specific value
   or want to step through a few lines of code.

3. **Start with testrun-start**: This breakpoint gives you the most control over
   the test execution from the beginning.

4. **Use test-discovery for collection issues**: When tests aren't being found or
   there are import errors during discovery.

5. **Keep VS Code launch configurations ready**: Having pre-configured launch
   configurations saves time when debugging is needed.

6. **Use DebugPyAssistant for long-running tests**: When you want the option to
   attach a debugger without knowing in advance when you'll need it.


See Also
========

- :mod:`automojo.xmodules.debugging` - Core debugging infrastructure
- :class:`automojo.testbase.breakpoints.WELLKNOWN_BREAKPOINTS` - Breakpoint enumeration
- :class:`automojo.testbase.cli.options.DiagnosticOptionGroup` - CLI options for debugging
