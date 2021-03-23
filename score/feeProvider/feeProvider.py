from iconservice import *
from .Math import *
from .utils.checks import * 

TAG = 'FeeProvider'

class FeeProvider(IconScoreBase):

    ORIGINATION_FEE_PERCENT = 'originationFeePercent'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._originationFeePercent = VarDB(self.ORIGINATION_FEE_PERCENT, db , value_type = int)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @only_owner
    @external
    def setLoanOriginationFeePercentage(self, _percentage: int) -> None:
        self._originationFeePercent.set(_percentage)
        
    @external(readonly=True)
    def name(self) -> str :
        return "OmmLendingPoolFeeProvider"  

    @external(readonly = True)
    def calculateOriginationFee(self, _amount: int) -> int:
        return exaMul(_amount, self.getLoanOriginationFeePercentage())
        
    @external(readonly = True)
    def getLoanOriginationFeePercentage(self) -> int:
        return self._originationFeePercent.get()

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        pass

    

