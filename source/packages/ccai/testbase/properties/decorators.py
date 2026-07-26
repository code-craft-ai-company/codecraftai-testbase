"""
    .. module:: ccai.testbase.properties.decorators
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for property test decorators — @given and expect_exception.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Optional

import functools
import inspect

from ccai.testbase.properties.strategies import Strategy


def given(*args, **kwargs) -> callable:
    """
        Decorator that marks a test function as a property-based test.

        Accepts keyword arguments mapping parameter names to ``Strategy``
        instances. An optional ``constraints`` keyword provides a dictionary
        of execution constraints for the property test runner.

        The decorator stores a ``_property_`` attribute on the decorated
        function containing the strategy mappings and constraints. This attribute
        is detected by the test sequencer to invoke the ``PropertyRunner``
        rather than the standard test execution path.

        Parameters not listed in the ``@given`` kwargs are resolved through
        the normal TestBase injection system.

        The ``@given`` decorator is composable with existing TestBase
        decorators (``@mark_categories``, ``@mark_priority``, ``@mark_keywords``).

        Supported Constraint Keys:
            - ``max_examples`` (int): Number of examples to generate. Default is 100.
            - ``max_shrink_attempts`` (int): Maximum shrinking iterations. Default is 100.

        .. note::
            The property test seed is always derived from the job seed and fully
            qualified test name. It cannot be overridden per-test. This ensures
            that a given ``--job-seed`` always reproduces the same property test
            results across all property tests in the job.

        Example::

            from ccai.testbase.properties import given
            from ccai.testbase.properties import strategies as st

            @given(x=st.integers(), y=st.integers())
            def test_addition_commutative(x, y):
                assert x + y == y + x

            @given(x=st.integers(min_value=0, max_value=100),
                   constraints={"max_examples": 50})
            def test_positive_square(x):
                assert x * x >= 0

        :param kwargs: Keyword arguments mapping parameter names to ``Strategy``
            instances, plus an optional ``constraints`` keyword for execution
            constraints dictionary.
        :returns: A decorator function.
    """
    # Extract constraints if provided
    prop_constraints = kwargs.pop("constraints", {})

    # Positional strategies bind to the decorated function's parameters in
    # order, which is how other property libraries allow @given(st.text()).
    # They are resolved against the signature at decoration time so a
    # mismatch is reported here rather than as a confusing call error.
    positional = list(args)
    for strategy in positional:
        if not isinstance(strategy, Strategy):
            raise TypeError(
                "Expected a Strategy instance for a positional argument, "
                f"got {type(strategy).__name__}"
            )

    # Validate that all remaining kwargs are Strategy instances
    strategies = {}
    for name, strategy in kwargs.items():
        if not isinstance(strategy, Strategy):
            raise TypeError(
                f"Expected a Strategy instance for parameter '{name}', "
                f"got {type(strategy).__name__}"
            )
        strategies[name] = strategy

    def decorator(fn):
        if positional:
            names = list(inspect.signature(fn).parameters.keys())
            # Positional strategies fill the LAST parameters, leaving any
            # leading ones (self, injected fixtures) to testbase's own
            # injection — matching how the keyword form composes.
            if len(positional) > len(names):
                raise TypeError(
                    f"@given received {len(positional)} positional "
                    f"strategies but {fn.__name__} takes {len(names)} "
                    "parameters."
                )
            targets = names[len(names) - len(positional):]
            for name, strategy in zip(targets, positional):
                if name in strategies:
                    raise TypeError(
                        f"@given got both a positional and a keyword "
                        f"strategy for parameter '{name}'."
                    )
                strategies[name] = strategy

        @functools.wraps(fn)
        def wrapper(*args, **kw):
            return fn(*args, **kw)

        # Attach property metadata for discovery by the test sequencer
        wrapper._property_ = {
            "strategies": strategies,
            "constraints": prop_constraints,
        }

        return wrapper

    return decorator


def expect_exception(exception_type: type, reason: str = "") -> callable:
    """
        Decorator that marks a test as expected to raise a specific exception.

        This decorator does NOT catch the exception itself. It sets an
        ``_expect_exception_`` attribute on the function that the test
        sequencer reads to determine how to handle the exception at
        test scope exit time.

        When the expected exception is raised:
            - The test result is marked as **PASSED** (expected failure occurred).
            - Any individual check results (e.g., from property testing)
              are still recorded as they occurred.

        When no exception is raised:
            - The test result is marked as **FAILED** with a message
              indicating the expected failure did not occur.

        When a different exception type is raised:
            - The test result is marked as **ERRORED** (unexpected exception).

        Example::

            from ccai.testbase.properties import expect_exception

            @expect_exception(AssertionError, reason="Known URL encoding edge case")
            @given(params=st.explicit([{'a': '1', 'b': '2'}]))
            def test_known_failure(params):
                assert params != params  # Will raise AssertionError

        :param exception_type: The exception class that is expected to be raised.
        :param reason: An optional human-readable reason for the expected failure.
        :returns: A decorator function.
    """

    def decorator(fn):
        fn._expect_exception_ = {
            "exception_type": exception_type,
            "reason": reason,
        }
        return fn

    return decorator
