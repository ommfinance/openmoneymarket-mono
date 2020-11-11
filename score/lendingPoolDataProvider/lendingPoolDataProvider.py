from iconservice import *
from .Math import *

TAG = 'LendingPoolDataProvider'

HEALTH_FACTOR_LIQUIDATION_THRESHOLD = 10 ** 18


# An interface to LendingPoolCore
class CoreInterface(InterfaceScore):
    @interface
    def getReserves(self) -> list:
        pass

    @interface
    def getUserBasicReserveData(self, _reserve: Address, _user: Address) -> dict:
        pass

    @interface
    def getReserveConfiguration(self, _reserve: Address) -> dict:
        pass

    @interface
    def getReserveData(self, _reserve: Address) -> dict:
        pass

    @interface
    def getUserReserveData(self, _reserve: Address, _user: Address) -> dict:
        pass

    @interface
    def getReserveConfiguration(self, _reserve) -> dict:
        pass

    @interface
    def getCompoundedBorrowBalance(self, _reserve: Address, _user: Address) -> int:
        pass


# An interface to PriceOracle
class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> int:
        pass


# An interface to oToken
class oTokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass


class LendingPoolDataProvider(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._symbol = DictDB('symbol', db, value_type=str)
        self._lendingPoolCoreAddress = VarDB('lendingPoolCore', db, value_type=Address)
        self._oracleAddress = VarDB('oracleAddress', db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external
    def setSymbol(self, _reserveAddress: Address, _sym: str):
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')
        self._symbol[_reserveAddress] = _sym

    @external
    def getSymbol(self,_reserveAddress:Address)->str:
        return self._symbol[_reserveAddress]
        
    @external
    def setLendingPoolCoreAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._lendingPoolCoreAddress.set(_address)

    @external
    def setOracleAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._oracleAddress.set(_address)

    @external(readonly=True)
    def getLendingPoolCoreAddress(self) -> Address:
        return self._lendingPoolCoreAddress.get()

    @external(readonly=True)
    def getOracleAddress(self) -> Address:
        return self._oracleAddress.get()
    
    @external(readonly=True)
    def getUserAccountData(self, _user: Address) -> dict:
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        oracle = self.create_interface_score(self._oracleAddress.get(), OracleInterface)
        totalLiquidityBalanceUSD = 0
        totalCollateralBalanceUSD = 0
        currentLtv = 0
        currentLiquidationThreshold = 0
        totalBorrowBalanceUSD = 0
        totalFeesUSD = 0
        healthFactorBelowThreshold = False

        reserves = core.getReserves()
        for _reserve in reserves:
            userBasicReserveData = core.getUserBasicReserveData(_reserve, _user)
            if userBasicReserveData['underlyingBalance'] == 0 and userBasicReserveData['compoundedBorrowBalance'] == 0:
                continue

            reserveConfiguration = core.getReserveConfiguration(_reserve)

            reserveConfiguration['reserveUnitPrice'] = oracle.get_reference_data(self._symbol[_reserve], 'USD')

            if userBasicReserveData['underlyingBalance'] > 0:
                liquidityBalanceUSD = exaMul(reserveConfiguration['reserveUnitPrice'],userBasicReserveData['underlyingBalance'])
                totalLiquidityBalanceUSD += liquidityBalanceUSD

                if reserveConfiguration['usageAsCollateralEnabled'] and userBasicReserveData['useAsCollateral']:
                    
                    totalCollateralBalanceUSD += liquidityBalanceUSD
                    currentLtv += exaMul(liquidityBalanceUSD, reserveConfiguration['baseLTVasCollateral'])
                    # revert("Reached data provider")
                    currentLiquidationThreshold += exaMul(liquidityBalanceUSD,
                                                          reserveConfiguration['liquidationThreshold'])

            if userBasicReserveData['compoundedBorrowBalance'] > 0:
                totalBorrowBalanceUSD += exaMul(reserveConfiguration['reserveUnitPrice'],
                                                userBasicReserveData['compoundedBorrowBalance'])
                totalFeesUSD += exaMul(reserveConfiguration['reserveUnitPrice'], userBasicReserveData['originationFee'])

        if totalCollateralBalanceUSD > 0:
            currentLtv = exaDiv(currentLtv,totalCollateralBalanceUSD)
        else:
            currentLtv = 0

        healthFactor = self.calculateHealthFactorFromBalancesInternal(totalCollateralBalanceUSD, totalBorrowBalanceUSD,
                                                                      totalFeesUSD, currentLiquidationThreshold)
        if healthFactor < HEALTH_FACTOR_LIQUIDATION_THRESHOLD and  healthFactor !=- 1:
            healthFactorBelowThreshold = True
        
        response = {
            'totalLiquidityBalanceUSD': totalLiquidityBalanceUSD,
            'totalCollateralBalanceUSD': totalCollateralBalanceUSD,
            'totalBorrowBalanceUSD': totalBorrowBalanceUSD,
            'totalFeesUSD': totalFeesUSD,
            'currentLtv': currentLtv,
            'currentLiquidationThreshold': currentLiquidationThreshold,
            'healthFactor': healthFactor,
            'healthFactorBelowThreshold': healthFactorBelowThreshold
        }

        return response

    @external(readonly=True)
    def getUserReserveData(self, _reserve: Address, _user: Address) -> dict:
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        reserveData = core.getReserveData(_reserve)
        userReserveData = core.getUserReserveData(_reserve, _user)
        oToken = self.create_interface_score(reserveData['oTokenAddress'], oTokenInterface)
        currentOTokenBalance = oToken.balanceOf(_user)
        principalBorrowBalance = userReserveData['principalBorrowBalance']
        currentBorrowBalance = core.getCompoundedBorrowBalance(_reserve, _user)
        borrowRate = reserveData['borrowRate']
        liquidityRate = reserveData['liquidityRate']
        originationFee = userReserveData['originationFee']
        userBorrowCumulativeIndex = userReserveData['userBorrowCumulativeIndex']
        lastUpdateTimestamp = userReserveData['lastUpdateTimestamp']
        useAsCollateral = userReserveData['useAsCollateral']
        price_provider = self.create_interface_score(self._oracleAddress.get(), OracleInterface)
        price = price_provider.get_reference_data(self._symbol[_reserve], "USD")
        currentOTokenBalanceUSD = exaMul(currentOTokenBalance, price)
        currentBorrowBalanceUSD = exaMul(currentBorrowBalance, price)
        principalBorrowBalanceUSD = exaMul(principalBorrowBalance, price)
        response = {
            'currentOTokenBalance': currentOTokenBalance,
            'currentOTokenBalanceUSD': currentOTokenBalanceUSD,
            'currentBorrowBalance': currentBorrowBalance,
            'currentBorrowBalanceUSD': currentBorrowBalanceUSD,
            'principalBorrowBalance': principalBorrowBalance,
            'principalBorrowBalanceUSD': principalBorrowBalanceUSD,
            'borrowRate': borrowRate,
            'liquidityRate': liquidityRate,
            'originationFee': originationFee,
            'userBorrowCumulativeIndex': userBorrowCumulativeIndex,
            'lastUpdateTimestamp': lastUpdateTimestamp,
            'useAsCollateral': useAsCollateral
        }

        return response


    @external(readonly=True)
    def balanceDecreaseAllowed(self, _reserve: Address, _user: Address, _amount: int) -> bool:
            core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
            reserveConfiguration = core.getReserveConfiguration(_reserve)
            userReserveData = core.getUserReserveData(_reserve, _user)
            reserveLiquidationThreshold = reserveConfiguration['liquidationThreshold']
            reserveUsageAsCollateralEnabled = reserveConfiguration['usageAsCollateralEnabled']

            if not reserveUsageAsCollateralEnabled or not userReserveData['useAsCollateral']:
                return True

            userAccountData = self.getUserAccountData(_user)
            collateralBalanceUSD = userAccountData['totalCollateralBalanceUSD']
            borrowBalanceUSD = userAccountData['totalBorrowBalanceUSD']
            totalFeesUSD = userAccountData['totalFeesUSD']
            currentLiquidationThreshold = userAccountData['currentLiquidationThreshold']

            if borrowBalanceUSD == 0:
                return True

            oracle = self.create_interface_score(self._oracleAddress.get(), OracleInterface)
            
            amountToDecreaseUSD = exaMul( oracle.get_reference_data(self._symbol[_reserve], 'USD') , _amount )
            collateralBalanceAfterDecreaseUSD = collateralBalanceUSD - amountToDecreaseUSD

            if collateralBalanceAfterDecreaseUSD == 0:
                return False

            liquidationThresholdAfterDecrease =exaDiv( (exaMul(collateralBalanceUSD, currentLiquidationThreshold) - exaMul( amountToDecreaseUSD , reserveLiquidationThreshold)), collateralBalanceAfterDecreaseUSD )

            healthFactorAfterDecrease = self.calculateHealthFactorFromBalancesInternal( collateralBalanceAfterDecreaseUSD , borrowBalanceUSD , totalFeesUSD , liquidationThresholdAfterDecrease)

            return healthFactorAfterDecrease > HEALTH_FACTOR_LIQUIDATION_THRESHOLD

            
            

    @external(readonly=True)
    def calculateCollateralNeededUSD(self, _reserve: Address, _amount: int, _fee: int, _userCurrentBorrowBalanceUSD: int,
                                     _userCurrentFeesUSD: int, _userCurrentLtv: int) -> int:

        price_provider = self.create_interface_score(self._oracleAddress.get(), OracleInterface)
        price = price_provider.get_reference_data(self._symbol[_reserve], "USD")
        requestedBorrowUSD = exaMul(price, _amount)

        collateralNeededInUSD = exaDiv(_userCurrentBorrowBalanceUSD + _userCurrentFeesUSD+requestedBorrowUSD, _userCurrentLtv)
        return collateralNeededInUSD


    @external(readonly=True)
    def getUserAllReserveData(self, _user: Address) -> dict:
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        reserves = core.getReserves()
        userData = {}
        for reserve in reserves:
            userData[self._symbol[reserve]] = self.getUserReserveData(reserve, _user)

        return userData

    def calculateHealthFactorFromBalancesInternal(self, _collateralBalanceUSD: int, _borrowBalanceUSD: int,
                                                  _totalFeesUSD: int, _liquidationThreshold: int) -> int:
        if _borrowBalanceUSD == 0:
            return -1
        healthFactor =exaDiv(exaMul(_collateralBalanceUSD, _liquidationThreshold),_borrowBalanceUSD + _totalFeesUSD) 
        return healthFactor

    def calculateBorrowingPowerFromBalancesInternal(self, _collateralBalanceUSD: int, _borrowBalanceUSD: int,
                                                    _totalFeesUSD: int, _ltv: int) -> int:
        borrowingPower = exaDiv((_borrowBalanceUSD + _totalFeesUSD), exaMul(_collateralBalanceUSD , _ltv))
        return borrowingPower

    @external(readonly=True)
    def getReserveData(self, _reserve: Address) -> dict:
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        return core.getReserveData(_reserve)

    @external(readonly=True)
    def getAllReserveData(self) -> dict:
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        reserves = core.getReserves()
        response = {}
        for reserve in reserves:
            response[self._symbol[reserve]] = core.getReserveData(reserve)

        return response

    @external(readonly=True)
    def getReserveConfigurationData(self, _reserve: Address) -> dict:
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        return core.getReserveConfiguration(_reserve)

    @external(readonly=True)
    def getAllReserveConfigurationData(self) -> dict:
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        reserves = core.getReserves()
        response = {}
        for reserve in reserves:
            response[self._symbol[reserve]] = core.getReserveConfiguration(reserve)

        return response
