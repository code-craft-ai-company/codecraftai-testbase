"""
    .. module:: automojo.testbase.properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based testing support for TestBase.

    This package provides a built-in, stdlib-only property testing engine
    for the TestBase framework. It enables test authors to declare invariants
    via the ``@given`` decorator and strategies, which are then verified
    against randomly generated inputs.

    **Quick Start**::

        from automojo.testbase.properties import given, settings
        from automojo.testbase.properties import strategies as st

        @given(x=st.integers(), y=st.integers())
        def test_addition_commutative(x, y):
            assert x + y == y + x

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.testbase.properties.decorators import (
    given,
    settings,
    expect_exception
)

from automojo.testbase.properties import strategies
from automojo.testbase.properties import strategies as st

from automojo.testbase.properties.propertysettings import PropertySettings
