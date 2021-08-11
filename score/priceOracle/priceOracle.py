from .addresses import *
from .utils.math import convertToExa, exaMul

EXA = 10 ** 18
STABLE_TOKENS = ["USDS", "USDB"]
BAND_ORACLE = "bandOracle"
DEX = "dex"

OMM_TOKENS = [
    {
        "name": "USDS",
        "priceOracleKey": "USDS",
        "convert": lambda _source, _amount, _decimals: convertToExa(_amount, _decimals)
    },
    {
        "name": "sICX",
        "priceOracleKey": "ICX",
        "convert": lambda _source, _amount, _decimals: exaMul(convertToExa(_amount, _decimals),
                                                              _source.getPriceByName("sICX/ICX"))
    },
    {
        "name": "IUSDC",
        "priceOracleKey": "USDC",
        "convert": lambda _source, _amount, _decimals: convertToExa(_amount, _decimals)
    }
]


class PriceOracle(Addresses):
    _PRICE = 'price'
    _ORACLE_PRICE_BOOL = 'oraclePriceBool'
    _OMM_POOL = "ommPool"

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._price = DictDB(self._PRICE, db, value_type=int, depth=2)
        self._oraclePriceBool = VarDB(self._ORACLE_PRICE_BOOL, db, value_type=bool)
        self._ommPool = VarDB(self._OMM_POOL, db, value_type=str)

    def on_install(self, _addressProvider: Address) -> None:
        super().on_install(_addressProvider)
        self._ommPool.set("OMM")

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return f'Omm {TAG}'

    @external
    @only_owner
    def setOraclePriceBool(self, _value: bool):
        self._oraclePriceBool.set(_value)

    @external(readonly=True)
    def getOraclePriceBool(self) -> bool:
        return self._oraclePriceBool.get()

    @only_owner
    @external
    def setOMMPool(self, _value: str):
        self._ommPool.set(_value)

    @external(readonly=True)
    def getOMMPool(self) -> str:
        return self._ommPool.get()

    @only_owner
    @external
    def set_reference_data(self, _base: str, _quote: str, _rate: int) -> None:
        self._price[_base][_quote] = _rate

    def _get_price(self, _base: str, _quote) -> int:
        if self._oraclePriceBool.get():
            if _base in STABLE_TOKENS:
                return 1 * 10 ** 18
            else:
                oracle = self.create_interface_score(self.getAddress(BAND_ORACLE), OracleInterface)
                price = oracle.get_reference_data(_base, _quote)
                return price['rate']
        else:
            return self._price[_base][_quote]

    def _get_omm_price(self, _quote: str) -> int:
        dex = self.create_interface_score(self.getAddress(DEX), DataSourceInterface)

        _total_price = 0
        _total_omm_supply = 0
        for token in OMM_TOKENS:
            name = token["name"]
            # key in band oracle
            price_oracle_key = token["priceOracleKey"]
            _pool_id = dex.lookupPid(f"{self.getOMMPool()}/{name}")
            if _pool_id == 0:
                continue
            _pool_stats = dex.getPoolStats(_pool_id)

            # convert price to 10**18 precision and calculate price in _quote
            _price = _pool_stats['price']
            _quote_decimals = _pool_stats['quote_decimals']
            _base_decimals = _pool_stats['base_decimals']
            _average_decimals = _quote_decimals * 18 // _base_decimals
            _adjusted_price = token["convert"](dex, _price, _average_decimals)
            _converted_price = exaMul(_adjusted_price, self._get_price(price_oracle_key, _quote))

            _total_supply = _pool_stats['base']

            _total_omm_supply += _total_supply
            _total_price += (_total_supply * _converted_price)

        if _total_omm_supply == 0:
            return -1

        return _total_price // _total_omm_supply

    @external(readonly=True)
    def get_reference_data(self, _base: str, _quote) -> int:
        if _base == 'OMM':
            return self._get_omm_price(_quote)
        else:
            return self._get_price(_base, _quote)
