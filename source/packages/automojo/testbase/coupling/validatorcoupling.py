"""
.. module:: automojo.testbase.coupling.validatorcoupling
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing the :class:`ValidatorCoupling` class for creating validators
        that verify test outcomes and attach to test scopes.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>

The ValidatorCoupling module provides a base type for validator objects that verify test outcomes
and attach to test scopes. Validators are used to perform assertions and verifications on test
results, providing a structured way to validate expected behaviors.

Example usage::

    from automojo.testbase.coupling.validatorcoupling import ValidatorCoupling

    class ResponseValidator(ValidatorCoupling):
        '''
            Validator for HTTP response characteristics.
        '''

        def attach_to_test(self, testscope, suffix):
            self._testscope = testscope
            self._suffix = suffix
            return

        def validate_status_code(self, expected_code):
            # Validation logic here
            return

"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Any

from automojo.errors.exceptions import AbstractMethodError

from automojo.testbase.coupling.basecoupling import BaseCoupling

class ValidatorCoupling(BaseCoupling):
    """
        The :class:`ValidatorCoupling` class serves as the base type for validator objects that
        verify test outcomes and attach to test scopes. Validators provide a structured way to
        perform assertions and verifications on test results.

        Derived classes must implement the :meth:`attach_to_test` method to define how the
        validator binds to a test scope and configures its validation rules.

        Example usage::

            from automojo.testbase.coupling.validatorcoupling import ValidatorCoupling

            class DataValidator(ValidatorCoupling):
                '''
                    Validator for data integrity checks.
                '''

                def __init__(self):
                    self._testscope = None
                    self._suffix = None
                    return

                def attach_to_test(self, testscope, suffix):
                    self._testscope = testscope
                    self._suffix = suffix
                    return

                def validate_data(self, data, expected):
                    # Perform validation
                    assert data == expected, f"Data mismatch: {data} != {expected}"
                    return


        .. seealso::
            :class:`IntegrationCoupling` for external resource integration
            :class:`ConfigurationCoupling` for environment configuration
    """

    def attach_to_test(self, testscope: Any, suffix: str):
        """
            Attaches the validator to a test scope for validation operations.

            This method is called by the sequencer to bind the validator to its partner test
            scope. Derived classes must override this method to implement their specific
            attachment logic, such as storing references to the test scope and configuring
            validation rules.

            :param testscope: The test scope object to attach the validator to. This provides
                context for the validation operations and access to test-specific data.
            :param suffix: A string suffix used to identify or differentiate this validator
                instance within the test scope. This can be used for naming validation
                results or organizing multiple validators.

            :returns: None. This method does not return a value.

            :raises automojo.errors.exceptions.AbstractMethodError: When called on the base
                :class:`ValidatorCoupling` class without being overloaded by a derived class.

            Example usage::

                class MyValidator(ValidatorCoupling):
                    '''
                        Custom validator implementation.
                    '''

                    def __init__(self):
                        self._testscope = None
                        self._suffix = None
                        return

                    def attach_to_test(self, testscope, suffix):
                        self._testscope = testscope
                        self._suffix = suffix
                        # Configure validation rules based on test scope
                        return

            .. note::
                This method must be overloaded by derived classes. Calling this method on
                the base :class:`ValidatorCoupling` class will raise an
                :class:`AbstractMethodError`.
        """
        raise AbstractMethodError("'ValidatorCoupling' derived objects must overload the 'attach_to_test' method.")

