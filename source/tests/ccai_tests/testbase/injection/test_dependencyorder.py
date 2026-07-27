"""
    .. module:: test_dependencyorder
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for ordering resource originations by dependency.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import inspect
import unittest

from ccai.errors.exceptions import SemanticError
from ccai.testbase.injection.dependencyorder import (
    order_originations_by_dependency
)


class _StubOrigin:
    """
        Stands in for a ResourceOrigin, carrying only the source signature.

        The ordering only reads ``source_signature``, so a stub keeps these
        tests independent of how originations are constructed.
    """

    def __init__(self, *parameter_names) -> None:
        """
            :param parameter_names: Names the stub factory takes.
        """
        parameters = [
            inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            for name in parameter_names
        ]
        self.source_signature = inspect.Signature(parameters)
        return


def _names(ordered):
    """
        Reduce ordered pairs to their names.

        :param ordered: The ordered (name, origin) pairs.

        :returns: The names in order.
    """
    return [name for name, _origin in ordered]


class TestDependencyOrdering(unittest.TestCase):
    """
        Verifies a factory is ordered after everything it consumes.
    """

    def test_a_dependency_declared_later_is_moved_ahead(self):

        # This is the case that failed: the dependent was declared first, so
        # resolution reported its dependency missing and the generated sequence
        # nested the loops inside out.
        items = [
            ("session_factory", _StubOrigin("credential", "world")),
            ("world", _StubOrigin()),
        ]

        ordered = order_originations_by_dependency(items, "azure")

        self.assertEqual(_names(ordered), ["world", "session_factory"])
        return

    def test_an_already_correct_order_is_left_alone(self):

        items = [
            ("raw_client", _StubOrigin()),
            ("do_client", _StubOrigin("credential", "raw_client")),
        ]

        ordered = order_originations_by_dependency(items, "digitalocean")

        self.assertEqual(_names(ordered), ["raw_client", "do_client"])
        return

    def test_a_chain_is_fully_ordered(self):

        items = [
            ("third", _StubOrigin("second")),
            ("second", _StubOrigin("first")),
            ("first", _StubOrigin()),
        ]

        ordered = order_originations_by_dependency(items, "chain")

        self.assertEqual(_names(ordered), ["first", "second", "third"])
        return

    def test_independent_parameters_keep_their_declared_order(self):

        # Stability matters: an unnecessary reshuffle churns the generated
        # sequence document for no reason.
        items = [
            ("credential", _StubOrigin()),
            ("region_config", _StubOrigin()),
            ("venue", _StubOrigin()),
        ]

        ordered = order_originations_by_dependency(items, "stable")

        self.assertEqual(_names(ordered),
                         ["credential", "region_config", "venue"])
        return

    def test_ordering_is_stable_around_a_moved_dependency(self):

        items = [
            ("alpha", _StubOrigin()),
            ("dependent", _StubOrigin("needed")),
            ("needed", _StubOrigin()),
            ("omega", _StubOrigin()),
        ]

        ordered = order_originations_by_dependency(items, "stable")

        self.assertEqual(_names(ordered),
                         ["alpha", "needed", "dependent", "omega"])
        return

    def test_the_origins_travel_with_their_names(self):

        world = _StubOrigin()
        factory = _StubOrigin("world")

        ordered = order_originations_by_dependency(
            [("session_factory", factory), ("world", world)], "azure")

        self.assertEqual(ordered, [("world", world),
                                   ("session_factory", factory)])
        return


class TestDependenciesOutsideTheScope(unittest.TestCase):
    """
        Verifies only same-scope dependencies participate in the ordering.
    """

    def test_parameters_from_an_enclosing_scope_are_ignored(self):

        # `credential` is not in this list, so it comes from a parent scope and
        # is already bound. It must not be treated as an ordering constraint.
        items = [
            ("client", _StubOrigin("credential", "region_config")),
        ]

        ordered = order_originations_by_dependency(items, "outer")

        self.assertEqual(_names(ordered), ["client"])
        return

    def test_an_unresolvable_parameter_is_not_an_ordering_concern(self):

        # A parameter satisfied nowhere is a missing parameter for resolution
        # to report. Ordering must not swallow it or fail on it.
        items = [
            ("client", _StubOrigin("nobody_originates_this")),
            ("other", _StubOrigin()),
        ]

        ordered = order_originations_by_dependency(items, "missing")

        self.assertEqual(_names(ordered), ["client", "other"])
        return

    def test_a_self_referencing_name_is_not_a_cycle(self):

        # A factory parameter that shares the resource's own name is satisfied
        # by an enclosing scope, not by itself.
        items = [
            ("client", _StubOrigin("client")),
        ]

        ordered = order_originations_by_dependency(items, "self")

        self.assertEqual(_names(ordered), ["client"])
        return

    def test_a_constraints_parameter_does_not_affect_ordering(self):

        items = [
            ("client", _StubOrigin("constraints")),
            ("other", _StubOrigin()),
        ]

        ordered = order_originations_by_dependency(items, "constraints")

        self.assertEqual(_names(ordered), ["client", "other"])
        return


class TestDegenerateInputs(unittest.TestCase):
    """
        Verifies the trivial inputs are handled without special-casing at call sites.
    """

    def test_an_empty_list_returns_empty(self):

        self.assertEqual(order_originations_by_dependency([], "empty"), [])
        return

    def test_a_single_item_returns_it(self):

        origin = _StubOrigin()

        ordered = order_originations_by_dependency([("only", origin)], "single")

        self.assertEqual(ordered, [("only", origin)])
        return

    def test_an_origin_without_a_signature_is_tolerated(self):

        class _Bare:
            pass

        items = [("bare", _Bare()), ("other", _StubOrigin())]

        ordered = order_originations_by_dependency(items, "bare")

        self.assertEqual(_names(ordered), ["bare", "other"])
        return


class TestCycleDetection(unittest.TestCase):
    """
        Verifies a cycle is reported rather than resolved arbitrarily.
    """

    def test_a_two_factory_cycle_raises(self):

        items = [
            ("left", _StubOrigin("right")),
            ("right", _StubOrigin("left")),
        ]

        with self.assertRaises(SemanticError) as caught:
            order_originations_by_dependency(items, "cyclic")

        message = str(caught.exception)

        self.assertIn("dependency cycle", message)
        self.assertIn("cyclic", message)
        return

    def test_the_error_shows_the_cycle_path(self):

        items = [
            ("a", _StubOrigin("c")),
            ("b", _StubOrigin("a")),
            ("c", _StubOrigin("b")),
        ]

        with self.assertRaises(SemanticError) as caught:
            order_originations_by_dependency(items, "cyclic")

        self.assertIn("->", str(caught.exception))
        return


if __name__ == "__main__":
    unittest.main()
