
import automojo.testbase as testbase

def test_intentional_error():
    raise Exception("Intentional error.")

def test_intentional_failure():
    testbase.assert_equal(False, True, "Intentional failure.")
    return

if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
