from iconservice import *

TAG = 'LendingPool'


class LendingPool(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()
    
    @payable
    @external
    def deposit(_reserve:Address,_amount:int)   
    
    @external
    def redeemUnderlying(_reserve:Address,_user:Address,_amount:int,_balanceAfterRedeem:int)

    @external
    def borrow(_reserve:Address,_amount:int)

    @payable
    @external
    def repay(_reserve:Address,_amount:int)

    @payable
    @external
    def liquidationCall(_collateral:Address,_reserve:Address,_user:Address,_purchaseAmount:int)
    



