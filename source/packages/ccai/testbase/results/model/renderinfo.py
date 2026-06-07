"""
    .. module:: ccai.testbase.results.model.renderinfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for renderinfo.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from dataclasses import dataclass

@dataclass
class RenderInfo:
    """
        Parameters that control how result rendering is performed.
    """

    title: str # A title to associated with the summary for the test results.
    summary_filename: str # The full path to the summary file where the test run summary should be written to.
    summary_template: str # The full path to the summary file source template
    stream_results_filename: str # The full path to the results stream file where the test run results are written as a stream.
    consolidated_results_filename: str # The full path to the consolidated results file, where the results stream is consolidated to a postable document.
    static_resource_source: str # The source folder for the static render resources
    static_resource_destination: str # The destination folder for static render resources
