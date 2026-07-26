"""
    .. module:: ccai.testbase.properties.strategies
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for property testing strategies — composable random value generators.

    This module provides the ``Strategy`` base class and a comprehensive set of
    built-in strategy implementations for generating random test inputs. All
    strategies support deterministic generation via ``random.Random`` instances,
    value shrinking for counterexample minimization, and human-readable
    descriptions for query mode output.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple, Union

import functools
import random
import string


class Strategy:
    """
        Abstract base class for all property testing strategies.

        A strategy is a composable generator that produces random values of
        a specific type. Strategies support three operations:

        - **generate(rng)**: Produce a random value using the given RNG
        - **shrink(value)**: Yield progressively simpler versions of a value
        - **describe()**: Return a human-readable description of this strategy

        All built-in strategies use only the ``random`` and ``string`` modules
        from the Python standard library.
    """

    def generate(self, rng: random.Random) -> Any:
        """
            Generate a random value using the provided random number generator.

            :param rng: A ``random.Random`` instance for deterministic generation.
            :returns: A randomly generated value of the appropriate type.
            :raises NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement generate()")

    def shrink(self, value: Any) -> Iterator[Any]:
        """
            Yield progressively simpler versions of the given value.

            The shrinking process attempts to reduce a failing input to
            a minimal counterexample. Yielded values should be "simpler"
            than the input (e.g., closer to zero for integers, shorter
            for strings).

            The default implementation yields nothing (no shrinking).

            :param value: The value to shrink.
            :returns: An iterator of simpler values.
        """
        return iter([])

    def describe(self) -> str:
        """
            Return a human-readable description of this strategy.

            Used in query mode output and error messages to describe
            what kind of values this strategy generates.

            :returns: A string description of the strategy configuration.
        """
        return self.__class__.__name__

    def map(self, fn: Callable) -> 'MappedStrategy':
        """
            Returns a new strategy that applies ``fn`` to each generated value.

            Example::

                st.integers(0, 100).map(lambda x: x * 2)

            :param fn: A callable to transform generated values.
            :returns: A ``MappedStrategy`` wrapping this strategy.
        """
        return MappedStrategy(self, fn)

    def filter(self, predicate: Callable, max_tries: int = 100) -> 'FilteredStrategy':
        """
            Returns a new strategy that only yields values satisfying
            the given predicate.

            If the predicate is not satisfied after ``max_tries`` attempts,
            an ``UnsatisfiedAssumption`` exception is raised.

            Example::

                st.integers(-100, 100).filter(lambda x: x != 0)

            :param predicate: A callable returning truthy for acceptable values.
            :param max_tries: Maximum generation attempts before giving up.
            :returns: A ``FilteredStrategy`` wrapping this strategy.
        """
        return FilteredStrategy(self, predicate, max_tries)

    def flatmap(self, fn: Callable) -> 'FlatMappedStrategy':
        """
            Returns a new strategy that generates a value from this strategy,
            passes it to ``fn`` to obtain a second strategy, and then generates
            from that second strategy.

            Example::

                st.integers(1, 5).flatmap(lambda n: st.text(min_size=n, max_size=n))

            :param fn: A callable that accepts a generated value and returns
                a ``Strategy`` instance.
            :returns: A ``FlatMappedStrategy`` wrapping this strategy.
        """
        return FlatMappedStrategy(self, fn)


class IntegerStrategy(Strategy):
    """
        Strategy that generates random integers within an inclusive range.

        Shrinking moves values toward zero: first yields 0 (if in range),
        then yields the value halved repeatedly.

        :param min_value: The minimum integer value (inclusive). Default is -1000000.
        :param max_value: The maximum integer value (inclusive). Default is 1000000.
    """

    def __init__(self, min_value: int = -1000000, max_value: int = 1000000):
        self._min_value = min_value
        self._max_value = max_value

    def generate(self, rng: random.Random) -> int:
        return rng.randint(self._min_value, self._max_value)

    def shrink(self, value: int) -> Iterator[int]:
        if value == 0:
            return

        # Try zero first
        if self._min_value <= 0 <= self._max_value:
            yield 0

        # Then halve toward zero
        current = value
        while abs(current) > 1:
            current = current // 2
            if self._min_value <= current <= self._max_value and current != 0:
                yield current

    def describe(self) -> str:
        parts = []
        if self._min_value != -1000000:
            parts.append(f"min_value={self._min_value}")
        if self._max_value != 1000000:
            parts.append(f"max_value={self._max_value}")
        args = ", ".join(parts)
        return f"integers({args})"


class FloatStrategy(Strategy):
    """
        Strategy that generates random floating-point numbers within a range.

        Shrinking moves values toward 0.0, halving repeatedly.

        :param min_value: The minimum float value. Default is -1e6.
        :param max_value: The maximum float value. Default is 1e6.
    """

    def __init__(self, min_value: float = -1e6, max_value: float = 1e6):
        self._min_value = min_value
        self._max_value = max_value

    def generate(self, rng: random.Random) -> float:
        return rng.uniform(self._min_value, self._max_value)

    def shrink(self, value: float) -> Iterator[float]:
        if value == 0.0:
            return

        # Try zero first
        if self._min_value <= 0.0 <= self._max_value:
            yield 0.0

        # Then halve toward zero
        current = value
        while abs(current) > 1e-10:
            current = current / 2.0
            if self._min_value <= current <= self._max_value and current != 0.0:
                yield current

    def describe(self) -> str:
        parts = []
        if self._min_value != -1e6:
            parts.append(f"min_value={self._min_value}")
        if self._max_value != 1e6:
            parts.append(f"max_value={self._max_value}")
        args = ", ".join(parts)
        return f"floats({args})"


class BooleanStrategy(Strategy):
    """
        Strategy that generates random boolean values.

        Shrinking yields ``False`` when given ``True``.
    """

    def generate(self, rng: random.Random) -> bool:
        return rng.choice([True, False])

    def shrink(self, value: bool) -> Iterator[bool]:
        if value:
            yield False

    def describe(self) -> str:
        return "booleans()"


class TextStrategy(Strategy):
    """
        Strategy that generates random strings from a given alphabet.

        Shrinking first yields the empty string, then the first half,
        then removes single characters one at a time.

        :param alphabet: The characters to draw from. Can be a string or a
            ``Strategy`` that generates individual characters. Default is
            ASCII letters and digits.
        :param min_size: Minimum string length. Default is 0.
        :param max_size: Maximum string length. Default is 100.
    """

    def __init__(self, alphabet: Union[str, 'Strategy', None] = None,
                 min_size: int = 0, max_size: int = 100):
        if alphabet is None:
            self._alphabet = string.ascii_letters + string.digits
        else:
            self._alphabet = alphabet
        self._min_size = min_size
        self._max_size = max_size

    def generate(self, rng: random.Random) -> str:
        length = rng.randint(self._min_size, self._max_size)
        if isinstance(self._alphabet, Strategy):
            return "".join(self._alphabet.generate(rng) for _ in range(length))
        return "".join(rng.choice(self._alphabet) for _ in range(length))

    def shrink(self, value: str) -> Iterator[str]:
        if len(value) <= self._min_size:
            return

        # Try empty string
        if self._min_size == 0:
            yield ""

        # Try first half
        half = len(value) // 2
        if half >= self._min_size and half > 0:
            yield value[:half]

        # Try removing single characters
        for i in range(len(value)):
            shrunk = value[:i] + value[i + 1:]
            if len(shrunk) >= self._min_size:
                yield shrunk

    def describe(self) -> str:
        parts = []
        if isinstance(self._alphabet, Strategy):
            parts.append(f"alphabet={self._alphabet.describe()}")
        elif self._alphabet != string.ascii_letters + string.digits:
            parts.append(f"alphabet='{self._alphabet}'")
        if self._min_size != 0:
            parts.append(f"min_size={self._min_size}")
        if self._max_size != 100:
            parts.append(f"max_size={self._max_size}")
        args = ", ".join(parts)
        return f"text({args})"


class CharacterStrategy(Strategy):
    """
        Strategy that generates single characters.

        Can generate from a codepoint range, unicode categories, or an
        explicit character set.

        Precedence is: ``characters``, then a codepoint range, then
        ``categories``, then all printable characters.

        :param categories: Tuple of unicode category identifiers to generate from.
            Currently maps to predefined character sets for simplicity.
        :param characters: An explicit string of characters to choose from.
            If provided, takes precedence over everything else.
        :param min_codepoint: Inclusive lower bound of a codepoint range.
        :param max_codepoint: Inclusive upper bound of a codepoint range.
            Either bound may be given alone; the other defaults to 0 or to
            0x10FFFF respectively.
    """

    _CATEGORY_MAP = {
        "L": string.ascii_letters,
        "Lu": string.ascii_uppercase,
        "Ll": string.ascii_lowercase,
        "N": string.digits,
        "Nd": string.digits,
        "P": string.punctuation,
        "S": "!@#$%^&*",
        "Z": " \t\n",
    }

    # Codepoints that cannot stand alone in a str: the surrogate range is not
    # encodable, so including it would make generated text unserialisable.
    _SURROGATE_FIRST = 0xD800
    _SURROGATE_LAST = 0xDFFF

    _MAX_CODEPOINT = 0x10FFFF

    def __init__(self, categories: Optional[Tuple[str, ...]] = None,
                 characters: Optional[str] = None,
                 min_codepoint: Optional[int] = None,
                 max_codepoint: Optional[int] = None):
        if characters is not None:
            self._characters = characters
        elif min_codepoint is not None or max_codepoint is not None:
            self._characters = self._from_codepoints(
                min_codepoint=min_codepoint, max_codepoint=max_codepoint)
        elif categories is not None:
            chars = ""
            for cat in categories:
                chars += self._CATEGORY_MAP.get(cat, "")
            self._characters = chars if chars else string.printable
        else:
            self._characters = string.printable

    @classmethod
    def _from_codepoints(cls, *, min_codepoint: Optional[int],
                         max_codepoint: Optional[int]) -> str:
        """
            Build the character set spanning a codepoint range.

            Surrogates are excluded: they are not independently encodable, so
            a generated string containing one cannot be written out, and the
            failure would surface far from here.

            :param min_codepoint: Inclusive lower bound, or None for 0.
            :param max_codepoint: Inclusive upper bound, or None for the
                maximum codepoint.

            :returns: The character set.

            :raises ValueError: When the range is inverted or empty, which is
                always a mistake at the call site rather than something to
                silently widen.
        """
        low = min_codepoint if min_codepoint is not None else 0
        high = max_codepoint if max_codepoint is not None else \
            cls._MAX_CODEPOINT

        if low > high:
            errmsg = (
                "characters() received an inverted codepoint range: "
                "min_codepoint={} is above max_codepoint={}.".format(low, high)
            )
            raise ValueError(errmsg)

        selected = [
            chr(point) for point in range(low, high + 1)
            if not (cls._SURROGATE_FIRST <= point <= cls._SURROGATE_LAST)
        ]

        if len(selected) == 0:
            errmsg = (
                "characters() codepoint range {}..{} selects no usable "
                "characters.".format(low, high)
            )
            raise ValueError(errmsg)

        rtnval = "".join(selected)
        return rtnval

    def generate(self, rng: random.Random) -> str:
        return rng.choice(self._characters)

    def describe(self) -> str:
        if self._characters == string.printable:
            return "characters()"
        return f"characters(characters='{self._characters[:20]}...')" if len(self._characters) > 20 \
            else f"characters(characters='{self._characters}')"


class ListStrategy(Strategy):
    """
        Strategy that generates random lists of elements.

        Each element is generated using the provided element strategy.
        Shrinking first yields the empty list, then the first half,
        then tries removing single elements.

        :param element: A ``Strategy`` for generating individual list elements.
        :param min_size: Minimum list length. Default is 0.
        :param max_size: Maximum list length. Default is 50.
    """

    def __init__(self, element: Strategy, min_size: int = 0, max_size: int = 50):
        self._element = element
        self._min_size = min_size
        self._max_size = max_size

    def generate(self, rng: random.Random) -> list:
        length = rng.randint(self._min_size, self._max_size)
        return [self._element.generate(rng) for _ in range(length)]

    def shrink(self, value: list) -> Iterator[list]:
        if len(value) <= self._min_size:
            return

        # Try empty list
        if self._min_size == 0:
            yield []

        # Try first half
        half = len(value) // 2
        if half >= self._min_size and half > 0:
            yield value[:half]

        # Try removing single elements
        for i in range(len(value)):
            shrunk = value[:i] + value[i + 1:]
            if len(shrunk) >= self._min_size:
                yield shrunk

    def describe(self) -> str:
        parts = [self._element.describe()]
        if self._min_size != 0:
            parts.append(f"min_size={self._min_size}")
        if self._max_size != 50:
            parts.append(f"max_size={self._max_size}")
        return f"lists({', '.join(parts)})"


class TupleStrategy(Strategy):
    """
        Strategy that generates random tuples with elements from
        the given strategies.

        Each position in the tuple is generated by its corresponding strategy.
        Shrinking attempts to shrink individual elements in order.

        :param strategies: One ``Strategy`` per tuple position.
    """

    def __init__(self, *strategies: Strategy):
        self._strategies = strategies

    def generate(self, rng: random.Random) -> tuple:
        return tuple(s.generate(rng) for s in self._strategies)

    def shrink(self, value: tuple) -> Iterator[tuple]:
        # Try shrinking each element individually
        for i, strategy in enumerate(self._strategies):
            for shrunk_elem in strategy.shrink(value[i]):
                result = list(value)
                result[i] = shrunk_elem
                yield tuple(result)

    def describe(self) -> str:
        inner = ", ".join(s.describe() for s in self._strategies)
        return f"tuples({inner})"


class DictionaryStrategy(Strategy):
    """
        Strategy that generates random dictionaries.

        Keys and values are generated using separate strategies.
        Shrinking first yields the empty dict, then the first half of keys,
        then removes single keys.

        :param keys: A ``Strategy`` for generating dictionary keys.
        :param values: A ``Strategy`` for generating dictionary values.
        :param min_size: Minimum number of entries. Default is 0.
        :param max_size: Maximum number of entries. Default is 20.
    """

    def __init__(self, keys: Strategy, values: Strategy,
                 min_size: int = 0, max_size: int = 20):
        self._keys = keys
        self._values = values
        self._min_size = min_size
        self._max_size = max_size

    def generate(self, rng: random.Random) -> dict:
        length = rng.randint(self._min_size, self._max_size)
        result = {}
        for _ in range(length):
            k = self._keys.generate(rng)
            v = self._values.generate(rng)
            result[k] = v
        return result

    def shrink(self, value: dict) -> Iterator[dict]:
        if len(value) <= self._min_size:
            return

        # Try empty dict
        if self._min_size == 0:
            yield {}

        # Try first half of keys
        keys = list(value.keys())
        half = len(keys) // 2
        if half >= self._min_size and half > 0:
            yield {k: value[k] for k in keys[:half]}

        # Try removing single keys
        for key in keys:
            shrunk = {k: v for k, v in value.items() if k != key}
            if len(shrunk) >= self._min_size:
                yield shrunk

    def describe(self) -> str:
        parts = [self._keys.describe(), self._values.describe()]
        if self._min_size != 0:
            parts.append(f"min_size={self._min_size}")
        if self._max_size != 20:
            parts.append(f"max_size={self._max_size}")
        return f"dictionaries({', '.join(parts)})"


class SampledFromStrategy(Strategy):
    """
        Strategy that randomly selects a value from a fixed sequence.

        No shrinking is performed since the elements are pre-defined.

        :param elements: A sequence of values to sample from.
    """

    def __init__(self, elements: Sequence):
        if len(elements) == 0:
            raise ValueError("sampled_from requires a non-empty sequence")
        self._elements = elements

    def generate(self, rng: random.Random) -> Any:
        return rng.choice(self._elements)

    def describe(self) -> str:
        if len(self._elements) <= 5:
            return f"sampled_from({list(self._elements)})"
        return f"sampled_from([{self._elements[0]}, ... ({len(self._elements)} elements)])"


class OneOfStrategy(Strategy):
    """
        Strategy that randomly selects one sub-strategy and then generates
        a value from it.

        :param strategies: Two or more strategies to choose from.
    """

    def __init__(self, *strategies: Strategy):
        if len(strategies) < 2:
            raise ValueError("one_of requires at least two strategies")
        self._strategies = strategies

    def generate(self, rng: random.Random) -> Any:
        chosen = rng.choice(self._strategies)
        return chosen.generate(rng)

    def shrink(self, value: Any) -> Iterator[Any]:
        # Attempt to shrink using each sub-strategy
        for strategy in self._strategies:
            try:
                for shrunk in strategy.shrink(value):
                    yield shrunk
            except (TypeError, ValueError, AttributeError):
                continue

    def describe(self) -> str:
        inner = ", ".join(s.describe() for s in self._strategies)
        return f"one_of({inner})"


class JustStrategy(Strategy):
    """
        Strategy that always returns the same fixed value.

        No shrinking is performed since the value is constant.

        :param value: The fixed value to always return.
    """

    def __init__(self, value: Any):
        self._value = value

    def generate(self, rng: random.Random) -> Any:
        return self._value

    def describe(self) -> str:
        return f"just({self._value!r})"


class CompositeStrategy(Strategy):
    """
        Strategy defined by a user function that uses a ``draw`` callable
        to pull values from other strategies.

        Created by the ``@composite`` decorator.

        :param fn: The composite strategy function.
        :param args: Positional arguments (beyond the first ``draw`` param).
        :param kwargs: Keyword arguments to pass to the function.
    """

    def __init__(self, fn: Callable, args: tuple = (), kwargs: Optional[dict] = None):
        self._fn = fn
        self._args = args
        self._kwargs = kwargs or {}

    def generate(self, rng: random.Random) -> Any:
        def draw(strategy: Strategy) -> Any:
            return strategy.generate(rng)
        return self._fn(draw, *self._args, **self._kwargs)

    def describe(self) -> str:
        return f"composite({self._fn.__name__})"


class ExplicitStrategy(Strategy):
    """
        Strategy that yields values from a predetermined sequence.

        Values are cycled in order, wrapping around when the sequence
        is exhausted. The random number generator is ignored — this
        strategy always produces the same deterministic sequence.

        No shrinking is performed since the values are user-specified.

        :param values: A non-empty sequence of values to yield.
    """

    def __init__(self, values: Sequence):
        if len(values) == 0:
            raise ValueError("explicit requires a non-empty sequence of values")
        self._values = list(values)
        self._index = 0

    def generate(self, rng: random.Random) -> Any:
        value = self._values[self._index % len(self._values)]
        self._index += 1
        return value

    def describe(self) -> str:
        if len(self._values) <= 3:
            return f"explicit({self._values!r})"
        return f"explicit([{self._values[0]!r}, ... ({len(self._values)} values)])"


# =============================================================================
# Strategy Combinators
# =============================================================================


class MappedStrategy(Strategy):
    """
        Strategy that applies a transformation function to values generated
        by a source strategy.

        Created by :meth:`Strategy.map`.

        :param source: The underlying strategy to generate values from.
        :param fn: A callable applied to each generated value.
    """

    def __init__(self, source: Strategy, fn: Callable):
        self._source = source
        self._fn = fn

    def generate(self, rng: random.Random) -> Any:
        return self._fn(self._source.generate(rng))

    def shrink(self, value: Any) -> Iterator[Any]:
        # We cannot invert the map, so we try shrinking the source
        # and re-mapping. This requires knowing the original pre-map
        # value, which we don't have — so no shrinking for mapped.
        return iter([])

    def describe(self) -> str:
        return f"{self._source.describe()}.map(...)"


class FilteredStrategy(Strategy):
    """
        Strategy that only yields values from a source strategy that
        satisfy a given predicate.

        Created by :meth:`Strategy.filter`.

        :param source: The underlying strategy to generate values from.
        :param predicate: A callable that returns truthy for acceptable values.
        :param max_tries: Maximum generation attempts before raising.
    """

    def __init__(self, source: Strategy, predicate: Callable,
                 max_tries: int = 100):
        self._source = source
        self._predicate = predicate
        self._max_tries = max_tries

    def generate(self, rng: random.Random) -> Any:
        from ccai.testbase.properties.assumptions import UnsatisfiedAssumption

        for _ in range(self._max_tries):
            value = self._source.generate(rng)
            if self._predicate(value):
                return value

        raise UnsatisfiedAssumption(
            f"Could not satisfy filter after {self._max_tries} attempts "
            f"on strategy {self._source.describe()}"
        )

    def shrink(self, value: Any) -> Iterator[Any]:
        for shrunk in self._source.shrink(value):
            if self._predicate(shrunk):
                yield shrunk

    def describe(self) -> str:
        return f"{self._source.describe()}.filter(...)"


class FlatMappedStrategy(Strategy):
    """
        Strategy that generates a value from a source strategy, passes it
        to a function to obtain a second strategy, and generates from that.

        Created by :meth:`Strategy.flatmap`.

        :param source: The underlying strategy to generate the initial value.
        :param fn: A callable that accepts the generated value and returns
            a ``Strategy`` instance.
    """

    def __init__(self, source: Strategy, fn: Callable):
        self._source = source
        self._fn = fn

    def generate(self, rng: random.Random) -> Any:
        first = self._source.generate(rng)
        second_strategy = self._fn(first)
        return second_strategy.generate(rng)

    def describe(self) -> str:
        return f"{self._source.describe()}.flatmap(...)"


# =============================================================================
# Additional Built-in Strategies
# =============================================================================


class NoneStrategy(Strategy):
    """
        Strategy that always generates ``None``.

        No shrinking is performed since the value is constant.
    """

    def generate(self, rng: random.Random) -> None:
        return None

    def describe(self) -> str:
        return "none()"


class BinaryStrategy(Strategy):
    """
        Strategy that generates random ``bytes`` objects.

        Shrinking first yields empty bytes, then the first half,
        then removes single bytes.

        :param min_size: Minimum byte sequence length. Default is 0.
        :param max_size: Maximum byte sequence length. Default is 100.
    """

    def __init__(self, min_size: int = 0, max_size: int = 100):
        self._min_size = min_size
        self._max_size = max_size

    def generate(self, rng: random.Random) -> bytes:
        length = rng.randint(self._min_size, self._max_size)
        return bytes(rng.randint(0, 255) for _ in range(length))

    def shrink(self, value: bytes) -> Iterator[bytes]:
        if len(value) <= self._min_size:
            return

        # Try empty bytes
        if self._min_size == 0:
            yield b""

        # Try first half
        half = len(value) // 2
        if half >= self._min_size and half > 0:
            yield value[:half]

        # Try removing single bytes
        for i in range(len(value)):
            shrunk = value[:i] + value[i + 1:]
            if len(shrunk) >= self._min_size:
                yield shrunk

    def describe(self) -> str:
        parts = []
        if self._min_size != 0:
            parts.append(f"min_size={self._min_size}")
        if self._max_size != 100:
            parts.append(f"max_size={self._max_size}")
        args = ", ".join(parts)
        return f"binary({args})"


class SetStrategy(Strategy):
    """
        Strategy that generates random ``set`` objects.

        Each element is generated using the provided element strategy.
        Due to set uniqueness constraints, the actual size may be smaller
        than requested if the element strategy produces duplicates.

        Shrinking first yields the empty set, then the first half,
        then tries removing single elements.

        :param element: A ``Strategy`` for generating individual set elements.
        :param min_size: Minimum set size. Default is 0.
        :param max_size: Maximum set size. Default is 50.
    """

    def __init__(self, element: Strategy, min_size: int = 0, max_size: int = 50):
        self._element = element
        self._min_size = min_size
        self._max_size = max_size

    def generate(self, rng: random.Random) -> set:
        target_length = rng.randint(self._min_size, self._max_size)
        result = set()
        # Allow extra attempts for uniqueness
        for _ in range(target_length * 3):
            if len(result) >= target_length:
                break
            result.add(self._element.generate(rng))
        return result

    def shrink(self, value: set) -> Iterator[set]:
        if len(value) <= self._min_size:
            return

        # Try empty set
        if self._min_size == 0:
            yield set()

        # Try first half
        items = list(value)
        half = len(items) // 2
        if half >= self._min_size and half > 0:
            yield set(items[:half])

        # Try removing single elements
        for item in items:
            shrunk = value - {item}
            if len(shrunk) >= self._min_size:
                yield shrunk

    def describe(self) -> str:
        parts = [self._element.describe()]
        if self._min_size != 0:
            parts.append(f"min_size={self._min_size}")
        if self._max_size != 50:
            parts.append(f"max_size={self._max_size}")
        return f"sets({', '.join(parts)})"


class FrozenSetStrategy(Strategy):
    """
        Strategy that generates random ``frozenset`` objects.

        Delegates to :class:`SetStrategy` for generation and converts
        the result to a frozenset.

        :param element: A ``Strategy`` for generating individual elements.
        :param min_size: Minimum size. Default is 0.
        :param max_size: Maximum size. Default is 50.
    """

    def __init__(self, element: Strategy, min_size: int = 0, max_size: int = 50):
        self._inner = SetStrategy(element, min_size, max_size)
        self._min_size = min_size

    def generate(self, rng: random.Random) -> frozenset:
        return frozenset(self._inner.generate(rng))

    def shrink(self, value: frozenset) -> Iterator[frozenset]:
        for shrunk_set in self._inner.shrink(set(value)):
            yield frozenset(shrunk_set)

    def describe(self) -> str:
        inner_desc = self._inner.describe()
        # Replace "sets(" with "frozensets("
        return "frozen" + inner_desc


class FixedDictionaryStrategy(Strategy):
    """
        Strategy that generates dictionaries with a fixed set of keys,
        where each key's value is drawn from a corresponding strategy.

        Shrinking attempts to shrink individual values.

        :param mapping: A dictionary mapping keys to ``Strategy`` instances.
    """

    def __init__(self, mapping: Dict[str, Strategy]):
        self._mapping = mapping

    def generate(self, rng: random.Random) -> dict:
        return {
            key: strategy.generate(rng)
            for key, strategy in self._mapping.items()
        }

    def shrink(self, value: dict) -> Iterator[dict]:
        # Try shrinking each value individually
        for key, strategy in self._mapping.items():
            if key in value:
                for shrunk_val in strategy.shrink(value[key]):
                    result = dict(value)
                    result[key] = shrunk_val
                    yield result

    def describe(self) -> str:
        inner = ", ".join(
            f"{k!r}: {v.describe()}" for k, v in self._mapping.items()
        )
        return f"fixed_dictionaries({{{inner}}})"


class BuildsStrategy(Strategy):
    """
        Strategy that constructs instances of a callable (typically a class)
        by generating values for its arguments from strategies.

        :param target: The callable to invoke with generated arguments.
        :param arg_strategies: Positional argument strategies.
        :param kwarg_strategies: Keyword argument strategies.
    """

    def __init__(self, target: Callable, arg_strategies: Tuple[Strategy, ...] = (),
                 kwarg_strategies: Optional[Dict[str, Strategy]] = None):
        self._target = target
        self._arg_strategies = arg_strategies
        self._kwarg_strategies = kwarg_strategies or {}

    def generate(self, rng: random.Random) -> Any:
        args = tuple(s.generate(rng) for s in self._arg_strategies)
        kwargs = {
            k: s.generate(rng) for k, s in self._kwarg_strategies.items()
        }
        return self._target(*args, **kwargs)

    def describe(self) -> str:
        parts = []
        for s in self._arg_strategies:
            parts.append(s.describe())
        for k, s in self._kwarg_strategies.items():
            parts.append(f"{k}={s.describe()}")
        args = ", ".join(parts)
        name = getattr(self._target, '__name__', repr(self._target))
        return f"builds({name}, {args})"


# =============================================================================
# Composite Decorator
# =============================================================================


def composite(fn: Callable) -> Callable:
    """
        Decorator that converts a function into a strategy factory.

        The decorated function receives a ``draw`` callable as its first
        argument. Calling ``draw(strategy)`` pulls a random value from the
        given strategy during generation.

        Example::

            @composite
            def sorted_lists(draw, min_size=0, max_size=10):
                xs = draw(lists(integers(), min_size=min_size, max_size=max_size))
                return sorted(xs)

            # Use as: @given(xs=sorted_lists(min_size=1))

        :param fn: A function that accepts ``draw`` as its first argument
            and returns a generated value.
        :returns: A factory function that produces ``CompositeStrategy`` instances.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return CompositeStrategy(fn, args=args, kwargs=kwargs)
    return wrapper


# =============================================================================
# Public Convenience Functions
# =============================================================================


def integers(min_value: int = -1000000, max_value: int = 1000000) -> IntegerStrategy:
    """
        Creates a strategy that generates random integers within an inclusive range.

        :param min_value: The minimum integer value (inclusive). Default is -1000000.
        :param max_value: The maximum integer value (inclusive). Default is 1000000.
        :returns: An ``IntegerStrategy`` instance.
    """
    return IntegerStrategy(min_value=min_value, max_value=max_value)


def floats(min_value: float = -1e6, max_value: float = 1e6) -> FloatStrategy:
    """
        Creates a strategy that generates random floating-point numbers.

        :param min_value: The minimum float value. Default is -1e6.
        :param max_value: The maximum float value. Default is 1e6.
        :returns: A ``FloatStrategy`` instance.
    """
    return FloatStrategy(min_value=min_value, max_value=max_value)


def text(alphabet: Union[str, Strategy, None] = None,
         min_size: int = 0, max_size: int = 100) -> TextStrategy:
    """
        Creates a strategy that generates random strings.

        :param alphabet: Characters to draw from. Can be a string or a character
            strategy. Default is ASCII letters and digits.
        :param min_size: Minimum string length. Default is 0.
        :param max_size: Maximum string length. Default is 100.
        :returns: A ``TextStrategy`` instance.
    """
    return TextStrategy(alphabet=alphabet, min_size=min_size, max_size=max_size)


def booleans() -> BooleanStrategy:
    """
        Creates a strategy that generates random boolean values.

        :returns: A ``BooleanStrategy`` instance.
    """
    return BooleanStrategy()


def lists(element: Strategy, min_size: int = 0, max_size: int = 50) -> ListStrategy:
    """
        Creates a strategy that generates random lists.

        :param element: A strategy for generating individual list elements.
        :param min_size: Minimum list length. Default is 0.
        :param max_size: Maximum list length. Default is 50.
        :returns: A ``ListStrategy`` instance.
    """
    return ListStrategy(element=element, min_size=min_size, max_size=max_size)


def tuples(*strategies: Strategy) -> TupleStrategy:
    """
        Creates a strategy that generates random tuples.

        Each position in the tuple is generated by its corresponding strategy.

        :param strategies: One strategy per tuple position.
        :returns: A ``TupleStrategy`` instance.
    """
    return TupleStrategy(*strategies)


def dictionaries(keys: Strategy, values: Strategy,
                 min_size: int = 0, max_size: int = 20) -> DictionaryStrategy:
    """
        Creates a strategy that generates random dictionaries.

        :param keys: A strategy for generating dictionary keys.
        :param values: A strategy for generating dictionary values.
        :param min_size: Minimum number of entries. Default is 0.
        :param max_size: Maximum number of entries. Default is 20.
        :returns: A ``DictionaryStrategy`` instance.
    """
    return DictionaryStrategy(keys=keys, values=values, min_size=min_size, max_size=max_size)


def sampled_from(elements: Sequence) -> SampledFromStrategy:
    """
        Creates a strategy that randomly selects from a fixed sequence.

        :param elements: A non-empty sequence of values to sample from.
        :returns: A ``SampledFromStrategy`` instance.
    """
    return SampledFromStrategy(elements=elements)


def one_of(*strategies: Strategy) -> OneOfStrategy:
    """
        Creates a strategy that randomly picks one sub-strategy and generates
        a value from it.

        :param strategies: Two or more strategies to choose from.
        :returns: A ``OneOfStrategy`` instance.
    """
    return OneOfStrategy(*strategies)


def just(value: Any) -> JustStrategy:
    """
        Creates a strategy that always returns the same fixed value.

        :param value: The fixed value to always return.
        :returns: A ``JustStrategy`` instance.
    """
    return JustStrategy(value=value)


def characters(categories: Optional[Tuple[str, ...]] = None,
               characters: Optional[str] = None,
               min_codepoint: Optional[int] = None,
               max_codepoint: Optional[int] = None) -> CharacterStrategy:
    """
        Creates a strategy that generates single characters.

        A codepoint range is the usual way to ask for a band such as
        printable ASCII::

            st.text(alphabet=st.characters(min_codepoint=33,
                                           max_codepoint=126))

        :param categories: Tuple of unicode category identifiers.
        :param characters: An explicit set of characters to choose from.
        :param min_codepoint: Inclusive lower bound of a codepoint range.
        :param max_codepoint: Inclusive upper bound of a codepoint range.
        :returns: A ``CharacterStrategy`` instance.
    """
    return CharacterStrategy(categories=categories, characters=characters,
                             min_codepoint=min_codepoint,
                             max_codepoint=max_codepoint)


def explicit(values: Sequence) -> ExplicitStrategy:
    """
        Creates a strategy that yields predetermined values in sequence.

        Values are cycled in order. The RNG is ignored — this strategy
        always produces the same deterministic output. Useful for
        reproducing known failures or testing specific edge cases.

        Example::

            @given(params=st.explicit([
                {'a': '1', 'b': '2'},
                {'x': 'hello'},
            ]))
            def test_known_case(params):
                ...

        :param values: A non-empty sequence of values to yield.
    :returns: An ``ExplicitStrategy`` instance.
    """
    return ExplicitStrategy(values=values)


def none() -> NoneStrategy:
    """
        Creates a strategy that always generates ``None``.

        :returns: A ``NoneStrategy`` instance.
    """
    return NoneStrategy()


def binary(min_size: int = 0, max_size: int = 100) -> BinaryStrategy:
    """
        Creates a strategy that generates random ``bytes`` objects.

        :param min_size: Minimum byte sequence length. Default is 0.
        :param max_size: Maximum byte sequence length. Default is 100.
        :returns: A ``BinaryStrategy`` instance.
    """
    return BinaryStrategy(min_size=min_size, max_size=max_size)


def sets(element: Strategy, min_size: int = 0, max_size: int = 50) -> SetStrategy:
    """
        Creates a strategy that generates random ``set`` objects.

        :param element: A strategy for generating individual set elements.
        :param min_size: Minimum set size. Default is 0.
        :param max_size: Maximum set size. Default is 50.
        :returns: A ``SetStrategy`` instance.
    """
    return SetStrategy(element=element, min_size=min_size, max_size=max_size)


def frozensets(element: Strategy, min_size: int = 0, max_size: int = 50) -> FrozenSetStrategy:
    """
        Creates a strategy that generates random ``frozenset`` objects.

        :param element: A strategy for generating individual elements.
        :param min_size: Minimum size. Default is 0.
        :param max_size: Maximum size. Default is 50.
        :returns: A ``FrozenSetStrategy`` instance.
    """
    return FrozenSetStrategy(element=element, min_size=min_size, max_size=max_size)


def fixed_dictionaries(mapping: Dict[str, Strategy]) -> FixedDictionaryStrategy:
    """
        Creates a strategy that generates dictionaries with a fixed set of keys.

        Each key's value is drawn from its corresponding strategy.

        :param mapping: A dictionary mapping keys to ``Strategy`` instances.
        :returns: A ``FixedDictionaryStrategy`` instance.
    """
    return FixedDictionaryStrategy(mapping=mapping)


def builds(target: Callable, *arg_strategies: Strategy,
           **kwarg_strategies: Strategy) -> BuildsStrategy:
    """
        Creates a strategy that constructs instances by calling ``target``
        with values generated from the provided strategies.

        Example::

            @dataclass
            class Point:
                x: int
                y: int

            point_strategy = builds(Point, x=st.integers(), y=st.integers())

        :param target: The callable to invoke with generated values.
        :param arg_strategies: Strategies for positional arguments.
        :param kwarg_strategies: Strategies for keyword arguments.
        :returns: A ``BuildsStrategy`` instance.
    """
    return BuildsStrategy(target=target, arg_strategies=arg_strategies,
                          kwarg_strategies=kwarg_strategies)
