"""
    .. module:: ccai.testbase.injection.dependencyorder
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Orders resource originations so each follows what its factory consumes.

    Within a single scope, the order parameters were declared says nothing about
    the order they can be built in. A factory that takes another parameter of
    the same scope has to come after it, and two places depend on that:

    - resolution, which validates a factory's dependencies against the
      parameters visible so far and reports anything not yet added as missing;
    - sequence generation, which turns each test-local parameter into a nested
      loop and so binds names in the order it emits them.

    Both used declaration order, which made a working set of factories fail
    depending on how they happened to be declared.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


from typing import Any, List, Tuple

from ccai.errors.exceptions import SemanticError


def order_originations_by_dependency(
        origination_items: List[Tuple[str, Any]],
        scope_description: str) -> List[Tuple[str, Any]]:
    """
        Order ``(name, ResourceOrigin)`` pairs so dependencies come first.

        Only dependencies drawn from the same list are considered. A factory
        parameter satisfied by an enclosing scope is already bound before this
        point, and one that is satisfied nowhere is a missing parameter — which
        is resolution's finding to report, not something to reorder around.

        The sort is stable: parameters with no dependency between them keep
        their original order, so a generated sequence document stays readable
        and diffable instead of reshuffling for no reason.

        :param origination_items: The pairs to order, as declared.
        :param scope_description: Scope or test name, used in a cycle error.

        :returns: The same pairs, dependencies first.

        :raises SemanticError: If the factories form a dependency cycle. A cycle
            cannot be built in any order, so it is reported rather than
            resolved to an arbitrary one.
    """
    if len(origination_items) < 2:
        return list(origination_items)

    origin_lookup = {}
    for param_name, param_origin in origination_items:
        origin_lookup[param_name] = param_origin

    dependencies = {}
    for param_name, param_origin in origination_items:
        signature = getattr(param_origin, "source_signature", None)
        if signature is None:
            dependencies[param_name] = []
            continue

        dependencies[param_name] = [
            candidate for candidate in signature.parameters
            if candidate != param_name and candidate in origin_lookup
        ]

    ordered: List[Tuple[str, Any]] = []
    placed = set()
    visiting: List[str] = []

    def _place(param_name: str) -> None:

        if param_name in placed:
            return

        if param_name in visiting:
            cycle = " -> ".join(
                visiting[visiting.index(param_name):] + [param_name])
            raise SemanticError(
                "The resource factories for '{}' form a dependency cycle and "
                "cannot be ordered: {}".format(scope_description, cycle))

        visiting.append(param_name)
        for required in dependencies[param_name]:
            _place(required)
        visiting.pop()

        placed.add(param_name)
        ordered.append((param_name, origin_lookup[param_name]))

        return

    for param_name, _param_origin in origination_items:
        _place(param_name)

    return ordered
