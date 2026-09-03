"""
    .. module:: ccai.testbase.results.recorders.csvresultrecorder
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for CSV result recording.

    .. moduleauthor:: CodeCraftX
"""

__author__ = "CodeCraftX"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, List, Optional

import csv
import json

from datetime import datetime

from ccai.xmodules.jsos import CHAR_RECORD_SEPERATOR

from ccai.testbase.results.exceptions import ResultRecordingError
from ccai.testbase.results.model.buildinfo import BuildInfo
from ccai.testbase.results.model.jobinfo import JobInfo
from ccai.testbase.results.model.pipelineinfo import PipelineInfo
from ccai.testbase.results.model.renderinfo import RenderInfo

from ccai.testbase.results.model.resultcode import ResultCode
from ccai.testbase.results.model.resultnode import ResultNode
from ccai.testbase.results.model.resulttype import ResultType

from ccai.testbase.results.recorders.resultrecorder import ResultRecorder


# CSV column headers for result records
RESULT_CSV_HEADERS = [
    "name",
    "instance",
    "parent",
    "rtype",
    "result",
    "start",
    "stop",
    "errors",
    "failures",
    "warnings"
]

# CSV column headers for summary records
SUMMARY_CSV_HEADERS = [
    "version",
    "title",
    "runid",
    "start",
    "stop",
    "result",
    "apod",
    "errors",
    "failed",
    "skipped",
    "passed",
    "total",
    "build_branch",
    "build_build",
    "build_flavor",
    "build_release",
    "build_url",
    "pipeline_id",
    "pipeline_name",
    "pipeline_instance",
    "job_id",
    "job_name",
    "job_type",
    "job_owner"
]


def _datetime_to_str(dt: datetime) -> str:
    """
        Converts a datetime object to an ISO format string.
        
        :param dt: The datetime object to convert.
        :returns: ISO format string representation.
    """
    if dt is None:
        return ""
    return dt.isoformat()


def _value_to_csv_str(value: Any) -> str:
    """
        Converts a value to a string representation for CSV.
        
        :param value: The value to convert.
        :returns: String representation of the value.
    """
    if value is None:
        return ""
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, (list, dict)):
        return json.dumps(value)
    elif isinstance(value, bool):
        return str(value).lower()
    else:
        return str(value)


def _result_dict_to_csv_row(result_dict: dict) -> List[str]:
    """
        Converts a result dictionary to a CSV row.
        
        :param result_dict: The result dictionary to convert.
        :returns: A list of string values for the CSV row.
    """
    row = []
    for header in RESULT_CSV_HEADERS:
        if header in result_dict:
            value = result_dict[header]
            row.append(_value_to_csv_str(value))
        elif header == "errors" and "detail" in result_dict:
            row.append(_value_to_csv_str(result_dict["detail"].get("errors", [])))
        elif header == "failures" and "detail" in result_dict:
            row.append(_value_to_csv_str(result_dict["detail"].get("failures", [])))
        elif header == "warnings" and "detail" in result_dict:
            row.append(_value_to_csv_str(result_dict["detail"].get("warnings", [])))
        else:
            row.append("")
    return row


class CsvResultRecorder(ResultRecorder):
    """
        Records test results in CSV format.

        The :class:`CsvResultRecorder` is a concrete implementation of
        :class:`ResultRecorder` that writes test results to CSV files. It produces
        three main output files:

        1. **Summary File** (testsummary.csv): Contains run metadata, timing, and
           result counts in CSV format with a single data row.

        2. **Stream Results File** (testresults_stream.csv): Contains individual
           result records as CSV rows. Records are written as tests execute.

        3. **Consolidated Results File** (testresults.csv): Contains all results
           in a flat CSV format (hierarchical structure is flattened).

        CSV Format Notes
        ----------------
        - The CSV format is inherently flat, so hierarchical result structures
          are flattened when written.
        - Complex fields (errors, failures, warnings) are serialized as JSON
          strings within CSV cells.
        - The stream file includes a header row followed by data rows.

        Context Manager Lifecycle
        -------------------------
        The CsvResultRecorder inherits the context manager pattern from ResultRecorder:

        1. **Entry (__enter__)**: Initializes output environment, writes initial
           summary, opens stream file with CSV header
        2. **Active Recording**: preview() and record() write CSV rows
        3. **Exit (__exit__)**: Finalizes counts, writes final summary, closes files

        Thread Safety
        -------------
        The CsvResultRecorder is thread-safe for concurrent recording:

        - The record() method uses locking when updating result counters
        - Multiple threads can call record() concurrently without data corruption
    """

    def __init__(self, *, runid: str, start: datetime, render_info: RenderInfo,
                 apod: Optional[str] = None, build_info: Optional[BuildInfo] = None,
                 pipeline_info: Optional[PipelineInfo] = None, job_info: Optional[JobInfo] = None):
        """
            Initializes the :class:`CsvResultRecorder` for recording test results.

            :param runid: The uuid string that identifies a set of test results.
            :param start: The date and time of the start of the test run.
            :param render_info: A :class:`RenderInfo` instance containing output file paths.
            :param apod: Optional name of an automation pod.
            :param build_info: Optional :class:`BuildInfo` instance.
            :param pipeline_info: Optional :class:`PipelineInfo` instance.
            :param job_info: Optional :class:`JobInfo` instance.

            :returns: None
        """
        super(CsvResultRecorder, self).__init__(runid=runid, start=start, render_info=render_info, apod=apod,
                                                build_info=build_info, pipeline_info=pipeline_info, job_info=job_info)
        self._csv_writer = None
        self._header_written = False
        return


    def __enter__(self):
        """
            Starts up the recording process of test results.

            This method extends the base class __enter__ to write the CSV header
            row to the stream file after opening it.

            :returns: self - The recorder instance for use within the context block.
        """
        # Call parent __enter__ which opens the stream file
        super(CsvResultRecorder, self).__enter__()
        
        # Write CSV header row
        self._csv_writer = csv.writer(self._rout)
        self._csv_writer.writerow(RESULT_CSV_HEADERS)
        self._rout.flush()
        self._header_written = True
        
        return self


    def preview(self, result: ResultNode):
        """
            Writes a preview of a result to the stream file in CSV format.

            This method serializes the result as a CSV row (without detail fields)
            and writes it to the stream results file.

            :param result: A :class:`ResultNode` object to preview.

            :returns: None
        """
        result_dict = result.as_dict(is_preview=True)
        row = _result_dict_to_csv_row(result_dict)
        
        self._csv_writer.writerow(row)
        self._rout.flush()

        self.catalog_output_directory()

        return


    def record(self, result: ResultNode):
        """
            Records a final result entry to the stream file in CSV format.

            This method serializes the complete result (with detail fields) and
            writes it to the stream results file. Result counters are updated based
            on the result type and code.

            Thread Safety:
                This method is thread-safe. Counter updates are performed within
                a lock-protected section.

            :param result: A :class:`ResultNode` object to record.

            :returns: None
        """
        result_dict = result.as_dict(is_preview=False)
        row = _result_dict_to_csv_row(result_dict)
        
        self._csv_writer.writerow(row)
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
            Writes the current summary state to the summary CSV file.

            This method serializes the internal summary dictionary to CSV format
            and writes it to the configured summary_filename. The CSV file contains
            a header row and a single data row.

            :returns: None

            :raises: ResultRecordingError if the summary file cannot be written.
        """
        summary_filename = self._render_info.summary_filename
        
        try:
            with open(summary_filename, 'w', newline='') as sout:
                writer = csv.writer(sout)
                writer.writerow(SUMMARY_CSV_HEADERS)
                
                # Build the summary row
                detail = self._summary.get("detail", {})
                build = self._summary.get("build", {})
                pipeline = self._summary.get("pipeline", {})
                job = self._summary.get("job", {})
                
                row = [
                    _value_to_csv_str(self._summary.get("version", "")),
                    _value_to_csv_str(self._summary.get("title", "")),
                    _value_to_csv_str(self._summary.get("runid", "")),
                    _value_to_csv_str(self._summary.get("start", "")),
                    _value_to_csv_str(self._summary.get("stop", "")),
                    _value_to_csv_str(self._summary.get("result", "")),
                    _value_to_csv_str(self._summary.get("apod", "")),
                    _value_to_csv_str(detail.get("errors", 0)),
                    _value_to_csv_str(detail.get("failed", 0)),
                    _value_to_csv_str(detail.get("skipped", 0)),
                    _value_to_csv_str(detail.get("passed", 0)),
                    _value_to_csv_str(detail.get("total", 0)),
                    _value_to_csv_str(build.get("branch", "")),
                    _value_to_csv_str(build.get("build", "")),
                    _value_to_csv_str(build.get("flavor", "")),
                    _value_to_csv_str(build.get("release", "")),
                    _value_to_csv_str(build.get("url", "")),
                    _value_to_csv_str(pipeline.get("id", "")),
                    _value_to_csv_str(pipeline.get("name", "")),
                    _value_to_csv_str(pipeline.get("instance", "")),
                    _value_to_csv_str(job.get("id", "")),
                    _value_to_csv_str(job.get("name", "")),
                    _value_to_csv_str(job.get("type", "")),
                    _value_to_csv_str(job.get("owner", ""))
                ]
                
                writer.writerow(row)
        except OSError as err:
            errmsg = f"Failed to write summary to '{summary_filename}'."
            raise ResultRecordingError(
                errmsg,
                file_path=summary_filename,
                operation="writing summary CSV",
                original_error=err
            ) from err

        self.catalog_output_directory()

        return


    def write_consolidated_results(self, root_node: dict):
        """
            Writes the consolidated results tree to the consolidated results CSV file.

            This method flattens the hierarchical result tree and writes all results
            as CSV rows to the configured consolidated_results_filename.

            :param root_node: A dictionary representing the root of the consolidated
                              result tree.

            :returns: None

            :raises: ResultRecordingError if the consolidated results file cannot be written.
        """
        consolidated_filename = self._render_info.consolidated_results_filename
        
        try:
            with open(consolidated_filename, 'w+', newline='') as rout:
                writer = csv.writer(rout)
                writer.writerow(RESULT_CSV_HEADERS)
                
                # Flatten the tree and write all results
                self._write_node_to_csv(writer, root_node)
                
        except OSError as err:
            errmsg = f"Failed to write consolidated results to '{consolidated_filename}'."
            raise ResultRecordingError(
                errmsg,
                file_path=consolidated_filename,
                operation="writing consolidated results CSV",
                original_error=err
            ) from err

        self.catalog_output_directory(force=True)

        return


    def _write_node_to_csv(self, writer: csv.writer, node: dict):
        """
            Recursively writes a node and its children to CSV.
            
            :param writer: The CSV writer to use.
            :param node: The node dictionary to write.
        """
        # Write the current node
        row = _result_dict_to_csv_row(node)
        writer.writerow(row)
        
        # Write child items if present
        if "items" in node:
            for item in node["items"]:
                self._write_node_to_csv(writer, item)
        
        # Write tasking groups if present
        if "tasking_groups" in node:
            for tg in node["tasking_groups"]:
                self._write_node_to_csv(writer, tg)
        
        # Write taskings if present
        if "taskings" in node:
            for tasking in node["taskings"]:
                self._write_node_to_csv(writer, tasking)
