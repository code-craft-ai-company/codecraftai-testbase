"""
    .. package:: ccai.testbase.output
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Output-location and run-metadata seams that let the ``testbase`` core run
               standalone (no dependency on ``codecraftai-runtime`` / ``codecraftai-this-app``).

    The standalone defaults (:class:`SimpleOutputContext`, :class:`StandaloneRunMetadata`) are
    used when ``testbase`` runs on its own. The integration layer
    (``codecraftai-integration-runtime`` / ``IntegratedTestJob``) registers richer implementations
    backed by ``ccai.thisapp`` well-known paths and ``RuntimeVariables``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []
