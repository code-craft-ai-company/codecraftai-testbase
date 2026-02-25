"""
.. module:: debug_diagnostics_basic
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Example demonstrating basic diagnostic capture usage with TestBase.

.. moduleauthor:: AutomationX

This example demonstrates the basic usage of the TestBase diagnostic capture system.
The diagnostic system enables capturing diagnostic information at key points during
test execution - before tests run (pre-run) and after tests complete (post-run).

Usage:
    To run tests with pre-run diagnostics enabled:

        testbase testing run --root ./tests --prerun-diagnostic

    To run tests with post-run diagnostics enabled:

        testbase testing run --root ./tests --postrun-diagnostic

    To enable both pre-run and post-run diagnostics:

        testbase testing run --root ./tests --prerun-diagnostic --postrun-diagnostic

Diagnostic Output:
    When diagnostics are enabled, the framework creates a folder structure under
    the test results directory:

        <test_results_dir>/
        └── diagnostics/
            ├── prerun-diagnostic/
            │   └── <integration_name>/
            │       └── diagnostic_files...
            └── postrun-diagnostic/
                └── <integration_name>/
                    └── diagnostic_files...

    Each integration coupling creates its own subfolder and writes diagnostic
    files specific to its resource type.

See Also:
    - debug_diagnostics_custom.py: Custom integration diagnostic implementation
    - debug_diagnostics_cli.py: CLI diagnostic options usage
    - debug_diagnostics_levels.py: Diagnostic level usage patterns
"""

__author__ = "AutomationX"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.testbase.diagnostics import DiagnosticLabel, RuntimeConfigPaths


def example_diagnostic_labels():
    """
    Demonstrates the usage of DiagnosticLabel constants.

    The DiagnosticLabel class provides string constants that identify
    diagnostic capture stages in the test execution lifecycle.
    """
    print("\n--- example_diagnostic_labels ---")
    print("DiagnosticLabel constants identify diagnostic capture stages.\n")

    # Access the pre-run diagnostic label
    prerun_label = DiagnosticLabel.PRERUN_DIAGNOSTIC
    print(f"PRERUN_DIAGNOSTIC: '{prerun_label}'")

    # Access the post-run diagnostic label
    postrun_label = DiagnosticLabel.POSTRUN_DIAGNOSTIC
    print(f"POSTRUN_DIAGNOSTIC: '{postrun_label}'")

    # Labels are string values that can be used for folder naming
    print(f"\nLabels are strings: type={type(prerun_label).__name__}")

    # Example: Using labels in conditional logic
    def process_diagnostic(label: str):
        if label == DiagnosticLabel.PRERUN_DIAGNOSTIC:
            print("  -> Processing pre-run diagnostics (initial system state)")
        elif label == DiagnosticLabel.POSTRUN_DIAGNOSTIC:
            print("  -> Processing post-run diagnostics (final system state)")
        else:
            print(f"  -> Unknown diagnostic label: {label}")

    print("\nProcessing diagnostics by label:")
    process_diagnostic(DiagnosticLabel.PRERUN_DIAGNOSTIC)
    process_diagnostic(DiagnosticLabel.POSTRUN_DIAGNOSTIC)


def example_runtime_config_paths():
    """
    Demonstrates the usage of RuntimeConfigPaths constants.

    The RuntimeConfigPaths class provides configuration paths for diagnostic
    runtime information within the application's configuration tree.
    """
    print("\n--- example_runtime_config_paths ---")
    print("RuntimeConfigPaths constants define configuration tree paths.\n")

    # Access the pre-run diagnostic configuration path
    prerun_path = RuntimeConfigPaths.DIAGNOSTIC_PRERUN
    print(f"DIAGNOSTIC_PRERUN: '{prerun_path}'")

    # Access the post-run diagnostic configuration path
    postrun_path = RuntimeConfigPaths.DIAGNOSTIC_POSTRUN
    print(f"DIAGNOSTIC_POSTRUN: '{postrun_path}'")

    # Paths follow a hierarchical format
    print("\nPath hierarchy breakdown:")
    path_parts = prerun_path.split('/')
    for i, part in enumerate(path_parts):
        if part:
            indent = "  " * i
            print(f"{indent}└── {part}")


def example_diagnostic_folder_structure():
    """
    Demonstrates the expected diagnostic folder structure.

    When diagnostics are enabled, the framework creates a specific folder
    hierarchy to organize diagnostic output from different integrations.
    """
    print("\n--- example_diagnostic_folder_structure ---")
    print("Diagnostic folder structure when diagnostics are enabled:\n")

    # Simulated folder structure
    structure = """
    <test_results_dir>/
    ├── testrun_results.json
    ├── testrun_summary.json
    └── diagnostics/
        ├── prerun-diagnostic/
        │   ├── device_integration/
        │   │   ├── status.json
        │   │   └── device_logs.txt
        │   └── network_integration/
        │       └── connection_state.json
        └── postrun-diagnostic/
            ├── device_integration/
            │   ├── status.json
            │   ├── device_logs.txt
            │   └── error_dump.json
            └── network_integration/
                └── connection_state.json
    """
    print(structure)

    print("Key points:")
    print("  - Diagnostics folder is at the root of test results")
    print("  - Pre-run and post-run have separate subfolders")
    print("  - Each integration creates its own subfolder")
    print("  - Diagnostic files are integration-specific")


def example_diagnostic_workflow():
    """
    Demonstrates the diagnostic capture workflow during test execution.

    This example shows the sequence of events when diagnostics are enabled
    and how they integrate with the test execution lifecycle.
    """
    print("\n--- example_diagnostic_workflow ---")
    print("Diagnostic capture workflow during test execution:\n")

    workflow_steps = [
        ("1. CLI Parsing", "Parse --prerun-diagnostic and --postrun-diagnostic flags"),
        ("2. Runtime Variables", "Set AM_DIAGNOSTICS_PRERUN and AM_DIAGNOSTICS_POSTRUN"),
        ("3. Integration Setup", "Initialize all integration couplings"),
        ("4. Pre-run Capture", "Call diagnostic() on each integration with 'prerun-diagnostic' label"),
        ("5. Test Execution", "Run all tests in the test suite"),
        ("6. Post-run Capture", "Call diagnostic() on each integration with 'postrun-diagnostic' label"),
        ("7. Finalization", "Complete test run and generate reports"),
    ]

    for step, description in workflow_steps:
        print(f"  {step}")
        print(f"      {description}")
        print()


def main():
    """
    Main entry point for the basic diagnostic examples.

    Run this script directly to see the examples in action:

        python debug_diagnostics_basic.py
    """
    print("=" * 70)
    print("Basic Diagnostic Capture Examples for TestBase")
    print("=" * 70)

    example_diagnostic_labels()
    example_runtime_config_paths()
    example_diagnostic_folder_structure()
    example_diagnostic_workflow()

    print("=" * 70)
    print("All basic diagnostic examples completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
