from iconservice import *

TAG = 'AddressProvider'


class AddressProvider(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._USDb = VarDB('USDb', db, value_type = Address)
        self._sICX = VarDB('sICX', db, value_type = Address)
        self._oUSDb = VarDB('oUSDb', db, value_type = Address)
        self._oICX = VarDB('oICX', db, value_type = Address)
        self._lendingPool = VarDB('lendingPool', db, value_type = Address)
        self._lendingPoolDataProvider = VarDB('lendingPoolDataProvider', db, value_type = Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()
    
    @external
    def setLendingPool(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Only owner can set the address')
        self._lendingPool.set(_address)

    @external
    def setLendingPoolDataProvider(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Only owner can set the address')
        self._lendingPoolDataProvider.set(_address)

    @external
    def setUSDb(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Only owner can set the address')
        self._USDb.set(_address)

    @external
    def setsICX(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Only owner can set the address')
        self._sICX.set(_address)

    @external
    def setoUSDb(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Only owner can set the address')
        self._oUSDb.set(_address)

    @external
    def setoICX(self, _address: Address) -> None:
        if self.msg.sender != self.owner:
            revert(f'Only owner can set the address')
        self._oICX.set(_address)

    @external(readonly = True)
    def getAllAddresses(self) -> dict:
        response = {"collateral" : {
                    "USDb":self._USDb.get(),
                    "sICX":self._sICX.get()
                    },
                    "oTokens": {
                        "oUSDb": self._oUSDb.get(),
                        "oICX": self._oICX.get()
                    },
                    "systemContract":{
                        "LendingPool": self._lendingPool.get(),
                        "LendingPoolDataProvider": self._lendingPoolDataProvider.get()
                    }
                    }
      
        return response






    
    
