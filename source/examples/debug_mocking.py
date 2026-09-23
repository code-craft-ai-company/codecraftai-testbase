

from ccai.testbase.mocking import Mock, SideEffect, create_module_patch, create_class_patch, create_instance_patch
import os # For module patching example

def replace_me():
    """
        This function is a placeholder for the actual implementation.
        It is used to demonstrate how to use the Mock class.
    """
    print("This is the original function. It will be replaced by a mock.")
    return "Original Value"

class SomeClass:
    class_attribute = "Original Class Attribute"

    def __init__(self):
        self._instance_prop = "Original Instance Property"
        self.instance_attribute = "Original Instance Attribute"

    def instance_method(self, val):
        print(f"Original instance_method called with {val}")
        return f"Original instance_method: {val}"

    @property
    def instance_property(self):
        print("Original instance_property getter called")
        return self._instance_prop

    @instance_property.setter
    def instance_property(self, value):
        print(f"Original instance_property setter called with {value}")
        self._instance_prop = value

    @classmethod
    def class_method(cls, val):
        print(f"Original class_method called with {val}")
        return f"Original class_method: {val}"

    @staticmethod
    def static_method(val):
        print(f"Original static_method called with {val}")
        return f"Original static_method: {val}"


def debug_mock_simple_function_return_value():
    print("\n--- debug_mock_simple_function_return_value ---")
    # Mock a standalone function to return a specific value
    mock_function = Mock(reference=replace_me, return_value="Mocked Return Value")
    rtnval = mock_function()
    print(f"Called mock_function, got: {rtnval}")
    assert rtnval == "Mocked Return Value"

def debug_mock_simple_function_side_effect():
    print("\n--- debug_mock_simple_function_side_effect ---")
    def replacement_function():
        print("Side effect function called!")
        return "Side Effect Result"

    # Mock a standalone function to execute a side_effect callable
    mock_function = Mock(reference=replace_me, return_value=None, side_effect=replacement_function)
    rtnval = mock_function()
    print(f"Called mock_function with side_effect, got: {rtnval}")
    assert rtnval == "Side Effect Result"

def debug_mock_simple_function_side_effect_with_args():
    print("\n--- debug_mock_simple_function_side_effect_with_args ---")
    def side_effect_with_params(a, b=10):
        print(f"Side effect with_params called with a={a}, b={b}")
        return a + b

    # Using the SideEffect object to provide default arguments
    side_effect_obj = SideEffect(side_effect_with_params, default_args=(5,), default_kwargs={'b': 20})
    mock_function = Mock(side_effect=side_effect_obj)
    
    # Call with no args, uses SideEffect defaults
    rtnval_default = mock_function()
    print(f"Called mock_function (default SideEffect args), got: {rtnval_default}")
    assert rtnval_default == 25 # 5 + 20

    # Call with runtime args, overrides SideEffect defaults
    rtnval_runtime = mock_function(1, b=2)
    print(f"Called mock_function (runtime args), got: {rtnval_runtime}")
    assert rtnval_runtime == 3 # 1 + 2

def debug_mock_instance_method():
    print("\n--- debug_mock_instance_method ---")
    obj = SomeClass()
    # To mock an instance method, you typically patch it on the instance or class.
    # Here, we'll demonstrate creating a mock that *could* replace it.
    mock_method = Mock(return_value="Mocked instance_method response")
    
    # Pretend 'mock_method' has replaced 'obj.instance_method'
    # In a real test, you'd use Patch for this.
    original_method = obj.instance_method
    obj.instance_method = mock_method
    try:
        rtnval = obj.instance_method("test_val")
        print(f"Called mocked obj.instance_method, got: {rtnval}")
        assert rtnval == "Mocked instance_method response"
    finally:
        obj.instance_method = original_method # Restore

def debug_mock_property_access():
    print("\n--- debug_mock_property_access ---")
    
    # Using the new PropertyMock for property getter/setter mocking
    from ccai.testbase.mocking import PropertyMock, create_property_mock
    
    # Create a PropertyMock with getter return value
    prop_mock = create_property_mock(getter_return_value="Mocked Property Value")
    
    # Access the property (getter)
    print(f"Calling prop_mock.get(): {prop_mock.get()}")
    assert prop_mock.get() == "Mocked Property Value"
    
    # Verify getter was called
    prop_mock.assert_getter_called()
    print(f"Getter call count: {prop_mock.getter_call_count}")
    
    # Create a PropertyMock with setter tracking
    received_values = []
    def on_set(value):
        print(f"Mocked property setter called with: {value}")
        received_values.append(value)
    
    prop_mock_with_setter = create_property_mock(
        getter_return_value="Initial Value",
        setter_side_effect=on_set
    )
    
    # Access getter
    print(f"Getting value: {prop_mock_with_setter.get()}")
    
    # Set value (triggers setter side effect)
    prop_mock_with_setter.set("new_value")
    prop_mock_with_setter.set("another_value")
    
    # Verify setter calls
    prop_mock_with_setter.assert_setter_called()
    prop_mock_with_setter.assert_setter_any_call("new_value")
    prop_mock_with_setter.assert_setter_called_with("another_value")  # Last call
    print(f"Setter call count: {prop_mock_with_setter.setter_call_count}")
    print(f"Received values: {received_values}")
    
    # Using PropertyMock with dynamic getter (side effect)
    counter = [0]
    def increment_counter():
        counter[0] += 1
        return f"Access #{counter[0]}"
    
    dynamic_prop = create_property_mock(getter_side_effect=increment_counter)
    print(f"First access: {dynamic_prop.get()}")
    print(f"Second access: {dynamic_prop.get()}")
    print(f"Third access: {dynamic_prop.get()}")
    
    # Fluent configuration
    prop = PropertyMock()
    prop.configure_getter(return_value="configured_value").configure_setter(
        side_effect=lambda v: print(f"Fluent setter received: {v}")
    )
    print(f"Fluent configured getter: {prop.get()}")
    prop.set("fluent_value")
    
    # Reset and reuse
    prop.reset()
    print(f"After reset, getter call count: {prop.getter_call_count}")
    print(f"After reset, setter call count: {prop.setter_call_count}")

def debug_recursive_mock():
    print("\n--- debug_recursive_mock ---")
    recursive_mock = Mock(recursive=True)

    # Scenario 1: Setting return_value via the mock_context's dedicated setter method
    recursive_mock.foo.bar.baz.configure(return_value="Deeply Mocked Value")
    rtnval = recursive_mock.foo.bar.baz()
    print(f"Called recursive_mock.foo.bar.baz(), got: {rtnval}")
    assert rtnval == "Deeply Mocked Value"
    
    print(f"Type of recursive_mock.foo: {type(recursive_mock.foo)}")
    assert isinstance(recursive_mock.foo, Mock)
    assert recursive_mock.foo.mock_context().recursive is True

    # Scenario 2: Setting return_value via mock_context()
    child_mock_1 = recursive_mock.alpha.beta
    child_mock_1.configure(return_value="Context Set Return Value for alpha.beta")
    rtnval_context_set = child_mock_1()
    print(f"Called recursive_mock.alpha.beta() after context set, got: {rtnval_context_set}")
    assert rtnval_context_set == "Context Set Return Value for alpha.beta"

    # Scenario 3: Setting side_effect via mock_context()
    def simple_side_effect():
        print("simple_side_effect via context called!")
        return "Context Set Side Effect"
    child_mock_2 = recursive_mock.delta.epsilon
    child_mock_2.configure(side_effect=simple_side_effect)
    rtnval_side_effect_context = child_mock_2()
    print(f"Called recursive_mock.delta.epsilon() after context side_effect set, got: {rtnval_side_effect_context}")
    assert rtnval_side_effect_context == "Context Set Side Effect"

    # Scenario 4: Setting recursive via mock_context() on a child
    recursive_mock.zeta.eta.mock_context().recursive = False # Make 'eta' non-recursive
    assert recursive_mock.zeta.eta.mock_context().recursive is False
    try:
        _ = recursive_mock.zeta.eta.theta # Accessing further should fail if 'eta' is not recursive
        assert False, "Accessing attribute on a non-recursive child should have raised AttributeError"
    except AttributeError:
        print("Correctly raised AttributeError for non-recursive child's attribute access.")

def debug_patch_module_function():
    print("\n--- debug_patch_module_function ---")
    # Patching 'os.path.exists' for this example
    print(f"Original os.path.exists('/tmp'): {os.path.exists('/tmp')}")
    with create_module_patch(os.path, "exists", recursive=True) as mock_exists:
        mock_exists.configure(return_value="Patched Exists!")
        rtnval = os.path.exists("/some/path")
        print(f"Called patched os.path.exists, got: {rtnval}")
        assert rtnval == "Patched Exists!"
    print(f"Restored os.path.exists('/tmp'): {os.path.exists('/tmp')}") # Should be back to original

def debug_patch_class_method():
    print("\n--- debug_patch_class_method ---")
    print(f"Original SomeClass.class_method('val'): {SomeClass.class_method('val')}")
    with create_class_patch(SomeClass, "class_method") as mock_cm:
        mock_cm.configure(return_value="Patched Class Method")
        rtnval = SomeClass.class_method("another_val")
        print(f"Called patched SomeClass.class_method, got: {rtnval}")
        assert rtnval == "Patched Class Method"
    print(f"Restored SomeClass.class_method('val'): {SomeClass.class_method('val')}")

def debug_patch_static_method():
    print("\n--- debug_patch_static_method ---")
    print(f"Original SomeClass.static_method('val'): {SomeClass.static_method('val')}")
    with create_class_patch(SomeClass, "static_method") as mock_sm: # Patching static method is same as class method
        mock_sm.configure(return_value="Patched Static Method")
        rtnval = SomeClass.static_method("another_val")
        print(f"Called patched SomeClass.static_method, got: {rtnval}")
        assert rtnval == "Patched Static Method"
    print(f"Restored SomeClass.static_method('val'): {SomeClass.static_method('val')}")

def debug_patch_instance_method():
    print("\n--- debug_patch_instance_method ---")
    obj = SomeClass()
    print(f"Original obj.instance_method('val'): {obj.instance_method('val')}")
    with create_instance_patch(obj, "instance_method") as mock_im:
        mock_im.configure(return_value="Patched Instance Method")
        rtnval = obj.instance_method("another_val")
        print(f"Called patched obj.instance_method, got: {rtnval}")
        assert rtnval == "Patched Instance Method"
    print(f"Restored obj.instance_method('val'): {obj.instance_method('val')}")

def debug_mock_configure_method():
    print("\n--- debug_mock_configure_method ---")
    
    # Create a recursive mock to get dynamically created children
    mock_obj = Mock(recursive=True)

    # Configure mocka.mockb
    mock_b = mock_obj.alpha.beta # mock_b is now a Mock instance
    mock_b.configure(return_value=5)
    
    rtn_b = mock_obj.alpha.beta()
    print(f"Called mock_obj.alpha.beta() after configure, got: {rtn_b}")
    assert rtn_b == 5
    mock_obj.alpha.beta.assert_called_once_with() # Verify it was called

    # Configure mocka.mockc with a side effect
    def my_side_effect(x, y):
        print(f"my_side_effect called with x={x}, y={y}")
        return x + y
    
    mock_c = mock_obj.alpha.gamma # mock_c is another Mock instance
    mock_c.configure(side_effect=my_side_effect, recursive=False) # Also make this child non-recursive
    
    rtn_c = mock_obj.alpha.gamma(10, 20)
    print(f"Called mock_obj.alpha.gamma(10, 20) after configure, got: {rtn_c}")
    assert rtn_c == 30
    mock_obj.alpha.gamma.assert_called_once_with(10, 20)
    assert mock_obj.alpha.gamma.mock_context().recursive is False

    # Test configuring only one aspect
    mock_d = mock_obj.delta
    mock_d.configure(return_value="Only Return Value Set")
    assert mock_d() == "Only Return Value Set"
    # Check that other properties were not unintentionally reset (if they had defaults or were set before)
    # For a fresh mock, side_effect would be None, recursive would be True (from parent)
    assert mock_d.mock_context().side_effect is None 
    assert mock_d.mock_context().recursive is True 

    # Fluent configuration of the same mock
    mock_obj.epsilon.zeta.configure(return_value=100).configure(recursive=False)
    assert mock_obj.epsilon.zeta() == 100
    assert mock_obj.epsilon.zeta.mock_context().recursive is False
    print("Fluent configuration successful for the same mock (zeta).")

    # Fluent configuration of parent then child
    mock_obj.theta.iota.configure(return_value="Theta Configured").kappa.configure(return_value="Kappa Configured")
    assert mock_obj.theta.iota() == "Theta Configured"
    assert mock_obj.theta.iota.kappa() == "Kappa Configured"
    print("Fluent configuration of parent (iota) and then its child (kappa) successful.")

def main_debug_mocking():
    debug_mock_simple_function_return_value()
    debug_mock_simple_function_side_effect()
    debug_mock_simple_function_side_effect_with_args()
    debug_mock_instance_method() # Shows mock configuration, patching is better
    debug_mock_property_access() # Shows mock configuration, patching is better
    debug_recursive_mock()
    debug_patch_module_function()
    debug_patch_class_method()
    debug_patch_static_method()
    debug_patch_instance_method()
    debug_mock_configure_method()
    return

if __name__ == "__main__":
    main_debug_mocking()