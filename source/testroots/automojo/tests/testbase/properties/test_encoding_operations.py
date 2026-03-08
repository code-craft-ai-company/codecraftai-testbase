"""
    .. module:: automojo.tests.testbase.properties.test_encoding_operations
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property tests for encoding and serialization operations.

    This module uses property-based testing to verify roundtrip
    invariants of common encoding and serialization operations
    such as JSON, base64, and URL encoding. These tests exercise
    the composite strategy pattern and demonstrate testing
    real I/O transformation pipelines.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

import base64
import json
import urllib.parse

import automojo.testbase as testbase

from automojo.testbase.properties import given, expect_exception
from automojo.testbase.properties import strategies as st


@given(s=st.text(max_size=100, alphabet="abcdefghijklmnopqrstuvwxyz0123456789 "))
def test_json_string_roundtrip(s):
    """
        Encoding a string to JSON and decoding it back always
        yields the original string.
    """
    encoded = json.dumps(s)
    decoded = json.loads(encoded)
    testbase.assert_equal(decoded, s,
        f"JSON roundtrip failed for string: {s!r}")


@given(x=st.integers(-10000, 10000))
def test_json_integer_roundtrip(x):
    """
        Encoding an integer to JSON and decoding it back yields
        the original integer.
    """
    encoded = json.dumps(x)
    decoded = json.loads(encoded)
    testbase.assert_equal(decoded, x,
        f"JSON roundtrip failed for integer: {x}")


@given(xs=st.lists(st.integers(-100, 100), max_size=10))
def test_json_list_roundtrip(xs):
    """
        Encoding a list of integers to JSON and decoding it back
        yields the original list.
    """
    encoded = json.dumps(xs)
    decoded = json.loads(encoded)
    testbase.assert_equal(decoded, xs,
        f"JSON roundtrip failed for list: {xs}")


@given(
    key=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"),
    value=st.integers(-100, 100)
)
def test_json_dict_roundtrip(key, value):
    """
        Encoding a dictionary to JSON and decoding it back yields
        the original dictionary.
    """
    d = {key: value}
    encoded = json.dumps(d)
    decoded = json.loads(encoded)
    testbase.assert_equal(decoded, d,
        f"JSON roundtrip failed for dict: {d}")


@given(b=st.booleans())
def test_json_boolean_roundtrip(b):
    """
        Encoding a boolean to JSON and decoding it back yields
        the original boolean.
    """
    encoded = json.dumps(b)
    decoded = json.loads(encoded)
    testbase.assert_equal(decoded, b,
        f"JSON roundtrip failed for boolean: {b}")


@given(s=st.text(max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"))
def test_base64_roundtrip(s):
    """
        Base64 encoding and decoding ASCII-safe text is a lossless
        roundtrip operation.
    """
    encoded = base64.b64encode(s.encode("utf-8"))
    decoded = base64.b64decode(encoded).decode("utf-8")
    testbase.assert_equal(decoded, s,
        f"Base64 roundtrip failed for: {s!r}")


@given(s=st.text(max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789 /&=?#"))
def test_url_quote_roundtrip(s):
    """
        URL quoting (percent-encoding) and unquoting is a lossless
        roundtrip for all characters.
    """
    quoted = urllib.parse.quote(s, safe="")
    unquoted = urllib.parse.unquote(quoted)
    testbase.assert_equal(unquoted, s,
        f"URL quote roundtrip failed for: {s!r}")


@expect_exception(AssertionError, reason="urlencode/parse_qsl loses empty-value entries")
@given(
    params=st.explicit([
        {"a": "", "b": "x"},
    ]),
    constraints={"max_examples": 1}
)
def test_url_encode_decode_roundtrip(params):
    """
        URL-encoding query parameters and parsing them back yields
        the original parameter dictionary.

        This test exercises a known edge case: ``urllib.parse.parse_qsl``
        with default settings drops keys that have empty-string values,
        so the roundtrip is lossy. The test is marked with
        ``@expect_exception`` to document this known limitation.
    """
    encoded = urllib.parse.urlencode(params)
    decoded = dict(urllib.parse.parse_qsl(encoded))
    testbase.assert_equal(decoded, params,
        f"URL encode/decode roundtrip failed for: {params}")


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
