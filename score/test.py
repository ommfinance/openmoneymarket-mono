import unittest
import sys

class MyTest(unittest.TestCase):
    def setUp(self):
        self.a = sys.argv[2]
    def runTest(self):
        self.assertEqual(self.a, "1")

unittest.TextTestRunner().run(MyTest())


