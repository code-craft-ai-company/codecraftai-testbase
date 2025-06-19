import unittest
import os
from automojo.testbase.mocking import (
    Mock,
    SideEffect,
    create_module_patch,
    create_class_patch,
    create_instance_patch,
)

# Tests proposed for automojo.testbase.mocking
# 1. SideEffect uses default arguments when none are provided.
# 2. Mock returns configured return_value and records call information.
# 3. Mock executes side_effect and returns its value.
# 4. Recursive Mock creates child mocks automatically.
# 5. strict_attrs prevents setting new attributes.
# 6. Module patch replaces attribute and restores it after exit.
# 7. Class and instance patching for methods work as expected.


def sample_function(x):
    return x + 1


class SampleClass:
    def __init__(self):
        self.value = 0

    def method(self, inc):
        return self.value + inc

    @classmethod
    def cmethod(cls, val):
        return f"orig:{val}"


class SideEffectTests(unittest.TestCase):
    def test_uses_default_arguments(self):
        def add(a, b):
            return a + b

        se = SideEffect(add, default_args=(1,), default_kwargs={"b": 2})
        self.assertEqual(se(), 3)
        self.assertEqual(se(3, b=4), 7)


class MockCallTests(unittest.TestCase):
    def test_returns_value_and_records_call(self):
        m = Mock(return_value=10)
        result = m(1, a=2)
        self.assertEqual(result, 10)
        self.assertEqual(m.call_count, 1)
        self.assertEqual(m.call_args, ((1,), {"a": 2}))
        self.assertEqual(m.call_args_list, [((1,), {"a": 2})])

    def test_executes_side_effect(self):
        def effect(x):
            return x * 2

        m = Mock(side_effect=effect)
        self.assertEqual(m(3), 6)
        m.assert_called_once_with(3)


class RecursiveMockTests(unittest.TestCase):
    def test_child_mocks_created(self):
        m = Mock(recursive=True)
        child = m.foo.bar
        self.assertIsInstance(child, Mock)
        self.assertTrue(child.mock_context().recursive) # recursive is a property on context
        child.configure(return_value="val")
        self.assertEqual(m.foo.bar(), "val")

    def test_fluent_configure_parent_then_child(self):
        m = Mock(recursive=True)
        # Configure 'parent', then access 'child' on it, then configure 'child'
        m.parent.configure(return_value="parent_val").child.configure(return_value="child_val")

        self.assertEqual(m.parent(), "parent_val")
        m.parent.assert_called_once()
        self.assertEqual(m.parent.child(), "child_val")
        m.parent.child.assert_called_once()

class StrictAttributeTests(unittest.TestCase):
    def test_setting_unknown_attr_raises(self):
        m = Mock(strict_attrs=True)
        with self.assertRaises(AttributeError):
            m.new_attr = 1
        # setting return_value is allowed
        m.configure(return_value=5)
        self.assertEqual(m(), 5)


class PatchTests(unittest.TestCase):
    def test_module_patch(self):
        original = os.path.exists
        with create_module_patch(os.path, "exists") as mock_exists:
            mock_exists.configure(return_value=True)
            self.assertTrue(os.path.exists("/tmp"))
        self.assertIs(os.path.exists, original)

    def test_class_patch(self):
        orig = SampleClass.cmethod("x")
        with create_class_patch(SampleClass, "cmethod") as mock_cm:
            mock_cm.configure(return_value="patched")
            self.assertEqual(SampleClass.cmethod("y"), "patched")
        self.assertEqual(SampleClass.cmethod("z"), "orig:z")

    def test_instance_patch(self):
        obj = SampleClass()
        orig = obj.method(1)
        with create_instance_patch(obj, "method") as mock_m:
            mock_m.configure(return_value=99)
            self.assertEqual(obj.method(2), 99)
        self.assertEqual(obj.method(3), obj.value + 3)


if __name__ == "__main__":
    unittest.main()
