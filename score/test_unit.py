import unittest
from Math import *
SECONDS_PER_YEAR = 31536000

class MathTestCase(unittest.TestCase):
    def test_exaMul(self):
        self.assertEqual(exaMul(8888888888888888889, 8888888888888888889 ), 79012345679012345681) #79,012,345,679,012,345,680,987,654,320,987,654,321
        self.assertEqual(exaMul(2 * 10**18, 2 * 10**18 ), 4 * 10**18)

    def test_exaDiv(self):
        self.assertEqual(exaDiv(2 * 10**18, 2 * 10**18), 1 * 10**18)

    def test_exaPow(self):
        self.assertEqual(exaPow(2 * 10**18, 3), 8 * 10**18)

    def test_calculateLinearInterest(self):
        self.assertEqual(calculateLinearInterest(12 * 10**18,2000000000 ),1000761035007610348)

    def test_calculateCompoundInterest(self):
        self.assertEqual(calculateCompoundedInterest(12 * 10**18,2000000000 ),1000761324523324312)

if __name__ == '__main__':
    unittest.main()