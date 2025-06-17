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


class ConstraintsCatalogTests(unittest.TestCase):
    def setUp(self):
        ConstraintsCatalog._instance = None
        ConstraintsCatalog._initialized = False
        self.catalog = ConstraintsCatalog()

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


if __name__ == '__main__':
    unittest.main()
