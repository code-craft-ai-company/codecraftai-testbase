"""
    .. package:: automojo.testbase.output
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Output-location and run-metadata seams that let the ``testbase`` core run
               standalone (no dependency on ``automojo-runtime`` / ``automojo-this-app``).

    The standalone defaults (:class:`SimpleOutputContext`, :class:`StandaloneRunMetadata`) are
    used when ``testbase`` runs on its own. The integration layer
    (``automojo-integration-runtime`` / ``IntegratedTestJob``) registers richer implementations
    backed by ``automojo.thisapp`` well-known paths and ``RuntimeVariables``.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Automation Mojo LLC"
__credits__ = []
