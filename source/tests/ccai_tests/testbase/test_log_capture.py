"""
    .. module:: test_log_capture
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the log-capture resource.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import logging
import unittest

from ccai.testbase.factories import LogCapture, create_log_capture


class LogCaptureTests(unittest.TestCase):
    """
        Verifies records are captured and the logging state is restored.
    """

    def setUp(self):
        """
            Note the state that must survive each test.
        """
        self.logger_name = "ccai_tests.logcapture.subject"
        self.logger = logging.getLogger(self.logger_name)
        self.original_level = self.logger.level
        self.original_handlers = self.logger.handlers[:]
        self.root_handlers = logging.getLogger().handlers[:]
        return

    def tearDown(self):
        """
            Put the subject logger back however the test left it.
        """
        self.logger.setLevel(self.original_level)
        for handler in self.logger.handlers[:]:
            if handler not in self.original_handlers:
                self.logger.removeHandler(handler)
        return

    def test_records_are_captured_in_order(self):

        capture = LogCapture()
        capture.set_level(logging.DEBUG, logger=self.logger_name)

        self.logger.debug("first")
        self.logger.info("second")

        self.assertEqual([r.getMessage() for r in capture.records],
                         ["first", "second"])

        capture.detach()
        return

    def test_messages_exposes_the_formatted_text(self):

        capture = LogCapture()
        capture.set_level(logging.DEBUG, logger=self.logger_name)

        self.logger.info("value is %s", 42)

        self.assertEqual(capture.messages, ["value is 42"])

        capture.detach()
        return

    def test_records_carry_the_logger_name(self):

        # The pytest caplog usage this replaces filters on rec.name.
        capture = LogCapture()
        capture.set_level(logging.DEBUG, logger=self.logger_name)

        self.logger.debug("subject message")

        self.assertEqual(capture.records[0].name, self.logger_name)

        capture.detach()
        return

    def test_a_level_below_the_threshold_is_not_captured(self):

        capture = LogCapture()
        capture.set_level(logging.INFO, logger=self.logger_name)

        self.logger.debug("too quiet")
        self.logger.warning("loud enough")

        self.assertEqual(capture.messages, ["loud enough"])

        capture.detach()
        return

    def test_clear_discards_the_records(self):

        capture = LogCapture()
        capture.set_level(logging.DEBUG, logger=self.logger_name)
        self.logger.debug("before")

        capture.clear()
        self.logger.debug("after")

        self.assertEqual(capture.messages, ["after"])

        capture.detach()
        return

    def test_detach_stops_the_capture(self):

        capture = LogCapture()
        capture.set_level(logging.DEBUG, logger=self.logger_name)
        self.logger.debug("captured")

        capture.detach()
        self.logger.debug("not captured")

        self.assertEqual(capture.messages, ["captured"])
        return

    def test_detach_restores_the_level(self):

        self.logger.setLevel(logging.WARNING)

        capture = LogCapture()
        capture.set_level(logging.DEBUG, logger=self.logger_name)
        capture.detach()

        self.assertEqual(self.logger.level, logging.WARNING)
        return

    def test_detach_restores_the_level_after_repeated_changes(self):

        self.logger.setLevel(logging.WARNING)

        capture = LogCapture()
        capture.set_level(logging.INFO, logger=self.logger_name)
        capture.set_level(logging.DEBUG, logger=self.logger_name)
        capture.detach()

        self.assertEqual(self.logger.level, logging.WARNING)
        return

    def test_detach_removes_only_its_own_handler(self):

        existing = logging.NullHandler()
        self.logger.addHandler(existing)

        capture = LogCapture()
        capture.set_level(logging.DEBUG, logger=self.logger_name)
        capture.detach()

        self.assertIn(existing, self.logger.handlers)

        self.logger.removeHandler(existing)
        return

    def test_the_root_logger_handlers_are_left_alone(self):

        # The runner owns the root logger's handlers for a run. Closing or
        # removing them stops the run making progress rather than failing it.
        capture = LogCapture()
        capture.set_level(logging.DEBUG, logger=self.logger_name)
        capture.detach()

        self.assertEqual(logging.getLogger().handlers, self.root_handlers)
        return


class LogCaptureFactoryTests(unittest.TestCase):
    """
        Verifies the factory yields a capture and detaches it afterwards.
    """

    def setUp(self):
        self.logger_name = "ccai_tests.logcapture.factory"
        self.logger = logging.getLogger(self.logger_name)
        self.original_level = self.logger.level
        return

    def tearDown(self):
        self.logger.setLevel(self.original_level)
        return

    def test_the_factory_yields_a_working_capture(self):

        generator = create_log_capture()
        capture = next(generator)

        capture.set_level(logging.DEBUG, logger=self.logger_name)
        self.logger.debug("from the factory")

        self.assertEqual(capture.messages, ["from the factory"])

        try:
            next(generator)
        except StopIteration:
            pass
        return

    def test_the_factory_detaches_on_teardown(self):

        generator = create_log_capture()
        capture = next(generator)
        capture.set_level(logging.DEBUG, logger=self.logger_name)

        try:
            next(generator)
        except StopIteration:
            pass

        self.logger.debug("after teardown")

        self.assertEqual(capture.messages, [])
        return

    def test_the_level_constraint_captures_from_the_root(self):

        generator = create_log_capture(constraints={"level": logging.DEBUG})
        capture = next(generator)

        self.logger.debug("via the root logger")

        self.assertIn("via the root logger", capture.messages)

        try:
            next(generator)
        except StopIteration:
            pass
        return


if __name__ == "__main__":
    unittest.main()
