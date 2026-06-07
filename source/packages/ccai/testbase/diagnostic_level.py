"""
.. module:: ccai.testbase.diagnostic_level
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for managing diagnostic level configuration.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>

This module provides functions for configuring and retrieving the diagnostic level
used during diagnostic capture operations. The diagnostic level controls the verbosity
of diagnostic information captured by integration couplings.

Diagnostic Levels:
    * Levels 1-3: Basic diagnostic information (quick status checks)
    * Levels 4-6: Standard diagnostic information (normal debugging)
    * Levels 7-9: Detailed diagnostic information (deep investigation)

The default diagnostic level is 9 (maximum detail) when not explicitly configured.

Example Usage::

    from ccai.testbase.diagnostic_level import (
        get_diagnostic_level,
        set_diagnostic_level,
        reset_diagnostic_level,
        DEFAULT_DIAGNOSTIC_LEVEL
    )

    # Get the current diagnostic level
    level = get_diagnostic_level()

    # Set a custom diagnostic level
    set_diagnostic_level(5)

    # Reset to default
    reset_diagnostic_level()

See Also:
    - :class:`ccai.testbase.cli.options.DiagnosticOptionGroup`: CLI options for
      configuring diagnostic level
    - :meth:`ccai.testbase.sequencing.testsequencer.TestSequencer.diagnostic_capture_pre_testrun`:
      Method that uses the diagnostic level during capture
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


# Default diagnostic level (maximum detail)
DEFAULT_DIAGNOSTIC_LEVEL: int = 9

# Module-level storage for the configured diagnostic level
_configured_diagnostic_level: int = DEFAULT_DIAGNOSTIC_LEVEL


def get_diagnostic_level() -> int:
    """
    Get the currently configured diagnostic level.

    The diagnostic level controls the verbosity of diagnostic information captured
    by integration couplings during pre-run and post-run diagnostic capture.

    :returns: The currently configured diagnostic level (1-9). Returns the default
        level (9) if not explicitly configured.

    Example Usage::

        from ccai.testbase.diagnostic_level import get_diagnostic_level

        level = get_diagnostic_level()
        print(f"Current diagnostic level: {level}")
    """
    return _configured_diagnostic_level


def set_diagnostic_level(level: int) -> None:
    """
    Set the diagnostic level for diagnostic capture operations.

    This function configures the diagnostic level that will be used when capturing
    diagnostic information from integration couplings. The level controls the
    verbosity of captured diagnostics.

    :param level: The diagnostic level to set (1-9). Higher levels indicate more
        detailed diagnostic information.

        * Levels 1-3: Basic diagnostic information (quick status checks)
        * Levels 4-6: Standard diagnostic information (normal debugging)
        * Levels 7-9: Detailed diagnostic information (deep investigation)

    :raises ValueError: If the level is not an integer between 1 and 9.

    Example Usage::

        from ccai.testbase.diagnostic_level import set_diagnostic_level

        # Set to basic diagnostics
        set_diagnostic_level(3)

        # Set to standard diagnostics
        set_diagnostic_level(5)

        # Set to detailed diagnostics
        set_diagnostic_level(9)
    """
    global _configured_diagnostic_level

    if not isinstance(level, int):
        raise ValueError(f"Diagnostic level must be an integer, got: {type(level).__name__}")

    if level < 1 or level > 9:
        raise ValueError(f"Diagnostic level must be between 1 and 9, got: {level}")

    _configured_diagnostic_level = level


def reset_diagnostic_level() -> None:
    """
    Reset the diagnostic level to the default value (9).

    This function resets the diagnostic level to the default maximum detail level.
    Useful for cleanup between test runs or when resetting configuration state.

    :returns: None

    Example Usage::

        from ccai.testbase.diagnostic_level import reset_diagnostic_level

        # Reset to default level
        reset_diagnostic_level()
    """
    global _configured_diagnostic_level
    _configured_diagnostic_level = DEFAULT_DIAGNOSTIC_LEVEL


def is_basic_level(level: int = None) -> bool:
    """
    Check if the diagnostic level is in the basic range (1-3).

    :param level: The level to check. If None, uses the currently configured level.

    :returns: True if the level is in the basic range (1-3), False otherwise.

    Example Usage::

        from ccai.testbase.diagnostic_level import is_basic_level

        if is_basic_level():
            # Capture only basic diagnostics
            pass
    """
    if level is None:
        level = _configured_diagnostic_level
    return 1 <= level <= 3


def is_standard_level(level: int = None) -> bool:
    """
    Check if the diagnostic level is in the standard range (4-6).

    :param level: The level to check. If None, uses the currently configured level.

    :returns: True if the level is in the standard range (4-6), False otherwise.

    Example Usage::

        from ccai.testbase.diagnostic_level import is_standard_level

        if is_standard_level():
            # Capture standard diagnostics
            pass
    """
    if level is None:
        level = _configured_diagnostic_level
    return 4 <= level <= 6


def is_detailed_level(level: int = None) -> bool:
    """
    Check if the diagnostic level is in the detailed range (7-9).

    :param level: The level to check. If None, uses the currently configured level.

    :returns: True if the level is in the detailed range (7-9), False otherwise.

    Example Usage::

        from ccai.testbase.diagnostic_level import is_detailed_level

        if is_detailed_level():
            # Capture detailed diagnostics
            pass
    """
    if level is None:
        level = _configured_diagnostic_level
    return 7 <= level <= 9
