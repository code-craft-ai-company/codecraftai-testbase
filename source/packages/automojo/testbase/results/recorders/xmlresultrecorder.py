"""
    .. module:: automojo.testbase.results.recorders.xmlresultrecorder
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for XML result recording.

    .. moduleauthor:: AutomationX
"""

__author__ = "AutomationX"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Any, Optional

import xml.etree.ElementTree as ET
from xml.dom import minidom

from datetime import datetime

from automojo.xmodules.jsos import CHAR_RECORD_SEPERATOR

from automojo.testbase.results.exceptions import ResultRecordingError
from automojo.testbase.results.model.buildinfo import BuildInfo
from automojo.testbase.results.model.jobinfo import JobInfo
from automojo.testbase.results.model.pipelineinfo import PipelineInfo
from automojo.testbase.results.model.renderinfo import RenderInfo

from automojo.testbase.results.model.resultcode import ResultCode
from automojo.testbase.results.model.resultnode import ResultNode
from automojo.testbase.results.model.resulttype import ResultType

from automojo.testbase.results.recorders.resultrecorder import ResultRecorder


def _datetime_to_str(dt: datetime) -> str:
    """
        Converts a datetime object to an ISO format string.
        
        :param dt: The datetime object to convert.
        :returns: ISO format string representation.
    """
    if dt is None:
        return ""
    return dt.isoformat()


def _dict_to_xml_element(data: dict, tag_name: str) -> ET.Element:
    """
        Converts a dictionary to an XML element recursively.
        
        :param data: The dictionary to convert.
        :param tag_name: The tag name for the root element.
        :returns: An XML Element representing the dictionary.
    """
    element = ET.Element(tag_name)
    
    for key, value in data.items():
        child = ET.SubElement(element, str(key))
        if isinstance(value, dict):
            # Recursively convert nested dictionaries
            for sub_key, sub_value in value.items():
                sub_child = ET.SubElement(child, str(sub_key))
                sub_child.text = _value_to_str(sub_value)
        elif isinstance(value, list):
            # Convert lists to repeated elements
            for item in value:
                if isinstance(item, dict):
                    item_elem = _dict_to_xml_element(item, "item")
                    child.append(item_elem)
                else:
                    item_elem = ET.SubElement(child, "item")
                    item_elem.text = _value_to_str(item)
        else:
            child.text = _value_to_str(value)
    
    return element


def _value_to_str(value: Any) -> str:
    """
        Converts a value to a string representation for XML.
        
        :param value: The value to convert.
        :returns: String representation of the value.
    """
    if value is None:
        return ""
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, bool):
        return str(value).lower()
    else:
        return str(value)


def _prettify_xml(element: ET.Element) -> str:
    """
        Returns a pretty-printed XML string for the Element.
        
        :param element: The XML element to prettify.
        :returns: A formatted XML string with proper indentation.
    """
    rough_string = ET.tostring(element, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")


class XmlResultRecorder(ResultRecorder):
    """
        Records test results in XML format.

        The :class:`XmlResultRecorder` is a concrete implementation of
        :class:`ResultRecorder` that writes test results to XML files. It produces
        three main output files:

        1. **Summary File** (testsummary.xml): Contains run metadata, timing, and
           result counts in XML format.

        2. **Stream Results File** (testresults_stream.xml): Contains individual
           result records. Records are written as tests execute, enabling real-time
           monitoring.

        3. **Consolidated Results File** (testresults.xml): Contains the complete
           result tree in a single XML document.

        Context Manager Lifecycle
        -------------------------
        The XmlResultRecorder inherits the context manager pattern from ResultRecorder:

        1. **Entry (__enter__)**: Initializes output environment, writes initial
           summary, opens stream file
        2. **Active Recording**: preview() and record() write to stream file
        3. **Exit (__exit__)**: Finalizes counts, writes final summary, closes files

        Thread Safety
        -------------
        The XmlResultRecorder is thread-safe for concurrent recording:

        - The record() method uses locking when updating result counters
        - Multiple threads can call record() concurrently without data corruption
        - The stream file writes are serialized through the lock
    """

    def __init__(self, *, runid: str, start: datetime, render_info: RenderInfo,
                 apod: Optional[str] = None, build_info: Optional[BuildInfo] = None,
                 pipeline_info: Optional[PipelineInfo] = None, job_info: Optional[JobInfo] = None):
        """
            Initializes the :class:`XmlResultRecorder` for recording test results.

            :param runid: The uuid string that identifies a set of test results.
            :param start: The date and time of the start of the test run.
            :param render_info: A :class:`RenderInfo` instance containing output file paths.
            :param apod: Optional name of an automation pod.
            :param build_info: Optional :class:`BuildInfo` instance.
            :param pipeline_info: Optional :class:`PipelineInfo` instance.
            :param job_info: Optional :class:`JobInfo` instance.

            :returns: None
        """
        super(XmlResultRecorder, self).__init__(runid=runid, start=start, render_info=render_info, apod=apod,
                                                build_info=build_info, pipeline_info=pipeline_info, job_info=job_info)
        return


    def preview(self, result: ResultNode):
        """
            Writes a preview of a result to the stream file in XML format.

            This method serializes the result as an XML preview (without detail section)
            and writes it to the stream results file. The preview is preceded by an
            ASCII record separator character.

            :param result: A :class:`ResultNode` object to preview.

            :returns: None
        """
        result_dict = result.as_dict(is_preview=True)
        xml_element = _dict_to_xml_element(result_dict, "result")
        xml_str = _prettify_xml(xml_element)

        self._rout.write(CHAR_RECORD_SEPERATOR)
        self._rout.write(xml_str)
        self._rout.flush()

        self.catalog_output_directory()

        return


    def record(self, result: ResultNode):
        """
            Records a final result entry to the stream file in XML format.

            This method serializes the complete result (with detail section) and
            writes it to the stream results file. Result counters are updated based
            on the result type and code.

            Thread Safety:
                This method is thread-safe. Counter updates are performed within
                a lock-protected section.

            :param result: A :class:`ResultNode` object to record.

            :returns: None
        """
        result_dict = result.as_dict(is_preview=False)
        xml_element = _dict_to_xml_element(result_dict, "result")
        xml_str = _prettify_xml(xml_element)

        self._rout.write(CHAR_RECORD_SEPERATOR)
        self._rout.write(xml_str)
        self._rout.flush()

        self._lock.acquire()
        try:
            if result.result_type == ResultType.TEST:
                self._total_count += 1

                result_code = result.result_code
                if result_code == ResultCode.PASSED:
                    self._pass_count += 1
                elif result_code == ResultCode.ERRORED:
                    self._error_count += 1
                elif result_code == ResultCode.FAILED:
                    self._failure_count += 1
                elif result_code == ResultCode.SKIPPED:
                    self._skip_count += 1
                else:
                    self._unknown_count += 1
        finally:
            self._lock.release()

        self.catalog_output_directory()

        return


    def update_summary(self):
        """
            Writes the current summary state to the summary XML file.

            This method serializes the internal summary dictionary to XML and
            writes it to the configured summary_filename.

            :returns: None

            :raises: ResultRecordingError if the summary file cannot be written.
        """
        summary_filename = self._render_info.summary_filename
        
        try:
            xml_element = _dict_to_xml_element(self._summary, "summary")
            xml_str = _prettify_xml(xml_element)
            
            with open(summary_filename, 'w') as sout:
                sout.write(xml_str)
        except OSError as err:
            errmsg = f"Failed to write summary to '{summary_filename}'."
            raise ResultRecordingError(
                errmsg,
                file_path=summary_filename,
                operation="writing summary XML",
                original_error=err
            ) from err

        self.catalog_output_directory()

        return


    def write_consolidated_results(self, root_node: dict):
        """
            Writes the consolidated results tree to the consolidated results XML file.

            This method serializes the complete result tree to XML and writes it
            to the configured consolidated_results_filename.

            :param root_node: A dictionary representing the root of the consolidated
                              result tree.

            :returns: None

            :raises: ResultRecordingError if the consolidated results file cannot be written.
        """
        consolidated_filename = self._render_info.consolidated_results_filename
        
        try:
            xml_element = _dict_to_xml_element(root_node, "testresults")
            xml_str = _prettify_xml(xml_element)
            
            with open(consolidated_filename, 'w+') as rout:
                rout.write(xml_str)
        except OSError as err:
            errmsg = f"Failed to write consolidated results to '{consolidated_filename}'."
            raise ResultRecordingError(
                errmsg,
                file_path=consolidated_filename,
                operation="writing consolidated results XML",
                original_error=err
            ) from err

        self.catalog_output_directory()

        return
