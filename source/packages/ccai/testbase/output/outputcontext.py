"""
    .. module:: ccai.testbase.output.outputcontext
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The :class:`IOutputContext` seam and its standalone :class:`SimpleOutputContext`
               default for resolving where ``testbase`` writes run artefacts.

    The ``testbase`` core asks an :class:`IOutputContext` for the directories it needs (results,
    per-testcase by-products, diagnostics) instead of importing the well-known-path helpers that
    now live in ``ccai.thisapp.paths``. This keeps the framework dependency-free of the
    runtime / this-app layers.

    ``SimpleOutputContext`` is the standalone default: it roots everything under a single base
    directory (``AM_OUTPUT_DIRECTORY`` or ``<cwd>/.output``). The integration runtime supplies a
    ``RuntimeOutputContext`` (backed by ``ccai.thisapp.paths``) instead.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from abc import ABC, abstractmethod
from typing import Optional

import os

from ccai.testbase import environment


TRANSLATE_TABLE_NORMALIZE_FOR_PATH = str.maketrans(",.:;", "    ")


def ensure_directory(target: str) -> None:
    """
        Creates a directory and any missing parents WITHOUT consulting
        ``os.path.exists``.

        ``os.makedirs`` internally checks ``os.path.exists`` to decide whether
        a parent needs creating -- and ``os.path.exists`` is one of the most
        commonly patched functions in tests.  A resource factory that patches
        it to return ``True`` makes ``os.makedirs`` skip a genuinely missing
        parent and then fail with ``FileNotFoundError`` on the leaf, killing
        the run from inside the framework.  This helper only issues
        ``os.mkdir`` calls and classifies the FILESYSTEM's own errors, so a
        patched ``exists`` cannot mislead it in either direction.

        :param target: The absolute directory path to create.
    """
    try:
        os.mkdir(target)
    except FileExistsError:
        return
    except FileNotFoundError:
        parent = os.path.dirname(target)
        if parent == target:
            raise
        ensure_directory(parent)
        try:
            os.mkdir(target)
        except FileExistsError:
            pass
    return


def normalize_name_for_path(name: str) -> str:
    """
        Normalises an identifier so it can be used as a path segment.

        :param name: The identifier to normalise.

        :returns: A filesystem-safe version of the identifier.
    """
    translated = name.translate(TRANSLATE_TABLE_NORMALIZE_FOR_PATH)
    collapsed = "-".join(translated.split())
    return collapsed


class IOutputContext(ABC):
    """
        Seam used by the ``testbase`` core to resolve the directories where run artefacts are
        written. Implementations decide whether artefacts go under a simple base directory
        (standalone) or under the well-known result paths managed by the integration runtime.
    """

    @abstractmethod
    def get_test_results_dir(self) -> str:
        """
            Returns the directory where the top-level test-run artefacts are written.

            :returns: An absolute path to the results directory (created if necessary).
        """
        raise NotImplementedError("IOutputContext.get_test_results_dir must be implemented")

    @abstractmethod
    def get_testcase_byproducts_dir(self, test_id: str) -> str:
        """
            Returns the directory where a single test case writes its by-products.

            :param test_id: The scope identifier of the test case.

            :returns: An absolute path to the test-case by-products directory (created if necessary).
        """
        raise NotImplementedError("IOutputContext.get_testcase_byproducts_dir must be implemented")

    @abstractmethod
    def get_diagnostics_dir(self, label: str) -> str:
        """
            Returns the directory where a diagnostic capture writes its artefacts.

            :param label: A label identifying the diagnostic capture.

            :returns: An absolute path to the diagnostics directory (created if necessary).
        """
        raise NotImplementedError("IOutputContext.get_diagnostics_dir must be implemented")

    @abstractmethod
    def get_summary_template_source(self) -> Optional[str]:
        """
            Returns the path to the HTML summary template, when HTML rendering is available.

            :returns: A path to the template, or ``None`` for standalone (stdout) operation.
        """
        raise NotImplementedError("IOutputContext.get_summary_template_source must be implemented")

    @abstractmethod
    def get_static_resource_source(self) -> Optional[str]:
        """
            Returns the source directory for static render resources, when available.

            :returns: A path, or ``None`` for standalone (stdout) operation.
        """
        raise NotImplementedError("IOutputContext.get_static_resource_source must be implemented")

    @abstractmethod
    def get_static_resource_destination(self) -> Optional[str]:
        """
            Returns the destination directory for static render resources, when available.

            :returns: A path, or ``None`` for standalone (stdout) operation.
        """
        raise NotImplementedError("IOutputContext.get_static_resource_destination must be implemented")


class SimpleOutputContext(IOutputContext):
    """
        Standalone :class:`IOutputContext` that roots every artefact under a single base directory.

        The base directory is, in order of precedence, the ``base_dir`` argument, the
        ``AM_OUTPUT_DIRECTORY`` environment variable, or ``<cwd>/.output``. No HTML template or
        static-resource paths are provided (standalone runs record to stdout), so the
        template / static-resource accessors return ``None``.
    """

    def __init__(self, base_dir: Optional[str] = None):
        """
            Constructor for a :class:`SimpleOutputContext`.

            :param base_dir: Optional explicit base directory for run artefacts.
        """
        resolved_base = base_dir
        if resolved_base is None:
            resolved_base = environment.get_output_directory()
        if resolved_base is None:
            resolved_base = os.path.join(os.getcwd(), ".output")

        self._base_dir = os.path.abspath(resolved_base)
        return

    @property
    def base_dir(self) -> str:
        return self._base_dir

    def get_test_results_dir(self) -> str:
        results_dir = self._base_dir
        ensure_directory(results_dir)
        return results_dir

    def get_testcase_byproducts_dir(self, test_id: str) -> str:
        safe_id = normalize_name_for_path(test_id)
        byproducts_dir = os.path.join(self._base_dir, "testcase_byproducts", safe_id)
        ensure_directory(byproducts_dir)
        return byproducts_dir

    def get_diagnostics_dir(self, label: str) -> str:
        safe_label = normalize_name_for_path(label)
        diagnostics_dir = os.path.join(self._base_dir, "diagnostics", safe_label)
        ensure_directory(diagnostics_dir)
        return diagnostics_dir

    def get_summary_template_source(self) -> Optional[str]:
        return None

    def get_static_resource_source(self) -> Optional[str]:
        return None

    def get_static_resource_destination(self) -> Optional[str]:
        return None
