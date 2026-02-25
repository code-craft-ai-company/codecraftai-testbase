import unittest
from automojo.testbase.constraints import (
    Constraints,
    FeatureConstraints,
    create_constraint_key,
    merge_constraints,
    ConstraintsCatalog,
    ConstraintsOrigin,
    ConstraintsRef,
)


class CreateConstraintKeyTests(unittest.TestCase):
    def test_creates_expected_format(self):
        self.assertEqual(create_constraint_key('scope', 'id'), 'scope:id')


class MergeConstraintsTests(unittest.TestCase):
    def test_merge_overwrites_later_values(self):
        c1 = Constraints(a=1, b=2)
        c2 = {'b': 3, 'c': 4}
        merged = merge_constraints(c1, c2)
        self.assertIsInstance(merged, Constraints)
        self.assertEqual(merged['a'], 1)
        self.assertEqual(merged['b'], 3)
        self.assertEqual(merged['c'], 4)

    def test_merge_with_no_arguments_returns_empty_constraints(self):
        """Test merge with no arguments returns empty Constraints (Requirement 11.4)."""
        merged = merge_constraints()
        self.assertIsInstance(merged, Constraints)
        self.assertEqual(len(merged), 0)


class ConstraintsCallTests(unittest.TestCase):
    def test_constraints_call_returns_new_dict(self):
        cons = Constraints(alpha=1)
        result = cons(beta=2)
        self.assertIsInstance(result, dict)
        self.assertNotEqual(id(result), id(cons))
        self.assertEqual(result['alpha'], 1)
        self.assertEqual(result['beta'], 2)


class FeatureConstraintsTests(unittest.TestCase):
    def test_call_extends_dict(self):
        fc = FeatureConstraints(required_features=['r'], excluded_features=['e'])
        updated = fc(extra=True)
        self.assertEqual(updated['required_features'], ['r'])
        self.assertEqual(updated['excluded_features'], ['e'])
        self.assertTrue(updated['extra'])

    def test_init_with_required_features_only(self):
        """Test FeatureConstraints initialization with required_features only."""
        required = ['feature_a', 'feature_b']
        fc = FeatureConstraints(required_features=required)

        self.assertEqual(fc['required_features'], required)
        self.assertIsNone(fc['excluded_features'])
        self.assertFalse(fc['checkout'])

    def test_init_with_excluded_features_only(self):
        """Test FeatureConstraints initialization with excluded_features only."""
        excluded = ['feature_x', 'feature_y']
        fc = FeatureConstraints(excluded_features=excluded)

        self.assertIsNone(fc['required_features'])
        self.assertEqual(fc['excluded_features'], excluded)
        self.assertFalse(fc['checkout'])

    def test_init_with_checkout_true(self):
        """Test FeatureConstraints initialization with checkout=True."""
        fc = FeatureConstraints(checkout=True)

        self.assertIsNone(fc['required_features'])
        self.assertIsNone(fc['excluded_features'])
        self.assertTrue(fc['checkout'])

    def test_init_with_additional_kwargs(self):
        """Test FeatureConstraints initialization with additional keyword arguments."""
        required = ['feature_a']
        excluded = ['feature_b']
        fc = FeatureConstraints(
            required_features=required,
            excluded_features=excluded,
            checkout=True,
            custom_param='custom_value',
            another_param=42
        )

        self.assertEqual(fc['required_features'], required)
        self.assertEqual(fc['excluded_features'], excluded)
        self.assertTrue(fc['checkout'])
        self.assertEqual(fc['custom_param'], 'custom_value')
        self.assertEqual(fc['another_param'], 42)


class ConstraintsCatalogTests(unittest.TestCase):
    def setUp(self):
        ConstraintsCatalog._instance = None
        ConstraintsCatalog._initialized = False
        self.catalog = ConstraintsCatalog()

    def test_add_constraints_raises_valueerror_for_invalid_origin(self):
        """Test that add_constraints raises ValueError for invalid origin."""
        invalid_origin = "invalid-origin"
        test_scope = "test_scope"
        test_identifier = "test_id"
        test_constraints = Constraints(value="test")

        with self.assertRaises(ValueError) as context:
            self.catalog.add_constraints(
                invalid_origin, test_scope, test_identifier, test_constraints
            )

        error_message = str(context.exception)
        self.assertIn(invalid_origin, error_message)
        self.assertIn(test_scope, error_message)
        self.assertIn(test_identifier, error_message)

    def test_add_constraints_valueerror_message_format(self):
        """Verify error message contains origin, scope, and identifier."""
        invalid_origin = "unknown-source"
        scope = "my.test.scope"
        identifier = "config_id"
        constraints = Constraints(key="value")

        with self.assertRaises(ValueError) as context:
            self.catalog.add_constraints(
                invalid_origin, scope, identifier, constraints
            )

        error_message = str(context.exception)
        # Verify all three components are present in the error message
        self.assertIn(f"origin='{invalid_origin}'", error_message)
        self.assertIn(f"scope='{scope}'", error_message)
        self.assertIn(f"identifier={identifier}", error_message)

    def test_singleton_returns_same_instance(self):
        """Test that multiple ConstraintsCatalog() calls return the same instance."""
        catalog1 = ConstraintsCatalog()
        catalog2 = ConstraintsCatalog()
        catalog3 = ConstraintsCatalog()

        self.assertIs(catalog1, catalog2)
        self.assertIs(catalog2, catalog3)
        self.assertIs(catalog1, self.catalog)

    def test_storage_tables_initialized_only_once(self):
        """Test that storage tables are initialized only once across multiple instantiations."""
        # Add constraints to the first catalog instance
        self.catalog.add_constraints(
            ConstraintsOrigin.SITE_PARAMETER, 'test_scope', 'test_id', Constraints(value='test')
        )

        # Create additional catalog instances
        catalog2 = ConstraintsCatalog()
        catalog3 = ConstraintsCatalog()

        # Verify all instances share the same storage tables
        self.assertIs(self.catalog._site_constraints, catalog2._site_constraints)
        self.assertIs(catalog2._site_constraints, catalog3._site_constraints)

        # Verify the constraint added via first instance is visible in all instances
        self.assertIn('test_scope:test_id', catalog2._site_constraints)
        self.assertIn('test_scope:test_id', catalog3._site_constraints)

        # Verify _initialized flag remains True
        self.assertTrue(ConstraintsCatalog._initialized)

    def test_add_and_lookup(self):
        c_site = Constraints(val='site')
        c_over = Constraints(val='override')
        key = self.catalog.add_constraints(
            ConstraintsOrigin.SITE_PARAMETER, 'myscope', 'cid', c_site
        )
        self.catalog.add_constraints(
            ConstraintsOrigin.OVERRIDE_PARAMETER, 'myscope', 'cid', c_over
        )

        looked = self.catalog.lookup_constraints(key)
        self.assertIs(looked, c_over)

    def test_prune_constraints(self):
        self.catalog.add_constraints(
            ConstraintsOrigin.SITE_PARAMETER, 'keep', 'k', Constraints()
        )
        self.catalog.add_constraints(
            ConstraintsOrigin.SITE_PARAMETER, 'drop', 'd', Constraints()
        )
        self.catalog.prune_constraints(['keep:k'])
        self.assertIn('keep:k', self.catalog._site_constraints)
        self.assertNotIn('drop:d', self.catalog._site_constraints)

    def test_lookup_constraints_returns_none_for_nonexistent_key(self):
        """Test lookup with non-existent key returns None."""
        result = self.catalog.lookup_constraints('nonexistent:key')
        self.assertIsNone(result)

    def test_lookup_constraints_returns_none_after_pruning_removes_key(self):
        """Test lookup after pruning removes key returns None."""
        # Add constraints to both site and override tables
        self.catalog.add_constraints(
            ConstraintsOrigin.SITE_PARAMETER, 'scope_to_prune', 'id', Constraints(val='site')
        )
        self.catalog.add_constraints(
            ConstraintsOrigin.OVERRIDE_PARAMETER, 'scope_to_prune', 'id', Constraints(val='override')
        )

        # Verify constraints exist before pruning
        key = 'scope_to_prune:id'
        self.assertIsNotNone(self.catalog.lookup_constraints(key))

        # Prune with empty list to remove all constraints
        self.catalog.prune_constraints([])

        # Verify lookup returns None after pruning
        result = self.catalog.lookup_constraints(key)
        self.assertIsNone(result)


class ConstraintsRefTests(unittest.TestCase):
    def test_property_accessors(self):
        cons = Constraints(x=1)
        cref = ConstraintsRef(
            ConstraintsOrigin.SITE_PARAMETER, 'scope', 'id', cons
        )
        self.assertIs(cref.constraints, cons)
        self.assertEqual(cref.identifier, 'id')
        self.assertEqual(cref.origin, ConstraintsOrigin.SITE_PARAMETER)
        self.assertEqual(cref.originating_scope, 'scope')


class ConstraintsOriginStringComparisonTests(unittest.TestCase):
    """Tests for ConstraintsOrigin string comparison (Requirement 2.4)."""

    def test_site_parameter_equals_string_value(self):
        """Test SITE_PARAMETER enum equals its string value."""
        self.assertEqual(ConstraintsOrigin.SITE_PARAMETER, "site-parameter")

    def test_override_parameter_equals_string_value(self):
        """Test OVERRIDE_PARAMETER enum equals its string value."""
        self.assertEqual(ConstraintsOrigin.OVERRIDE_PARAMETER, "override-parameter")

    def test_site_parameter_equals_enum_value(self):
        """Test SITE_PARAMETER enum equals itself."""
        self.assertEqual(ConstraintsOrigin.SITE_PARAMETER, ConstraintsOrigin.SITE_PARAMETER)

    def test_override_parameter_equals_enum_value(self):
        """Test OVERRIDE_PARAMETER enum equals itself."""
        self.assertEqual(ConstraintsOrigin.OVERRIDE_PARAMETER, ConstraintsOrigin.OVERRIDE_PARAMETER)

    def test_site_parameter_not_equals_wrong_string(self):
        """Test SITE_PARAMETER does not equal incorrect string."""
        self.assertNotEqual(ConstraintsOrigin.SITE_PARAMETER, "override-parameter")
        self.assertNotEqual(ConstraintsOrigin.SITE_PARAMETER, "invalid")

    def test_override_parameter_not_equals_wrong_string(self):
        """Test OVERRIDE_PARAMETER does not equal incorrect string."""
        self.assertNotEqual(ConstraintsOrigin.OVERRIDE_PARAMETER, "site-parameter")
        self.assertNotEqual(ConstraintsOrigin.OVERRIDE_PARAMETER, "invalid")

    def test_enum_inherits_from_str(self):
        """Test ConstraintsOrigin inherits from str for string compatibility."""
        self.assertIsInstance(ConstraintsOrigin.SITE_PARAMETER, str)
        self.assertIsInstance(ConstraintsOrigin.OVERRIDE_PARAMETER, str)

    def test_string_comparison_in_conditional(self):
        """Test enum can be used in conditional with string comparison."""
        origin = ConstraintsOrigin.SITE_PARAMETER
        if origin == "site-parameter":
            result = True
        else:
            result = False
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
