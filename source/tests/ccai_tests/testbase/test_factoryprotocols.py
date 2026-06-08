
import unittest
from ccai.testbase.factoryprotocols import TestBaseFactoryProtocol
from ccai.testbase.testjob import DefaultTestJob

class TestFactoryProtocols(unittest.TestCase):
    def test_get_testbase_default_job_type_returns_default_test_job(self):
        proto = TestBaseFactoryProtocol()
        result = proto.get_testbase_default_job_type()
        self.assertEqual(result, DefaultTestJob, "get_testbase_default_job_type should return DefaultTestJob")

if __name__ == '__main__':
    unittest.main()
