from .utils.math import *
from .utils.checks import *
from .addresses import *
from .interfaces import *


class LiquidationManager(Addresses):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self, _addressProvider: Address) -> None:
        super().on_install(_addressProvider)

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=3)
    def OriginationFeeLiquidated(self, _collateral: Address, _reserve: Address, _user: Address, _feeLiquidated: int,
                                 _liquidatedCollateralForFee: int):
        pass

    @eventlog(indexed=3)
    def LiquidationCall(self, _collateral: Address, _reserve: Address, _user: Address, _purchaseAmount: int,
                        _liquidatedCollateralAmount: int, _accruedBorrowInterest: int, _liquidator: Address):
        pass

    @external(readonly=True)
    def name(self) -> str:
        return f"Omm {TAG}"

    @external(readonly=True)
    def calculateBadDebt(self, _totalBorrowBalanceUSD: int, _totalFeesUSD: int, _totalCollateralBalanceUSD: int,
                         _ltv: int) -> int:
        badDebtUSD = _totalBorrowBalanceUSD - exaMul(_totalCollateralBalanceUSD - _totalFeesUSD, _ltv)

        if badDebtUSD < 0:
            badDebtUSD = 0

        return badDebtUSD

    def calculateAvailableCollateralToLiquidate(self, _collateral: Address, _reserve: Address, _purchaseAmount: int,
                                                _userCollateralBalance: int, _fee: bool) -> dict:
        priceOracle = self.create_interface_score(self.getAddress(PRICE_ORACLE), OracleInterface)
        dataProvider = self.create_interface_score(self.getAddress(LENDING_POOL_DATA_PROVIDER), DataProviderInterface)
        core = self.create_interface_score(self.getAddress(LENDING_POOL_CORE), CoreInterface)

        if _fee:
            liquidationBonus = 0
        else:
            collateralConfigs = dataProvider.getReserveConfigurationData(_collateral)
            liquidationBonus = collateralConfigs['liquidationBonus']
        collateralBase = dataProvider.getSymbol(_collateral)
        principalBase = dataProvider.getSymbol(_reserve)

        collateralPrice = priceOracle.get_reference_data(collateralBase, 'USD')
        principalPrice = priceOracle.get_reference_data(principalBase, 'USD')
        _stakingAddress=self.getAddress(STAKING)
        if collateralBase == 'ICX':
            staking = self.create_interface_score(_stakingAddress, StakingInterface)
            sicxRate = staking.getTodayRate()
            collateralPrice = exaMul(collateralPrice, sicxRate)
        if principalBase == 'ICX':
            staking = self.create_interface_score(_stakingAddress, StakingInterface)
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

    @only_lending_pool
    @external
    def liquidationCall(self, _collateral: Address, _reserve: Address, _user: Address, _purchaseAmount: int) -> dict:
        core = self.create_interface_score(self.getAddress(LENDING_POOL_CORE), CoreInterface)
        priceOracle = self.create_interface_score(self.getAddress(PRICE_ORACLE), OracleInterface)
        dataProvider = self.create_interface_score(self.getAddress(LENDING_POOL_DATA_PROVIDER), DataProviderInterface)
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
            core.liquidateFee(_collateral, liquidatedCollateralForFee, self.getAddress(FEE_PROVIDER))
            self.OriginationFeeLiquidated(_collateral, _reserve, _user, feeLiquidated, liquidatedCollateralForFee)
        self.LiquidationCall(_collateral, _reserve, _user, actualAmountToLiquidate, maxCollateralToLiquidate,
                             userBorrowBalances['borrowBalanceIncrease'], self.tx.origin)
        return {
            'maxCollateralToLiquidate': maxCollateralToLiquidate,
            'actualAmountToLiquidate': actualAmountToLiquidate
        }
