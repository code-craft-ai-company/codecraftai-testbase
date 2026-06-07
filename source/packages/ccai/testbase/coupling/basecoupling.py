"""
.. module:: ccai.testbase.coupling.basecoupling
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing the :class:`BaseCoupling` class which serves as the foundational
        abstract base class for all coupling-based resources in the TestBase framework.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>

The BaseCoupling module provides the foundational type for all coupling-based resources in the
TestBase test execution framework. It establishes common infrastructure including logging
capabilities that are shared across all derived coupling types.

Example usage::

    from ccai.testbase.coupling.basecoupling import BaseCoupling

    class MyCustomCoupling(BaseCoupling):
        '''
            Custom coupling implementation.
        '''

        def do_something(self):
            self.logger.info("Performing custom coupling operation")
            return

"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.xmodules.xlogging.enhancedloggers import getEnhancedLogger


class BaseCoupling:
    """
        The :class:`BaseCoupling` class serves as the foundational abstract base class for all
        coupling-based resources in the TestBase framework. It provides common infrastructure
        including logging capabilities that are shared across all derived coupling types.

        This class is the base type used for detecting coupling-based resources during dependency
        injection and test execution. All coupling types (IntegrationCoupling, ConfigurationCoupling)
        inherit from this class to gain access to the shared logger instance.

        :cvar logger: A shared :class:`EnhancedLogger` instance accessible to all derived classes
            for logging coupling operations and diagnostic information.

        Example usage::

            from ccai.testbase.coupling.basecoupling import BaseCoupling

            class DeviceCoupling(BaseCoupling):
                '''
                    Coupling for device automation resources.
                '''

                def connect(self):
                    self.logger.info("Connecting to device...")
                    # Connection logic here
                    return

        .. note::
            This class should not be instantiated directly. Instead, use one of the derived
            coupling types: :class:`IntegrationCoupling`, :class:`ConfigurationCoupling`, or
            :class:`ValidatorCoupling`.
    """

    logger = getEnhancedLogger()
