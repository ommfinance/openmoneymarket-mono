from .utils.checks import *


class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> dict:
        pass


class PriceOracle(IconScoreBase):
    _PRICE = 'price'
    _BAND_ORACLE = 'bandOracle'
    _ORACLE_PRICE_BOOL = 'oraclePriceFeed'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._price = DictDB(self._PRICE, db, value_type=int, depth=2)
        self._bandOracle = VarDB(self._BAND_ORACLE, db, value_type=Address)
        self._oraclePriceBool = VarDB(self._ORACLE_PRICE_BOOL, db, value_type=bool)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "OmmPriceOracleProxy"

    @external
    @only_owner
    def toggleOraclePriceBool(self):
        self._oraclePriceBool.set(not self._oraclePriceBool.get())

    @external(readonly=True)
    def getOraclePriceBool(self) -> bool:
        return self._oraclePriceBool.get()

    @external
    @only_owner
    def setBandOracle(self, _address: Address):
        self._bandOracle.set(_address)

    def getBandOracle(self) -> Address:
        return self._bandOracle.get()

    @only_owner
    @external
    def set_reference_data(self, _base: str, _quote: str, _rate: int) -> None:
        self._price[_base][_quote] = _rate

    @external(readonly=True)
    def get_reference_data(self, _base: str, _quote) -> int:
        if self._oraclePriceBool.get():
            if _base == "USDb":
                return 10 ** 18
            else:
                oracle = self.create_interface_score(self._bandOracle.get(), OracleInterface)
                price = oracle.get_reference_data(_base, _quote)
                return price['rate']
        else:
            return self._price[_base][_quote]
