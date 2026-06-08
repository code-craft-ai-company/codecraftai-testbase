"""
    .. module:: ccai.testbase.results.recorders
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for recorders.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.testbase.results.recorders.resultrecorder import ResultRecorder
from ccai.testbase.results.recorders.jsonresultrecorder import JsonResultRecorder, JsonResultEncoder
from ccai.testbase.results.recorders.xmlresultrecorder import XmlResultRecorder
from ccai.testbase.results.recorders.csvresultrecorder import CsvResultRecorder

# NOTE: StreamingResultRecorder relocated to codecraftai-integration-runtime (Phase 3 results split):
# ccai.integrationruntime.results.recorders.streamingresultrecorder. It depends on the streaming
# transport (also relocated), which the near-standalone testbase framework deliberately omits.

__all__ = [
    "ResultRecorder",
    "JsonResultRecorder",
    "JsonResultEncoder",
    "XmlResultRecorder",
    "CsvResultRecorder"
]


