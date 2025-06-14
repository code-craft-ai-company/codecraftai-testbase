"""
    .. module:: automojo.testbase.results.model.pipelineinfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for pipelineinfo.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from dataclasses import dataclass


@dataclass
class PipelineInfo:
    """
        Metadata describing the pipeline associated with a run.
    """

    id: str # identifier such as a uuid which identifies a particular venue associated with the pipeline.
    name: str # name for the venue associated pipeline.
    instance: str # identifier such as a uuid which identifies an instance of a pipeline.