"""
    .. module:: automojo_tests.testbase.properties.test_decorators
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the @given decorator and settings() function.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

import unittest

from automojo.testbase.properties.decorators import given, settings
from automojo.testbase.properties.strategies import integers, text, booleans
from automojo.testbase.properties.propertysettings import PropertySettings


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

    def test_given_with_settings(self):
        """Test that @given accepts and stores settings."""
        ps = settings(max_examples=50, seed=42)

        @given(x=integers(), settings=ps)
        def test_func(x):
            pass

        self.assertIsInstance(test_func._property_['settings'], PropertySettings)
        self.assertEqual(test_func._property_['settings'].max_examples, 50)
        self.assertEqual(test_func._property_['settings'].seed, 42)

    def test_given_default_settings(self):
        """Test that @given uses default settings when none provided."""
        @given(x=integers())
        def test_func(x):
            pass

        self.assertIsInstance(test_func._property_['settings'], PropertySettings)
        self.assertEqual(test_func._property_['settings'].max_examples, 100)
        self.assertIsNone(test_func._property_['settings'].seed)

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


class SettingsFunctionTests(unittest.TestCase):
    """Tests for the settings() helper function."""

    def test_settings_returns_property_settings(self):
        """Test that settings() returns a PropertySettings instance."""
        ps = settings()
        self.assertIsInstance(ps, PropertySettings)

    def test_settings_with_max_examples(self):
        """Test settings() with custom max_examples."""
        ps = settings(max_examples=200)
        self.assertEqual(ps.max_examples, 200)

    def test_settings_with_seed(self):
        """Test settings() with custom seed."""
        ps = settings(seed=12345)
        self.assertEqual(ps.seed, 12345)

    def test_settings_with_max_shrink_attempts(self):
        """Test settings() with custom max_shrink_attempts."""
        ps = settings(max_shrink_attempts=50)
        self.assertEqual(ps.max_shrink_attempts, 50)

    def test_settings_with_all_params(self):
        """Test settings() with all parameters."""
        ps = settings(max_examples=50, seed=999, max_shrink_attempts=25)
        self.assertEqual(ps.max_examples, 50)
        self.assertEqual(ps.seed, 999)
        self.assertEqual(ps.max_shrink_attempts, 25)

    def test_settings_defaults(self):
        """Test settings() default values."""
        ps = settings()
        self.assertEqual(ps.max_examples, 100)
        self.assertIsNone(ps.seed)
        self.assertEqual(ps.max_shrink_attempts, 100)


if __name__ == '__main__':
    unittest.main()
