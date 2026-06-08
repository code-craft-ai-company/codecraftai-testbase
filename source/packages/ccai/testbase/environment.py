"""
    .. module:: ccai.testbase.environment
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Dependency-free access to the small set of environment-sourced knobs that the
               standalone ``testbase`` core needs.

    ``testbase`` is a near-standalone single-host test framework and must not depend on
    ``codecraftai-runtime``, ``codecraftai-this-app``, or ``codecraftai-configuration``. The richer
    ``RuntimeVariables`` descriptor set (now owned by ``ccai.thisapp``) is used only by the
    integration layer (``codecraftai-integration-runtime`` / ``IntegratedTestJob``).

    This module reads the handful of CORE test-execution knobs directly from ``os.environ`` so
    the framework has no dependency on the runtime/this-app variable machinery. The integration
    layer may still set these same environment variables (its richer machinery resolves them
    from files + the environment), so behaviour is consistent whether ``testbase`` runs standalone
    or under the integration runtime.

    Because the integration machinery stores variable values into ``os.environ`` as strings, an
    *unset* value is represented by the literal string ``"None"`` (or ``"null"`` / empty). The
    accessors here treat those sentinels as absent.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from typing import List, Optional

import os


TRUE_TOKENS = ("1", "true", "yes", "on")

NONE_TOKENS = ("", "none", "null")


def _lookup(name: str) -> Optional[str]:
    """
        Reads an environment variable, treating the unset sentinels (``""``, ``"None"``,
        ``"null"``, case-insensitive) as absent.

        :param name: The environment variable name to read.

        :returns: The trimmed value, or ``None`` when unset or set to a sentinel.
    """
    raw_value = os.environ.get(name, None)
    if raw_value is None:
        return None

    trimmed = raw_value.strip()
    if trimmed.lower() in NONE_TOKENS:
        return None

    return trimmed


def get_testroot() -> Optional[str]:
    """
        Returns the configured test root directory, if any.

        :returns: The value of ``AM_TESTROOT`` or ``None`` when it is not set.
    """
    rtnval = _lookup("AM_TESTROOT")
    return rtnval


def get_output_directory() -> Optional[str]:
    """
        Returns the configured output directory, if any.

        :returns: The value of ``AM_OUTPUT_DIRECTORY`` or ``None`` when it is not set.
    """
    rtnval = _lookup("AM_OUTPUT_DIRECTORY")
    return rtnval


def get_run_id() -> Optional[str]:
    """
        Returns the run identifier from the environment, if any.

        :returns: The value of ``AM_RUN_ID`` or ``None`` when it is not set.
    """
    rtnval = _lookup("AM_RUN_ID")
    return rtnval


def get_debugger_name() -> Optional[str]:
    """
        Returns the configured debugger name, if any.

        :returns: The value of ``AM_DEBUG_DEBUGGER`` or ``None`` when it is not set.
    """
    rtnval = _lookup("AM_DEBUG_DEBUGGER")
    return rtnval


def get_debug_breakpoints() -> Optional[List[str]]:
    """
        Returns the list of configured well-known breakpoints, if any.

        The environment value is a comma-separated list of breakpoint names.

        :returns: A list of breakpoint name strings, or ``None`` when not configured.
    """
    raw_value = _lookup("AM_DEBUG_BREAKPOINTS")
    if raw_value is None:
        return None

    parts = raw_value.split(",")
    breakpoints = []
    for part in parts:
        trimmed = part.strip()
        if len(trimmed) > 0:
            breakpoints.append(trimmed)

    return breakpoints


def diagnostics_prerun_enabled() -> bool:
    """
        Indicates whether pre-run diagnostic capture is enabled.

        :returns: ``True`` when ``AM_DIAGNOSTICS_PRERUN`` is set to a truthy token.
    """
    raw_value = _lookup("AM_DIAGNOSTICS_PRERUN")
    if raw_value is None:
        return False

    rtnval = raw_value.lower() in TRUE_TOKENS
    return rtnval


def diagnostics_postrun_enabled() -> bool:
    """
        Indicates whether post-run diagnostic capture is enabled.

        :returns: ``True`` when ``AM_DIAGNOSTICS_POSTRUN`` is set to a truthy token.
    """
    raw_value = _lookup("AM_DIAGNOSTICS_POSTRUN")
    if raw_value is None:
        return False

    rtnval = raw_value.lower() in TRUE_TOKENS
    return rtnval


def get_testrun_timeout() -> Optional[int]:
    """
        Returns the configured test-run timeout in seconds, if any.

        :returns: An integer number of seconds, or ``None`` when not configured.
        :raises ValueError: When ``AM_TESTRUN_TIMEOUT`` is set to a non-sentinel, non-integer value.
    """
    raw_value = _lookup("AM_TESTRUN_TIMEOUT")
    if raw_value is None:
        return None

    timeout_seconds = int(raw_value)
    return timeout_seconds
