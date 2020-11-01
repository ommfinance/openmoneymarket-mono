from iconservice import *

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
    def getReserveData(self, _reserveAddress: Address) -> dict:
        pass

    @interface
    def getReserveConfiguration(self, _reserve) -> dict:
        pass

# An interface to PriceOracle
class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> int:
        pass


class LendingPoolDataProvider(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._symbol = DictDB('symbol', db , value_type = str)
        self._lendingPoolCoreAddress = VarDB('lendingPoolCore', db, value_type = Address)
        self._oracleAddress = VarDB('oracleAddress', db, value_type = Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()
        self._symbol[Address.from_string("cx072d8f95877a53df350e3dc3d8dba2f379037d42")] = "USDb"

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

    @external(readonly = True)
    def getLendingPoolCoreAddress(self) -> Address:
        return self._lendingPoolCoreAddress.get()
    
    @external(readonly = True)
    def getOracleAddress(self) -> Address:
        return self._oracleAddress.get()
    

    @external(readonly=True)
    def getUserAccountData(self, _user: Address) -> dict:
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        oracle = self.create_interface_score(ORACLE_ADDRESS, OracleInterface)
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
            reserveConfiguration['tokenUnit'] = 10 ** reserveConfiguration['decimals']
            reserveConfiguration['reserveUnitPrice'] = oracle.get_reference_data(self._symbol[_reserve], 'USD')

            if userBasicReserveData['underlyingBalance'] > 0:
                liquidityBalanceUSD = reserveConfiguration['reserveUnitPrice'] * userBasicReserveData['underlyingBalance'] // reserveConfiguration['tokenUnit']
                totalLiquidityBalanceUSD += liquidityBalanceUSD

                if reserveConfiguration['usageAsCollateralEnabled'] and userBasicReserveData['useAsCollateral']:
                    totalCollateralBalanceUSD += liquidityBalanceUSD
                    currentLtv += liquidityBalanceUSD * reserveConfiguration['baseLTVasCollateral']
                    currentLiquidationThreshold += liquidityBalanceUSD * reserveConfiguration['liquidationThreshold'] 

            if userBasicReserveData['compoundedBorrowBalance'] > 0:
                totalBorrowBalanceUSD += reserveConfiguration['reserveUnitPrice'] * userBasicReserveData['compoundedBorrowBalance'] //  reserveConfiguration['tokenUnit']
                totalFeesUSD += reserveConfiguration['reserveUnitPrice'] * userBasicReserveData['originationFee'] // reserveConfiguration['tokenUnit']


        if totalCollateralBalanceUSD > 0:
            currentLtv = ((currentLtv * 10**18) // totalCollateralBalanceUSD) // 10 ** 18
        else:
            currentLtv = 0

        healthFactor = self.calculateHealthFactorFromBalancesInternal(totalCollateralBalanceUSD,totalBorrowBalanceUSD,totalFeesUSD,currentLiquidationThreshold)
        if healthFactor < HEALTH_FACTOR_LIQUIDATION_THRESHOLD:
            healthFactorBelowThreshold = True

        response ={
            'totalLiquidityBalanceUSD': totalLiquidityBalanceUSD,
            'totalCollateralBalanceUSD': totalCollateralBalanceUSD,
            'totalBorrowBalanceUSD' : totalBorrowBalanceUSD,
            'totalFeesUSD' : totalFeesUSD,
            'currentLtv' : currentLtv,
            'currentLiquidationThreshold' : currentLiquidationThreshold,
            'healthFactor' : healthFactor,
            'healthFactorBelowThreshold' : healthFactorBelowThreshold
        }

        return response


    def calculateHealthFactorFromBalancesInternal(self, _collateralBalanceUSD: int, _borrowBalanceUSD: int, _totalFeesUSD: int, _liquidationThreshold: int) -> int:
        if _borrowBalanceUSD == 0:
            return -1
        healthFactor = (_collateralBalanceUSD * _liquidationThreshold // 100)  // (_borrowBalanceUSD + _totalFeesUSD)
        return healthFactor


    def calculateBorrowingPowerFromBalancesInternal(self, _collateralBalanceUSD: int, _borrowBalanceUSD: int, _totalFeesUSD: int, _ltv: int) -> int:
        borrowingPower = (_borrowBalanceUSD + _totalFeesUSD) // (_collateralBalanceUSD * _ltv // 100) 
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

    
    









