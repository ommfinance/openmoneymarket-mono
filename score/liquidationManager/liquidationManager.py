from iconservice import *
from .Math import *
from .utils.checks import *

TAG = 'LiquidationManager'


class DataProviderInterface(InterfaceScore):
    @interface
    def getUserAccountData(self, _user: Address) -> dict:
        pass

    @interface
    def getReserveData(self, _reserve: Address) -> dict:
        pass

    @interface
    def getSymbol(self, _reserveAddress: Address) -> str:
        pass

    @interface
    def getReserveConfigurationData(self, _reserve: Address) -> dict:
        pass


class CoreInterface(InterfaceScore):
    @interface
    def getUserUnderlyingAssetBalance(self, _reserve: Address, _user: Address) -> int:
        pass

    @interface
    def getUserBorrowBalances(self, _reserve: Address, _user: Address):
        pass

    @interface
    def getReserveConfiguration(self, _reserve: Address) -> dict:
        pass

    @interface
    def getUserOriginationFee(self, _reserve: Address, _user: Address) -> int:
        pass

    @interface
    def updateStateOnLiquidation(self, _principalReserve: Address, _collateralReserve: Address, _user: Address,
                                 _amountToLiquidate: int, _collateralToLiquidate: int, _feeLiquidated: int,
                                 _liquidatedCollateralForFee: int, _balanceIncrease: int):
        pass

    @interface
    def getReserveOTokenAddress(self, _reserve: Address) -> Address:
        pass

    @interface
    def transferToUser(self, _reserve: Address, _user: Address, _amount: int) -> None:
        pass

    @interface
    def liquidateFee(self, _reserve: Address, _amount: int, _destination: Address) -> None:
        pass


class OtokenInterface(InterfaceScore):
    @interface
    def burnOnLiquidation(self, _user: Address, _value: int) -> None:
        pass


class ReserveInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _amount: int) -> None:
        pass


class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> int:
        pass


class StakingInterface(InterfaceScore):
    @interface
    def getTodayRate(self) -> int:
        pass


class LiquidationManager(IconScoreBase):
    _LENDING_POOL_DATA_PROVIDER = 'lendingPoolDataProvider'
    _LENDINGPOOLCORE = 'lendingPoolCore'
    _PRICE_ORACLE = 'priceOracle'
    _FEE_PROVIDER = 'feeProvider'
    _STAKING = 'staking'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._lendingPoolDataProvider = VarDB(self._LENDING_POOL_DATA_PROVIDER, db, value_type=Address)
        self._lendingPoolCore = VarDB(self._LENDINGPOOLCORE, db, value_type=Address)
        self._priceOracle = VarDB(self._PRICE_ORACLE, db, value_type=Address)
        self._feeProvider = VarDB(self._FEE_PROVIDER, db, value_type=Address)
        self._staking = VarDB(self._STAKING, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=3)
    def OriginationFeeLiquidated(self, _collateral: Address, _reserve: Address, _user: Address, _feeLiquidated: int,
                                 _liquidatedCollateralForFee: int, _timestamp: int):
        pass

    @eventlog(indexed=3)
    def LiquidationCall(self, _collateral: Address, _reserve: Address, _user: Address, _purchaseAmount: int,
                        _liquidatedCollateralAmount: int, _accruedBorrowInterest: int, _liquidator: Address,
                        _timestamp: int):
        pass

    @external(readonly=True)
    def name(self) -> str:
        return "OmmLiquidationManager"

    @only_owner
    @external
    def setLendingPoolDataProvider(self, _address: Address) -> None:
        self._lendingPoolDataProvider.set(_address)

    @external(readonly=True)
    def getLendingPoolDataProvider(self) -> Address:
        return self._lendingPoolDataProvider.get()

    @only_owner
    @external
    def setFeeProvider(self, _address: Address) -> None:
        self._feeProvider.set(_address)

    @external(readonly=True)
    def getFeeProvider(self) -> Address:
        return self._feeProvider.get()

    @only_owner
    @external
    def setLendingPoolCore(self, _address: Address):
        self._lendingPoolCore.set(_address)

    @external(readonly=True)
    def getLendingPoolCore(self) -> Address:
        return self._lendingPoolCore.get()

    @only_owner
    @external
    def setPriceOracle(self, _address: Address):
        self._priceOracle.set(_address)

    @external(readonly=True)
    def getPriceOracle(self) -> Address:
        return self._priceOracle.get()

    @only_owner
    @external
    def setStaking(self, _address: Address):
        self._staking.set(_address)

    @external(readonly=True)
    def getStaking(self) -> Address:
        return self._staking.get()

    @external(readonly=True)
    def calculateBadDebt(self, _totalBorrowBalanceUSD: int, _totalFeesUSD: int, _totalCollateralBalanceUSD: int,
                         _ltv: int) -> int:
        priceOracle = self.create_interface_score(self.getPriceOracle(), OracleInterface)
        badDebtUSD = _totalBorrowBalanceUSD - exaMul(_totalCollateralBalanceUSD - _totalFeesUSD, _ltv)

        if badDebtUSD < 0:
            badDebtUSD = 0

        return badDebtUSD

    def calculateAvailableCollateralToLiquidate(self, _collateral: Address, _reserve: Address, _purchaseAmount: int,
                                                _userCollateralBalance: int, _fee: bool) -> dict:
        priceOracle = self.create_interface_score(self.getPriceOracle(), OracleInterface)
        dataProvider = self.create_interface_score(self.getLendingPoolDataProvider(), DataProviderInterface)
        core = self.create_interface_score(self.getLendingPoolCore(), CoreInterface)

        collateralConfigs = dataProvider.getReserveConfigurationData(_collateral)
        liquidationBonus = collateralConfigs['liquidationBonus']
        if _fee:
            liquidationBonus = 0
        collateralBase = dataProvider.getSymbol(_collateral)
        principalBase = dataProvider.getSymbol(_reserve)

        collateralPrice = priceOracle.get_reference_data(collateralBase, 'USD')
        principalPrice = priceOracle.get_reference_data(principalBase, 'USD')
        if collateralBase == 'ICX':
            staking = self.create_interface_score(self._staking.get(), StakingInterface)
            sicxRate = staking.getTodayRate()
            collateralPrice = exaMul(collateralPrice, sicxRate)
        if principalPrice == 'ICX':
            staking = self.create_interface_score(self._staking.get(), StakingInterface)
            sicxRate = staking.getTodayRate()
            principalPrice = exaMul(principalPrice, sicxRate)
        reserveConfiguration = core.getReserveConfiguration(_reserve)
        reserveDecimals = reserveConfiguration['decimals']
        reserveConfiguration = core.getReserveConfiguration(_collateral)
        collateralDecimals = reserveConfiguration['decimals']

        userCollateralUSD = exaMul(convertToExa(_userCollateralBalance, collateralDecimals), collateralPrice)
        purchaseAmountUSD = exaMul(convertToExa(_purchaseAmount, reserveDecimals), principalPrice)

        maxCollateralToLiquidate = convertExaToOther(
            exaDiv(exaMul(purchaseAmountUSD, EXA + liquidationBonus), collateralPrice), collateralDecimals)
        if maxCollateralToLiquidate > _userCollateralBalance:
            collateralAmount = _userCollateralBalance
            principalAmountNeeded = convertExaToOther(
                exaDiv(exaDiv(userCollateralUSD, EXA + liquidationBonus), principalPrice), reserveDecimals)
        else:
            collateralAmount = maxCollateralToLiquidate
            principalAmountNeeded = _purchaseAmount
        response = {"collateralAmount": collateralAmount,
                    "principalAmountNeeded": principalAmountNeeded}
        return response

    def calculateCurrentLiquidationThreshold(self, _totalBorrowBalanceUSD: int, _totalFeesUSD: int,
                                             _totalCollateralBalanceUSD: int) -> int:
        if _totalCollateralBalanceUSD == 0:
            return 0
        liquidationThreshold = exaDiv(_totalBorrowBalanceUSD, _totalCollateralBalanceUSD - _totalFeesUSD)
        return liquidationThreshold

    @external
    def liquidationCall(self, _collateral: Address, _reserve: Address, _user: Address, _purchaseAmount: int) -> dict:
        dataProvider = self.create_interface_score(self.getLendingPoolDataProvider(), DataProviderInterface)
        core = self.create_interface_score(self.getLendingPoolCore(), CoreInterface)
        priceOracle = self.create_interface_score(self.getPriceOracle(), OracleInterface)
        dataProvider = self.create_interface_score(self.getLendingPoolDataProvider(), DataProviderInterface)
        principalBase = dataProvider.getSymbol(_reserve)
        principalPrice = priceOracle.get_reference_data(principalBase, 'USD')
        userAccountData = dataProvider.getUserAccountData(_user)
        reserveData = dataProvider.getReserveData(_reserve)

        actualAmountToLiquidate = 0
        liquidatedCollateralForFee = 0
        feeLiquidated = 0

        reserveLiquidationThreshold = reserveData['liquidationThreshold']
        userLiquidationThreshold = self.calculateCurrentLiquidationThreshold(userAccountData['totalBorrowBalanceUSD'],
                                                                             userAccountData['totalFeesUSD'],
                                                                             userAccountData[
                                                                                 'totalCollateralBalanceUSD'])

        if reserveLiquidationThreshold >= userLiquidationThreshold:
            revert("Liquidation manager SCORE : Unsuccessful liquidation call-user is below liquidation threshold")

        if not userAccountData['healthFactorBelowThreshold']:
            revert("Liquidation manager SCORE : Unsuccessful liquidation call-health factor is above threshold")

        userCollateralBalance = core.getUserUnderlyingAssetBalance(_collateral, _user)
        if userCollateralBalance == 0:
            revert(
                'Liquidation manager SCORE : Unsuccessful liquidation call-user dont have any collateral to liquidate')

        userBorrowBalances = core.getUserBorrowBalances(_reserve, _user)
        if userBorrowBalances['compoundedBorrowBalance'] == 0:
            revert('Liquidation manager SCORE : Unsuccessful liquidation call-user dont have any borrow')
        maxPrincipalAmountToLiquidateUSD = self.calculateBadDebt(userAccountData['totalBorrowBalanceUSD'],
                                                                 userAccountData['totalFeesUSD'],
                                                                 userAccountData['totalCollateralBalanceUSD'],
                                                                 userAccountData['currentLtv'])
        maxPrincipalAmountToLiquidate = exaDiv(maxPrincipalAmountToLiquidateUSD, principalPrice)
        reserveConfiguration = core.getReserveConfiguration(_reserve)
        reserveDecimals = reserveConfiguration['decimals']

        # converting the user balances into 18 decimals
        if reserveDecimals != 18:
            maxPrincipalAmountToLiquidate = convertExaToOther(maxPrincipalAmountToLiquidate, reserveDecimals)

        if _purchaseAmount > maxPrincipalAmountToLiquidate:
            actualAmountToLiquidate = maxPrincipalAmountToLiquidate
        else:
            actualAmountToLiquidate = _purchaseAmount

        liquidationDetails = self.calculateAvailableCollateralToLiquidate(_collateral, _reserve,
                                                                          actualAmountToLiquidate,
                                                                          userCollateralBalance, False)
        maxCollateralToLiquidate = liquidationDetails['collateralAmount']
        principalAmountNeeded = liquidationDetails['principalAmountNeeded']
        userOriginationFee = core.getUserOriginationFee(_reserve, _user)
        if userOriginationFee > 0:
            feeLiquidationDetails = self.calculateAvailableCollateralToLiquidate(_collateral, _reserve,
                                                                                 userOriginationFee,
                                                                                 userCollateralBalance - maxCollateralToLiquidate,
                                                                                 True)
            liquidatedCollateralForFee = feeLiquidationDetails['collateralAmount']
            feeLiquidated = feeLiquidationDetails['principalAmountNeeded']
        if principalAmountNeeded < actualAmountToLiquidate:
            actualAmountToLiquidate = principalAmountNeeded
        core.updateStateOnLiquidation(_reserve, _collateral, _user, actualAmountToLiquidate, maxCollateralToLiquidate,
                                      feeLiquidated, liquidatedCollateralForFee,
                                      userBorrowBalances['borrowBalanceIncrease'])
        collateralOtokenAddress = core.getReserveOTokenAddress(_collateral)
        collateralOtoken = self.create_interface_score(collateralOtokenAddress, OtokenInterface)
        collateralOtoken.burnOnLiquidation(_user, maxCollateralToLiquidate)
        # core.transferToUser(_collateral, self.msg.sender, maxCollateralToLiquidate)
        # # have a deeper look at this part (transfering principal currency to the pool)
        #
        # principalCurrency = self.create_interface_score(_reserve, ReserveInterface)
        # principalCurrency.transfer(self.getLendingPoolCore(), actualAmountToLiquidate)

        if feeLiquidated > 0:
            collateralOtoken.burnOnLiquidation(_user, liquidatedCollateralForFee)
            # the liquidated fee is sent to fee provider
            core.liquidateFee(_collateral, liquidatedCollateralForFee, self.getFeeProvider())
            self.OriginationFeeLiquidated(_collateral, _reserve, _user, feeLiquidated, liquidatedCollateralForFee,
                                          self.now())
        self.LiquidationCall(_collateral, _reserve, _user, actualAmountToLiquidate, maxCollateralToLiquidate,
                             userBorrowBalances['borrowBalanceIncrease'], self.tx.origin, self.now())
        response = {'maxCollateralToLiquidate': maxCollateralToLiquidate,
                    'actualAmountToLiquidate': actualAmountToLiquidate}
        return response
