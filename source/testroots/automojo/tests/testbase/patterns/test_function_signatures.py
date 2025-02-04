
import automojo.testbase as testbase


def test_no_parameters():
    testbase.logger.info("test_no_parameters: was run.")
    return

if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
