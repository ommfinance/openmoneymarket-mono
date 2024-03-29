from .utils.checks import *
from .addresses import *

TAG = 'Dao Fund Manager'


# This contract manages the fund for Dao operations

class DaoFund(Addresses):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self, _addressProvider: Address) -> None:
        super().on_install(_addressProvider)

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=1)
    def FundReceived(self, _amount: int, _reserve: Address):
        pass

    @external(readonly=True)
    def name(self) -> str:
        return f"Omm {TAG}"

    @only_governance
    @external
    def transferOmm(self, _value: int, _address: Address):
        omm = self.create_interface_score(self._addresses[OMM_TOKEN], TokenInterface)
        omm.transfer(_address, _value)

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes = None) -> None:
        self.FundReceived(_value, self.msg.sender)
