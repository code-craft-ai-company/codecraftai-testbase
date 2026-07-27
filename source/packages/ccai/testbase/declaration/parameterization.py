"""
    .. module:: ccai.testbase.declaration.parameterization
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Table-driven test cases via the ``parametrize`` decorator.

    Covers what ``pytest.mark.parametrize`` did for tests being brought onto
    testbase, and the plain case of a test that should run over a small fixed
    table of inputs.

    Reach for :func:`ccai.testbase.properties.given` instead when the cases are
    a *range* rather than a list — a property holds for all integers, and
    enumerating five of them tests less while reading as though it tests more.
    ``parametrize`` is for a genuinely enumerable set: the four filesystem
    kinds a venue rejects, the three endpoints that must be project-scoped.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import functools
import inspect

from typing import Any, Callable, Iterable, List, Sequence, Tuple, Union


class ParametrizedCaseError(AssertionError):
    """
        Raised when one or more cases of a parametrized test fail.

        Subclasses :class:`AssertionError` so it is reported as a test failure
        rather than an error: a failing case means the assertion under test did
        not hold, which is not the same as the test being unable to run.
    """


def parametrize(argnames: Union[str, Sequence[str]],
                argvalues: Iterable[Any]) -> Callable:
    """
        Run the decorated test once per entry in ``argvalues``.

        ``argnames`` follows the familiar comma-separated form — ``"a,b"`` or
        ``["a", "b"]`` — and each entry of ``argvalues`` supplies one case. A
        single name takes bare values; multiple names take a tuple or list per
        case, and a length mismatch raises at decoration time rather than
        surfacing as a confusing call error inside a test run.

        The parametrized names are removed from the signature testbase sees, so
        the injector resolves only the test's remaining parameters. Without
        that, every parametrized name would be reported as an unresolvable
        parameter — the decorator supplies them, but the injector has no way to
        know it.

        Every case runs even after one fails, because stopping at the first
        failure hides how many of the table's entries are broken — the useful
        signal when a table grows. Failures are collected and re-raised
        together, each labelled with the arguments that produced it.

        Example::

            from ccai import testbase

            @testbase.parametrize("fs_kind", ["LUSTRE", "WEKA", "VAST"])
            def test_rejects_unsupported_shared_fs(fs_kind, venue):
                with testbase.expect_exception(SchemaSemanticError):
                    validate(venue=venue, fs_kind=fs_kind)

            @testbase.parametrize("method_name,collection", [
                ("list_devices", "devices"),
                ("list_volumes", "volumes"),
            ])
            def test_list_endpoints_are_project_scoped(method_name,
                                                       collection, client):
                ...

        :param argnames: The parameter name, or names, the cases supply.
        :param argvalues: One entry per case. For multiple names, each entry is
            a sequence of values positionally matching ``argnames``.

        :returns: A decorator.

        :raises ValueError: If a case's value count does not match ``argnames``.
    """
    if isinstance(argnames, str):
        names = [part.strip() for part in argnames.split(",") if part.strip()]
    else:
        names = [str(part).strip() for part in argnames]

    if len(names) == 0:
        raise ValueError("parametrize requires at least one argument name.")

    cases: List[Tuple[Any, ...]] = []
    for entry in argvalues:
        if len(names) == 1:
            cases.append((entry,))
            continue

        if not isinstance(entry, (tuple, list)):
            raise ValueError(
                "parametrize({!r}) expects a tuple or list per case, "
                "got {}.".format(argnames, type(entry).__name__))
        if len(entry) != len(names):
            raise ValueError(
                "parametrize({!r}) expects {} values per case, got {}: "
                "{!r}".format(argnames, len(names), len(entry), entry))
        cases.append(tuple(entry))

    if len(cases) == 0:
        raise ValueError(
            "parametrize({!r}) was given no cases; a test that runs zero "
            "times passes without testing anything.".format(argnames))

    def decorator(fn):

        signature = inspect.signature(fn)
        for name in names:
            if name not in signature.parameters:
                raise ValueError(
                    "parametrize names {!r}, which {} does not take.".format(
                        name, fn.__name__))

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):

            failures = []

            for index, values in enumerate(cases):
                supplied = dict(zip(names, values))
                try:
                    fn(*args, **dict(kwargs, **supplied))
                except Exception as xcpt:  # noqa: BLE001 - reported below
                    described = ", ".join(
                        "{}={!r}".format(name, value)
                        for name, value in supplied.items())
                    failures.append(
                        "case[{}] {}: {}: {}".format(
                            index, described, type(xcpt).__name__, xcpt))

            if len(failures) > 0:
                raise ParametrizedCaseError(
                    "{} of {} parametrized cases failed for {}:\n{}".format(
                        len(failures), len(cases), fn.__name__,
                        "\n".join("    " + line for line in failures)))

            return

        # Hide the parametrized names from the injector; it must resolve only
        # what the decorator does not supply.
        remaining = [parameter for name, parameter in signature.parameters.items()
                     if name not in names]
        wrapper.__signature__ = signature.replace(parameters=remaining)

        wrapper._parametrized_ = {"argnames": names, "cases": cases}

        return wrapper

    return decorator
