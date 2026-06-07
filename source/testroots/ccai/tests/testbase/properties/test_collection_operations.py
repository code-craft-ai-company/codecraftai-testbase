"""
    .. module:: ccai.tests.testbase.properties.test_collection_operations
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property tests for collection/container operations.

    This module uses property-based testing to verify fundamental
    invariants of Python lists, dictionaries, and sets using randomly
    generated data. These tests exercise composite strategies and
    multi-strategy parameter combinations.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st


@given(xs=st.lists(st.integers(-100, 100), max_size=20))
def test_sorted_list_is_ordered(xs):
    """
        Sorting a list always produces an ordered sequence where
        each element is less than or equal to the next.
    """
    sorted_xs = sorted(xs)
    for i in range(len(sorted_xs) - 1):
        testbase.assert_true(sorted_xs[i] <= sorted_xs[i + 1],
            f"sorted list not ordered at index {i}: {sorted_xs[i]} > {sorted_xs[i+1]}")


@given(xs=st.lists(st.integers(-100, 100), max_size=20))
def test_sorted_preserves_length(xs):
    """
        Sorting a list never changes its length.
    """
    testbase.assert_equal(len(sorted(xs)), len(xs),
        f"sorted() changed length from {len(xs)}.")


@given(xs=st.lists(st.integers(-100, 100), max_size=20))
def test_sorted_preserves_elements(xs):
    """
        Sorting a list preserves all elements — the sorted list
        contains exactly the same multiset of values.
    """
    testbase.assert_equal(sorted(xs), sorted(sorted(xs)),
        "Sorting should be idempotent.")
    # Verify element counts match
    for val in set(xs):
        testbase.assert_equal(xs.count(val), sorted(xs).count(val),
            f"Element count for {val} changed after sort.")


@given(xs=st.lists(st.integers(0, 50), max_size=15))
def test_list_reverse_preserves_length(xs):
    """
        Reversing a list preserves the length.
    """
    reversed_xs = list(reversed(xs))
    testbase.assert_equal(len(reversed_xs), len(xs),
        "Reversing should preserve list length.")


@given(xs=st.lists(st.integers(0, 50), max_size=15))
def test_list_reverse_involution(xs):
    """
        Reversing a list twice yields the original list.
    """
    reversed_twice = list(reversed(list(reversed(xs))))
    testbase.assert_equal(reversed_twice, xs,
        "Reversing twice should yield the original list.")


@given(
    xs=st.lists(st.integers(0, 20), min_size=1, max_size=15),
    ys=st.lists(st.integers(0, 20), min_size=1, max_size=15)
)
def test_list_concatenation_length(xs, ys):
    """
        Concatenating two lists produces a list whose length equals
        the sum of the individual lengths.
    """
    combined = xs + ys
    testbase.assert_equal(len(combined), len(xs) + len(ys),
        "Concatenation length should be sum of individual lengths.")


@given(
    keys=st.lists(st.integers(0, 50), min_size=1, max_size=10),
    value=st.text(max_size=10)
)
def test_dict_from_keys_all_present(keys, value):
    """
        dict.fromkeys() creates a dictionary where every key from
        the input list is present.
    """
    d = dict.fromkeys(keys, value)
    for key in keys:
        testbase.assert_true(key in d,
            f"Key {key} should be present in dict created from keys.")
        testbase.assert_equal(d[key], value,
            f"Value for key {key} should be '{value}'.")


@given(
    xs=st.lists(st.integers(0, 30), max_size=20),
    ys=st.lists(st.integers(0, 30), max_size=20)
)
def test_set_union_contains_all_elements(xs, ys):
    """
        The union of two sets contains every element from both sets.
    """
    set_x = set(xs)
    set_y = set(ys)
    union = set_x | set_y

    for elem in set_x:
        testbase.assert_true(elem in union,
            f"Element {elem} from set_x missing from union.")
    for elem in set_y:
        testbase.assert_true(elem in union,
            f"Element {elem} from set_y missing from union.")


@given(
    xs=st.lists(st.integers(0, 30), max_size=20),
    ys=st.lists(st.integers(0, 30), max_size=20)
)
def test_set_intersection_subset_of_both(xs, ys):
    """
        The intersection of two sets is a subset of both original sets.
    """
    set_x = set(xs)
    set_y = set(ys)
    intersection = set_x & set_y

    for elem in intersection:
        testbase.assert_true(elem in set_x,
            f"Intersection element {elem} not in set_x.")
        testbase.assert_true(elem in set_y,
            f"Intersection element {elem} not in set_y.")


@given(xs=st.lists(st.integers(0, 100), min_size=1, max_size=20))
def test_min_max_within_list(xs):
    """
        min(xs) and max(xs) are always elements of the list, and
        min(xs) <= max(xs).
    """
    testbase.assert_true(min(xs) in xs, "min should be an element of the list.")
    testbase.assert_true(max(xs) in xs, "max should be an element of the list.")
    testbase.assert_true(min(xs) <= max(xs),
        f"min={min(xs)} should be <= max={max(xs)}.")


@given(
    xs=st.lists(st.integers(0, 100), max_size=15),
    constraints={"max_examples": 30}
)
def test_list_sum_matches_manual_accumulation(xs):
    """
        sum(xs) matches manually accumulating each element.
    """
    manual_sum = 0
    for x in xs:
        manual_sum += x
    testbase.assert_equal(sum(xs), manual_sum,
        f"sum({xs}) should equal manual accumulation ({manual_sum}).")


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
