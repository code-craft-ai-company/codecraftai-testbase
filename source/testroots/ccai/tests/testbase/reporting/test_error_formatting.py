
import ccai.testbase as testbase

from ccai.testbase.properties import expect_exception

@expect_exception(Exception, reason="Intentional error for error formatting verification")
def test_intentional_error():
    raise Exception("Intentional error.")

@expect_exception(AssertionError, reason="Intentional failure for error formatting verification")
def test_intentional_failure():
    testbase.assert_equal(False, True, "Intentional failure.")
    return

if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
