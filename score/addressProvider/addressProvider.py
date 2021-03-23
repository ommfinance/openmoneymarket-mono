from iconservice import *
from .utils.checks import *

TAG = 'AddressProvider'


class AddressProvider(IconScoreBase):
    USDb = 'usdb'
    sICX = 'sicx'
    oICX = 'oICX'
    oUSDb = 'ousdb'
    IUSDC = 'iusdc'
    oIUSDC = 'oiusdc'
    LENDING_POOL = 'lendingPool'
    LENDING_POOL_DATA_PROVIDER = 'lendingPoolDataProvider'
    STAKING = 'staking'
    DELEGATION ='delegation'
    OMM_TOKEN = 'ommToken'
    REWARDS = 'rewards'


    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._USDb = VarDB(self.USDb, db, value_type=Address)
        self._sICX = VarDB(self.sICX, db, value_type=Address)
        self._oUSDb = VarDB(self.oUSDb, db, value_type=Address)
        self._oICX = VarDB(self.oICX, db, value_type=Address)
        self._lendingPool = VarDB(self.LENDING_POOL, db, value_type=Address)
        self._lendingPoolDataProvider = VarDB(self.LENDING_POOL_DATA_PROVIDER, db, value_type=Address)
        self._staking = VarDB(self.STAKING, db, value_type=Address)
        self._IUSDC = VarDB(self.IUSDC, db, value_type=Address)
        self._oIUSDC = VarDB (self.oIUSDC, db, value_type=Address)
        self._ommToken = VarDB(self.OMM_TOKEN,db,value_type=Address)
        self._delegation = VarDB(self.DELEGATION,db,value_type=Address)
        self._rewards = VarDB(self.REWARDS,db,value_type=Address)


    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str :
        return "OmmAddressProvider" 

    @only_owner
    @external
    def setLendingPool(self, _address: Address) -> None:
        self._lendingPool.set(_address)

    @only_owner
    @external
    def setLendingPoolDataProvider(self, _address: Address) -> None:
        self._lendingPoolDataProvider.set(_address)

    @only_owner
    @external
    def setUSDb(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Only owner can set the address')
        self._USDb.set(_address)

    @only_owner
    @external
    def setsICX(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Only owner can set the address')
        self._sICX.set(_address)

    @only_owner
    @external
    def setoUSDb(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Only owner can set the address')
        self._oUSDb.set(_address)

    @only_owner
    @external
    def setoICX(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Only owner can set the address')
        self._oICX.set(_address)

    @only_owner
    @external
    def setStaking(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Only owner can set the address')
        self._staking.set(_address)

    @only_owner
    @external
    def setIUSDC(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Only owner can set the address')
        self._IUSDC.set(_address)

    @only_owner
    @external
    def setoIUSDC(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Only owner can set the address')
        self._oIUSDC.set(_address)

    @only_owner
    @external
    def setOmmToken(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Only owner can set the address')
        self._ommToken.set(_address)
    
    @only_owner
    @external
    def setDelegation(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Only owner can set the address')
        self._delegation.set(_address)

    @only_owner
    @external
    def setRewards(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Only owner can set the address')
        self._rewards.set(_address)

    @external(readonly=True)
    def getAllAddresses(self) -> dict:
        response = {"collateral": {
            "USDb": self._USDb.get(),
            "sICX": self._sICX.get(),
            "IUSDC": self._IUSDC.get()
        },
            "oTokens": {
                "oUSDb": self._oUSDb.get(),
                "oICX": self._oICX.get(),
                "oIUSDC": self._oIUSDC.get()
            },
            "systemContract": {
                "LendingPool": self._lendingPool.get(),
                "LendingPoolDataProvider": self._lendingPoolDataProvider.get(),
                "Staking": self._staking.get(),
                "Delegation": self._delegation.get(),
                "OmmToken": self._ommToken.get(),
                "Rewards": self._rewards.get()
            }
        }

        return response
