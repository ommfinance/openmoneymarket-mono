from iconservice import *

TAG = 'LendingPoolDataProvider'


# Fetches data from the core  and aggregate them
class LendingPoolDataProvider(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def calculateUserGlobalData(self, _user: Address) -> dict:
        """
        calculates the user data across the reserve
        :param _user:address of the user
        :return:dict with totalLiquidityBalance,totalCollateralBalance,totalBorrowBalance,totalFees,currentLtv,currentLiquidationThreshold,healthFactor,healthFactorBelowThreshold
        """

    @external(readonly=True)
    def balanceDecreaseAllowed(self, _reserve: Address, _user: Address, _amount: int) -> bool:
        """
        check if a specific balance decrease is allowed (i.e. doesn't bring the user borrow position health factor under 1)
        :param _reserve:address of the reserve
        :param _user:address of the user
        :param _amount:amount to borrow
        :return:true if the decrease in the balance is allowed
        """

    @external(readonly=True)
    def calculateCollateralNeeded(self, _reserve: Address, _amount: int, _fee: int, _userCurrentBorrowBalance: int,
                                  _userCurrentFees: int, _userCurrentLtv: int):
        """
        calculates the amount of collateral needed to borrow a new loan
        :param _reserve: address of the reserve
        :param _amount: amount user wants to borrow
        :param _fee: borrow fee required for the borrow
        :param _userCurrentBorrowBalance: current collateral balance of the user
        :param _userCurrentFees: current fees of the user
        :param _userCurrentLtv:the average ltv of the user given his current collateral
        :return:total amount of collateral in ETH to cover the current borrow balance + the new amount + fee
        """

    @external(readonly=True)
    def getReserveConfigurationData(self, _reserve: Address) -> dict:
        """
        fetches the configuration details of a reserve
        :param _reserve: address of the reserve
        :return: dict with ltv,liquidationThreshold,liquidationBonus,usageAsCollateralEnabled,borrowingEnabled,isActive
        """

    @external(readonly=True)
    def getReserveData(self, _reserve: Address):
        """
        fetches the data of a specific reserve
        :param _reserve: address of the reserve
        :return: dict with totalLiquidity,availableLiquidity,totalBorrows,liquidityRate,borrowRate,utilizationRate,liquidityIndex,aTokenAddress,lastUpdateTimestamp
        """

    @external(readonly=True)
    def getUserAccountData(self, _user: Address):
        """
        get the user data for all the reserves
        :param _user:address of the reserve
        :return:dict with totalLiquidityBalance,totalCollateralBalance,totalBorrowBalance,totalFees,currentLtv,currentLiquidationThreshold,healthFactor,availableBorrows
        """

    @external(readonly=True)
    def getUserReserveData(self, _reserve: Address, _user: Address):
        """
        fetches the user's data for specific reserve
        :param _reserve: address of the reserve
        :param _user: address of the user
        :return: dict with currentOTokenBalance,currentBorrowBalance,pricicipalBorrowBalance,borrowRate,liquidityRate,originationFee,lastUpdateTimestamp,usageAsCollateralEnabled
        """
    @external(readonly=True)
    def getReserves(self) -> list:
        """
        list of reserves
        :return:the list of reserves configured on the core
        """