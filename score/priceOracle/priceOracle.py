from iconservice import *

TAG = 'PriceOracle'


class PriceOracle(IconScoreBase):

    PRICE = 'price'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._price = DictDB(self.PRICE, db, value_type = int, depth = 2)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external
    def set_reference_data(self, _base: str, _quote: str, _rate: int) -> None:
        self._price[_base][_quote] = _rate
    
    @external(readonly = True)
    def get_reference_data(self, _base: str, _quote) -> int:
        return self._price[_base][_quote]
