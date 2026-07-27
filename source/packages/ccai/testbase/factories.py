"""
    .. module:: factories
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Resource factories provided by testbase itself.

    These cover the small number of resources that nearly every test tree
    needs and that would otherwise be reimplemented per repository — where a
    dozen near-identical copies eventually disagree about cleanup.

    Import the factory and originate or attach it under whatever identifier
    the tests expect::

        from ccai import testbase
        from ccai.testbase.factories import create_temporary_directory

        testbase.originate.parameter(create_temporary_directory,
                                     identifier="temporary_directory")

    Or, to get a fresh directory per test rather than one shared across the
    scope::

        @testbase.attach.parameter(create_temporary_directory,
                                   identifier="temporary_directory")
        def test_writes_a_file(temporary_directory):
            ...

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import logging
import pathlib
import shutil
import tempfile

from collections.abc import Generator
from typing import Any, Dict, List, Optional, Tuple

from ccai.testbase.declaration import registrations as register


DEFAULT_TEMPORARY_PREFIX = "ccai-testbase-"


@register.resource_factory()
def create_temporary_directory(
        constraints: Optional[Dict[str, Any]] = None
        ) -> Generator[pathlib.Path, None, None]:
    """
        Yield the path of an empty temporary directory, then remove it.

        The value is a :class:`pathlib.Path`, not a string, so callers can
        use ``directory / "name"`` to build child paths.  A string works
        for anything taking a path argument but breaks that operator, and
        the resulting TypeError names ``str`` rather than the factory.

        The directory is removed after the consuming test finishes, whether it
        passed or failed, because the cleanup follows the ``yield`` in a
        generator factory.

        Removal is tolerant of a directory the test already deleted or moved,
        so a test that tears down its own workspace does not fail in cleanup
        for having been tidy.  It is NOT tolerant of anything else: a
        permissions or busy-file error still raises, since silently leaving
        directories behind fills a developer's temp space with no indication
        of why.

        Supported constraints:

            - ``prefix`` (str): Name prefix for the directory, which makes
              stray directories attributable when one does survive.
            - ``keep`` (bool): Leave the directory in place. For diagnosing a
              failure whose evidence is on disk — the path is the yielded
              value, so it is in the test's own log.

        :param constraints: Optional constraint dictionary.

        :returns: A generator yielding the directory path.
    """
    settings: Dict[str, Any] = {}
    if constraints is not None:
        settings = constraints

    prefix = str(settings.get("prefix", DEFAULT_TEMPORARY_PREFIX))
    keep = bool(settings.get("keep", False))

    directory = pathlib.Path(tempfile.mkdtemp(prefix=prefix))

    try:
        yield directory
    finally:
        if keep is False:
            shutil.rmtree(directory, ignore_errors=False,
                          onexc=_ignore_missing)

    return


def _ignore_missing(function: Any, path: str, excinfo: BaseException) -> None:
    """
        Re-raise a cleanup error unless the target is simply already gone.

        :param function: The failing operation.
        :param path: The path it was applied to.
        :param excinfo: The raised exception.

        :returns: ``None``

        :raises: The original exception, unless it was a missing path.
    """
    if isinstance(excinfo, FileNotFoundError):
        return

    raise excinfo


class LogCapture:
    """
        Collects log records emitted during a test.

        Covers what pytest's ``caplog`` fixture provided for tests being brought
        onto testbase: :meth:`set_level` and :attr:`records`.

        The handler is attached to the specific loggers the test names rather
        than to the root logger, and levels are restored afterwards. Nothing
        already attached is removed or closed — the runner owns the root
        logger's handlers for the duration of a run, and closing them stops the
        run making progress rather than failing it.
    """

    def __init__(self) -> None:
        """
            Initializes the capture with no records and nothing attached.
        """
        self._records: List[logging.LogRecord] = []
        self._handler = _CollectingHandler(self._records)
        self._attached: List[logging.Logger] = []
        self._restore_levels: List[Tuple[logging.Logger, int]] = []
        return

    @property
    def records(self) -> List[logging.LogRecord]:
        """
            The records captured so far, in the order they were emitted.

            :returns: The captured records.
        """
        return self._records

    @property
    def messages(self) -> List[str]:
        """
            The formatted message of each captured record.

            :returns: The captured messages.
        """
        return [record.getMessage() for record in self._records]

    def set_level(self, level: int, logger: Optional[str] = None) -> None:
        """
            Capture records at ``level`` or above from the named logger.

            :param level: The lowest level to capture.
            :param logger: Name of the logger to capture from. ``None`` means
                the root logger, which captures from everything that propagates
                to it.

            :returns: ``None``
        """
        target = logging.getLogger(logger)

        self._restore_levels.append((target, target.level))
        target.setLevel(level)

        if target not in self._attached:
            target.addHandler(self._handler)
            self._attached.append(target)

        self._handler.setLevel(level)

        return

    def clear(self) -> None:
        """
            Discard the records captured so far.

            :returns: ``None``
        """
        del self._records[:]
        return

    def detach(self) -> None:
        """
            Detach the handler and restore the levels that were changed.

            :returns: ``None``
        """
        for target in self._attached:
            target.removeHandler(self._handler)
        del self._attached[:]

        # Restored newest-first, so a logger whose level was set more than once
        # ends up with the level it had before the first change.
        for target, level in reversed(self._restore_levels):
            target.setLevel(level)
        del self._restore_levels[:]

        return


class _CollectingHandler(logging.Handler):
    """
        A handler that appends every record it is given to a list.
    """

    def __init__(self, records: List[logging.LogRecord]) -> None:
        """
            :param records: The list to append to.
        """
        super().__init__()
        self._records = records
        return

    def emit(self, record: logging.LogRecord) -> None:
        """
            Append a record.

            :param record: The record to collect.

            :returns: ``None``
        """
        self._records.append(record)
        return


@register.resource_factory()
def create_log_capture(
        constraints: Optional[Dict[str, Any]] = None
        ) -> Generator[LogCapture, None, None]:
    """
        Yield a :class:`LogCapture` for one test, detaching it afterwards.

        Stands in for pytest's ``caplog``. Attach it per test with
        ``@testbase.attach.parameter``: a capture shared across tests would
        accumulate records from earlier ones, so an assertion on how many times
        something was logged would pass or fail depending on what ran before.

        Supported constraints:

            - ``level`` (int): Level to capture at from the root logger, applied
              before the test runs. Without it, the test calls
              :meth:`LogCapture.set_level` for the loggers it cares about.

        :param constraints: Optional constraint dictionary.

        :returns: A generator yielding the capture.
    """
    settings: Dict[str, Any] = {}
    if constraints is not None:
        settings = constraints

    capture = LogCapture()

    level = settings.get("level", None)
    if level is not None:
        capture.set_level(int(level))

    try:
        yield capture
    finally:
        capture.detach()

    return
