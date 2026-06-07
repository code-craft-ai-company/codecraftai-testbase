"""
.. module:: debug_pdb_example
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Example demonstrating basic pdb debugging with TestBase.

.. moduleauthor:: CodeCraftX

This example demonstrates how to use the built-in Python debugger (pdb) with
TestBase's well-known breakpoints. PDB provides terminal-based interactive
debugging without requiring any external IDE setup.

Usage:
    To run tests with pdb debugging enabled at the testrun-start breakpoint:

        testbase testing run --root ./tests --debugger pdb --breakpoint testrun-start

    To enable the test-discovery breakpoint:

        testbase testing run --root ./tests --debugger pdb --breakpoint test-discovery

    To enable multiple breakpoints:

        testbase testing run --root ./tests --debugger pdb \\
            --breakpoint test-discovery \\
            --breakpoint testrun-start

PDB Commands:
    Once the debugger pauses at a breakpoint, you can use these common commands:
    - n (next): Execute the next line
    - s (step): Step into a function call
    - c (continue): Continue execution until the next breakpoint
    - l (list): Show the current location in the code
    - p <expr>: Print the value of an expression
    - q (quit): Quit the debugger and abort execution
    - h (help): Show help for debugger commands

Example Output:
    When a pdb breakpoint is hit, you'll see output like:

        > /path/to/testrun_sequence.py(42)session()
        -> with sequencer.enter_session_scope_context() as ssc:
        (Pdb)

    The (Pdb) prompt indicates you're in the interactive debugger.
"""

__author__ = "CodeCraftX"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.xmodules.debugging import (
    DEBUGGER,
    debugger_wellknown_breakpoint_entry,
)
from ccai.testbase.breakpoints import WELLKNOWN_BREAKPOINTS


def example_pdb_breakpoint_entry():
    """
    Demonstrates programmatic use of pdb breakpoint entry.

    This function shows how to trigger a pdb breakpoint programmatically
    using the debugger_wellknown_breakpoint_entry function. In normal
    TestBase usage, this is handled automatically by the framework when
    CLI options are specified.
    """
    print("\n--- example_pdb_breakpoint_entry ---")
    print("This example demonstrates triggering a pdb breakpoint programmatically.")
    print("When the breakpoint is hit, you'll enter the interactive pdb debugger.")
    print("Use 'c' to continue or 'q' to quit.\n")

    # Define which breakpoints are enabled
    # In normal usage, this comes from the --breakpoint CLI option
    configured_breakpoints = [WELLKNOWN_BREAKPOINTS.TESTRUN_START]

    # Trigger the breakpoint
    # This will pause execution and drop into pdb if the breakpoint is configured
    debugger_wellknown_breakpoint_entry(
        debugger=DEBUGGER.PDB,
        breakpoint_name=WELLKNOWN_BREAKPOINTS.TESTRUN_START,
        configured_breakpoints=configured_breakpoints
    )

    print("Execution continued after breakpoint.")


def example_pdb_breakpoint_not_configured():
    """
    Demonstrates that breakpoints only trigger when configured.

    This function shows that calling debugger_wellknown_breakpoint_entry
    with a breakpoint that is not in the configured list will simply
    return without pausing execution.
    """
    print("\n--- example_pdb_breakpoint_not_configured ---")
    print("This example shows that unconfigured breakpoints are skipped.")

    # Empty list means no breakpoints are enabled
    configured_breakpoints = []

    # This will NOT pause because TESTRUN_START is not in configured_breakpoints
    debugger_wellknown_breakpoint_entry(
        debugger=DEBUGGER.PDB,
        breakpoint_name=WELLKNOWN_BREAKPOINTS.TESTRUN_START,
        configured_breakpoints=configured_breakpoints
    )

    print("Breakpoint was skipped because it was not configured.")


def example_pdb_multiple_breakpoints():
    """
    Demonstrates configuring multiple breakpoints.

    This function shows how multiple breakpoints can be configured
    and how each breakpoint location can be triggered independently.
    """
    print("\n--- example_pdb_multiple_breakpoints ---")
    print("This example demonstrates multiple configured breakpoints.")

    # Configure both available breakpoints
    configured_breakpoints = [
        WELLKNOWN_BREAKPOINTS.TEST_DISCOVERY,
        WELLKNOWN_BREAKPOINTS.TESTRUN_START,
    ]

    print(f"Configured breakpoints: {configured_breakpoints}")

    # Simulate test discovery phase
    print("\nSimulating test discovery phase...")
    debugger_wellknown_breakpoint_entry(
        debugger=DEBUGGER.PDB,
        breakpoint_name=WELLKNOWN_BREAKPOINTS.TEST_DISCOVERY,
        configured_breakpoints=configured_breakpoints
    )
    print("Test discovery phase complete.")

    # Simulate testrun start phase
    print("\nSimulating testrun start phase...")
    debugger_wellknown_breakpoint_entry(
        debugger=DEBUGGER.PDB,
        breakpoint_name=WELLKNOWN_BREAKPOINTS.TESTRUN_START,
        configured_breakpoints=configured_breakpoints
    )
    print("Testrun start phase complete.")


def main():
    """
    Main entry point for the pdb debugging examples.

    Run this script directly to see the examples in action:

        python debug_pdb_example.py

    Note: The first example will drop you into the pdb debugger.
    Use 'c' to continue to the next example or 'q' to quit.
    """
    print("=" * 60)
    print("PDB Debugging Examples for TestBase")
    print("=" * 60)

    # Run examples that don't trigger breakpoints first
    example_pdb_breakpoint_not_configured()

    # This example will trigger a breakpoint - run last
    print("\n" + "=" * 60)
    print("The next example will trigger a pdb breakpoint.")
    print("Use 'c' to continue or 'q' to quit the debugger.")
    print("=" * 60)
    example_pdb_breakpoint_entry()

    print("\n" + "=" * 60)
    print("All examples completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
