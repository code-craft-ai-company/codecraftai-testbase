import unittest
import os
import asyncio
from ccai.testbase.mocking import (
    Mock,
    MockContext,
    MockType,
    Patch,
    PatchType,
    SideEffect,
    AsyncSideEffect,
    AsyncMock,
    PropertyMock,
    create_module_patch,
    create_class_patch,
    create_instance_patch,
    create_async_mock,
    create_property_mock,
    # Automatic cleanup imports
    MockRegistry,
    get_mock_registry,
    register_mock,
    register_patch,
    cleanup_all_mocks,
    create_tracked_mock,
    create_tracked_module_patch,
    create_tracked_class_patch,
    create_tracked_instance_patch,
)

# Tests proposed for ccai.testbase.mocking
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


class MockTypeDeterminationTests(unittest.TestCase):
    """Tests for MockContext.determine_mock_type static method."""

    def test_property_detection(self):
        """Test that property objects are detected as MockType.Property."""
        class TestClass:
            @property
            def test_prop(self):
                return "value"
        
        prop = TestClass.__dict__['test_prop']
        result = MockContext.determine_mock_type(prop)
        self.assertEqual(result, MockType.Property)

    def test_function_detection(self):
        """Test that functions are detected as MockType.Function."""
        def test_func():
            pass
        
        result = MockContext.determine_mock_type(test_func)
        self.assertEqual(result, MockType.Function)

    def test_method_detection(self):
        """Test that bound methods are detected as MockType.Method."""
        class TestClass:
            def test_method(self):
                pass
        
        instance = TestClass()
        bound_method = instance.test_method
        result = MockContext.determine_mock_type(bound_method)
        self.assertEqual(result, MockType.Method)

    def test_class_detection(self):
        """Test that classes are detected as MockType.Class."""
        class TestClass:
            pass
        
        result = MockContext.determine_mock_type(TestClass)
        self.assertEqual(result, MockType.Class)

    def test_instance_detection(self):
        """Test that object instances are detected as MockType.Instance."""
        class TestClass:
            pass
        
        instance = TestClass()
        result = MockContext.determine_mock_type(instance)
        self.assertEqual(result, MockType.Instance)

    def test_none_returns_generic(self):
        """Test that None returns MockType.Generic."""
        result = MockContext.determine_mock_type(None)
        self.assertEqual(result, MockType.Generic)


class SideEffectTests(unittest.TestCase):
    def test_uses_default_arguments(self):
        def add(a, b):
            return a + b

        se = SideEffect(add, default_args=(1,), default_kwargs={"b": 2})
        self.assertEqual(se(), 3)
        self.assertEqual(se(3, b=4), 7)

    def test_callable_that_raises_exception(self):
        """Test that SideEffect properly propagates exceptions from the wrapped callable."""
        def raise_error():
            raise ValueError("Test error from callable")

        se = SideEffect(raise_error)
        with self.assertRaises(ValueError) as context:
            se()
        self.assertEqual(str(context.exception), "Test error from callable")

    def test_callable_raises_with_args(self):
        """Test that SideEffect propagates exceptions when called with arguments."""
        def raise_with_args(x, y):
            raise RuntimeError(f"Error with args: {x}, {y}")

        se = SideEffect(raise_with_args)
        with self.assertRaises(RuntimeError) as context:
            se(1, 2)
        self.assertEqual(str(context.exception), "Error with args: 1, 2")

    def test_with_none_default_args(self):
        """Test SideEffect with None as default_args."""
        def func(a=10, b=20):
            return a + b

        # When default_args is None, the callable should use its own defaults
        se = SideEffect(func, default_args=None, default_kwargs=None)
        self.assertEqual(se(), 30)  # Uses func's own defaults

    def test_with_empty_default_kwargs(self):
        """Test SideEffect with empty dict as default_kwargs."""
        def func(a=5, b=10):
            return a * b

        # Empty dict should not override anything
        se = SideEffect(func, default_args=None, default_kwargs={})
        self.assertEqual(se(), 50)  # Uses func's own defaults

    def test_mock_wraps_callable_in_side_effect(self):
        """Test that Mock wraps a callable in a SideEffect instance (Requirement 4.5)."""
        def my_effect(x):
            return x * 3

        m = Mock(side_effect=my_effect)
        # Verify the side_effect is wrapped in a SideEffect instance
        self.assertIsInstance(m.mock_context().side_effect, SideEffect)
        # Verify it works correctly
        self.assertEqual(m(5), 15)

    def test_mock_raises_type_error_for_non_callable_side_effect(self):
        """Test that Mock raises TypeError for non-callable side_effect (Requirement 4.6)."""
        with self.assertRaises(TypeError) as context:
            Mock(side_effect="not a callable")
        self.assertIn("side_effect must be a SideEffect instance or a callable", str(context.exception))

    def test_mock_raises_type_error_for_non_callable_via_configure(self):
        """Test that configure raises TypeError for non-callable side_effect."""
        m = Mock()
        with self.assertRaises(TypeError) as context:
            m.configure(side_effect=123)
        self.assertIn("side_effect must be a SideEffect instance or a callable", str(context.exception))

    def test_mock_accepts_side_effect_instance(self):
        """Test that Mock accepts a SideEffect instance directly."""
        def my_effect(x):
            return x + 100

        se = SideEffect(my_effect)
        m = Mock(side_effect=se)
        # Verify the side_effect is the same instance
        self.assertIs(m.mock_context().side_effect, se)
        # Verify it works correctly
        self.assertEqual(m(5), 105)


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


class AssertionMethodTests(unittest.TestCase):
    """Tests for MockContext assertion methods (Requirements 6.1-6.11)."""

    # --- assert_called tests ---
    def test_assert_called_passes_when_mock_was_called(self):
        """Test assert_called passes when mock was called at least once (Requirement 6.1)."""
        m = Mock()
        m()
        # Should not raise
        m.assert_called()

    def test_assert_called_raises_when_mock_was_not_called(self):
        """Test assert_called raises AssertionError when mock was never called (Requirement 6.2)."""
        m = Mock()
        with self.assertRaises(AssertionError) as context:
            m.assert_called()
        self.assertIn("Expected mock to have been called", str(context.exception))

    def test_assert_called_passes_after_multiple_calls(self):
        """Test assert_called passes after multiple calls."""
        m = Mock()
        m()
        m()
        m()
        # Should not raise
        m.assert_called()

    # --- assert_called_once tests ---
    def test_assert_called_once_passes_when_called_exactly_once(self):
        """Test assert_called_once passes when mock was called exactly once (Requirement 6.3)."""
        m = Mock()
        m()
        # Should not raise
        m.assert_called_once()

    def test_assert_called_once_raises_when_not_called(self):
        """Test assert_called_once raises AssertionError when mock was not called (Requirement 6.4)."""
        m = Mock()
        with self.assertRaises(AssertionError) as context:
            m.assert_called_once()
        self.assertIn("Expected mock to have been called once", str(context.exception))
        self.assertIn("Called 0 times", str(context.exception))

    def test_assert_called_once_raises_when_called_multiple_times(self):
        """Test assert_called_once raises AssertionError when mock was called multiple times (Requirement 6.4)."""
        m = Mock()
        m()
        m()
        with self.assertRaises(AssertionError) as context:
            m.assert_called_once()
        self.assertIn("Expected mock to have been called once", str(context.exception))
        self.assertIn("Called 2 times", str(context.exception))

    def test_assert_called_once_raises_when_called_three_times(self):
        """Test assert_called_once raises AssertionError when mock was called three times."""
        m = Mock()
        m()
        m()
        m()
        with self.assertRaises(AssertionError) as context:
            m.assert_called_once()
        self.assertIn("Called 3 times", str(context.exception))

    # --- assert_called_with tests ---
    def test_assert_called_with_passes_with_matching_args(self):
        """Test assert_called_with passes when last call matches (Requirement 6.5)."""
        m = Mock()
        m(1, 2, key="value")
        # Should not raise
        m.assert_called_with(1, 2, key="value")

    def test_assert_called_with_raises_with_non_matching_args(self):
        """Test assert_called_with raises AssertionError when last call doesn't match (Requirement 6.6)."""
        m = Mock()
        m(1, 2, key="value")
        with self.assertRaises(AssertionError) as context:
            m.assert_called_with(3, 4, key="other")
        self.assertIn("Expected last call with", str(context.exception))
        self.assertIn("Actual last call:", str(context.exception))

    def test_assert_called_with_raises_when_not_called(self):
        """Test assert_called_with raises AssertionError when mock was never called."""
        m = Mock()
        with self.assertRaises(AssertionError) as context:
            m.assert_called_with(1, 2)
        self.assertIn("Expected mock to have been called with specific arguments", str(context.exception))

    def test_assert_called_with_checks_only_last_call(self):
        """Test assert_called_with only checks the last call."""
        m = Mock()
        m(1, 2)
        m(3, 4)
        # Should pass because last call was (3, 4)
        m.assert_called_with(3, 4)
        # Should fail because last call was not (1, 2)
        with self.assertRaises(AssertionError):
            m.assert_called_with(1, 2)

    def test_assert_called_with_empty_args(self):
        """Test assert_called_with with no arguments."""
        m = Mock()
        m()
        # Should not raise
        m.assert_called_with()

    def test_assert_called_with_only_kwargs(self):
        """Test assert_called_with with only keyword arguments."""
        m = Mock()
        m(a=1, b=2)
        # Should not raise
        m.assert_called_with(a=1, b=2)

    # --- assert_called_once_with tests ---
    def test_assert_called_once_with_passes_when_called_once_with_matching_args(self):
        """Test assert_called_once_with passes when called exactly once with matching args (Requirement 6.7)."""
        m = Mock()
        m("arg1", kwarg="value")
        # Should not raise
        m.assert_called_once_with("arg1", kwarg="value")

    def test_assert_called_once_with_raises_when_called_multiple_times(self):
        """Test assert_called_once_with raises when called multiple times even with matching args."""
        m = Mock()
        m("arg1")
        m("arg1")
        with self.assertRaises(AssertionError) as context:
            m.assert_called_once_with("arg1")
        self.assertIn("Called 2 times", str(context.exception))

    def test_assert_called_once_with_raises_when_args_dont_match(self):
        """Test assert_called_once_with raises when called once but args don't match."""
        m = Mock()
        m("arg1")
        with self.assertRaises(AssertionError) as context:
            m.assert_called_once_with("arg2")
        self.assertIn("Expected last call with", str(context.exception))

    # --- assert_any_call tests ---
    def test_assert_any_call_passes_when_call_is_present(self):
        """Test assert_any_call passes when the specified call is in call history (Requirement 6.8)."""
        m = Mock()
        m(1, 2)
        m(3, 4)
        m(5, 6)
        # Should not raise - call (3, 4) is in the history
        m.assert_any_call(3, 4)

    def test_assert_any_call_raises_when_call_is_absent(self):
        """Test assert_any_call raises AssertionError when call is not in history (Requirement 6.9)."""
        m = Mock()
        m(1, 2)
        m(3, 4)
        with self.assertRaises(AssertionError) as context:
            m.assert_any_call(5, 6)
        self.assertIn("Expected at least one call with", str(context.exception))

    def test_assert_any_call_passes_with_first_call(self):
        """Test assert_any_call passes when checking the first call."""
        m = Mock()
        m("first")
        m("second")
        m("third")
        # Should not raise
        m.assert_any_call("first")

    def test_assert_any_call_passes_with_last_call(self):
        """Test assert_any_call passes when checking the last call."""
        m = Mock()
        m("first")
        m("second")
        m("third")
        # Should not raise
        m.assert_any_call("third")

    def test_assert_any_call_with_kwargs(self):
        """Test assert_any_call with keyword arguments."""
        m = Mock()
        m(a=1, b=2)
        m(c=3, d=4)
        # Should not raise
        m.assert_any_call(a=1, b=2)
        # Should raise
        with self.assertRaises(AssertionError):
            m.assert_any_call(a=1, b=3)

    def test_assert_any_call_raises_when_no_calls_made(self):
        """Test assert_any_call raises when no calls were made."""
        m = Mock()
        with self.assertRaises(AssertionError) as context:
            m.assert_any_call(1, 2)
        self.assertIn("no calls made", str(context.exception))

    # --- assert_has_calls tests ---
    def test_assert_has_calls_passes_with_exact_sequence(self):
        """Test assert_has_calls passes when call sequence matches exactly (Requirement 6.10)."""
        m = Mock()
        m(1)
        m(2)
        m(3)
        # Should not raise - exact sequence
        m.assert_has_calls([((1,), {}), ((2,), {}), ((3,), {})])

    def test_assert_has_calls_passes_with_subsequence(self):
        """Test assert_has_calls passes when call sequence is a subsequence."""
        m = Mock()
        m(1)
        m(2)
        m(3)
        m(4)
        # Should not raise - subsequence (2, 3) is present
        m.assert_has_calls([((2,), {}), ((3,), {})])

    def test_assert_has_calls_raises_when_sequence_not_found(self):
        """Test assert_has_calls raises when call sequence is not found."""
        m = Mock()
        m(1)
        m(2)
        m(3)
        with self.assertRaises(AssertionError) as context:
            # Sequence (2, 4) is not present
            m.assert_has_calls([((2,), {}), ((4,), {})])
        self.assertIn("Expected call sequence not found", str(context.exception))

    def test_assert_has_calls_with_any_order_passes(self):
        """Test assert_has_calls with any_order=True passes when all calls exist (Requirement 6.11)."""
        m = Mock()
        m(1)
        m(2)
        m(3)
        # Should not raise - all calls exist, order doesn't matter
        m.assert_has_calls([((3,), {}), ((1,), {})], any_order=True)

    def test_assert_has_calls_with_any_order_raises_when_call_missing(self):
        """Test assert_has_calls with any_order=True raises when a call is missing."""
        m = Mock()
        m(1)
        m(2)
        with self.assertRaises(AssertionError) as context:
            m.assert_has_calls([((1,), {}), ((3,), {})], any_order=True)
        self.assertIn("Expected call", str(context.exception))
        self.assertIn("not found", str(context.exception))

    def test_assert_has_calls_with_kwargs(self):
        """Test assert_has_calls with keyword arguments."""
        m = Mock()
        m(a=1)
        m(b=2)
        m(c=3)
        # Should not raise
        m.assert_has_calls([((), {"a": 1}), ((), {"b": 2})])

    def test_assert_has_calls_raises_when_more_calls_expected_than_made(self):
        """Test assert_has_calls raises when more calls are expected than were made."""
        m = Mock()
        m(1)
        with self.assertRaises(AssertionError) as context:
            m.assert_has_calls([((1,), {}), ((2,), {}), ((3,), {})])
        self.assertIn("Expected 3 calls", str(context.exception))
        self.assertIn("only 1 were made", str(context.exception))

    def test_assert_has_calls_empty_list(self):
        """Test assert_has_calls with empty list passes."""
        m = Mock()
        m(1)
        # Empty list should always pass
        m.assert_has_calls([])

    # --- Improved error message tests ---
    def test_assert_called_with_error_includes_call_history(self):
        """Test that assert_called_with error includes call history when multiple calls made."""
        m = Mock()
        m(1, 2)
        m(3, 4)
        m(5, 6)
        with self.assertRaises(AssertionError) as context:
            m.assert_called_with(10, 20)
        error_msg = str(context.exception)
        # Should include call history
        self.assertIn("Call history", error_msg)
        self.assertIn("3 total calls", error_msg)
        # Should include numbered calls
        self.assertIn("1.", error_msg)
        self.assertIn("2.", error_msg)
        self.assertIn("3.", error_msg)

    def test_assert_called_once_error_includes_call_history(self):
        """Test that assert_called_once error includes call history when multiple calls made."""
        m = Mock()
        m("first")
        m("second")
        m("third")
        with self.assertRaises(AssertionError) as context:
            m.assert_called_once()
        error_msg = str(context.exception)
        # Should include call history
        self.assertIn("Call history", error_msg)
        # Should include numbered calls
        self.assertIn("1.", error_msg)
        self.assertIn("2.", error_msg)
        self.assertIn("3.", error_msg)

    def test_assert_any_call_error_includes_call_history(self):
        """Test that assert_any_call error includes call history."""
        m = Mock()
        m(1, 2)
        m(3, 4)
        with self.assertRaises(AssertionError) as context:
            m.assert_any_call(10, 20)
        error_msg = str(context.exception)
        # Should include call history
        self.assertIn("Actual calls", error_msg)
        self.assertIn("2 total", error_msg)
        # Should include numbered calls
        self.assertIn("1.", error_msg)
        self.assertIn("2.", error_msg)

    def test_assert_has_calls_error_includes_expected_and_actual(self):
        """Test that assert_has_calls error includes expected and actual calls."""
        m = Mock()
        m(1)
        m(2)
        m(3)
        with self.assertRaises(AssertionError) as context:
            m.assert_has_calls([((10,), {}), ((20,), {})])
        error_msg = str(context.exception)
        # Should include expected sequence
        self.assertIn("Expected sequence", error_msg)
        # Should include actual calls
        self.assertIn("Actual calls", error_msg)
        self.assertIn("3 total", error_msg)

    def test_error_message_formats_long_strings(self):
        """Test that error messages truncate long strings for readability."""
        m = Mock()
        long_string = "a" * 200
        m(long_string)
        with self.assertRaises(AssertionError) as context:
            m.assert_called_with("different")
        error_msg = str(context.exception)
        # Should truncate long strings
        self.assertIn("truncated", error_msg)
        self.assertIn("200 chars", error_msg)

    def test_error_message_formats_large_collections(self):
        """Test that error messages truncate large collections for readability."""
        m = Mock()
        large_list = list(range(50))
        m(large_list)
        with self.assertRaises(AssertionError) as context:
            m.assert_called_with([])
        error_msg = str(context.exception)
        # Should truncate large collections
        self.assertIn("...", error_msg)
        self.assertIn("50 items", error_msg)


class MockContextResetTests(unittest.TestCase):
    """Tests for MockContext.reset method (Requirements 8.1-8.6)."""

    def test_reset_sets_return_value_to_none(self):
        """Test that reset sets return_value to None (Requirement 8.1)."""
        m = Mock(return_value=42)
        self.assertEqual(m.mock_context().return_value, 42)
        
        m.mock_context().reset()
        
        self.assertIsNone(m.mock_context().return_value)

    def test_reset_sets_side_effect_to_none(self):
        """Test that reset sets side_effect to None (Requirement 8.2)."""
        def my_effect():
            return "effect"
        
        m = Mock(side_effect=my_effect)
        self.assertIsNotNone(m.mock_context().side_effect)
        
        m.mock_context().reset()
        
        self.assertIsNone(m.mock_context().side_effect)

    def test_reset_sets_call_count_to_zero(self):
        """Test that reset sets call_count to zero (Requirement 8.3)."""
        m = Mock()
        m()
        m()
        m()
        self.assertEqual(m.call_count, 3)
        
        m.mock_context().reset()
        
        self.assertEqual(m.call_count, 0)

    def test_reset_clears_call_args_to_none(self):
        """Test that reset clears call_args to None (Requirement 8.4)."""
        m = Mock()
        m(1, 2, key="value")
        self.assertEqual(m.call_args, ((1, 2), {"key": "value"}))
        
        m.mock_context().reset()
        
        self.assertIsNone(m.call_args)

    def test_reset_clears_call_args_list_to_empty(self):
        """Test that reset clears call_args_list to an empty list (Requirement 8.5)."""
        m = Mock()
        m(1)
        m(2)
        m(3)
        self.assertEqual(len(m.call_args_list), 3)
        
        m.mock_context().reset()
        
        self.assertEqual(m.call_args_list, [])

    def test_reset_clears_mock_calls_to_empty(self):
        """Test that reset clears mock_calls to an empty list (Requirement 8.6)."""
        m = Mock()
        m("a")
        m("b")
        self.assertGreater(len(m.mock_calls), 0)
        
        m.mock_context().reset()
        
        self.assertEqual(m.mock_calls, [])

    def test_reset_all_state_at_once(self):
        """Test that reset clears all state in a single call."""
        def my_effect(x):
            return x * 2
        
        m = Mock(return_value=100, side_effect=my_effect)
        m(1)
        m(2)
        m(3)
        
        # Verify state before reset
        self.assertEqual(m.mock_context().return_value, 100)
        self.assertIsNotNone(m.mock_context().side_effect)
        self.assertEqual(m.call_count, 3)
        self.assertIsNotNone(m.call_args)
        self.assertEqual(len(m.call_args_list), 3)
        
        m.mock_context().reset()
        
        # Verify all state is reset
        self.assertIsNone(m.mock_context().return_value)
        self.assertIsNone(m.mock_context().side_effect)
        self.assertEqual(m.call_count, 0)
        self.assertIsNone(m.call_args)
        self.assertEqual(m.call_args_list, [])
        self.assertEqual(m.mock_calls, [])

    def test_mock_can_be_reused_after_reset(self):
        """Test that mock can be reused after reset."""
        m = Mock(return_value="first")
        
        # First usage
        result1 = m("arg1")
        self.assertEqual(result1, "first")
        self.assertEqual(m.call_count, 1)
        m.assert_called_once_with("arg1")
        
        # Reset
        m.mock_context().reset()
        
        # Reconfigure and reuse
        m.configure(return_value="second")
        result2 = m("arg2")
        self.assertEqual(result2, "second")
        self.assertEqual(m.call_count, 1)
        m.assert_called_once_with("arg2")

    def test_mock_reused_with_side_effect_after_reset(self):
        """Test that mock can be reused with side_effect after reset."""
        def effect1(x):
            return x + 10
        
        def effect2(x):
            return x * 10
        
        m = Mock(side_effect=effect1)
        
        # First usage
        self.assertEqual(m(5), 15)
        self.assertEqual(m.call_count, 1)
        
        # Reset
        m.mock_context().reset()
        
        # Reconfigure with new side_effect
        m.configure(side_effect=effect2)
        self.assertEqual(m(5), 50)
        self.assertEqual(m.call_count, 1)

    def test_assertions_work_correctly_after_reset(self):
        """Test that assertion methods work correctly after reset."""
        m = Mock()
        m(1)
        m(2)
        m.assert_called()
        
        # Reset
        m.mock_context().reset()
        
        # After reset, assert_called should fail
        with self.assertRaises(AssertionError):
            m.assert_called()
        
        # Make new calls
        m(3)
        m.assert_called()
        m.assert_called_once()
        m.assert_called_with(3)


class PatchTests(unittest.TestCase):
    def test_module_patch(self):
        original = os.path.exists
        with create_module_patch(os.path, "exists") as mock_exists:
            mock_exists.configure(return_value=True)
            self.assertTrue(os.path.exists("/tmp"))
        self.assertIs(os.path.exists, original)

    def test_class_patch(self):
        with create_class_patch(SampleClass, "cmethod") as mock_cm:
            mock_cm.configure(return_value="patched")
            self.assertEqual(SampleClass.cmethod("y"), "patched")
        self.assertEqual(SampleClass.cmethod("z"), "orig:z")

    def test_instance_patch(self):
        obj = SampleClass()
        with create_instance_patch(obj, "method") as mock_m:
            mock_m.configure(return_value=99)
            self.assertEqual(obj.method(2), 99)
        self.assertEqual(obj.method(3), obj.value + 3)


if __name__ == "__main__":
    unittest.main()


class MockMagicMethodTests(unittest.TestCase):
    """Tests for Mock magic methods (Requirements 11.1-11.12)."""

    # --- __bool__ tests ---
    def test_bool_returns_true_by_default(self):
        """Test that __bool__ returns True when return_value is not set (Requirement 11.2)."""
        m = Mock()
        self.assertTrue(bool(m))

    def test_bool_returns_bool_of_return_value_when_set(self):
        """Test that __bool__ returns bool(return_value) when return_value is set (Requirement 11.1)."""
        # Test with truthy return_value
        m = Mock(return_value=42)
        self.assertTrue(bool(m))

        # Test with falsy return_value (empty list)
        m2 = Mock(return_value=[])
        self.assertFalse(bool(m2))

        # Test with falsy return_value (0)
        m3 = Mock(return_value=0)
        self.assertFalse(bool(m3))

        # Test with falsy return_value (empty string)
        m4 = Mock(return_value="")
        self.assertFalse(bool(m4))

        # Test with truthy return_value (non-empty string)
        m5 = Mock(return_value="hello")
        self.assertTrue(bool(m5))

    def test_bool_with_none_return_value(self):
        """Test that __bool__ returns True when return_value is explicitly None."""
        m = Mock(return_value=None)
        # When return_value is None, the mock should be truthy by default
        self.assertTrue(bool(m))

    # --- __len__ tests ---
    def test_len_returns_length_of_return_value(self):
        """Test that __len__ returns len(return_value) when return_value supports len() (Requirement 11.3)."""
        # Test with list
        m = Mock(return_value=[1, 2, 3, 4, 5])
        self.assertEqual(len(m), 5)

        # Test with string
        m2 = Mock(return_value="hello")
        self.assertEqual(len(m2), 5)

        # Test with dict
        m3 = Mock(return_value={"a": 1, "b": 2})
        self.assertEqual(len(m3), 2)

        # Test with empty list
        m4 = Mock(return_value=[])
        self.assertEqual(len(m4), 0)

    def test_len_raises_type_error_without_return_value(self):
        """Test that __len__ raises TypeError when return_value is not set (Requirement 11.4)."""
        m = Mock()
        with self.assertRaises(TypeError) as context:
            len(m)
        self.assertIn("has no len()", str(context.exception))
        self.assertIn("return_value is not set", str(context.exception))

    def test_len_raises_type_error_for_non_sized_return_value(self):
        """Test that __len__ raises TypeError when return_value doesn't support len()."""
        m = Mock(return_value=42)  # int has no len()
        with self.assertRaises(TypeError) as context:
            len(m)
        self.assertIn("has no len()", str(context.exception))

    # --- __iter__ tests ---
    def test_iter_returns_iterator_of_return_value(self):
        """Test that __iter__ returns iter(return_value) when return_value is iterable (Requirement 11.5)."""
        # Test with list
        m = Mock(return_value=[1, 2, 3])
        result = list(m)
        self.assertEqual(result, [1, 2, 3])

        # Test with string
        m2 = Mock(return_value="abc")
        result2 = list(m2)
        self.assertEqual(result2, ["a", "b", "c"])

        # Test with tuple
        m3 = Mock(return_value=(10, 20, 30))
        result3 = list(m3)
        self.assertEqual(result3, [10, 20, 30])

    def test_iter_raises_type_error_without_return_value(self):
        """Test that __iter__ raises TypeError when return_value is not set (Requirement 11.6)."""
        m = Mock()
        with self.assertRaises(TypeError) as context:
            iter(m)
        self.assertIn("not iterable", str(context.exception))
        self.assertIn("return_value is not set", str(context.exception))

    def test_iter_raises_type_error_for_non_iterable_return_value(self):
        """Test that __iter__ raises TypeError when return_value is not iterable."""
        m = Mock(return_value=42)  # int is not iterable
        with self.assertRaises(TypeError) as context:
            iter(m)
        self.assertIn("not iterable", str(context.exception))

    def test_iter_in_for_loop(self):
        """Test that mock can be used in a for loop when return_value is iterable."""
        m = Mock(return_value=[1, 2, 3])
        collected = []
        for item in m:
            collected.append(item)
        self.assertEqual(collected, [1, 2, 3])

    # --- __contains__ tests ---
    def test_contains_checks_item_in_return_value(self):
        """Test that __contains__ checks if item is in return_value (Requirement 11.7)."""
        # Test with list
        m = Mock(return_value=[1, 2, 3, 4, 5])
        self.assertIn(2, m)
        self.assertNotIn(10, m)

        # Test with string
        m2 = Mock(return_value="hello world")
        self.assertIn("world", m2)
        self.assertNotIn("foo", m2)

        # Test with dict (checks keys)
        m3 = Mock(return_value={"a": 1, "b": 2})
        self.assertIn("a", m3)
        self.assertNotIn("c", m3)

        # Test with set
        m4 = Mock(return_value={1, 2, 3})
        self.assertIn(1, m4)
        self.assertNotIn(5, m4)

    def test_contains_raises_type_error_without_return_value(self):
        """Test that __contains__ raises TypeError when return_value is not set (Requirement 11.8)."""
        m = Mock()
        with self.assertRaises(TypeError) as context:
            _ = 1 in m
        self.assertIn("requires container support", str(context.exception))
        self.assertIn("return_value is not set", str(context.exception))

    def test_contains_raises_type_error_for_non_container_return_value(self):
        """Test that __contains__ raises TypeError when return_value doesn't support 'in'."""
        m = Mock(return_value=42)  # int doesn't support 'in'
        with self.assertRaises(TypeError) as context:
            _ = 1 in m
        self.assertIn("requires container support", str(context.exception))

    # --- __dir__ tests ---
    def test_dir_includes_mock_attributes(self):
        """Test that __dir__ returns a sorted list including mock_attributes keys (Requirement 11.9)."""
        m = Mock()
        ctx = m.mock_context()
        ctx.set_attribute("custom_attr", "value1")
        ctx.set_attribute("another_attr", "value2")

        dir_result = dir(m)

        # Check that custom attributes are included
        self.assertIn("custom_attr", dir_result)
        self.assertIn("another_attr", dir_result)

        # Check that the list is sorted
        self.assertEqual(dir_result, sorted(dir_result))

    def test_dir_includes_standard_mock_attributes(self):
        """Test that __dir__ includes standard Mock class attributes."""
        m = Mock()
        dir_result = dir(m)

        # Check for some standard attributes
        self.assertIn("configure", dir_result)
        self.assertIn("mock_context", dir_result)
        self.assertIn("call_count", dir_result)
        self.assertIn("call_args", dir_result)

    def test_dir_with_recursive_mock_attributes(self):
        """Test that __dir__ includes attributes created via recursive access."""
        m = Mock(recursive=True)
        _ = m.foo  # Access creates the attribute
        _ = m.bar  # Access creates another attribute

        dir_result = dir(m)

        self.assertIn("foo", dir_result)
        self.assertIn("bar", dir_result)

    # --- __repr__ tests ---
    def test_repr_includes_return_value_and_side_effect(self):
        """Test that __repr__ returns a string representation including return_value and side_effect (Requirement 11.10)."""
        m = Mock(return_value=42)
        repr_str = repr(m)
        self.assertIn("Mock", repr_str)
        self.assertIn("return_value=42", repr_str)
        self.assertIn("side_effect=None", repr_str)

    def test_repr_with_side_effect(self):
        """Test that __repr__ includes side_effect when set."""
        def my_effect():
            return "effect"
        m = Mock(side_effect=my_effect)
        repr_str = repr(m)
        self.assertIn("Mock", repr_str)
        self.assertIn("side_effect=", repr_str)

    # --- __eq__ and __ne__ tests ---
    def test_eq_same_mock_is_equal(self):
        """Test that a mock is equal to itself."""
        m = Mock(return_value=42)
        self.assertEqual(m, m)

    def test_eq_mocks_with_same_configuration_are_equal(self):
        """Test that __eq__ compares configuration (Requirement 11.11)."""
        m1 = Mock(return_value=42, recursive=True, strict_attrs=False)
        m2 = Mock(return_value=42, recursive=True, strict_attrs=False)
        self.assertEqual(m1, m2)

    def test_eq_mocks_with_different_return_value_are_not_equal(self):
        """Test that mocks with different return_value are not equal."""
        m1 = Mock(return_value=42)
        m2 = Mock(return_value=100)
        self.assertNotEqual(m1, m2)

    def test_eq_mocks_with_different_recursive_are_not_equal(self):
        """Test that mocks with different recursive setting are not equal."""
        m1 = Mock(recursive=True)
        m2 = Mock(recursive=False)
        self.assertNotEqual(m1, m2)

    def test_eq_mocks_with_different_strict_attrs_are_not_equal(self):
        """Test that mocks with different strict_attrs setting are not equal."""
        m1 = Mock(strict_attrs=True)
        m2 = Mock(strict_attrs=False)
        self.assertNotEqual(m1, m2)

    def test_eq_mocks_with_different_mock_attributes_are_not_equal(self):
        """Test that mocks with different mock_attributes are not equal."""
        m1 = Mock(mock_attributes={"a": 1})
        m2 = Mock(mock_attributes={"b": 2})
        self.assertNotEqual(m1, m2)

    def test_eq_with_non_mock_returns_not_implemented(self):
        """Test that __eq__ with non-Mock returns NotImplemented."""
        m = Mock()
        result = m.__eq__("not a mock")
        self.assertEqual(result, NotImplemented)

    def test_ne_mocks_with_different_configuration(self):
        """Test that __ne__ returns True for mocks with different configuration."""
        m1 = Mock(return_value=42)
        m2 = Mock(return_value=100)
        self.assertNotEqual(m1, m2)

    def test_ne_mocks_with_same_configuration(self):
        """Test that __ne__ returns False for mocks with same configuration."""
        m1 = Mock(return_value=42)
        m2 = Mock(return_value=42)
        self.assertFalse(m1 != m2)

    # --- __hash__ tests ---
    def test_hash_returns_consistent_value(self):
        """Test that __hash__ returns a consistent value based on object identity (Requirement 11.12)."""
        m = Mock()
        hash1 = hash(m)
        hash2 = hash(m)
        self.assertEqual(hash1, hash2)

    def test_hash_different_mocks_have_different_hashes(self):
        """Test that different mock instances have different hashes."""
        m1 = Mock()
        m2 = Mock()
        # Different objects should have different hashes (based on id())
        self.assertNotEqual(hash(m1), hash(m2))

    def test_hash_allows_mock_in_set(self):
        """Test that mocks can be used in sets due to __hash__."""
        m1 = Mock()
        m2 = Mock()
        mock_set = {m1, m2}
        self.assertEqual(len(mock_set), 2)
        self.assertIn(m1, mock_set)
        self.assertIn(m2, mock_set)

    def test_hash_allows_mock_as_dict_key(self):
        """Test that mocks can be used as dictionary keys due to __hash__."""
        m1 = Mock()
        m2 = Mock()
        mock_dict = {m1: "value1", m2: "value2"}
        self.assertEqual(mock_dict[m1], "value1")
        self.assertEqual(mock_dict[m2], "value2")

    def test_hash_same_mock_same_hash_after_configuration_change(self):
        """Test that hash remains consistent even after configuration changes."""
        m = Mock()
        hash_before = hash(m)
        m.configure(return_value=42)
        hash_after = hash(m)
        # Hash is based on id(), so it should remain the same
        self.assertEqual(hash_before, hash_after)


class PatchTypeValidationTests(unittest.TestCase):
    """Tests for Patch type validation (Requirements 15.1, 15.2, 15.3, 15.4)."""

    def test_class_owner_with_non_class_patch_type_raises_type_error(self):
        """Test TypeError for class owner with non-Class PatchType (Requirement 15.1)."""
        class TestClass:
            attr = "value"

        # Test with PatchType.Module
        with self.assertRaises(TypeError) as context:
            Patch(TestClass, "attr", PatchType.Module)
        self.assertIn("class", str(context.exception).lower())
        self.assertIn(str(PatchType.Class), str(context.exception))

        # Test with PatchType.Instance
        with self.assertRaises(TypeError) as context:
            Patch(TestClass, "attr", PatchType.Instance)
        self.assertIn("class", str(context.exception).lower())
        self.assertIn(str(PatchType.Class), str(context.exception))

    def test_module_owner_with_non_module_patch_type_raises_type_error(self):
        """Test TypeError for module owner with non-Module PatchType (Requirement 15.2)."""
        import os

        # Test with PatchType.Class
        with self.assertRaises(TypeError) as context:
            Patch(os, "path", PatchType.Class)
        self.assertIn("module", str(context.exception).lower())
        self.assertIn(str(PatchType.Module), str(context.exception))

        # Test with PatchType.Instance
        with self.assertRaises(TypeError) as context:
            Patch(os, "path", PatchType.Instance)
        self.assertIn("module", str(context.exception).lower())
        self.assertIn(str(PatchType.Module), str(context.exception))

    def test_instance_owner_with_non_instance_patch_type_raises_type_error(self):
        """Test TypeError for instance owner with non-Instance PatchType (Requirement 15.3)."""
        class TestClass:
            attr = "value"

        instance = TestClass()

        # Test with PatchType.Module
        with self.assertRaises(TypeError) as context:
            Patch(instance, "attr", PatchType.Module)
        self.assertIn("instance", str(context.exception).lower())
        self.assertIn(str(PatchType.Instance), str(context.exception))

        # Test with PatchType.Class
        with self.assertRaises(TypeError) as context:
            Patch(instance, "attr", PatchType.Class)
        self.assertIn("instance", str(context.exception).lower())
        self.assertIn(str(PatchType.Instance), str(context.exception))

    def test_error_message_indicates_expected_patch_type(self):
        """Test that error message indicates the expected PatchType (Requirement 15.4)."""
        class TestClass:
            attr = "value"

        instance = TestClass()

        # Test class owner error message
        with self.assertRaises(TypeError) as context:
            Patch(TestClass, "attr", PatchType.Module)
        error_msg = str(context.exception)
        self.assertIn(str(PatchType.Class), error_msg)

        # Test module owner error message
        import os
        with self.assertRaises(TypeError) as context:
            Patch(os, "path", PatchType.Class)
        error_msg = str(context.exception)
        self.assertIn(str(PatchType.Module), error_msg)

        # Test instance owner error message
        with self.assertRaises(TypeError) as context:
            Patch(instance, "attr", PatchType.Module)
        error_msg = str(context.exception)
        self.assertIn(str(PatchType.Instance), error_msg)

    def test_valid_class_owner_with_class_patch_type_succeeds(self):
        """Test that class owner with Class PatchType succeeds."""
        class TestClass:
            attr = "value"

        # Should not raise
        patch = Patch(TestClass, "attr", PatchType.Class)
        self.assertEqual(patch.patch_type, PatchType.Class)
        self.assertEqual(patch.owner, TestClass)
        self.assertEqual(patch.target_name, "attr")

    def test_valid_module_owner_with_module_patch_type_succeeds(self):
        """Test that module owner with Module PatchType succeeds."""
        import os

        # Should not raise
        patch = Patch(os, "path", PatchType.Module)
        self.assertEqual(patch.patch_type, PatchType.Module)
        self.assertEqual(patch.owner, os)
        self.assertEqual(patch.target_name, "path")

    def test_valid_instance_owner_with_instance_patch_type_succeeds(self):
        """Test that instance owner with Instance PatchType succeeds."""
        class TestClass:
            attr = "value"

        instance = TestClass()

        # Should not raise
        patch = Patch(instance, "attr", PatchType.Instance)
        self.assertEqual(patch.patch_type, PatchType.Instance)
        self.assertEqual(patch.owner, instance)
        self.assertEqual(patch.target_name, "attr")


class FactoryFunctionValidationTests(unittest.TestCase):
    """Tests for factory function validation (Requirements 12.4, 12.5, 12.6, 12.7)."""

    # --- create_module_patch validation tests ---
    def test_create_module_patch_raises_type_error_for_non_module(self):
        """Test TypeError for non-module in create_module_patch (Requirement 12.4)."""
        # Test with a class
        class TestClass:
            attr = "value"

        with self.assertRaises(TypeError) as context:
            create_module_patch(TestClass, "attr")
        self.assertIn("module must be a module", str(context.exception))
        self.assertIn("type", str(context.exception).lower())

    def test_create_module_patch_raises_type_error_for_instance(self):
        """Test TypeError when passing an instance to create_module_patch."""
        class TestClass:
            attr = "value"

        instance = TestClass()
        with self.assertRaises(TypeError) as context:
            create_module_patch(instance, "attr")
        self.assertIn("module must be a module", str(context.exception))

    def test_create_module_patch_raises_type_error_for_string(self):
        """Test TypeError when passing a string to create_module_patch."""
        with self.assertRaises(TypeError) as context:
            create_module_patch("not_a_module", "attr")
        self.assertIn("module must be a module", str(context.exception))

    def test_create_module_patch_raises_type_error_for_none(self):
        """Test TypeError when passing None to create_module_patch."""
        with self.assertRaises(TypeError) as context:
            create_module_patch(None, "attr")
        self.assertIn("module must be a module", str(context.exception))

    # --- create_class_patch validation tests ---
    def test_create_class_patch_raises_type_error_for_non_class(self):
        """Test TypeError for non-class in create_class_patch (Requirement 12.5)."""
        # Test with an instance
        class TestClass:
            attr = "value"

        instance = TestClass()
        with self.assertRaises(TypeError) as context:
            create_class_patch(instance, "attr")
        self.assertIn("cls must be a class", str(context.exception))

    def test_create_class_patch_raises_type_error_for_module(self):
        """Test TypeError when passing a module to create_class_patch."""
        import os
        with self.assertRaises(TypeError) as context:
            create_class_patch(os, "path")
        self.assertIn("cls must be a class", str(context.exception))

    def test_create_class_patch_raises_type_error_for_string(self):
        """Test TypeError when passing a string to create_class_patch."""
        with self.assertRaises(TypeError) as context:
            create_class_patch("not_a_class", "attr")
        self.assertIn("cls must be a class", str(context.exception))

    def test_create_class_patch_raises_type_error_for_none(self):
        """Test TypeError when passing None to create_class_patch."""
        with self.assertRaises(TypeError) as context:
            create_class_patch(None, "attr")
        self.assertIn("cls must be a class", str(context.exception))

    # --- create_instance_patch validation tests ---
    def test_create_instance_patch_raises_type_error_for_non_string_target_name(self):
        """Test TypeError for non-string target_name in create_instance_patch (Requirement 12.7)."""
        class TestClass:
            attr = "value"

        instance = TestClass()
        with self.assertRaises(TypeError) as context:
            create_instance_patch(instance, 123)
        self.assertIn("'target_name' must be a string", str(context.exception))

    # --- target_name validation tests (Requirement 12.7) ---
    def test_create_module_patch_raises_type_error_for_non_string_target_name(self):
        """Test TypeError for non-string target_name in create_module_patch (Requirement 12.7)."""
        import os
        with self.assertRaises(TypeError) as context:
            create_module_patch(os, 123)
        self.assertIn("'target_name' must be a string", str(context.exception))

    def test_create_class_patch_raises_type_error_for_non_string_target_name(self):
        """Test TypeError for non-string target_name in create_class_patch (Requirement 12.7)."""
        class TestClass:
            attr = "value"

        with self.assertRaises(TypeError) as context:
            create_class_patch(TestClass, 456)
        self.assertIn("'target_name' must be a string", str(context.exception))

    def test_create_module_patch_raises_type_error_for_none_target_name(self):
        """Test TypeError for None target_name in create_module_patch."""
        import os
        with self.assertRaises(TypeError) as context:
            create_module_patch(os, None)
        self.assertIn("'target_name' must be a string", str(context.exception))

    def test_create_class_patch_raises_type_error_for_none_target_name(self):
        """Test TypeError for None target_name in create_class_patch."""
        class TestClass:
            attr = "value"

        with self.assertRaises(TypeError) as context:
            create_class_patch(TestClass, None)
        self.assertIn("'target_name' must be a string", str(context.exception))

    def test_create_instance_patch_raises_type_error_for_none_target_name(self):
        """Test TypeError for None target_name in create_instance_patch."""
        class TestClass:
            attr = "value"

        instance = TestClass()
        with self.assertRaises(TypeError) as context:
            create_instance_patch(instance, None)
        self.assertIn("'target_name' must be a string", str(context.exception))

    def test_create_module_patch_raises_type_error_for_list_target_name(self):
        """Test TypeError for list target_name in create_module_patch."""
        import os
        with self.assertRaises(TypeError) as context:
            create_module_patch(os, ["path"])
        self.assertIn("'target_name' must be a string", str(context.exception))

    # --- Valid cases to ensure factory functions work correctly ---
    def test_create_module_patch_succeeds_with_valid_args(self):
        """Test that create_module_patch succeeds with valid arguments."""
        import os
        patch = create_module_patch(os, "path")
        self.assertEqual(patch.patch_type, PatchType.Module)
        self.assertEqual(patch.owner, os)
        self.assertEqual(patch.target_name, "path")

    def test_create_class_patch_succeeds_with_valid_args(self):
        """Test that create_class_patch succeeds with valid arguments."""
        class TestClass:
            attr = "value"

        patch = create_class_patch(TestClass, "attr")
        self.assertEqual(patch.patch_type, PatchType.Class)
        self.assertEqual(patch.owner, TestClass)
        self.assertEqual(patch.target_name, "attr")

    def test_create_instance_patch_succeeds_with_valid_args(self):
        """Test that create_instance_patch succeeds with valid arguments."""
        class TestClass:
            attr = "value"

        instance = TestClass()
        patch = create_instance_patch(instance, "attr")
        self.assertEqual(patch.patch_type, PatchType.Instance)
        self.assertEqual(patch.owner, instance)
        self.assertEqual(patch.target_name, "attr")


class PatchActivationErrorTests(unittest.TestCase):
    """Tests for patch activation errors (Requirement 13.3)."""

    def test_activate_raises_value_error_when_patching_already_patched_attribute(self):
        """Test ValueError when patching an attribute that is already a Mock from this framework (Requirement 13.3)."""
        class TestClass:
            attr = "original_value"

        # Create first patch and activate it
        patch1 = create_class_patch(TestClass, "attr")
        patch1.activate()

        # Verify the attribute is now a Mock
        self.assertIsInstance(TestClass.attr, Mock)

        # Create second patch for the same attribute
        patch2 = create_class_patch(TestClass, "attr")

        # Attempting to activate the second patch should raise ValueError
        with self.assertRaises(ValueError) as context:
            patch2.activate()

        self.assertIn("already a Mock", str(context.exception))
        self.assertIn("attr", str(context.exception))

        # Clean up - deactivate the first patch
        patch1.deactivate()

        # Verify the original value is restored
        self.assertEqual(TestClass.attr, "original_value")

    def test_activate_raises_value_error_for_module_patch_already_patched(self):
        """Test ValueError when patching an already-patched module attribute."""
        import os

        original_exists = os.path.exists

        # Create first patch and activate it
        patch1 = create_module_patch(os.path, "exists")
        patch1.activate()

        # Verify the attribute is now a Mock
        self.assertIsInstance(os.path.exists, Mock)

        # Create second patch for the same attribute
        patch2 = create_module_patch(os.path, "exists")

        # Attempting to activate the second patch should raise ValueError
        with self.assertRaises(ValueError) as context:
            patch2.activate()

        self.assertIn("already a Mock", str(context.exception))
        self.assertIn("exists", str(context.exception))

        # Clean up - deactivate the first patch
        patch1.deactivate()

        # Verify the original function is restored
        self.assertIs(os.path.exists, original_exists)

    def test_activate_raises_value_error_for_instance_patch_already_patched(self):
        """Test ValueError when patching an already-patched instance attribute."""
        class TestClass:
            def method(self):
                return "original"

        instance = TestClass()

        # Create first patch and activate it
        patch1 = create_instance_patch(instance, "method")
        patch1.activate()

        # Verify the attribute is now a Mock
        self.assertIsInstance(instance.method, Mock)

        # Create second patch for the same attribute
        patch2 = create_instance_patch(instance, "method")

        # Attempting to activate the second patch should raise ValueError
        with self.assertRaises(ValueError) as context:
            patch2.activate()

        self.assertIn("already a Mock", str(context.exception))
        self.assertIn("method", str(context.exception))

        # Clean up - deactivate the first patch
        patch1.deactivate()

    def test_activate_succeeds_after_deactivation(self):
        """Test that a new patch can be activated after the previous patch is deactivated."""
        class TestClass:
            attr = "original_value"

        # Create first patch, activate, then deactivate
        patch1 = create_class_patch(TestClass, "attr")
        patch1.activate()
        patch1.deactivate()

        # Verify the original value is restored
        self.assertEqual(TestClass.attr, "original_value")

        # Create second patch and activate it - should succeed
        patch2 = create_class_patch(TestClass, "attr")
        mock2 = patch2.activate()

        # Verify the attribute is now a Mock
        self.assertIsInstance(TestClass.attr, Mock)
        self.assertIs(TestClass.attr, mock2)

        # Clean up
        patch2.deactivate()

        # Verify the original value is restored
        self.assertEqual(TestClass.attr, "original_value")

    def test_activate_raises_value_error_with_context_manager(self):
        """Test ValueError when using context manager to patch an already-patched attribute."""
        class TestClass:
            attr = "original_value"

        # First patch using context manager
        with create_class_patch(TestClass, "attr") as mock1:
            self.assertIsInstance(TestClass.attr, Mock)

            # Create second patch while first is active
            patch2 = create_class_patch(TestClass, "attr")

            # Attempting to activate the second patch should raise ValueError
            with self.assertRaises(ValueError) as context:
                patch2.activate()

            self.assertIn("already a Mock", str(context.exception))

        # After exiting the context, the original value should be restored
        self.assertEqual(TestClass.attr, "original_value")


class WeakReferenceBehaviorTests(unittest.TestCase):
    """Tests for weak reference behavior in MockContext (Requirements 16.1, 16.2, 16.3, 16.4)."""

    def test_get_mock_returns_correct_mock(self):
        """Test that get_mock returns the correct Mock object (Requirement 16.3)."""
        m = Mock()
        ctx = m.mock_context()
        
        # get_mock should return the same Mock instance
        retrieved_mock = ctx.get_mock()
        self.assertIs(retrieved_mock, m)

    def test_get_mock_returns_same_mock_after_configuration(self):
        """Test that get_mock returns the same Mock after configuration changes."""
        m = Mock()
        ctx = m.mock_context()
        
        # Configure the mock
        m.configure(return_value=42, recursive=True)
        
        # get_mock should still return the same Mock instance
        retrieved_mock = ctx.get_mock()
        self.assertIs(retrieved_mock, m)

    def test_get_mock_returns_same_mock_after_calls(self):
        """Test that get_mock returns the same Mock after the mock has been called."""
        m = Mock(return_value="result")
        ctx = m.mock_context()
        
        # Call the mock multiple times
        m(1, 2, 3)
        m(a=1, b=2)
        m()
        
        # get_mock should still return the same Mock instance
        retrieved_mock = ctx.get_mock()
        self.assertIs(retrieved_mock, m)

    def test_get_mock_owner_returns_correct_owner(self):
        """Test that get_mock_owner returns the correct owner Mock (Requirement 16.4)."""
        parent_mock = Mock(recursive=True)
        
        # Access a child attribute to create a child mock
        child_mock = parent_mock.child_attr
        child_ctx = child_mock.mock_context()
        
        # get_mock_owner should return the parent mock
        retrieved_owner = child_ctx.get_mock_owner()
        self.assertIs(retrieved_owner, parent_mock)

    def test_get_mock_owner_returns_none_when_no_owner(self):
        """Test that get_mock_owner returns None when there is no owner (Requirement 16.4)."""
        m = Mock()
        ctx = m.mock_context()
        
        # A top-level mock has no owner
        retrieved_owner = ctx.get_mock_owner()
        self.assertIsNone(retrieved_owner)

    def test_get_mock_owner_returns_none_for_explicitly_created_mock(self):
        """Test that get_mock_owner returns None for a mock created without mock_owner."""
        m = Mock(return_value=42, recursive=True, strict_attrs=False)
        ctx = m.mock_context()
        
        # No mock_owner was provided
        retrieved_owner = ctx.get_mock_owner()
        self.assertIsNone(retrieved_owner)

    def test_get_mock_owner_with_mock_method(self):
        """Test that get_mock_owner works correctly for mocks created via mock_method."""
        parent_mock = Mock()
        parent_ctx = parent_mock.mock_context()
        
        # Create a child mock method
        child_mock = parent_ctx.mock_method("test_method", return_value="method_result")
        child_ctx = child_mock.mock_context()
        
        # get_mock_owner should return the parent mock
        retrieved_owner = child_ctx.get_mock_owner()
        self.assertIs(retrieved_owner, parent_mock)

    def test_get_mock_owner_with_mock_property(self):
        """Test that get_mock_owner works correctly for mocks created via mock_property."""
        parent_mock = Mock()
        parent_ctx = parent_mock.mock_context()
        
        # Create a child mock property
        child_mock = parent_ctx.mock_property("test_property", return_value="property_value")
        child_ctx = child_mock.mock_context()
        
        # get_mock_owner should return the parent mock
        retrieved_owner = child_ctx.get_mock_owner()
        self.assertIs(retrieved_owner, parent_mock)

    def test_weak_reference_stores_mock_reference(self):
        """Test that MockContext stores a weak reference to the Mock (Requirement 16.1)."""
        import weakref
        
        m = Mock()
        ctx = m.mock_context()
        
        # Verify that _mock_ref is a weak reference
        self.assertIsInstance(ctx._mock_ref, weakref.ref)
        
        # Verify that dereferencing it returns the mock
        self.assertIs(ctx._mock_ref(), m)

    def test_weak_reference_stores_owner_reference(self):
        """Test that MockContext stores a weak reference to the owner (Requirement 16.2)."""
        import weakref
        
        parent_mock = Mock(recursive=True)
        child_mock = parent_mock.child_attr
        child_ctx = child_mock.mock_context()
        
        # Verify that _mock_owner_ref is a weak reference
        self.assertIsInstance(child_ctx._mock_owner_ref, weakref.ref)
        
        # Verify that dereferencing it returns the parent mock
        self.assertIs(child_ctx._mock_owner_ref(), parent_mock)

    def test_weak_reference_owner_is_none_when_no_owner(self):
        """Test that _mock_owner_ref is None when no owner is provided."""
        m = Mock()
        ctx = m.mock_context()
        
        # _mock_owner_ref should be None for a top-level mock
        self.assertIsNone(ctx._mock_owner_ref)

    def test_get_mock_with_nested_recursive_mocks(self):
        """Test get_mock works correctly with deeply nested recursive mocks."""
        root = Mock(recursive=True)
        
        # Create a chain of nested mocks
        level1 = root.level1
        level2 = level1.level2
        level3 = level2.level3
        
        # Each mock's context should return the correct mock
        self.assertIs(root.mock_context().get_mock(), root)
        self.assertIs(level1.mock_context().get_mock(), level1)
        self.assertIs(level2.mock_context().get_mock(), level2)
        self.assertIs(level3.mock_context().get_mock(), level3)

    def test_get_mock_owner_with_nested_recursive_mocks(self):
        """Test get_mock_owner works correctly with deeply nested recursive mocks."""
        root = Mock(recursive=True)
        
        # Create a chain of nested mocks
        level1 = root.level1
        level2 = level1.level2
        level3 = level2.level3
        
        # Each mock's context should return the correct owner
        self.assertIsNone(root.mock_context().get_mock_owner())  # Root has no owner
        self.assertIs(level1.mock_context().get_mock_owner(), root)
        self.assertIs(level2.mock_context().get_mock_owner(), level1)
        self.assertIs(level3.mock_context().get_mock_owner(), level2)


class MultipleSimultaneousPatchesIntegrationTests(unittest.TestCase):
    """Integration tests for multiple simultaneous patches (Requirements 13.4, 14.3, 14.4)."""

    # --- Test multiple patches active at once ---
    def test_multiple_module_patches_active_simultaneously(self):
        """Test that multiple module patches can be active at the same time."""
        import os
        
        original_exists = os.path.exists
        original_isfile = os.path.isfile
        original_isdir = os.path.isdir
        
        # Create multiple patches
        patch_exists = create_module_patch(os.path, "exists")
        patch_isfile = create_module_patch(os.path, "isfile")
        patch_isdir = create_module_patch(os.path, "isdir")
        
        # Activate all patches
        mock_exists = patch_exists.activate()
        mock_isfile = patch_isfile.activate()
        mock_isdir = patch_isdir.activate()
        
        # Configure each mock differently
        mock_exists.configure(return_value=True)
        mock_isfile.configure(return_value=False)
        mock_isdir.configure(return_value=True)
        
        # Verify all patches are active and working
        self.assertTrue(os.path.exists("/any/path"))
        self.assertFalse(os.path.isfile("/any/path"))
        self.assertTrue(os.path.isdir("/any/path"))
        
        # Verify call tracking works for each
        mock_exists.assert_called_once_with("/any/path")
        mock_isfile.assert_called_once_with("/any/path")
        mock_isdir.assert_called_once_with("/any/path")
        
        # Deactivate all patches
        patch_exists.deactivate()
        patch_isfile.deactivate()
        patch_isdir.deactivate()
        
        # Verify all originals are restored
        self.assertIs(os.path.exists, original_exists)
        self.assertIs(os.path.isfile, original_isfile)
        self.assertIs(os.path.isdir, original_isdir)

    def test_multiple_class_patches_active_simultaneously(self):
        """Test that multiple class patches can be active at the same time."""
        class TestClass:
            attr1 = "original1"
            attr2 = "original2"
            attr3 = "original3"
        
        original_attr1 = TestClass.attr1
        original_attr2 = TestClass.attr2
        original_attr3 = TestClass.attr3
        
        # Create and activate multiple patches
        patch1 = create_class_patch(TestClass, "attr1")
        patch2 = create_class_patch(TestClass, "attr2")
        patch3 = create_class_patch(TestClass, "attr3")
        
        mock1 = patch1.activate()
        mock2 = patch2.activate()
        mock3 = patch3.activate()
        
        # Configure each mock
        mock1.configure(return_value="mocked1")
        mock2.configure(return_value="mocked2")
        mock3.configure(return_value="mocked3")
        
        # Verify all patches are active
        self.assertEqual(TestClass.attr1(), "mocked1")
        self.assertEqual(TestClass.attr2(), "mocked2")
        self.assertEqual(TestClass.attr3(), "mocked3")
        
        # Deactivate all patches
        patch1.deactivate()
        patch2.deactivate()
        patch3.deactivate()
        
        # Verify all originals are restored
        self.assertEqual(TestClass.attr1, original_attr1)
        self.assertEqual(TestClass.attr2, original_attr2)
        self.assertEqual(TestClass.attr3, original_attr3)

    def test_multiple_instance_patches_active_simultaneously(self):
        """Test that multiple instance patches can be active at the same time."""
        class TestClass:
            def method1(self):
                return "original1"
            def method2(self):
                return "original2"
            def method3(self):
                return "original3"
        
        instance = TestClass()
        
        # Create and activate multiple patches
        patch1 = create_instance_patch(instance, "method1")
        patch2 = create_instance_patch(instance, "method2")
        patch3 = create_instance_patch(instance, "method3")
        
        mock1 = patch1.activate()
        mock2 = patch2.activate()
        mock3 = patch3.activate()
        
        # Configure each mock
        mock1.configure(return_value="mocked1")
        mock2.configure(return_value="mocked2")
        mock3.configure(return_value="mocked3")
        
        # Verify all patches are active
        self.assertEqual(instance.method1(), "mocked1")
        self.assertEqual(instance.method2(), "mocked2")
        self.assertEqual(instance.method3(), "mocked3")
        
        # Deactivate all patches
        patch1.deactivate()
        patch2.deactivate()
        patch3.deactivate()
        
        # Verify originals are restored (methods should work again)
        self.assertEqual(instance.method1(), "original1")
        self.assertEqual(instance.method2(), "original2")
        self.assertEqual(instance.method3(), "original3")

    def test_mixed_patch_types_active_simultaneously(self):
        """Test that module, class, and instance patches can all be active at the same time."""
        import os
        
        class TestClass:
            class_attr = "original_class"
            def instance_method(self):
                return "original_instance"
        
        instance = TestClass()
        
        # Store originals
        original_exists = os.path.exists
        original_class_attr = TestClass.class_attr
        
        # Create patches of different types
        module_patch = create_module_patch(os.path, "exists")
        class_patch = create_class_patch(TestClass, "class_attr")
        instance_patch = create_instance_patch(instance, "instance_method")
        
        # Activate all patches
        mock_module = module_patch.activate()
        mock_class = class_patch.activate()
        mock_instance = instance_patch.activate()
        
        # Configure each mock
        mock_module.configure(return_value=True)
        mock_class.configure(return_value="mocked_class")
        mock_instance.configure(return_value="mocked_instance")
        
        # Verify all patches are active
        self.assertTrue(os.path.exists("/path"))
        self.assertEqual(TestClass.class_attr(), "mocked_class")
        self.assertEqual(instance.instance_method(), "mocked_instance")
        
        # Deactivate all patches
        module_patch.deactivate()
        class_patch.deactivate()
        instance_patch.deactivate()
        
        # Verify all originals are restored
        self.assertIs(os.path.exists, original_exists)
        self.assertEqual(TestClass.class_attr, original_class_attr)
        self.assertEqual(instance.instance_method(), "original_instance")

    # --- Test nested patch contexts ---
    def test_nested_patch_contexts_same_module(self):
        """Test nested patch contexts on different attributes of the same module."""
        import os
        
        original_exists = os.path.exists
        original_isfile = os.path.isfile
        
        with create_module_patch(os.path, "exists") as mock_exists:
            mock_exists.configure(return_value=True)
            self.assertTrue(os.path.exists("/outer"))
            
            with create_module_patch(os.path, "isfile") as mock_isfile:
                mock_isfile.configure(return_value=False)
                
                # Both patches should be active
                self.assertTrue(os.path.exists("/inner"))
                self.assertFalse(os.path.isfile("/inner"))
            
            # Inner patch should be deactivated, outer still active
            self.assertIs(os.path.isfile, original_isfile)
            self.assertTrue(os.path.exists("/still_outer"))
        
        # Both patches should be deactivated
        self.assertIs(os.path.exists, original_exists)
        self.assertIs(os.path.isfile, original_isfile)

    def test_nested_patch_contexts_different_classes(self):
        """Test nested patch contexts on different classes."""
        class ClassA:
            attr = "original_a"
        
        class ClassB:
            attr = "original_b"
        
        original_a = ClassA.attr
        original_b = ClassB.attr
        
        with create_class_patch(ClassA, "attr") as mock_a:
            mock_a.configure(return_value="mocked_a")
            self.assertEqual(ClassA.attr(), "mocked_a")
            
            with create_class_patch(ClassB, "attr") as mock_b:
                mock_b.configure(return_value="mocked_b")
                
                # Both patches should be active
                self.assertEqual(ClassA.attr(), "mocked_a")
                self.assertEqual(ClassB.attr(), "mocked_b")
            
            # Inner patch should be deactivated
            self.assertEqual(ClassB.attr, original_b)
            self.assertEqual(ClassA.attr(), "mocked_a")
        
        # Both patches should be deactivated
        self.assertEqual(ClassA.attr, original_a)
        self.assertEqual(ClassB.attr, original_b)

    def test_deeply_nested_patch_contexts(self):
        """Test deeply nested patch contexts (3+ levels)."""
        import os
        
        original_exists = os.path.exists
        original_isfile = os.path.isfile
        original_isdir = os.path.isdir
        
        with create_module_patch(os.path, "exists") as mock_exists:
            mock_exists.configure(return_value=True)
            
            with create_module_patch(os.path, "isfile") as mock_isfile:
                mock_isfile.configure(return_value=False)
                
                with create_module_patch(os.path, "isdir") as mock_isdir:
                    mock_isdir.configure(return_value=True)
                    
                    # All three patches should be active
                    self.assertTrue(os.path.exists("/deep"))
                    self.assertFalse(os.path.isfile("/deep"))
                    self.assertTrue(os.path.isdir("/deep"))
                
                # isdir should be restored
                self.assertIs(os.path.isdir, original_isdir)
                self.assertTrue(os.path.exists("/mid"))
                self.assertFalse(os.path.isfile("/mid"))
            
            # isfile should be restored
            self.assertIs(os.path.isfile, original_isfile)
            self.assertTrue(os.path.exists("/outer"))
        
        # All should be restored
        self.assertIs(os.path.exists, original_exists)
        self.assertIs(os.path.isfile, original_isfile)
        self.assertIs(os.path.isdir, original_isdir)

    def test_nested_patch_contexts_mixed_types(self):
        """Test nested patch contexts with mixed patch types (module, class, instance)."""
        import os
        
        class TestClass:
            attr = "original_class"
            def method(self):
                return "original_method"
        
        instance = TestClass()
        
        original_exists = os.path.exists
        original_attr = TestClass.attr
        
        with create_module_patch(os.path, "exists") as mock_module:
            mock_module.configure(return_value=True)
            
            with create_class_patch(TestClass, "attr") as mock_class:
                mock_class.configure(return_value="mocked_class")
                
                with create_instance_patch(instance, "method") as mock_instance:
                    mock_instance.configure(return_value="mocked_instance")
                    
                    # All patches should be active
                    self.assertTrue(os.path.exists("/path"))
                    self.assertEqual(TestClass.attr(), "mocked_class")
                    self.assertEqual(instance.method(), "mocked_instance")
                
                # Instance patch should be deactivated
                self.assertEqual(instance.method(), "original_method")
                self.assertTrue(os.path.exists("/path"))
                self.assertEqual(TestClass.attr(), "mocked_class")
            
            # Class patch should be deactivated
            self.assertEqual(TestClass.attr, original_attr)
            self.assertTrue(os.path.exists("/path"))
        
        # All patches should be deactivated
        self.assertIs(os.path.exists, original_exists)
        self.assertEqual(TestClass.attr, original_attr)
        self.assertEqual(instance.method(), "original_method")

    # --- Verify all originals restored correctly ---
    def test_originals_restored_after_sequential_patches(self):
        """Test that originals are correctly restored after sequential patch activations/deactivations."""
        class TestClass:
            attr = "original"
        
        original = TestClass.attr
        
        # First patch cycle
        patch1 = create_class_patch(TestClass, "attr")
        mock1 = patch1.activate()
        mock1.configure(return_value="first_mock")
        self.assertEqual(TestClass.attr(), "first_mock")
        patch1.deactivate()
        self.assertEqual(TestClass.attr, original)
        
        # Second patch cycle
        patch2 = create_class_patch(TestClass, "attr")
        mock2 = patch2.activate()
        mock2.configure(return_value="second_mock")
        self.assertEqual(TestClass.attr(), "second_mock")
        patch2.deactivate()
        self.assertEqual(TestClass.attr, original)
        
        # Third patch cycle
        patch3 = create_class_patch(TestClass, "attr")
        mock3 = patch3.activate()
        mock3.configure(return_value="third_mock")
        self.assertEqual(TestClass.attr(), "third_mock")
        patch3.deactivate()
        self.assertEqual(TestClass.attr, original)

    def test_originals_restored_in_reverse_order(self):
        """Test that originals are restored correctly when patches are deactivated in reverse order."""
        class TestClass:
            attr1 = "original1"
            attr2 = "original2"
            attr3 = "original3"
        
        original1 = TestClass.attr1
        original2 = TestClass.attr2
        original3 = TestClass.attr3
        
        # Activate patches in order
        patch1 = create_class_patch(TestClass, "attr1")
        patch2 = create_class_patch(TestClass, "attr2")
        patch3 = create_class_patch(TestClass, "attr3")
        
        mock1 = patch1.activate()
        mock2 = patch2.activate()
        mock3 = patch3.activate()
        
        mock1.configure(return_value="mocked1")
        mock2.configure(return_value="mocked2")
        mock3.configure(return_value="mocked3")
        
        # Verify all are mocked
        self.assertEqual(TestClass.attr1(), "mocked1")
        self.assertEqual(TestClass.attr2(), "mocked2")
        self.assertEqual(TestClass.attr3(), "mocked3")
        
        # Deactivate in reverse order (LIFO)
        patch3.deactivate()
        self.assertEqual(TestClass.attr3, original3)
        self.assertEqual(TestClass.attr1(), "mocked1")
        self.assertEqual(TestClass.attr2(), "mocked2")
        
        patch2.deactivate()
        self.assertEqual(TestClass.attr2, original2)
        self.assertEqual(TestClass.attr1(), "mocked1")
        
        patch1.deactivate()
        self.assertEqual(TestClass.attr1, original1)

    def test_originals_restored_in_arbitrary_order(self):
        """Test that originals are restored correctly when patches are deactivated in arbitrary order."""
        class TestClass:
            attr1 = "original1"
            attr2 = "original2"
            attr3 = "original3"
        
        original1 = TestClass.attr1
        original2 = TestClass.attr2
        original3 = TestClass.attr3
        
        # Activate patches
        patch1 = create_class_patch(TestClass, "attr1")
        patch2 = create_class_patch(TestClass, "attr2")
        patch3 = create_class_patch(TestClass, "attr3")
        
        mock1 = patch1.activate()
        mock2 = patch2.activate()
        mock3 = patch3.activate()
        
        mock1.configure(return_value="mocked1")
        mock2.configure(return_value="mocked2")
        mock3.configure(return_value="mocked3")
        
        # Deactivate in arbitrary order (middle first)
        patch2.deactivate()
        self.assertEqual(TestClass.attr2, original2)
        self.assertEqual(TestClass.attr1(), "mocked1")
        self.assertEqual(TestClass.attr3(), "mocked3")
        
        # Deactivate first
        patch1.deactivate()
        self.assertEqual(TestClass.attr1, original1)
        self.assertEqual(TestClass.attr3(), "mocked3")
        
        # Deactivate last
        patch3.deactivate()
        self.assertEqual(TestClass.attr3, original3)

    def test_call_tracking_independent_across_simultaneous_patches(self):
        """Test that call tracking is independent across multiple simultaneous patches."""
        class TestClass:
            def method1(self):
                return "original1"
            def method2(self):
                return "original2"
        
        instance = TestClass()
        
        patch1 = create_instance_patch(instance, "method1")
        patch2 = create_instance_patch(instance, "method2")
        
        mock1 = patch1.activate()
        mock2 = patch2.activate()
        
        mock1.configure(return_value="mocked1")
        mock2.configure(return_value="mocked2")
        
        # Call method1 multiple times
        instance.method1("a")
        instance.method1("b")
        instance.method1("c")
        
        # Call method2 once
        instance.method2("x")
        
        # Verify independent call tracking
        self.assertEqual(mock1.call_count, 3)
        self.assertEqual(mock2.call_count, 1)
        
        mock1.assert_any_call("a")
        mock1.assert_any_call("b")
        mock1.assert_any_call("c")
        mock2.assert_called_once_with("x")
        
        # Deactivate
        patch1.deactivate()
        patch2.deactivate()

    def test_multiple_patches_with_side_effects(self):
        """Test multiple simultaneous patches with different side effects."""
        class TestClass:
            def method1(self, x):
                return x
            def method2(self, x):
                return x
        
        instance = TestClass()
        
        patch1 = create_instance_patch(instance, "method1")
        patch2 = create_instance_patch(instance, "method2")
        
        mock1 = patch1.activate()
        mock2 = patch2.activate()
        
        # Configure with different side effects
        mock1.configure(side_effect=lambda x: x * 2)
        mock2.configure(side_effect=lambda x: x + 10)
        
        # Verify side effects work independently
        self.assertEqual(instance.method1(5), 10)
        self.assertEqual(instance.method2(5), 15)
        self.assertEqual(instance.method1(3), 6)
        self.assertEqual(instance.method2(3), 13)
        
        # Deactivate
        patch1.deactivate()
        patch2.deactivate()
        
        # Verify originals are restored
        self.assertEqual(instance.method1(5), 5)
        self.assertEqual(instance.method2(5), 5)


class NestedMockHierarchyIntegrationTests(unittest.TestCase):
    """Integration tests for nested mock hierarchies (Requirements 5.6, 9.2, 10.7)."""

    # --- Deep recursive mock chain tests (Requirement 9.2) ---
    def test_deep_recursive_mock_chain_creation(self):
        """Test that deep recursive mock chains are created correctly."""
        root = Mock(recursive=True)
        
        # Access a deep chain of attributes
        deep_mock = root.level1.level2.level3.level4.level5
        
        # Verify each level is a Mock
        self.assertIsInstance(root.level1, Mock)
        self.assertIsInstance(root.level1.level2, Mock)
        self.assertIsInstance(root.level1.level2.level3, Mock)
        self.assertIsInstance(root.level1.level2.level3.level4, Mock)
        self.assertIsInstance(root.level1.level2.level3.level4.level5, Mock)
        
        # Verify the final mock is the same as the one we accessed
        self.assertIs(deep_mock, root.level1.level2.level3.level4.level5)

    def test_deep_recursive_mock_chain_preserves_identity(self):
        """Test that accessing the same path returns the same mock instance."""
        root = Mock(recursive=True)
        
        # Access the same path multiple times
        first_access = root.a.b.c.d
        second_access = root.a.b.c.d
        third_access = root.a.b.c.d
        
        # All accesses should return the same mock instance
        self.assertIs(first_access, second_access)
        self.assertIs(second_access, third_access)

    def test_deep_recursive_mock_chain_inherits_recursive_setting(self):
        """Test that child mocks in deep chains inherit recursive setting (Requirement 10.7)."""
        root = Mock(recursive=True)
        
        # Access a deep chain
        level1 = root.level1
        level2 = level1.level2
        level3 = level2.level3
        level4 = level3.level4
        
        # Verify all levels inherit recursive=True
        self.assertTrue(level1.mock_context().recursive)
        self.assertTrue(level2.mock_context().recursive)
        self.assertTrue(level3.mock_context().recursive)
        self.assertTrue(level4.mock_context().recursive)

    def test_deep_recursive_mock_chain_inherits_strict_attrs_setting(self):
        """Test that child mocks in deep chains inherit strict_attrs setting (Requirement 10.7)."""
        # Note: When strict_attrs=True, it takes precedence over recursive=True
        # So we test by creating child mocks via mock_method which respects both settings
        root = Mock(recursive=True, strict_attrs=False)
        
        # Access a deep chain - this works because strict_attrs=False
        level1 = root.level1
        level2 = level1.level2
        level3 = level2.level3
        
        # Verify all levels inherit strict_attrs=False (the parent's setting)
        self.assertFalse(level1.mock_context()._strict_attrs)
        self.assertFalse(level2.mock_context()._strict_attrs)
        self.assertFalse(level3.mock_context()._strict_attrs)
        
        # Now test that strict_attrs=True prevents attribute access even with recursive=True
        strict_root = Mock(recursive=True, strict_attrs=True)
        with self.assertRaises(AttributeError):
            _ = strict_root.undefined_attr

    def test_deep_recursive_mock_chain_can_be_configured_at_any_level(self):
        """Test that mocks at any level in a deep chain can be configured."""
        root = Mock(recursive=True)
        
        # Configure mocks at different levels
        root.level1.configure(return_value="level1_value")
        root.level1.level2.configure(return_value="level2_value")
        root.level1.level2.level3.configure(return_value="level3_value")
        
        # Verify configurations work
        self.assertEqual(root.level1(), "level1_value")
        self.assertEqual(root.level1.level2(), "level2_value")
        self.assertEqual(root.level1.level2.level3(), "level3_value")

    def test_deep_recursive_mock_chain_with_side_effects(self):
        """Test that side effects work at any level in a deep chain."""
        root = Mock(recursive=True)
        
        # Configure side effects at different levels
        root.level1.configure(side_effect=lambda: "effect1")
        root.level1.level2.configure(side_effect=lambda x: x * 2)
        root.level1.level2.level3.configure(side_effect=lambda x, y: x + y)
        
        # Verify side effects work
        self.assertEqual(root.level1(), "effect1")
        self.assertEqual(root.level1.level2(5), 10)
        self.assertEqual(root.level1.level2.level3(3, 4), 7)

    def test_deep_recursive_mock_chain_call_tracking_at_each_level(self):
        """Test that call tracking works independently at each level."""
        root = Mock(recursive=True)
        
        # Call mocks at different levels
        root.level1(1)
        root.level1(2)
        root.level1.level2(3)
        root.level1.level2.level3(4, key="value")
        
        # Verify call tracking at each level
        self.assertEqual(root.level1.call_count, 2)
        self.assertEqual(root.level1.call_args_list, [((1,), {}), ((2,), {})])
        
        self.assertEqual(root.level1.level2.call_count, 1)
        self.assertEqual(root.level1.level2.call_args, ((3,), {}))
        
        self.assertEqual(root.level1.level2.level3.call_count, 1)
        self.assertEqual(root.level1.level2.level3.call_args, ((4,), {"key": "value"}))

    def test_deep_recursive_mock_chain_assertions_at_each_level(self):
        """Test that assertion methods work at each level in a deep chain."""
        root = Mock(recursive=True)
        
        # Call mocks at different levels
        root.level1("arg1")
        root.level1.level2("arg2", key="val")
        root.level1.level2.level3()
        
        # Verify assertions work at each level
        root.level1.assert_called()
        root.level1.assert_called_once()
        root.level1.assert_called_with("arg1")
        
        root.level1.level2.assert_called()
        root.level1.level2.assert_called_once_with("arg2", key="val")
        
        root.level1.level2.level3.assert_called()
        root.level1.level2.level3.assert_called_once_with()

    def test_deep_recursive_mock_chain_branching_paths(self):
        """Test that different branches in a mock hierarchy are independent."""
        root = Mock(recursive=True)
        
        # Create two different branches
        branch_a = root.branch_a.sub_a.leaf_a
        branch_b = root.branch_b.sub_b.leaf_b
        
        # Configure them differently
        branch_a.configure(return_value="A")
        branch_b.configure(return_value="B")
        
        # Verify they are independent
        self.assertEqual(root.branch_a.sub_a.leaf_a(), "A")
        self.assertEqual(root.branch_b.sub_b.leaf_b(), "B")
        
        # Verify they are different mock instances
        self.assertIsNot(branch_a, branch_b)
        self.assertIsNot(root.branch_a, root.branch_b)

    def test_deep_recursive_mock_chain_with_mock_method(self):
        """Test that mock_method works correctly in deep chains."""
        root = Mock(recursive=True)
        
        # Create a method on a deep mock
        root.level1.level2.mock_context().mock_method("custom_method", return_value="custom_result")
        
        # Verify the method works
        result = root.level1.level2.custom_method()
        self.assertEqual(result, "custom_result")
        
        # Verify call tracking on the method
        root.level1.level2.custom_method.assert_called_once()

    def test_deep_recursive_mock_chain_with_mock_property(self):
        """Test that mock_property works correctly in deep chains."""
        root = Mock(recursive=True)
        
        # Create a property on a deep mock
        root.level1.level2.mock_context().mock_property("custom_property", return_value="property_value")
        
        # Verify the property works
        result = root.level1.level2.custom_property()
        self.assertEqual(result, "property_value")

    # --- mock_calls tracking for nested calls tests (Requirement 5.6) ---
    def test_mock_calls_tracks_direct_calls(self):
        """Test that mock_calls tracks direct calls to the mock."""
        m = Mock()
        
        m(1, 2)
        m(3, key="value")
        m()
        
        # mock_calls should contain all direct calls
        self.assertEqual(len(m.mock_calls), 3)
        self.assertEqual(m.mock_calls[0], ('', (1, 2), {}))
        self.assertEqual(m.mock_calls[1], ('', (3,), {"key": "value"}))
        self.assertEqual(m.mock_calls[2], ('', (), {}))

    def test_mock_calls_format_is_correct(self):
        """Test that mock_calls entries have the correct format (name, args, kwargs)."""
        m = Mock()
        
        m("arg1", "arg2", kwarg1="val1", kwarg2="val2")
        
        # Verify the format
        self.assertEqual(len(m.mock_calls), 1)
        call_entry = m.mock_calls[0]
        
        # Should be a tuple of (name, args, kwargs)
        self.assertIsInstance(call_entry, tuple)
        self.assertEqual(len(call_entry), 3)
        
        name, args, kwargs = call_entry
        self.assertEqual(name, '')  # Direct call has empty name
        self.assertEqual(args, ("arg1", "arg2"))
        self.assertEqual(kwargs, {"kwarg1": "val1", "kwarg2": "val2"})

    def test_mock_calls_empty_when_no_calls_made(self):
        """Test that mock_calls is empty when no calls have been made."""
        m = Mock()
        
        self.assertEqual(m.mock_calls, [])
        self.assertEqual(len(m.mock_calls), 0)

    def test_mock_calls_cleared_after_reset(self):
        """Test that mock_calls is cleared after reset."""
        m = Mock()
        
        m(1)
        m(2)
        m(3)
        
        self.assertEqual(len(m.mock_calls), 3)
        
        m.mock_context().reset()
        
        self.assertEqual(m.mock_calls, [])

    def test_child_mock_has_independent_mock_calls(self):
        """Test that child mocks have their own independent mock_calls."""
        root = Mock(recursive=True)
        
        # Call root and child
        root("root_call")
        root.child("child_call")
        
        # Each should have independent mock_calls
        self.assertEqual(len(root.mock_calls), 1)
        self.assertEqual(root.mock_calls[0], ('', ("root_call",), {}))
        
        self.assertEqual(len(root.child.mock_calls), 1)
        self.assertEqual(root.child.mock_calls[0], ('', ("child_call",), {}))

    def test_nested_mock_calls_tracking_in_deep_hierarchy(self):
        """Test mock_calls tracking in a deep mock hierarchy."""
        root = Mock(recursive=True)
        
        # Make calls at various levels
        root("root")
        root.level1("l1")
        root.level1.level2("l2")
        root.level1.level2.level3("l3")
        
        # Verify each level tracks its own calls
        self.assertEqual(root.call_count, 1)
        self.assertEqual(root.level1.call_count, 1)
        self.assertEqual(root.level1.level2.call_count, 1)
        self.assertEqual(root.level1.level2.level3.call_count, 1)
        
        # Verify mock_calls at each level
        self.assertEqual(root.mock_calls, [('', ("root",), {})])
        self.assertEqual(root.level1.mock_calls, [('', ("l1",), {})])
        self.assertEqual(root.level1.level2.mock_calls, [('', ("l2",), {})])
        self.assertEqual(root.level1.level2.level3.mock_calls, [('', ("l3",), {})])

    # --- Integration scenarios ---
    def test_complex_mock_hierarchy_simulation(self):
        """Test a complex mock hierarchy simulating a real-world scenario."""
        # Simulate a database session with query builder pattern
        db = Mock(recursive=True)
        
        # Configure the chain: db.session.query(Model).filter(...).first()
        db.session.query.configure(return_value=db.session.query)
        db.session.query.filter.configure(return_value=db.session.query.filter)
        db.session.query.filter.first.configure(return_value={"id": 1, "name": "Test"})
        
        # Use the mock chain
        result = db.session.query("User").filter(id=1).first()
        
        # Verify the result
        self.assertEqual(result, {"id": 1, "name": "Test"})
        
        # Verify calls were tracked
        db.session.query.assert_called_with("User")
        db.session.query.filter.assert_called_with(id=1)
        db.session.query.filter.first.assert_called_once()

    def test_mock_hierarchy_with_method_chaining(self):
        """Test mock hierarchy with fluent method chaining pattern."""
        builder = Mock(recursive=True)
        
        # Configure each method to return the builder for chaining
        builder.set_name.configure(return_value=builder)
        builder.set_age.configure(return_value=builder)
        builder.set_email.configure(return_value=builder)
        builder.build.configure(return_value={"name": "John", "age": 30, "email": "john@example.com"})
        
        # Use the fluent interface
        result = builder.set_name("John").set_age(30).set_email("john@example.com").build()
        
        # Verify the result
        self.assertEqual(result, {"name": "John", "age": 30, "email": "john@example.com"})
        
        # Verify all methods were called
        builder.set_name.assert_called_with("John")
        builder.set_age.assert_called_with(30)
        builder.set_email.assert_called_with("john@example.com")
        builder.build.assert_called_once()

    def test_mock_hierarchy_reset_at_specific_level(self):
        """Test that resetting a mock at one level doesn't affect other levels."""
        root = Mock(recursive=True)
        
        # Make calls at multiple levels
        root("root_call")
        root.child("child_call")
        root.child.grandchild("grandchild_call")
        
        # Reset only the child level
        root.child.mock_context().reset()
        
        # Root should still have its calls
        self.assertEqual(root.call_count, 1)
        root.assert_called_with("root_call")
        
        # Child should be reset
        self.assertEqual(root.child.call_count, 0)
        
        # Grandchild should still have its calls (reset doesn't cascade)
        self.assertEqual(root.child.grandchild.call_count, 1)
        root.child.grandchild.assert_called_with("grandchild_call")

    def test_mock_hierarchy_owner_chain(self):
        """Test that the owner chain is correctly maintained in deep hierarchies."""
        root = Mock(recursive=True)
        
        # Create a deep chain
        level1 = root.level1
        level2 = level1.level2
        level3 = level2.level3
        level4 = level3.level4
        
        # Verify the owner chain
        self.assertIsNone(root.mock_context().get_mock_owner())
        self.assertIs(level1.mock_context().get_mock_owner(), root)
        self.assertIs(level2.mock_context().get_mock_owner(), level1)
        self.assertIs(level3.mock_context().get_mock_owner(), level2)
        self.assertIs(level4.mock_context().get_mock_owner(), level3)

    def test_mock_hierarchy_with_mixed_configuration(self):
        """Test a mock hierarchy with different configurations at different levels."""
        root = Mock(recursive=True)
        
        # Configure different behaviors at different levels
        root.configure(return_value="root_value")
        root.level1.configure(side_effect=lambda x: x * 2)
        root.level1.level2.configure(return_value=[1, 2, 3])
        
        # Verify each level behaves according to its configuration
        self.assertEqual(root(), "root_value")
        self.assertEqual(root.level1(5), 10)
        self.assertEqual(root.level1.level2(), [1, 2, 3])
        
        # Verify magic methods work on configured mocks
        self.assertEqual(len(root.level1.level2), 3)
        self.assertIn(2, root.level1.level2)

    def test_deep_mock_chain_with_ten_levels(self):
        """Test that very deep mock chains (10 levels) work correctly."""
        root = Mock(recursive=True)
        
        # Access a 10-level deep chain
        deep = root.l1.l2.l3.l4.l5.l6.l7.l8.l9.l10
        
        # Configure and use the deepest level
        deep.configure(return_value="deep_value")
        result = deep()
        
        self.assertEqual(result, "deep_value")
        deep.assert_called_once()
        
        # Verify the chain is intact
        self.assertIs(root.l1.l2.l3.l4.l5.l6.l7.l8.l9.l10, deep)


class PatchExceptionHandlingIntegrationTests(unittest.TestCase):
    """Integration tests for exception handling in patches (Requirements 14.4, 14.5)."""

    # --- Test patch deactivation when exception raised (Requirement 14.4) ---
    def test_module_patch_restores_original_on_exception(self):
        """Test that module patch restores original attribute when exception is raised in context."""
        import os
        
        original_exists = os.path.exists
        
        # Verify original is restored even when exception is raised
        with self.assertRaises(ValueError):
            with create_module_patch(os.path, "exists") as mock_exists:
                mock_exists.configure(return_value=True)
                # Verify patch is active
                self.assertTrue(os.path.exists("/any/path"))
                self.assertIsInstance(os.path.exists, Mock)
                # Raise an exception
                raise ValueError("Test exception")
        
        # Verify original is restored after exception
        self.assertIs(os.path.exists, original_exists)
        self.assertNotIsInstance(os.path.exists, Mock)

    def test_class_patch_restores_original_on_exception(self):
        """Test that class patch restores original attribute when exception is raised in context."""
        class TestClass:
            attr = "original_value"
        
        original_attr = TestClass.attr
        
        # Verify original is restored even when exception is raised
        with self.assertRaises(RuntimeError):
            with create_class_patch(TestClass, "attr") as mock_attr:
                mock_attr.configure(return_value="mocked_value")
                # Verify patch is active
                self.assertEqual(TestClass.attr(), "mocked_value")
                self.assertIsInstance(TestClass.attr, Mock)
                # Raise an exception
                raise RuntimeError("Test exception")
        
        # Verify original is restored after exception
        self.assertEqual(TestClass.attr, original_attr)
        self.assertNotIsInstance(TestClass.attr, Mock)

    def test_instance_patch_restores_original_on_exception(self):
        """Test that instance patch restores original attribute when exception is raised in context."""
        class TestClass:
            def method(self):
                return "original_method"
        
        instance = TestClass()
        
        # Verify original is restored even when exception is raised
        with self.assertRaises(KeyError):
            with create_instance_patch(instance, "method") as mock_method:
                mock_method.configure(return_value="mocked_method")
                # Verify patch is active
                self.assertEqual(instance.method(), "mocked_method")
                self.assertIsInstance(instance.method, Mock)
                # Raise an exception
                raise KeyError("Test exception")
        
        # Verify original is restored after exception
        self.assertEqual(instance.method(), "original_method")
        self.assertNotIsInstance(instance.method, Mock)

    def test_nested_patches_restore_originals_on_exception_in_inner_context(self):
        """Test that nested patches restore originals when exception is raised in inner context."""
        import os
        
        class TestClass:
            attr = "original_class"
        
        original_exists = os.path.exists
        original_attr = TestClass.attr
        
        # Outer patch should remain active, inner patch should be deactivated
        with create_module_patch(os.path, "exists") as mock_exists:
            mock_exists.configure(return_value=True)
            
            with self.assertRaises(TypeError):
                with create_class_patch(TestClass, "attr") as mock_attr:
                    mock_attr.configure(return_value="mocked_class")
                    # Both patches should be active
                    self.assertTrue(os.path.exists("/path"))
                    self.assertEqual(TestClass.attr(), "mocked_class")
                    # Raise exception in inner context
                    raise TypeError("Inner exception")
            
            # Inner patch should be deactivated, outer still active
            self.assertEqual(TestClass.attr, original_attr)
            self.assertTrue(os.path.exists("/still_patched"))
        
        # Both patches should be deactivated
        self.assertIs(os.path.exists, original_exists)
        self.assertEqual(TestClass.attr, original_attr)

    def test_nested_patches_restore_originals_on_exception_in_outer_context(self):
        """Test that nested patches restore originals when exception is raised in outer context."""
        import os
        
        class TestClass:
            attr = "original_class"
        
        original_exists = os.path.exists
        original_attr = TestClass.attr
        
        with self.assertRaises(AttributeError):
            with create_module_patch(os.path, "exists") as mock_exists:
                mock_exists.configure(return_value=True)
                
                with create_class_patch(TestClass, "attr") as mock_attr:
                    mock_attr.configure(return_value="mocked_class")
                    # Both patches should be active
                    self.assertTrue(os.path.exists("/path"))
                    self.assertEqual(TestClass.attr(), "mocked_class")
                
                # Inner context exited normally, inner patch deactivated
                self.assertEqual(TestClass.attr, original_attr)
                # Outer patch still active
                self.assertTrue(os.path.exists("/still_patched"))
                # Raise exception in outer context
                raise AttributeError("Outer exception")
        
        # Both patches should be deactivated
        self.assertIs(os.path.exists, original_exists)
        self.assertEqual(TestClass.attr, original_attr)

    def test_deeply_nested_patches_restore_originals_on_exception(self):
        """Test that deeply nested patches (3+ levels) restore originals on exception."""
        import os
        
        original_exists = os.path.exists
        original_isfile = os.path.isfile
        original_isdir = os.path.isdir
        
        with self.assertRaises(IOError):
            with create_module_patch(os.path, "exists") as mock_exists:
                mock_exists.configure(return_value=True)
                
                with create_module_patch(os.path, "isfile") as mock_isfile:
                    mock_isfile.configure(return_value=False)
                    
                    with create_module_patch(os.path, "isdir") as mock_isdir:
                        mock_isdir.configure(return_value=True)
                        
                        # All three patches should be active
                        self.assertTrue(os.path.exists("/deep"))
                        self.assertFalse(os.path.isfile("/deep"))
                        self.assertTrue(os.path.isdir("/deep"))
                        
                        # Raise exception at deepest level
                        raise IOError("Deep exception")
        
        # All patches should be deactivated
        self.assertIs(os.path.exists, original_exists)
        self.assertIs(os.path.isfile, original_isfile)
        self.assertIs(os.path.isdir, original_isdir)

    # --- Test exception is not suppressed (Requirement 14.5) ---
    def test_module_patch_does_not_suppress_exception(self):
        """Test that module patch context manager does not suppress exceptions."""
        import os
        
        # Verify the specific exception type and message are preserved
        with self.assertRaises(ValueError) as context:
            with create_module_patch(os.path, "exists") as mock_exists:
                raise ValueError("Specific error message")
        
        self.assertEqual(str(context.exception), "Specific error message")

    def test_class_patch_does_not_suppress_exception(self):
        """Test that class patch context manager does not suppress exceptions."""
        class TestClass:
            attr = "original"
        
        # Verify the specific exception type and message are preserved
        with self.assertRaises(RuntimeError) as context:
            with create_class_patch(TestClass, "attr") as mock_attr:
                raise RuntimeError("Runtime error message")
        
        self.assertEqual(str(context.exception), "Runtime error message")

    def test_instance_patch_does_not_suppress_exception(self):
        """Test that instance patch context manager does not suppress exceptions."""
        class TestClass:
            def method(self):
                return "original"
        
        instance = TestClass()
        
        # Verify the specific exception type and message are preserved
        with self.assertRaises(KeyError) as context:
            with create_instance_patch(instance, "method") as mock_method:
                raise KeyError("key_name")
        
        self.assertEqual(str(context.exception), "'key_name'")

    def test_patch_does_not_suppress_custom_exception(self):
        """Test that patch context manager does not suppress custom exception types."""
        class CustomException(Exception):
            def __init__(self, code, message):
                self.code = code
                self.message = message
                super().__init__(f"[{code}] {message}")
        
        class TestClass:
            attr = "original"
        
        # Verify custom exception is not suppressed and attributes are preserved
        with self.assertRaises(CustomException) as context:
            with create_class_patch(TestClass, "attr") as mock_attr:
                raise CustomException(404, "Not found")
        
        self.assertEqual(context.exception.code, 404)
        self.assertEqual(context.exception.message, "Not found")

    def test_patch_does_not_suppress_base_exception(self):
        """Test that patch context manager does not suppress BaseException subclasses."""
        class TestClass:
            attr = "original"
        
        original_attr = TestClass.attr
        
        # Test with SystemExit (a BaseException subclass)
        with self.assertRaises(SystemExit) as context:
            with create_class_patch(TestClass, "attr") as mock_attr:
                raise SystemExit(1)
        
        self.assertEqual(context.exception.code, 1)
        # Verify original is still restored
        self.assertEqual(TestClass.attr, original_attr)

    def test_patch_does_not_suppress_keyboard_interrupt(self):
        """Test that patch context manager does not suppress KeyboardInterrupt."""
        class TestClass:
            attr = "original"
        
        original_attr = TestClass.attr
        
        # Test with KeyboardInterrupt (a BaseException subclass)
        with self.assertRaises(KeyboardInterrupt):
            with create_class_patch(TestClass, "attr") as mock_attr:
                raise KeyboardInterrupt()
        
        # Verify original is still restored
        self.assertEqual(TestClass.attr, original_attr)

    # --- Combined tests for both requirements ---
    def test_exception_propagates_and_original_restored_with_side_effect(self):
        """Test that exception propagates and original is restored when mock has side_effect."""
        class TestClass:
            def method(self, x):
                return x * 2
        
        instance = TestClass()
        
        with self.assertRaises(ZeroDivisionError):
            with create_instance_patch(instance, "method") as mock_method:
                # Configure mock with a side effect that will be called
                mock_method.configure(side_effect=lambda x: x * 3)
                # Verify mock is working
                self.assertEqual(instance.method(5), 15)
                # Raise an exception
                raise ZeroDivisionError("division by zero")
        
        # Verify original is restored
        self.assertEqual(instance.method(5), 10)

    def test_exception_propagates_and_original_restored_after_mock_calls(self):
        """Test that exception propagates and original is restored after mock has been called."""
        import os
        
        original_exists = os.path.exists
        
        with self.assertRaises(PermissionError):
            with create_module_patch(os.path, "exists") as mock_exists:
                mock_exists.configure(return_value=True)
                # Make several calls to the mock
                os.path.exists("/path1")
                os.path.exists("/path2")
                os.path.exists("/path3")
                # Verify call tracking
                self.assertEqual(mock_exists.call_count, 3)
                # Raise an exception
                raise PermissionError("Access denied")
        
        # Verify original is restored
        self.assertIs(os.path.exists, original_exists)

    def test_exception_in_mock_side_effect_restores_original(self):
        """Test that exception raised by mock's side_effect still restores original."""
        class TestClass:
            def method(self):
                return "original"
        
        instance = TestClass()
        
        def raising_side_effect():
            raise ValueError("Side effect error")
        
        with self.assertRaises(ValueError) as context:
            with create_instance_patch(instance, "method") as mock_method:
                mock_method.configure(side_effect=raising_side_effect)
                # This call will raise the exception from side_effect
                instance.method()
        
        self.assertEqual(str(context.exception), "Side effect error")
        # Verify original is restored
        self.assertEqual(instance.method(), "original")

    def test_multiple_patches_all_restore_on_exception(self):
        """Test that multiple simultaneous patches all restore originals on exception."""
        import os
        
        class TestClass:
            attr1 = "original1"
            attr2 = "original2"
        
        original_exists = os.path.exists
        original_attr1 = TestClass.attr1
        original_attr2 = TestClass.attr2
        
        # Activate multiple patches manually
        patch1 = create_module_patch(os.path, "exists")
        patch2 = create_class_patch(TestClass, "attr1")
        patch3 = create_class_patch(TestClass, "attr2")
        
        mock1 = patch1.activate()
        mock2 = patch2.activate()
        mock3 = patch3.activate()
        
        mock1.configure(return_value=True)
        mock2.configure(return_value="mocked1")
        mock3.configure(return_value="mocked2")
        
        try:
            # Verify all patches are active
            self.assertTrue(os.path.exists("/path"))
            self.assertEqual(TestClass.attr1(), "mocked1")
            self.assertEqual(TestClass.attr2(), "mocked2")
            # Raise an exception
            raise Exception("Test exception")
        except Exception:
            pass
        finally:
            # Deactivate all patches (simulating what context manager does)
            patch3.deactivate()
            patch2.deactivate()
            patch1.deactivate()
        
        # Verify all originals are restored
        self.assertIs(os.path.exists, original_exists)
        self.assertEqual(TestClass.attr1, original_attr1)
        self.assertEqual(TestClass.attr2, original_attr2)


class ConfigurationValidationTests(unittest.TestCase):
    """Tests for validation of invalid configurations (Requirements 4.6, 7.3, 7.4)."""

    # --- side_effect validation tests (Requirement 4.6) ---
    def test_mock_init_raises_type_error_for_non_callable_side_effect(self):
        """Test that Mock.__init__ raises TypeError for non-callable side_effect (Requirement 4.6)."""
        with self.assertRaises(TypeError) as context:
            Mock(side_effect="not a callable")
        self.assertIn("side_effect must be a SideEffect instance or a callable", str(context.exception))

    def test_mock_init_raises_type_error_for_integer_side_effect(self):
        """Test that Mock.__init__ raises TypeError for integer side_effect."""
        with self.assertRaises(TypeError) as context:
            Mock(side_effect=123)
        self.assertIn("side_effect must be a SideEffect instance or a callable", str(context.exception))

    def test_mock_init_raises_type_error_for_list_side_effect(self):
        """Test that Mock.__init__ raises TypeError for list side_effect."""
        with self.assertRaises(TypeError) as context:
            Mock(side_effect=[1, 2, 3])
        self.assertIn("side_effect must be a SideEffect instance or a callable", str(context.exception))

    def test_mock_init_raises_type_error_for_dict_side_effect(self):
        """Test that Mock.__init__ raises TypeError for dict side_effect."""
        with self.assertRaises(TypeError) as context:
            Mock(side_effect={"key": "value"})
        self.assertIn("side_effect must be a SideEffect instance or a callable", str(context.exception))

    def test_mock_init_accepts_callable_side_effect(self):
        """Test that Mock.__init__ accepts callable side_effect."""
        def my_effect(x):
            return x * 2
        
        # Should not raise
        m = Mock(side_effect=my_effect)
        self.assertEqual(m(5), 10)

    def test_mock_init_accepts_side_effect_instance(self):
        """Test that Mock.__init__ accepts SideEffect instance."""
        def my_effect(x):
            return x + 100
        
        se = SideEffect(my_effect)
        # Should not raise
        m = Mock(side_effect=se)
        self.assertEqual(m(5), 105)

    def test_mock_init_accepts_none_side_effect(self):
        """Test that Mock.__init__ accepts None side_effect."""
        # Should not raise
        m = Mock(side_effect=None)
        self.assertIsNone(m.mock_context().side_effect)

    def test_configure_raises_type_error_for_non_callable_side_effect(self):
        """Test that configure raises TypeError for non-callable side_effect."""
        m = Mock()
        with self.assertRaises(TypeError) as context:
            m.configure(side_effect="not callable")
        self.assertIn("side_effect must be a SideEffect instance or a callable", str(context.exception))

    def test_configure_raises_type_error_for_integer_side_effect(self):
        """Test that configure raises TypeError for integer side_effect."""
        m = Mock()
        with self.assertRaises(TypeError) as context:
            m.configure(side_effect=42)
        self.assertIn("side_effect must be a SideEffect instance or a callable", str(context.exception))

    def test_configure_accepts_callable_side_effect(self):
        """Test that configure accepts callable side_effect."""
        m = Mock()
        m.configure(side_effect=lambda x: x * 3)
        self.assertEqual(m(4), 12)

    def test_configure_accepts_side_effect_instance(self):
        """Test that configure accepts SideEffect instance."""
        m = Mock()
        se = SideEffect(lambda x: x - 10)
        m.configure(side_effect=se)
        self.assertEqual(m(20), 10)

    def test_configure_accepts_none_side_effect(self):
        """Test that configure accepts None side_effect to clear it."""
        m = Mock(side_effect=lambda: "effect")
        self.assertIsNotNone(m.mock_context().side_effect)
        m.configure(side_effect=None)
        self.assertIsNone(m.mock_context().side_effect)

    # --- recursive validation tests (Requirement 7.3) ---
    def test_mock_init_raises_type_error_for_non_boolean_recursive(self):
        """Test that Mock.__init__ raises TypeError for non-boolean recursive (Requirement 7.3)."""
        with self.assertRaises(TypeError) as context:
            Mock(recursive="true")
        self.assertIn("'recursive' must be a boolean value", str(context.exception))

    def test_mock_init_raises_type_error_for_integer_recursive(self):
        """Test that Mock.__init__ raises TypeError for integer recursive."""
        with self.assertRaises(TypeError) as context:
            Mock(recursive=1)
        self.assertIn("'recursive' must be a boolean value", str(context.exception))

    def test_mock_init_raises_type_error_for_none_recursive(self):
        """Test that Mock.__init__ raises TypeError for None recursive."""
        with self.assertRaises(TypeError) as context:
            Mock(recursive=None)
        self.assertIn("'recursive' must be a boolean value", str(context.exception))

    def test_mock_init_raises_type_error_for_list_recursive(self):
        """Test that Mock.__init__ raises TypeError for list recursive."""
        with self.assertRaises(TypeError) as context:
            Mock(recursive=[True])
        self.assertIn("'recursive' must be a boolean value", str(context.exception))

    def test_mock_init_accepts_true_recursive(self):
        """Test that Mock.__init__ accepts True for recursive."""
        # Should not raise
        m = Mock(recursive=True)
        self.assertTrue(m.mock_context().recursive)

    def test_mock_init_accepts_false_recursive(self):
        """Test that Mock.__init__ accepts False for recursive."""
        # Should not raise
        m = Mock(recursive=False)
        self.assertFalse(m.mock_context().recursive)

    def test_configure_raises_type_error_for_non_boolean_recursive(self):
        """Test that configure raises TypeError for non-boolean recursive."""
        m = Mock()
        with self.assertRaises(TypeError) as context:
            m.configure(recursive="yes")
        self.assertIn("'recursive' must be a boolean value", str(context.exception))

    def test_configure_raises_type_error_for_integer_recursive(self):
        """Test that configure raises TypeError for integer recursive."""
        m = Mock()
        with self.assertRaises(TypeError) as context:
            m.configure(recursive=0)
        self.assertIn("'recursive' must be a boolean value", str(context.exception))

    def test_configure_accepts_true_recursive(self):
        """Test that configure accepts True for recursive."""
        m = Mock()
        m.configure(recursive=True)
        self.assertTrue(m.mock_context().recursive)

    def test_configure_accepts_false_recursive(self):
        """Test that configure accepts False for recursive."""
        m = Mock(recursive=True)
        m.configure(recursive=False)
        self.assertFalse(m.mock_context().recursive)

    def test_recursive_setter_raises_type_error_for_non_boolean(self):
        """Test that recursive setter raises TypeError for non-boolean value."""
        m = Mock()
        with self.assertRaises(TypeError) as context:
            m.mock_context().recursive = "true"
        self.assertIn("recursive must be a boolean value", str(context.exception))

    def test_recursive_setter_accepts_boolean(self):
        """Test that recursive setter accepts boolean values."""
        m = Mock()
        m.mock_context().recursive = True
        self.assertTrue(m.mock_context().recursive)
        m.mock_context().recursive = False
        self.assertFalse(m.mock_context().recursive)

    # --- strict_attrs validation tests (Requirement 7.4) ---
    def test_mock_init_raises_type_error_for_non_boolean_strict_attrs(self):
        """Test that Mock.__init__ raises TypeError for non-boolean strict_attrs (Requirement 7.4)."""
        with self.assertRaises(TypeError) as context:
            Mock(strict_attrs="true")
        self.assertIn("'strict_attrs' must be a boolean value", str(context.exception))

    def test_mock_init_raises_type_error_for_integer_strict_attrs(self):
        """Test that Mock.__init__ raises TypeError for integer strict_attrs."""
        with self.assertRaises(TypeError) as context:
            Mock(strict_attrs=1)
        self.assertIn("'strict_attrs' must be a boolean value", str(context.exception))

    def test_mock_init_raises_type_error_for_none_strict_attrs(self):
        """Test that Mock.__init__ raises TypeError for None strict_attrs."""
        with self.assertRaises(TypeError) as context:
            Mock(strict_attrs=None)
        self.assertIn("'strict_attrs' must be a boolean value", str(context.exception))

    def test_mock_init_raises_type_error_for_list_strict_attrs(self):
        """Test that Mock.__init__ raises TypeError for list strict_attrs."""
        with self.assertRaises(TypeError) as context:
            Mock(strict_attrs=[False])
        self.assertIn("'strict_attrs' must be a boolean value", str(context.exception))

    def test_mock_init_accepts_true_strict_attrs(self):
        """Test that Mock.__init__ accepts True for strict_attrs."""
        # Should not raise
        m = Mock(strict_attrs=True)
        self.assertTrue(m.mock_context()._strict_attrs)

    def test_mock_init_accepts_false_strict_attrs(self):
        """Test that Mock.__init__ accepts False for strict_attrs."""
        # Should not raise
        m = Mock(strict_attrs=False)
        self.assertFalse(m.mock_context()._strict_attrs)

    def test_configure_raises_type_error_for_non_boolean_strict_attrs(self):
        """Test that configure raises TypeError for non-boolean strict_attrs."""
        m = Mock()
        with self.assertRaises(TypeError) as context:
            m.configure(strict_attrs="no")
        self.assertIn("'strict_attrs' must be a boolean value", str(context.exception))

    def test_configure_raises_type_error_for_integer_strict_attrs(self):
        """Test that configure raises TypeError for integer strict_attrs."""
        m = Mock()
        with self.assertRaises(TypeError) as context:
            m.configure(strict_attrs=0)
        self.assertIn("'strict_attrs' must be a boolean value", str(context.exception))

    def test_configure_accepts_true_strict_attrs(self):
        """Test that configure accepts True for strict_attrs."""
        m = Mock()
        m.configure(strict_attrs=True)
        self.assertTrue(m.mock_context()._strict_attrs)

    def test_configure_accepts_false_strict_attrs(self):
        """Test that configure accepts False for strict_attrs."""
        m = Mock(strict_attrs=True)
        m.configure(strict_attrs=False)
        self.assertFalse(m.mock_context()._strict_attrs)

    # --- Error message quality tests ---
    def test_error_message_includes_type_name_for_recursive(self):
        """Test that error message includes the actual type name for recursive."""
        with self.assertRaises(TypeError) as context:
            Mock(recursive="string_value")
        error_msg = str(context.exception)
        self.assertIn("str", error_msg)

    def test_error_message_includes_type_name_for_strict_attrs(self):
        """Test that error message includes the actual type name for strict_attrs."""
        with self.assertRaises(TypeError) as context:
            Mock(strict_attrs=123)
        error_msg = str(context.exception)
        self.assertIn("int", error_msg)

    def test_error_message_includes_type_name_for_side_effect(self):
        """Test that error message includes the actual type name for side_effect."""
        with self.assertRaises(TypeError) as context:
            Mock(side_effect={"key": "value"})
        error_msg = str(context.exception)
        self.assertIn("dict", error_msg)

    # --- Combined validation tests ---
    def test_mock_init_validates_all_parameters_together(self):
        """Test that Mock.__init__ validates all parameters correctly when provided together."""
        # Valid combination should work
        m = Mock(return_value=42, recursive=True, strict_attrs=False, side_effect=lambda: 100)
        self.assertEqual(m.mock_context().return_value, 42)
        self.assertTrue(m.mock_context().recursive)
        self.assertFalse(m.mock_context()._strict_attrs)
        self.assertIsNotNone(m.mock_context().side_effect)

    def test_configure_validates_all_parameters_together(self):
        """Test that configure validates all parameters correctly when provided together."""
        m = Mock()
        # Valid combination should work
        m.configure(return_value=100, recursive=True, strict_attrs=True, side_effect=lambda x: x)
        self.assertEqual(m.mock_context().return_value, 100)
        self.assertTrue(m.mock_context().recursive)
        self.assertTrue(m.mock_context()._strict_attrs)
        self.assertIsNotNone(m.mock_context().side_effect)


if __name__ == "__main__":
    unittest.main()


# ============================================================================
# Spec-Based Mocking Tests
# ============================================================================

from ccai.testbase.mocking import SpecMock, SpecViolationError, create_spec_mock


class SpecMockBasicTests(unittest.TestCase):
    """Tests for basic SpecMock functionality."""

    def setUp(self):
        """Set up test fixtures."""
        class SampleSpec:
            """A sample specification class for testing."""
            
            def __init__(self):
                self.name = ""
                self.value = 0
            
            def get_data(self, key: str) -> dict:
                """Get data by key."""
                pass
            
            def process(self, data: dict, validate: bool = True) -> bool:
                """Process data with optional validation."""
                pass
            
            @property
            def status(self) -> str:
                """Get the current status."""
                pass
        
        self.SampleSpec = SampleSpec

    def test_create_spec_mock_with_class(self):
        """Test that create_spec_mock creates a SpecMock from a class."""
        mock = create_spec_mock(self.SampleSpec)
        self.assertIsInstance(mock, SpecMock)
        self.assertEqual(mock.spec, self.SampleSpec)

    def test_create_spec_mock_raises_for_non_class(self):
        """Test that create_spec_mock raises TypeError for non-class spec."""
        with self.assertRaises(TypeError) as context:
            create_spec_mock("not a class")
        self.assertIn("spec must be a class", str(context.exception))

    def test_spec_mock_raises_for_non_class(self):
        """Test that SpecMock raises TypeError for non-class spec."""
        with self.assertRaises(TypeError) as context:
            SpecMock(123)
        self.assertIn("spec must be a class", str(context.exception))

    def test_spec_mock_allows_valid_method_access(self):
        """Test that SpecMock allows access to methods defined in spec."""
        mock = create_spec_mock(self.SampleSpec)
        # Should not raise
        method_mock = mock.get_data
        self.assertIsNotNone(method_mock)

    def test_spec_mock_allows_valid_attribute_access(self):
        """Test that SpecMock allows access to attributes defined in spec."""
        mock = create_spec_mock(self.SampleSpec)
        # Access should create a mock for the attribute
        attr = mock.name
        self.assertIsNotNone(attr)

    def test_spec_mock_raises_for_invalid_attribute(self):
        """Test that SpecMock raises SpecViolationError for undefined attributes."""
        mock = create_spec_mock(self.SampleSpec)
        with self.assertRaises(SpecViolationError) as context:
            _ = mock.nonexistent_attribute
        self.assertIn("has no attribute 'nonexistent_attribute'", str(context.exception))
        self.assertIn("Available attributes", str(context.exception))

    def test_spec_mock_raises_for_invalid_method(self):
        """Test that SpecMock raises SpecViolationError for undefined methods."""
        mock = create_spec_mock(self.SampleSpec)
        with self.assertRaises(SpecViolationError) as context:
            _ = mock.undefined_method
        self.assertIn("has no attribute 'undefined_method'", str(context.exception))

    def test_spec_mock_method_can_be_configured(self):
        """Test that spec mock methods can be configured with return values."""
        mock = create_spec_mock(self.SampleSpec)
        mock.get_data.return_value = {"key": "value"}
        result = mock.get_data("test_key")
        self.assertEqual(result, {"key": "value"})

    def test_spec_mock_method_tracks_calls(self):
        """Test that spec mock methods track calls correctly."""
        mock = create_spec_mock(self.SampleSpec)
        mock.get_data("key1")
        mock.get_data("key2")
        self.assertEqual(mock.get_data.call_count, 2)
        mock.get_data.assert_any_call("key1")
        mock.get_data.assert_any_call("key2")

    def test_spec_mock_same_attribute_returns_same_mock(self):
        """Test that accessing the same attribute returns the same mock."""
        mock = create_spec_mock(self.SampleSpec)
        method1 = mock.get_data
        method2 = mock.get_data
        self.assertIs(method1, method2)


class SpecMockSignatureValidationTests(unittest.TestCase):
    """Tests for SpecMock method signature validation."""

    def setUp(self):
        """Set up test fixtures."""
        class ServiceSpec:
            """A service specification with typed methods."""
            
            def fetch(self, url: str, timeout: int = 30) -> dict:
                """Fetch data from URL."""
                pass
            
            def save(self, data: dict, path: str) -> bool:
                """Save data to path."""
                pass
            
            def no_args(self) -> str:
                """Method with no arguments."""
                pass
        
        self.ServiceSpec = ServiceSpec

    def test_signature_validation_disabled_by_default(self):
        """Test that signature validation is disabled by default."""
        mock = create_spec_mock(self.ServiceSpec)
        # Should not raise even with wrong arguments
        mock.fetch()  # Missing required 'url' argument
        mock.fetch("url", "not_an_int", extra="arg")  # Wrong types and extra args

    def test_signature_validation_enabled_allows_valid_calls(self):
        """Test that valid calls pass when signature validation is enabled."""
        mock = create_spec_mock(self.ServiceSpec, validate_signatures=True)
        # Should not raise
        mock.fetch("http://example.com")
        mock.fetch("http://example.com", timeout=60)
        mock.fetch(url="http://example.com")
        mock.save({"key": "value"}, "/path/to/file")
        mock.no_args()

    def test_signature_validation_raises_for_missing_required_args(self):
        """Test that missing required arguments raise SpecViolationError."""
        mock = create_spec_mock(self.ServiceSpec, validate_signatures=True)
        with self.assertRaises(SpecViolationError) as context:
            mock.fetch()  # Missing required 'url' argument
        self.assertIn("invalid arguments", str(context.exception))
        self.assertIn("fetch", str(context.exception))

    def test_signature_validation_raises_for_extra_positional_args(self):
        """Test that extra positional arguments raise SpecViolationError."""
        mock = create_spec_mock(self.ServiceSpec, validate_signatures=True)
        with self.assertRaises(SpecViolationError) as context:
            mock.fetch("url", 30, "extra_arg")  # Extra positional argument
        self.assertIn("invalid arguments", str(context.exception))

    def test_signature_validation_raises_for_unknown_kwargs(self):
        """Test that unknown keyword arguments raise SpecViolationError."""
        mock = create_spec_mock(self.ServiceSpec, validate_signatures=True)
        with self.assertRaises(SpecViolationError) as context:
            mock.fetch("url", unknown_kwarg="value")
        self.assertIn("invalid arguments", str(context.exception))

    def test_signature_validation_allows_default_args(self):
        """Test that default arguments work correctly with validation."""
        mock = create_spec_mock(self.ServiceSpec, validate_signatures=True)
        # Should not raise - timeout has a default value
        mock.fetch("http://example.com")
        mock.fetch.assert_called_with("http://example.com")


class SpecMockSpecSetTests(unittest.TestCase):
    """Tests for SpecMock spec_set functionality."""

    def setUp(self):
        """Set up test fixtures."""
        class DataSpec:
            """A data specification class."""
            
            def __init__(self):
                self.id = 0
                self.name = ""
            
            def update(self, data: dict) -> bool:
                pass
        
        self.DataSpec = DataSpec

    def test_spec_set_false_allows_new_attributes(self):
        """Test that spec_set=False allows setting new attributes."""
        mock = create_spec_mock(self.DataSpec, spec_set=False)
        # Should not raise
        mock.new_attribute = "value"
        self.assertEqual(mock.new_attribute, "value")

    def test_spec_set_true_raises_for_new_attributes(self):
        """Test that spec_set=True raises for new attributes."""
        mock = create_spec_mock(self.DataSpec, spec_set=True)
        with self.assertRaises(SpecViolationError) as context:
            mock.new_attribute = "value"
        self.assertIn("Cannot set attribute 'new_attribute'", str(context.exception))
        self.assertIn("has no such attribute", str(context.exception))

    def test_spec_set_true_allows_spec_attributes(self):
        """Test that spec_set=True allows setting spec-defined attributes."""
        mock = create_spec_mock(self.DataSpec, spec_set=True)
        # Should not raise - these are defined in the spec
        mock.id = 123
        mock.name = "test"

    def test_spec_set_true_allows_mock_config_attributes(self):
        """Test that spec_set=True allows setting mock configuration attributes."""
        mock = create_spec_mock(self.DataSpec, spec_set=True)
        # Should not raise - these are special mock attributes
        mock.return_value = "test"
        mock.side_effect = lambda: "effect"


class SpecMockDirTests(unittest.TestCase):
    """Tests for SpecMock __dir__ method."""

    def setUp(self):
        """Set up test fixtures."""
        class ApiSpec:
            """An API specification class."""
            
            def get(self, endpoint: str) -> dict:
                pass
            
            def post(self, endpoint: str, data: dict) -> dict:
                pass
            
            @property
            def base_url(self) -> str:
                pass
        
        self.ApiSpec = ApiSpec

    def test_dir_includes_spec_methods(self):
        """Test that dir() includes methods from the spec."""
        mock = create_spec_mock(self.ApiSpec)
        attrs = dir(mock)
        self.assertIn("get", attrs)
        self.assertIn("post", attrs)

    def test_dir_includes_spec_properties(self):
        """Test that dir() includes properties from the spec."""
        mock = create_spec_mock(self.ApiSpec)
        attrs = dir(mock)
        self.assertIn("base_url", attrs)

    def test_dir_includes_set_attributes(self):
        """Test that dir() includes attributes set on the mock."""
        mock = create_spec_mock(self.ApiSpec, spec_set=False)
        mock.custom_attr = "value"
        attrs = dir(mock)
        self.assertIn("custom_attr", attrs)


class SpecMockIntegrationTests(unittest.TestCase):
    """Integration tests for SpecMock with realistic scenarios."""

    def test_mock_database_client(self):
        """Test mocking a database client with spec validation."""
        class DatabaseClient:
            def __init__(self):
                self.connection = None
            
            def connect(self, host: str, port: int, database: str) -> bool:
                pass
            
            def query(self, sql: str, params: tuple = ()) -> list:
                pass
            
            def close(self) -> None:
                pass
        
        mock_db = create_spec_mock(DatabaseClient)
        mock_db.connect.return_value = True
        mock_db.query.return_value = [{"id": 1, "name": "Test"}]
        
        # Simulate usage
        connected = mock_db.connect("localhost", 5432, "testdb")
        self.assertTrue(connected)
        
        results = mock_db.query("SELECT * FROM users")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Test")
        
        mock_db.close()
        
        # Verify calls
        mock_db.connect.assert_called_once_with("localhost", 5432, "testdb")
        mock_db.query.assert_called_once_with("SELECT * FROM users")
        mock_db.close.assert_called_once()

    def test_mock_http_client_with_signature_validation(self):
        """Test mocking an HTTP client with signature validation."""
        class HttpClient:
            def get(self, url: str, headers: dict = None) -> dict:
                pass
            
            def post(self, url: str, data: dict, headers: dict = None) -> dict:
                pass
        
        mock_client = create_spec_mock(HttpClient, validate_signatures=True)
        mock_client.get.return_value = {"status": "ok"}
        mock_client.post.return_value = {"id": 123}
        
        # Valid calls
        response = mock_client.get("http://api.example.com/data")
        self.assertEqual(response["status"], "ok")
        
        response = mock_client.post("http://api.example.com/create", {"name": "test"})
        self.assertEqual(response["id"], 123)
        
        # Invalid call should raise
        with self.assertRaises(SpecViolationError):
            mock_client.post("url")  # Missing required 'data' argument

    def test_spec_mock_with_side_effect(self):
        """Test SpecMock with side effects on methods."""
        class Calculator:
            def add(self, a: int, b: int) -> int:
                pass
            
            def multiply(self, a: int, b: int) -> int:
                pass
        
        mock_calc = create_spec_mock(Calculator)
        mock_calc.add.side_effect = lambda a, b: a + b
        mock_calc.multiply.side_effect = lambda a, b: a * b
        
        self.assertEqual(mock_calc.add(2, 3), 5)
        self.assertEqual(mock_calc.multiply(4, 5), 20)

    def test_spec_mock_assertion_methods(self):
        """Test that assertion methods work correctly on SpecMock."""
        class Service:
            def process(self, item: str) -> bool:
                pass
        
        mock_service = create_spec_mock(Service)
        mock_service.process.return_value = True
        
        # Make some calls
        mock_service.process("item1")
        mock_service.process("item2")
        mock_service.process("item3")
        
        # Test assertions
        mock_service.process.assert_called()
        mock_service.process.assert_any_call("item2")
        mock_service.process.assert_called_with("item3")  # Last call
        
        with self.assertRaises(AssertionError):
            mock_service.process.assert_called_once()  # Called 3 times


class AsyncSideEffectTests(unittest.TestCase):
    """Tests for AsyncSideEffect class."""

    def test_async_side_effect_basic(self):
        """Test basic AsyncSideEffect functionality."""
        async def async_func(x, y):
            return x + y
        
        se = AsyncSideEffect(async_func)
        result = asyncio.run(se(1, 2))
        self.assertEqual(result, 3)

    def test_async_side_effect_with_default_args(self):
        """Test AsyncSideEffect with default arguments."""
        async def async_func(a, b):
            return a * b
        
        se = AsyncSideEffect(async_func, default_args=(5, 10))
        result = asyncio.run(se())
        self.assertEqual(result, 50)
        
        # Override with call-time args
        result = asyncio.run(se(3, 4))
        self.assertEqual(result, 12)

    def test_async_side_effect_with_default_kwargs(self):
        """Test AsyncSideEffect with default keyword arguments."""
        async def async_func(name="World", greeting="Hello"):
            return f"{greeting}, {name}!"
        
        se = AsyncSideEffect(async_func, default_kwargs={"name": "User"})
        result = asyncio.run(se())
        self.assertEqual(result, "Hello, User!")

    def test_async_side_effect_requires_coroutine_function(self):
        """Test that AsyncSideEffect raises TypeError for non-coroutine functions."""
        def sync_func(x):
            return x
        
        with self.assertRaises(TypeError) as context:
            AsyncSideEffect(sync_func)
        self.assertIn("coroutine function", str(context.exception))

    def test_async_side_effect_propagates_exceptions(self):
        """Test that AsyncSideEffect propagates exceptions from the wrapped callable."""
        async def raise_error():
            raise ValueError("Test async error")
        
        se = AsyncSideEffect(raise_error)
        with self.assertRaises(ValueError) as context:
            asyncio.run(se())
        self.assertEqual(str(context.exception), "Test async error")


class AsyncMockTests(unittest.TestCase):
    """Tests for AsyncMock class."""

    def test_async_mock_basic_return_value(self):
        """Test AsyncMock returns configured return_value when awaited."""
        async_mock = AsyncMock(return_value=42)
        result = asyncio.run(async_mock())
        self.assertEqual(result, 42)

    def test_async_mock_with_async_side_effect(self):
        """Test AsyncMock executes async side_effect when awaited."""
        async def async_effect(x):
            return x * 2
        
        async_mock = AsyncMock(side_effect=async_effect)
        result = asyncio.run(async_mock(5))
        self.assertEqual(result, 10)

    def test_async_mock_records_calls(self):
        """Test AsyncMock records call information."""
        async_mock = AsyncMock(return_value="result")
        asyncio.run(async_mock(1, 2, key="value"))
        
        self.assertEqual(async_mock.call_count, 1)
        self.assertEqual(async_mock.call_args, ((1, 2), {"key": "value"}))
        self.assertEqual(async_mock.call_args_list, [((1, 2), {"key": "value"})])

    def test_async_mock_multiple_calls(self):
        """Test AsyncMock tracks multiple calls."""
        async_mock = AsyncMock(return_value="result")
        asyncio.run(async_mock("a"))
        asyncio.run(async_mock("b"))
        asyncio.run(async_mock("c"))
        
        self.assertEqual(async_mock.call_count, 3)
        self.assertEqual(len(async_mock.call_args_list), 3)
        self.assertEqual(async_mock.call_args, (("c",), {}))

    def test_async_mock_assertion_methods(self):
        """Test AsyncMock assertion methods work correctly."""
        async_mock = AsyncMock(return_value="result")
        asyncio.run(async_mock(1, 2))
        
        async_mock.assert_called()
        async_mock.assert_called_once()
        async_mock.assert_called_with(1, 2)
        async_mock.assert_called_once_with(1, 2)

    def test_async_mock_assert_any_call(self):
        """Test AsyncMock assert_any_call works correctly."""
        async_mock = AsyncMock(return_value="result")
        asyncio.run(async_mock("first"))
        asyncio.run(async_mock("second"))
        asyncio.run(async_mock("third"))
        
        async_mock.assert_any_call("second")
        
        with self.assertRaises(AssertionError):
            async_mock.assert_any_call("not_called")

    def test_async_mock_configure(self):
        """Test AsyncMock configure method."""
        async_mock = AsyncMock()
        async_mock.configure(return_value=100)
        
        result = asyncio.run(async_mock())
        self.assertEqual(result, 100)

    def test_async_mock_configure_with_side_effect(self):
        """Test AsyncMock configure with async side_effect."""
        async def new_effect(x):
            return x + 100
        
        async_mock = AsyncMock(return_value=0)
        async_mock.configure(side_effect=new_effect)
        
        result = asyncio.run(async_mock(5))
        self.assertEqual(result, 105)

    def test_async_mock_configure_clear_side_effect(self):
        """Test AsyncMock configure can clear side_effect."""
        async def effect(x):
            return x * 2
        
        async_mock = AsyncMock(side_effect=effect, return_value=42)
        
        # Side effect takes precedence
        result = asyncio.run(async_mock(5))
        self.assertEqual(result, 10)
        
        # Clear side effect
        async_mock.configure(side_effect=None)
        result = asyncio.run(async_mock(5))
        self.assertEqual(result, 42)

    def test_async_mock_recursive(self):
        """Test AsyncMock with recursive=True creates child AsyncMocks."""
        async_mock = AsyncMock(recursive=True)
        child = async_mock.child
        
        self.assertIsInstance(child, AsyncMock)
        
        # Configure child
        child.configure(return_value="child_result")
        result = asyncio.run(async_mock.child())
        self.assertEqual(result, "child_result")

    def test_async_mock_strict_attrs(self):
        """Test AsyncMock with strict_attrs=True."""
        async_mock = AsyncMock(strict_attrs=True)
        
        with self.assertRaises(AttributeError):
            async_mock.undefined_attr = "value"
        
        # return_value should still be configurable
        async_mock.configure(return_value=42)
        result = asyncio.run(async_mock())
        self.assertEqual(result, 42)

    def test_async_mock_raises_for_non_async_side_effect(self):
        """Test AsyncMock raises TypeError for non-async side_effect."""
        def sync_func(x):
            return x
        
        with self.assertRaises(TypeError) as context:
            AsyncMock(side_effect=sync_func)
        self.assertIn("coroutine function", str(context.exception))

    def test_async_mock_accepts_async_side_effect_instance(self):
        """Test AsyncMock accepts AsyncSideEffect instance directly."""
        async def async_func(x):
            return x + 100
        
        se = AsyncSideEffect(async_func)
        async_mock = AsyncMock(side_effect=se)
        
        self.assertIs(async_mock.async_side_effect, se)
        result = asyncio.run(async_mock(5))
        self.assertEqual(result, 105)

    def test_async_mock_directly_awaitable(self):
        """Test AsyncMock can be awaited directly without calling."""
        async_mock = AsyncMock(return_value="direct_await")
        
        async def test_await():
            return await async_mock
        
        result = asyncio.run(test_await())
        self.assertEqual(result, "direct_await")

    def test_async_mock_repr(self):
        """Test AsyncMock __repr__ method."""
        async_mock = AsyncMock(return_value=42)
        repr_str = repr(async_mock)
        
        self.assertIn("AsyncMock", repr_str)
        self.assertIn("return_value=42", repr_str)


class CreateAsyncMockTests(unittest.TestCase):
    """Tests for create_async_mock factory function."""

    def test_create_async_mock_basic(self):
        """Test create_async_mock creates an AsyncMock."""
        async_mock = create_async_mock()
        self.assertIsInstance(async_mock, AsyncMock)

    def test_create_async_mock_with_return_value(self):
        """Test create_async_mock with return_value."""
        async_mock = create_async_mock(return_value={"status": "ok"})
        result = asyncio.run(async_mock())
        self.assertEqual(result, {"status": "ok"})

    def test_create_async_mock_with_side_effect(self):
        """Test create_async_mock with async side_effect."""
        async def fetch_data(url):
            return {"url": url, "data": "response"}
        
        async_mock = create_async_mock(side_effect=fetch_data)
        result = asyncio.run(async_mock("http://example.com"))
        self.assertEqual(result, {"url": "http://example.com", "data": "response"})

    def test_create_async_mock_with_recursive(self):
        """Test create_async_mock with recursive=True."""
        async_mock = create_async_mock(recursive=True)
        child = async_mock.child
        
        self.assertIsInstance(child, AsyncMock)

    def test_create_async_mock_with_strict_attrs(self):
        """Test create_async_mock with strict_attrs=True."""
        async_mock = create_async_mock(strict_attrs=True)
        
        with self.assertRaises(AttributeError):
            async_mock.undefined = "value"


class MockContextAsyncMethodTests(unittest.TestCase):
    """Tests for MockContext.mock_async_method."""

    def test_mock_async_method_basic(self):
        """Test mock_async_method creates an AsyncMock."""
        mock = Mock()
        ctx = mock.mock_context()
        
        ctx.mock_async_method('fetch_data', return_value={'id': 1})
        
        self.assertIsInstance(mock.fetch_data, AsyncMock)
        result = asyncio.run(mock.fetch_data())
        self.assertEqual(result, {'id': 1})

    def test_mock_async_method_with_side_effect(self):
        """Test mock_async_method with async side_effect."""
        async def async_process(x):
            return x * 2
        
        mock = Mock()
        ctx = mock.mock_context()
        
        ctx.mock_async_method('process', side_effect=async_process)
        
        result = asyncio.run(mock.process(5))
        self.assertEqual(result, 10)

    def test_mock_async_method_tracks_calls(self):
        """Test mock_async_method tracks calls correctly."""
        mock = Mock()
        ctx = mock.mock_context()
        
        ctx.mock_async_method('fetch', return_value='data')
        
        asyncio.run(mock.fetch('arg1'))
        asyncio.run(mock.fetch('arg2'))
        
        self.assertEqual(mock.fetch.call_count, 2)
        mock.fetch.assert_any_call('arg1')
        mock.fetch.assert_called_with('arg2')

    def test_mock_async_method_inherits_settings(self):
        """Test mock_async_method inherits recursive and strict_attrs settings."""
        mock = Mock(recursive=True, strict_attrs=False)
        ctx = mock.mock_context()
        
        async_method = ctx.mock_async_method('async_op', return_value='result')
        
        # The async method should inherit recursive setting
        self.assertTrue(async_method._mock_context.recursive)


class PropertyMockTests(unittest.TestCase):
    """Tests for PropertyMock class - property getter and setter mocking."""

    # --- Basic getter tests ---
    def test_property_mock_getter_returns_configured_value(self):
        """Test that PropertyMock getter returns the configured return value."""
        prop = PropertyMock(getter_return_value="test_value")
        result = prop.get()
        self.assertEqual(result, "test_value")

    def test_property_mock_getter_with_side_effect(self):
        """Test that PropertyMock getter executes side effect."""
        counter = [0]
        def increment():
            counter[0] += 1
            return counter[0]
        
        prop = PropertyMock(getter_side_effect=increment)
        
        self.assertEqual(prop.get(), 1)
        self.assertEqual(prop.get(), 2)
        self.assertEqual(prop.get(), 3)

    def test_property_mock_getter_side_effect_overrides_return_value(self):
        """Test that getter side effect takes precedence over return value."""
        prop = PropertyMock(
            getter_return_value="ignored",
            getter_side_effect=lambda: "from_side_effect"
        )
        result = prop.get()
        self.assertEqual(result, "from_side_effect")

    def test_property_mock_getter_tracks_call_count(self):
        """Test that PropertyMock tracks getter call count."""
        prop = PropertyMock(getter_return_value="value")
        
        self.assertEqual(prop.getter_call_count, 0)
        
        prop.get()
        self.assertEqual(prop.getter_call_count, 1)
        
        prop.get()
        prop.get()
        self.assertEqual(prop.getter_call_count, 3)

    def test_property_mock_getter_tracks_call_args_list(self):
        """Test that PropertyMock tracks getter call arguments."""
        prop = PropertyMock(getter_return_value="value")
        
        prop.get()
        prop.get()
        
        self.assertEqual(len(prop.getter_call_args_list), 2)
        self.assertEqual(prop.getter_call_args_list[0], ((), {}))
        self.assertEqual(prop.getter_call_args_list[1], ((), {}))

    # --- Basic setter tests ---
    def test_property_mock_setter_tracks_call_count(self):
        """Test that PropertyMock tracks setter call count."""
        prop = PropertyMock()
        
        self.assertEqual(prop.setter_call_count, 0)
        
        prop.set("value1")
        self.assertEqual(prop.setter_call_count, 1)
        
        prop.set("value2")
        prop.set("value3")
        self.assertEqual(prop.setter_call_count, 3)

    def test_property_mock_setter_tracks_call_args(self):
        """Test that PropertyMock tracks setter call arguments."""
        prop = PropertyMock()
        
        prop.set("first_value")
        self.assertEqual(prop.setter_call_args, (("first_value",), {}))
        
        prop.set("second_value")
        self.assertEqual(prop.setter_call_args, (("second_value",), {}))

    def test_property_mock_setter_tracks_call_args_list(self):
        """Test that PropertyMock tracks all setter calls."""
        prop = PropertyMock()
        
        prop.set("value1")
        prop.set("value2")
        prop.set("value3")
        
        self.assertEqual(len(prop.setter_call_args_list), 3)
        self.assertEqual(prop.setter_call_args_list[0], (("value1",), {}))
        self.assertEqual(prop.setter_call_args_list[1], (("value2",), {}))
        self.assertEqual(prop.setter_call_args_list[2], (("value3",), {}))

    def test_property_mock_setter_executes_side_effect(self):
        """Test that PropertyMock setter executes side effect."""
        received_values = []
        def on_set(value):
            received_values.append(value)
        
        prop = PropertyMock(setter_side_effect=on_set)
        
        prop.set("first")
        prop.set("second")
        
        self.assertEqual(received_values, ["first", "second"])

    def test_property_mock_setter_side_effect_can_raise(self):
        """Test that setter side effect can raise exceptions."""
        def validate(value):
            if not isinstance(value, int):
                raise ValueError("Must be an integer")
        
        prop = PropertyMock(setter_side_effect=validate)
        
        # Should not raise
        prop.set(42)
        
        # Should raise
        with self.assertRaises(ValueError) as context:
            prop.set("not an int")
        self.assertIn("Must be an integer", str(context.exception))

    # --- Getter assertion tests ---
    def test_assert_getter_called_passes_when_called(self):
        """Test assert_getter_called passes when getter was accessed."""
        prop = PropertyMock(getter_return_value="value")
        prop.get()
        # Should not raise
        prop.assert_getter_called()

    def test_assert_getter_called_raises_when_not_called(self):
        """Test assert_getter_called raises when getter was not accessed."""
        prop = PropertyMock(getter_return_value="value")
        with self.assertRaises(AssertionError) as context:
            prop.assert_getter_called()
        self.assertIn("Expected property getter to have been accessed", str(context.exception))

    def test_assert_getter_called_once_passes_when_called_once(self):
        """Test assert_getter_called_once passes when getter was accessed once."""
        prop = PropertyMock(getter_return_value="value")
        prop.get()
        # Should not raise
        prop.assert_getter_called_once()

    def test_assert_getter_called_once_raises_when_not_called(self):
        """Test assert_getter_called_once raises when getter was not accessed."""
        prop = PropertyMock(getter_return_value="value")
        with self.assertRaises(AssertionError) as context:
            prop.assert_getter_called_once()
        self.assertIn("Accessed 0 times", str(context.exception))

    def test_assert_getter_called_once_raises_when_called_multiple_times(self):
        """Test assert_getter_called_once raises when getter was accessed multiple times."""
        prop = PropertyMock(getter_return_value="value")
        prop.get()
        prop.get()
        with self.assertRaises(AssertionError) as context:
            prop.assert_getter_called_once()
        self.assertIn("Accessed 2 times", str(context.exception))

    # --- Setter assertion tests ---
    def test_assert_setter_called_passes_when_called(self):
        """Test assert_setter_called passes when setter was called."""
        prop = PropertyMock()
        prop.set("value")
        # Should not raise
        prop.assert_setter_called()

    def test_assert_setter_called_raises_when_not_called(self):
        """Test assert_setter_called raises when setter was not called."""
        prop = PropertyMock()
        with self.assertRaises(AssertionError) as context:
            prop.assert_setter_called()
        self.assertIn("Expected property setter to have been called", str(context.exception))

    def test_assert_setter_called_once_passes_when_called_once(self):
        """Test assert_setter_called_once passes when setter was called once."""
        prop = PropertyMock()
        prop.set("value")
        # Should not raise
        prop.assert_setter_called_once()

    def test_assert_setter_called_once_raises_when_not_called(self):
        """Test assert_setter_called_once raises when setter was not called."""
        prop = PropertyMock()
        with self.assertRaises(AssertionError) as context:
            prop.assert_setter_called_once()
        self.assertIn("Called 0 times", str(context.exception))

    def test_assert_setter_called_once_raises_when_called_multiple_times(self):
        """Test assert_setter_called_once raises when setter was called multiple times."""
        prop = PropertyMock()
        prop.set("value1")
        prop.set("value2")
        with self.assertRaises(AssertionError) as context:
            prop.assert_setter_called_once()
        self.assertIn("Called 2 times", str(context.exception))

    def test_assert_setter_called_with_passes_with_matching_value(self):
        """Test assert_setter_called_with passes when last call matches."""
        prop = PropertyMock()
        prop.set("expected_value")
        # Should not raise
        prop.assert_setter_called_with("expected_value")

    def test_assert_setter_called_with_raises_with_non_matching_value(self):
        """Test assert_setter_called_with raises when last call doesn't match."""
        prop = PropertyMock()
        prop.set("actual_value")
        with self.assertRaises(AssertionError) as context:
            prop.assert_setter_called_with("expected_value")
        self.assertIn("Expected setter call with", str(context.exception))
        self.assertIn("Actual last call", str(context.exception))

    def test_assert_setter_called_with_raises_when_not_called(self):
        """Test assert_setter_called_with raises when setter was not called."""
        prop = PropertyMock()
        with self.assertRaises(AssertionError) as context:
            prop.assert_setter_called_with("value")
        self.assertIn("but it was not called", str(context.exception))

    def test_assert_setter_called_once_with_passes(self):
        """Test assert_setter_called_once_with passes when called once with matching value."""
        prop = PropertyMock()
        prop.set("expected_value")
        # Should not raise
        prop.assert_setter_called_once_with("expected_value")

    def test_assert_setter_called_once_with_raises_when_called_multiple_times(self):
        """Test assert_setter_called_once_with raises when called multiple times."""
        prop = PropertyMock()
        prop.set("value1")
        prop.set("value2")
        with self.assertRaises(AssertionError) as context:
            prop.assert_setter_called_once_with("value2")
        self.assertIn("Called 2 times", str(context.exception))

    def test_assert_setter_any_call_passes_when_call_exists(self):
        """Test assert_setter_any_call passes when the call exists in history."""
        prop = PropertyMock()
        prop.set("first")
        prop.set("second")
        prop.set("third")
        # Should not raise
        prop.assert_setter_any_call("second")

    def test_assert_setter_any_call_raises_when_call_not_found(self):
        """Test assert_setter_any_call raises when the call doesn't exist."""
        prop = PropertyMock()
        prop.set("first")
        prop.set("second")
        with self.assertRaises(AssertionError) as context:
            prop.assert_setter_any_call("third")
        self.assertIn("Expected at least one setter call with", str(context.exception))

    # --- Configuration tests ---
    def test_configure_getter_updates_return_value(self):
        """Test configure_getter updates the return value."""
        prop = PropertyMock(getter_return_value="initial")
        self.assertEqual(prop.get(), "initial")
        
        prop.configure_getter(return_value="updated")
        self.assertEqual(prop.get(), "updated")

    def test_configure_getter_updates_side_effect(self):
        """Test configure_getter updates the side effect."""
        prop = PropertyMock(getter_return_value="initial")
        
        prop.configure_getter(side_effect=lambda: "from_side_effect")
        self.assertEqual(prop.get(), "from_side_effect")

    def test_configure_getter_returns_self_for_chaining(self):
        """Test configure_getter returns self for fluent chaining."""
        prop = PropertyMock()
        result = prop.configure_getter(return_value="value")
        self.assertIs(result, prop)

    def test_configure_setter_updates_side_effect(self):
        """Test configure_setter updates the side effect."""
        received = []
        prop = PropertyMock()
        
        prop.configure_setter(side_effect=lambda v: received.append(v))
        prop.set("test")
        
        self.assertEqual(received, ["test"])

    def test_configure_setter_returns_self_for_chaining(self):
        """Test configure_setter returns self for fluent chaining."""
        prop = PropertyMock()
        result = prop.configure_setter(side_effect=lambda v: None)
        self.assertIs(result, prop)

    def test_fluent_configuration(self):
        """Test fluent configuration of both getter and setter."""
        received = []
        prop = PropertyMock()
        
        prop.configure_getter(return_value="getter_value").configure_setter(
            side_effect=lambda v: received.append(v)
        )
        
        self.assertEqual(prop.get(), "getter_value")
        prop.set("setter_value")
        self.assertEqual(received, ["setter_value"])

    # --- Reset tests ---
    def test_reset_clears_getter_tracking(self):
        """Test reset clears getter tracking."""
        prop = PropertyMock(getter_return_value="value")
        prop.get()
        prop.get()
        
        self.assertEqual(prop.getter_call_count, 2)
        
        prop.reset()
        
        self.assertEqual(prop.getter_call_count, 0)
        self.assertEqual(prop.getter_call_args_list, [])

    def test_reset_clears_setter_tracking(self):
        """Test reset clears setter tracking."""
        prop = PropertyMock()
        prop.set("value1")
        prop.set("value2")
        
        self.assertEqual(prop.setter_call_count, 2)
        
        prop.reset()
        
        self.assertEqual(prop.setter_call_count, 0)
        self.assertIsNone(prop.setter_call_args)
        self.assertEqual(prop.setter_call_args_list, [])

    def test_reset_allows_reuse(self):
        """Test that PropertyMock can be reused after reset."""
        prop = PropertyMock(getter_return_value="initial")
        
        prop.get()
        prop.set("value")
        
        prop.reset()
        
        # Should work after reset
        prop.get()
        prop.assert_getter_called_once()
        
        prop.set("new_value")
        prop.assert_setter_called_once_with("new_value")

    # --- Callable behavior tests ---
    def test_calling_property_mock_acts_as_getter(self):
        """Test that calling PropertyMock directly acts as getter."""
        prop = PropertyMock(getter_return_value="value")
        result = prop()
        self.assertEqual(result, "value")
        self.assertEqual(prop.getter_call_count, 1)

    # --- Type error tests ---
    def test_invalid_getter_side_effect_raises_type_error(self):
        """Test that invalid getter_side_effect raises TypeError."""
        with self.assertRaises(TypeError) as context:
            PropertyMock(getter_side_effect="not_callable")
        self.assertIn("side_effect must be a SideEffect instance or a callable", str(context.exception))

    def test_invalid_setter_side_effect_raises_type_error(self):
        """Test that invalid setter_side_effect raises TypeError."""
        with self.assertRaises(TypeError) as context:
            PropertyMock(setter_side_effect="not_callable")
        self.assertIn("setter_side_effect must be a SideEffect instance or a callable", str(context.exception))

    def test_configure_getter_invalid_side_effect_raises_type_error(self):
        """Test that configure_getter with invalid side_effect raises TypeError."""
        prop = PropertyMock()
        with self.assertRaises(TypeError) as context:
            prop.configure_getter(side_effect="not_callable")
        self.assertIn("getter side_effect must be a SideEffect instance or a callable", str(context.exception))

    def test_configure_setter_invalid_side_effect_raises_type_error(self):
        """Test that configure_setter with invalid side_effect raises TypeError."""
        prop = PropertyMock()
        with self.assertRaises(TypeError) as context:
            prop.configure_setter(side_effect="not_callable")
        self.assertIn("setter side_effect must be a SideEffect instance or a callable", str(context.exception))

    # --- Repr test ---
    def test_repr(self):
        """Test PropertyMock __repr__ method."""
        prop = PropertyMock(getter_return_value="test")
        repr_str = repr(prop)
        self.assertIn("PropertyMock", repr_str)
        self.assertIn("getter_return_value", repr_str)
        self.assertIn("'test'", repr_str)


class PropertyMockFactoryTests(unittest.TestCase):
    """Tests for create_property_mock factory function."""

    def test_create_property_mock_basic(self):
        """Test create_property_mock creates a PropertyMock."""
        prop = create_property_mock(getter_return_value="value")
        self.assertIsInstance(prop, PropertyMock)
        self.assertEqual(prop.get(), "value")

    def test_create_property_mock_with_getter_side_effect(self):
        """Test create_property_mock with getter_side_effect."""
        prop = create_property_mock(getter_side_effect=lambda: "dynamic")
        self.assertEqual(prop.get(), "dynamic")

    def test_create_property_mock_with_setter_side_effect(self):
        """Test create_property_mock with setter_side_effect."""
        received = []
        prop = create_property_mock(setter_side_effect=lambda v: received.append(v))
        prop.set("test")
        self.assertEqual(received, ["test"])

    def test_create_property_mock_with_all_options(self):
        """Test create_property_mock with all options."""
        received = []
        prop = create_property_mock(
            getter_return_value="getter_value",
            getter_side_effect=lambda: "side_effect_value",
            setter_side_effect=lambda v: received.append(v)
        )
        
        # Side effect takes precedence
        self.assertEqual(prop.get(), "side_effect_value")
        
        prop.set("setter_value")
        self.assertEqual(received, ["setter_value"])


class MockContextPropertyMockTests(unittest.TestCase):
    """Tests for MockContext.mock_property with PropertyMock."""

    def test_mock_property_creates_property_mock(self):
        """Test mock_property creates a PropertyMock."""
        mock = Mock()
        ctx = mock.mock_context()
        
        ctx.mock_property('name', return_value='test_name')
        
        self.assertIsInstance(mock.name, PropertyMock)

    def test_mock_property_getter_works(self):
        """Test mock_property getter returns configured value."""
        mock = Mock()
        ctx = mock.mock_context()
        
        ctx.mock_property('status', return_value='active')
        
        self.assertEqual(mock.status.get(), 'active')

    def test_mock_property_setter_works(self):
        """Test mock_property setter tracks calls."""
        mock = Mock()
        ctx = mock.mock_context()
        
        received = []
        ctx.mock_property('value', setter_side_effect=lambda v: received.append(v))
        
        mock.value.set('new_value')
        
        self.assertEqual(received, ['new_value'])
        mock.value.assert_setter_called_with('new_value')

    def test_mock_property_with_getter_side_effect(self):
        """Test mock_property with getter side effect."""
        mock = Mock()
        ctx = mock.mock_context()
        
        counter = [0]
        def increment():
            counter[0] += 1
            return counter[0]
        
        ctx.mock_property('count', side_effect=increment)
        
        self.assertEqual(mock.count.get(), 1)
        self.assertEqual(mock.count.get(), 2)

    def test_mock_property_with_both_getter_and_setter(self):
        """Test mock_property with both getter and setter configuration."""
        mock = Mock()
        ctx = mock.mock_context()
        
        received = []
        ctx.mock_property(
            'data',
            return_value='initial',
            setter_side_effect=lambda v: received.append(v)
        )
        
        self.assertEqual(mock.data.get(), 'initial')
        mock.data.set('updated')
        self.assertEqual(received, ['updated'])
        
        mock.data.assert_getter_called_once()
        mock.data.assert_setter_called_once_with('updated')


class CallOrderVerificationTests(unittest.TestCase):
    """Tests for MockContext.assert_calls_in_order method (call ordering verification)."""

    def test_assert_calls_in_order_passes_with_exact_order(self):
        """Test assert_calls_in_order passes when calls are in exact order."""
        m = Mock()
        m("first")
        m("second")
        m("third")
        
        # Should not raise - calls are in exact order
        m.mock_context().assert_calls_in_order([
            (("first",), {}),
            (("second",), {}),
            (("third",), {})
        ])

    def test_assert_calls_in_order_passes_with_non_contiguous_calls(self):
        """Test assert_calls_in_order passes when expected calls are not contiguous."""
        m = Mock()
        m("first")
        m("middle1")
        m("second")
        m("middle2")
        m("third")
        
        # Should not raise - expected calls are in order, even with other calls between
        m.mock_context().assert_calls_in_order([
            (("first",), {}),
            (("second",), {}),
            (("third",), {})
        ])

    def test_assert_calls_in_order_passes_with_partial_order(self):
        """Test assert_calls_in_order supports partial order verification."""
        m = Mock()
        m("a")
        m("b")
        m("c")
        m("d")
        m("e")
        
        # Should not raise - only checking that "a" comes before "c" which comes before "e"
        m.mock_context().assert_calls_in_order([
            (("a",), {}),
            (("c",), {}),
            (("e",), {})
        ])

    def test_assert_calls_in_order_raises_when_order_violated(self):
        """Test assert_calls_in_order raises AssertionError when order is violated."""
        m = Mock()
        m("first")
        m("third")
        m("second")
        
        with self.assertRaises(AssertionError) as context:
            # Should fail - "second" comes after "third" in actual calls
            m.mock_context().assert_calls_in_order([
                (("first",), {}),
                (("second",), {}),
                (("third",), {})
            ])
        
        error_msg = str(context.exception)
        self.assertIn("Call order verification failed", error_msg)
        self.assertIn("not found", error_msg)

    def test_assert_calls_in_order_raises_when_call_missing(self):
        """Test assert_calls_in_order raises AssertionError when expected call is missing."""
        m = Mock()
        m("first")
        m("third")
        
        with self.assertRaises(AssertionError) as context:
            m.mock_context().assert_calls_in_order([
                (("first",), {}),
                (("second",), {}),  # This call never happened
                (("third",), {})
            ])
        
        error_msg = str(context.exception)
        self.assertIn("Call order verification failed", error_msg)
        self.assertIn("not found", error_msg)

    def test_assert_calls_in_order_raises_when_no_calls_made(self):
        """Test assert_calls_in_order raises AssertionError when no calls were made."""
        m = Mock()
        
        with self.assertRaises(AssertionError) as context:
            m.mock_context().assert_calls_in_order([
                (("first",), {})
            ])
        
        error_msg = str(context.exception)
        self.assertIn("Call order verification failed", error_msg)
        self.assertIn("no calls made", error_msg)

    def test_assert_calls_in_order_passes_with_empty_list(self):
        """Test assert_calls_in_order passes with empty list."""
        m = Mock()
        m("something")
        
        # Should not raise - empty list always passes
        m.mock_context().assert_calls_in_order([])

    def test_assert_calls_in_order_with_kwargs(self):
        """Test assert_calls_in_order works with keyword arguments."""
        m = Mock()
        m(a=1)
        m(b=2)
        m(c=3)
        
        # Should not raise
        m.mock_context().assert_calls_in_order([
            ((), {"a": 1}),
            ((), {"c": 3})
        ])

    def test_assert_calls_in_order_with_mixed_args_and_kwargs(self):
        """Test assert_calls_in_order works with mixed positional and keyword arguments."""
        m = Mock()
        m(1, key="value1")
        m(2, key="value2")
        m(3, key="value3")
        
        # Should not raise
        m.mock_context().assert_calls_in_order([
            ((1,), {"key": "value1"}),
            ((3,), {"key": "value3"})
        ])

    def test_assert_calls_in_order_raises_type_error_for_non_list(self):
        """Test assert_calls_in_order raises TypeError for non-list input."""
        m = Mock()
        m("test")
        
        with self.assertRaises(TypeError) as context:
            m.mock_context().assert_calls_in_order("not a list")
        
        self.assertIn("list", str(context.exception))

    def test_assert_calls_in_order_raises_value_error_for_invalid_call_format(self):
        """Test assert_calls_in_order raises ValueError for invalid call format."""
        m = Mock()
        m("test")
        
        with self.assertRaises(ValueError) as context:
            m.mock_context().assert_calls_in_order([
                ("invalid", "format")  # Should be ((args,), {kwargs})
            ])
        
        self.assertIn("tuple of (args_tuple, kwargs_dict)", str(context.exception))

    def test_assert_calls_in_order_error_message_shows_positions(self):
        """Test that error message shows positions of found calls."""
        m = Mock()
        m("first")
        m("second")
        m("wrong")
        
        with self.assertRaises(AssertionError) as context:
            m.mock_context().assert_calls_in_order([
                (("first",), {}),
                (("second",), {}),
                (("third",), {})  # Not found
            ])
        
        error_msg = str(context.exception)
        # Should show positions of found calls
        self.assertIn("position", error_msg.lower())

    def test_assert_calls_in_order_error_message_shows_expected_order(self):
        """Test that error message shows expected call order."""
        m = Mock()
        m("a")
        m("c")
        m("b")
        
        with self.assertRaises(AssertionError) as context:
            m.mock_context().assert_calls_in_order([
                (("a",), {}),
                (("b",), {}),
                (("c",), {})
            ])
        
        error_msg = str(context.exception)
        # Should show expected call order
        self.assertIn("Expected call order", error_msg)

    def test_assert_calls_in_order_error_message_shows_actual_calls(self):
        """Test that error message shows actual call history."""
        m = Mock()
        m("actual1")
        m("actual2")
        
        with self.assertRaises(AssertionError) as context:
            m.mock_context().assert_calls_in_order([
                (("expected",), {})
            ])
        
        error_msg = str(context.exception)
        # Should show actual calls
        self.assertIn("Actual calls", error_msg)
        self.assertIn("actual1", error_msg)
        self.assertIn("actual2", error_msg)

    def test_assert_calls_in_order_with_duplicate_calls(self):
        """Test assert_calls_in_order handles duplicate calls correctly."""
        m = Mock()
        m("repeat")
        m("other")
        m("repeat")
        m("another")
        m("repeat")
        
        # Should pass - finds first "repeat", then second "repeat" after it
        m.mock_context().assert_calls_in_order([
            (("repeat",), {}),
            (("repeat",), {})
        ])

    def test_assert_calls_in_order_with_three_duplicate_calls(self):
        """Test assert_calls_in_order with three duplicate calls in order."""
        m = Mock()
        m("x")
        m("y")
        m("x")
        m("z")
        m("x")
        
        # Should pass - finds three "x" calls in order
        m.mock_context().assert_calls_in_order([
            (("x",), {}),
            (("x",), {}),
            (("x",), {})
        ])

    def test_assert_calls_in_order_fails_when_not_enough_duplicates(self):
        """Test assert_calls_in_order fails when not enough duplicate calls exist."""
        m = Mock()
        m("x")
        m("y")
        m("x")
        
        with self.assertRaises(AssertionError):
            # Should fail - only 2 "x" calls, but expecting 3
            m.mock_context().assert_calls_in_order([
                (("x",), {}),
                (("x",), {}),
                (("x",), {})
            ])

    def test_assert_calls_in_order_single_call(self):
        """Test assert_calls_in_order with single expected call."""
        m = Mock()
        m("first")
        m("second")
        m("third")
        
        # Should pass - "second" exists in call history
        m.mock_context().assert_calls_in_order([
            (("second",), {})
        ])

    def test_assert_calls_in_order_accessible_from_mock(self):
        """Test that assert_calls_in_order is accessible from Mock object."""
        m = Mock()
        m("first")
        m("second")
        
        # Should be accessible via mock.assert_calls_in_order
        m.assert_calls_in_order([
            (("first",), {}),
            (("second",), {})
        ])


# =============================================================================
# AUTOMATIC MOCK CLEANUP TESTS
# =============================================================================


class MockRegistryTests(unittest.TestCase):
    """Tests for MockRegistry class - automatic mock cleanup functionality."""

    def setUp(self):
        """Clear the registry before each test."""
        registry = get_mock_registry()
        registry.clear()

    def tearDown(self):
        """Clean up after each test."""
        cleanup_all_mocks()

    def test_get_instance_returns_singleton(self):
        """Test that get_instance returns the same instance."""
        registry1 = MockRegistry.get_instance()
        registry2 = MockRegistry.get_instance()
        self.assertIs(registry1, registry2)

    def test_register_mock_adds_to_registry(self):
        """Test that register_mock adds a mock to the registry."""
        registry = get_mock_registry()
        mock = Mock()
        
        self.assertEqual(registry.get_registered_mock_count(), 0)
        registry.register_mock(mock)
        self.assertEqual(registry.get_registered_mock_count(), 1)

    def test_register_mock_returns_same_mock(self):
        """Test that register_mock returns the same mock for fluent chaining."""
        registry = get_mock_registry()
        mock = Mock()
        
        result = registry.register_mock(mock)
        self.assertIs(result, mock)

    def test_register_mock_does_not_duplicate(self):
        """Test that registering the same mock twice doesn't duplicate it."""
        registry = get_mock_registry()
        mock = Mock()
        
        registry.register_mock(mock)
        registry.register_mock(mock)
        self.assertEqual(registry.get_registered_mock_count(), 1)

    def test_register_patch_adds_to_registry(self):
        """Test that register_patch adds a patch to the registry."""
        registry = get_mock_registry()
        patch = create_module_patch(os.path, 'exists')
        
        self.assertEqual(registry.get_registered_patch_count(), 0)
        registry.register_patch(patch)
        self.assertEqual(registry.get_registered_patch_count(), 1)

    def test_register_patch_returns_same_patch(self):
        """Test that register_patch returns the same patch for fluent chaining."""
        registry = get_mock_registry()
        patch = create_module_patch(os.path, 'exists')
        
        result = registry.register_patch(patch)
        self.assertIs(result, patch)

    def test_unregister_mock_removes_from_registry(self):
        """Test that unregister_mock removes a mock from the registry."""
        registry = get_mock_registry()
        mock = Mock()
        
        registry.register_mock(mock)
        self.assertEqual(registry.get_registered_mock_count(), 1)
        
        registry.unregister_mock(mock)
        self.assertEqual(registry.get_registered_mock_count(), 0)

    def test_unregister_patch_removes_from_registry(self):
        """Test that unregister_patch removes a patch from the registry."""
        registry = get_mock_registry()
        patch = create_module_patch(os.path, 'exists')
        
        registry.register_patch(patch)
        self.assertEqual(registry.get_registered_patch_count(), 1)
        
        registry.unregister_patch(patch)
        self.assertEqual(registry.get_registered_patch_count(), 0)

    def test_cleanup_all_resets_mocks(self):
        """Test that cleanup_all resets all registered mocks."""
        registry = get_mock_registry()
        mock = Mock(return_value=42)
        registry.register_mock(mock)
        
        # Call the mock to record some state
        mock(1, 2, key="value")
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(mock.mock_context().return_value, 42)
        
        # Cleanup should reset the mock
        registry.cleanup_all()
        
        self.assertEqual(mock.call_count, 0)
        self.assertIsNone(mock.mock_context().return_value)
        self.assertEqual(registry.get_registered_mock_count(), 0)

    def test_cleanup_all_deactivates_patches(self):
        """Test that cleanup_all deactivates all registered patches."""
        registry = get_mock_registry()
        original_exists = os.path.exists
        
        patch = create_module_patch(os.path, 'exists')
        registry.register_patch(patch)
        mock = patch.activate()
        mock.return_value = True
        
        # Verify patch is active
        self.assertTrue(os.path.exists('/nonexistent'))
        
        # Cleanup should deactivate the patch
        registry.cleanup_all()
        
        # Verify original is restored
        self.assertIs(os.path.exists, original_exists)
        self.assertEqual(registry.get_registered_patch_count(), 0)

    def test_cleanup_all_with_reset_mocks_false(self):
        """Test cleanup_all with reset_mocks=False only deactivates patches."""
        registry = get_mock_registry()
        mock = Mock(return_value=42)
        registry.register_mock(mock)
        mock(1, 2)
        
        patch = create_module_patch(os.path, 'exists')
        registry.register_patch(patch)
        patch.activate()
        
        # Cleanup with reset_mocks=False
        registry.cleanup_all(reset_mocks=False)
        
        # Mock should still have its state
        self.assertEqual(mock.call_count, 1)
        # Patch should be deactivated
        self.assertEqual(registry.get_registered_patch_count(), 0)
        # Mock should still be registered (not cleared)
        self.assertEqual(registry.get_registered_mock_count(), 1)

    def test_cleanup_all_with_deactivate_patches_false(self):
        """Test cleanup_all with deactivate_patches=False only resets mocks."""
        registry = get_mock_registry()
        mock = Mock(return_value=42)
        registry.register_mock(mock)
        mock(1, 2)
        
        patch = create_module_patch(os.path, 'exists')
        registry.register_patch(patch)
        patch.activate()
        
        # Cleanup with deactivate_patches=False
        registry.cleanup_all(deactivate_patches=False)
        
        # Mock should be reset
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(registry.get_registered_mock_count(), 0)
        # Patch should still be registered
        self.assertEqual(registry.get_registered_patch_count(), 1)
        
        # Clean up the patch manually
        patch.deactivate()

    def test_clear_removes_all_without_cleanup(self):
        """Test that clear removes all items without cleaning them up."""
        registry = get_mock_registry()
        mock = Mock(return_value=42)
        registry.register_mock(mock)
        mock(1, 2)
        
        # Clear without cleanup
        registry.clear()
        
        # Registry should be empty
        self.assertEqual(registry.get_registered_mock_count(), 0)
        # But mock should still have its state
        self.assertEqual(mock.call_count, 1)


class ConvenienceFunctionTests(unittest.TestCase):
    """Tests for convenience functions for automatic mock cleanup."""

    def setUp(self):
        """Clear the registry before each test."""
        get_mock_registry().clear()

    def tearDown(self):
        """Clean up after each test."""
        cleanup_all_mocks()

    def test_get_mock_registry_returns_singleton(self):
        """Test that get_mock_registry returns the singleton instance."""
        registry1 = get_mock_registry()
        registry2 = get_mock_registry()
        self.assertIs(registry1, registry2)

    def test_register_mock_function(self):
        """Test the register_mock convenience function."""
        mock = Mock()
        result = register_mock(mock)
        
        self.assertIs(result, mock)
        self.assertEqual(get_mock_registry().get_registered_mock_count(), 1)

    def test_register_patch_function(self):
        """Test the register_patch convenience function."""
        patch = create_module_patch(os.path, 'exists')
        result = register_patch(patch)
        
        self.assertIs(result, patch)
        self.assertEqual(get_mock_registry().get_registered_patch_count(), 1)

    def test_cleanup_all_mocks_function(self):
        """Test the cleanup_all_mocks convenience function."""
        mock = Mock(return_value=42)
        register_mock(mock)
        mock(1, 2)
        
        patch = create_module_patch(os.path, 'exists')
        register_patch(patch)
        patch.activate()
        
        # Cleanup using convenience function
        cleanup_all_mocks()
        
        # Verify cleanup
        self.assertEqual(mock.call_count, 0)
        self.assertEqual(get_mock_registry().get_registered_mock_count(), 0)
        self.assertEqual(get_mock_registry().get_registered_patch_count(), 0)


class TrackedMockCreationTests(unittest.TestCase):
    """Tests for tracked mock creation functions."""

    def setUp(self):
        """Clear the registry before each test."""
        get_mock_registry().clear()

    def tearDown(self):
        """Clean up after each test."""
        cleanup_all_mocks()

    def test_create_tracked_mock(self):
        """Test create_tracked_mock creates and registers a mock."""
        mock = create_tracked_mock(return_value=42, recursive=True)
        
        self.assertIsInstance(mock, Mock)
        self.assertEqual(mock.mock_context().return_value, 42)
        self.assertTrue(mock.mock_context().recursive)
        self.assertEqual(get_mock_registry().get_registered_mock_count(), 1)

    def test_create_tracked_module_patch(self):
        """Test create_tracked_module_patch creates and registers a patch."""
        original_exists = os.path.exists
        
        patch = create_tracked_module_patch(os.path, 'exists')
        mock = patch.activate()
        mock.return_value = True
        
        self.assertIsInstance(patch, Patch)
        self.assertEqual(get_mock_registry().get_registered_patch_count(), 1)
        self.assertTrue(os.path.exists('/nonexistent'))
        
        # Cleanup
        cleanup_all_mocks()
        self.assertIs(os.path.exists, original_exists)

    def test_create_tracked_class_patch(self):
        """Test create_tracked_class_patch creates and registers a patch."""
        class TestClass:
            attr = "original"
        
        original_attr = TestClass.attr
        
        patch = create_tracked_class_patch(TestClass, 'attr')
        mock = patch.activate()
        mock.return_value = "mocked"
        
        self.assertIsInstance(patch, Patch)
        self.assertEqual(get_mock_registry().get_registered_patch_count(), 1)
        
        # Cleanup
        cleanup_all_mocks()
        self.assertEqual(TestClass.attr, original_attr)

    def test_create_tracked_instance_patch(self):
        """Test create_tracked_instance_patch creates and registers a patch."""
        class TestClass:
            def method(self):
                return "original"
        
        instance = TestClass()
        
        patch = create_tracked_instance_patch(instance, 'method')
        mock = patch.activate()
        mock.return_value = "mocked"
        
        self.assertIsInstance(patch, Patch)
        self.assertEqual(get_mock_registry().get_registered_patch_count(), 1)
        self.assertEqual(instance.method(), "mocked")
        
        # Cleanup
        cleanup_all_mocks()


class MockCleanupIntegrationTests(unittest.TestCase):
    """Integration tests for automatic mock cleanup with test lifecycle."""

    def setUp(self):
        """Clear the registry before each test."""
        get_mock_registry().clear()

    def tearDown(self):
        """Clean up after each test - simulates test lifecycle integration."""
        cleanup_all_mocks()

    def test_multiple_mocks_cleaned_up(self):
        """Test that multiple mocks are all cleaned up."""
        mock1 = create_tracked_mock(return_value=1)
        mock2 = create_tracked_mock(return_value=2)
        mock3 = create_tracked_mock(return_value=3)
        
        mock1(1)
        mock2(2)
        mock3(3)
        
        self.assertEqual(get_mock_registry().get_registered_mock_count(), 3)
        
        cleanup_all_mocks()
        
        self.assertEqual(get_mock_registry().get_registered_mock_count(), 0)
        self.assertEqual(mock1.call_count, 0)
        self.assertEqual(mock2.call_count, 0)
        self.assertEqual(mock3.call_count, 0)

    def test_multiple_patches_cleaned_up_in_reverse_order(self):
        """Test that multiple patches are deactivated in reverse order."""
        original_exists = os.path.exists
        original_isfile = os.path.isfile
        
        patch1 = create_tracked_module_patch(os.path, 'exists')
        patch2 = create_tracked_module_patch(os.path, 'isfile')
        
        mock1 = patch1.activate()
        mock2 = patch2.activate()
        
        mock1.return_value = True
        mock2.return_value = False
        
        self.assertEqual(get_mock_registry().get_registered_patch_count(), 2)
        
        cleanup_all_mocks()
        
        self.assertEqual(get_mock_registry().get_registered_patch_count(), 0)
        self.assertIs(os.path.exists, original_exists)
        self.assertIs(os.path.isfile, original_isfile)

    def test_mixed_mocks_and_patches_cleaned_up(self):
        """Test that both mocks and patches are cleaned up together."""
        original_exists = os.path.exists
        
        mock = create_tracked_mock(return_value=42)
        patch = create_tracked_module_patch(os.path, 'exists')
        
        mock(1, 2)
        patch_mock = patch.activate()
        patch_mock.return_value = True
        
        self.assertEqual(get_mock_registry().get_registered_mock_count(), 1)
        self.assertEqual(get_mock_registry().get_registered_patch_count(), 1)
        
        cleanup_all_mocks()
        
        self.assertEqual(get_mock_registry().get_registered_mock_count(), 0)
        self.assertEqual(get_mock_registry().get_registered_patch_count(), 0)
        self.assertEqual(mock.call_count, 0)
        self.assertIs(os.path.exists, original_exists)

    def test_cleanup_prevents_mock_leakage(self):
        """Test that cleanup prevents mock state from leaking between tests."""
        # Simulate first test
        mock = create_tracked_mock(return_value=42)
        mock(1, 2, 3)
        self.assertEqual(mock.call_count, 1)
        
        # Cleanup at end of first test
        cleanup_all_mocks()
        
        # Simulate second test - mock should be reset
        self.assertEqual(mock.call_count, 0)
        self.assertIsNone(mock.mock_context().return_value)

    def test_cleanup_handles_errors_gracefully(self):
        """Test that cleanup continues even if individual cleanup fails."""
        registry = get_mock_registry()
        
        # Create a mock that will be cleaned up normally
        mock1 = Mock(return_value=1)
        registry.register_mock(mock1)
        mock1(1)
        
        # Create another mock
        mock2 = Mock(return_value=2)
        registry.register_mock(mock2)
        mock2(2)
        
        # Cleanup should handle all mocks even if one has issues
        cleanup_all_mocks()
        
        # Both mocks should be cleaned up
        self.assertEqual(registry.get_registered_mock_count(), 0)


if __name__ == "__main__":
    unittest.main()
