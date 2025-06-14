"""
    .. module:: automojo.testbase.diagnostics
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for diagnostics.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


class DiagnosticLabel:
    PRERUN_DIAGNOSTIC = "prerun-diagnostic"
    POSTRUN_DIAGNOSTIC = "postrun-diagnostic"


class RuntimeConfigPaths:
    DIAGNOSTIC_PRERUN = "/configuration/runtime/diagnostics/prerun-diagnostic"
    DIAGNOSTIC_POSTRUN = "/configuration/runtime/diagnostics/postrun-diagnostic"
