"""
.. module:: debug_diagnostics_cli
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Example demonstrating CLI diagnostic options usage with TestBase.

.. moduleauthor:: CodeCraftX

This example demonstrates how to use the command-line interface (CLI) options
for controlling diagnostic capture during test execution. The DiagnosticOptionGroup
provides options for enabling pre-run and post-run diagnostic capture.

CLI Options:
    --prerun-diagnostic     Enable pre-run diagnostic capture
    --postrun-diagnostic    Enable post-run diagnostic capture
    --debugger              Select debugger (pdb or debugpy)
    --breakpoint            Specify breakpoints to activate

Usage Examples:
    # Enable pre-run diagnostics only
    testbase testing run --root ./tests --prerun-diagnostic

    # Enable post-run diagnostics only
    testbase testing run --root ./tests --postrun-diagnostic

    # Enable both pre-run and post-run diagnostics
    testbase testing run --root ./tests --prerun-diagnostic --postrun-diagnostic

    # Combine with other options
    testbase testing run --root ./tests \\
        --prerun-diagnostic \\
        --postrun-diagnostic \\
        --output ./results \\
        --include my_tests

Runtime Variables:
    When CLI options are specified, they set corresponding runtime variables:
    - --prerun-diagnostic  -> AM_DIAGNOSTICS_PRERUN = True
    - --postrun-diagnostic -> AM_DIAGNOSTICS_POSTRUN = True

See Also:
    - debug_diagnostics_basic.py: Basic diagnostic capture usage
    - debug_diagnostics_custom.py: Custom integration diagnostic implementation
    - debug_diagnostics_levels.py: Diagnostic level usage patterns
"""

__author__ = "CodeCraftX"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.testbase.diagnostics import RuntimeConfigPaths


def example_cli_options_overview():
    """
    Demonstrates an overview of available CLI diagnostic options.

    The DiagnosticOptionGroup provides several options for controlling
    diagnostic and debugging behavior during test execution.
    """
    print("\n--- example_cli_options_overview ---")
    print("Available CLI diagnostic options:\n")

    options = [
        ("--prerun-diagnostic", "Boolean", "False", "Enable pre-run diagnostic capture"),
        ("--postrun-diagnostic", "Boolean", "False", "Enable post-run diagnostic capture"),
        ("--debugger", "Choice", "None", "Debugger to activate (pdb or debugpy)"),
        ("--breakpoint", "Multiple", "None", "Breakpoints to activate"),
    ]

    print(f"{'Option':<25} {'Type':<10} {'Default':<10} {'Description'}")
    print("-" * 80)
    for option, opt_type, default, description in options:
        print(f"{option:<25} {opt_type:<10} {default:<10} {description}")


def example_prerun_diagnostic_usage():
    """
    Demonstrates the --prerun-diagnostic CLI option usage.

    Pre-run diagnostics capture the initial state of the test environment
    before any tests are executed.
    """
    print("\n--- example_prerun_diagnostic_usage ---")
    print("Using --prerun-diagnostic CLI option:\n")

    print("Command:")
    print("    testbase testing run --root ./tests --prerun-diagnostic\n")

    print("What happens:")
    print("    1. CLI parses --prerun-diagnostic flag")
    print("    2. AM_DIAGNOSTICS_PRERUN runtime variable is set to True")
    print("    3. After integration setup, TestSequencer calls diagnostic_capture_pre_testrun()")
    print("    4. Each integration's diagnostic() method is called with label='prerun-diagnostic'")
    print("    5. Diagnostic files are written to <results>/diagnostics/prerun-diagnostic/\n")

    print("Use cases:")
    print("    - Capture initial device configurations")
    print("    - Record environment state before tests modify it")
    print("    - Document baseline system conditions")
    print("    - Audit test environment setup")


def example_postrun_diagnostic_usage():
    """
    Demonstrates the --postrun-diagnostic CLI option usage.

    Post-run diagnostics capture the final state of the test environment
    after all tests have completed.
    """
    print("\n--- example_postrun_diagnostic_usage ---")
    print("Using --postrun-diagnostic CLI option:\n")

    print("Command:")
    print("    testbase testing run --root ./tests --postrun-diagnostic\n")

    print("What happens:")
    print("    1. CLI parses --postrun-diagnostic flag")
    print("    2. AM_DIAGNOSTICS_POSTRUN runtime variable is set to True")
    print("    3. After test execution, TestSequencer calls diagnostic_capture_post_testrun()")
    print("    4. Each integration's diagnostic() method is called with label='postrun-diagnostic'")
    print("    5. Diagnostic files are written to <results>/diagnostics/postrun-diagnostic/\n")

    print("Use cases:")
    print("    - Capture device logs after test failures")
    print("    - Record final system state for debugging")
    print("    - Collect error dumps and stack traces")
    print("    - Document changes made during testing")


def example_combined_diagnostics():
    """
    Demonstrates using both diagnostic options together.

    Combining pre-run and post-run diagnostics provides a complete picture
    of the test environment before and after test execution.
    """
    print("\n--- example_combined_diagnostics ---")
    print("Using both --prerun-diagnostic and --postrun-diagnostic:\n")

    print("Command:")
    print("    testbase testing run --root ./tests --prerun-diagnostic --postrun-diagnostic\n")

    print("Resulting folder structure:")
    structure = """
    <test_results_dir>/
    └── diagnostics/
        ├── prerun-diagnostic/      <- Captured BEFORE tests run
        │   ├── device_integration/
        │   │   └── initial_state.json
        │   └── service_integration/
        │       └── initial_config.json
        └── postrun-diagnostic/     <- Captured AFTER tests complete
            ├── device_integration/
            │   ├── final_state.json
            │   └── error_logs.txt
            └── service_integration/
                └── final_config.json
    """
    print(structure)

    print("Benefits of combined diagnostics:")
    print("    - Compare before/after states to identify changes")
    print("    - Debug test failures with full context")
    print("    - Verify test cleanup and teardown")
    print("    - Support post-mortem analysis")


def example_cli_with_other_options():
    """
    Demonstrates combining diagnostic options with other CLI options.

    Diagnostic options can be combined with other TestBase CLI options
    for comprehensive test execution control.
    """
    print("\n--- example_cli_with_other_options ---")
    print("Combining diagnostic options with other CLI options:\n")

    examples = [
        (
            "With output directory",
            "testbase testing run --root ./tests --prerun-diagnostic --output ./my_results"
        ),
        (
            "With test filtering",
            "testbase testing run --root ./tests --postrun-diagnostic --include smoke_tests"
        ),
        (
            "With debugging",
            "testbase testing run --root ./tests --prerun-diagnostic --debugger pdb --breakpoint testrun-start"
        ),
        (
            "Full example",
            """testbase testing run \\
        --root ./tests \\
        --prerun-diagnostic \\
        --postrun-diagnostic \\
        --output ./results \\
        --include integration_tests \\
        --exclude slow_tests"""
        ),
    ]

    for description, command in examples:
        print(f"{description}:")
        print(f"    {command}\n")


def example_runtime_variable_mapping():
    """
    Demonstrates the mapping between CLI options and runtime variables.

    CLI options set runtime variables that control diagnostic behavior
    throughout the test execution lifecycle.
    """
    print("\n--- example_runtime_variable_mapping ---")
    print("CLI option to runtime variable mapping:\n")

    mappings = [
        ("--prerun-diagnostic", "AM_DIAGNOSTICS_PRERUN", RuntimeConfigPaths.DIAGNOSTIC_PRERUN),
        ("--postrun-diagnostic", "AM_DIAGNOSTICS_POSTRUN", RuntimeConfigPaths.DIAGNOSTIC_POSTRUN),
    ]

    print(f"{'CLI Option':<25} {'Runtime Variable':<25} {'Config Path'}")
    print("-" * 100)
    for cli_opt, runtime_var, config_path in mappings:
        print(f"{cli_opt:<25} {runtime_var:<25} {config_path}")

    print("\nRuntime variable flow:")
    print("    1. CLI option parsed by DiagnosticOptionGroup")
    print("    2. Runtime option override mechanism sets runtime variable")
    print("    3. TestSequencer checks runtime variable before diagnostic capture")
    print("    4. If True, diagnostic capture proceeds; if False, it's skipped")


def main():
    """
    Main entry point for the CLI diagnostic options examples.

    Run this script directly to see the examples in action:

        python debug_diagnostics_cli.py
    """
    print("=" * 70)
    print("CLI Diagnostic Options Usage Examples")
    print("=" * 70)

    example_cli_options_overview()
    example_prerun_diagnostic_usage()
    example_postrun_diagnostic_usage()
    example_combined_diagnostics()
    example_cli_with_other_options()
    example_runtime_variable_mapping()

    print("\n" + "=" * 70)
    print("All CLI diagnostic examples completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
