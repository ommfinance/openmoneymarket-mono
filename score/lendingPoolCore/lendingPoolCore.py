from iconservice import *

TAG = 'LendingPoolCore'


class LendingPoolCore(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external
    def updateStateOnDeposit(self, _reserve: Address, _user: Address, _amount: int, _isFirstDeposit: bool):
        """
        updates the states to handle a deposit action by the _user
        :param _reserve:address of the reserve
        :param _user:address of the user
        :param _amount:amount to be deposited
        :param _isFirstDeposit:true if the user don't have any previous deposit
        :return:
        """

    @external
    def updateStateOnRedeem(self, _reserve: Address, _user: Address, _amountRedeemed: int,
                            _userRedeemedEverything: bool):
        """
        updates the states to handle a redeem action by the _user
        :param _reserve: address of the reserve
        :param _user: address of the user
        :param _amountRedeemed: amount to be redeemed
        :param _userRedeemedEverything: true if the user is redeeming everything
        :return:
        """

    @external
    def updateStateOnBorrow(self, _reserve: Address, _user: Address, _amountBorrowed: int, _borrowFee: int):
        """
        updates the states to handle a borrow action by the _user
        :param _reserve:address of the reserve
        :param _user: address of the user
        :param _amountBorrowed: amount to be borrowed
        :param _borrowFee: fee to be paid for borrow amount
        :return:
        """

    @external
    def updateStateOnRepay(self, _reserve: Address, _user: Address, _paybackAmountMinusFees, _originationFeeRepaid: int,
                           _balanceIncrease: int, _repaidWholeLoan: bool):
        """
        updates the states to handle a loan repay action by the _user
        :param _reserve: address of the reserve
        :param _user: address of the user
        :param _paybackAmountMinusFees: amount to be paid back after the deduction of the borrow fee
        :param _originationFeeRepaid: amount of fee to be paid
        :param _balanceIncrease:accrued interest on borrow amount
        :param _repaidWholeLoan:true in case the user is clearing all the loan
        :return:
        """

    @external
    def updateStateOnLiquidation(self, _principalReserve: Address, _collateralReserve: Address, _user: Address,
                                 _amountToLiquidate: int, _collateralToLiquidate: int, _feeLiquidated: int,
                                 _liquidatedCollateralForFee: int, _balanceIncrease: int):
        """
        updates the state of collateral and principal reserve to handle the liquidation call by a liquidator
        :param _principalReserve:address of the principal reserve that is being paid
        :param _collateralReserve:address of the collateral that is being liquidated
        :param _user:address of the user
        :param _amountToLiquidate:amount paid by the liquidator
        :param _collateralToLiquidate:amount of collateral being liquidated
        :param _feeLiquidated:amount of origination fee liquidated
        :param _liquidatedCollateralForFee:the amount of collateral equivalent to the origination fee + bonus
        :param _balanceIncrease:accrues interest on the borrowed amount
        :return:
        """

    @external
    def transferToUser(self, _reserve: Address, _user: Address, _amount: int):
        """
        transfers asset from reserve to the user
        :param _reserve:address of the reserve
        :param _user:address of the user
        :param _amount:amount to be transferred
        :return:
        """

    @external
    def transferToFeeCollectionAddress(self, _token: Address, _user: Address, _amount: int, _destination: Address):
        """
        transfer the fee to fee collection address
        :param _token:address of token being transferred
        :param _user:address of the user from where the transfer is performed
        :param _amount:amount to be transferred
        :param _destination:fee collection address
        :return:
        """

    @external
    def liquidateFee(self, _token: Address, _amount: int, _destination: Address):
        """
        transfers the fees to the fees collection address in the case of liquidation
        :param _token:address of token being transferred
        :param _amount:amount to be transferred
        :param _destination:fee collection address
        :return:
        """

    @external
    def transferToReserve(self, _reserve: Address, _user: Address, _amount: int):
        """
        transfers an asset to the reserve
        :param _reserve:address of the reserve
        :param _user:address of the user
        :param _amount:amount to be transferred
        :return:
        """

    @external
    def setReserveBaseLTVasCollateral(self, _reserve: Address, _ltv: int):
        """
        sets/updates  the loan to value of a reserve
        :param _reserve:address of the reserve
        :param _ltv:the value of ltv to set
        :return:
        """

    @external
    def setReserveLiquidationThreshold(self, _reserve: Address, _threshold: int):
        """
        updates the liquidation threshold of the reserve
        :param _reserve:address of the reserve
        :param _threshold:the value liquidation threshold to set
        :return:
        """

    @external
    def setReserveLiquidationBonus(self, _reserve: Address, _bonus: int):
        """
        updates the liquidation bonus of the reserve
        :param _reserve: address of the reserve
        :param _bonus: the value for liquidation bonus
        :return:
        """

    @external
    def setReserveDecimals(self, _reserve: Address, _decimals: int):
        """
        updates the reserve decimals
        :param _reserve:address of the reserve
        :param _decimals:the new number of  decimals
        :return:
        """

    @external
    def refreshConfiguration(self):
        """
        updates the lending pool core configuration
        :return:
        """

    @external
    def initReserve(self, _reserve: Address, _oTokenAddress: Address, _decimals: int):
        """
        initilizes a reserve
        :param _reserve: address of the reserve
        :param _oTokenAddress: address of the oToken contract
        :param _decimals: decimals of the reserve 
        :return: 
        """

    @external
    def removeLastAddedReserve(self, _reserveToRemove: Address):
        """
        removes the last added reserve
        :param _reserveToRemove: the address of the reserve to remove
        :return:
        """

    @external
    def activateReserve(self, _reserve: Address):
        """
        activates a reserve
        :param _reserve:address of the reserve
        :return:
        """

    @external
    def deactivateReserve(self, _reserve: Address):
        """
        deactivates a reserve
        :param _reserve:address of the reserve
        :return:
        """

    @external
    def freezeReserve(self, _reserve: Address):
        """
        freezes a reserve
        :param _reserve: address of the reserve
        :return:
        """

    @external
    def unfreezeReserve(self, _reserve: Address):
        """
        unfreezes a reserve
        :param _reserve: address of the reserve
        :return:
        """

    @external(readonly=True)
    def getUserBasicReserveData(self, _reserve: Address, _user: Address) -> dict:
        """
        returns the basic data (balances, fee accrued, reserve enabled/disabled as collateral),
        needed to calculate the global account data in the LendingPoolDataProvider
        :param _reserve:address of the reserve
        :param _user:address of the user
        :return:the user deposited balance, the principal borrow balance, the fee, and if the reserve is enabled as collateral or not in the form of a dict
        """

    @external(readonly=True)
    def getUserUnderlyingAssetBalance(self, _reserve: Address, _user: Address) -> int:
        """
        gets the underlying asset balance of a user based on the corresponding oToken balance.
        :param _reserve:address of the reserve
        :param _user:address of the user
        :return:the underlying deposit balance of the user
        """

    @external(readonly=True)
    def getReserveOTokenAddress(self, _reserve: Address) -> Address:
        """
        gets the oToken contract address for the reserve
        :param _reserve: address of the reserve
        :return:address of the oToken contract
        """

    @external(readonly=True)
    def getReserveAvailableLiquidity(self, _reserve: Address) -> int:
        """
        gets the available liquidity in the reserve. The available liquidity is the balance of the core contract
        :param _reserve: address of the reserve
        :return: the available liquidity
        """

    @external(readonly=True)
    def getReserveTotalLiquidity(self, _reserve: Address) -> int:
        """
        gets the total liquidity in the reserve. The total liquidity is the balance of the core contract + total borrows
        :param _reserve:address of the reserve
        :return:the total liquidity
        """

    @external(readonly=True)
    def getReserveConfiguration(self, _reserve: Address) -> dict:
        """
        this function aggregates the configuration parameters of the reserve.
        It's used in the LendingPoolDataProvider specifically to save gas, and avoid multiple external contract calls to fetch the same data.
        :param _reserve:address of the reserve
        :return:a dict with reserve decimals,the base ltv as collateral,the liquidation threshold,if the reserve is used as collateral or not
        """

    @external(readonly=True)
    def getReserves(self) -> list:
        """
        list of reserves
        :return:the list of reserves configured on the core
        """
