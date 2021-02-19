from iconservice import *
from .Math import *
from .utils.checks import *

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

    @interface
    def principalBalanceOf(self, _user: Address) -> int:
        pass

    def getUserLiquidityCumulativeIndex(self, _user: Address) -> int:
        pass


# An interface to LendingPool
class LendingPoolInterface(InterfaceScore):
    @interface
    def getBorrowWallets(self) -> list:
        pass


# An interface to liquidation manager
class LiquidationInterface(InterfaceScore):
    @interface
    def calculateBadDebt(self, _totalBorrowBalanceUSD: int, _totalFeesUSD: int, _totalCollateralBalanceUSD: int,
                         _ltv: int) -> int:
        pass


# An interface to liquidation manager
class LiquidationInterface(InterfaceScore):
    @interface
    def calculateBadDebt(self, _totalBorrowBalanceUSD: int, _totalFeesUSD: int, _totalCollateralBalanceUSD: int,
                         _ltv: int) -> int:
        pass


class StakingInterface(InterfaceScore):
    @interface
    def getTodayRate(self) -> int:
        pass

    @interface
    def getUserUnstakeInfo(self, _address: Address) -> list:
        pass


class LendingPoolDataProvider(IconScoreBase):
    _SYMBOL='symbol'
    _LENDING_POOL_CORE='lendingPoolCore'
    _LENDING_POOL='lendingPool'
    _PRICE_ORACLE='priceOracle'
    _LIQUIDATION_MANAGER='liquidationManager'
    _STAKING='staking'


    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._symbol = DictDB(self._SYMBOL, db, value_type=str)
        self._lendingPoolCore = VarDB(self._LENDING_POOL_CORE, db, value_type=Address)
        self._lendingPool = VarDB(self._LENDING_POOL, db, value_type=Address)
        self._priceOracle = VarDB(self._PRICE_ORACLE, db, value_type=Address)
        self._liquidationManager = VarDB(self._LIQUIDATION_MANAGER, db, value_type=Address)
        self._staking = VarDB(self._STAKING, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self):
        return "OmmLendingPoolDataProvider"

    @only_owner
    @external
    def setSymbol(self, _reserveAddress: Address, _sym: str):
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')
        self._symbol[_reserveAddress] = _sym

    @external
    def getSymbol(self, _reserveAddress: Address) -> str:
        return self._symbol[_reserveAddress]

    @only_owner
    @external
    def setLendingPoolCoreAddress(self, _address: Address) -> None:
        self._lendingPoolCore.set(_address)

    @external
    def setLendingPoolAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._lendingPool.set(_address)

    @only_owner
    @external
    def setOracleAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._priceOracle.set(_address)

    @only_owner
    @external
    def setStakingAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')

        self._staking.set(_address)

    @external(readonly=True)
    def getLendingPoolCoreAddress(self) -> Address:
        return self._lendingPoolCore.get()

    @external(readonly=True)
    def getLendingPoolAddress(self) -> Address:
        return self._lendingPool.get()

    @external(readonly=True)
    def getOracleAddress(self) -> Address:
        return self._priceOracle.get()

    @only_owner
    @external
    def setLiquidationAddress(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Method can only be invoked by the owner')
        self._liquidationManager.set(_address)

    @external(readonly=True)
    def getLiquidationAddress(self) -> Address:
        return self._liquidationManager.get()

    @external(readonly=True)
    def getStakingAddress(self) -> Address:
        return self._staking.get()

    @external(readonly=True)
    def getReserveAccountData(self) -> dict:
        core = self.create_interface_score(self._lendingPoolCore.get(), CoreInterface)
        oracle = self.create_interface_score(self._priceOracle.get(), OracleInterface)
        staking = self.create_interface_score(self._staking.get(), StakingInterface)
        todayRate = staking.getTodayRate()
        totalLiquidityBalanceUSD = 0
        totalCollateralBalanceUSD = 0
        totalBorrowBalanceUSD = 0
        availableLiquidityBalanceUSD = 0
        reserves = core.getReserves()

        for _reserve in reserves:
            reserveData = core.getReserveData(_reserve)
            reserveDecimals = reserveData['decimals']
            reservePrice = oracle.get_reference_data(self._symbol[_reserve], 'USD')
            if self._symbol[_reserve] == 'ICX':
                reservePrice = exaMul(reservePrice, todayRate)
            reserveTotalLiquidity = reserveData['totalLiquidity']
            reserveAvailableLiquidity = reserveData['availableLiquidity']
            reserveTotalBorrows = reserveData['totalBorrows']

            if reserveDecimals !=18:
                reserveTotalLiquidity = convertToExa(reserveTotalLiquidity,reserveDecimals)
                reserveAvailableLiquidity = convertToExa(reserveAvailableLiquidity,reserveDecimals)
                reserveTotalBorrows = convertToExa(reserveAvailableLiquidity,reserveDecimals)
                
            totalLiquidityBalanceUSD += exaMul(reserveTotalLiquidity, reservePrice)
            availableLiquidityBalanceUSD += exaMul(reserveAvailableLiquidity, reservePrice)
            totalBorrowBalanceUSD += exaMul(reserveTotalBorrows, reservePrice)
            if reserveData['usageAsCollateralEnabled']:
                totalCollateralBalanceUSD += exaMul(reserveTotalLiquidity, reservePrice)
        response = {
            'totalLiquidityBalanceUSD': totalLiquidityBalanceUSD,
            'availableLiquidityBalanceUSD': availableLiquidityBalanceUSD,
            'totalBorrowsBalanceUSD': totalBorrowBalanceUSD,
            'totalCollateralBalanceUSD': totalCollateralBalanceUSD,

        }

        return response

    @external(readonly=True)
    def getUserAccountData(self, _user: Address) -> dict:
        core = self.create_interface_score(self._lendingPoolCore.get(), CoreInterface)
        oracle = self.create_interface_score(self._priceOracle.get(), OracleInterface)
        staking = self.create_interface_score(self._staking.get(), StakingInterface)
        todaySicxRate = staking.getTodayRate()
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
            reserveDecimals = reserveConfiguration['decimals']

            # converting the user balances into 18 decimals
            if  reserveDecimals != 18:
                userBasicReserveData['underlyingBalance']=convertToExa(userBasicReserveData['underlyingBalance'],reserveDecimals)
                userBasicReserveData['compoundedBorrowBalance']=convertToExa(userBasicReserveData['compoundedBorrowBalance'],reserveDecimals)
                userBasicReserveData['originationFee']=convertToExa(userBasicReserveData['originationFee'],reserveDecimals)

            reserveConfiguration['reserveUnitPrice'] = oracle.get_reference_data(self._symbol[_reserve], 'USD')
            if self._symbol[_reserve] == 'ICX':
                reserveConfiguration['reserveUnitPrice'] = exaMul(reserveConfiguration['reserveUnitPrice'],
                                                                  todaySicxRate)

            if userBasicReserveData['underlyingBalance'] > 0:
                liquidityBalanceUSD = exaMul(reserveConfiguration['reserveUnitPrice'],
                                             userBasicReserveData['underlyingBalance'])
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
            currentLtv = exaDiv(currentLtv, totalCollateralBalanceUSD)
            currentLiquidationThreshold = exaDiv(currentLiquidationThreshold, totalCollateralBalanceUSD)
        else:
            currentLtv = 0
            currentLiquidationThreshold = 0

        healthFactor = self.calculateHealthFactorFromBalancesInternal(totalCollateralBalanceUSD, totalBorrowBalanceUSD,
                                                                      totalFeesUSD, currentLiquidationThreshold)
        if healthFactor < HEALTH_FACTOR_LIQUIDATION_THRESHOLD and healthFactor != - 1:
            healthFactorBelowThreshold = True

        borrowingPower = self.calculateBorrowingPowerFromBalancesInternal(totalCollateralBalanceUSD,
                                                                          totalBorrowBalanceUSD,
                                                                          totalFeesUSD, currentLiquidationThreshold)
        borrowsAllowedUSD = exaMul(totalCollateralBalanceUSD - totalFeesUSD, currentLtv)
        availableBorrowsUSD = borrowsAllowedUSD - totalBorrowBalanceUSD
        if availableBorrowsUSD < 0:
            availableBorrowsUSD = 0
        response = {
            'totalLiquidityBalanceUSD': totalLiquidityBalanceUSD,
            'totalCollateralBalanceUSD': totalCollateralBalanceUSD,
            'totalBorrowBalanceUSD': totalBorrowBalanceUSD,
            'totalFeesUSD': totalFeesUSD,
            'availableBorrowsUSD': availableBorrowsUSD,
            'currentLtv': currentLtv,
            'currentLiquidationThreshold': currentLiquidationThreshold,
            'healthFactor': healthFactor,
            'borrowingPower': borrowingPower,
            'healthFactorBelowThreshold': healthFactorBelowThreshold
        }

        return response

    @external(readonly=True)
    def getUserReserveData(self, _reserve: Address, _user: Address) -> dict:
        response = {}
        core = self.create_interface_score(self._lendingPoolCore.get(), CoreInterface)
        reserveData = core.getReserveData(_reserve)
        userReserveData = core.getUserReserveData(_reserve, _user)
        oToken = self.create_interface_score(reserveData['oTokenAddress'], oTokenInterface)
        currentOTokenBalance = oToken.balanceOf(_user)
        principalOTokenBalance = oToken.principalBalanceOf(_user)
        userLiquidityCumulativeIndex = oToken.getUserLiquidityCumulativeIndex(_user)
        principalBorrowBalance = userReserveData['principalBorrowBalance']
        currentBorrowBalance = core.getCompoundedBorrowBalance(_reserve, _user)
        borrowRate = reserveData['borrowRate']
        reserveDecimals = reserveData['decimals']
        liquidityRate = reserveData['liquidityRate']
        originationFee = userReserveData['originationFee']
        userBorrowCumulativeIndex = userReserveData['userBorrowCumulativeIndex']
        lastUpdateTimestamp = userReserveData['lastUpdateTimestamp']
        useAsCollateral = userReserveData['useAsCollateral']
        price_provider = self.create_interface_score(self._priceOracle.get(), OracleInterface)
        price = price_provider.get_reference_data(self._symbol[_reserve], "USD")
        if self._symbol[_reserve] == "ICX":
            staking = self.create_interface_score(self._staking.get(), StakingInterface)
            todaySicxRate = staking.getTodayRate()
            response['sICXRate'] = todaySicxRate
            price = exaMul(price, todaySicxRate)
            # currentOTokenBalance = exaMul(currentOTokenBalance, todaySicxRate)
            # principalOTokenBalance = exaMul(principalOTokenBalance, todaySicxRate)
            # currentBorrowBalance = exaMul(currentBorrowBalance, todaySicxRate)
            # principalBorrowBalance = exaMul(principalBorrowBalance, todaySicxRate)
        
        currentOTokenBalanceUSD = exaMul(convertToExa(currentOTokenBalance,reserveDecimals), price)
        principalOTokenBalanceUSD = exaMul(convertToExa(principalOTokenBalance,reserveDecimals), price)
        currentBorrowBalanceUSD = exaMul(convertToExa(currentBorrowBalance,reserveDecimals), price)
        principalBorrowBalanceUSD = exaMul(convertToExa(principalBorrowBalance,reserveDecimals), price)
        response = {
            'currentOTokenBalance': currentOTokenBalance,
            'currentOTokenBalanceUSD': currentOTokenBalanceUSD,
            'principalOTokenBalance': principalOTokenBalance,
            'principalOTokenBalanceUSD': principalOTokenBalanceUSD,
            'currentBorrowBalance': currentBorrowBalance,
            'currentBorrowBalanceUSD': currentBorrowBalanceUSD,
            'principalBorrowBalance': principalBorrowBalance,
            'principalBorrowBalanceUSD': principalBorrowBalanceUSD,
            'userLiquidityCumulativeIndex': userLiquidityCumulativeIndex,
            'borrowRate': borrowRate,
            'liquidityRate': liquidityRate,
            'originationFee': originationFee,
            'userBorrowCumulativeIndex': userBorrowCumulativeIndex,
            'lastUpdateTimestamp': lastUpdateTimestamp,
            'useAsCollateral': useAsCollateral,
            'exchangeRate': price,
            'decimals': reserveDecimals
        }

        return response

    @external(readonly=True)
    def balanceDecreaseAllowed(self, _reserve: Address, _user: Address, _amount: int) -> bool:
        core = self.create_interface_score(self._lendingPoolCore.get(), CoreInterface)
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

        if reserveConfiguration['decimals'] !=18:
            _amount = convertToExa(_amount,reserveConfiguration['decimals'])

        if borrowBalanceUSD == 0:
            return True

        oracle = self.create_interface_score(self._priceOracle.get(), OracleInterface)
        price = oracle.get_reference_data(self._symbol[_reserve], 'USD')
        if self._symbol[_reserve] == "ICX":
            staking = self.create_interface_score(self._staking.get(), StakingInterface)
            todaySicxRate = staking.getTodayRate()
            price = exaMul(price, todaySicxRate)
        amountToDecreaseUSD = exaMul(price, _amount)
        collateralBalanceAfterDecreaseUSD = collateralBalanceUSD - amountToDecreaseUSD

        if collateralBalanceAfterDecreaseUSD == 0:
            return False

        liquidationThresholdAfterDecrease = exaDiv((exaMul(collateralBalanceUSD, currentLiquidationThreshold) - exaMul(
            amountToDecreaseUSD, reserveLiquidationThreshold)), collateralBalanceAfterDecreaseUSD)

        healthFactorAfterDecrease = self.calculateHealthFactorFromBalancesInternal(collateralBalanceAfterDecreaseUSD,
                                                                                   borrowBalanceUSD, totalFeesUSD,
                                                                                   liquidationThresholdAfterDecrease)

        return healthFactorAfterDecrease > HEALTH_FACTOR_LIQUIDATION_THRESHOLD

    @external(readonly=True)
    def calculateCollateralNeededUSD(self, _reserve: Address, _amount: int, _fee: int,
                                     _userCurrentBorrowBalanceUSD: int,
                                     _userCurrentFeesUSD: int, _userCurrentLtv: int) -> int:

        price_provider = self.create_interface_score(self._priceOracle.get(), OracleInterface)
        price = price_provider.get_reference_data(self._symbol[_reserve], "USD")
        core = self.create_interface_score(self._lendingPoolCore.get(), CoreInterface)
        reserveConfiguration = core.getReserveConfiguration(_reserve)
        if reserveConfiguration['decimals'] != 18:
            _amount = _amount * EXA // (10 ** reserveConfiguration["decimals"])
        if self._symbol[_reserve] == "ICX":
            staking = self.create_interface_score(self._staking.get(), StakingInterface)
            todaySicxRate = staking.getTodayRate()
            price = exaMul(price, todaySicxRate)
        requestedBorrowUSD = exaMul(price, _amount)
        collateralNeededInUSD = exaDiv(_userCurrentBorrowBalanceUSD + requestedBorrowUSD,
                                       _userCurrentLtv) + _userCurrentFeesUSD
        return collateralNeededInUSD

    @external(readonly=True)
    def getUserAllReserveData(self, _user: Address) -> dict:
        core = self.create_interface_score(self._lendingPoolCore.get(), CoreInterface)
        reserves = core.getReserves()
        userData = {}
        for reserve in reserves:
            userData[self._symbol[reserve]] = self.getUserReserveData(reserve, _user)

        return userData

    @external(readonly=True)
    def getUserLiquidationData(self, _user: Address) -> dict:
        liquidationManager = self.create_interface_score(self.getLiquidationAddress(), LiquidationInterface)
        core = self.create_interface_score(self._lendingPoolCore.get(), CoreInterface)
        price_provider = self.create_interface_score(self._priceOracle.get(), OracleInterface)
        reserves = core.getReserves()
        userAccountData = self.getUserAccountData(_user)
        badDebt = liquidationManager.calculateBadDebt(userAccountData['totalBorrowBalanceUSD'],
                                                      userAccountData['totalFeesUSD'],
                                                      userAccountData['totalCollateralBalanceUSD'],
                                                      userAccountData['currentLtv'])
        response = {'badDebt': badDebt, 'borrows': {}, 'collaterals': {}}
        for _reserve in reserves:
            userReserveData = core.getUserBasicReserveData(_reserve, _user)
            reserveConfiguration = core.getReserveConfiguration(_reserve)
            reserveDecimals = reserveConfiguration['decimals']
            if reserveDecimals != 18:
                userReserveData['compoundedBorrowBalance'] = convertToExa(userReserveData['compoundedBorrowBalance'],reserveDecimals)
                userReserveData['underlyingBalance'] =convertToExa(userReserveData['underlyingBalance'],reserveDecimals)
                
            userBorrowBalance = userReserveData['compoundedBorrowBalance']
            price = price_provider.get_reference_data(self._symbol[_reserve], "USD")
            if self._symbol[_reserve] == "ICX":
                staking = self.create_interface_score(self._staking.get(), StakingInterface)
                todaySicxRate = staking.getTodayRate()
                price = exaMul(price, todaySicxRate)
            userReserveUnderlyingBalance = userReserveData['underlyingBalance']
            if userBorrowBalance > 0:
                if badDebt > exaMul(price, userBorrowBalance):
                    maxAmountToLiquidateUSD = exaMul(price, userBorrowBalance)
                    maxAmountToLiquidate = userBorrowBalance
                else:
                    maxAmountToLiquidateUSD = badDebt
                    maxAmountToLiquidate = exaDiv(badDebt, price)

                response['borrows'][self._symbol[_reserve]] = {'compoundedBorrowBalance': userBorrowBalance,
                                                               'compoundedBorrowBalanceUSD': exaMul(price,
                                                                                                    userBorrowBalance),
                                                               'maxAmountToLiquidate': maxAmountToLiquidate,
                                                               'maxAmountToLiquidateUSD': maxAmountToLiquidateUSD}
            if userReserveUnderlyingBalance > 0:
                response['collaterals'][self._symbol[_reserve]] = {'underlyingBalance': userReserveUnderlyingBalance,
                                                                   'underlyingBalanceUSD': exaMul(price,
                                                                                                  userReserveUnderlyingBalance)}

        return response

    @external(readonly=True)
    def liquidationList(self) -> dict:
        pool = self.create_interface_score(self._lendingPool.get(), LendingPoolInterface)
        wallets = pool.getBorrowWallets()
        response = {}
        for wallet in wallets:
            userAccountData = self.getUserAccountData(wallet)
            if userAccountData['healthFactor'] < 10 ** 18:
                response[wallet] = self.getUserLiquidationData(wallet)

        return response

    def calculateHealthFactorFromBalancesInternal(self, _collateralBalanceUSD: int, _borrowBalanceUSD: int,
                                                  _totalFeesUSD: int, _liquidationThreshold: int) -> int:
        if _borrowBalanceUSD == 0:
            return -1
        healthFactor = exaDiv(exaMul(_collateralBalanceUSD - _totalFeesUSD, _liquidationThreshold), _borrowBalanceUSD)
        return healthFactor

    def calculateBorrowingPowerFromBalancesInternal(self, _collateralBalanceUSD: int, _borrowBalanceUSD: int,
                                                    _totalFeesUSD: int, _ltv: int) -> int:
        if _collateralBalanceUSD == 0:
            return 0
        borrowingPower = exaDiv(_borrowBalanceUSD, exaMul(_collateralBalanceUSD - _totalFeesUSD, _ltv))
        return borrowingPower

    @external(readonly=True)
    def getReserveData(self, _reserve: Address) -> dict:
        core = self.create_interface_score(self._lendingPoolCore.get(), CoreInterface)
        oracle = self.create_interface_score(self._priceOracle.get(), OracleInterface)
        reserveData = core.getReserveData(_reserve)
        price = oracle.get_reference_data(self._symbol[_reserve], "USD")
        reserveData["exchangePrice"] = price
        if self._symbol[_reserve] == "ICX":
            staking = self.create_interface_score(self._staking.get(), StakingInterface)
            reserveData['sICXRate'] = staking.getTodayRate()
            price = exaMul(staking.getTodayRate(),price)
            # reserveData['totalLiquidity'] = exaMul(reserveData['totalLiquidity'], todaySicxRate)
            # reserveData['availableLiquidity'] = exaMul(reserveData['availableLiquidity'], todaySicxRate)
            # reserveData['totalBorrows'] = exaMul(reserveData['totalBorrows'], todaySicxRate)
        reserveDecimals = reserveData['decimals'] 
        if reserveDecimals != 18 :
            reserveData['totalLiquidity'] = convertToExa(reserveData['totalLiquidity'],reserveDecimals)
            reserveData['availableLiquidity'] = convertToExa(reserveData['availableLiquidity'],reserveDecimals)
            reserveData['totalBorrows'] = convertToExa(reserveData['totalBorrows'],reserveDecimals)

        reserveData["totalLiquidityUSD"]=exaMul(reserveData['totalLiquidity'],price)
        reserveData["availableLiquidityUSD"]=exaMul(reserveData['availableLiquidity'],price)
        reserveData["totalBorrowsUSD"]=exaMul(reserveData['totalBorrows'],price)


        return reserveData

    @external(readonly=True)
    def getAllReserveData(self) -> dict:
        core = self.create_interface_score(self._lendingPoolCore.get(), CoreInterface)
        reserves = core.getReserves()
        response = {}
        for reserve in reserves:
            response[self._symbol[reserve]] = self.getReserveData(reserve)

        return response

    @external(readonly=True)
    def getReserveConfigurationData(self, _reserve: Address) -> dict:
        core = self.create_interface_score(self._lendingPoolCore.get(), CoreInterface)
        return core.getReserveConfiguration(_reserve)

    @external(readonly=True)
    def getAllReserveConfigurationData(self) -> dict:
        core = self.create_interface_score(self._lendingPoolCore.get(), CoreInterface)
        reserves = core.getReserves()
        response = {}
        for reserve in reserves:
            response[self._symbol[reserve]] = core.getReserveConfiguration(reserve)

        return response

    @external(readonly=True)
    def getUserUnstakeInfo(self, _address: Address) -> list:
        staking = self.create_interface_score(self._staking.get(), StakingInterface)
        unstakeDetails = staking.getUserUnstakeInfo(_address)
        response = []
        for unstakedRecords in unstakeDetails:
            if unstakedRecords['contract'] == self._lendingPoolCore.get():
                unstake = {'amount': unstakedRecords["amount"], 'unstakingBlockHeight': unstakedRecords["blockHeight"]}
                response.append(unstake)
        return response
