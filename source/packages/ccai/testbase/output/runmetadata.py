"""
    .. module:: ccai.testbase.output.runmetadata
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The :class:`IRunMetadata` seam and its standalone :class:`StandaloneRunMetadata`
               default for the build / pipeline / job metadata associated with a test run.

    The ``testbase`` core obtains run metadata from an :class:`IRunMetadata` instead of reading
    the ``RuntimeVariables`` descriptor set (which now lives in ``ccai.thisapp`` and is used
    only by the integration runtime). Standalone runs use :class:`StandaloneRunMetadata`, which
    auto-generates a run id and fills CI/build/pipeline/job fields with ``(unknown)`` placeholders.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

import uuid

from ccai.testbase import environment
from ccai.testbase.results.model.buildinfo import BuildInfo
from ccai.testbase.results.model.pipelineinfo import PipelineInfo
from ccai.testbase.results.model.jobinfo import JobInfo


UNKNOWN = "(unknown)"


class IRunMetadata(ABC):
    """
        Seam used by the ``testbase`` core to obtain the run-level metadata (run id, start time,
        timeout, and the build / pipeline / job descriptors) for a test run. Implementations
        decide whether the values come from CI environment / runtime variables (integration) or
        from standalone defaults.
    """

    @property
    @abstractmethod
    def run_id(self) -> str:
        """The unique identifier for this test run."""
        raise NotImplementedError("IRunMetadata.run_id must be implemented")

    @property
    @abstractmethod
    def apod(self) -> Optional[str]:
        """The name of the automation pod the run executes on, when applicable."""
        raise NotImplementedError("IRunMetadata.apod must be implemented")

    @property
    @abstractmethod
    def title(self) -> str:
        """A human-readable title for the test run."""
        raise NotImplementedError("IRunMetadata.title must be implemented")

    @property
    @abstractmethod
    def starttime(self) -> datetime:
        """The start time of the test run."""
        raise NotImplementedError("IRunMetadata.starttime must be implemented")

    @property
    @abstractmethod
    def testrun_timeout(self) -> Optional[int]:
        """The optional whole-run timeout, in seconds."""
        raise NotImplementedError("IRunMetadata.testrun_timeout must be implemented")

    @property
    @abstractmethod
    def job_seed(self) -> str:
        """The job-level seed used for reproducible property testing."""
        raise NotImplementedError("IRunMetadata.job_seed must be implemented")

    @abstractmethod
    def build_info(self) -> BuildInfo:
        """
            :returns: A :class:`BuildInfo` describing the build the run is associated with.
        """
        raise NotImplementedError("IRunMetadata.build_info must be implemented")

    @abstractmethod
    def pipeline_info(self) -> PipelineInfo:
        """
            :returns: A :class:`PipelineInfo` describing the pipeline the run is associated with.
        """
        raise NotImplementedError("IRunMetadata.pipeline_info must be implemented")

    @abstractmethod
    def job_info(self) -> JobInfo:
        """
            :returns: A :class:`JobInfo` describing the job the run is associated with.
        """
        raise NotImplementedError("IRunMetadata.job_info must be implemented")


class StandaloneRunMetadata(IRunMetadata):
    """
        Standalone :class:`IRunMetadata` for plain ``testbase`` runs.

        The run id is taken from ``AM_RUN_ID`` or auto-generated; the start time defaults to the
        construction time; the timeout is read from the environment; and the build / pipeline / job
        descriptors are filled with ``(unknown)`` placeholders so the result model and stdout
        summary remain well-formed without any CI/runtime context.
    """

    def __init__(self, run_id: Optional[str] = None, apod: Optional[str] = None,
                 title: str = "Test Run", starttime: Optional[datetime] = None,
                 testrun_timeout: Optional[int] = None):
        """
            Constructor for a :class:`StandaloneRunMetadata`.

            :param run_id: Optional explicit run id (otherwise ``AM_RUN_ID`` or a new uuid).
            :param apod: Optional automation-pod name.
            :param title: A human-readable title for the run.
            :param starttime: Optional explicit start time (otherwise the construction time).
            :param testrun_timeout: Optional explicit timeout (otherwise read from the environment).
        """
        resolved_run_id = run_id
        if resolved_run_id is None:
            resolved_run_id = environment.get_run_id()
        if resolved_run_id is None:
            resolved_run_id = str(uuid.uuid4())
        self._run_id = resolved_run_id

        self._apod = apod

        self._title = title

        resolved_start = starttime
        if resolved_start is None:
            resolved_start = datetime.now()
        self._starttime = resolved_start

        resolved_timeout = testrun_timeout
        if resolved_timeout is None:
            resolved_timeout = environment.get_testrun_timeout()
        self._testrun_timeout = resolved_timeout

        self._job_seed = None
        return

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def apod(self) -> Optional[str]:
        return self._apod

    @property
    def title(self) -> str:
        return self._title

    @property
    def starttime(self) -> datetime:
        return self._starttime

    @property
    def testrun_timeout(self) -> Optional[int]:
        return self._testrun_timeout

    @property
    def job_seed(self) -> str:
        if self._job_seed is None:
            self._job_seed = str(uuid.uuid4())
        return self._job_seed

    def build_info(self) -> BuildInfo:
        info = BuildInfo(branch=UNKNOWN, build=UNKNOWN, flavor=UNKNOWN, release=UNKNOWN, url=UNKNOWN)
        return info

    def pipeline_info(self) -> PipelineInfo:
        info = PipelineInfo(id=UNKNOWN, name=UNKNOWN, instance=UNKNOWN)
        return info

    def job_info(self) -> JobInfo:
        info = JobInfo(id=UNKNOWN, name=self._title, type=UNKNOWN, owner=UNKNOWN, label=UNKNOWN,
                       initiator=UNKNOWN, venue=UNKNOWN, seed=self.job_seed, tag=UNKNOWN)
        return info
