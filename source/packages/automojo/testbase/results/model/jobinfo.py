"""
    .. module:: automojo.testbase.results.model.jobinfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for jobinfo.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Optional

from dataclasses import dataclass


@dataclass
class JobInfo:

    id: str # identifier for a job from the runner perspective
    name: str # name of the job.
    type: str # job type.
    owner: Optional[str] = None # Optional owner of the job.
    label: Optional[str] = None # Optional label associated with the job.
    initiator: Optional[str] = None # Optional name of the initiator of the job.
    venue: Optional[str] = None # Optional identifier of a venue the job was run in.
    seed: Optional[str] = None # Optional seed for the job.
    tag: Optional[str] = None # Optional correlation tag to associate with the job.