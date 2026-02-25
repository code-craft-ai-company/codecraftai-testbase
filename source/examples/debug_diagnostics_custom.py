"""
.. module:: debug_diagnostics_custom
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Example demonstrating custom integration diagnostic implementation.

.. moduleauthor:: AutomationX

This example demonstrates how to implement custom diagnostic capture logic
in an IntegrationCoupling subclass. Each integration type can capture
diagnostic information specific to its resource type.

The diagnostic method is called by the TestSequencer at diagnostic capture
points (pre-run and post-run) and receives:
    - label: The diagnostic stage identifier (e.g., "prerun-diagnostic")
    - level: The maximum diagnostic level (1-9, higher = more detail)
    - diag_folder: The output directory for diagnostic files

Implementation Guidelines:
    1. Create an integration-specific subfolder within diag_folder
    2. Respect the diagnostic level parameter for verbosity control
    3. Handle errors internally to prevent propagation to the framework
    4. Write diagnostic files in standard formats (JSON, text, etc.)

See Also:
    - debug_diagnostics_basic.py: Basic diagnostic capture usage
    - debug_diagnostics_cli.py: CLI diagnostic options usage
    - debug_diagnostics_levels.py: Diagnostic level usage patterns
"""

__author__ = "AutomationX"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import os
import json
import tempfile
from typing import Dict, Any, List, Tuple

from automojo.testbase.diagnostics import DiagnosticLabel


# Note: In a real implementation, you would import IntegrationCoupling:
# from automojo.testbase.coupling.integrationcoupling import IntegrationCoupling


class ExampleServiceCoupling:
    """
    Example integration coupling demonstrating custom diagnostic implementation.

    This class shows how to implement the diagnostic() method in a custom
    integration coupling. In a real implementation, this would inherit from
    IntegrationCoupling.

    The diagnostic method captures information about the service state at
    different diagnostic levels:
        - Level 1-3: Basic status (service health, version)
        - Level 4-6: Standard diagnostics (configuration, connections)
        - Level 7-9: Detailed diagnostics (full logs, memory state)
    """

    # Integration identification attributes
    integration_root = "services"
    integration_section = "api"
    integration_leaf = "example"
    integration_class = "ExampleServiceCoupling"

    # Simulated service state
    _service_status = "running"
    _service_version = "1.2.3"
    _connection_count = 5
    _error_count = 0

    @classmethod
    def diagnostic(cls, label: str, level: int, diag_folder: str):
        """
        Capture diagnostic information for the example service.

        This method demonstrates the recommended pattern for implementing
        diagnostic capture in a custom integration coupling.

        :param label: The diagnostic stage identifier (e.g., "prerun-diagnostic")
        :param level: The maximum diagnostic level (1-9)
        :param diag_folder: The output directory for diagnostic files
        """
        try:
            # Step 1: Create integration-specific subfolder
            service_diag_folder = os.path.join(diag_folder, "example_service")
            os.makedirs(service_diag_folder, exist_ok=True)

            # Step 2: Capture diagnostics based on level
            # Level 1-3: Basic status
            if level >= 1:
                cls._capture_basic_status(service_diag_folder, label)

            # Level 4-6: Standard diagnostics
            if level >= 4:
                cls._capture_standard_diagnostics(service_diag_folder, label)

            # Level 7-9: Detailed diagnostics
            if level >= 7:
                cls._capture_detailed_diagnostics(service_diag_folder, label)

        except Exception as err:
            # Step 3: Handle errors internally - don't propagate to framework
            # In production, you would log this error
            print(f"Warning: Diagnostic capture failed for {cls.integration_class}: {err}")

    @classmethod
    def _capture_basic_status(cls, diag_folder: str, label: str):
        """Capture basic service status (Level 1-3)."""
        status_data = {
            "diagnostic_label": label,
            "service_status": cls._service_status,
            "service_version": cls._service_version,
            "integration_key": f"{cls.integration_root}:{cls.integration_section}:{cls.integration_leaf}:{cls.integration_class}"
        }

        status_file = os.path.join(diag_folder, "status.json")
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)

    @classmethod
    def _capture_standard_diagnostics(cls, diag_folder: str, label: str):
        """Capture standard diagnostics (Level 4-6)."""
        config_data = {
            "diagnostic_label": label,
            "connection_count": cls._connection_count,
            "error_count": cls._error_count,
            "configuration": {
                "timeout": 30,
                "retry_count": 3,
                "endpoint": "https://api.example.com"
            }
        }

        config_file = os.path.join(diag_folder, "configuration.json")
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

    @classmethod
    def _capture_detailed_diagnostics(cls, diag_folder: str, label: str):
        """Capture detailed diagnostics (Level 7-9)."""
        # Simulated detailed logs
        logs = [
            f"[INFO] Diagnostic capture started for label: {label}",
            "[DEBUG] Checking service health...",
            "[DEBUG] Service health: OK",
            "[DEBUG] Checking connection pool...",
            f"[DEBUG] Active connections: {cls._connection_count}",
            "[INFO] Diagnostic capture completed"
        ]

        logs_file = os.path.join(diag_folder, "detailed_logs.txt")
        with open(logs_file, 'w') as f:
            f.write('\n'.join(logs))

        # Full state dump
        full_dump = {
            "diagnostic_label": label,
            "service_state": {
                "status": cls._service_status,
                "version": cls._service_version,
                "uptime_seconds": 3600,
                "memory_usage_mb": 256
            },
            "connection_pool": {
                "active": cls._connection_count,
                "idle": 10,
                "max": 20
            },
            "error_history": []
        }

        dump_file = os.path.join(diag_folder, "full_dump.json")
        with open(dump_file, 'w') as f:
            json.dump(full_dump, f, indent=2)


class ExampleDeviceCoupling:
    """
    Another example integration coupling for device diagnostics.

    This demonstrates how different integration types capture different
    diagnostic information based on their resource type.
    """

    integration_root = "devices"
    integration_section = "network"
    integration_leaf = "router"
    integration_class = "ExampleDeviceCoupling"

    # Simulated device state
    _device_name = "router-001"
    _device_ip = "192.168.1.1"
    _firmware_version = "2.1.0"

    @classmethod
    def diagnostic(cls, label: str, level: int, diag_folder: str):
        """
        Capture diagnostic information for the device.

        :param label: The diagnostic stage identifier
        :param level: The maximum diagnostic level (1-9)
        :param diag_folder: The output directory for diagnostic files
        """
        try:
            # Create device-specific subfolder
            device_diag_folder = os.path.join(diag_folder, "router")
            os.makedirs(device_diag_folder, exist_ok=True)

            # Level 1+: Device identification
            if level >= 1:
                device_info = {
                    "diagnostic_label": label,
                    "device_name": cls._device_name,
                    "device_ip": cls._device_ip,
                    "firmware_version": cls._firmware_version
                }
                with open(os.path.join(device_diag_folder, "device_info.json"), 'w') as f:
                    json.dump(device_info, f, indent=2)

            # Level 5+: Interface status
            if level >= 5:
                interface_status = {
                    "interfaces": [
                        {"name": "eth0", "status": "up", "speed": "1Gbps"},
                        {"name": "eth1", "status": "up", "speed": "1Gbps"},
                        {"name": "wlan0", "status": "down", "speed": "N/A"}
                    ]
                }
                with open(os.path.join(device_diag_folder, "interfaces.json"), 'w') as f:
                    json.dump(interface_status, f, indent=2)

            # Level 9: Full device dump
            if level >= 9:
                full_dump = {
                    "device": cls._device_name,
                    "routing_table": [
                        {"destination": "0.0.0.0/0", "gateway": "192.168.1.254", "interface": "eth0"},
                        {"destination": "192.168.1.0/24", "gateway": "0.0.0.0", "interface": "eth0"}
                    ],
                    "arp_cache": [
                        {"ip": "192.168.1.254", "mac": "00:11:22:33:44:55"}
                    ]
                }
                with open(os.path.join(device_diag_folder, "full_dump.json"), 'w') as f:
                    json.dump(full_dump, f, indent=2)

        except Exception as err:
            print(f"Warning: Device diagnostic capture failed: {err}")


def example_custom_diagnostic_capture():
    """
    Demonstrates custom diagnostic capture with example integrations.

    This example shows how the diagnostic method is called and what
    output files are created at different diagnostic levels.
    """
    print("\n--- example_custom_diagnostic_capture ---")
    print("Demonstrating custom diagnostic capture implementation.\n")

    # Create a temporary directory for diagnostic output
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Diagnostic output directory: {temp_dir}\n")

        # Simulate pre-run diagnostic capture at level 9 (maximum detail)
        print("Capturing pre-run diagnostics at level 9...")
        ExampleServiceCoupling.diagnostic(
            label=DiagnosticLabel.PRERUN_DIAGNOSTIC,
            level=9,
            diag_folder=temp_dir
        )
        ExampleDeviceCoupling.diagnostic(
            label=DiagnosticLabel.PRERUN_DIAGNOSTIC,
            level=9,
            diag_folder=temp_dir
        )

        # List created files
        print("\nCreated diagnostic files:")
        for root, dirs, files in os.walk(temp_dir):
            level = root.replace(temp_dir, '').count(os.sep)
            indent = '  ' * level
            folder_name = os.path.basename(root) or 'diagnostics'
            print(f"{indent}{folder_name}/")
            sub_indent = '  ' * (level + 1)
            for file in files:
                print(f"{sub_indent}{file}")

        # Show content of a sample file
        status_file = os.path.join(temp_dir, "example_service", "status.json")
        if os.path.exists(status_file):
            print("\nSample diagnostic file content (status.json):")
            with open(status_file, 'r') as f:
                content = json.load(f)
                print(json.dumps(content, indent=2))


def example_diagnostic_level_filtering():
    """
    Demonstrates how diagnostic level affects captured information.

    This example shows the difference in output between low and high
    diagnostic levels.
    """
    print("\n--- example_diagnostic_level_filtering ---")
    print("Demonstrating diagnostic level filtering.\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Capture at level 3 (basic only)
        level_3_dir = os.path.join(temp_dir, "level_3")
        os.makedirs(level_3_dir)
        print("Capturing at level 3 (basic)...")
        ExampleServiceCoupling.diagnostic(
            label=DiagnosticLabel.PRERUN_DIAGNOSTIC,
            level=3,
            diag_folder=level_3_dir
        )

        # Capture at level 9 (full detail)
        level_9_dir = os.path.join(temp_dir, "level_9")
        os.makedirs(level_9_dir)
        print("Capturing at level 9 (detailed)...")
        ExampleServiceCoupling.diagnostic(
            label=DiagnosticLabel.PRERUN_DIAGNOSTIC,
            level=9,
            diag_folder=level_9_dir
        )

        # Compare file counts
        level_3_files = []
        for root, dirs, files in os.walk(level_3_dir):
            level_3_files.extend(files)

        level_9_files = []
        for root, dirs, files in os.walk(level_9_dir):
            level_9_files.extend(files)

        print(f"\nLevel 3 files ({len(level_3_files)}): {level_3_files}")
        print(f"Level 9 files ({len(level_9_files)}): {level_9_files}")
        print("\nHigher levels capture more detailed diagnostic information.")


def main():
    """
    Main entry point for the custom diagnostic implementation examples.

    Run this script directly to see the examples in action:

        python debug_diagnostics_custom.py
    """
    print("=" * 70)
    print("Custom Integration Diagnostic Implementation Examples")
    print("=" * 70)

    example_custom_diagnostic_capture()
    example_diagnostic_level_filtering()

    print("\n" + "=" * 70)
    print("All custom diagnostic examples completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
