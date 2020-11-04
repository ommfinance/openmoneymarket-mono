from iconservice import *
from .Math import *

TAG = 'FeeProvider'


class FeeProvider(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external
    def distribute(self, _tokens: list) -> None:
        pass

    @external
    def setLoanOriginationFeePercentage(self, _percentage: int) -> None:
        pass

    @external(readonly = True)
    def calculateOriginationFee(self, _user: Address, _amount: int) -> int:
        return examul(_amount,self.getLoanOriginationFeePercentage)
        pass
    
    @external(readonly = True)
    def getLoanOriginationFeePercentage(self) -> int:
        pass
        
    @external(readonly = True)
    def getDistribution(self) -> dict:
        pass



    

