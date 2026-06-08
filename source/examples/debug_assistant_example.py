"""
.. module:: debug_assistant_example
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Example demonstrating DebugPyAssistant usage for on-demand debugging.

.. moduleauthor:: CodeCraftX

This example demonstrates how to use the DebugPyAssistant class for on-demand
remote debugging. The DebugPyAssistant creates a background daemon thread that
exposes a debugpy endpoint, allowing you to attach a debugger at any time during
test execution without blocking the main process.

Key Features:
    - Non-blocking: Tests continue running while the debug endpoint is available
    - On-demand: Attach your debugger whenever you need to inspect state
    - Reconnectable: Disconnect and reconnect as needed during a test run
    - Daemon thread: Automatically terminates when the main program exits

Network Configuration:
    - Default port: 5679 (different from direct debugging port 5678)
    - Listen address: 0.0.0.0 (accepts connections from any interface)
    - Custom endpoints can be specified during initialization

Usage:
    1. Create a DebugPyAssistant instance at the start of your test run
    2. Tests execute normally without blocking
    3. When you need to debug, attach your IDE to localhost:5679
    4. The assistant triggers a breakpoint upon connection
    5. Debug as needed, then disconnect to continue execution
    6. Reconnect anytime to debug again

VS Code Setup:
    Add this configuration to .vscode/launch.json:

    {
        "name": "TestBase: Attach to Assistant",
        "type": "debugpy",
        "request": "attach",
        "connect": {
            "host": "localhost",
            "port": 5679
        }
    }

Prerequisites:
    Install debugpy if not already installed:

        pip install debugpy
"""

__author__ = "CodeCraftX"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import time
import logging

from ccai.xmodules.debugging import (
    DebugPyAssistant,
    PORT_DEBUGPY_ASSISTANT,
)


# Configure logging to see debug messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_assistant():
    """
    Demonstrates basic DebugPyAssistant usage.

    This example creates a DebugPyAssistant with default settings and
    shows how to access its properties. The assistant runs in a background
    daemon thread, so the main program continues executing.
    """
    print("\n--- example_basic_assistant ---")
    print("Creating DebugPyAssistant with default settings...")

    # Create the assistant with default settings
    # Default endpoint: ("0.0.0.0", 5679)
    assistant = DebugPyAssistant()

    # Access properties
    print(f"Endpoint: {assistant.endpoint}")
    print(f"Thread name: {assistant.thread.name}")
    print(f"Thread is daemon: {assistant.thread.daemon}")
    print(f"Thread is alive: {assistant.thread.is_alive()}")

    print(f"\nDebug endpoint available at localhost:{PORT_DEBUGPY_ASSISTANT}")
    print("Attach your debugger to this port to trigger a breakpoint.")

    return assistant


def example_custom_endpoint():
    """
    Demonstrates creating a DebugPyAssistant with a custom endpoint.

    You can specify a custom host and port when creating the assistant.
    This is useful when running multiple test processes or when the
    default port is already in use.
    """
    print("\n--- example_custom_endpoint ---")
    print("Creating DebugPyAssistant with custom endpoint...")

    # Create assistant with custom endpoint
    custom_endpoint = ("0.0.0.0", 5680)
    assistant = DebugPyAssistant(
        name="CustomDebugAssistant",
        endpoint=custom_endpoint
    )

    print(f"Custom endpoint: {assistant.endpoint}")
    print(f"Thread name: {assistant.thread.name}")

    return assistant


def example_assistant_properties():
    """
    Demonstrates accessing DebugPyAssistant properties.

    The assistant exposes read-only properties for the endpoint and
    the background thread, allowing you to inspect the assistant's state.
    """
    print("\n--- example_assistant_properties ---")

    assistant = DebugPyAssistant(name="PropertyDemo")

    # Endpoint property returns (host, port) tuple
    host, port = assistant.endpoint
    print(f"Host: {host}")
    print(f"Port: {port}")

    # Thread property returns the Thread object
    thread = assistant.thread
    print(f"Thread name: {thread.name}")
    print(f"Thread daemon: {thread.daemon}")
    print(f"Thread alive: {thread.is_alive()}")
    print(f"Thread ident: {thread.ident}")

    return assistant


def example_simulated_test_run():
    """
    Demonstrates using DebugPyAssistant during a simulated test run.

    This example shows how the assistant allows non-blocking test execution
    while maintaining a debug endpoint for on-demand debugging.
    """
    print("\n--- example_simulated_test_run ---")
    print("Simulating a test run with DebugPyAssistant...")

    # Create the assistant at the start of the test run
    assistant = DebugPyAssistant(name="TestRunAssistant")
    print(f"Debug assistant started on port {assistant.endpoint[1]}")

    # Simulate test execution
    print("\nSimulating test execution...")
    for i in range(5):
        print(f"  Running test {i + 1}/5...")
        time.sleep(0.5)  # Simulate test work

        # At any point, you could attach a debugger to inspect state
        # The assistant will trigger a breakpoint when you connect

    print("\nTest run complete.")
    print("The debug assistant remained available throughout the run.")
    print("You could have attached a debugger at any time to inspect state.")

    return assistant


def main():
    """
    Main entry point for the DebugPyAssistant examples.

    Run this script directly to see the examples in action:

        python debug_assistant_example.py

    Note: The examples create debug endpoints that remain active until
    the script exits. You can attach a debugger to any of these endpoints
    while the script is running.
    """
    print("=" * 60)
    print("DebugPyAssistant Examples for TestBase")
    print("=" * 60)
    print(f"\nDefault assistant port: {PORT_DEBUGPY_ASSISTANT}")
    print("This is different from the direct debugging port (5678)")
    print("to avoid conflicts when both are used.\n")

    # Run examples
    assistants = []

    try:
        assistants.append(example_basic_assistant())
        assistants.append(example_custom_endpoint())
        assistants.append(example_assistant_properties())
        assistants.append(example_simulated_test_run())

        print("\n" + "=" * 60)
        print("All examples completed.")
        print("=" * 60)
        print("\nActive debug endpoints:")
        for assistant in assistants:
            if assistant.thread.is_alive():
                print(f"  - {assistant.thread.name}: localhost:{assistant.endpoint[1]}")

        print("\nThe script will now exit, terminating all daemon threads.")
        print("In a real test run, the assistant would remain active until")
        print("the test process completes.")

    except ImportError as e:
        print(f"\nError: {e}")
        print("Make sure debugpy is installed: pip install debugpy")


if __name__ == "__main__":
    main()
