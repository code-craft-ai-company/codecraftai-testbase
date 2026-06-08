"""
    .. module:: ccai.testbase.extensionprotocols
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for extensionprotocols.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Type

from ccai.testbase.testjob import TestJob, DefaultTestJob

from ccai.extension.factory.factoryprotocolbase import FactoryProtocolBase

class TestBaseFactoryProtocol(FactoryProtocolBase):
    """
        Extension protocol used by Code Craft AI testbase tooling.
    """

    factory_protocol_name = "codecraftai-testbase-default-types"

    @classmethod
    def get_testbase_default_job_type(cls) -> Type[TestJob]:
        """
            Used to lookup and return the most relevant default job type as determined
            by the super factory search path.
        """
        return DefaultTestJob
