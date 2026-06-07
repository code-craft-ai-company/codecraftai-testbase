

import ccai.testbase as testbase

import time

from ccai.testbase.sequencing.sequencertestscope import SequencerTestScope as TestScope

def test_constraint_constrained_parameter(blah: str):
    testbase.logger.info(f"test_constraint_constrained_parameter: blah={blah}.")
    return


def test_tscope_parameter(tscope: TestScope, blah: str):
    testbase.logger.info(f"test_constraint_constrained_parameter: blah={blah}.")
    return

def test_activity_logging(tscope: TestScope):

    with tscope.begin_activity("first activity") as a:
        time.sleep(2)
    
    tscope.mark_activity("second activity")

    with tscope.begin_activity("third activity") as a:
        time.sleep(2)

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
