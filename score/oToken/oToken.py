from iconservice import *

TAG = 'OToken'


class OToken(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()
    
    @external
    def redeem(self, _amount: int ) -> None:
        pass
    
    @external
    def mintOnDeposit(self, _account: Address, _amount: int) -> None:
        pass

    @external
    def burnOnLiquidation(self, _account: Address, _value: int) -> None:
        pass
    
    @external
    def transferOnLiquidation(self, _from: Address, _to: Address, _value: int) -> None:
        pass
    
    @external(readonly = True)
    def balanceOf(self, _account: Address) -> int:
        pass

    @external(readonly = True)
    def principalBalanceOf(self, _account: Address) -> int:
        pass

    @external(readonly = True)
    def totalSupply(self) -> int:
        pass

    @external(readonly = True)
    def isTransferAllowed(self, _account: Address, _amount: int) -> bool:
        pass

    @external(readonly = True)
    def getUserIndex(self, _account: Address) -> int:
        pass