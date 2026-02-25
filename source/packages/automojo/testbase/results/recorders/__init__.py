"""
    .. module:: automojo.testbase.results.recorders
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for recorders.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.testbase.results.recorders.resultrecorder import ResultRecorder
from automojo.testbase.results.recorders.jsonresultrecorder import JsonResultRecorder, JsonResultEncoder
from automojo.testbase.results.recorders.xmlresultrecorder import XmlResultRecorder
from automojo.testbase.results.recorders.csvresultrecorder import CsvResultRecorder
from automojo.testbase.results.recorders.streamingresultrecorder import StreamingResultRecorder

__all__ = [
    "ResultRecorder",
    "JsonResultRecorder",
    "JsonResultEncoder",
    "XmlResultRecorder",
    "CsvResultRecorder",
    "StreamingResultRecorder"
]


