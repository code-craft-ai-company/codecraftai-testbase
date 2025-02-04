
__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Type

from automojo.testbase.testjob import TestJob

from automojo.foundation.extension.extensionprotocolbase import ExtensionProtocolBase

class TestBaseExtensionProtocol(ExtensionProtocolBase):

    ext_protocol_name = "automojo-testbase"

    def get_testbase_default_job_type() -> Type[TestJob]:
        """
            Used to lookup and return the most relevant default job type as determined
            by the super factory search path.
        """
        return 
