import unittest

from ccai.testbase.errors.testruntimeouterror import TestRunTimeoutError


class TestRunTimeoutErrorTests(unittest.TestCase):
    """Tests for the TestRunTimeoutError exception class."""

    def test_creation_with_timeout_value(self):
        """Test that TestRunTimeoutError can be created with a timeout value."""
        err = TestRunTimeoutError(300)
        self.assertIsInstance(err, Exception)
        self.assertIsInstance(err, TestRunTimeoutError)

    def test_timeout_seconds_property(self):
        """Test that the timeout_seconds property returns the configured value."""
        err = TestRunTimeoutError(600)
        self.assertEqual(err.timeout_seconds, 600)

    def test_timeout_seconds_property_with_small_value(self):
        """Test timeout_seconds property with a small timeout value."""
        err = TestRunTimeoutError(1)
        self.assertEqual(err.timeout_seconds, 1)

    def test_timeout_seconds_property_with_large_value(self):
        """Test timeout_seconds property with a large timeout value."""
        err = TestRunTimeoutError(86400)
        self.assertEqual(err.timeout_seconds, 86400)

    def test_message_includes_timeout_duration(self):
        """Test that the exception message includes the timeout duration."""
        err = TestRunTimeoutError(300)
        self.assertIn("300", str(err))

    def test_message_format(self):
        """Test the exact format of the exception message."""
        err = TestRunTimeoutError(300)
        self.assertEqual(
            str(err),
            "Test run exceeded the configured timeout of 300 seconds."
        )

    def test_inherits_from_exception(self):
        """Test that TestRunTimeoutError inherits from Exception."""
        self.assertTrue(issubclass(TestRunTimeoutError, Exception))

    def test_can_be_raised_and_caught(self):
        """Test that TestRunTimeoutError can be raised and caught."""
        with self.assertRaises(TestRunTimeoutError) as ctx:
            raise TestRunTimeoutError(120)
        self.assertEqual(ctx.exception.timeout_seconds, 120)

    def test_can_be_caught_as_exception(self):
        """Test that TestRunTimeoutError can be caught as a generic Exception."""
        with self.assertRaises(Exception):
            raise TestRunTimeoutError(60)


if __name__ == "__main__":
    unittest.main()
