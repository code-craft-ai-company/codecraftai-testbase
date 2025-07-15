
__author__ = "Myron Walker"
__copyright__ = "Copyright 2020, Myron W Walker"
__credits__ = []

from typing import Type

from automojo.extension.factory.factoryextension import FactoryExtension

from automojo.testbase.factoryprotocols import TestBaseExtensionProtocol

from automojo.testbase.testjob import TestJob, DefaultTestJob


class TestPlusDefaultExtensionFactory(FactoryExtension, TestBaseExtensionProtocol):

    PRECEDENCE = 0

    def get_testbase_default_job_type() -> Type[TestJob]:
        """
            Used to lookup and return the most relevant default job type as determined
            by the super factory search path.
        """
        return DefaultTestJob
