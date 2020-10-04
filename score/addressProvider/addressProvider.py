from iconservice import *

TAG = 'AddressProvider'


class AddressProvider(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()
    
    @external
    def setLendingPool(self, _pool: Address) -> None:
        pass

    @external
    def setLendingPoolCore(self, _pool: Address) -> None:
        pass

    @external
    def setLendingPoolConfigurator(self, _pool: Address) -> None:
        pass

    @external
    def setFeeProvider(self, _pool: Address) -> None:
        pass

    @external
    def setLiquidationManager(self, _pool: Address) -> None:
        pass

    @external
    def getPriceOracle(self) -> None:
        pass

    @external
    def setDaoFund(self) -> None:
        pass

    @external(readonly = True)
    def getAddress(self, _name: str) -> Address:
        pass
    
    
