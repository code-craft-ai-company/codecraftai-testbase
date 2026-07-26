"""
    .. module:: ccai_tests.testbase.properties.test_strategies
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the property testing strategies.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

import unittest
import random
import re
import unicodedata

from ccai.testbase.properties.strategies import (
    from_regex,
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
    MappedStrategy,
    FilteredStrategy,
    FlatMappedStrategy,
    NoneStrategy,
    BinaryStrategy,
    SetStrategy,
    FrozenSetStrategy,
    FixedDictionaryStrategy,
    BuildsStrategy,
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
    none,
    binary,
    sets,
    frozensets,
    fixed_dictionaries,
    builds,
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


# =============================================================================
# Strategy Combinator Tests
# =============================================================================


class MappedStrategyTests(unittest.TestCase):
    """Tests for the .map() combinator."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_map_transforms_value(self):
        """Test that map applies the function to generated values."""
        strat = integers(0, 100).map(lambda x: x * 2)
        for _ in range(50):
            value = strat.generate(self.rng)
            self.assertEqual(value % 2, 0)  # always even

    def test_map_abs(self):
        """Test mapping with abs to produce non-negative values."""
        strat = integers(-100, 100).map(abs)
        for _ in range(50):
            value = strat.generate(self.rng)
            self.assertGreaterEqual(value, 0)

    def test_map_to_string(self):
        """Test mapping integers to strings."""
        strat = integers(0, 10).map(str)
        for _ in range(20):
            value = strat.generate(self.rng)
            self.assertIsInstance(value, str)

    def test_map_describe(self):
        """Test describe output includes .map(...)."""
        strat = integers().map(abs)
        desc = strat.describe()
        self.assertIn("integers()", desc)
        self.assertIn(".map(...)", desc)

    def test_map_deterministic(self):
        """Test that mapped strategies are deterministic with same seed."""
        strat = integers(0, 100).map(lambda x: x * 3)
        rng1 = random.Random(999)
        rng2 = random.Random(999)
        vals1 = [strat.generate(rng1) for _ in range(20)]
        vals2 = [strat.generate(rng2) for _ in range(20)]
        self.assertEqual(vals1, vals2)


class FilteredStrategyTests(unittest.TestCase):
    """Tests for the .filter() combinator."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_filter_excludes_values(self):
        """Test that filter excludes values not matching predicate."""
        strat = integers(-100, 100).filter(lambda x: x > 0)
        for _ in range(50):
            value = strat.generate(self.rng)
            self.assertGreater(value, 0)

    def test_filter_non_zero(self):
        """Test filtering out zero."""
        strat = integers(-10, 10).filter(lambda x: x != 0)
        for _ in range(50):
            value = strat.generate(self.rng)
            self.assertNotEqual(value, 0)

    def test_filter_even_numbers(self):
        """Test filtering for even numbers."""
        strat = integers(0, 100).filter(lambda x: x % 2 == 0)
        for _ in range(50):
            value = strat.generate(self.rng)
            self.assertEqual(value % 2, 0)

    def test_filter_exhaustion_raises(self):
        """Test that impossible filter raises UnsatisfiedAssumption."""
        from ccai.testbase.properties.assumptions import UnsatisfiedAssumption
        strat = integers(0, 10).filter(lambda x: x > 100, max_tries=10)
        with self.assertRaises(UnsatisfiedAssumption):
            strat.generate(self.rng)

    def test_filter_shrink_preserves_predicate(self):
        """Test that filtered shrinking only yields satisfying values."""
        strat = integers(-100, 100).filter(lambda x: x > 0)
        shrinks = list(strat.shrink(50))
        for s in shrinks:
            self.assertGreater(s, 0)

    def test_filter_describe(self):
        """Test describe output includes .filter(...)."""
        strat = integers().filter(lambda x: x > 0)
        desc = strat.describe()
        self.assertIn("integers()", desc)
        self.assertIn(".filter(...)", desc)

    def test_filter_deterministic(self):
        """Test that filtered strategies are deterministic with same seed."""
        strat = integers(0, 100).filter(lambda x: x % 3 == 0)
        rng1 = random.Random(888)
        rng2 = random.Random(888)
        vals1 = [strat.generate(rng1) for _ in range(20)]
        vals2 = [strat.generate(rng2) for _ in range(20)]
        self.assertEqual(vals1, vals2)


class FlatMappedStrategyTests(unittest.TestCase):
    """Tests for the .flatmap() combinator."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_flatmap_dependent_generation(self):
        """Test that flatmap creates dependent strategies."""
        # Generate a length n, then generate a string of exactly length n
        strat = integers(1, 5).flatmap(
            lambda n: text(min_size=n, max_size=n)
        )
        for _ in range(50):
            value = strat.generate(self.rng)
            self.assertIsInstance(value, str)
            self.assertGreaterEqual(len(value), 1)
            self.assertLessEqual(len(value), 5)

    def test_flatmap_describe(self):
        """Test describe output includes .flatmap(...)."""
        strat = integers(1, 5).flatmap(
            lambda n: text(min_size=n, max_size=n)
        )
        desc = strat.describe()
        self.assertIn(".flatmap(...)", desc)

    def test_flatmap_deterministic(self):
        """Test that flatmapped strategies are deterministic with same seed."""
        strat = integers(1, 3).flatmap(
            lambda n: lists(booleans(), min_size=n, max_size=n)
        )
        rng1 = random.Random(777)
        rng2 = random.Random(777)
        vals1 = [strat.generate(rng1) for _ in range(20)]
        vals2 = [strat.generate(rng2) for _ in range(20)]
        self.assertEqual(vals1, vals2)


# =============================================================================
# Additional Strategy Tests
# =============================================================================


class NoneStrategyTests(unittest.TestCase):
    """Tests for the none() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_generate_returns_none(self):
        strat = none()
        for _ in range(10):
            self.assertIsNone(strat.generate(self.rng))

    def test_describe(self):
        strat = none()
        self.assertEqual(strat.describe(), "none()")


class BinaryStrategyTests(unittest.TestCase):
    """Tests for the binary() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_generate_returns_bytes(self):
        strat = binary()
        value = strat.generate(self.rng)
        self.assertIsInstance(value, bytes)

    def test_generate_within_size_bounds(self):
        strat = binary(min_size=2, max_size=5)
        for _ in range(100):
            value = strat.generate(self.rng)
            self.assertGreaterEqual(len(value), 2)
            self.assertLessEqual(len(value), 5)

    def test_shrink_includes_empty_bytes(self):
        strat = binary()
        shrinks = list(strat.shrink(b"\x01\x02\x03"))
        self.assertIn(b"", shrinks)

    def test_shrink_includes_first_half(self):
        strat = binary()
        shrinks = list(strat.shrink(b"\x01\x02\x03\x04"))
        self.assertIn(b"\x01\x02", shrinks)

    def test_shrink_empty_yields_nothing(self):
        strat = binary()
        shrinks = list(strat.shrink(b""))
        self.assertEqual(shrinks, [])

    def test_describe(self):
        strat = binary()
        self.assertEqual(strat.describe(), "binary()")

    def test_describe_with_params(self):
        strat = binary(min_size=5, max_size=10)
        desc = strat.describe()
        self.assertIn("min_size=5", desc)
        self.assertIn("max_size=10", desc)

    def test_deterministic(self):
        strat = binary(max_size=10)
        rng1 = random.Random(123)
        rng2 = random.Random(123)
        vals1 = [strat.generate(rng1) for _ in range(20)]
        vals2 = [strat.generate(rng2) for _ in range(20)]
        self.assertEqual(vals1, vals2)


class SetStrategyTests(unittest.TestCase):
    """Tests for the sets() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_generate_returns_set(self):
        strat = sets(integers(0, 100))
        value = strat.generate(self.rng)
        self.assertIsInstance(value, set)

    def test_generate_within_size_bounds(self):
        strat = sets(integers(0, 1000), min_size=2, max_size=5)
        for _ in range(50):
            value = strat.generate(self.rng)
            self.assertGreaterEqual(len(value), 2)
            self.assertLessEqual(len(value), 5)

    def test_elements_are_unique(self):
        """Sets naturally enforce uniqueness."""
        strat = sets(integers(0, 5), max_size=5)
        for _ in range(20):
            value = strat.generate(self.rng)
            self.assertEqual(len(value), len(list(value)))

    def test_shrink_includes_empty_set(self):
        strat = sets(integers(0, 10))
        shrinks = list(strat.shrink({1, 2, 3}))
        self.assertIn(set(), shrinks)

    def test_shrink_empty_yields_nothing(self):
        strat = sets(integers())
        shrinks = list(strat.shrink(set()))
        self.assertEqual(shrinks, [])

    def test_describe(self):
        strat = sets(integers())
        desc = strat.describe()
        self.assertIn("sets(", desc)
        self.assertIn("integers()", desc)


class FrozenSetStrategyTests(unittest.TestCase):
    """Tests for the frozensets() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_generate_returns_frozenset(self):
        strat = frozensets(integers(0, 100))
        value = strat.generate(self.rng)
        self.assertIsInstance(value, frozenset)

    def test_shrink_returns_frozensets(self):
        strat = frozensets(integers(0, 10))
        shrinks = list(strat.shrink(frozenset({1, 2, 3})))
        for s in shrinks:
            self.assertIsInstance(s, frozenset)

    def test_describe(self):
        strat = frozensets(integers())
        desc = strat.describe()
        self.assertIn("frozensets(", desc)


class FixedDictionaryStrategyTests(unittest.TestCase):
    """Tests for the fixed_dictionaries() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_generate_returns_dict_with_correct_keys(self):
        strat = fixed_dictionaries({
            "name": text(max_size=10),
            "age": integers(0, 120),
            "active": booleans(),
        })
        for _ in range(20):
            value = strat.generate(self.rng)
            self.assertIsInstance(value, dict)
            self.assertEqual(set(value.keys()), {"name", "age", "active"})
            self.assertIsInstance(value["name"], str)
            self.assertIsInstance(value["age"], int)
            self.assertIsInstance(value["active"], bool)

    def test_shrink_yields_dicts_with_same_keys(self):
        strat = fixed_dictionaries({
            "x": integers(0, 100),
            "y": integers(0, 100),
        })
        shrinks = list(strat.shrink({"x": 50, "y": 50}))
        for s in shrinks:
            self.assertEqual(set(s.keys()), {"x", "y"})

    def test_describe(self):
        strat = fixed_dictionaries({
            "x": integers(),
            "y": text(),
        })
        desc = strat.describe()
        self.assertIn("fixed_dictionaries(", desc)
        self.assertIn("'x'", desc)
        self.assertIn("'y'", desc)

    def test_deterministic(self):
        strat = fixed_dictionaries({
            "a": integers(0, 10),
            "b": booleans(),
        })
        rng1 = random.Random(555)
        rng2 = random.Random(555)
        vals1 = [strat.generate(rng1) for _ in range(20)]
        vals2 = [strat.generate(rng2) for _ in range(20)]
        self.assertEqual(vals1, vals2)


class BuildsStrategyTests(unittest.TestCase):
    """Tests for the builds() strategy."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_builds_with_kwargs(self):
        """Test building a dict-like object with kwargs."""
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        strat = builds(Point, x=integers(0, 10), y=integers(0, 10))
        for _ in range(20):
            value = strat.generate(self.rng)
            self.assertIsInstance(value, Point)
            self.assertGreaterEqual(value.x, 0)
            self.assertLessEqual(value.x, 10)
            self.assertGreaterEqual(value.y, 0)
            self.assertLessEqual(value.y, 10)

    def test_builds_with_positional_args(self):
        """Test building with positional strategies."""
        strat = builds(complex, integers(0, 5), integers(0, 5))
        for _ in range(20):
            value = strat.generate(self.rng)
            self.assertIsInstance(value, complex)

    def test_builds_describe(self):
        class Foo:
            def __init__(self, a, b):
                pass

        strat = builds(Foo, a=integers(), b=text())
        desc = strat.describe()
        self.assertIn("builds(Foo", desc)
        self.assertIn("integers()", desc)
        self.assertIn("text()", desc)

    def test_builds_deterministic(self):
        strat = builds(dict, x=integers(0, 10), y=booleans())
        rng1 = random.Random(444)
        rng2 = random.Random(444)
        vals1 = [strat.generate(rng1) for _ in range(20)]
        vals2 = [strat.generate(rng2) for _ in range(20)]
        self.assertEqual(vals1, vals2)


# =============================================================================
# Determinism tests for new strategies
# =============================================================================


class NewStrategyReproducibilityTests(unittest.TestCase):
    """Tests that each new strategy produces identical sequences given the same seed."""

    SEED = 8888
    NUM_SAMPLES = 20

    def _assert_deterministic(self, strategy, msg=None):
        rng1 = random.Random(self.SEED)
        rng2 = random.Random(self.SEED)
        vals1 = [strategy.generate(rng1) for _ in range(self.NUM_SAMPLES)]
        vals2 = [strategy.generate(rng2) for _ in range(self.NUM_SAMPLES)]
        self.assertEqual(vals1, vals2, msg or f"Non-deterministic: {strategy.describe()}")

    def test_none_deterministic(self):
        self._assert_deterministic(none())

    def test_binary_deterministic(self):
        self._assert_deterministic(binary(max_size=10))

    def test_fixed_dictionaries_deterministic(self):
        self._assert_deterministic(fixed_dictionaries({
            "a": integers(0, 10),
            "b": booleans(),
        }))

    def test_map_deterministic(self):
        self._assert_deterministic(integers(0, 100).map(lambda x: x * 2))

    def test_filter_deterministic(self):
        self._assert_deterministic(integers(0, 100).filter(lambda x: x % 2 == 0))

    def test_flatmap_deterministic(self):
        self._assert_deterministic(
            integers(1, 3).flatmap(lambda n: lists(booleans(), min_size=n, max_size=n))
        )


class CharacterCodepointTests(unittest.TestCase):
    """
        Verifies the codepoint range support on ``characters()``.
    """

    def test_codepoint_range_bounds_the_output(self):
        """
            Every generated character falls inside the requested range.
        """
        strategy = characters(min_codepoint=33, max_codepoint=126)
        rng = random.Random(11)

        for _ in range(500):
            point = ord(strategy.generate(rng))
            self.assertGreaterEqual(point, 33)
            self.assertLessEqual(point, 126)

    def test_codepoint_range_is_inclusive_at_both_ends(self):
        """
            A single-codepoint range yields exactly that character.
        """
        strategy = characters(min_codepoint=65, max_codepoint=65)
        rng = random.Random(12)

        self.assertEqual(strategy.generate(rng), "A")

    def test_min_codepoint_alone_defaults_the_upper_bound(self):
        strategy = characters(min_codepoint=48)
        rng = random.Random(13)

        for _ in range(50):
            self.assertGreaterEqual(ord(strategy.generate(rng)), 48)

    def test_max_codepoint_alone_defaults_the_lower_bound(self):
        strategy = characters(max_codepoint=57)
        rng = random.Random(14)

        for _ in range(50):
            self.assertLessEqual(ord(strategy.generate(rng)), 57)

    def test_surrogates_are_excluded(self):
        """
            Surrogate codepoints are skipped.

            They are not independently encodable, so a generated string
            containing one cannot be written out — and that failure would
            surface far away from the strategy that produced it.
        """
        strategy = characters(min_codepoint=0xD7FF, max_codepoint=0xE000)
        rng = random.Random(15)

        for _ in range(300):
            point = ord(strategy.generate(rng))
            self.assertFalse(0xD800 <= point <= 0xDFFF)

    def test_explicit_characters_take_precedence(self):
        strategy = characters(characters="abc", min_codepoint=33,
                              max_codepoint=126)
        rng = random.Random(16)

        for _ in range(50):
            self.assertIn(strategy.generate(rng), "abc")

    def test_inverted_range_is_refused(self):
        """
            An inverted range raises rather than silently widening.

            It is always a mistake at the call site, and quietly returning
            some other character set would hide it.
        """
        with self.assertRaises(ValueError):
            characters(min_codepoint=99, max_codepoint=10)

    def test_categories_still_work_without_codepoints(self):
        strategy = characters(categories=("Nd",))
        rng = random.Random(17)

        for _ in range(50):
            self.assertTrue(strategy.generate(rng).isdigit())


class CharacterCategoryFilterTests(unittest.TestCase):
    """
        Verifies whitelist/blacklist category support on ``characters()``.
    """

    def test_whitelist_categories_selects_those_categories(self):
        strategy = characters(whitelist_categories=("Ll", "Lu"))
        rng = random.Random(21)

        for _ in range(200):
            self.assertTrue(strategy.generate(rng).isalpha())

    def test_whitelist_categories_matches_categories(self):
        """
            whitelist_categories is the same request as categories.
        """
        rng_a = random.Random(22)
        rng_b = random.Random(22)

        first = characters(categories=("Nd",))
        second = characters(whitelist_categories=("Nd",))

        self.assertEqual([first.generate(rng_a) for _ in range(20)],
                         [second.generate(rng_b) for _ in range(20)])

    def test_categories_takes_precedence_over_whitelist(self):
        strategy = characters(categories=("Nd",),
                              whitelist_categories=("Lu",))
        rng = random.Random(23)

        for _ in range(50):
            self.assertTrue(strategy.generate(rng).isdigit())

    def test_blacklist_excludes_control_and_surrogate_categories(self):
        """
            Cc and Cs are the categories callers actually exclude, and neither
            appears in the approximate _CATEGORY_MAP — so exclusion has to use
            each character's real unicode category.
        """
        strategy = characters(min_codepoint=0, max_codepoint=300,
                              blacklist_categories=("Cc", "Cs"))
        rng = random.Random(24)

        for _ in range(500):
            category = unicodedata.category(strategy.generate(rng))
            self.assertNotIn(category, ("Cc", "Cs"))

    def test_blacklist_major_class_excludes_its_subcategories(self):
        """
            A one-letter code matches the whole major class.
        """
        strategy = characters(min_codepoint=0, max_codepoint=300,
                              blacklist_categories=("C",))
        rng = random.Random(25)

        for _ in range(300):
            category = unicodedata.category(strategy.generate(rng))
            self.assertNotEqual(category[:1], "C")

    def test_blacklist_composes_with_an_explicit_set(self):
        strategy = characters(characters="ab1!",
                             blacklist_categories=("Nd",))
        rng = random.Random(26)

        for _ in range(50):
            self.assertNotEqual(strategy.generate(rng), "1")

    def test_blacklist_that_removes_everything_is_refused(self):
        """
            An exclusion leaving no candidates raises here rather than failing
            later inside generate().
        """
        with self.assertRaises(ValueError):
            characters(characters="abc", blacklist_categories=("L",))


class RegexStrategyTests(unittest.TestCase):
    """
        Verifies regex-directed generation.
    """

    _DNS_LABEL = r"^[a-z]([a-z0-9-]{0,12}[a-z0-9])?$"

    def test_generates_only_matching_values(self):
        strategy = from_regex(re.compile(self._DNS_LABEL), fullmatch=True)
        rng = random.Random(31)

        for _ in range(300):
            self.assertRegex(strategy.generate(rng), self._DNS_LABEL)

    def test_accepts_a_pattern_string(self):
        strategy = from_regex(r"^[0-9]{4}$", fullmatch=True)
        rng = random.Random(32)

        value = strategy.generate(rng)
        self.assertEqual(len(value), 4)
        self.assertTrue(value.isdigit())

    def test_branches_are_both_reachable(self):
        strategy = from_regex(r"^(foo|bar)$", fullmatch=True)
        rng = random.Random(33)

        seen = {strategy.generate(rng) for _ in range(200)}
        self.assertEqual(seen, {"foo", "bar"})

    def test_bounded_repeat_respects_its_range(self):
        strategy = from_regex(r"^[a-z]{2,4}$", fullmatch=True)
        rng = random.Random(34)

        for _ in range(200):
            self.assertIn(len(strategy.generate(rng)), (2, 3, 4))

    def test_escape_classes_are_honoured(self):
        strategy = from_regex(r"^\d{3}$", fullmatch=True)
        rng = random.Random(35)

        for _ in range(100):
            self.assertTrue(strategy.generate(rng).isdigit())

    def test_negated_class_excludes_its_members(self):
        strategy = from_regex(r"^[^0-9]{3}$", fullmatch=True)
        rng = random.Random(36)

        for _ in range(100):
            for character in strategy.generate(rng):
                self.assertFalse(character.isdigit())

    def test_shrink_only_offers_matching_values(self):
        """
            A shrunk value must still match, or the test would be handed
            something the strategy could never have produced.
        """
        strategy = from_regex(re.compile(self._DNS_LABEL), fullmatch=True)

        for candidate in strategy.shrink("abc-def-ghi"):
            self.assertRegex(candidate, self._DNS_LABEL)

    def test_unsupported_construct_is_reported(self):
        """
            A lookahead cannot be generated forward, so it raises with the
            construct named rather than silently producing something else.
        """
        strategy = from_regex(re.compile(r"(?=x)y"), fullmatch=True)

        with self.assertRaises(ValueError):
            strategy.generate(random.Random(37))


if __name__ == '__main__':
    unittest.main()
