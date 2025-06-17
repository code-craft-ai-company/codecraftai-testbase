import unittest
from types import ModuleType

from automojo.testbase.expressions import parse_test_include_expression


class ParseTestIncludeExpressionTests(unittest.TestCase):

    def test_module_run_invalid_expression(self):
        mod = ModuleType('pkg.mod')
        with self.assertRaises(ValueError):
            parse_test_include_expression('Bad.Expression', mod)

    def test_module_run_extracts_package_module(self):
        mod = ModuleType('pkg.mod')
        pkg, module, testclass, testname = parse_test_include_expression('*', mod)
        self.assertEqual(pkg, 'pkg')
        self.assertEqual(module, 'mod')
        self.assertIsNone(testclass)
        self.assertIsNone(testname)

    def test_cli_expression_full(self):
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.mod@TestClass#test_demo', None)
        self.assertEqual(pkg, 'pkg')
        self.assertEqual(module, 'mod')
        self.assertEqual(testclass, 'TestClass')
        self.assertEqual(testname, 'test_demo')

    def test_cli_method_prefix_validation(self):
        with self.assertRaises(ValueError):
            parse_test_include_expression('pkg.mod@TestClass#demo', None)

    def test_empty_testclass_becomes_none(self):
        pkg, module, testclass, testname = parse_test_include_expression(
            'pkg.mod@#test_demo', None)
        self.assertIsNone(testclass)
        self.assertEqual(testname, 'test_demo')


if __name__ == '__main__':
    unittest.main()
