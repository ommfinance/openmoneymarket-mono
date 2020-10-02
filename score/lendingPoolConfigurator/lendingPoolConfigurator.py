from iconservice import *

TAG = 'LendingPoolConfigurator'


class LendingPoolConfigurator(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external
    def initReserve(_reserve:Address,_underlyingAssetDecimals:int):

    @external
    def initReserveWithData(_reserve:Address,_underlyingAssetDecimals:int,_oTokenName:str,_oTokenSymbol:str):
        """
        initializes a reserve using aTokenData provided externally (useful if the underlying ERC20 contract doesn't expose name or decimals)
    
        """   
    @external    
    def removeLastAddedReserve(_reserveToRemove:Address):

    @external
    def enableBorrowingOnReserve(_reserve:Address):

    @external
    def disableBorrowingOnReserve(_reserve:Address):

    @external
    def enableReserveAsCollateral(_reserve:Address,_baseLTVasCollateral:int,_liquidationThreshold:int,_liquidationBonus:int):
    
    @external
    def disableReserveAsCollateral(_reserve:Address):

    @external
    def activateReserve(__reserve:Address):
    
    @external
    def deactiveReserve(_reserve:Address):
    
    @external
    def freezeReserve(_reserve:Address):

    @external
    def unfreezeReserve(_reserve:Address):
    
    @external
    def setReserveBaseLTVasCollateral(_reserve:Address,_ltv:int):

    @external
    def setReserveLiquidationThreshold(_reserve:Address,_threshold:int):
    
    @external
    def setReserveLiquidationBonus(_reserve:Address,_bonus:int):
    
    @external
    def setReserveDecimals(_reserve:Address,_decimals:int):
    
    @external
    def refreshLendingPoolCoreConfiguration():