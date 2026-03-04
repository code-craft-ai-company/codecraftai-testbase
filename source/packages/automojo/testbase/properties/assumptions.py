"""
    .. module:: automojo.testbase.properties.assumptions
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for the assume() function and UnsatisfiedAssumption exception.

    The ``assume()`` function allows test authors to express preconditions
    on generated data within property tests. When a precondition is not met,
    the current example is silently skipped without being counted as a failure.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


class UnsatisfiedAssumption(Exception):
    """
        Sentinel exception raised when ``assume()`` receives a falsy condition.

        This exception is caught by the ``PropertyRunner`` to skip the current
        example without recording a failure. It is NOT a test failure — it
        signals that the current set of generated inputs is invalid for the
        property under test.
    """
    pass


def assume(condition) -> None:
    """
        Skip the current property test example if the condition is not met.

        When called with a falsy value, raises ``UnsatisfiedAssumption``,
        which the ``PropertyRunner`` catches and treats as "skip this example."
        The example is not counted toward ``examples_run`` and no
        ``CheckResult`` is created for it.

        Example::

            from automojo.testbase.properties import given, assume
            from automojo.testbase.properties import strategies as st

            @given(x=st.integers(), y=st.integers())
            def test_division(x, y):
                assume(y != 0)
                result = x / y
                assert result * y == x

        :param condition: A value that is evaluated for truthiness.
        :raises UnsatisfiedAssumption: When ``condition`` is falsy.
    """
    if not condition:
        raise UnsatisfiedAssumption()
