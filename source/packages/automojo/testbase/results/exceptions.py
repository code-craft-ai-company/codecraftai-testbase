"""
    .. module:: automojo.testbase.results.exceptions
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing exceptions for the results recording system.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


class ResultRecordingError(RuntimeError):
    """
        Exception raised when a file I/O operation fails during result recording.

        This exception wraps underlying OSError or IOError exceptions to provide
        more context about what operation was being performed and which file
        was involved.

        Attributes:
            file_path: The path to the file that caused the error.
            operation: A description of the operation being performed.
            original_error: The underlying exception that caused this error.
    """

    def __init__(self, message: str, file_path: str, operation: str, original_error: Exception):
        """
            Initializes a :class:`ResultRecordingError` instance.

            :param message: A human-readable description of the error.
            :param file_path: The path to the file that caused the error.
            :param operation: A description of the operation being performed
                              (e.g., "copying template", "writing summary").
            :param original_error: The underlying exception that caused this error.

            :returns: None
        """
        super().__init__(message)
        self.file_path = file_path
        self.operation = operation
        self.original_error = original_error
        return

    def __str__(self) -> str:
        """
            Returns a detailed string representation of the error.

            :returns: A formatted error message including file path, operation,
                      and underlying error details.
        """
        return (
            f"{self.args[0]}\n"
            f"  File path: {self.file_path}\n"
            f"  Operation: {self.operation}\n"
            f"  Underlying error: {type(self.original_error).__name__}: {self.original_error}"
        )
