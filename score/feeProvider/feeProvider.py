from iconservice import *
from .Math import *

TAG = 'FeeProvider'


class FeeProvider(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._originationFeePercent = VarDB('originationFeePercent', db , value_type = int)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    # @external
    # def distribute(self, _tokens: str) -> None:
    #     pass

    @external
    def setLoanOriginationFeePercentage(self, _percentage: int) -> None:
        self._originationFeePercent.set(_percentage)
        

    @external(readonly = True)
    def calculateOriginationFee(self, _user: Address, _amount: int) -> int:
        return exaMul(_amount, self.getLoanOriginationFeePercentage())
        
    
    @external(readonly = True)
    def getLoanOriginationFeePercentage(self) -> int:
        return self._originationFeePercent.get()
        
    @external(readonly = True)
    def getDistribution(self) -> dict:
        pass

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        pass

    

