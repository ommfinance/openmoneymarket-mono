from lendingPoolCore.lendingPoolCore import LendingPoolCore
from sample_token.sample_token import SampleToken
from addressProvider.addressProvider import AddressProvider
from lendingPool.lendingPool import LendingPool
from lendingPoolDataProvider.lendingPoolDataProvider import LendingPoolDataProvider
from oToken.oToken import OToken
from priceOracle.priceOracle import PriceOracle
from feeProvider.feeProvider import FeeProvider


from tbears.libs.scoretest.score_test_case import ScoreTestCase
from iconservice import Address, AddressPrefix, IconScoreException



class TestSimpleDeposit(ScoreTestCase):
    
    def setUp(self):
        super().setUp()

        params = {}
        USDbParams = {'_initialSupply':500000000, '_decimals': 18}
        oTokenParams = {"_name":"BridgeUSDInterestToken","_symbol":"oUSDb"}
        self.USDb = self.get_score_instance(SampleToken, self.test_account1, USDbParams)
        self.lendingPoolCore = self.get_score_instance(LendingPoolCore, self.test_account1, params)
        self.addressProvider = self.get_score_instance(AddressProvider, self.test_account1, params)
        self.lendingPool = self.get_score_instance(LendingPool, self.test_account1, params)
        self.lendingPoolDataProvider = self.get_score_instance(LendingPoolDataProvider, self.test_account1, params)
        self.oToken = self.get_score_instance(OToken, self.test_account1, oTokenParams)
        self.priceOracle = self.get_score_instance(PriceOracle, self.test_account1, params)
        self.feeProvider = self.get_score_instance(FeeProvider, self.test_account1, params)

        self.set_msg(self.test_account1,0)

        #setting interfaces for lending pool
        self.lendingPool.setLendingPoolCoreAddress(self.lendingPoolCore.address)
        self.lendingPool.setDataProvider(self.lendingPoolDataProvider.address)
        self.lendingPool.setUSDbAddress(self.USDb.address)
        self.lendingPool.setFeeProvider(self.feeProvider.address)

        #setting orgination fee
        self.feeProvider.setLoanOriginationFeePercentage(25*10**14)

        #setting interfaces in lending pool data provider
        self.lendingPoolDataProvider.setSymbol(self.USDb.address,"USDb")
        self.lendingPoolDataProvider.setLendingPoolCoreAddress(self.lendingPoolCore.address)
        self.lendingPoolDataProvider.setOracleAddress(self.priceOracle.address)

        #setting otoken interface addresses
        self.oToken.setCoreAddress(self.lendingPoolCore.address)
        self.oToken.setDataProviderAddress(self.lendingPoolDataProvider.address)
        self.oToken.setLendingPoolAddress(self.lendingPool.address)
        self.oToken.setReserveAddress(self.USDb.address)

        #setting price in oracle
        self.priceOracle.set_reference_data('USDb','USD',1*10**18)

        #setting interfaces in address provider
        self.addressProvider.setLendingPool(self.lendingPool.address)
        self.addressProvider.setLendingPoolDataProvider(self.lendingPoolDataProvider.address)
        self.addressProvider.setUSDb(self.USDb.address)
        self.addressProvider.setoUSDb(self.oToken.address)
        
        #reserve constants for USDb
        reserveConstants=[{"reserve":self.USDb.address,
                           "optimalUtilizationRate":600000000000000000,
                           "baseBorrowRate":10000000000000000,
                           "slopeRate1":40000000000000000,
                           "slopeRate2":500000000000000000}]

        #setting the reserve constants
        self.lendingPoolCore.setReserveConstants(reserveConstants)

        #setting the  intial reserve attributes for USDb reserve
        reserveParams ={"reserveAddress":self.USDb.address,
                        "oTokenAddress":self.oToken.address,
                        "totalBorrows":0,
                        "lastUpdateTimestamp": 0,
                        "liquidityRate":0,
                        "borrowRate":0,
                        "liquidityCumulativeIndex":1*10**18,
                        "borrowCumulativeIndex":1*10**18,
                        "baseLTVasCollateral":60*10**18,
                        "liquidationThreshold":65*10**18,
                        "liquidationBonus":10,
                        "decimals":18,
                        "borrowingEnabled": True,
                        "usageAsCollateralEnabled":True,
                        "isFreezed": False,
                        "isActive": True } 

        #initializing the USDb reserve 
        self.lendingPoolCore.addReserveData(reserveParams)

    def test_simple_deposit(self):
        self.assertEqual(self.USDb.name(), 'USDb')
        # self.assertEqual(self.lendingPoolCore.address,"")
        self.assertTrue(True)
        
        
    def test_lendingPoolAddresses(self):
        self.assertEqual(self.lendingPool.getLendingPoolCoreAddress(),self.lendingPoolCore.address)
        self.assertEqual(self.lendingPool.getDataProvider(),self.lendingPoolDataProvider.address)
        self.assertEqual(self.lendingPool.getFeeProvider(),self.feeProvider.address)
        self.assertEqual(self.lendingPool.getUSDbAddress(),self.USDb.address)

    def test_lendingPoolDataProviderAddresses(self):
        self.assertEqual(self.lendingPoolDataProvider.getLendingPoolCoreAddress(),self.lendingPoolCore.address)
        self.assertEqual(self.lendingPoolDataProvider.getOracleAddress(),self.priceOracle.address)
        
        self.assertEqual(self.lendingPoolDataProvider.getSymbol(self.USDb.address),'USDb')

    def test_fee(self):
        self.assertEqual(self.feeProvider.getLoanOriginationFeePercentage(),25*10**14)

    def test_oTokenAddresses(self):
        self.assertEqual(self.oToken.getCoreAddress(),self.lendingPoolCore.address)
        self.assertEqual(self.oToken.getDataProviderAddress(),self.lendingPoolDataProvider.address)
        self.assertEqual(self.oToken.getLendingPoolAddress(),self.lendingPool.address)
        self.assertEqual(self.oToken.getReserveAddress(),self.USDb.address)

    def test_reserveConstants(self):
        reserve_constants=self.lendingPoolCore.getReserveConstants(self.USDb.address)
        actualReserveConstants={"reserve":self.USDb.address,
                           "optimalUtilizationRate":600000000000000000,
                           "baseBorrowRate":10000000000000000,
                           "slopeRate1":40000000000000000,
                           "slopeRate2":500000000000000000}
        self.assertEqual(reserve_constants,actualReserveConstants)

    def test_price(self):
        self.assertEqual(self.priceOracle.get_reference_data('USDb','USD'),1*10**18)

    def test_addressProvider(self):
        addresses=self.addressProvider.getAllAddresses()
        self.assertEqual(addresses['collateral']['USDb'],self.USDb.address)
        self.assertEqual(addresses['oTokens']['oUSDb'],self.oToken.address)
        self.assertEqual(addresses['systemContract']['LendingPool'],self.lendingPool.address)
        self.assertEqual(addresses['systemContract']['LendingPoolDataProvider'],self.lendingPoolDataProvider.address)

    # def test_deposit(self):
    #     self.USDb.transfer(self.test_account2,1000 * 10**18)
    #     depositAmount = 100*10**18
    #     data = "{\"method\": \"deposit\", \"params\": {\"amount\": 100000000000000000000}}".encode("utf-8")
    #     self.set_msg(self.test_account2)
    #     self.USDb.transfer(self.lendingPool.address,depositAmount,data)