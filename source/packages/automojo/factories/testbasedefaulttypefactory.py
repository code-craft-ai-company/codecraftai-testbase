
__author__ = "Myron Walker"
__copyright__ = "Copyright 2020, Myron W Walker"
__credits__ = []

from typing import Type

from automojo.foundation.extension.extensionfactory import ExtensionFactory
from automojo.foundation.extension.extensionprotocolbase import ExtensionProtocolBase

from automojo.testbase.testjob import TestJob, DefaultTestJob


class TestPlusDefaultExtensionFactory(ExtensionFactory, ExtensionProtocolBase):

    ext_protocol_name = "testbase.default.types"

    def get_testplus_default_job_type() -> Type[TestJob]:
        """
            Used to lookup and return the most relevant default job type as determined
            by the super factory search path.
        """
        return DefaultTestJob

