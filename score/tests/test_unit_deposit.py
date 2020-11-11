
from lendingPoolCore.lendingPoolCore import LendingPoolCore
from sample_token.sample_token import SampleToken
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from iconservice import Address, AddressPrefix, IconScoreException



class TestSimpleDeposit(ScoreTestCase):
    def setUp(self):
        super().setUp()

        params = {}
        params2 = {'_initialSupply':500000000, '_decimals': 18}
        self.USDb = self.get_score_instance(SampleToken, self.test_account1, params2)
        self.score1 = self.get_score_instance(LendingPoolCore, self.test_account1, params)
        

    def test_simple_deposit(self):
        self.assertEqual(self.USDb.name(), 'USDb')
        self.assertTrue(True)
        
        
