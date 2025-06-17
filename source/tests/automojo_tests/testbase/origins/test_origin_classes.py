import inspect
import unittest

from automojo.testbase.origins.resourceorigin import ResourceOrigin, constraints_catalog
from automojo.testbase.origins.validatororigin import ValidatorOrigin
from automojo.testbase.sources.sourcebase import SourceBase
from automojo.testbase.resourcelifespan import ResourceLifespan


class OriginBaseTest(unittest.TestCase):
    def setUp(self):
        constraints_catalog._site_constraints.clear()
        constraints_catalog._override_constraints.clear()

        def dummy_query():
            return True

        def dummy_source(a, b, constraints=None):
            return a, b, constraints

        self.func = dummy_source
        self.source = SourceBase(dummy_source, dummy_query, int, {})


class ResourceOriginTests(OriginBaseTest):
    def test_properties_without_constraints(self):
        origin = ResourceOrigin(
            "scope",
            "ident",
            ResourceLifespan.Session,
            source=self.source,
            implied=True,
        )

        expected_id = f"{self.func.__module__}#{self.func.__name__}"
        self.assertIsNone(origin.constraints_key)
        self.assertEqual(origin.identifier, "ident")
        self.assertTrue(origin.implied)
        self.assertEqual(origin.life_span, ResourceLifespan.Session)
        self.assertEqual(origin.originating_scope, "scope")
        self.assertIs(origin.source_function, self.func)
        self.assertEqual(origin.source_function_name, self.func.__name__)
        self.assertEqual(origin.source_signature, inspect.signature(self.func))
        self.assertEqual(origin.source_id, expected_id)
        self.assertEqual(origin.source_module_name, self.func.__module__)
        self.assertIs(origin.source_resource_type, int)
        self.assertEqual(origin.describe_source(), expected_id)

    def test_generate_call_variations(self):
        origin = ResourceOrigin(
            "scope",
            "ident",
            ResourceLifespan.Session,
            source=self.source,
        )

        call_no_constraints = origin.generate_call()
        call_with_constraints = origin.generate_call(constraints={"a": 1})

        self.assertEqual(call_no_constraints, "dummy_source(a, b)")
        self.assertEqual(call_with_constraints, "dummy_source(a, b, constraints)")

    def test_constraints_key_in_catalog(self):
        origin = ResourceOrigin(
            "scope2",
            "id2",
            ResourceLifespan.Session,
            source=self.source,
            constraints={"x": 1},
        )
        key = "scope2:id2"
        self.assertEqual(origin.constraints_key, key)
        self.assertIn(key, constraints_catalog._site_constraints)
        expected_desc = f"{self.func.__module__}#{self.func.__name__} constraints='{key}'"
        self.assertEqual(origin.describe_source(), expected_desc)


class ValidatorOriginTests(OriginBaseTest):
    def test_validator_properties_and_call(self):
        origin = ValidatorOrigin(
            "scope",
            "ident",
            "suf",
            source=self.source,
        )

        expected_id = f"{self.func.__module__}#{self.func.__name__}"
        self.assertIsNone(origin.constraints_key)
        self.assertEqual(origin.identifier, "ident")
        self.assertEqual(origin.suffix, "suf")
        self.assertEqual(origin.life_span, ResourceLifespan.Test)
        self.assertEqual(origin.describe_source(), expected_id)

        call_no_constraints = origin.generate_call()
        call_with_constraints = origin.generate_call(constraints={"x": 1})
        self.assertEqual(call_no_constraints, "dummy_source(a, b)")
        self.assertEqual(call_with_constraints, "dummy_source(a, b, constraints)")


if __name__ == "__main__":
    unittest.main()
