from iconservice import *

TAG = 'DaoFund'


# This contract manages the fund for Dao operations

class DaoFund(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=3)
    def FundReceived(self, _amount: int, _reserve: Address, _time: int):
        pass
    
    @external(readonly=True)
    def name(self) -> str :
        return "OmmDaoFundManager" 

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes = None) -> None:
        self.FundReceived(_value,self.msg.sender,self.now())