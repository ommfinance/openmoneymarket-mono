from iconservice import *
from .Math import *

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


class LiquidationManager(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._dataProviderAddress = VarDB('data_provider_address', db, value_type=Address)
        self._coreAddress = VarDB('core_address', db, value_type=Address)
        self._priceOracleAddress = VarDB('price_oracle', db, value_type=Address)
        self._feeProviderAddress = VarDB('fee_provider_address', db, value_type=Address)

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

    @external
    def setDataProviderAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert("Data provider set error:Not authorized")
        self._dataProviderAddress.set(_address)

    @external(readonly=True)
    def getDataProviderAddress(self) -> Address:
        return self._dataProviderAddress.get()

    @external
    def setFeeProviderAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert("Fee provider set error:Not authorized")
        self._feeProviderAddress.set(_address)

    @external(readonly=True)
    def getFeeProviderAddress(self) -> Address:
        return self._feeProviderAddress.get()

    @external
    def setCoreAddress(self, _address: Address):
        if self.msg.sender != self.owner:
            revert("Core address set error:Not authorized")
        self._coreAddress.set(_address)

    @external(readonly=True)
    def getCoreAddress(self):
        return self._coreAddress.get()

    @external
    def setOracleAddress(self, _address: Address):
        if self.msg.sender != self.owner:
            revert("Core address set error:Not authorized")
        self._priceOracleAddress.set(_address)

    @external(readonly=True)
    def getOracleAddress(self):
        return self._priceOracleAddress.get()

    def calculateBadDebt(self, _totalBorrowBalanceUSD: int, _totalFeesUSD: int, _totalCollateralBalanceUSD: int,
                         _reserve: Address, _ltv:int) -> int:
        priceOracle = self.create_interface_score(self.getOracleAddress(), OracleInterface)
        dataProvider = self.create_interface_score(self.getDataProviderAddress(), DataProviderInterface)
        principalBase = dataProvider.getSymbol(_reserve)
        principalPrice = priceOracle.get_reference_data(principalBase, 'USD')
        badDebtUSD = _totalBorrowBalanceUSD + _totalFeesUSD - exaMul(_totalCollateralBalanceUSD, _ltv)
        badDebt = exaMul(badDebtUSD, principalPrice)
               
        return badDebt

    def calculateAvailableCollateralToLiquidate(self, _collateral: Address, _reserve: Address, _purchaseAmount: int,
                                                _userCollateralBalance: int) -> dict:
        priceOracle = self.create_interface_score(self.getOracleAddress(), OracleInterface)
        dataProvider = self.create_interface_score(self.getDataProviderAddress(), DataProviderInterface)

        collateralConfigs = dataProvider.getReserveConfigurationData(_collateral)
        liquidationBonus = collateralConfigs['liquidationBonus']

        collateralBase = dataProvider.getSymbol(_collateral)
        principalBase = dataProvider.getSymbol(_reserve)

        collateralPrice = priceOracle.get_reference_data(collateralBase, 'USD')
        principalPrice = priceOracle.get_reference_data(principalBase, 'USD')

        userCollateralUSD = exaMul(_userCollateralBalance, collateralPrice)
        purchaseAmountUSD = exaMul(_purchaseAmount, principalPrice)

        maxCollateralToLiquidate = exaDiv(exaMul(purchaseAmountUSD, EXA + liquidationBonus), collateralPrice)
        if maxCollateralToLiquidate > _userCollateralBalance:
            collateralAmount = _userCollateralBalance
            principalAmountNeeded = exaDiv(exaDiv(userCollateralUSD, EXA + liquidationBonus), principalPrice)
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
        liquidationThreshold = exaDiv(_totalBorrowBalanceUSD + _totalFeesUSD, _totalCollateralBalanceUSD)
        return liquidationThreshold

    @external
    def liquidationCall(self, _collateral: Address, _reserve: Address, _user: Address, _purchaseAmount: int) -> dict:
        dataProvider = self.create_interface_score(self.getDataProviderAddress(), DataProviderInterface)
        core = self.create_interface_score(self.getCoreAddress(), CoreInterface)

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
            revert("Liquidation call error: The user cant get liquidated")

        if not userAccountData['healthFactorBelowThreshold']:
            revert("Liquidation call error:The health factor is not below threshold")

        userCollateralBalance = core.getUserUnderlyingAssetBalance(_collateral, _user)
        if userCollateralBalance == 0:
            revert('Liquidation call error:No collateral to be liquidated')

        userBorrowBalances = core.getUserBorrowBalances(_reserve, _user)
        if userBorrowBalances['compoundedBorrowBalance'] == 0:
            revert('Liquidation call error: No borrow by the user')
        maxPrincipalAmountToLiquidate = self.calculateBadDebt(userAccountData['totalBorrowBalanceUSD'],
                                                              userAccountData['totalFeesUSD'],
                                                              userAccountData['totalCollateralBalanceUSD'],
                                                              _reserve,
                                                              userAccountData['currentLtv'])
        if _purchaseAmount > maxPrincipalAmountToLiquidate:
            actualAmountToLiquidate = maxPrincipalAmountToLiquidate
        else:
            actualAmountToLiquidate = _purchaseAmount
        liquidationDetails = self.calculateAvailableCollateralToLiquidate(_collateral, _reserve,
                                                                          actualAmountToLiquidate,
                                                                          userCollateralBalance)
        maxCollateralToLiquidate = liquidationDetails['collateralAmount']
        principalAmountNeeded = liquidationDetails['principalAmountNeeded']
        userOriginationFee = core.getUserOriginationFee(_reserve, _user)
        if userOriginationFee > 0:
            feeLiquidationDetails = self.calculateAvailableCollateralToLiquidate(_collateral, _reserve,
                                                                                 userOriginationFee,
                                                                                 userCollateralBalance - maxCollateralToLiquidate)
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
        # principalCurrency.transfer(self.getCoreAddress(), actualAmountToLiquidate)

        if feeLiquidated > 0:
            collateralOtoken.burnOnLiquidation(_user, liquidatedCollateralForFee)
            # the liquidated fee is sent to fee provider
            core.liquidateFee(_collateral, liquidatedCollateralForFee, self.getFeeProviderAddress())
            self.OriginationFeeLiquidated(_collateral, _reserve, _user, feeLiquidated, liquidatedCollateralForFee,
                                          self.now())
        self.LiquidationCall(_collateral, _reserve, _user, actualAmountToLiquidate, maxCollateralToLiquidate,
                             userBorrowBalances['borrowBalanceIncrease'], self.tx.origin, self.now())
        response = {'maxCollateralToLiquidate': maxCollateralToLiquidate,
                    'actualAmountToLiquidate': actualAmountToLiquidate}
        return response
