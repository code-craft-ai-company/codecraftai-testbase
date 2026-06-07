
__author__ = "Myron Walker"
__copyright__ = "Copyright 2020, Myron W Walker"
__credits__ = []

from typing import Type

from ccai.extension.factory.factoryextension import FactoryExtension

from ccai.testbase.factoryprotocols import TestBaseFactoryProtocol

from ccai.testbase.testjob import TestJob, DefaultTestJob


class TestBaseDefaultExtensionFactory(FactoryExtension, TestBaseFactoryProtocol):

    PRECEDENCE = 0

    @classmethod
    def get_testbase_default_job_type(cls) -> Type[TestJob]:
        """
            Used to lookup and return the most relevant default job type as determined
            by the super factory search path.
        """
        return DefaultTestJob
