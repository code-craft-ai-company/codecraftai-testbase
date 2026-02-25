"""
    .. module:: automojo.testbase.examples.mocking_examples
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Comprehensive usage examples for the TestBase mocking framework.

    This module provides detailed examples demonstrating all major features of the
    TestBase mocking framework, including:
    
    1. Basic mock creation and configuration
    2. Side effect usage patterns
    3. Patch context manager usage
    4. Recursive mock patterns
    5. Strict attribute mode usage

    .. moduleauthor:: AutomationX
"""

__author__ = "AutomationX"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Generator
import os
import types

from automojo.testbase.mocking import (
    Mock,
    MockContext,
    MockType,
    SideEffect,
    Patch,
    PatchType,
    create_module_patch,
    create_class_patch,
    create_instance_patch,
)


# =============================================================================
# SECTION 1: BASIC MOCK CREATION AND CONFIGURATION
# =============================================================================

def example_basic_mock_creation():
    """
    Demonstrates basic mock object creation with various configurations.
    
    This example shows how to create Mock objects with different initial
    configurations including return values, mock types, and attributes.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Basic Mock Creation")
    print("=" * 70)

    # Example 1.1: Simple mock with no configuration
    # A basic mock that returns None when called
    simple_mock = Mock()
    result = simple_mock()
    print(f"1.1 Simple mock call result: {result}")  # None
    assert result is None
    
    # Example 1.2: Mock with return value
    # Configure a mock to return a specific value when called
    mock_with_return = Mock(return_value=42)
    result = mock_with_return()
    print(f"1.2 Mock with return_value: {result}")  # 42
    assert result == 42
    
    # Example 1.3: Mock with pre-defined attributes
    # Create a mock with attributes already set
    mock_with_attrs = Mock(mock_attributes={
        'id': 123,
        'name': 'test_object',
        'active': True
    })
    print(f"1.3 Mock attributes - id: {mock_with_attrs.id}, name: {mock_with_attrs.name}")
    assert mock_with_attrs.id == 123
    assert mock_with_attrs.name == 'test_object'
    assert mock_with_attrs.active is True
    
    # Example 1.4: Configuring mock after creation using configure()
    # The configure() method allows fluent configuration
    mock = Mock()
    mock.configure(return_value="configured value")
    result = mock()
    print(f"1.4 Configured mock result: {result}")
    assert result == "configured value"
    
    # Example 1.5: Configuring mock via attribute assignment
    # You can also set return_value directly as an attribute
    mock = Mock()
    mock.return_value = "assigned value"
    result = mock()
    print(f"1.5 Attribute-assigned mock result: {result}")
    assert result == "assigned value"
    
    # Example 1.6: Using MockContext for advanced configuration
    # Access the mock's context for more control
    mock = Mock()
    ctx = mock.mock_context()
    ctx.set_attribute('custom_attr', 'custom_value')
    ctx.mock_method('calculate', return_value=100)
    
    print(f"1.6 Custom attribute: {mock.custom_attr}")
    print(f"1.6 Mock method result: {mock.calculate()}")
    assert mock.custom_attr == 'custom_value'
    assert mock.calculate() == 100
    
    print("\n✓ Basic mock creation examples completed successfully!")


def example_mock_call_tracking():
    """
    Demonstrates how mocks track calls for verification.
    
    This example shows how to use call tracking properties and assertion
    methods to verify mock interactions.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Mock Call Tracking")
    print("=" * 70)
    
    # Create a mock and make several calls
    mock = Mock(return_value="result")
    
    # Make calls with different arguments
    mock(1, 2)
    mock("hello", key="value")
    mock(a=1, b=2, c=3)
    
    # Example 2.1: Check call count
    print(f"2.1 Call count: {mock.call_count}")  # 3
    assert mock.call_count == 3
    
    # Example 2.2: Check last call arguments
    # call_args returns (args_tuple, kwargs_dict)
    args, kwargs = mock.call_args
    print(f"2.2 Last call - args: {args}, kwargs: {kwargs}")
    assert args == ()
    assert kwargs == {'a': 1, 'b': 2, 'c': 3}
    
    # Example 2.3: Check all calls
    print(f"2.3 All calls: {mock.call_args_list}")
    assert len(mock.call_args_list) == 3
    
    # Example 2.4: Using assertion methods
    ctx = mock.mock_context()
    
    # Assert mock was called
    ctx.assert_called()
    print("2.4 assert_called() passed")
    
    # Assert specific call was made (any position)
    ctx.assert_any_call(1, 2)
    print("2.4 assert_any_call(1, 2) passed")
    
    # Assert last call arguments
    ctx.assert_called_with(a=1, b=2, c=3)
    print("2.4 assert_called_with(a=1, b=2, c=3) passed")
    
    # Example 2.5: assert_called_once with fresh mock
    fresh_mock = Mock()
    fresh_mock("single call")
    fresh_mock.mock_context().assert_called_once()
    fresh_mock.mock_context().assert_called_once_with("single call")
    print("2.5 assert_called_once() and assert_called_once_with() passed")
    
    # Example 2.6: assert_has_calls for sequence verification
    sequence_mock = Mock()
    sequence_mock(1)
    sequence_mock(2)
    sequence_mock(3)
    
    # Check for a contiguous sequence
    sequence_mock.mock_context().assert_has_calls([
        ((1,), {}),
        ((2,), {})
    ])
    print("2.6 assert_has_calls() for sequence passed")
    
    # Check for calls in any order
    sequence_mock.mock_context().assert_has_calls([
        ((3,), {}),
        ((1,), {})
    ], any_order=True)
    print("2.6 assert_has_calls(any_order=True) passed")
    
    print("\n✓ Mock call tracking examples completed successfully!")


def example_mock_reset():
    """
    Demonstrates how to reset mock state for reuse.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Mock Reset")
    print("=" * 70)
    
    mock = Mock(return_value=42)
    mock(1, 2, 3)
    mock("a", "b")
    
    print(f"Before reset - call_count: {mock.call_count}, return_value: {mock.mock_context().return_value}")
    assert mock.call_count == 2
    
    # Reset the mock
    mock.mock_context().reset()
    
    print(f"After reset - call_count: {mock.call_count}, return_value: {mock.mock_context().return_value}")
    assert mock.call_count == 0
    assert mock.mock_context().return_value is None
    assert mock.call_args is None
    assert mock.call_args_list == []
    
    print("\n✓ Mock reset example completed successfully!")


# =============================================================================
# SECTION 2: SIDE EFFECT USAGE PATTERNS
# =============================================================================

def example_basic_side_effects():
    """
    Demonstrates basic side effect usage with mocks.
    
    Side effects allow you to execute custom logic when a mock is called,
    enabling dynamic return values based on input arguments.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Basic Side Effects")
    print("=" * 70)
    
    # Example 3.1: Simple side effect function
    def add_numbers(a, b):
        return a + b
    
    mock = Mock(side_effect=add_numbers)
    result = mock(5, 3)
    print(f"3.1 Side effect add_numbers(5, 3): {result}")
    assert result == 8
    
    # Example 3.2: Side effect with lambda
    mock = Mock(side_effect=lambda x: x * 2)
    result = mock(10)
    print(f"3.2 Lambda side effect (10 * 2): {result}")
    assert result == 20
    
    # Example 3.3: Side effect that raises an exception
    def raise_error():
        raise ValueError("Simulated error")
    
    mock = Mock(side_effect=raise_error)
    try:
        mock()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"3.3 Side effect raised exception: {e}")
    
    # Example 3.4: Side effect with state (closure)
    call_count = [0]
    def counting_side_effect():
        call_count[0] += 1
        return f"Call #{call_count[0]}"
    
    mock = Mock(side_effect=counting_side_effect)
    print(f"3.4 First call: {mock()}")   # Call #1
    print(f"3.4 Second call: {mock()}")  # Call #2
    print(f"3.4 Third call: {mock()}")   # Call #3
    assert call_count[0] == 3
    
    # Example 3.5: Side effect takes precedence over return_value
    mock = Mock(return_value="ignored", side_effect=lambda: "from side effect")
    result = mock()
    print(f"3.5 Side effect overrides return_value: {result}")
    assert result == "from side effect"
    
    print("\n✓ Basic side effect examples completed successfully!")


def example_side_effect_class():
    """
    Demonstrates using the SideEffect class for advanced side effect patterns.
    
    The SideEffect class allows you to configure default arguments that are
    used when the mock is called without arguments.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: SideEffect Class Usage")
    print("=" * 70)
    
    # Example 4.1: SideEffect with default positional arguments
    def compute(a, b, c=1):
        return (a + b) * c
    
    side_effect = SideEffect(compute, default_args=(10, 20))
    mock = Mock(side_effect=side_effect)
    
    # Call without arguments - uses defaults
    result = mock()
    print(f"4.1 With default args (10, 20): {result}")  # (10 + 20) * 1 = 30
    assert result == 30
    
    # Call with arguments - overrides defaults
    result = mock(5, 5)
    print(f"4.1 With provided args (5, 5): {result}")  # (5 + 5) * 1 = 10
    assert result == 10
    
    # Example 4.2: SideEffect with default keyword arguments
    def greet(name="World", greeting="Hello"):
        return f"{greeting}, {name}!"
    
    side_effect = SideEffect(greet, default_kwargs={'name': 'Developer', 'greeting': 'Welcome'})
    mock = Mock(side_effect=side_effect)
    
    # Call without arguments - uses defaults
    result = mock()
    print(f"4.2 With default kwargs: {result}")
    assert result == "Welcome, Developer!"
    
    # Call with keyword arguments - overrides defaults
    result = mock(name="Tester", greeting="Hi")
    print(f"4.2 With provided kwargs: {result}")
    assert result == "Hi, Tester!"
    
    # Example 4.3: SideEffect with both default args and kwargs
    def format_data(value, prefix="", suffix=""):
        return f"{prefix}{value}{suffix}"
    
    side_effect = SideEffect(
        format_data,
        default_args=("default_value",),
        default_kwargs={'prefix': '[', 'suffix': ']'}
    )
    mock = Mock(side_effect=side_effect)
    
    result = mock()
    print(f"4.3 With both defaults: {result}")
    assert result == "[default_value]"
    
    result = mock("custom", prefix="<", suffix=">")
    print(f"4.3 With overrides: {result}")
    assert result == "<custom>"
    
    print("\n✓ SideEffect class examples completed successfully!")


def example_side_effect_patterns():
    """
    Demonstrates common side effect patterns used in testing.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Common Side Effect Patterns")
    print("=" * 70)
    
    # Pattern 5.1: Return different values on successive calls
    values = iter([1, 2, 3, 4, 5])
    mock = Mock(side_effect=lambda: next(values))
    
    results = [mock() for _ in range(5)]
    print(f"5.1 Successive return values: {results}")
    assert results == [1, 2, 3, 4, 5]
    
    # Pattern 5.2: Return value based on input
    def lookup_value(key):
        data = {'a': 1, 'b': 2, 'c': 3}
        return data.get(key, None)
    
    mock = Mock(side_effect=lookup_value)
    print(f"5.2 Lookup 'a': {mock('a')}")  # 1
    print(f"5.2 Lookup 'b': {mock('b')}")  # 2
    print(f"5.2 Lookup 'x': {mock('x')}")  # None
    
    # Pattern 5.3: Conditional exception raising
    def conditional_error(value):
        if value < 0:
            raise ValueError("Negative values not allowed")
        return value * 2
    
    mock = Mock(side_effect=conditional_error)
    print(f"5.3 Positive value (5): {mock(5)}")  # 10
    try:
        mock(-1)
    except ValueError as e:
        print(f"5.3 Negative value raised: {e}")
    
    # Pattern 5.4: Side effect that modifies external state
    external_log = []
    def logging_side_effect(*args, **kwargs):
        external_log.append({'args': args, 'kwargs': kwargs})
        return "logged"
    
    mock = Mock(side_effect=logging_side_effect)
    mock(1, 2, key="value")
    mock("test")
    print(f"5.4 External log: {external_log}")
    assert len(external_log) == 2
    
    # Pattern 5.5: Chained method calls with side effects
    # Useful for mocking database queries or API clients
    mock_query = Mock(recursive=True)
    
    # Configure the chain: session.query(Model).filter(...).first()
    mock_filter = Mock(recursive=True)
    mock_filter.first.configure(return_value="filtered_result")
    
    mock_query.query.configure(return_value=mock_filter)
    
    result = mock_query.query().first()
    print(f"5.5 Chained call result: {result}")
    
    print("\n✓ Side effect pattern examples completed successfully!")


# =============================================================================
# SECTION 3: PATCH CONTEXT MANAGER USAGE
# =============================================================================

# Helper classes and functions for patching examples
class DatabaseService:
    """Example service class for demonstrating patching."""
    
    connection_string = "production://database"
    
    def __init__(self):
        self.connected = False
    
    def connect(self):
        self.connected = True
        return f"Connected to {self.connection_string}"
    
    def query(self, sql):
        if not self.connected:
            raise RuntimeError("Not connected")
        return f"Results for: {sql}"
    
    @classmethod
    def get_connection_string(cls):
        return cls.connection_string
    
    @staticmethod
    def validate_sql(sql):
        return sql.strip().upper().startswith("SELECT")


def fetch_data_from_api():
    """Example function for demonstrating module patching."""
    return "Real API data"


def example_module_patching():
    """
    Demonstrates patching module-level attributes.
    
    Module patching is useful for replacing functions, classes, or variables
    defined at the module level.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Module Patching")
    print("=" * 70)
    
    # Example 6.1: Patch a module function using context manager
    print(f"6.1 Before patch - os.path.exists('/tmp'): {os.path.exists('/tmp')}")
    
    with create_module_patch(os.path, "exists") as mock_exists:
        mock_exists.configure(return_value=True)
        result = os.path.exists("/nonexistent/path")
        print(f"6.1 During patch - os.path.exists('/nonexistent/path'): {result}")
        assert result is True
        
        # Verify the mock was called
        mock_exists.mock_context().assert_called_once_with("/nonexistent/path")
    
    # Original is restored after context exit
    print(f"6.1 After patch - os.path.exists('/tmp'): {os.path.exists('/tmp')}")
    
    # Example 6.2: Patch with side effect
    with create_module_patch(os.path, "isfile") as mock_isfile:
        def check_file(path):
            # Only return True for .txt files
            return path.endswith('.txt')
        
        mock_isfile.configure(side_effect=check_file)
        
        print(f"6.2 isfile('test.txt'): {os.path.isfile('test.txt')}")  # True
        print(f"6.2 isfile('test.py'): {os.path.isfile('test.py')}")    # False
    
    # Example 6.3: Manual activation/deactivation
    patch = create_module_patch(os.path, "isdir")
    mock = patch.activate()
    mock.configure(return_value=False)
    
    result = os.path.isdir("/any/path")
    print(f"6.3 Manual patch - isdir result: {result}")
    assert result is False
    
    patch.deactivate()
    print(f"6.3 After deactivate - isdir('/tmp'): {os.path.isdir('/tmp')}")
    
    # Example 6.4: Patch with recursive mock
    with create_module_patch(os.path, "join", recursive=True) as mock_join:
        mock_join.configure(return_value="/mocked/path")
        result = os.path.join("a", "b", "c")
        print(f"6.4 Recursive patch result: {result}")
        assert result == "/mocked/path"
    
    print("\n✓ Module patching examples completed successfully!")


def example_class_patching():
    """
    Demonstrates patching class-level attributes.
    
    Class patching is useful for replacing class methods, static methods,
    or class variables.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Class Patching")
    print("=" * 70)
    
    # Example 7.1: Patch a class method
    print(f"7.1 Before patch - get_connection_string(): {DatabaseService.get_connection_string()}")
    
    with create_class_patch(DatabaseService, "get_connection_string") as mock_method:
        mock_method.configure(return_value="test://localhost")
        result = DatabaseService.get_connection_string()
        print(f"7.1 During patch - get_connection_string(): {result}")
        assert result == "test://localhost"
    
    print(f"7.1 After patch - get_connection_string(): {DatabaseService.get_connection_string()}")
    
    # Example 7.2: Patch a static method
    print(f"7.2 Before patch - validate_sql('SELECT *'): {DatabaseService.validate_sql('SELECT *')}")
    
    with create_class_patch(DatabaseService, "validate_sql") as mock_static:
        mock_static.configure(return_value=True)  # Always return True
        result = DatabaseService.validate_sql("DELETE FROM users")
        print(f"7.2 During patch - validate_sql('DELETE...'): {result}")
        assert result is True
    
    print(f"7.2 After patch - validate_sql('DELETE...'): {DatabaseService.validate_sql('DELETE FROM users')}")
    
    # Example 7.3: Patch a class attribute
    print(f"7.3 Before patch - connection_string: {DatabaseService.connection_string}")
    
    with create_class_patch(DatabaseService, "connection_string") as mock_attr:
        mock_attr.configure(return_value="test://mock_db")
        # Note: For class attributes, you access the mock directly
        result = DatabaseService.connection_string()
        print(f"7.3 During patch - connection_string: {result}")
    
    print(f"7.3 After patch - connection_string: {DatabaseService.connection_string}")
    
    print("\n✓ Class patching examples completed successfully!")


def example_instance_patching():
    """
    Demonstrates patching instance-level attributes.
    
    Instance patching is useful for replacing methods or attributes on
    specific object instances without affecting other instances.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Instance Patching")
    print("=" * 70)
    
    # Create two instances
    service1 = DatabaseService()
    service2 = DatabaseService()
    
    # Example 8.1: Patch an instance method
    print(f"8.1 Before patch - service1.connect(): {service1.connect()}")
    
    with create_instance_patch(service1, "connect") as mock_connect:
        mock_connect.configure(return_value="Mocked connection")
        
        result1 = service1.connect()
        result2 = service2.connect()  # Not patched
        
        print(f"8.1 service1.connect() (patched): {result1}")
        print(f"8.1 service2.connect() (not patched): {result2}")
        
        assert result1 == "Mocked connection"
        assert "Connected to" in result2
    
    print(f"8.1 After patch - service1.connect(): {service1.connect()}")
    
    # Example 8.2: Patch with side effect that uses instance state
    service = DatabaseService()
    service.connected = True
    
    with create_instance_patch(service, "query") as mock_query:
        def mock_query_impl(sql):
            return f"MOCKED: {sql}"
        
        mock_query.configure(side_effect=mock_query_impl)
        
        result = service.query("SELECT * FROM users")
        print(f"8.2 Mocked query result: {result}")
        assert result == "MOCKED: SELECT * FROM users"
        
        # Verify the call
        mock_query.mock_context().assert_called_once_with("SELECT * FROM users")
    
    # Example 8.3: Patch an instance attribute
    service = DatabaseService()
    
    with create_instance_patch(service, "connected") as mock_connected:
        mock_connected.configure(return_value=True)
        # Access as a callable since it's now a mock
        print(f"8.3 Mocked connected attribute: {service.connected()}")
    
    print("\n✓ Instance patching examples completed successfully!")


def example_nested_patches():
    """
    Demonstrates using multiple patches simultaneously.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Nested Patches")
    print("=" * 70)
    
    # Example 9.1: Multiple patches using nested context managers
    with create_module_patch(os.path, "exists") as mock_exists:
        mock_exists.configure(return_value=True)
        
        with create_module_patch(os.path, "isfile") as mock_isfile:
            mock_isfile.configure(return_value=True)
            
            with create_module_patch(os.path, "isdir") as mock_isdir:
                mock_isdir.configure(return_value=False)
                
                print(f"9.1 exists: {os.path.exists('/test')}")
                print(f"9.1 isfile: {os.path.isfile('/test')}")
                print(f"9.1 isdir: {os.path.isdir('/test')}")
                
                assert os.path.exists('/test') is True
                assert os.path.isfile('/test') is True
                assert os.path.isdir('/test') is False
    
    # All patches are restored
    print(f"9.1 After all patches - exists('/tmp'): {os.path.exists('/tmp')}")
    
    # Example 9.2: Patches with exception handling
    try:
        with create_module_patch(os.path, "exists") as mock_exists:
            mock_exists.configure(return_value=True)
            print(f"9.2 Before exception - exists: {os.path.exists('/test')}")
            raise RuntimeError("Simulated error")
    except RuntimeError:
        print("9.2 Exception caught, patch should be restored")
    
    # Verify patch was restored even after exception
    actual_result = os.path.exists('/tmp')
    print(f"9.2 After exception - exists('/tmp'): {actual_result}")
    
    print("\n✓ Nested patches examples completed successfully!")


# =============================================================================
# SECTION 4: RECURSIVE MOCK PATTERNS
# =============================================================================

def example_recursive_mock_basics():
    """
    Demonstrates basic recursive mock functionality.
    
    Recursive mocks automatically create child mocks when accessing
    undefined attributes, enabling fluent chained access patterns.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Recursive Mock Basics")
    print("=" * 70)
    
    # Example 10.1: Basic recursive mock
    mock = Mock(recursive=True)
    
    # Accessing undefined attributes creates child mocks
    child = mock.some_attribute
    print(f"10.1 Child mock type: {type(child).__name__}")
    assert isinstance(child, Mock)
    
    # Same attribute returns same mock (identity consistency)
    assert mock.some_attribute is child
    print("10.1 Identity consistency verified: mock.some_attribute is child")
    
    # Example 10.2: Deep chained access
    mock = Mock(recursive=True)
    
    # Access deeply nested attributes
    deep_mock = mock.level1.level2.level3.level4
    print(f"10.2 Deep mock type: {type(deep_mock).__name__}")
    assert isinstance(deep_mock, Mock)
    
    # Configure the deep mock
    deep_mock.configure(return_value="deep value")
    result = mock.level1.level2.level3.level4()
    print(f"10.2 Deep mock call result: {result}")
    assert result == "deep value"
    
    # Example 10.3: Child mocks inherit recursive setting
    mock = Mock(recursive=True)
    child = mock.child
    
    # Child should also be recursive
    assert child.mock_context().recursive is True
    print("10.3 Child mock inherited recursive=True")
    
    # Grandchild should also be recursive
    grandchild = child.grandchild
    assert grandchild.mock_context().recursive is True
    print("10.3 Grandchild mock inherited recursive=True")
    
    # Example 10.4: Disabling recursion on a child
    mock = Mock(recursive=True)
    child = mock.child
    child.mock_context().recursive = False
    
    # Now accessing undefined attributes on child should fail
    try:
        _ = child.undefined_attr
        assert False, "Should have raised AttributeError"
    except AttributeError:
        print("10.4 AttributeError raised for non-recursive child")
    
    print("\n✓ Recursive mock basics examples completed successfully!")


def example_recursive_mock_configuration():
    """
    Demonstrates configuring recursive mocks for complex scenarios.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Recursive Mock Configuration")
    print("=" * 70)
    
    # Example 11.1: Configure return values at different levels
    mock = Mock(recursive=True)
    
    mock.configure(return_value="root result")
    mock.child.configure(return_value="child result")
    mock.child.grandchild.configure(return_value="grandchild result")
    
    print(f"11.1 mock(): {mock()}")
    print(f"11.1 mock.child(): {mock.child()}")
    print(f"11.1 mock.child.grandchild(): {mock.child.grandchild()}")
    
    assert mock() == "root result"
    assert mock.child() == "child result"
    assert mock.child.grandchild() == "grandchild result"
    
    # Example 11.2: Fluent configuration chaining
    mock = Mock(recursive=True)
    
    # Configure parent and child in one chain
    mock.api.client.configure(return_value="client").request.configure(return_value="response")
    
    print(f"11.2 mock.api.client(): {mock.api.client()}")
    print(f"11.2 mock.api.client.request(): {mock.api.client.request()}")
    
    # Example 11.3: Configure side effects on nested mocks
    mock = Mock(recursive=True)
    
    def process_data(data):
        return f"Processed: {data}"
    
    mock.processor.transform.configure(side_effect=process_data)
    
    result = mock.processor.transform("input data")
    print(f"11.3 Nested side effect result: {result}")
    assert result == "Processed: input data"
    
    # Example 11.4: Using mock_method on recursive mocks
    mock = Mock(recursive=True)
    ctx = mock.service.mock_context()
    
    ctx.mock_method('fetch', return_value={'data': 'value'})
    ctx.mock_method('save', side_effect=lambda x: f"Saved: {x}")
    
    print(f"11.4 mock.service.fetch(): {mock.service.fetch()}")
    print(f"11.4 mock.service.save('test'): {mock.service.save('test')}")
    
    print("\n✓ Recursive mock configuration examples completed successfully!")


def example_recursive_mock_real_world():
    """
    Demonstrates real-world use cases for recursive mocks.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Recursive Mock Real-World Patterns")
    print("=" * 70)
    
    # Pattern 12.1: Mocking a database session (SQLAlchemy-style)
    mock_session = Mock(recursive=True)
    
    # Configure the query chain: session.query(Model).filter(...).first()
    mock_session.query.configure(return_value=mock_session.query)
    mock_session.query.filter.configure(return_value=mock_session.query.filter)
    mock_session.query.filter.first.configure(return_value={'id': 1, 'name': 'Test User'})
    
    # Simulate the query
    result = mock_session.query("User").filter(name="test").first()
    print(f"12.1 Database query result: {result}")
    
    # Verify the chain was called
    mock_session.query.mock_context().assert_called_with("User")
    
    # Pattern 12.2: Mocking an HTTP client
    mock_client = Mock(recursive=True)
    
    # Configure response
    mock_response = Mock()
    mock_response.configure(return_value={'status': 200, 'data': 'response data'})
    mock_response.mock_context().set_attribute('status_code', 200)
    mock_response.mock_context().set_attribute('json', lambda: {'key': 'value'})
    
    mock_client.get.configure(return_value=mock_response)
    mock_client.post.configure(return_value=mock_response)
    
    response = mock_client.get("https://api.example.com/data")
    print(f"12.2 HTTP GET response status: {response.status_code}")
    print(f"12.2 HTTP GET response json: {response.json()}")
    
    # Pattern 12.3: Mocking a file system interface
    mock_fs = Mock(recursive=True)
    
    mock_fs.path.exists.configure(return_value=True)
    mock_fs.path.join.configure(side_effect=lambda *parts: '/'.join(parts))
    mock_fs.open.configure(return_value=Mock(
        mock_attributes={
            'read': Mock(return_value="file contents"),
            'write': Mock(return_value=None)
        }
    ))
    
    path = mock_fs.path.join("home", "user", "file.txt")
    print(f"12.3 Joined path: {path}")
    print(f"12.3 Path exists: {mock_fs.path.exists(path)}")
    
    # Pattern 12.4: Mocking a configuration object
    mock_config = Mock(recursive=True)
    
    mock_config.database.host.configure(return_value="localhost")
    mock_config.database.port.configure(return_value=5432)
    mock_config.database.name.configure(return_value="testdb")
    mock_config.api.key.configure(return_value="secret-key")
    mock_config.api.timeout.configure(return_value=30)
    
    print(f"12.4 DB Host: {mock_config.database.host()}")
    print(f"12.4 DB Port: {mock_config.database.port()}")
    print(f"12.4 API Key: {mock_config.api.key()}")
    
    print("\n✓ Recursive mock real-world examples completed successfully!")


# =============================================================================
# SECTION 5: STRICT ATTRIBUTE MODE USAGE
# =============================================================================

def example_strict_attrs_basics():
    """
    Demonstrates basic strict attribute mode functionality.
    
    Strict attribute mode restricts attribute access to only pre-defined
    attributes, preventing accidental access to undefined attributes.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Strict Attribute Mode Basics")
    print("=" * 70)
    
    # Example 13.1: Create a strict mock with pre-defined attributes
    mock = Mock(
        mock_attributes={
            'id': 123,
            'name': 'test',
            'active': True
        },
        strict_attrs=True
    )
    
    # Access pre-defined attributes works
    print(f"13.1 mock.id: {mock.id}")
    print(f"13.1 mock.name: {mock.name}")
    print(f"13.1 mock.active: {mock.active}")
    
    # Example 13.2: Accessing undefined attributes raises AttributeError
    try:
        _ = mock.undefined_attribute
        assert False, "Should have raised AttributeError"
    except AttributeError as e:
        print(f"13.2 AttributeError for undefined attribute: {e}")
    
    # Example 13.3: Setting new attributes raises AttributeError
    try:
        mock.new_attribute = "value"
        assert False, "Should have raised AttributeError"
    except AttributeError as e:
        print(f"13.3 AttributeError for setting new attribute: {e}")
    
    # Example 13.4: Modifying existing attributes works
    mock.name = "updated_name"
    print(f"13.4 Updated mock.name: {mock.name}")
    assert mock.name == "updated_name"
    
    # Example 13.5: Special mock attributes can always be set
    mock.return_value = "special value"
    mock.side_effect = lambda: "effect"
    print(f"13.5 return_value set: {mock.mock_context().return_value}")
    print("13.5 side_effect set successfully")
    
    print("\n✓ Strict attribute mode basics examples completed successfully!")


def example_strict_attrs_with_methods():
    """
    Demonstrates strict attribute mode with mock methods.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Strict Attributes with Methods")
    print("=" * 70)
    
    # Example 14.1: Create strict mock with methods
    mock = Mock(strict_attrs=True)
    ctx = mock.mock_context()
    
    # Add methods using mock_method
    ctx.mock_method('calculate', return_value=42)
    ctx.mock_method('process', side_effect=lambda x: x * 2)
    
    # Access defined methods works
    print(f"14.1 mock.calculate(): {mock.calculate()}")
    print(f"14.1 mock.process(5): {mock.process(5)}")
    
    # Access undefined methods fails
    try:
        _ = mock.undefined_method
        assert False, "Should have raised AttributeError"
    except AttributeError:
        print("14.1 AttributeError for undefined method")
    
    # Example 14.2: Strict mock with properties
    mock = Mock(strict_attrs=True)
    ctx = mock.mock_context()
    
    ctx.mock_property('name', return_value='Test Name')
    ctx.mock_property('value', return_value=100)
    
    print(f"14.2 mock.name: {mock.name}")
    print(f"14.2 mock.value: {mock.value}")
    
    # Example 14.3: Combining strict_attrs with return_value
    mock = Mock(
        mock_attributes={'allowed': True},
        return_value="callable result",
        strict_attrs=True
    )
    
    print(f"14.3 mock(): {mock()}")
    print(f"14.3 mock.allowed: {mock.allowed}")
    
    print("\n✓ Strict attributes with methods examples completed successfully!")


def example_strict_attrs_inheritance():
    """
    Demonstrates how strict_attrs is inherited by child mocks.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Strict Attributes Inheritance")
    print("=" * 70)
    
    # Example 15.1: Child mocks inherit strict_attrs
    mock = Mock(recursive=True, strict_attrs=True)
    ctx = mock.mock_context()
    
    # Define an attribute that is a child mock
    ctx.set_attribute('child', Mock(recursive=True, strict_attrs=True))
    
    # The child should also be strict
    child = mock.child
    assert child.mock_context()._strict_attrs is True
    print("15.1 Child mock inherited strict_attrs=True")
    
    # Example 15.2: Strict parent with defined children
    mock = Mock(strict_attrs=True)
    ctx = mock.mock_context()
    
    # Create a child with its own attributes
    child_mock = Mock(
        mock_attributes={'child_attr': 'value'},
        strict_attrs=True
    )
    ctx.set_attribute('child', child_mock)
    
    # Access child's defined attribute
    print(f"15.2 mock.child.child_attr: {mock.child.child_attr}")
    
    # Access undefined attribute on child fails
    try:
        _ = mock.child.undefined
        assert False, "Should have raised AttributeError"
    except AttributeError:
        print("15.2 AttributeError for child's undefined attribute")
    
    # Example 15.3: Mixed strict and non-strict
    parent = Mock(strict_attrs=True)
    parent_ctx = parent.mock_context()
    
    # Add a non-strict child
    non_strict_child = Mock(recursive=True, strict_attrs=False)
    parent_ctx.set_attribute('flexible_child', non_strict_child)
    
    # Parent is strict
    try:
        _ = parent.undefined
        assert False, "Should have raised AttributeError"
    except AttributeError:
        print("15.3 Parent is strict - undefined access fails")
    
    # Child is not strict - undefined access creates new mock
    grandchild = parent.flexible_child.any_attribute
    print(f"15.3 Non-strict child allows undefined access: {type(grandchild).__name__}")
    
    print("\n✓ Strict attributes inheritance examples completed successfully!")


def example_strict_attrs_real_world():
    """
    Demonstrates real-world use cases for strict attribute mode.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Strict Attributes Real-World Patterns")
    print("=" * 70)
    
    # Pattern 16.1: Mocking a well-defined interface
    # When you want to ensure tests only use expected attributes
    
    class UserInterface:
        """Interface definition for reference."""
        id: int
        name: str
        email: str
        def save(self): pass
        def delete(self): pass
    
    # Create a strict mock that matches the interface
    mock_user = Mock(strict_attrs=True)
    ctx = mock_user.mock_context()
    
    ctx.set_attribute('id', 1)
    ctx.set_attribute('name', 'Test User')
    ctx.set_attribute('email', 'test@example.com')
    ctx.mock_method('save', return_value=True)
    ctx.mock_method('delete', return_value=True)
    
    print(f"16.1 User ID: {mock_user.id}")
    print(f"16.1 User Name: {mock_user.name}")
    print(f"16.1 User save(): {mock_user.save()}")
    
    # Accessing undefined attribute fails - catches typos!
    try:
        _ = mock_user.nmae  # Typo: 'nmae' instead of 'name'
        assert False, "Should catch typo"
    except AttributeError:
        print("16.1 Strict mode caught typo 'nmae'")
    
    # Pattern 16.2: Mocking a configuration object with known keys
    mock_config = Mock(strict_attrs=True)
    config_ctx = mock_config.mock_context()
    
    config_ctx.set_attribute('host', 'localhost')
    config_ctx.set_attribute('port', 8080)
    config_ctx.set_attribute('debug', True)
    config_ctx.set_attribute('timeout', 30)
    
    print(f"16.2 Config host: {mock_config.host}")
    print(f"16.2 Config port: {mock_config.port}")
    
    # Pattern 16.3: Strict mock for API response validation
    mock_response = Mock(strict_attrs=True)
    response_ctx = mock_response.mock_context()
    
    response_ctx.set_attribute('status_code', 200)
    response_ctx.set_attribute('headers', {'Content-Type': 'application/json'})
    response_ctx.mock_method('json', return_value={'data': 'value'})
    response_ctx.mock_method('text', return_value='{"data": "value"}')
    
    print(f"16.3 Response status: {mock_response.status_code}")
    print(f"16.3 Response json: {mock_response.json()}")
    
    print("\n✓ Strict attributes real-world examples completed successfully!")


# =============================================================================
# SECTION 6: MAGIC METHODS AND SPECIAL BEHAVIORS
# =============================================================================

def example_magic_methods():
    """
    Demonstrates mock support for Python magic methods.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE: Magic Methods")
    print("=" * 70)
    
    # Example 17.1: __bool__ - truthiness
    mock = Mock()
    print(f"17.1 bool(Mock()): {bool(mock)}")  # True by default
    assert bool(mock) is True
    
    mock_with_value = Mock(return_value=0)
    print(f"17.1 bool(Mock(return_value=0)): {bool(mock_with_value)}")  # False
    assert bool(mock_with_value) is False
    
    mock_with_list = Mock(return_value=[1, 2, 3])
    print(f"17.1 bool(Mock(return_value=[1,2,3])): {bool(mock_with_list)}")  # True
    assert bool(mock_with_list) is True
    
    # Example 17.2: __len__ - length
    mock = Mock(return_value=[1, 2, 3, 4, 5])
    print(f"17.2 len(Mock(return_value=[1,2,3,4,5])): {len(mock)}")
    assert len(mock) == 5
    
    mock_str = Mock(return_value="hello")
    print(f"17.2 len(Mock(return_value='hello')): {len(mock_str)}")
    assert len(mock_str) == 5
    
    # Example 17.3: __iter__ - iteration
    mock = Mock(return_value=[1, 2, 3])
    items = list(mock)
    print(f"17.3 list(Mock(return_value=[1,2,3])): {items}")
    assert items == [1, 2, 3]
    
    # Iterate with for loop
    mock = Mock(return_value=['a', 'b', 'c'])
    result = []
    for item in mock:
        result.append(item)
    print(f"17.3 for loop iteration: {result}")
    
    # Example 17.4: __contains__ - membership testing
    mock = Mock(return_value=[1, 2, 3, 4, 5])
    print(f"17.4 3 in Mock(return_value=[1,2,3,4,5]): {3 in mock}")
    assert 3 in mock
    assert 10 not in mock
    
    mock_dict = Mock(return_value={'key1': 'value1', 'key2': 'value2'})
    print(f"17.4 'key1' in Mock(return_value=dict): {'key1' in mock_dict}")
    assert 'key1' in mock_dict
    
    # Example 17.5: __repr__ and __str__
    mock = Mock(return_value=42)
    print(f"17.5 repr(mock): {repr(mock)}")
    print(f"17.5 str(mock): {str(mock)}")
    
    # Example 17.6: __eq__ and __ne__ - equality
    mock1 = Mock(return_value=42, recursive=True)
    mock2 = Mock(return_value=42, recursive=True)
    mock3 = Mock(return_value=0, recursive=False)
    
    print(f"17.6 mock1 == mock2 (same config): {mock1 == mock2}")
    print(f"17.6 mock1 == mock3 (different config): {mock1 == mock3}")
    
    # Example 17.7: __hash__ - hashing
    mock = Mock()
    hash_value = hash(mock)
    print(f"17.7 hash(mock): {hash_value}")
    
    # Mocks can be used in sets and as dict keys
    mock_set = {mock}
    print(f"17.7 Mock in set: {mock in mock_set}")
    
    # Example 17.8: __dir__ - attribute listing
    mock = Mock()
    ctx = mock.mock_context()
    ctx.set_attribute('custom_attr', 'value')
    ctx.mock_method('custom_method', return_value=None)
    
    attrs = dir(mock)
    print(f"17.8 'custom_attr' in dir(mock): {'custom_attr' in attrs}")
    print(f"17.8 'custom_method' in dir(mock): {'custom_method' in attrs}")
    
    print("\n✓ Magic methods examples completed successfully!")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def run_all_examples():
    """
    Runs all mocking framework examples.
    """
    print("\n" + "=" * 70)
    print("TESTBASE MOCKING FRAMEWORK - COMPREHENSIVE EXAMPLES")
    print("=" * 70)
    
    # Section 1: Basic Mock Creation and Configuration
    example_basic_mock_creation()
    example_mock_call_tracking()
    example_mock_reset()
    
    # Section 2: Side Effect Usage Patterns
    example_basic_side_effects()
    example_side_effect_class()
    example_side_effect_patterns()
    
    # Section 3: Patch Context Manager Usage
    example_module_patching()
    example_class_patching()
    example_instance_patching()
    example_nested_patches()
    
    # Section 4: Recursive Mock Patterns
    example_recursive_mock_basics()
    example_recursive_mock_configuration()
    example_recursive_mock_real_world()
    
    # Section 5: Strict Attribute Mode Usage
    example_strict_attrs_basics()
    example_strict_attrs_with_methods()
    example_strict_attrs_inheritance()
    example_strict_attrs_real_world()
    
    # Section 6: Magic Methods
    example_magic_methods()
    
    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_examples()
