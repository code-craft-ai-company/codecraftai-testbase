"""
    .. module:: ccai.tests.testbase.properties.test_numeric_operations
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property tests for numeric operations.

    This module uses property-based testing to verify fundamental
    mathematical invariants of integer and floating-point arithmetic.
    These tests exercise the @given decorator and numeric strategies
    against well-known algebraic properties.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st


@given(x=st.integers(-1000, 1000), y=st.integers(-1000, 1000))
def test_addition_commutative(x, y):
    """
        Integer addition is commutative: x + y == y + x.
    """
    testbase.assert_equal(x + y, y + x,
        f"Addition should be commutative: {x} + {y} != {y} + {x}.")


@given(
    x=st.integers(-500, 500),
    y=st.integers(-500, 500),
    z=st.integers(-500, 500)
)
def test_addition_associative(x, y, z):
    """
        Integer addition is associative: (x + y) + z == x + (y + z).
    """
    testbase.assert_equal((x + y) + z, x + (y + z),
        f"Addition should be associative for ({x}, {y}, {z}).")


@given(x=st.integers(-1000, 1000))
def test_additive_identity(x):
    """
        Zero is the additive identity: x + 0 == x.
    """
    testbase.assert_equal(x + 0, x,
        f"x + 0 should equal x for x={x}.")


@given(x=st.integers(-1000, 1000))
def test_additive_inverse(x):
    """
        Every integer has an additive inverse: x + (-x) == 0.
    """
    testbase.assert_equal(x + (-x), 0,
        f"x + (-x) should equal 0 for x={x}.")


@given(x=st.integers(-100, 100), y=st.integers(-100, 100))
def test_multiplication_commutative(x, y):
    """
        Integer multiplication is commutative: x * y == y * x.
    """
    testbase.assert_equal(x * y, y * x,
        f"Multiplication should be commutative: {x} * {y} != {y} * {x}.")


@given(x=st.integers(-100, 100))
def test_multiplicative_identity(x):
    """
        One is the multiplicative identity: x * 1 == x.
    """
    testbase.assert_equal(x * 1, x,
        f"x * 1 should equal x for x={x}.")


@given(
    x=st.integers(-50, 50),
    y=st.integers(-50, 50),
    z=st.integers(-50, 50)
)
def test_distributive_property(x, y, z):
    """
        Multiplication distributes over addition: x * (y + z) == x*y + x*z.
    """
    testbase.assert_equal(x * (y + z), x * y + x * z,
        f"Distributive property failed for ({x}, {y}, {z}).")


@given(x=st.integers(0, 10000))
def test_integer_division_roundtrip(x):
    """
        For non-negative integer division by a positive divisor,
        the quotient and remainder reconstruct the original:
        x == (x // d) * d + (x % d) for all d > 0.
    """
    for d in [1, 2, 3, 7, 10, 100]:
        quotient = x // d
        remainder = x % d
        reconstructed = quotient * d + remainder
        testbase.assert_equal(x, reconstructed,
            f"Division roundtrip failed: {x} // {d} = {quotient}, {x} % {d} = {remainder}.")


@given(x=st.integers(0, 1000000))
def test_absolute_value_non_negative(x):
    """
        The absolute value of any integer is non-negative.
    """
    testbase.assert_true(abs(x) >= 0,
        f"abs({x}) should be non-negative.")
    testbase.assert_true(abs(-x) >= 0,
        f"abs({-x}) should be non-negative.")
    testbase.assert_equal(abs(x), abs(-x),
        f"abs({x}) should equal abs({-x}).")


@given(
    base=st.integers(2, 10),
    exp=st.integers(0, 6),
    constraints={"max_examples": 50}
)
def test_power_of_base(base, exp):
    """
        base^exp computed via ** matches repeated multiplication.
    """
    expected = 1
    for _ in range(exp):
        expected *= base
    testbase.assert_equal(base ** exp, expected,
        f"{base}**{exp} should equal repeated multiplication ({expected}).")


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
