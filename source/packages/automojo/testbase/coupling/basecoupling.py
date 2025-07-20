"""
    .. module:: automojo.testbase.coupling.basecoupling
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for basecoupling.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.xmodules.xlogging.enhancedloggers import getEnhancedLogger


class BaseCoupling:
    """
        The :class:`BaseCoupling` object serves as a base type to detect coupling based
        resources.
    """

    logger = getEnhancedLogger()
