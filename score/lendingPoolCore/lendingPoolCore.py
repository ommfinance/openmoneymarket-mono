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
    def updateStateOnDeposit(_reserve:Address,_user:Address,_amount:int,_isFirstDeposit:bool):

    @external
    def updateStateOnRedeem(_reserve:Address,_user:Address,_amountRedeemed:int,_userRedeemedEverything:bool):

    @external
    def updateStateOnBorrow(_reserve:Address,_user:Address,_amountBorrowed:int,_borrowFee:int):

    @external
    def updateStateOnRepay(_reserve:Address,_user:Address,_paybackAmountMinusFees,_originationFeeRepaid:int,_balanceIncrease:int,_repaidWholeLoan:bool):

    @external
    def updateStateOnLiquidation(_principalReserve:Address,_collateralReserve:Address,_user:Address,_amountToLiquidate:int,_collateralToLiquidate:int,_feeLiquidated:int,_liquidatedCollateralForFee:int,_balanceIncrease:int):

    @external
    def transferToUser(_reserve:Address,_user:Address,_amount:int):

    @external
    def transferToFeeCollectionAddress(_token:Address,_user:Address,_amount:int,_destination:Address):

    @external
    def liquidateFee(_token:Address,_amount:int,_destination:Address):

    @external
    def transferToReserve(_reserve:Address,_user:Address,_amount:int):

    @external
    def setReserveBaseLTVasCollateral(_reserve:Address,_ltv:int):

    @external
    def setReserveLiquidationThreshold(_reserve:Address,_threshold:int):
    
    @external
    def setReserveLiquidationBonus(_reserve:Address,_bonus:int):
    
    @external
    def setReserveDecimals(_reserve:Address,_decimals:int):
    
    @external
    def refreshConfiguration():
    
    @external
    def initReserve(_reserve:Address,_oTokenAddress:Address,_decimals:int)

    @external 
    def removeLastAddedReserve(_reserveToRemove:Address):
    
    @external
    def activateReserve(_reserve:Address):
    
    @external
    def deactivateReserve(_reserve:Address):

    @external
    def freezeReserve(_reserve:Address):

    @external
    def unfreezeReserve(_reserve:Address):
    
    @external(readonly=True)
    def getUserBasicReserveData(_reserve:Address,_user:Address)->dict:

    @external(readonly=True)
    def getUserUnderlyingAssetBalance(_reserve:Address,_user:Address)->int:
    
    @external(readonly=True)
    def getReserveOTokenAddress(_reserve:Address)->Address:

    @external(readonly=True)
    def getReserveAvailableLiquidity(_reserve:Address)->int:

    @external(readonly=True)
    def getReserveTotalLiquidity(_reserve:Address)->int:

    @external(readonly=True)
    def getReserveConfiguration(_reserve:Address)->dict:
    
    @external(readonly=True)
    def getReserves()->list:
    


