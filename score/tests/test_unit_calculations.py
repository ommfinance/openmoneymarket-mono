from lendingPoolCore.lendingPoolCore import LendingPoolCore
from sample_token.sample_token import SampleToken
from addressProvider.addressProvider import AddressProvider
from lendingPool.lendingPool import LendingPool
from lendingPoolDataProvider.lendingPoolDataProvider import LendingPoolDataProvider
from oToken.oToken import OToken
from priceOracle.priceOracle import PriceOracle
from feeProvider.feeProvider import FeeProvider
from lendingPoolCore.Math import exaMul, exaDiv, exaPow

from tbears.libs.scoretest.score_test_case import ScoreTestCase
from iconservice import Address, AddressPrefix, IconScoreException


class TestSimpleDeposit(ScoreTestCase):
    def setUp(self):
        super().setUp()

        params = {}
        USDbParams = {'_initialSupply': 500000000, '_decimals': 18}
        oTokenParams = {"_name": "BridgeUSDInterestToken", "_symbol": "oUSDb"}
        self.USDb = self.get_score_instance(SampleToken, self.test_account1, USDbParams)
        self.lendingPoolCore = self.get_score_instance(LendingPoolCore, self.test_account1, params)
        self.addressProvider = self.get_score_instance(AddressProvider, self.test_account1, params)
        self.lendingPool = self.get_score_instance(LendingPool, self.test_account1, params)
        self.lendingPoolDataProvider = self.get_score_instance(LendingPoolDataProvider, self.test_account1, params)
        self.oToken = self.get_score_instance(OToken, self.test_account1, oTokenParams)
        self.priceOracle = self.get_score_instance(PriceOracle, self.test_account1, params)
        self.feeProvider = self.get_score_instance(FeeProvider, self.test_account1, params)

        self.set_msg(self.test_account1, 0)

        # setting interfaces for lending pool
        self.lendingPool.setLendingPoolCoreAddress(self.lendingPoolCore.address)
        self.lendingPool.setDataProvider(self.lendingPoolDataProvider.address)
        self.lendingPool.setUSDbAddress(self.USDb.address)
        self.lendingPool.setFeeProvider(self.feeProvider.address)

        # setting origination fee
        self.feeProvider.setLoanOriginationFeePercentage(25 * 10 ** 14)

        # setting interfaces in lending pool data provider
        self.lendingPoolDataProvider.setSymbol(self.USDb.address, "USDb")
        self.lendingPoolDataProvider.setLendingPoolCoreAddress(self.lendingPoolCore.address)
        self.lendingPoolDataProvider.setOracleAddress(self.priceOracle.address)

        # setting otoken interface addresses
        self.oToken.setCoreAddress(self.lendingPoolCore.address)
        self.oToken.setDataProviderAddress(self.lendingPoolDataProvider.address)
        self.oToken.setLendingPoolAddress(self.lendingPool.address)
        self.oToken.setReserveAddress(self.USDb.address)

        # setting price in oracle
        self.priceOracle.set_reference_data('USDb', 'USD', 1 * 10 ** 18)

        # setting interfaces in address provider
        self.addressProvider.setLendingPool(self.lendingPool.address)
        self.addressProvider.setLendingPoolDataProvider(self.lendingPoolDataProvider.address)
        self.addressProvider.setUSDb(self.USDb.address)
        self.addressProvider.setoUSDb(self.oToken.address)

        # reserve constants for USDb
        reserveConstants = [{"reserve": self.USDb.address,
                             "optimalUtilizationRate": 600000000000000000,
                             "baseBorrowRate": 10000000000000000,
                             "slopeRate1": 40000000000000000,
                             "slopeRate2": 500000000000000000}]

        # setting the reserve constants
        self.lendingPoolCore.setReserveConstants(reserveConstants)

        # setting the  initial reserve attributes for USDb reserve
        reserveParams = {"reserveAddress": self.USDb.address,
                         "oTokenAddress": self.oToken.address,
                         "totalBorrows": 0,
                         "lastUpdateTimestamp": 0,
                         "liquidityRate": 0,
                         "borrowRate": 0,
                         "liquidityCumulativeIndex": 1 * 10 ** 18,
                         "borrowCumulativeIndex": 1 * 10 ** 18,
                         "baseLTVasCollateral": 60 * 10 ** 16,
                         "liquidationThreshold": 65 * 10 ** 16,
                         "liquidationBonus": 10,
                         "decimals": 18,
                         "borrowingEnabled": True,
                         "usageAsCollateralEnabled": True,
                         "isFreezed": False,
                         "isActive": True}

        # initializing the USDb reserve
        self.lendingPoolCore.addReserveData(reserveParams)

    def test_calculateOriginationFee(self):
        borrowAmount = 1000 * 10 ** 18
        originationFee = self.feeProvider.calculateOriginationFee(self.test_account1, borrowAmount)
        # manual calcuation
        originationFee2 = exaMul(self.feeProvider.getLoanOriginationFeePercentage(), borrowAmount)
        self.assertEqual(originationFee, originationFee2)

    def test_calculateLinearInterest(self):
        # creating a time difference of 10 seconds i.e 10 * 10 ** 6 microseconds
        self.set_block(30, 10 * 10 ** 6)
        liquidityRate = 4200000000000000
        SECONDS_PER_YEAR = 31536000
        EXA = 10 ** 18
        interest = self.lendingPoolCore.calculateLinearInterest(liquidityRate, 0)
        # manual calculation
        timeDifference = (10 * 10 ** 6 - 0) // 10 ** 6
        timeDelta = exaDiv(timeDifference, SECONDS_PER_YEAR)
        interest2 = exaMul(liquidityRate, timeDelta) + EXA
        self.assertEqual(interest, interest2)

    def test_calculateCompoundedInterest(self):
        # creating a time difference of 10 seconds i.e 10 * 10 ** 6 microseconds
        self.set_block(30, 10 * 10 ** 6)
        borrowRate = 23333333333333333
        SECONDS_PER_YEAR = 31536000
        EXA = 10 ** 18
        interest = self.lendingPoolCore.calculateCompoundedInterest(borrowRate, 0)
        # manual calculation
        timeDifference = (10 * 10 ** 6 - 0) // 10 ** 6
        ratePerSecond = borrowRate // SECONDS_PER_YEAR
        interest2 = exaPow((ratePerSecond + EXA), timeDifference)
        self.assertEqual(interest, interest2)

    def test_calculateInterestRates(self):
        _reserve = self.USDb.address
        _availableLiquidity = 1000 * 10 ** 18
        _totalBorrows = 400 * 10 ** 18
        rates = self.lendingPoolCore.calculateInterestRates(_reserve, _availableLiquidity, _totalBorrows)
        # manual calculation
        rate = {}
        EXA = 10 ** 18
        constants = self.lendingPoolCore.getReserveConstants(self.USDb.address)
        if _totalBorrows == 0 and _availableLiquidity == 0:
            utilizationRate = 0
        else:
            utilizationRate = exaDiv(_totalBorrows, (_totalBorrows + _availableLiquidity))

        if utilizationRate < constants['optimalUtilizationRate']:
            rate['borrowRate'] = constants['baseBorrowRate'] + exaMul(
                exaDiv(utilizationRate, constants['optimalUtilizationRate']), constants['slopeRate1'])
        else:
            rate['borrowRate'] = constants['baseBorrowRate'] + constants['slopeRate1'] + exaMul(
                exaDiv((utilizationRate - constants['optimalUtilizationRate']),
                       (EXA - constants['optimalUtilizationRate'])), constants['slopeRate2'])

        rate['liquidityRate'] = exaMul(exaMul(rate['borrowRate'], utilizationRate), 9 * EXA // 10)

        self.assertEqual(rates, rate)

    """
    def test_calculateCollateralNeededUSD(self):
        _reserve = self.USDb.address
        _amount = 10000 * 10 ** 18
        _fee = self.feeProvider.calculateOriginationFee(self.test_account1, _amount)
        _userCurrentBorrowBalanceUSD = 5000 * 10 ** 18
        _userCurrentFeesUSD = 0
        _userCurrentLtv = 60 * 10 ** 18
        collateralNeededUSD = self.lendingPoolDataProvider.calculateCollateralNeededUSD(_reserve, _amount, _fee, _userCurrentBorrowBalanceUSD, _userCurrentFeesUSD, _userCurrentLtv)
        print(collateralNeededUSD)
    """

    def test_calculateHealthFactorFromBalancesInternal(self):
        _collateralBalanceUSD = 1000 * 10 ** 18
        _borrowBalanceUSD = 555 * 10 ** 18
        _totalFeesUSD = 0
        _liquidationThreshold = 65 * 10 ** 16
        healthFactor = self.lendingPoolDataProvider.calculateHealthFactorFromBalancesInternal(_collateralBalanceUSD,
                                                                                              _borrowBalanceUSD,
                                                                                              _totalFeesUSD,
                                                                                              _liquidationThreshold)
        # manual calculation
        if _borrowBalanceUSD == 0:
            return -1
        healthFactor2 = exaDiv(exaMul(_collateralBalanceUSD, _liquidationThreshold), _borrowBalanceUSD + _totalFeesUSD)
        self.assertEqual(healthFactor, healthFactor2)

    def test_calculateBorrowingPowerFromBalancesInternal(self):
        _collateralBalanceUSD = 1000 * 10 ** 18
        _borrowBalanceUSD = 555 * 10 ** 18
        _totalFeesUSD = 0
        _ltv = 60 * 10 ** 16
        borrowingPower = self.lendingPoolDataProvider.calculateBorrowingPowerFromBalancesInternal(_collateralBalanceUSD,
                                                                                                  _borrowBalanceUSD,
                                                                                                  _totalFeesUSD, _ltv)
        # manual calculation
        if _collateralBalanceUSD == 0:
            return 0
        borrowingPower2 = exaDiv((_borrowBalanceUSD + _totalFeesUSD), exaMul(_collateralBalanceUSD, _ltv))
        self.assertEqual(borrowingPower, borrowingPower2)
