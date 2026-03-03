"""
    .. module:: automojo.testbase.properties.propertysettings
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for property test settings configuration.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Optional

from dataclasses import dataclass


@dataclass
class PropertySettings:
    """
        Configuration settings for property-based test execution.

        Controls the behavior of the property test runner including
        how many examples to generate, the random seed for reproducibility,
        and bounds on the shrinking process.

        :param max_examples: The maximum number of randomly generated examples
            to run per property test function. Default is 100.
        :param seed: An optional integer seed that overrides the per-test seed
            derived from the job seed. When set, this seed takes precedence
            and is used directly to initialize the random number generator
            for this specific property test.
        :param max_shrink_attempts: The maximum number of shrinking iterations
            to attempt when simplifying a failing counterexample. Default is 100.
    """

    max_examples: int = 100
    seed: Optional[int] = None
    max_shrink_attempts: int = 100
