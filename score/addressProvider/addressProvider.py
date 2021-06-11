from iconservice import *


class AddressProvider(IconScoreBase):
    USDs = 'usds'
    sICX = 'sicx'
    IUSDC = 'iusdc'
    oICX = 'oICX'
    oUSDs = 'ousds'
    oIUSDC = 'oiusdc'
    dICX = 'dICX'
    dUSDs = 'dusds'
    dIUSDC = 'diusdc'
    LENDING_POOL = 'lendingPool'
    LENDING_POOL_DATA_PROVIDER = 'lendingPoolDataProvider'
    STAKING = 'staking'
    DELEGATION = 'delegation'
    OMM_TOKEN = 'ommToken'
    REWARDS = 'rewards'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._addresses = DictDB("address", db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "OmmAddressProvider"

    def _get_address(self, name: str) -> Address:
        return self._addresses[name]

    def _set_address(self, name: str, address: Address):
        if self.msg.sender != self.owner:
            revert(f"Only owner can set the address")
        self._addresses[name] = address

    @external
    def setLendingPool(self, _address: Address) -> None:
        self._set_address(self.LENDING_POOL, _address)

    @external
    def setLendingPoolDataProvider(self, _address: Address) -> None:
        self._set_address(self.LENDING_POOL_DATA_PROVIDER, _address)

    @external
    def setUSDs(self, _address: Address) -> None:
        self._set_address(self.USDs, _address)

    @external
    def setsICX(self, _address: Address) -> None:
        self._set_address(self.sICX, _address)

    @external
    def setoUSDs(self, _address: Address) -> None:
        self._set_address(self.oUSDs, _address)

    @external
    def setdUSDs(self, _address: Address) -> None:
        self._set_address(self.dUSDs, _address)

    @external
    def setoICX(self, _address: Address) -> None:
        self._set_address(self.oICX, _address)

    @external
    def setdICX(self, _address: Address) -> None:
        self._set_address(self.dICX, _address)

    @external
    def setStaking(self, _address: Address) -> None:
        self._set_address(self.STAKING, _address)

    @external
    def setIUSDC(self, _address: Address) -> None:
        self._set_address(self.IUSDC, _address)

    @external
    def setoIUSDC(self, _address: Address) -> None:
        self._set_address(self.oIUSDC, _address)

    @external
    def setdIUSDC(self, _address: Address) -> None:
        self._set_address(self.dIUSDC, _address)

    @external
    def setOmmToken(self, _address: Address) -> None:
        self._set_address(self.OMM_TOKEN, _address)

    @external
    def setDelegation(self, _address: Address) -> None:
        self._set_address(self.DELEGATION, _address)

    @external
    def setRewards(self, _address: Address) -> None:
        self._set_address(self.REWARDS, _address)

    @external(readonly=True)
    def getAllAddresses(self) -> dict:
        return {
            "collateral": {
                "USDS": self._get_address(self.USDs),
                "sICX": self._get_address(self.sICX),
                "IUSDC": self._get_address(self.IUSDC),
            },
            "oTokens": {
                "oUSDS": self._get_address(self.oUSDs),
                "oICX": self._get_address(self.oICX),
                "oIUSDC": self._get_address(self.oIUSDC),
            },
            "dTokens": {
                "dUSDS": self._get_address(self.dUSDs),
                "dICX": self._get_address(self.dICX),
                "dIUSDC": self._get_address(self.dIUSDC),
            },
            "systemContract": {
                "LendingPool": self._get_address(self.LENDING_POOL),
                "LendingPoolDataProvider": self._get_address(self.LENDING_POOL_DATA_PROVIDER),
                "Staking": self._get_address(self.STAKING),
                "Delegation": self._get_address(self.DELEGATION),
                "OmmToken": self._get_address(self.OMM_TOKEN),
                "Rewards": self._get_address(self.REWARDS),
            }
        }
