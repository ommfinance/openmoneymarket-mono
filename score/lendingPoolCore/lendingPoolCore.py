from iconservice import *
from .ReserveData import *
from .UserData import *
from .Math import *
from .utils.checks import *

TAG = 'LendingPoolCore'

RESERVE_DB_PREFIX = b'reserve'
USER_DB_PREFIX = b'userReserve'


class ReserveAttributes(TypedDict):
    reserveAddress: Address
    oTokenAddress: Address
    totalBorrows: int
    lastUpdateTimestamp: int
    liquidityRate: int
    borrowRate: int
    liquidityCumulativeIndex: int
    borrowCumulativeIndex: int
    baseLTVasCollateral: int
    liquidationThreshold: int
    liquidationBonus: int
    decimals: int
    borrowingEnabled: bool
    usageAsCollateralEnabled: bool
    isFreezed: bool
    isActive: bool


class UserDataAttributes(TypedDict):
    reserveAddress: Address
    userAddress: Address
    principalBorrowBalance: int
    userBorrowCumulativeIndex: int
    lastUpdateTimestamp: int
    originationFee: int
    useAsCollateral: bool


class UserSnapshotData(TypedDict):
    principalOTokenBalance: int
    principalBorrowBalance: int
    userLiquidityCumulativeIndex: int
    userBorrowCumulativeIndex: int


class ReserveSnapshotData(TypedDict):
    liquidityRate: int
    borrowRate: int
    liquidityCumulativeIndex: int
    borrowCumulativeIndex: int
    lastUpdateTimestamp: int
    price: int


class Constant(TypedDict):
    reserve: Address
    optimalUtilizationRate: int
    baseBorrowRate: int
    slopeRate1: int
    slopeRate2: int


class PrepDelegations(TypedDict):
    _address: Address
    _votes_in_per: int


# An interface to oToken
class oTokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def principalBalanceOf(self, _user: Address) -> int:
        pass

    @interface
    def getUserLiquidityCumulativeIndex(self, _user: Address) -> int:
        pass


# An interface to PriceOracle
class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> int:
        pass


# An interface to Reserve
class ReserveInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass


class StakingInterface(InterfaceScore):
    @interface
    def getTodayRate(self) -> int:
        pass

    @interface
    def delegate(self, _delegations: List[PrepDelegations]):
        pass


class LendingPoolCore(IconScoreBase):
    _ID = 'id'
    _RESERVE_LIST = '_reserveList'
    _LENDING_POOL = 'lendingPool'
    _CONSTANTS = 'constants'
    _DAOFUND = 'daoFund'
    _PRICE_ORACLE = 'priceOracle'
    _STAKING = 'staking'
    _DELEGATION = 'delegation'
    _LIQUIDATION = 'liquidation'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._id = VarDB(self._ID, db, str)
        self._reserveList = ArrayDB(self._RESERVE_LIST, db, value_type=Address)
        self._lendingPool = VarDB(self._LENDING_POOL, db, value_type=Address)
        self._constants = DictDB(self._CONSTANTS, db, value_type=int, depth=2)
        self._daoFund = VarDB(self._DAOFUND, db, value_type=Address)
        self._priceOracle = VarDB(self._PRICE_ORACLE, db, value_type=Address)
        self._staking = VarDB(self._STAKING, db, value_type=Address)
        self._delegation = VarDB(self._DELEGATION, db, value_type=Address)
        self._liquidation = VarDB(self._LIQUIDATION, db, value_type=Address)
        self.reserve = ReserveDataDB(db)
        self.userReserve = UserReserveDataDB(db)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=3)
    def ReserveUpdated(self, _reserve: Address, _liquidityRate: int, _borrowRate: int, _liquidityCumulativeIndex: int,
                       _borrowCumulativeIndex: int):
        pass

    @eventlog(indexed=3)
    def DaoFundTransfer(self, _amount: int, _reserve: Address, _initiatiator: Address):
        pass

    @external(readonly=True)
    def name(self) -> str:
        return 'OmmLendingPoolCore'
        
    @only_owner
    @external
    def set_id(self, _value: str):
        self._id.set(_value)

    @external(readonly=True)
    def get_id(self) -> str:
        return self._id.get()

    @only_owner
    @external
    def setStaking(self, _address: Address) -> None:
        self._staking.set(_address)

    @external(readonly=True)
    def getStaking(self) -> Address:
        return self._staking.get()

    @only_owner
    @external
    def setLendingPool(self, _address: Address):
        self._lendingPool.set(_address)

    @external(readonly=True)
    def getLendingPool(self) -> Address:
        return self._lendingPool.get()

    @only_owner
    @external
    def setLiquidationManager(self, _address: Address):
        self._liquidation.set(_address)

    @external(readonly=True)
    def getLiquidationManager(self) -> Address:
        return self._liquidation.get()

    @only_owner
    @external
    def setDelegation(self, _address: Address):
        self._delegation.set(_address)

    @external(readonly=True)
    def getDelegation(self) -> Address:
        return self._delegation.get()

    @only_owner
    @external
    def setPriceOracle(self, _address: Address) -> None:
        self._priceOracle.set(_address)

    @external(readonly=True)
    def getPriceOracle(self) -> Address:
        return self._priceOracle.get()

    @external(readonly=True)
    def getDaoFund(self) -> Address:
        return self._daoFund.get()

    @only_owner
    @external
    def setDaoFund(self, _address: Address):
        self._daoFund.set(_address)

    def reservePrefix(self, _reserve: Address) -> bytes:
        return b'|'.join([RESERVE_DB_PREFIX, self._id.get().encode(), str(_reserve).encode()])

    def userReservePrefix(self, _reserve: Address, _user: Address) -> bytes:
        return b'|'.join([USER_DB_PREFIX, self._id.get().encode(), str(_reserve).encode(), str(_user).encode()])

    # Methods to update the states of a reserve

    def updateTotalBorrows(self, _reserve: Address, _totalBorrows: int):
        prefix = self.reservePrefix(_reserve)
        self.reserve[prefix].totalBorrows.set(_totalBorrows)

    def updateLastUpdateTimestamp(self, _reserve: Address, _lastUpdateTimestamp: int):
        prefix = self.reservePrefix(_reserve)
        self.reserve[prefix].lastUpdateTimestamp.set(_lastUpdateTimestamp)

    def updateLiquidityRate(self, _reserve: Address, _liquidityRate: int):
        prefix = self.reservePrefix(_reserve)
        self.reserve[prefix].liquidityRate.set(_liquidityRate)

    def updateBorrowRate(self, _reserve: Address, _borrowRate: int):
        prefix = self.reservePrefix(_reserve)
        self.reserve[prefix].borrowRate.set(_borrowRate)

    def updateBorrowCumulativeIndex(self, _reserve: Address, _borrowCumulativeIndex: int):
        prefix = self.reservePrefix(_reserve)
        self.reserve[prefix].borrowCumulativeIndex.set(_borrowCumulativeIndex)

    def updateLiquidityCumulativeIndex(self, _reserve: Address, _liquidityCumulativeIndex: int):
        prefix = self.reservePrefix(_reserve)
        self.reserve[prefix].liquidityCumulativeIndex.set(_liquidityCumulativeIndex)

    def updateBaseLTVasCollateral(self, _reserve: Address, _baseLTVasCollateral: int):
        prefix = self.reservePrefix(_reserve)
        self.reserve[prefix].baseLTVasCollateral.set(_baseLTVasCollateral)

    def updateLiquidationThreshold(self, _reserve: Address, _liquidationThreshold: int):
        prefix = self.reservePrefix(_reserve)
        self.reserve[prefix].liquidationThreshold.set(_liquidationThreshold)

    def updateLiquidationBonus(self, _reserve: Address, _liquidationBonus: int):
        prefix = self.reservePrefix(_reserve)
        self.reserve[prefix].liquidationBonus.set(_liquidationBonus)

    def updateDecimals(self, _reserve: Address, _decimals: int):
        prefix = self.reservePrefix(_reserve)
        self.reserve[prefix].decimals.set(_decimals)

    def updateBorrowingEnabled(self, _reserve: Address, _borrowingEnabled: bool):
        prefix = self.reservePrefix(_reserve)
        self.reserve[prefix].borrowingEnabled.set(_borrowingEnabled)

    def updateUsageAsCollateralEnabled(self, _reserve: Address, _usageAsCollateralEnabled: bool):
        prefix = self.reservePrefix(_reserve)
        self.reserve[prefix].usageAsCollateralEnabled.set(_usageAsCollateralEnabled)

    def updateIsFreezed(self, _reserve: Address, _isFreezed: bool):
        prefix = self.reservePrefix(_reserve)
        self.reserve[prefix].isFreezed.set(_isFreezed)

    def updateIsActive(self, _reserve: Address, _isActive: bool):
        prefix = self.reservePrefix(_reserve)
        self.reserve[prefix].isActive.set(_isActive)

    def updateOtokenAddress(self, _reserve: Address, _oTokenAddress: Address):
        prefix = self.reservePrefix(_reserve)
        self.reserve[prefix].oTokenAddress.set(_oTokenAddress)

    # Update methods for user attributes for a specific reserve

    def updateUserPrincipalBorrowBalance(self, _reserve: Address, _user: Address,
                                         _principalBorrowBalance: int):
        prefix = self.userReservePrefix(_reserve, _user)
        self.userReserve[prefix].principalBorrowBalance.set(_principalBorrowBalance)

    def updateUserBorrowCumulativeIndex(self, _reserve: Address, _user: Address,
                                        _userBorrowCumulativeIndex: int):
        prefix = self.userReservePrefix(_reserve, _user)
        self.userReserve[prefix].userBorrowCumulativeIndex.set(_userBorrowCumulativeIndex)

    def updateUserLastUpdateTimestamp(self, _reserve: Address, _user: Address,
                                      _lastUpdateTimestamp: int):
        prefix = self.userReservePrefix(_reserve, _user)
        self.userReserve[prefix].lastUpdateTimestamp.set(_lastUpdateTimestamp)

    def updateUserOriginationFee(self, _reserve: Address, _user: Address, _originationFee: int):
        prefix = self.userReservePrefix(_reserve, _user)
        self.userReserve[prefix].originationFee.set(_originationFee)

    def updateUserReserveUseAsCollateral(self, _reserve: Address, _user: Address, _useAsCollateral: int):
        prefix = self.userReservePrefix(_reserve, _user)
        self.userReserve[prefix].useAsCollateral.set(_useAsCollateral)

    def _check_reserve(self, _reserve: Address):
        return _reserve in self._reserveList

    @external(readonly=True)
    def getReserves(self) -> list:
        return [reserve for reserve in self._reserveList]

    def _addNewReserve(self, _res: Address):
        self._reserveList.put(_res)

    @external(readonly=True)
    def isReserveBorrowingEnabled(self, _reserve: Address) -> bool:
        return self.getReserveData(_reserve)['borrowingEnabled']

    @only_owner
    @external
    def addReserveData(self, _reserve: ReserveAttributes):
        reserve_data_obj = createReserveDataObject(_reserve)
        if not self._check_reserve(reserve_data_obj.reserveAddress):
            self._addNewReserve(reserve_data_obj.reserveAddress)
        prefix = self.reservePrefix(reserve_data_obj.reserveAddress)
        addDataToReserve(prefix, self.reserve, reserve_data_obj)

    @external(readonly=True)
    def getReserveData(self, _reserve: Address) -> dict:
        if self._check_reserve(_reserve):
            prefix = self.reservePrefix(_reserve)
            response = getDataFromReserve(prefix, self.reserve)
            response['totalLiquidity'] = self.getReserveTotalLiquidity(_reserve)
            response['availableLiquidity'] = self.getReserveAvailableLiquidity(_reserve)
        else:
            response = {}
        return response

    # @external
    # def addUserReserveData(self, _userReserveData: UserDataAttributes):
    #     user_reserve_data_object = createUserReserveDataObject(_userReserveData)
    #     if self._check_reserve(user_reserve_data_object.reserveAddress):
    #         prefix = self.userReservePrefix(user_reserve_data_object.reserveAddress,
    #                                         user_reserve_data_object.userAddress)
    #         addDataToUserReserve(prefix, self.userReserve, user_reserve_data_object)
    #     else:
    #         revert("Reserve error:The reserve is not added to pool")

    @external(readonly=True)
    def getUserReserveData(self, _reserve: Address, _user: Address) -> dict:
        if self._check_reserve(_reserve):
            prefix = self.userReservePrefix(_reserve, _user)
            response = getDataFromUserReserve(prefix, self.userReserve)
            return response

    # @external
    # def enableAsCollateral(self, _reserve: Address, _baseLTVasCollateral: int, _liquidationThreshold: int,
    #                        _liquidationBonus: int) -> None:
    #     self.updateUsageAsCollateralEnabled(_reserve, True)
    #     self.updateBaseLTVasCollateral(_reserve, _baseLTVasCollateral)
    #     self.updateLiquidationThreshold(_reserve, _liquidationThreshold)
    #     self.updateLiquidationBonus(_reserve, _liquidationBonus)

    #     reserveData = self.getReserveData(_reserve)
    #     if reserveData['liquidityCumulativeIndex'] == 0:
    #         self.updateLiquidityCumulativeIndex(_reserve, 10 ** 18)

    # @external
    # def disableAsCollateral(self, _reserve: Address) -> None:
    #     self.updateUsageAsCollateralEnabled(_reserve, False)

    # @external
    # def enableBorrowing(self, _reserve: Address) -> None:
    #     self.updateBorrowingEnabled(_reserve, True)

    # @external
    # def disableBorrowing(self, _reserve: Address) -> None:
    #     self.updateBorrowingEnabled(_reserve, False)

    # Internal calculations

    def calculateLinearInterest(self, _rate: int, _lastUpdateTimestamp: int) -> int:
        timeDifference = (self.now() - _lastUpdateTimestamp) // 10 ** 6
        timeDelta = exaDiv(timeDifference, SECONDS_PER_YEAR)
        return exaMul(_rate, timeDelta) + EXA

    def calculateCompoundedInterest(self, _rate: int, _lastUpdateTimestamp: int) -> int:
        timeDifference = (self.now() - _lastUpdateTimestamp) // 10 ** 6
        ratePerSecond = _rate // SECONDS_PER_YEAR
        return exaPow((ratePerSecond + EXA), timeDifference)

    @external(readonly=True)
    def getNormalizedIncome(self, _reserve: Address) -> int:
        reserveData = self.getReserveData(_reserve)
        interest = self.calculateLinearInterest(reserveData['liquidityRate'], reserveData['lastUpdateTimestamp'])
        cumulated = exaMul(interest, reserveData['liquidityCumulativeIndex'])
        return cumulated

    def updateCumulativeIndexes(self, _reserve: Address) -> None:
        reserveData = self.getReserveData(_reserve)
        totalBorrows = reserveData['totalBorrows']

        if totalBorrows > 0:
            cummulatedLiquidityInterest = self.calculateLinearInterest(reserveData['liquidityRate'],
                                                                       reserveData['lastUpdateTimestamp'])
            self.updateLiquidityCumulativeIndex(_reserve, exaMul(cummulatedLiquidityInterest,
                                                                 reserveData['liquidityCumulativeIndex']))
            cummulatedBorrowInterest = self.calculateCompoundedInterest(reserveData['borrowRate'],
                                                                        reserveData['lastUpdateTimestamp'])
            self.updateBorrowCumulativeIndex(_reserve,
                                             exaMul(cummulatedBorrowInterest, reserveData['borrowCumulativeIndex']))

    def _increaseTotalBorrows(self, _reserve: Address, _amount: int) -> None:
        reserveData = self.getReserveData(_reserve)
        self.updateTotalBorrows(_reserve, reserveData['totalBorrows'] + _amount)

    def _decreaseTotalBorrows(self, _reserve: Address, _amount: int) -> None:
        reserveData = self.getReserveData(_reserve)
        self.updateTotalBorrows(_reserve, reserveData['totalBorrows'] - _amount)

    @external(readonly=True)
    def getCompoundedBorrowBalance(self, _reserve: Address, _user: Address) -> int:
        userReserveData = self.getUserReserveData(_reserve, _user)
        reserveData = self.getReserveData(_reserve)
        if userReserveData['principalBorrowBalance'] == 0:
            return 0

        cumulatedInterest = exaDiv(
            exaMul(self.calculateCompoundedInterest(reserveData['borrowRate'], reserveData['lastUpdateTimestamp']),
                   reserveData['borrowCumulativeIndex']), userReserveData['userBorrowCumulativeIndex'])
        compoundedBalance = exaMul(userReserveData['principalBorrowBalance'], cumulatedInterest)

        if compoundedBalance == userReserveData['principalBorrowBalance']:
            if userReserveData['lastUpdateTimestamp'] != self.now():
                return userReserveData['principalBorrowBalance'] + 1

        return compoundedBalance

    @external(readonly=True)
    def getReserveAvailableLiquidity(self, _reserve: Address) -> int:
        reserveScore = self.create_interface_score(_reserve, ReserveInterface)
        balance = reserveScore.balanceOf(self.address)
        return balance

    def getReserveTotalLiquidity(self, _reserve: Address) -> int:
        prefix = self.reservePrefix(_reserve)
        reserveData = getDataFromReserve(prefix, self.reserve)
        return self.getReserveAvailableLiquidity(_reserve) + reserveData['totalBorrows']

    def getReserveNormalizedIncome(self, _reserve: Address) -> int:
        return self.getNormalizedIncome(_reserve)

    def getReserveUtilizationRate(self, _reserve: Address) -> int:
        reserveData = self.getReserveData(_reserve)
        totalBorrows = reserveData['totalBorrows']

        if totalBorrows == 0:
            return 0

        totalLiquidity = self.getReserveTotalLiquidity(_reserve)

        return exaDiv(totalBorrows, totalLiquidity)

    @external(readonly=True)
    def getReserveConfiguration(self, _reserve: Address) -> dict:
        reserveData = self.getReserveData(_reserve)
        response = {
            'decimals': reserveData['decimals'],
            'baseLTVasCollateral': reserveData['baseLTVasCollateral'],
            'liquidationThreshold': reserveData['liquidationThreshold'],
            'usageAsCollateralEnabled': reserveData['usageAsCollateralEnabled'],
            'isActive': reserveData['isActive'],
            'borrowingEnabled': reserveData['borrowingEnabled'],
            'liquidationBonus': reserveData['liquidationBonus']

        }
        return response

    def updateReserveInterestRatesAndTimestampInternal(self, _reserve: Address, _liquidityAdded: int,
                                                       _liquidityTaken: int) -> None:
        reserveData = self.getReserveData(_reserve)
        rate = self.calculateInterestRates(_reserve, self.getReserveAvailableLiquidity(
            _reserve) + _liquidityAdded - _liquidityTaken, reserveData['totalBorrows'])
        self.updateLiquidityRate(_reserve, rate['liquidityRate'])
        self.updateBorrowRate(_reserve, rate['borrowRate'])
        self.updateLastUpdateTimestamp(_reserve, self.now())

        self.ReserveUpdated(_reserve, rate['liquidityRate'], rate['borrowRate'],
                            reserveData['liquidityCumulativeIndex'], reserveData['borrowCumulativeIndex'])

    @only_owner
    @external
    def setReserveConstants(self, _constants: List[Constant]) -> None:
        for constants in _constants:
            self._constants[(constants['reserve'])]['optimalUtilizationRate'] = constants['optimalUtilizationRate']
            self._constants[(constants['reserve'])]['baseBorrowRate'] = constants['baseBorrowRate']
            self._constants[(constants['reserve'])]['slopeRate1'] = constants['slopeRate1']
            self._constants[(constants['reserve'])]['slopeRate2'] = constants['slopeRate2']

    @external(readonly=True)
    def getReserveConstants(self, _reserve: Address) -> dict:
        data = {
            'reserve': _reserve,
            'optimalUtilizationRate': self._constants[_reserve]['optimalUtilizationRate'],
            'baseBorrowRate': self._constants[_reserve]['baseBorrowRate'],
            'slopeRate1': self._constants[_reserve]['slopeRate1'],
            'slopeRate2': self._constants[_reserve]['slopeRate2']
        }

        return data

    @only_lending_pool
    @external
    def transferToUser(self, _reserve: Address, _user: Address, _amount: int, _data: bytes = None) -> None:
        reserveScore = self.create_interface_score(_reserve, ReserveInterface)
        reserveScore.transfer(_user, _amount, _data)

    @only_liquidation_manager
    @external
    def liquidateFee(self, _reserve: Address, _amount: int, _destination: Address) -> None:
        reserveScore = self.create_interface_score(_reserve, ReserveInterface)
        reserveScore.transfer(_destination, _amount)

    @only_lending_pool
    @external
    def updateStateOnDeposit(self, _reserve: Address, _user: Address, _amount: int, _isFirstDeposit: bool) -> None:

        self.updateCumulativeIndexes(_reserve)
        self.updateReserveInterestRatesAndTimestampInternal(_reserve, _amount, 0)

        if _isFirstDeposit:
            self.setUserUseReserveAsCollateral(_reserve, _user, True)

    @only_lending_pool
    @external
    def updateStateOnRedeem(self, _reserve: Address, _user: Address, _amountRedeemed: int,
                            _userRedeemEverything: bool) -> None:
        self.updateCumulativeIndexes(_reserve)
        self.updateReserveInterestRatesAndTimestampInternal(_reserve, 0, _amountRedeemed)

        if _userRedeemEverything:
            self.setUserUseReserveAsCollateral(_reserve, _user, False)

    @only_lending_pool
    @external
    def updateStateOnBorrow(self, _reserve: Address, _user: Address, _amountBorrowed: int, _borrowFee: int) -> dict:
        borrowData = self.getUserBorrowBalances(_reserve, _user)
        balanceIncrease = borrowData['borrowBalanceIncrease']
        reserve = self.create_interface_score(_reserve, ReserveInterface)
        if balanceIncrease > 0:
            reserve.transfer(self._daoFund.get(), balanceIncrease // 10)
        self.DaoFundTransfer(balanceIncrease // 10, _reserve, self.tx.origin)
        self.updateReserveStateOnBorrowInternal(_reserve, balanceIncrease, _amountBorrowed)
        self.updateUserStateOnBorrowInternal(_reserve, _user, _amountBorrowed, balanceIncrease, _borrowFee)
        self.updateReserveInterestRatesAndTimestampInternal(_reserve, 0, _amountBorrowed)
        currentBorrowRate = self.getCurrentBorrowRate(_reserve)
       
        return {
            "currentBorrowRate": currentBorrowRate,
            "balanceIncrease": balanceIncrease
        }

    @only_lending_pool
    @external
    def updateStateOnRepay(self, _reserve: Address, _user: Address, _paybackAmountMinusFees: int,
                           _originationFeeRepaid: int, _balanceIncrease: int, _repaidWholeLoan: bool):
        reserve = self.create_interface_score(_reserve, ReserveInterface)
        if _balanceIncrease > 0:
            reserve.transfer(self._daoFund.get(), _balanceIncrease // 10)
        self.DaoFundTransfer(_balanceIncrease // 10, _reserve, self.tx.origin)
        self.updateReserveStateOnRepayInternal(_reserve, _user, _paybackAmountMinusFees, _balanceIncrease)
        self.updateUserStateOnRepayInternal(_reserve, _user, _paybackAmountMinusFees, _originationFeeRepaid,
                                            _balanceIncrease, _repaidWholeLoan)
        self.updateReserveInterestRatesAndTimestampInternal(_reserve, _paybackAmountMinusFees, 0)

    def updateReserveStateOnBorrowInternal(self, _reserve: Address, _balanceIncrease: int, _amountBorrowed: int):
        self.updateCumulativeIndexes(_reserve)
        self.updateReserveTotalBorrows(_reserve, _balanceIncrease, _amountBorrowed)

    def updateReserveStateOnRepayInternal(self, _reserve: Address, _user: Address, _paybackAmountMinusFees: int,
                                          _balanceIncrease: int):
        self.updateCumulativeIndexes(_reserve)
        reserveData = self.getReserveData(_reserve)
        totalBorrows = reserveData['totalBorrows']
        newTotalBorrows = totalBorrows + _balanceIncrease - _paybackAmountMinusFees
        self.updateTotalBorrows(_reserve, newTotalBorrows)

    def updateReserveTotalBorrows(self, _reserve: Address, _balanceIncrease: int, _amountBorrowed: int):

        reserveData = self.getReserveData(_reserve)
        reserveBorrows = reserveData['totalBorrows']
        newTotalBorrows = reserveBorrows + _balanceIncrease + _amountBorrowed
        self.updateTotalBorrows(_reserve, newTotalBorrows)

    def getCurrentBorrowRate(self, _reserve: Address) -> int:
        reserveData = self.getReserveData(_reserve)
        return reserveData['borrowRate']

    def updateUserStateOnBorrowInternal(self, _reserve: Address, _user: Address, _amountBorrowed: int,
                                        _balanceIncrease: int, _borrowFee: int):
        reserveData = self.getReserveData(_reserve)
        userReserveData = self.getUserReserveData(_reserve, _user)
        principalBorrowBalance = userReserveData['principalBorrowBalance']
        userPreviousOriginationFee = userReserveData['originationFee']
        lastReserveBorrowCumulativeIndex = reserveData['borrowCumulativeIndex']
        self.updateUserBorrowCumulativeIndex(_reserve, _user, lastReserveBorrowCumulativeIndex)
        self.updateUserPrincipalBorrowBalance(_reserve, _user,
                                              principalBorrowBalance + _amountBorrowed + _balanceIncrease)
        self.updateUserOriginationFee(_reserve, _user, userPreviousOriginationFee + _borrowFee)
        self.updateUserLastUpdateTimestamp(_reserve, _user, self.now())

    def updateUserStateOnRepayInternal(self, _reserve: Address, _user: Address, _paybackAmountMinusFees: int,
                                       _originationFeeRepaid: int, _balanceIncrease: int, _repaidWholeLoan: bool):
        reserveData = self.getReserveData(_reserve)
        userReserveData = self.getUserReserveData(_reserve, _user)
        self.updateUserPrincipalBorrowBalance(_reserve, _user, userReserveData[
            'principalBorrowBalance'] + _balanceIncrease - _paybackAmountMinusFees)
        self.updateUserBorrowCumulativeIndex(_reserve, _user, reserveData['borrowCumulativeIndex'])
        if _repaidWholeLoan:
            self.updateUserBorrowCumulativeIndex(_reserve, _user, 0)

        self.updateUserOriginationFee(_reserve, _user, userReserveData['originationFee'] - _originationFeeRepaid)
        self.updateUserLastUpdateTimestamp(_reserve, _user, self.now())

    @external(readonly=True)
    def getReserveOTokenAddress(self, _reserve: Address) -> Address:
        reserveData = self.getReserveData(_reserve)
        return reserveData['oTokenAddress']

    @only_liquidation_manager
    @external
    def updateStateOnLiquidation(self, _principalReserve: Address, _collateralReserve: Address, _user: Address,
                                 _amountToLiquidate: int, _collateralToLiquidate: int, _feeLiquidated: int,
                                 _liquidatedCollateralForFee: int, _balanceIncrease: int):
        reserve = self.create_interface_score(_principalReserve, ReserveInterface)
        reserve.transfer(self._daoFund.get(), _balanceIncrease // 10)
        self.updatePrincipalReserveStateOnLiquidationInternal(_principalReserve, _user, _amountToLiquidate,
                                                              _balanceIncrease)
        self.updateCollateralReserveStateOnLiquidationInternal(_collateralReserve)
        self.updateUserStateOnLiquidationInternal(_principalReserve, _user, _amountToLiquidate, _feeLiquidated,
                                                  _balanceIncrease)
        self.updateReserveInterestRatesAndTimestampInternal(_principalReserve, _amountToLiquidate, 0)
        self.updateReserveInterestRatesAndTimestampInternal(_collateralReserve, 0,
                                                            _collateralToLiquidate + _liquidatedCollateralForFee)

    def updatePrincipalReserveStateOnLiquidationInternal(self, _principalReserve: Address, _user: Address,
                                                         _amountToLiquidate: int, _balanceIncrease: int) -> None:
        reserveData = self.getReserveData(_principalReserve)
        self.updateTotalBorrows(_principalReserve, reserveData['totalBorrows'] + _balanceIncrease - _amountToLiquidate)

    def updateCollateralReserveStateOnLiquidationInternal(self, _collateralReserve: Address) -> None:
        self.updateCumulativeIndexes(_collateralReserve)

    def updateUserStateOnLiquidationInternal(self, _reserve: Address, _user: Address, _amountToLiquidate: int,
                                             _feeLiquidated: int, _balanceIncrease: int) -> None:
        reserveData = self.getReserveData(_reserve)
        userData = self.getUserReserveData(_reserve, _user)
        self.updateUserPrincipalBorrowBalance(_reserve, _user, userData[
            'principalBorrowBalance'] - _amountToLiquidate + _balanceIncrease)
        self.updateUserBorrowCumulativeIndex(_reserve, _user, reserveData['borrowCumulativeIndex'])

        if _feeLiquidated > 0:
            self.updateUserOriginationFee(_reserve, _user, userData['originationFee'] - _feeLiquidated)

        self.updateUserLastUpdateTimestamp(_reserve, _user, self.now())

    def setUserUseReserveAsCollateral(self, _reserve: Address, _user: Address, _useAsCollateral: bool) -> None:
        self.updateUserReserveUseAsCollateral(_reserve, _user, _useAsCollateral)

    @external(readonly=True)
    def getUserUnderlyingAssetBalance(self, _reserve: Address, _user: Address) -> int:
        reserveData = self.getReserveData(_reserve)
        oToken = self.create_interface_score(reserveData['oTokenAddress'], oTokenInterface)
        balance = oToken.balanceOf(_user)
        return balance

    @external(readonly=True)
    def getUserOriginationFee(self, _reserve: Address, _user: Address) -> int:
        userReserveData = self.getUserReserveData(_reserve, _user)
        return userReserveData['originationFee']

    @external(readonly=True)
    def getUserBasicReserveData(self, _reserve: Address, _user: Address) -> dict:
        userReserveData = self.getUserReserveData(_reserve, _user)
        underlyingBalance = self.getUserUnderlyingAssetBalance(_reserve, _user)
        if userReserveData['principalBorrowBalance'] == 0:
            return {
                'underlyingBalance': underlyingBalance,
                'compoundedBorrowBalance': 0,
                'originationFee': 0,
                'useAsCollateral': userReserveData['useAsCollateral']
            }

        compoundedBorrowBalance = self.getCompoundedBorrowBalance(_reserve, _user)
        return {
            'underlyingBalance': underlyingBalance,
            'compoundedBorrowBalance': compoundedBorrowBalance,
            'originationFee': userReserveData['originationFee'],
            'useAsCollateral': userReserveData['useAsCollateral']
        }

    @external(readonly=True)
    def getUserBorrowBalances(self, _reserve: Address, _user: Address) -> dict:
        userReserveData = self.getUserReserveData(_reserve, _user)
        principalBorrowBalance = userReserveData['principalBorrowBalance']
        if principalBorrowBalance == 0:
            return {
                "principalBorrowBalance": 0,
                "compoundedBorrowBalance": 0,
                "borrowBalanceIncrease": 0
            }
        compoundedBorrowBalance = self.getCompoundedBorrowBalance(_reserve, _user)
        borrowBalanceIncrease = compoundedBorrowBalance - principalBorrowBalance
        return {
                "principalBorrowBalance": principalBorrowBalance,
                "compoundedBorrowBalance": compoundedBorrowBalance,
                "borrowBalanceIncrease": borrowBalanceIncrease
        }

    def calculateInterestRates(self, _reserve: Address, _availableLiquidity: int, _totalBorrows: int) -> dict:
        constants = self.getReserveConstants(_reserve)
        rate = {}
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
        return rate

    @only_delegation
    @external
    def updatePrepDelegations(self, _delegations: List[PrepDelegations]) -> None:
        staking = self.create_interface_score(self._staking.get(), StakingInterface)
        staking.delegate(_delegations)

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        pass

    @payable
    def fallback(self) -> None:
        pass
