"""
    .. module:: automojo.testbase.results.model.buildinfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for buildinfo.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []



from dataclasses import dataclass


@dataclass
class BuildInfo:
    """
        Information describing a build under test.
    """

    branch: str # name of a code 'branch' to associate with the results.
    build: str # name of a product 'build' to associate with the results
    flavor: str # label that indicates the flavor of build the automation is running against.
    release: str # name of a release to associate a automation run with.
    url: str # build url
