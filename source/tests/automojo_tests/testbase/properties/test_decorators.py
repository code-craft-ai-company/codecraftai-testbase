"""
    .. module:: automojo_tests.testbase.properties.test_decorators
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the @given decorator and expect_exception decorator.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

import unittest

from automojo.testbase.properties.decorators import given, expect_exception
from automojo.testbase.properties.strategies import integers, text, booleans


class GivenDecoratorTests(unittest.TestCase):
    """Tests for the @given decorator."""

    def test_given_attaches_property_metadata(self):
        """Test that @given attaches _property_ attribute with strategies."""
        @given(x=integers(), y=text())
        def test_func(x, y):
            pass

        self.assertTrue(hasattr(test_func, '_property_'))
        self.assertIn('strategies', test_func._property_)
        self.assertIn('x', test_func._property_['strategies'])
        self.assertIn('y', test_func._property_['strategies'])

    def test_given_preserves_function_name(self):
        """Test that @given preserves the original function name."""
        @given(x=integers())
        def my_test_function(x):
            pass

        self.assertEqual(my_test_function.__name__, 'my_test_function')

    def test_given_preserves_docstring(self):
        """Test that @given preserves the original function docstring."""
        @given(x=integers())
        def my_test_function(x):
            """This is a docstring."""
            pass

        self.assertEqual(my_test_function.__doc__, "This is a docstring.")

    def test_given_stores_strategy_instances(self):
        """Test that @given stores actual strategy instances."""
        int_strat = integers(0, 10)
        text_strat = text(max_size=5)

        @given(x=int_strat, y=text_strat)
        def test_func(x, y):
            pass

        self.assertIs(test_func._property_['strategies']['x'], int_strat)
        self.assertIs(test_func._property_['strategies']['y'], text_strat)

    def test_given_with_constraints(self):
        """Test that @given accepts and stores constraints dict."""
        @given(x=integers(), constraints={"max_examples": 50})
        def test_func(x):
            pass

        self.assertIsInstance(test_func._property_['constraints'], dict)
        self.assertEqual(test_func._property_['constraints']['max_examples'], 50)

    def test_given_default_constraints(self):
        """Test that @given uses empty constraints dict when none provided."""
        @given(x=integers())
        def test_func(x):
            pass

        self.assertIsInstance(test_func._property_['constraints'], dict)
        self.assertEqual(len(test_func._property_['constraints']), 0)

    def test_given_with_multiple_strategies(self):
        """Test @given with many parameter strategies."""
        @given(a=integers(), b=text(), c=booleans())
        def test_func(a, b, c):
            pass

        strategies = test_func._property_['strategies']
        self.assertEqual(len(strategies), 3)
        self.assertIn('a', strategies)
        self.assertIn('b', strategies)
        self.assertIn('c', strategies)

    def test_given_function_still_callable(self):
        """Test that the decorated function is still directly callable."""
        @given(x=integers())
        def test_func(x):
            return x * 2

        # Direct call should still work
        result = test_func(x=5)
        self.assertEqual(result, 10)

    def test_given_rejects_non_strategy_kwargs(self):
        """Test that @given raises TypeError for non-Strategy kwargs."""
        with self.assertRaises(TypeError):
            @given(x=42)
            def test_func(x):
                pass

    def test_given_with_full_constraints(self):
        """Test @given with all supported constraint keys."""
        @given(x=integers(), constraints={"max_examples": 200, "max_shrink_attempts": 50})
        def test_func(x):
            pass

        self.assertEqual(test_func._property_['constraints']['max_examples'], 200)
        self.assertEqual(test_func._property_['constraints']['max_shrink_attempts'], 50)


class ExpectExceptionDecoratorTests(unittest.TestCase):
    """Tests for the expect_exception decorator."""

    def test_expect_exception_attaches_metadata(self):
        """Test that expect_exception sets _expect_exception_ attribute."""
        @expect_exception(ValueError, reason="test reason")
        def test_func():
            pass

        self.assertTrue(hasattr(test_func, '_expect_exception_'))
        self.assertEqual(test_func._expect_exception_['exception_type'], ValueError)
        self.assertEqual(test_func._expect_exception_['reason'], 'test reason')

    def test_expect_exception_default_reason(self):
        """Test that expect_exception defaults to empty reason."""
        @expect_exception(RuntimeError)
        def test_func():
            pass

        self.assertEqual(test_func._expect_exception_['reason'], '')


if __name__ == '__main__':
    unittest.main()
