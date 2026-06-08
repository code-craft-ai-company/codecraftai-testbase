import unittest
import os
from ccai.testbase.testcollector import catagorize_exclusions

class CategorizeExclusionsFixTests(unittest.TestCase):
    def test_returns_file_exclusions_when_no_at_symbol(self):
        # This test expects the FIXED behavior
        files, specific = catagorize_exclusions(["pkg.module"])
        expected_path = "pkg.module".replace(".", os.sep)
        self.assertEqual(files, [expected_path])
        self.assertEqual(specific, [])

    def test_returns_specific_exclusions_when_at_symbol_present(self):
        files, specific = catagorize_exclusions(["pkg.module@Test"])
        self.assertEqual(files, [])
        self.assertEqual(specific, ["pkg.module@Test"])

if __name__ == "__main__":
    unittest.main()
