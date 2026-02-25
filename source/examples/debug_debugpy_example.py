"""
.. module:: debug_debugpy_example
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Example demonstrating remote debugpy debugging with TestBase.

.. moduleauthor:: AutomationX

This example demonstrates how to use the debugpy remote debugging protocol
with TestBase's well-known breakpoints. Debugpy enables IDE integration,
allowing you to debug tests using VS Code or other compatible IDEs.

Prerequisites:
    Install debugpy if not already installed:

        pip install debugpy

Usage:
    To run tests with debugpy debugging enabled:

        testbase testing run --root ./tests --debugger debugpy --breakpoint testrun-start

    Then attach your IDE to localhost:5678 to begin debugging.

VS Code Setup:
    1. Add a launch configuration to .vscode/launch.json (see debug_vscode_launch_example.json)
    2. Run the testbase command with --debugger debugpy
    3. In VS Code, select "TestBase: Attach" from the debug dropdown
    4. Click the green play button or press F5 to attach

Network Configuration:
    - Default debug port: 5678
    - Listen address: 0.0.0.0 (accepts connections from any interface)
    - For remote debugging, ensure the port is accessible through firewalls

Example Output:
    When debugpy is waiting for a connection:

        INFO:root:Waiting for debugger on port=5678

    Once attached, execution will pause at the breakpoint and you can
    use your IDE's debugging features (step, inspect variables, etc.).
"""

__author__ = "AutomationX"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import logging

from automojo.xmodules.debugging import (
    DEBUGGER,
    DEFAULT_DEBUG_PORT,
    debugger_wellknown_breakpoint_entry,
    debugger_wellknown_breakpoint_code_append,
    in_vscode_debugger,
)
from automojo.testbase.breakpoints import WELLKNOWN_BREAKPOINTS


# Configure logging to see debug messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_check_vscode_debugger():
    """
    Demonstrates checking if running under VS Code debugger.

    The in_vscode_debugger() function detects whether the current process
    is being debugged by VS Code. This is used internally to determine
    whether to set up the remote debugging endpoint.
    """
    print("\n--- example_check_vscode_debugger ---")

    is_vscode = in_vscode_debugger()
    print(f"Running under VS Code debugger: {is_vscode}")

    if is_vscode:
        print("VS Code debugger detected - debugpy.listen() and wait_for_client() will be called")
    else:
        print("Not running under VS Code - only debugpy.breakpoint() will be called")


def example_debugpy_breakpoint_entry():
    """
    Demonstrates programmatic use of debugpy breakpoint entry.

    This function shows how to trigger a debugpy breakpoint programmatically.
    When running under VS Code, this will:
    1. Start listening for debugger connections on port 5678
    2. Wait for a debug client to attach
    3. Trigger a breakpoint once attached

    Note: This example will block waiting for a debugger connection if
    running under VS Code. Press Ctrl+C to abort if no debugger attaches.
    """
    print("\n--- example_debugpy_breakpoint_entry ---")
    print("This example demonstrates triggering a debugpy breakpoint.")
    print(f"Debug port: {DEFAULT_DEBUG_PORT}")

    # Check if we're under VS Code
    if in_vscode_debugger():
        print("\nVS Code detected - will wait for debugger connection.")
        print("Attach your debugger to localhost:5678 to continue.")
    else:
        print("\nNot running under VS Code - breakpoint will trigger immediately.")

    # Define which breakpoints are enabled
    configured_breakpoints = [WELLKNOWN_BREAKPOINTS.TESTRUN_START]

    # Trigger the breakpoint
    # If under VS Code, this will wait for a debugger to attach
    debugger_wellknown_breakpoint_entry(
        debugger=DEBUGGER.DEBUGPY,
        breakpoint_name=WELLKNOWN_BREAKPOINTS.TESTRUN_START,
        configured_breakpoints=configured_breakpoints
    )

    print("Execution continued after breakpoint.")


def example_debugpy_code_generation():
    """
    Demonstrates debugpy breakpoint code generation.

    This function shows how the debugger_wellknown_breakpoint_code_append
    function generates Python source code for breakpoints. This is used
    by the TestSequencer to insert breakpoint code into generated test
    sequence documents.
    """
    print("\n--- example_debugpy_code_generation ---")
    print("This example shows the code generated for debugpy breakpoints.")

    # List to collect generated code lines
    code_lines = []
    current_indent = "    "  # 4-space indentation (typical method body)

    # Configure the testrun-start breakpoint
    configured_breakpoints = [WELLKNOWN_BREAKPOINTS.TESTRUN_START]

    # Generate the breakpoint code
    debugger_wellknown_breakpoint_code_append(
        debugger=DEBUGGER.DEBUGPY,
        breakpoint_name=WELLKNOWN_BREAKPOINTS.TESTRUN_START,
        code_lines=code_lines,
        current_indent=current_indent,
        configured_breakpoints=configured_breakpoints
    )

    print("\nGenerated code for debugpy breakpoint:")
    print("-" * 40)
    for line in code_lines:
        print(line)
    print("-" * 40)


def example_debugpy_code_generation_pdb():
    """
    Demonstrates pdb breakpoint code generation for comparison.

    This function shows the simpler code generated for pdb breakpoints,
    which doesn't require the remote debugging setup.
    """
    print("\n--- example_debugpy_code_generation_pdb ---")
    print("This example shows the code generated for pdb breakpoints (for comparison).")

    code_lines = []
    current_indent = "    "
    configured_breakpoints = [WELLKNOWN_BREAKPOINTS.TESTRUN_START]

    # Generate pdb breakpoint code
    debugger_wellknown_breakpoint_code_append(
        debugger=DEBUGGER.PDB,
        breakpoint_name=WELLKNOWN_BREAKPOINTS.TESTRUN_START,
        code_lines=code_lines,
        current_indent=current_indent,
        configured_breakpoints=configured_breakpoints
    )

    print("\nGenerated code for pdb breakpoint:")
    print("-" * 40)
    for line in code_lines:
        print(line)
    print("-" * 40)


def example_breakpoint_not_configured():
    """
    Demonstrates that no code is generated for unconfigured breakpoints.
    """
    print("\n--- example_breakpoint_not_configured ---")
    print("This example shows that unconfigured breakpoints generate no code.")

    code_lines = []
    current_indent = "    "
    configured_breakpoints = []  # No breakpoints configured

    # Try to generate code for an unconfigured breakpoint
    debugger_wellknown_breakpoint_code_append(
        debugger=DEBUGGER.DEBUGPY,
        breakpoint_name=WELLKNOWN_BREAKPOINTS.TESTRUN_START,
        code_lines=code_lines,
        current_indent=current_indent,
        configured_breakpoints=configured_breakpoints
    )

    print(f"\nGenerated code lines: {len(code_lines)}")
    if not code_lines:
        print("No code generated (breakpoint not configured)")


def main():
    """
    Main entry point for the debugpy debugging examples.

    Run this script directly to see the examples in action:

        python debug_debugpy_example.py

    Note: The breakpoint entry example may block waiting for a debugger
    connection if running under VS Code. Use Ctrl+C to abort.
    """
    print("=" * 60)
    print("Debugpy Remote Debugging Examples for TestBase")
    print("=" * 60)

    # Run non-blocking examples first
    example_check_vscode_debugger()
    example_debugpy_code_generation()
    example_debugpy_code_generation_pdb()
    example_breakpoint_not_configured()

    # This example may block - run last
    print("\n" + "=" * 60)
    print("The next example may wait for a debugger connection.")
    print("If running under VS Code, attach to localhost:5678")
    print("Otherwise, press Ctrl+C to skip.")
    print("=" * 60)

    try:
        example_debugpy_breakpoint_entry()
    except KeyboardInterrupt:
        print("\nSkipped - no debugger attached.")

    print("\n" + "=" * 60)
    print("All examples completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
