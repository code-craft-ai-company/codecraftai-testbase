"""
.. module:: breakpoints
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Declares the wellknown breakpoints available in the 'testbase' application.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>

This module defines the ``WELLKNOWN_BREAKPOINTS`` enumeration, which provides
predefined breakpoint locations within the test execution lifecycle. These
breakpoints allow developers to pause test execution at key stages for
debugging purposes.

Example Usage::

    from ccai.testbase.breakpoints import WELLKNOWN_BREAKPOINTS

    # Check if a breakpoint is enabled
    if "test-discovery" in configured_breakpoints:
        print("Test discovery breakpoint is enabled")

    # Use enum member for comparison
    if WELLKNOWN_BREAKPOINTS.TESTRUN_START in configured_breakpoints:
        print("Testrun start breakpoint is enabled")

    # String comparison works due to str inheritance
    assert WELLKNOWN_BREAKPOINTS.TEST_DISCOVERY == "test-discovery"

"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from enum import Enum


class WELLKNOWN_BREAKPOINTS(str, Enum):
    """
    Enumeration of well-known breakpoint locations within the test execution lifecycle.

    This enum inherits from both ``str`` and ``Enum``, allowing enum members to be
    compared directly with string values. This design enables flexible breakpoint
    configuration via CLI options while maintaining type safety in code.

    The breakpoints defined here represent key stages in test execution where
    developers may want to pause for debugging:

    - **TEST_DISCOVERY**: Pause during the test discovery phase, before test
      collection begins. Useful for debugging test collection issues.
    - **TESTRUN_START**: Pause at the start of test execution, at the entry
      point of the session() method in the sequence document. Useful for
      debugging test setup and initialization.

    Attributes:
        TEST_DISCOVERY (str): Breakpoint identifier for the test discovery phase.
            Value: ``"test-discovery"``
        TESTRUN_START (str): Breakpoint identifier for the start of test execution.
            Value: ``"testrun-start"``

    Example::

        from ccai.testbase.breakpoints import WELLKNOWN_BREAKPOINTS

        # Access enum members as class attributes
        bp = WELLKNOWN_BREAKPOINTS.TEST_DISCOVERY
        print(bp)  # Output: test-discovery

        # String comparison works due to str inheritance
        assert WELLKNOWN_BREAKPOINTS.TESTRUN_START == "testrun-start"

        # Use in conditional checks
        configured = ["test-discovery", "testrun-start"]
        if WELLKNOWN_BREAKPOINTS.TEST_DISCOVERY in configured:
            print("Discovery breakpoint enabled")

        # Iterate over all breakpoints
        for bp in WELLKNOWN_BREAKPOINTS:
            print(f"Breakpoint: {bp.name} = {bp.value}")

    See Also:
        - :mod:`ccai.xmodules.debugging`: Core debugging infrastructure
        - :class:`ccai.testbase.cli.options.DiagnosticOptionGroup`: CLI options for debugging
    """

    TEST_DISCOVERY = "test-discovery"
    """
    Breakpoint that pauses execution during the test discovery phase.

    When enabled, this breakpoint triggers before test collection begins,
    allowing developers to debug issues related to test discovery, module
    loading, and test registration.

    CLI Usage::

        testbase testing run --root ./tests --debugger pdb --breakpoint test-discovery
    """

    TESTRUN_START = "testrun-start"
    """
    Breakpoint that pauses execution at the start of test execution.

    When enabled, this breakpoint triggers at the entry point of the
    session() method in the generated test sequence document, before
    the session scope context is entered. This is useful for debugging
    test initialization and setup.

    CLI Usage::

        testbase testing run --root ./tests --debugger debugpy --breakpoint testrun-start
    """
