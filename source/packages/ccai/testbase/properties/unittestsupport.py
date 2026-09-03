"""
    .. module:: ccai.testbase.properties.unittestsupport
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for running property checks from plain unittest or pytest tests.

    The ``@given`` decorator only marks a function for the testbase sequencer's
    property runner; it does not draw examples when the function is called
    directly. Test modules that run under ``unittest`` or ``pytest`` use
    :func:`run_property` instead, which draws examples itself from a fixed seed
    so a failure reproduces from run to run.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Any, Callable, Dict, Optional

import contextlib
import random

from ccai.testbase.properties.assumptions import UnsatisfiedAssumption
from ccai.testbase.properties.strategies import Strategy

DEFAULT_PROPERTY_SEED = 0x5EED

# Each example may reject its inputs through assume(); this many rejections per
# requested example is treated as strategies that cannot satisfy the preconditions.
MAX_REJECTIONS_PER_EXAMPLE = 50


def run_property(check: Callable[..., Any], max_examples: int = 100, *, seed: int = DEFAULT_PROPERTY_SEED,
                 case: Optional[Any] = None, **strategies: Strategy) -> int:
    """
        Runs ``check`` against ``max_examples`` inputs drawn from ``strategies``.

        Examples are drawn from a :class:`random.Random` seeded with ``seed`` so
        the same inputs are generated on every run. When ``case`` is a
        :class:`unittest.TestCase`, every example runs inside ``case.subTest``
        with the generated values as its parameters, so a failure report names
        the inputs that produced it.

        Inputs rejected through :func:`ccai.testbase.properties.assume` are not
        counted as examples; too many rejections raise ``RuntimeError``.

        :param check: The callable that asserts the property. It receives the
                      generated values as keyword arguments.
        :param max_examples: The number of examples to run.
        :param seed: The seed for the example generator.
        :param case: An optional test case whose ``subTest`` wraps each example.
        :param strategies: A strategy per keyword argument of ``check``.

        :returns: The number of examples that ran.

        :raises RuntimeError: When the strategies cannot satisfy the assumptions.
    """
    rng = random.Random(seed)
    examples_run = 0
    rejections = 0
    max_rejections = MAX_REJECTIONS_PER_EXAMPLE * max(max_examples, 1)

    while examples_run < max_examples:
        if rejections >= max_rejections:
            errmsg = "Too many assumption rejections ({}) after {} examples; the assume() preconditions " \
                     "are too restrictive for the strategies in use.".format(rejections, examples_run)
            raise RuntimeError(errmsg)

        kwargs: Dict[str, Any] = {name: strategy.generate(rng) for name, strategy in strategies.items()}

        if case is not None:
            labels = {name: repr(value)[:48] for name, value in kwargs.items()}
            scope = case.subTest(example=examples_run, **labels)
        else:
            scope = contextlib.nullcontext()

        with scope:
            try:
                check(**kwargs)
            except UnsatisfiedAssumption:
                rejections += 1
                continue

        examples_run += 1

    return examples_run
