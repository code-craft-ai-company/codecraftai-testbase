"""
    .. module:: automojo.tests.testbase.properties.test_string_operations
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property tests for string operations.

    This module uses property-based testing with the @given decorator
    and strategies to verify fundamental invariants of Python string
    operations. These are real TestBase tests that exercise the property
    testing engine against meaningful string properties.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

import automojo.testbase as testbase

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st


@given(s=st.text(max_size=50))
def test_string_reverse_involution(s):
    """
        Reversing a string twice always yields the original string.

        This property holds for all possible strings, including empty
        strings, single characters, and strings with special characters.
    """
    reversed_twice = s[::-1][::-1]
    testbase.assert_equal(s, reversed_twice,
        f"Reversing '{s}' twice should yield the original string.")


@given(a=st.text(max_size=30), b=st.text(max_size=30))
def test_string_concatenation_length(a, b):
    """
        The length of two concatenated strings always equals the sum
        of their individual lengths.
    """
    combined = a + b
    testbase.assert_equal(len(combined), len(a) + len(b),
        f"len('{a}' + '{b}') should equal len(a) + len(b).")


@given(s=st.text(max_size=50))
def test_string_upper_lower_length_preserved(s):
    """
        Converting a string to uppercase or lowercase never changes
        its length. This holds for all ASCII characters.
    """
    testbase.assert_equal(len(s.upper()), len(s),
        f"upper() should preserve length for '{s}'.")
    testbase.assert_equal(len(s.lower()), len(s),
        f"lower() should preserve length for '{s}'.")


@given(s=st.text(max_size=50))
def test_string_upper_idempotent(s):
    """
        Applying upper() twice gives the same result as applying
        it once. upper() is an idempotent operation.
    """
    testbase.assert_equal(s.upper().upper(), s.upper(),
        f"upper() should be idempotent for '{s}'.")


@given(s=st.text(max_size=50), sub=st.text(min_size=1, max_size=5))
def test_string_replace_then_count(s, sub):
    """
        After replacing all occurrences of a substring with the empty
        string, the count of that substring should be zero.
    """
    cleaned = s.replace(sub, "")
    count = cleaned.count(sub)
    testbase.assert_equal(count, 0,
        f"After replacing '{sub}' in '{s}', count should be 0 but got {count}.")


@given(s=st.text(max_size=50))
def test_string_split_join_roundtrip(s):
    """
        Splitting a string by whitespace and joining with a single
        space produces the same result as calling split().join() —
        this normalizes whitespace but is consistent.
    """
    result = " ".join(s.split())
    re_result = " ".join(result.split())
    testbase.assert_equal(result, re_result,
        "split-join should be idempotent after first application.")


@given(
    s=st.text(max_size=50),
    settings=settings(max_examples=25)
)
def test_string_strip_idempotent(s):
    """
        Stripping whitespace is idempotent: strip(strip(s)) == strip(s).
    """
    stripped = s.strip()
    testbase.assert_equal(stripped.strip(), stripped,
        f"strip() should be idempotent for '{s}'.")


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
