from .utils.Math import convertToExa, exaMul
from .utils.checks import *

OMM_TOKENS = [
    {
        "name": "OMM/USDS",
        "base": "USDS",
        "convert": lambda _amount, _source: _amount
    },
    {
        "name": "OMM/sICX",
        "base": "ICX",
        "convert": lambda _amount, _source: exaMul(_amount, _source.getPriceByName("sICX/ICX"))
    },
    {
        "name": "OMM/IUSDC",
        "base": "IUSDC",
        "convert": lambda _amount, _source: convertToExa(_amount, 6)
    }
]


class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> dict:
        pass


class DataSourceInterface(InterfaceScore):
    @interface
    def getPriceByName(self, _name: str) -> int:
        pass


class PriceOracle(IconScoreBase):
    _PRICE = 'price'
    _BAND_ORACLE = 'bandOracle'
    _ORACLE_PRICE_BOOL = 'oraclePriceFeed'
    _DATA_SOURCE = 'data_source'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._price = DictDB(self._PRICE, db, value_type=int, depth=2)
        self._bandOracle = VarDB(self._BAND_ORACLE, db, value_type=Address)
        self._oraclePriceBool = VarDB(self._ORACLE_PRICE_BOOL, db, value_type=bool)
        self._data_source = VarDB(self._DATA_SOURCE, db, value_type=Address)

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

    @external()
    @only_owner
    def setDataSource(self, _address: Address):
        self._data_source.set(_address)

    def getDataSource(self) -> Address:
        return self._data_source.get()

    @only_owner
    @external
    def set_reference_data(self, _base: str, _quote: str, _rate: int) -> None:
        self._price[_base][_quote] = _rate

    def _get_price(self, _base: str, _quote) -> int:
        if self._oraclePriceBool.get():
            oracle = self.create_interface_score(self._bandOracle.get(), OracleInterface)
            price = oracle.get_reference_data(_base, _quote)
            return price['rate']
        else:
            return self._price[_base][_quote]

    def _get_omm_price(self, _quote) -> int:
        lp_token = self.create_interface_score(self.getDataSource(), DataSourceInterface)
        _total_price = 0
        for token in OMM_TOKENS:
            name = token["name"]
            base = token["base"]
            _price = lp_token.getPriceByName(name)
            _adjusted_price = token["convert"](_price, lp_token)
            _total_price += exaMul(_adjusted_price, self._get_price(base, _quote))

        return _total_price // len(OMM_TOKENS)

    @external(readonly=True)
    def get_reference_data(self, _base: str, _quote) -> int:
        if _base == 'OMM':
            return self._get_omm_price(_quote)
        else:
            return self._get_price(_base, _quote)
