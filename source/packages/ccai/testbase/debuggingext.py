"""
.. module:: debuggingext
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Extended debugging support with configurable port options.

.. moduleauthor:: CodeCraftX

This module provides extended debugging functionality that wraps the core
debugging module from ccai.xmodules.debugging. It adds support for:

- Configurable debug ports via CLI options
- Port range support for multiple debug sessions
- Port conflict detection
- Breakpoint logging with configurable log levels

The functions in this module are designed to be drop-in replacements for
the core debugging functions when custom port configuration is needed.

Example Usage::

    from ccai.testbase.debuggingext import (
        debugger_wellknown_breakpoint_code_append_with_port,
        debugger_wellknown_breakpoint_entry_with_port
    )

    # Generate breakpoint code with custom port
    code_lines = []
    debugger_wellknown_breakpoint_code_append_with_port(
        debugger="debugpy",
        breakpoint_name="testrun-start",
        code_lines=code_lines,
        current_indent="    ",
        configured_breakpoints=["testrun-start"],
        debug_port=5680
    )

"""

__author__ = "CodeCraftX"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import List, Optional

import logging

from ccai.xmodules.debugging import (
    DEBUGGER,
    in_vscode_debugger,
)

from ccai.testbase.debugports import get_configured_debug_port

from ccai.testbase.debuglogging import (
    log_breakpoint_triggered,
    log_debugger_connection,
    log_debug_session_start
)


logger = logging.getLogger(__name__)


def debugger_wellknown_breakpoint_entry_with_port(
    debugger: str,
    breakpoint_name: str,
    configured_breakpoints: List[str],
    debug_port: Optional[int] = None
) -> None:
    """
    Triggers a breakpoint if the named well-known breakpoint is enabled,
    with support for custom debug port configuration.

    This function extends the core debugger_wellknown_breakpoint_entry function
    by allowing a custom debug port to be specified for debugpy connections.
    It also logs breakpoint trigger events and debugger connection events.

    :param debugger: The name of the debugger to use when a breakpoint is hit.
        Valid values: 'pdb' or 'debugpy'.
    :param breakpoint_name: Key identifying the breakpoint (e.g., 'testrun-start').
    :param configured_breakpoints: A list of breakpoints that have been configured by the user.
    :param debug_port: Optional custom port for debugpy. If None, uses the globally configured port
        or DEFAULT_DEBUG_PORT (5678).

    Example::

        # Trigger breakpoint with default port
        debugger_wellknown_breakpoint_entry_with_port(
            debugger="debugpy",
            breakpoint_name="testrun-start",
            configured_breakpoints=["testrun-start"]
        )

        # Trigger breakpoint with custom port
        debugger_wellknown_breakpoint_entry_with_port(
            debugger="debugpy",
            breakpoint_name="testrun-start",
            configured_breakpoints=["testrun-start"],
            debug_port=5680
        )
    """
    # Use provided port, or fall back to globally configured port, or default
    if debug_port is None:
        debug_port = get_configured_debug_port()

    if breakpoint_name in configured_breakpoints:
        # Log the debug session start
        log_debug_session_start(
            debugger=debugger,
            breakpoint_name=breakpoint_name,
            port=debug_port if debugger == DEBUGGER.DEBUGPY else None
        )

        if debugger == DEBUGGER.PDB:
            # PDB Backend: Use Python's built-in debugger for terminal debugging
            # Log the breakpoint trigger event
            log_breakpoint_triggered(
                breakpoint_name=breakpoint_name,
                debugger=debugger
            )

            import pdb
            pdb.set_trace()
        elif debugger == DEBUGGER.DEBUGPY:
            # DEBUGPY Backend: Use remote debugging protocol for IDE integration
            logger.info(f"Waiting for debugger on port={debug_port}")

            # Check if we're already running under VS Code's debugger
            invscode = in_vscode_debugger()

            import debugpy
            if invscode:
                # Log the listening event
                log_debugger_connection(
                    event="listening",
                    debugger=debugger,
                    port=debug_port
                )

                # When running under VS Code, set up the remote debugging endpoint.
                # Bind loopback-only: debugpy has no authentication and exposes an
                # arbitrary-code-execution surface, so it must not listen on all interfaces.
                debugpy.listen(("127.0.0.1", debug_port))

                # Log the waiting event
                log_debugger_connection(
                    event="waiting",
                    debugger=debugger,
                    port=debug_port
                )

                debugpy.wait_for_client()

                # Log the connected event
                log_debugger_connection(
                    event="connected",
                    debugger=debugger,
                    port=debug_port
                )

            # Log the breakpoint trigger event
            log_breakpoint_triggered(
                breakpoint_name=breakpoint_name,
                debugger=debugger,
                port=debug_port
            )

            # Trigger the actual breakpoint
            debugpy.breakpoint()

    return


def debugger_wellknown_breakpoint_code_append_with_port(
    debugger: str,
    breakpoint_name: str,
    code_lines: list,
    current_indent: str,
    configured_breakpoints: List[str],
    debug_port: Optional[int] = None
) -> None:
    """
    Appends source lines that trigger a well-known breakpoint when enabled,
    with support for custom debug port configuration.

    This function extends the core debugger_wellknown_breakpoint_code_append function
    by allowing a custom debug port to be specified in the generated code.
    It also logs breakpoint code generation events.

    :param debugger: The name of the debugger to use when a breakpoint is hit.
        Valid values: 'pdb' or 'debugpy'.
    :param breakpoint_name: Identifier for the breakpoint (e.g., 'testrun-start').
    :param code_lines: List of lines being emitted.
    :param current_indent: Current indentation prefix for the new lines.
    :param configured_breakpoints: A list of breakpoints that have been configured by the user.
    :param debug_port: Optional custom port for debugpy. If None, uses the globally configured port
        or DEFAULT_DEBUG_PORT (5678).

    Example::

        code_lines = []

        # Generate code with default port
        debugger_wellknown_breakpoint_code_append_with_port(
            debugger="debugpy",
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="    ",
            configured_breakpoints=["testrun-start"]
        )

        # Generate code with custom port
        debugger_wellknown_breakpoint_code_append_with_port(
            debugger="debugpy",
            breakpoint_name="testrun-start",
            code_lines=code_lines,
            current_indent="    ",
            configured_breakpoints=["testrun-start"],
            debug_port=5680
        )
    """
    # Use provided port, or fall back to globally configured port, or default
    if debug_port is None:
        debug_port = get_configured_debug_port()

    if breakpoint_name in configured_breakpoints:
        if debugger == DEBUGGER.PDB:
            # PDB Code Generation Pattern:
            # Generate code for terminal-based debugging using Python's built-in debugger
            code_lines.append('')
            code_lines.append('{}# The debug flag was passed on the commandline so we break here.'.format(current_indent))
            # Add logging import and call for breakpoint trigger
            code_lines.append('{}from ccai.testbase.debuglogging import log_breakpoint_triggered'.format(current_indent))
            code_lines.append('{}log_breakpoint_triggered(breakpoint_name="{}", debugger="{}")'.format(
                current_indent, breakpoint_name, debugger))
            code_lines.append('{}import pdb'.format(current_indent))
            code_lines.append('{}pdb.set_trace()'.format(current_indent))

            # Log that we generated breakpoint code
            log_breakpoint_triggered(
                breakpoint_name=breakpoint_name,
                debugger=debugger
            )
        elif debugger == DEBUGGER.DEBUGPY:
            # DEBUGPY Code Generation Pattern:
            # Generate code for remote/IDE debugging using debugpy protocol with custom port

            # Check VS Code status at code generation time
            invscode = in_vscode_debugger()

            code_lines.append('')
            code_lines.append('{}# The remote debug flag was passed on the commandline so we break here.'.format(current_indent))
            # Add logging imports
            code_lines.append('{}from ccai.testbase.debuglogging import log_breakpoint_triggered, log_debugger_connection'.format(current_indent))
            code_lines.append('{}import debugpy'.format(current_indent))
            if invscode:
                # Include the remote debugging setup calls with custom port and logging
                code_lines.append('{}log_debugger_connection(event="listening", debugger="{}", port={})'.format(
                    current_indent, debugger, debug_port))
                code_lines.append('{}debugpy.listen(("127.0.0.1", {}))'.format(current_indent, debug_port))
                code_lines.append('{}log_debugger_connection(event="waiting", debugger="{}", port={})'.format(
                    current_indent, debugger, debug_port))
                code_lines.append('{}debugpy.wait_for_client()'.format(current_indent))
                code_lines.append('{}log_debugger_connection(event="connected", debugger="{}", port={})'.format(
                    current_indent, debugger, debug_port))
            code_lines.append('{}log_breakpoint_triggered(breakpoint_name="{}", debugger="{}", port={})'.format(
                current_indent, breakpoint_name, debugger, debug_port))
            code_lines.append('{}debugpy.breakpoint()'.format(current_indent))

            # Log to inform user about the debug port
            logger.info(f"Waiting for debugger on port={debug_port}")

            # Log that we generated breakpoint code
            log_breakpoint_triggered(
                breakpoint_name=breakpoint_name,
                debugger=debugger,
                port=debug_port
            )

    return
