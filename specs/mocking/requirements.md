# Mocking Framework - Requirements Document

## Introduction

The Mocking Framework provides a comprehensive system for creating mock objects, managing mock contexts, and patching modules, classes, and instances during test execution. It enables test isolation by replacing real dependencies with configurable mock objects that can track calls, return predetermined values, and execute side effects. The framework is designed to be lightweight, intuitive, and fully integrated with the TestBase testing ecosystem while providing familiar patterns for developers experienced with Python's `unittest.mock` module.

## Glossary

- **Mock**: A configurable object that simulates the behavior of real objects, tracking calls and returning predetermined values
- **MockContext**: An internal class that stores all state and configuration for a mock object including call tracking, return values, and side effects
- **MockType**: An enumeration defining the type of mock object (Generic, Class, Instance, Property, Function, Method)
- **SideEffect**: A callable wrapper that executes when a mock is invoked, optionally with default arguments
- **Patch**: A context manager that temporarily replaces an attribute on a module, class, or instance with a mock object
- **PatchType**: An enumeration defining the type of target being patched (Module, Class, Instance)
- **Call_Tracking**: The mechanism by which mocks record invocation details including arguments and call count
- **Recursive_Mock**: A mock configured to automatically create child mocks for undefined attribute access
- **Strict_Attrs_Mode**: A mock configuration that restricts attribute access to only pre-defined attributes
- **Child_Mock**: A mock object created as an attribute of another mock, maintaining a reference to its parent

## Requirements

### Requirement 1: Mock Object Creation

**User Story:** As a test developer, I want to create mock objects with configurable behavior, so that I can simulate dependencies and isolate the code under test.

#### Acceptance Criteria

1. WHEN a Mock is instantiated without parameters, THE Mock SHALL be created with MockType.Generic and default configuration
2. WHEN a Mock is instantiated with a reference parameter, THE Mock SHALL determine the appropriate MockType from the reference object
3. WHEN a Mock is instantiated with an explicit mtype parameter, THE Mock SHALL use the specified MockType regardless of reference
4. WHEN a Mock is instantiated with mock_attributes parameter, THE Mock SHALL store the provided attributes dictionary
5. WHEN a Mock is instantiated with return_value parameter, THE Mock SHALL return that value when called
6. WHEN a Mock is instantiated with side_effect parameter, THE Mock SHALL execute the side effect when called
7. WHEN a Mock is instantiated with recursive=True, THE Mock SHALL create child mocks for undefined attribute access
8. WHEN a Mock is instantiated with strict_attrs=True, THE Mock SHALL restrict attribute access to pre-defined attributes only

### Requirement 2: Mock Type Determination

**User Story:** As a test developer, I want mock types to be automatically determined from reference objects, so that mocks accurately represent the type of object being mocked.

#### Acceptance Criteria

1. WHEN determine_mock_type is called with a property object, THE MockContext SHALL return MockType.Property
2. WHEN determine_mock_type is called with a function, THE MockContext SHALL return MockType.Function
3. WHEN determine_mock_type is called with a method, THE MockContext SHALL return MockType.Method
4. WHEN determine_mock_type is called with a class, THE MockContext SHALL return MockType.Class
5. WHEN determine_mock_type is called with an object instance, THE MockContext SHALL return MockType.Instance
6. WHEN determine_mock_type is called with None or no reference, THE MockContext SHALL return MockType.Generic

### Requirement 3: Mock Invocation and Return Values

**User Story:** As a test developer, I want mocks to return configured values when called, so that I can control the behavior of mocked dependencies.

#### Acceptance Criteria

1. WHEN a Mock is called and return_value is configured, THE Mock SHALL return the configured return_value
2. WHEN a Mock is called and side_effect is configured, THE Mock SHALL execute the side_effect and return its result
3. WHEN a Mock is called with both return_value and side_effect configured, THE Mock SHALL execute the side_effect and return its result
4. WHEN a Mock is called without return_value or side_effect configured, THE Mock SHALL return None
5. WHEN a Mock is called, THE Mock SHALL record the call arguments for later verification

### Requirement 4: Side Effect Execution

**User Story:** As a test developer, I want to configure side effects on mocks, so that I can execute custom logic when mocks are invoked.

#### Acceptance Criteria

1. WHEN a SideEffect is instantiated with a callable, THE SideEffect SHALL store the callable for later execution
2. WHEN a SideEffect is called with arguments, THE SideEffect SHALL pass those arguments to the wrapped callable
3. WHEN a SideEffect is called without arguments and default_args is configured, THE SideEffect SHALL use the default_args
4. WHEN a SideEffect is called without keyword arguments and default_kwargs is configured, THE SideEffect SHALL use the default_kwargs
5. WHEN a callable is provided as side_effect to Mock, THE Mock SHALL wrap it in a SideEffect instance
6. IF a non-callable, non-SideEffect value is provided as side_effect, THEN THE Mock SHALL raise a TypeError

### Requirement 5: Call Tracking

**User Story:** As a test developer, I want mocks to track all calls made to them, so that I can verify interactions with mocked dependencies.

#### Acceptance Criteria

1. WHEN a Mock is called, THE MockContext SHALL increment the call_count by one
2. WHEN a Mock is called, THE MockContext SHALL store the call arguments as a tuple (args, kwargs) in call_args
3. WHEN a Mock is called multiple times, THE MockContext SHALL append each call to call_args_list
4. WHEN call_args is accessed, THE MockContext SHALL return the arguments from the most recent call
5. WHEN call_args_list is accessed, THE MockContext SHALL return a list of all calls in order
6. WHEN mock_calls is accessed, THE MockContext SHALL return a list of calls including child mock calls

### Requirement 6: Call Assertion Methods

**User Story:** As a test developer, I want assertion methods on mocks, so that I can verify expected interactions occurred during test execution.

#### Acceptance Criteria

1. WHEN assert_called is invoked on a Mock that was called at least once, THE MockContext SHALL return without raising an exception
2. WHEN assert_called is invoked on a Mock that was never called, THE MockContext SHALL raise an AssertionError
3. WHEN assert_called_once is invoked on a Mock that was called exactly once, THE MockContext SHALL return without raising an exception
4. WHEN assert_called_once is invoked on a Mock that was not called exactly once, THE MockContext SHALL raise an AssertionError with the actual call count
5. WHEN assert_called_with is invoked with arguments matching the last call, THE MockContext SHALL return without raising an exception
6. WHEN assert_called_with is invoked with arguments not matching the last call, THE MockContext SHALL raise an AssertionError with expected and actual arguments
7. WHEN assert_called_once_with is invoked on a Mock called exactly once with matching arguments, THE MockContext SHALL return without raising an exception
8. WHEN assert_any_call is invoked with arguments matching any recorded call, THE MockContext SHALL return without raising an exception
9. WHEN assert_any_call is invoked with arguments not matching any recorded call, THE MockContext SHALL raise an AssertionError
10. WHEN assert_has_calls is invoked with a call sequence present in call history, THE MockContext SHALL return without raising an exception
11. WHEN assert_has_calls is invoked with any_order=True, THE MockContext SHALL verify all expected calls exist regardless of order

### Requirement 7: Mock Configuration

**User Story:** As a test developer, I want to configure mock behavior after creation, so that I can adjust mock settings during test setup.

#### Acceptance Criteria

1. WHEN configure is called with return_value, THE MockContext SHALL update the return_value setting
2. WHEN configure is called with side_effect, THE MockContext SHALL update the side_effect setting
3. WHEN configure is called with recursive, THE MockContext SHALL update the recursive setting
4. WHEN configure is called with strict_attrs, THE MockContext SHALL update the strict_attrs setting
5. WHEN configure is called, THE Mock SHALL return itself for fluent method chaining
6. WHEN return_value is set via attribute assignment on Mock, THE MockContext SHALL update the return_value setting
7. WHEN side_effect is set via attribute assignment on Mock, THE MockContext SHALL update the side_effect setting

### Requirement 8: Mock Reset

**User Story:** As a test developer, I want to reset mock state between tests, so that I can reuse mocks without interference from previous test executions.

#### Acceptance Criteria

1. WHEN reset is called on MockContext, THE MockContext SHALL set return_value to None
2. WHEN reset is called on MockContext, THE MockContext SHALL set side_effect to None
3. WHEN reset is called on MockContext, THE MockContext SHALL set call_count to zero
4. WHEN reset is called on MockContext, THE MockContext SHALL clear call_args to None
5. WHEN reset is called on MockContext, THE MockContext SHALL clear call_args_list to an empty list
6. WHEN reset is called on MockContext, THE MockContext SHALL clear mock_calls to an empty list

### Requirement 9: Attribute Access on Mocks

**User Story:** As a test developer, I want to access and set attributes on mocks, so that I can simulate object properties and nested structures.

#### Acceptance Criteria

1. WHEN an attribute is accessed on a Mock and the attribute exists in mock_attributes, THE Mock SHALL return the stored attribute value
2. WHEN an attribute is accessed on a Mock with recursive=True and the attribute does not exist, THE Mock SHALL create and return a new child Mock
3. WHEN an attribute is accessed on a Mock with recursive=False and the attribute does not exist, THE Mock SHALL raise an AttributeError
4. WHEN an attribute is accessed on a Mock with strict_attrs=True and the attribute does not exist, THE Mock SHALL raise an AttributeError
5. WHEN an attribute starting with underscore is accessed, THE Mock SHALL raise an AttributeError
6. WHEN an assertion method name is accessed, THE Mock SHALL return the corresponding method from MockContext
7. WHEN an attribute is set on a Mock, THE MockContext SHALL store the value in mock_attributes
8. WHEN an attribute is set on a Mock with strict_attrs=True and the attribute is not pre-defined, THE Mock SHALL raise an AttributeError

### Requirement 10: Mock Method and Property Creation

**User Story:** As a test developer, I want to create mock methods and properties on mocks, so that I can simulate complex object interfaces.

#### Acceptance Criteria

1. WHEN mock_method is called on MockContext, THE MockContext SHALL create a new Mock with MockType.Method
2. WHEN mock_method is called with return_value, THE created Mock SHALL be configured with that return_value
3. WHEN mock_method is called with side_effect, THE created Mock SHALL be configured with that side_effect
4. WHEN mock_method is called, THE MockContext SHALL store the created Mock in mock_attributes under the given name
5. WHEN mock_property is called on MockContext, THE MockContext SHALL create a new Mock with MockType.Property
6. WHEN mock_property is called, THE MockContext SHALL store the created Mock in mock_attributes under the given name
7. WHEN a child Mock is created, THE child Mock SHALL inherit recursive and strict_attrs settings from the parent

### Requirement 11: Mock Magic Methods

**User Story:** As a test developer, I want mocks to support Python magic methods, so that mocks can be used in contexts requiring specific protocols.

#### Acceptance Criteria

1. WHEN __bool__ is called on a Mock with return_value set, THE Mock SHALL return bool(return_value)
2. WHEN __bool__ is called on a Mock without return_value set, THE Mock SHALL return True
3. WHEN __len__ is called on a Mock with return_value supporting len(), THE Mock SHALL return len(return_value)
4. WHEN __len__ is called on a Mock without return_value set, THE Mock SHALL raise a TypeError
5. WHEN __iter__ is called on a Mock with iterable return_value, THE Mock SHALL return iter(return_value)
6. WHEN __iter__ is called on a Mock without return_value set, THE Mock SHALL raise a TypeError
7. WHEN __contains__ is called on a Mock with container return_value, THE Mock SHALL check if item is in return_value
8. WHEN __contains__ is called on a Mock without return_value set, THE Mock SHALL raise a TypeError
9. WHEN __dir__ is called on a Mock, THE Mock SHALL return a sorted list including mock_attributes keys
10. WHEN __repr__ is called on a Mock, THE Mock SHALL return a string representation including return_value and side_effect
11. WHEN __eq__ is called comparing two Mocks, THE Mock SHALL compare return_value, side_effect, recursive, strict_attrs, mock_type, and mock_attributes
12. WHEN __hash__ is called on a Mock, THE Mock SHALL return a hash based on object identity

### Requirement 12: Patch Creation

**User Story:** As a test developer, I want to create patches for modules, classes, and instances, so that I can temporarily replace attributes with mocks.

#### Acceptance Criteria

1. WHEN create_module_patch is called with a module and target_name, THE function SHALL return a Patch with PatchType.Module
2. WHEN create_class_patch is called with a class and target_name, THE function SHALL return a Patch with PatchType.Class
3. WHEN create_instance_patch is called with an instance and target_name, THE function SHALL return a Patch with PatchType.Instance
4. IF create_module_patch is called with a non-module owner, THEN THE function SHALL raise a TypeError
5. IF create_class_patch is called with a non-class owner, THEN THE function SHALL raise a TypeError
6. IF create_instance_patch is called with a non-object owner, THEN THE function SHALL raise a TypeError
7. IF target_name is not a string, THEN THE factory function SHALL raise a TypeError
8. WHEN a Patch is created with recursive=True, THE Patch SHALL create recursive mocks
9. WHEN a Patch is created with strict_attrs=True, THE Patch SHALL create strict attribute mocks

### Requirement 13: Patch Activation and Deactivation

**User Story:** As a test developer, I want to activate and deactivate patches, so that I can control when mocks replace real objects.

#### Acceptance Criteria

1. WHEN activate is called on a Patch, THE Patch SHALL replace the target attribute with a Mock
2. WHEN activate is called on a Patch, THE Patch SHALL return the Mock object
3. WHEN activate is called and the target is already a Mock from this framework, THE Patch SHALL raise a ValueError
4. WHEN deactivate is called on a Patch, THE Patch SHALL restore the original attribute value
5. WHEN deactivate is called on a Patch that was never activated, THE Patch SHALL return without error
6. WHEN mock is called on a Patch before activation, THE Patch SHALL create and return a Mock with the target as reference

### Requirement 14: Patch Context Manager

**User Story:** As a test developer, I want to use patches as context managers, so that I can ensure automatic cleanup of patches after test execution.

#### Acceptance Criteria

1. WHEN a Patch is used as a context manager, THE Patch SHALL activate on entering the context
2. WHEN a Patch context is entered, THE Patch SHALL return the Mock object
3. WHEN a Patch context is exited normally, THE Patch SHALL deactivate and restore the original attribute
4. WHEN a Patch context is exited due to an exception, THE Patch SHALL deactivate and restore the original attribute
5. WHEN a Patch context is exited due to an exception, THE Patch SHALL not suppress the exception

### Requirement 15: Patch Type Validation

**User Story:** As a framework developer, I want patch types to be validated against owner types, so that users receive clear error messages for mismatched configurations.

#### Acceptance Criteria

1. IF a Patch is created with a class owner and PatchType is not Class, THEN THE Patch SHALL raise a TypeError
2. IF a Patch is created with a module owner and PatchType is not Module, THEN THE Patch SHALL raise a TypeError
3. IF a Patch is created with an instance owner and PatchType is not Instance, THEN THE Patch SHALL raise a TypeError
4. THE error message SHALL indicate the expected PatchType for the given owner type

### Requirement 16: Weak Reference Management

**User Story:** As a framework developer, I want mock contexts to use weak references, so that circular references do not cause memory leaks.

#### Acceptance Criteria

1. WHEN a MockContext is created, THE MockContext SHALL store a weak reference to the Mock
2. WHEN a MockContext is created with a mock_owner, THE MockContext SHALL store a weak reference to the owner
3. WHEN get_mock is called on MockContext, THE MockContext SHALL dereference and return the Mock
4. WHEN get_mock_owner is called on MockContext, THE MockContext SHALL dereference and return the owner or None
