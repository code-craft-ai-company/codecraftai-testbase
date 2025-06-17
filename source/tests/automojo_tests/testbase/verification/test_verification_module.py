import unittest

from automojo.testbase.verification import (
    assert_dict_response_has_keys,
    assert_equal,
    assert_expression,
    assert_greater,
    assert_lessthan,
    assert_list_length,
    assert_list_length_greater,
    assert_list_length_less,
    assert_not_equal,
    assert_type,
    verify_dict_has_keys,
)


class AssertDictResponseHasKeysTests(unittest.TestCase):
    def test_success_when_keys_present(self):
        assert_dict_response_has_keys({'a': 1, 'b': 2}, ['a', 'b'])

    def test_error_when_keys_missing(self):
        with self.assertRaises(AssertionError) as ctx:
            assert_dict_response_has_keys({'a': 1}, ['a', 'b'], api='API')
        self.assertIn("'API' API result verification failed", str(ctx.exception))
        self.assertIn("'b' key not found.", str(ctx.exception))


class VerifyDictHasKeysTests(unittest.TestCase):
    def test_missing_key_list_with_template(self):
        missing = verify_dict_has_keys({'a': 1}, ['a', 'b'], template="missing {}")
        self.assertEqual(missing, ['missing b'])

    def test_no_missing_keys(self):
        missing = verify_dict_has_keys({'a': 1, 'b': 2}, ['a', 'b'])
        self.assertEqual(missing, [])


class AssertionFunctionTests(unittest.TestCase):
    def test_assert_equal_failure_message(self):
        with self.assertRaises(AssertionError) as ctx:
            assert_equal(1, 2, api='EQ')
        self.assertIn("'EQ' API result verification failed", str(ctx.exception))

    def test_assert_expression_failure(self):
        with self.assertRaises(AssertionError) as ctx:
            assert_expression('abc', 'def', api='EXP')
        self.assertIn("'EXP' API result verification failed", str(ctx.exception))

    def test_assert_greater_and_lessthan_failures(self):
        with self.assertRaises(AssertionError):
            assert_greater(1, 2, api='GR')
        with self.assertRaises(AssertionError):
            assert_lessthan(2, 1, api='LT')

    def test_list_length_checks(self):
        with self.assertRaises(AssertionError):
            assert_list_length([1, 2], 1, api='LEN')
        with self.assertRaises(AssertionError):
            assert_list_length_greater([1], 2, api='GT')
        with self.assertRaises(AssertionError):
            assert_list_length_less([1, 2, 3], 2, api='LT')

    def test_assert_type(self):
        with self.assertRaises(AssertionError):
            assert_type('val', int, api='T')
        # correct type should not raise
        assert_type(3, int, api='T')

    def test_assert_not_equal_bug(self):
        """Ensure current buggy behaviour raises NameError when values match."""
        with self.assertRaises(NameError):
            assert_not_equal(1, 1)


if __name__ == '__main__':
    unittest.main()
