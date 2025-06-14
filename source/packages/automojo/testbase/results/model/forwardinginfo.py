"""
    .. module:: automojo.testbase.results.model.forwardinginfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for forwardinginfo.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Optional


from dataclasses import dataclass


@dataclass
class ForwardingInfo:

    forwarding_interval: float # The interval in seconds to use when forwarding job summary information
    forwarding_url: str # identifier such as a uuid which identifies a particular pipeline.
    forwarding_headers: Optional[dict] = None # Headers to use when forwarding progress, results or summaries.
