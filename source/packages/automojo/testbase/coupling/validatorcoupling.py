"""
.. module:: validatorcoupling
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing the :class:`ValidatorCoupling` class and associated reflection methods.
        The :class:`ValidatorCoupling` derived classes can be used to integraton validator resources 
        into the test environment.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Any

from automojo.errors.exceptions import NotOverloadedError

class ValidatorCoupling:
    """
        Base type for Validator objects used to verify return types of validator factory methods.
    """

    def attach_to_test(self, testscope: Any, suffix: str):
        """
            The 'attach_to_test' method is called by the sequencer in order to attach the validator to its partner
            test scope.
        """
        raise NotOverloadedError("'ValidatorCoupling' derived objects must overload the 'attach_to_test' method.")

