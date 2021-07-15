from .Math import *
from .utils.checks import *

class AddressDetails(TypedDict):
    name: str
    address: Address

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
    ADDRESSES = "addresses"

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._addresses = DictDB(self.ADDRESSES, db, value_type=Address)

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

    @only_address_provider
    @external
    def setAddresses(self, _addressDetails: List[AddressDetails]) -> None:
        for addressDetail in _addressDetails:
            self._addresses[addressDetail['name']] = addressDetail['address']

    @external(readonly=True)
    def getAddress(self, _name: str) -> Address:
        return self._addresses[_name]



    @external(readonly=True)
    def calculateBadDebt(self, _totalBorrowBalanceUSD: int, _totalFeesUSD: int, _totalCollateralBalanceUSD: int,
                         _ltv: int) -> int:
        badDebtUSD = _totalBorrowBalanceUSD - exaMul(_totalCollateralBalanceUSD - _totalFeesUSD, _ltv)

        if badDebtUSD < 0:
            badDebtUSD = 0

        return badDebtUSD

    def calculateAvailableCollateralToLiquidate(self, _collateral: Address, _reserve: Address, _purchaseAmount: int,
                                                _userCollateralBalance: int, _fee: bool) -> dict:
        priceOracle = self.create_interface_score(self.getPriceOracle(), OracleInterface)
        dataProvider = self.create_interface_score(self.getLendingPoolDataProvider(), DataProviderInterface)
        core = self.create_interface_score(self.getLendingPoolCore(), CoreInterface)

        if _fee:
            liquidationBonus = 0
        else:
            collateralConfigs = dataProvider.getReserveConfigurationData(_collateral)
            liquidationBonus = collateralConfigs['liquidationBonus']
        collateralBase = dataProvider.getSymbol(_collateral)
        principalBase = dataProvider.getSymbol(_reserve)

        collateralPrice = priceOracle.get_reference_data(collateralBase, 'USD')
        principalPrice = priceOracle.get_reference_data(principalBase, 'USD')
        if collateralBase == 'ICX':
            staking = self.create_interface_score(self._staking.get(), StakingInterface)
            sicxRate = staking.getTodayRate()
            collateralPrice = exaMul(collateralPrice, sicxRate)
        if principalBase == 'ICX':
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

        return {
            "collateralAmount": collateralAmount,
            "principalAmountNeeded": principalAmountNeeded
        }

    @staticmethod
    def calculateCurrentLiquidationThreshold(_totalBorrowBalanceUSD: int, _totalFeesUSD: int,
                                             _totalCollateralBalanceUSD: int) -> int:
        if _totalCollateralBalanceUSD == 0:
            return 0
        return exaDiv(_totalBorrowBalanceUSD, _totalCollateralBalanceUSD - _totalFeesUSD)

    @external
    def liquidationCall(self, _collateral: Address, _reserve: Address, _user: Address, _purchaseAmount: int) -> dict:
        core = self.create_interface_score(self.getLendingPoolCore(), CoreInterface)
        priceOracle = self.create_interface_score(self.getPriceOracle(), OracleInterface)
        dataProvider = self.create_interface_score(self.getLendingPoolDataProvider(), DataProviderInterface)
        principalBase = dataProvider.getSymbol(_reserve)
        principalPrice = priceOracle.get_reference_data(principalBase, 'USD')
        userAccountData = dataProvider.getUserAccountData(_user)
        reserveData = dataProvider.getReserveData(_reserve)

        liquidatedCollateralForFee = 0
        feeLiquidated = 0

        reserveLiquidationThreshold = reserveData['liquidationThreshold']
        userLiquidationThreshold = self.calculateCurrentLiquidationThreshold(userAccountData['totalBorrowBalanceUSD'],
                                                                             userAccountData['totalFeesUSD'],
                                                                             userAccountData[
                                                                                 'totalCollateralBalanceUSD'])

        if reserveLiquidationThreshold >= userLiquidationThreshold:
            revert(f'{TAG}: '
                   f'unsuccessful liquidation call,user is below liquidation threshold'
                   f'liquidation threshold of reserve is {reserveLiquidationThreshold}'
                   f'user ltv is {userLiquidationThreshold}')
        userHealthFactor = userAccountData['healthFactor']
        if not userAccountData['healthFactorBelowThreshold']:
            revert(f'{TAG}: '
                   f'unsuccessful liquidation call,health factor of user is above 1'
                   f'health factor of user {userHealthFactor}')

        userCollateralBalance = core.getUserUnderlyingAssetBalance(_collateral, _user)
        if userCollateralBalance == 0:
            revert(f'{TAG}: '
                   f'unsuccessful liquidation call,user have no collateral balance'
                   f'for collateral {_collateral}'
                   f'balance of user: {_user} is {userCollateralBalance}')

        userBorrowBalances = core.getUserBorrowBalances(_reserve, _user)
        if userBorrowBalances['compoundedBorrowBalance'] == 0:
            revert(f'{TAG}: '
                   f'unsuccessful liquidation call,user have no borrow balance'
                   f'for reserve {_reserve}'
                   f'borrow balance of user: {_user} is {userBorrowBalances}')
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
        if feeLiquidated > 0:
            collateralOtoken.burnOnLiquidation(_user, liquidatedCollateralForFee)
            # the liquidated fee is sent to fee provider
            core.liquidateFee(_collateral, liquidatedCollateralForFee, self.getFeeProvider())
            self.OriginationFeeLiquidated(_collateral, _reserve, _user, feeLiquidated, liquidatedCollateralForFee,
                                          self.now())
        self.LiquidationCall(_collateral, _reserve, _user, actualAmountToLiquidate, maxCollateralToLiquidate,
                             userBorrowBalances['borrowBalanceIncrease'], self.tx.origin, self.now())
        return {
            'maxCollateralToLiquidate': maxCollateralToLiquidate,
            'actualAmountToLiquidate': actualAmountToLiquidate
        }
