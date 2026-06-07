import unittest

from ccai.errors.exceptions import SemanticError
from ccai.testbase.tandem.validators import (
    Validator,
    LoopingValidator,
    LoopingValidatorState,
)
from ccai.waiting.waitmodel import TimeoutContext


class DummyRecorder:
    def __init__(self):
        self.previewed = None
        self.recorded = None

    def preview(self, result):
        self.previewed = result

    def record(self, result):
        self.recorded = result


class DummyScope:
    def __init__(self, name="test"):
        self.test_name = name
        self._parent_scope_id = "parent"
        self._monikers = []
        self._pivots = {}
        self.recorder = DummyRecorder()


class PassingValidator(Validator):
    def validate(self):
        pass


class FailingValidator(Validator):
    def validate(self):
        raise AssertionError("boom")


class ErrorValidator(Validator):
    def validate(self):
        raise RuntimeError("err")


class SimpleLoopingValidator(LoopingValidator):
    def __init__(self):
        super().__init__(loop_delay=0)
        self.calls = 0

    def do_work(self) -> bool:
        self.calls += 1
        return self.calls < 2

    def validate(self):
        pass


class ValidatorFinalizeTests(unittest.TestCase):
    def test_finalize_pass(self):
        val = PassingValidator()
        scope = DummyScope()
        val.attach_to_test(scope, "v")
        val.finalize()
        self.assertEqual(val._result._result_code.name, "PASSED")
        self.assertIs(scope.recorder.recorded, val._result)

    def test_finalize_failure(self):
        val = FailingValidator()
        scope = DummyScope()
        val.attach_to_test(scope, "f")
        val.finalize()
        self.assertEqual(val._result._result_code.name, "FAILED")

    def test_finalize_error(self):
        val = ErrorValidator()
        scope = DummyScope()
        val.attach_to_test(scope, "e")
        val.finalize()
        self.assertEqual(val._result._result_code.name, "ERRORED")


class LoopingValidatorTests(unittest.TestCase):
    def test_initialize_and_finalize(self):
        lv = SimpleLoopingValidator()
        lv.attach_to_test(DummyScope(), "lp")
        lv.initialize()
        lv.finalize()
        self.assertEqual(lv._state, LoopingValidatorState.Shutdown)
        self.assertGreaterEqual(lv.calls, 1)

    def test_double_initialize_error(self):
        lv = SimpleLoopingValidator()
        lv.attach_to_test(DummyScope(), "lp")
        lv.initialize()
        with self.assertRaises(SemanticError):
            lv.initialize()
        lv.finalize()

    def test_wait_for_shutdown_helper(self):
        lv = SimpleLoopingValidator()
        wctx = TimeoutContext(1)
        self.assertTrue(lv._wait_for_shutdown(wctx))

        lv._state = LoopingValidatorState.Finished
        wctx = TimeoutContext(1)
        self.assertFalse(lv._wait_for_shutdown(wctx))

        wctx.mark_begin()
        wctx.mark_final_attempt()
        with self.assertRaises(TimeoutError):
            lv._wait_for_shutdown(wctx)


if __name__ == "__main__":
    unittest.main()
