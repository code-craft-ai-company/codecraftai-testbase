"""
    .. module:: ccai.testbase.errors.testruntimeouterror
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for testruntimeouterror.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []



class TestRunTimeoutError(Exception):
    """
        Exception raised when a test run exceeds the configured timeout duration.

        This exception is used to signal that the test execution phase has exceeded
        the maximum allowed time. When raised, the test run should terminate gracefully,
        marking any remaining unexecuted tests as errored.

        The ``timeout_seconds`` parameter is optional because ``ctypes.PyThreadState_SetAsyncExc``
        instantiates the exception class without arguments when injecting it into a thread.

        :param timeout_seconds: The configured timeout value in seconds that was exceeded.
            Defaults to 0 when not provided (e.g. when raised by ctypes).
    """

    def __init__(self, timeout_seconds: int = 0):
        self._timeout_seconds = timeout_seconds
        if timeout_seconds > 0:
            super().__init__(
                "Test run exceeded the configured timeout of %d seconds." % timeout_seconds
            )
        else:
            super().__init__(
                "Test run exceeded the configured timeout."
            )

    @property
    def timeout_seconds(self) -> int:
        """
            Returns the configured timeout value in seconds that was exceeded.

            :returns: The timeout duration in seconds.
        """
        return self._timeout_seconds
