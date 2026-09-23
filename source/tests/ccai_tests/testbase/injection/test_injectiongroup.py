"""
    Unit tests for InjectionGroup class.

    Tests cover:
    - Group hierarchy construction (Requirements 11.1, 11.2, 11.3)
    - Metadata resolution and propagation (Requirements 12.1, 12.2, 12.3, 12.4)
    - Context manager protocol (Requirement 11.5)
    - Resource scope access (Requirement 11.4)
"""

import sys
import unittest

from ccai.errors.exceptions import SemanticError
from ccai.testbase.injection.injectiongroup import InjectionGroup
from ccai.testbase.injection.injectionmoment import InjectionMoment
from ccai.testbase.injection.injectionregistry import InjectionRegistry


def sample_test_function():
    """Sample function for creating InjectionMoment instances."""
    pass


def another_test_function():
    """Another sample function for testing."""
    pass


# Create a fake module with metadata for testing metadata resolution
class FakeModuleWithMetadata:
    _metadata_ = {"author": "test", "priority": "high"}


class FakeModuleNoMetadata:
    pass


class InjectionGroupHierarchyTests(unittest.TestCase):
    """Tests for group hierarchy construction (Requirements 11.1, 11.2, 11.3)."""

    def test_children_dictionary_maintained(self):
        """Requirement 11.1: InjectionGroup SHALL maintain a dictionary of child groups and moments."""
        group = InjectionGroup("root")
        self.assertIsInstance(group.children, dict)
        self.assertEqual(len(group.children), 0)

    def test_add_descendent_creates_intermediate_groups(self):
        """Requirement 11.2: WHEN adding a descendent, THE System SHALL create intermediate group nodes."""
        root = InjectionGroup("root")

        # Create an injection moment with a nested module path
        sample_test_function.__module__ = "pkg.subpkg.module"
        moment = InjectionMoment(sample_test_function)

        root.add_descendent(moment)

        # Verify intermediate groups were created
        self.assertIn("pkg", root.children)
        pkg_group = root.children["pkg"]
        self.assertIsInstance(pkg_group, InjectionGroup)

        self.assertIn("subpkg", pkg_group.children)
        subpkg_group = pkg_group.children["subpkg"]
        self.assertIsInstance(subpkg_group, InjectionGroup)

        self.assertIn("module", subpkg_group.children)
        module_group = subpkg_group.children["module"]
        self.assertIsInstance(module_group, InjectionGroup)

        # The moment should be at the leaf
        self.assertIn("sample_test_function", module_group.children)
        self.assertIs(module_group.children["sample_test_function"], moment)

    def test_add_descendent_on_non_root_raises_error(self):
        """Requirement 11.3: WHEN add_descendent is called on non-root group, SHALL raise SemanticError."""
        non_root = InjectionGroup("child", package="parent")

        sample_test_function.__module__ = "pkg.module"
        moment = InjectionMoment(sample_test_function)

        with self.assertRaises(SemanticError) as ctx:
            non_root.add_descendent(moment)

        self.assertIn("root package", str(ctx.exception))

    def test_add_multiple_descendents_shares_intermediate_groups(self):
        """Verify that multiple descendents share intermediate group nodes."""
        root = InjectionGroup("root")

        sample_test_function.__module__ = "pkg.module"
        another_test_function.__module__ = "pkg.module"

        moment1 = InjectionMoment(sample_test_function)
        moment2 = InjectionMoment(another_test_function)

        root.add_descendent(moment1)
        root.add_descendent(moment2)

        # Both should be under the same module group
        module_group = root.children["pkg"].children["module"]
        self.assertIn("sample_test_function", module_group.children)
        self.assertIn("another_test_function", module_group.children)


class InjectionGroupPropertiesTests(unittest.TestCase):
    """Tests for InjectionGroup properties."""

    def test_name_property(self):
        """Verify name property returns the group name."""
        group = InjectionGroup("mygroup")
        self.assertEqual(group.name, "mygroup")

    def test_package_property(self):
        """Verify package property returns the package path."""
        group = InjectionGroup("mygroup", package="parent.pkg")
        self.assertEqual(group.package, "parent.pkg")

    def test_package_property_none(self):
        """Verify package property returns None for root groups."""
        group = InjectionGroup("root")
        self.assertIsNone(group.package)

    def test_scope_name_with_package(self):
        """Verify scope_name combines package and name."""
        group = InjectionGroup("module", package="pkg.subpkg")
        self.assertEqual(group.scope_name, "pkg.subpkg.module")

    def test_scope_name_without_package(self):
        """Verify scope_name returns just name when no package."""
        group = InjectionGroup("root")
        self.assertEqual(group.scope_name, "root")

    def test_finalized_property(self):
        """Verify finalized property tracks finalization state."""
        group = InjectionGroup("test")
        self.assertFalse(group.finalized)
        group.finalize()
        self.assertTrue(group.finalized)


class InjectionGroupContextManagerTests(unittest.TestCase):
    """Tests for context manager protocol (Requirement 11.5)."""

    def test_context_manager_enter_returns_self(self):
        """Requirement 11.5: InjectionGroup SHALL support context manager protocol."""
        group = InjectionGroup("test")

        with group as ctx:
            self.assertIs(ctx, group)

    def test_context_manager_exit_returns_false(self):
        """Verify context manager exit returns False to propagate exceptions."""
        group = InjectionGroup("test")

        result = group.__exit__(None, None, None)
        self.assertFalse(result)

    def test_context_manager_propagates_exceptions(self):
        """Verify exceptions are propagated through context manager."""
        group = InjectionGroup("test")

        with self.assertRaises(ValueError):
            with group:
                raise ValueError("test error")


class InjectionGroupResourceScopeTests(unittest.TestCase):
    """Tests for resource scope access (Requirement 11.4)."""

    def setUp(self):
        """Reset the InjectionRegistry singleton for test isolation."""
        InjectionRegistry._instance = None
        InjectionRegistry._initialized = False
        self.registry = InjectionRegistry()

    def test_get_resource_scope_returns_scope(self):
        """Requirement 11.4: InjectionGroup SHALL provide access to its associated resource scope."""
        # The root scope is always available as '<session>'
        group = InjectionGroup("<session>")
        scope = group.get_resource_scope()
        self.assertIsNotNone(scope)

    def test_get_resource_scope_returns_none_for_nonexistent(self):
        """Verify get_resource_scope returns None for non-existent scopes."""
        group = InjectionGroup("nonexistent", package="fake.path")
        scope = group.get_resource_scope()
        self.assertIsNone(scope)


class InjectionGroupMetadataTests(unittest.TestCase):
    """Tests for metadata resolution and propagation (Requirements 12.1, 12.2, 12.3, 12.4)."""

    def setUp(self):
        """Set up test fixtures."""
        # Store original modules to restore later
        self._original_modules = dict(sys.modules)

    def tearDown(self):
        """Restore original sys.modules state."""
        # Remove any test modules we added
        for key in list(sys.modules.keys()):
            if key not in self._original_modules:
                del sys.modules[key]

    def test_resolve_metadata_from_module(self):
        """Requirement 12.1: WHEN resolving metadata, SHALL check module for _metadata_ attribute."""
        # Register a fake module with metadata
        sys.modules["testmod"] = FakeModuleWithMetadata()

        group = InjectionGroup("testmod")
        group.resolve_metadata()

        self.assertEqual(group._metadata, {"author": "test", "priority": "high"})

    def test_resolve_metadata_merges_parent(self):
        """Requirement 12.2: WHEN parent metadata exists, SHALL merge with group's reference metadata."""
        sys.modules["childmod"] = FakeModuleWithMetadata()

        parent_metadata = {"env": "test", "author": "parent"}
        group = InjectionGroup("childmod")
        group.resolve_metadata(parent_metadata)

        # Child metadata should override parent for 'author'
        self.assertEqual(group._metadata["author"], "test")
        # Parent metadata should be preserved for 'env'
        self.assertEqual(group._metadata["env"], "test")
        # Child metadata should be included
        self.assertEqual(group._metadata["priority"], "high")

    def test_resolve_metadata_child_overrides_parent(self):
        """Requirement 12.3: WHEN merging metadata, child metadata SHALL override parent metadata."""
        sys.modules["overridemod"] = FakeModuleWithMetadata()

        parent_metadata = {"author": "parent_author", "version": "1.0"}
        group = InjectionGroup("overridemod")
        group.resolve_metadata(parent_metadata)

        # Child's 'author' should override parent's
        self.assertEqual(group._metadata["author"], "test")
        # Parent's 'version' should be preserved
        self.assertEqual(group._metadata["version"], "1.0")

    def test_resolve_metadata_propagates_to_children(self):
        """Requirement 12.4: THE System SHALL propagate resolved metadata to all child groups."""
        root = InjectionGroup("root")

        # Create a child group manually
        child = InjectionGroup("child", package="root")
        root._children["child"] = child

        # Create a grandchild moment
        sample_test_function.__module__ = "root.child"
        sample_test_function._metadata_ = {"func_meta": "value"}
        moment = InjectionMoment(sample_test_function)
        child._children["sample_test_function"] = moment

        # Resolve metadata from root with parent metadata
        parent_metadata = {"root_key": "root_value"}
        root.resolve_metadata(parent_metadata)

        # Child should have inherited metadata
        self.assertEqual(child._metadata, parent_metadata)

        # Moment should have inherited and merged metadata
        self.assertIn("root_key", moment._metadata)
        self.assertIn("func_meta", moment._metadata)

    def test_resolve_metadata_no_module_metadata(self):
        """Verify resolve_metadata handles modules without _metadata_ attribute."""
        sys.modules["nomd"] = FakeModuleNoMetadata()

        group = InjectionGroup("nomd")
        group.resolve_metadata()

        self.assertIsNone(group._metadata)

    def test_resolve_metadata_parent_only(self):
        """Verify parent metadata is used when module has no metadata."""
        sys.modules["parentonly"] = FakeModuleNoMetadata()

        parent_metadata = {"inherited": "value"}
        group = InjectionGroup("parentonly")
        group.resolve_metadata(parent_metadata)

        self.assertEqual(group._metadata, parent_metadata)

    def test_resolve_metadata_nonexistent_module(self):
        """Verify resolve_metadata handles non-existent modules gracefully."""
        group = InjectionGroup("nonexistent_module_xyz")
        group.resolve_metadata()

        self.assertIsNone(group._metadata)


class InjectionGroupContainerProtocolTests(unittest.TestCase):
    """Tests for container protocol methods (__contains__, __getitem__, __setitem__)."""

    def test_contains_returns_true_for_existing_child(self):
        """Verify __contains__ returns True for existing children."""
        group = InjectionGroup("test")
        group._children["child"] = InjectionGroup("child", package="test")

        self.assertIn("child", group)

    def test_contains_returns_false_for_missing_child(self):
        """Verify __contains__ returns False for missing children."""
        group = InjectionGroup("test")

        self.assertNotIn("nonexistent", group)

    def test_getitem_returns_child(self):
        """Verify __getitem__ returns the child object."""
        group = InjectionGroup("test")
        child = InjectionGroup("child", package="test")
        group._children["child"] = child

        self.assertIs(group["child"], child)

    def test_getitem_raises_keyerror_for_missing(self):
        """Verify __getitem__ raises KeyError for missing children."""
        group = InjectionGroup("test")

        with self.assertRaises(KeyError):
            _ = group["nonexistent"]

    def test_setitem_adds_child(self):
        """Verify __setitem__ adds a child to the group."""
        group = InjectionGroup("test")
        child = InjectionGroup("child", package="test")

        group["child"] = child

        self.assertIn("child", group._children)
        self.assertIs(group._children["child"], child)


if __name__ == "__main__":
    unittest.main()
