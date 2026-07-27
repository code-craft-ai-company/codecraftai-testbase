"""
    .. module:: test_monikers_from_notables
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for deriving monikers and pivots from notables.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import unittest

from collections import OrderedDict
from unittest.mock import MagicMock

from ccai.testbase.sequencing.sequencertestscope import SequencerTestScope


class _MethodProxy:
    """Stands in for a mock's attribute proxy, which is not a string."""

    def __init__(self, name: str) -> None:
        self._name = name
        return


class _ProxyingDouble:
    """
        A test double that answers every attribute with a proxy.

        This is a common idiom, and it defeats a bare ``hasattr`` check: the
        object claims to have ``moniker`` and ``pivots`` while supplying neither.
    """

    def __getattr__(self, name):
        return _MethodProxy(name)


class _Described:
    """A resource that supplies a real moniker and pivots."""

    def __init__(self) -> None:
        self.moniker = "region-eastus"
        self.pivots = {"region": "eastus"}
        return


def _derive(notables):
    """
        Run the moniker derivation against a notables mapping.

        Built without going through __init__, which needs a sequencer and a
        recorder that are irrelevant to this behaviour.

        :param notables: The notables mapping to derive from.

        :returns: The (monikers, pivots) tuple.
    """
    scope = SequencerTestScope.__new__(SequencerTestScope)
    scope._notables = notables
    return scope._get_monikers_and_pivots()


class TestMonikersFromDescribedResources(unittest.TestCase):
    """
        Verifies a resource's own moniker and pivots are used when present.
    """

    def test_a_real_moniker_is_used(self):

        monikers, _pivots = _derive(OrderedDict([("venue", _Described())]))

        self.assertEqual(monikers, ["region-eastus"])
        return

    def test_real_pivots_are_used(self):

        _monikers, pivots = _derive(OrderedDict([("venue", _Described())]))

        self.assertEqual(pivots, {"venue": {"region": "eastus"}})
        return


class TestMonikersFromProxyingDoubles(unittest.TestCase):
    """
        Verifies a double that proxies every attribute does not break the scope.
    """

    def test_a_proxied_moniker_falls_back_to_the_string_form(self):

        # Before this was fixed, hasattr succeeded, the proxy was appended, and
        # the join in SequencerTestScope.__init__ raised
        # "sequence item 0: expected str instance, _MethodProxy found" from
        # inside the sequencer.
        double = _ProxyingDouble()

        monikers, _pivots = _derive(OrderedDict([("transport", double)]))

        self.assertEqual(monikers, [str(double)])
        return

    def test_the_monikers_are_all_strings(self):

        notables = OrderedDict([("transport", _ProxyingDouble()),
                                ("venue", _Described())])

        monikers, _pivots = _derive(notables)

        for moniker in monikers:
            self.assertIsInstance(moniker, str)
        return

    def test_the_monikers_can_be_joined(self):

        # The join is what actually failed, so assert it directly.
        notables = OrderedDict([("transport", _ProxyingDouble()),
                                ("venue", _Described())])

        monikers, _pivots = _derive(notables)

        joined = ",".join(monikers)

        self.assertIn("region-eastus", joined)
        return

    def test_proxied_pivots_fall_back_to_the_string_form(self):

        double = _ProxyingDouble()

        _monikers, pivots = _derive(OrderedDict([("transport", double)]))

        self.assertEqual(pivots, {"transport": str(double)})
        return

    def test_a_magicmock_notable_is_tolerated(self):

        # MagicMock answers every attribute too, and is the most likely double
        # to be attached by accident.
        mock = MagicMock()

        monikers, pivots = _derive(OrderedDict([("client", mock)]))

        self.assertIsInstance(monikers[0], str)
        self.assertIsInstance(pivots["client"], str)
        return


class TestMonikersFromPlainValues(unittest.TestCase):
    """
        Verifies ordinary values still describe themselves.
    """

    def test_a_plain_object_uses_its_string_form(self):

        monikers, pivots = _derive(OrderedDict([("size", 42)]))

        self.assertEqual(monikers, ["42"])
        self.assertEqual(pivots, {"size": "42"})
        return

    def test_no_notables_yields_nothing(self):

        monikers, pivots = _derive(OrderedDict())

        self.assertEqual(monikers, [])
        self.assertEqual(pivots, OrderedDict())
        return

    def test_ordering_follows_the_notables(self):

        notables = OrderedDict([("first", 1), ("second", 2)])

        monikers, pivots = _derive(notables)

        self.assertEqual(monikers, ["1", "2"])
        self.assertEqual(list(pivots.keys()), ["first", "second"])
        return


if __name__ == "__main__":
    unittest.main()
