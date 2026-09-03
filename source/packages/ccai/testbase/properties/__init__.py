"""
    .. module:: ccai.testbase.properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based testing support for TestBase.

    This package provides a built-in, stdlib-only property testing engine
    for the TestBase framework. It enables test authors to declare invariants
    via the ``@given`` decorator and strategies, which are then verified
    against randomly generated inputs.

    **Quick Start**::

        from ccai.testbase.properties import given
        from ccai.testbase.properties import strategies as st

        @given(x=st.integers(), y=st.integers())
        def test_addition_commutative(x, y):
            assert x + y == y + x

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.testbase.properties.decorators import (
    given,
    expect_exception
)

from ccai.testbase.properties.assumptions import assume

from ccai.testbase.properties.unittestsupport import run_property

from ccai.testbase.properties import strategies
from ccai.testbase.properties import strategies as st
