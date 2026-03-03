"""
    .. module:: automojo_tests.testbase.properties.test_strategies
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the property testing strategies.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

import unittest
import random

from automojo.testbase.properties.strategies import (
    Strategy,
    IntegerStrategy,
    FloatStrategy,
    TextStrategy,
    BooleanStrategy,
    ListStrategy,
    TupleStrategy,
    DictionaryStrategy,
    SampledFromStrategy,
    OneOfStrategy,
    JustStrategy,
    CharacterStrategy,
    CompositeStrategy,
    composite,
    integers,
    floats,
    text,
    booleans,
    lists,
    tuples,
    dictionaries,
    sampled_from,
    one_of,
    just,
    characters,
)


class IntegerStrategyTests(unittest.TestCase):
    """Tests for the integers() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_generate_returns_int(self):
        """Test that integers strategy generates integer values."""
        strat = integers()
        value = strat.generate(self.rng)
        self.assertIsInstance(value, int)

    def test_generate_within_range(self):
        """Test that generated integers fall within the specified range."""
        strat = integers(min_value=10, max_value=20)
        for _ in range(100):
            value = strat.generate(self.rng)
            self.assertGreaterEqual(value, 10)
            self.assertLessEqual(value, 20)

    def test_generate_default_range(self):
        """Test that default range generates within expected bounds."""
        strat = integers()
        for _ in range(50):
            value = strat.generate(self.rng)
            self.assertIsInstance(value, int)

    def test_generate_negative_range(self):
        """Test generation with negative range."""
        strat = integers(min_value=-100, max_value=-1)
        for _ in range(50):
            value = strat.generate(self.rng)
            self.assertGreaterEqual(value, -100)
            self.assertLessEqual(value, -1)

    def test_generate_single_value(self):
        """Test generation when min == max."""
        strat = integers(min_value=42, max_value=42)
        for _ in range(10):
            value = strat.generate(self.rng)
            self.assertEqual(value, 42)

    def test_shrink_toward_zero(self):
        """Test that shrinking moves values toward zero."""
        strat = integers()
        shrinks = list(strat.shrink(50))
        self.assertIn(0, shrinks)
        self.assertIn(25, shrinks)  # halved

    def test_shrink_negative_includes_zero(self):
        """Test that shrinking a negative number includes zero."""
        strat = integers()
        shrinks = list(strat.shrink(-50))
        self.assertIn(0, shrinks)

    def test_shrink_zero_yields_nothing(self):
        """Test that shrinking zero yields no candidates."""
        strat = integers()
        shrinks = list(strat.shrink(0))
        self.assertEqual(shrinks, [])

    def test_describe(self):
        """Test strategy description output."""
        strat = integers()
        self.assertEqual(strat.describe(), "integers()")

        strat = integers(min_value=0, max_value=10)
        desc = strat.describe()
        self.assertIn("min_value=0", desc)
        self.assertIn("max_value=10", desc)

    def test_deterministic_with_same_seed(self):
        """Test that the same seed produces the same sequence."""
        strat = integers(0, 1000)
        rng1 = random.Random(123)
        rng2 = random.Random(123)
        vals1 = [strat.generate(rng1) for _ in range(20)]
        vals2 = [strat.generate(rng2) for _ in range(20)]
        self.assertEqual(vals1, vals2)


class FloatStrategyTests(unittest.TestCase):
    """Tests for the floats() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_generate_returns_float(self):
        strat = floats()
        value = strat.generate(self.rng)
        self.assertIsInstance(value, float)

    def test_generate_within_range(self):
        strat = floats(min_value=1.0, max_value=2.0)
        for _ in range(100):
            value = strat.generate(self.rng)
            self.assertGreaterEqual(value, 1.0)
            self.assertLessEqual(value, 2.0)

    def test_shrink_toward_zero(self):
        strat = floats()
        shrinks = list(strat.shrink(4.0))
        self.assertIn(0.0, shrinks)
        self.assertIn(2.0, shrinks)  # halved

    def test_describe(self):
        strat = floats()
        self.assertEqual(strat.describe(), "floats()")


class TextStrategyTests(unittest.TestCase):
    """Tests for the text() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_generate_returns_str(self):
        strat = text()
        value = strat.generate(self.rng)
        self.assertIsInstance(value, str)

    def test_generate_within_size_bounds(self):
        strat = text(min_size=2, max_size=5)
        for _ in range(100):
            value = strat.generate(self.rng)
            self.assertGreaterEqual(len(value), 2)
            self.assertLessEqual(len(value), 5)

    def test_generate_with_custom_alphabet(self):
        strat = text(alphabet="abc", max_size=20)
        for _ in range(50):
            value = strat.generate(self.rng)
            for ch in value:
                self.assertIn(ch, "abc")

    def test_shrink_includes_empty_string(self):
        strat = text()
        shrinks = list(strat.shrink("hello"))
        self.assertIn("", shrinks)

    def test_shrink_includes_first_half(self):
        strat = text()
        shrinks = list(strat.shrink("hello"))
        self.assertIn("he", shrinks)

    def test_shrink_empty_yields_nothing(self):
        strat = text()
        shrinks = list(strat.shrink(""))
        self.assertEqual(shrinks, [])

    def test_describe(self):
        strat = text()
        self.assertEqual(strat.describe(), "text()")


class BooleanStrategyTests(unittest.TestCase):
    """Tests for the booleans() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_generate_returns_bool(self):
        strat = booleans()
        value = strat.generate(self.rng)
        self.assertIsInstance(value, bool)

    def test_generates_both_values(self):
        """Test that both True and False are generated over many trials."""
        strat = booleans()
        values = {strat.generate(self.rng) for _ in range(50)}
        self.assertIn(True, values)
        self.assertIn(False, values)

    def test_shrink_true_to_false(self):
        strat = booleans()
        shrinks = list(strat.shrink(True))
        self.assertEqual(shrinks, [False])

    def test_shrink_false_yields_nothing(self):
        strat = booleans()
        shrinks = list(strat.shrink(False))
        self.assertEqual(shrinks, [])

    def test_describe(self):
        strat = booleans()
        self.assertEqual(strat.describe(), "booleans()")


class ListStrategyTests(unittest.TestCase):
    """Tests for the lists() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_generate_returns_list(self):
        strat = lists(integers())
        value = strat.generate(self.rng)
        self.assertIsInstance(value, list)

    def test_generate_within_size_bounds(self):
        strat = lists(integers(), min_size=2, max_size=5)
        for _ in range(100):
            value = strat.generate(self.rng)
            self.assertGreaterEqual(len(value), 2)
            self.assertLessEqual(len(value), 5)

    def test_generate_elements_are_integers(self):
        strat = lists(integers(0, 10))
        value = strat.generate(self.rng)
        for item in value:
            self.assertIsInstance(item, int)
            self.assertGreaterEqual(item, 0)
            self.assertLessEqual(item, 10)

    def test_shrink_includes_empty_list(self):
        strat = lists(integers())
        shrinks = list(strat.shrink([1, 2, 3]))
        self.assertIn([], shrinks)

    def test_shrink_includes_first_half(self):
        strat = lists(integers())
        shrinks = list(strat.shrink([1, 2, 3, 4]))
        self.assertIn([1, 2], shrinks)

    def test_shrink_includes_removed_elements(self):
        strat = lists(integers())
        shrinks = list(strat.shrink([1, 2, 3]))
        # Should include lists with one element removed
        self.assertIn([2, 3], shrinks)
        self.assertIn([1, 3], shrinks)
        self.assertIn([1, 2], shrinks)

    def test_shrink_empty_list_yields_nothing(self):
        strat = lists(integers())
        shrinks = list(strat.shrink([]))
        self.assertEqual(shrinks, [])

    def test_describe(self):
        strat = lists(integers())
        self.assertEqual(strat.describe(), "lists(integers())")


class TupleStrategyTests(unittest.TestCase):
    """Tests for the tuples() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_generate_returns_tuple(self):
        strat = tuples(integers(), booleans())
        value = strat.generate(self.rng)
        self.assertIsInstance(value, tuple)
        self.assertEqual(len(value), 2)

    def test_generate_correct_types(self):
        strat = tuples(integers(0, 10), text(max_size=5), booleans())
        value = strat.generate(self.rng)
        self.assertIsInstance(value[0], int)
        self.assertIsInstance(value[1], str)
        self.assertIsInstance(value[2], bool)

    def test_shrink_yields_element_wise(self):
        strat = tuples(integers(), booleans())
        shrinks = list(strat.shrink((5, True)))
        # Should attempt shrinking individual elements
        self.assertTrue(len(shrinks) > 0)

    def test_describe(self):
        strat = tuples(integers(), booleans())
        desc = strat.describe()
        self.assertIn("integers()", desc)
        self.assertIn("booleans()", desc)


class DictionaryStrategyTests(unittest.TestCase):
    """Tests for the dictionaries() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_generate_returns_dict(self):
        strat = dictionaries(integers(0, 10), text(max_size=5))
        value = strat.generate(self.rng)
        self.assertIsInstance(value, dict)

    def test_generate_within_size_bounds(self):
        strat = dictionaries(integers(0, 100), booleans(), min_size=1, max_size=3)
        for _ in range(50):
            value = strat.generate(self.rng)
            self.assertGreaterEqual(len(value), 1)
            self.assertLessEqual(len(value), 3)

    def test_shrink_includes_empty_dict(self):
        strat = dictionaries(integers(0, 10), text(max_size=5))
        shrinks = list(strat.shrink({1: "a", 2: "b"}))
        self.assertIn({}, shrinks)

    def test_describe(self):
        strat = dictionaries(integers(), text())
        desc = strat.describe()
        self.assertIn("integers()", desc)
        self.assertIn("text()", desc)


class SampledFromStrategyTests(unittest.TestCase):
    """Tests for the sampled_from() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_generate_returns_element_from_list(self):
        elements = ["a", "b", "c"]
        strat = sampled_from(elements)
        for _ in range(50):
            value = strat.generate(self.rng)
            self.assertIn(value, elements)

    def test_all_elements_reachable(self):
        elements = ["x", "y", "z"]
        strat = sampled_from(elements)
        values = {strat.generate(self.rng) for _ in range(100)}
        for e in elements:
            self.assertIn(e, values)

    def test_shrink_yields_nothing(self):
        strat = sampled_from(["a", "b"])
        shrinks = list(strat.shrink("a"))
        self.assertEqual(shrinks, [])

    def test_describe(self):
        strat = sampled_from(["a", "b", "c"])
        desc = strat.describe()
        self.assertIn("sampled_from", desc)


class OneOfStrategyTests(unittest.TestCase):
    """Tests for the one_of() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_generate_returns_value_from_one_strategy(self):
        strat = one_of(integers(0, 5), text(max_size=3))
        for _ in range(50):
            value = strat.generate(self.rng)
            self.assertTrue(isinstance(value, (int, str)))

    def test_describe(self):
        strat = one_of(integers(), text())
        desc = strat.describe()
        self.assertIn("one_of", desc)
        self.assertIn("integers()", desc)
        self.assertIn("text()", desc)


class JustStrategyTests(unittest.TestCase):
    """Tests for the just() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_generate_always_returns_same_value(self):
        strat = just(42)
        for _ in range(20):
            self.assertEqual(strat.generate(self.rng), 42)

    def test_generate_with_string(self):
        strat = just("hello")
        self.assertEqual(strat.generate(self.rng), "hello")

    def test_generate_with_none(self):
        strat = just(None)
        self.assertIsNone(strat.generate(self.rng))

    def test_shrink_yields_nothing(self):
        strat = just(42)
        self.assertEqual(list(strat.shrink(42)), [])

    def test_describe(self):
        strat = just(42)
        desc = strat.describe()
        self.assertIn("42", desc)


class CharacterStrategyTests(unittest.TestCase):
    """Tests for the characters() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_generate_returns_single_char(self):
        strat = characters()
        value = strat.generate(self.rng)
        self.assertIsInstance(value, str)
        self.assertEqual(len(value), 1)

    def test_generate_with_explicit_set(self):
        strat = characters(characters="xyz")
        for _ in range(50):
            value = strat.generate(self.rng)
            self.assertIn(value, "xyz")

    def test_describe(self):
        strat = characters()
        desc = strat.describe()
        self.assertIn("characters", desc)


class CompositeStrategyTests(unittest.TestCase):
    """Tests for the @composite decorator."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_composite_basic(self):
        """Test basic composite strategy creation."""
        @composite
        def sorted_list(draw, max_size=5):
            xs = draw(lists(integers(0, 20), max_size=max_size))
            return sorted(xs)

        strat = sorted_list(max_size=3)
        value = strat.generate(self.rng)
        self.assertIsInstance(value, list)
        self.assertEqual(value, sorted(value))

    def test_composite_with_multiple_draws(self):
        """Test composite strategy with multiple draw calls."""
        @composite
        def pair(draw):
            a = draw(integers(0, 100))
            b = draw(integers(a, 100))  # b >= a
            return (a, b)

        strat = pair()
        value = strat.generate(self.rng)
        self.assertIsInstance(value, tuple)
        self.assertLessEqual(value[0], value[1])

    def test_composite_describe(self):
        @composite
        def my_strat(draw):
            return draw(integers())

        strat = my_strat()
        desc = strat.describe()
        self.assertIn("composite", desc)
        self.assertIn("my_strat", desc)


class StrategyReproducibilityTests(unittest.TestCase):
    """Tests that each strategy produces identical sequences given the same seed."""

    SEED = 7777
    NUM_SAMPLES = 20

    def _assert_deterministic(self, strategy, msg=None):
        """Helper: verify identical sequences from two independently-seeded RNGs."""
        rng1 = random.Random(self.SEED)
        rng2 = random.Random(self.SEED)
        vals1 = [strategy.generate(rng1) for _ in range(self.NUM_SAMPLES)]
        vals2 = [strategy.generate(rng2) for _ in range(self.NUM_SAMPLES)]
        self.assertEqual(vals1, vals2, msg or f"Non-deterministic: {strategy.describe()}")

    def test_integers_deterministic(self):
        """integers() produces the same sequence of values with the same seed."""
        self._assert_deterministic(integers(-1000, 1000))

    def test_integers_custom_range_deterministic(self):
        """integers(0, 10) produces the same sequence with the same seed."""
        self._assert_deterministic(integers(0, 10))

    def test_floats_deterministic(self):
        """floats() produces the same sequence of values with the same seed."""
        self._assert_deterministic(floats(-100.0, 100.0))

    def test_text_deterministic(self):
        """text() produces the same sequence of strings with the same seed."""
        self._assert_deterministic(text(max_size=20))

    def test_text_custom_alphabet_deterministic(self):
        """text(alphabet='abc') produces the same sequence with the same seed."""
        self._assert_deterministic(text(alphabet="abc", min_size=1, max_size=10))

    def test_booleans_deterministic(self):
        """booleans() produces the same sequence of booleans with the same seed."""
        self._assert_deterministic(booleans())

    def test_lists_deterministic(self):
        """lists(integers()) produces the same sequence of lists with the same seed."""
        self._assert_deterministic(lists(integers(0, 50), max_size=8))

    def test_tuples_deterministic(self):
        """tuples(integers(), booleans()) produces the same sequence with the same seed."""
        self._assert_deterministic(tuples(integers(0, 100), booleans(), text(max_size=5)))

    def test_dictionaries_deterministic(self):
        """dictionaries() produces the same sequence with the same seed."""
        self._assert_deterministic(dictionaries(integers(0, 20), text(max_size=5), max_size=4))

    def test_sampled_from_deterministic(self):
        """sampled_from() produces the same sequence with the same seed."""
        self._assert_deterministic(sampled_from(["alpha", "beta", "gamma", "delta"]))

    def test_one_of_deterministic(self):
        """one_of() produces the same sequence with the same seed."""
        self._assert_deterministic(one_of(integers(0, 10), booleans()))

    def test_just_deterministic(self):
        """just() always produces the same value regardless of seed."""
        self._assert_deterministic(just("constant"))

    def test_characters_deterministic(self):
        """characters() produces the same sequence with the same seed."""
        self._assert_deterministic(characters(characters="abcdefghij"))

    def test_composite_deterministic(self):
        """@composite strategies produce the same sequence with the same seed."""
        @composite
        def sorted_pair(draw):
            a = draw(integers(0, 100))
            b = draw(integers(a, 200))
            return (a, b)

        self._assert_deterministic(sorted_pair())

    def test_different_seeds_produce_different_sequences(self):
        """Different seeds produce different sequences (statistical check)."""
        strat = integers(0, 1000000)
        rng1 = random.Random(111)
        rng2 = random.Random(222)
        vals1 = [strat.generate(rng1) for _ in range(self.NUM_SAMPLES)]
        vals2 = [strat.generate(rng2) for _ in range(self.NUM_SAMPLES)]
        self.assertNotEqual(vals1, vals2,
            "Different seeds should generally produce different sequences.")


if __name__ == '__main__':
    unittest.main()
