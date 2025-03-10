
import time

import automojo.testbase as testbase

factory = testbase.factory
originate = testbase.originate


from automojo.testbase.tandem.validators import Validator, LoopingValidator, TimeIntervalValidator


class TestValidator(Validator):

    def __init__(self):
        super().__init__()
        return

    def validate(self):
        self._logger.info("TestValidator 'validate' called ...")
        return


class TestLoopingValidator(LoopingValidator):
    
    def do_work(self):
        self._logger.info("TestLoopingValidator 'do_work' called ...")
        return True
    
    def validate(self):
        self._logger.info("TestLoopingValidator 'validate' called ...")
        return


class TestTimeIntervalValidator(TimeIntervalValidator):
    
    def tick(self):
        now = time.time()
        self._logger.info(f"TestTimeIntervalValidator 'tick' called ... now={now}")
        return

    def validate(self):
        self._logger.info("TestTimeIntervalValidator 'validate' called ...")
        return


@factory.validator()
def create_validator() -> TestValidator:

    validator = TestValidator()
    validator.initialize()

    return validator

@factory.validator()
def create_looping_validator() -> TestLoopingValidator:

    validator = TestLoopingValidator()
    validator.initialize()

    return validator

@factory.validator()
def create_time_interval_validator() -> TimeIntervalValidator:

    validator = TestTimeIntervalValidator(interval=1)
    validator.initialize()

    return validator


@originate.validate(create_validator, suffix="vcheck", identifier="nvalidator")
@originate.validate(create_looping_validator, suffix="vlcheck", identifier="lvalidator")
@originate.validate(create_time_interval_validator, suffix="vticheck", identifier="tivalidator")
def test_with_validators(nvalidator: TestValidator, lvalidator: TestLoopingValidator, tivalidator: TimeIntervalValidator):

    # The test function can ask for the validators as parameters so it has a way to handle synchronization
    # of parallel checks.

    testbase.logger.info("test_no_parameters: was run.")
    time.sleep(10)
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
