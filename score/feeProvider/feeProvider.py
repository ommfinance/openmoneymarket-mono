from .utils.checks import *
from .utils.math import *
from .addresses import *

TAG = 'Fee Provider'


class FeeProvider(Addresses):
    ORIGINATION_FEE_PERCENT = 'originationFeePercent'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._originationFeePercent = VarDB(self.ORIGINATION_FEE_PERCENT, db, value_type=int)

    def on_install(self, _addressProvider: Address) -> None:
        super().on_install(_addressProvider)

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=3)
    def FeeReceived(self, _from: Address, _value: int, _data: bytes,_sender:Address):
        pass

    @only_owner
    @external
    def setLoanOriginationFeePercentage(self, _percentage: int) -> None:
        self._originationFeePercent.set(_percentage)

    @external(readonly=True)
    def name(self) -> str:
        return f"Omm {TAG}"

    @external(readonly=True)
    def calculateOriginationFee(self, _amount: int) -> int:
        return exaMul(_amount, self.getLoanOriginationFeePercentage())

    @external(readonly=True)
    def getLoanOriginationFeePercentage(self) -> int:
        return self._originationFeePercent.get()

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        self.FeeReceived(_from, _value, _data,self.msg.sender)

    @only_governance
    @external
    def transferFund(self, _token: Address, _value: int, _to: Address):
        token = self.create_interface_score(_token, TokenInterface)
        token.transfer(_to, _value)
