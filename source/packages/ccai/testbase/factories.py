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


import pathlib
import shutil
import tempfile

from collections.abc import Generator
from typing import Any, Dict, Optional

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
