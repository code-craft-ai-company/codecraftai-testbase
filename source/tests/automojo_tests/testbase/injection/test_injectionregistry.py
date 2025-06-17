import unittest

from automojo.testbase.injection.injectionregistry import InjectionRegistry
from automojo.testbase.origins.resourceorigin import ResourceOrigin
from automojo.testbase.resourcelifespan import ResourceLifespan


class InjectionRegistryTests(unittest.TestCase):

    def setUp(self):
        InjectionRegistry._instance = None
        InjectionRegistry._initialized = False
        self.registry = InjectionRegistry()

    def test_add_implied_session_resource(self):
        self.registry.add_implied_session_resource('myres')
        scope = self.registry.lookup_resource_scope('<session>')
        self.assertIn('myres', scope.parameter_originations)
        origin = scope.parameter_originations['myres']
        self.assertEqual(origin.originating_scope, '<session>')
        self.assertTrue(origin.implied)

    def test_rename_resource_origins_from_main(self):
        origin = ResourceOrigin('__main__#func', 'id', ResourceLifespan.Test)
        self.registry.register_resource_origin('id', origin)
        self.registry.rename_resource_origins_from_main('pkg.mod')

        self.assertEqual(origin.originating_scope, 'pkg.mod#func')
        scope = self.registry.lookup_resource_scope('pkg.mod')
        self.assertIsNotNone(scope)
        self.assertIn('func', scope.children)
        self.assertIn('id', scope.children['func'].parameter_originations)
        self.assertIs(scope.children['func'].parameter_originations['id'], origin)
        self.assertIsNone(self.registry.lookup_resource_scope('__main'))


if __name__ == '__main__':
    unittest.main()
