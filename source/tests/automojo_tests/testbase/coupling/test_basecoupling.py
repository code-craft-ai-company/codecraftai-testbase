"""
    .. module:: automojo_tests.testbase.coupling.test_basecoupling
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for BaseCoupling class.

    .. moduleauthor:: AutomationX
"""

import unittest

from automojo.testbase.coupling.basecoupling import BaseCoupling
from automojo.xmodules.xlogging.enhancedloggers import EnhancedLogger


class BaseCouplingTests(unittest.TestCase):
    """Tests for the BaseCoupling class."""

    def test_logger_property_is_accessible(self):
        """Test that the logger property is accessible on BaseCoupling."""
        logger = BaseCoupling.logger
        self.assertIsNotNone(logger)

    def test_logger_is_enhanced_logger_instance(self):
        """Test that the logger property is an EnhancedLogger instance."""
        logger = BaseCoupling.logger
        self.assertIsInstance(logger, EnhancedLogger)

    def test_logger_accessible_from_instance(self):
        """Test that the logger property is accessible from a BaseCoupling instance."""
        coupling = BaseCoupling()
        logger = coupling.logger
        self.assertIsNotNone(logger)
        self.assertIsInstance(logger, EnhancedLogger)


if __name__ == "__main__":
    unittest.main()
