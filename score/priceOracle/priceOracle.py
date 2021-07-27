from .utils.Math import convertToExa, exaMul
from .utils.checks import *

BAND_ORACLE = 'bandOracle'
DEX = 'dex'
ADDRESS_PROVIDER = 'addressProvider'
STABLE_TOKENS = ["USDS", "USDB"]

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


class AddressDetails(TypedDict):
    name: str
    address: Address


class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> dict:
        pass


class AddressProviderInterface(InterfaceScore):
    @interface
    def getReserveAddresses(self) -> dict:
        pass


class DataSourceInterface(InterfaceScore):
    @interface
    def getPriceByName(self, _name: str) -> int:
        pass


class TokenInterface(InterfaceScore):
    @interface
    def decimals(self) -> int:
        pass


class PriceOracle(IconScoreBase):
    _PRICE = 'price'
    _ORACLE_PRICE_BOOL = 'oraclePriceFeed'

    _ADDRESSES = 'addresses'
    _CONTRACTS = 'contracts'

    _OMM_POOL = "ommPool"

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._price = DictDB(self._PRICE, db, value_type=int, depth=2)
        self._oraclePriceBool = VarDB(self._ORACLE_PRICE_BOOL, db, value_type=bool)
        self._ommPool = VarDB(self._OMM_POOL, db, value_type=str)
        self._addresses = DictDB(self._ADDRESSES, db, value_type=Address)
        self._contracts = ArrayDB(self._CONTRACTS, db, value_type=str)

    def on_install(self) -> None:
        super().on_install()
        self._oraclePriceBool.set(True)
        self._ommPool.set("OMM")

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return f"{TAG}"

    @origin_owner
    @external
    def setAddresses(self, _addressDetails: List[AddressDetails]) -> None:
        for contracts in _addressDetails:
            if contracts['name'] not in self._contracts:
                self._contracts.put(contracts['name'])
            self._addresses[contracts['name']] = contracts['address']

    @external(readonly=True)
    def getAddresses(self) -> dict:
        return {item: self._addresses[item] for item in self._contracts}

    @external(readonly=True)
    def getAddress(self, _name: str) -> Address:
        return self._addresses[_name]

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
        lp_token = self.create_interface_score(self.getAddress(DEX), DataSourceInterface)
        address_provider = self.create_interface_score(self.getAddress(ADDRESS_PROVIDER), AddressProviderInterface)
        reserve_addresses = address_provider.getReserveAddresses()

        _total_price = 0
        for token in OMM_TOKENS:
            name = token["name"]
            price_oracle_key = token["priceOracleKey"]

            _price = lp_token.getPriceByName(f"{self.getOMMPool()}/{name}")

            _interface = self.create_interface_score(reserve_addresses[name], TokenInterface)
            _decimals = _interface.decimals()

            _adjusted_price = token["convert"](lp_token, _price, _decimals)
            _total_price += exaMul(_adjusted_price, self._get_price(price_oracle_key, _quote))

        return _total_price // len(OMM_TOKENS)

    @external(readonly=True)
    def get_reference_data(self, _base: str, _quote) -> int:
        if _base == 'OMM':
            return self._get_omm_price(_quote)
        else:
            return self._get_price(_base, _quote)
