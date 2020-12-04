from lendingPoolCore.lendingPoolCore import LendingPoolCore
from sample_token.sample_token import SampleToken
from addressProvider.addressProvider import AddressProvider
from lendingPool.lendingPool import LendingPool
from lendingPoolDataProvider.lendingPoolDataProvider import LendingPoolDataProvider
from oToken.oToken import OToken
from priceOracle.priceOracle import PriceOracle
from feeProvider.feeProvider import FeeProvider
from lendingPoolCore.Math import exaMul

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
                        "totalBorrows":50,
                        "lastUpdateTimestamp": 0,
                        "liquidityRate":4200000000000000,
                        "borrowRate": 23333333333333333,
                        "liquidityCumulativeIndex":1*10**18,
                        "borrowCumulativeIndex":1*10**18,
                        "baseLTVasCollateral":60*10**18,
                        "liquidationThreshold":65*10**18,
                        "liquidationBonus":10,
                        "decimals":18,
                        "borrowingEnabled": True,
                        "usageAsCollateralEnabled":True,
                        "isFreezed": False,
                        "isActive": True,
                        "availableLiquidity": 200*10**18,
                        "totalLiquidity": 250*10**18} 

        #initializing the USDb reserve 
        self.lendingPoolCore.addReserveData(reserveParams)

    def test_LCI(self):
        #lastUpdateTime is set to 0 in USDb reserve
        #Checking LCI for timediffrerences of 10sec = 10 UNIX time, 20sec = 20, 60sec = 60, 1hr = 3600, 1day = 86400, 7days = 604800, 15days = 129600
        #The unix times are in second so converting all to microseconds before calling calculateLinearInterest
        times = [ 10 * 10 ** 6, 20 * 10 ** 6, 60 * 10 ** 6, 3600 * 10 ** 6, 86400 * 10 ** 6, 129600 * 10 ** 6 ]
        liquidityRate = 4200000000000000
        defaultLCI = 1 * 10 ** 18
        for time in times:
            print('time is',time)
            self.set_block(30, time)
            value = self.lendingPoolCore.calculateLinearInterest(liquidityRate ,0)
            updatedLCI = exaMul(value, defaultLCI)
            print('updated CLI', updatedLCI) 
        #checked result with manually computed value and it matches

    def test_BCI(self):
        times = [ 10 * 10 ** 6, 20 * 10 ** 6, 60 * 10 ** 6, 3600 * 10 ** 6, 86400 * 10 ** 6, 129600 * 10 ** 6 ]
        borrowRate = 23333333333333333
        defaultBCI = 1 * 10 ** 18
        for time in times:
            print('time is',time)
            self.set_block(30, time)
            value = self.lendingPoolCore.calculateCompoundedInterest(borrowRate ,0)
            updatedBCI = exaMul(value, defaultBCI)
            print('updated BCI', updatedBCI) 
        #checked result with manually computed value and it matches
