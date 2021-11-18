from iconservice import *


class AddressDetails(TypedDict):
    name: str
    address: Address


class TokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

    @interface
    def balanceOf(self, _owner: Address):
        pass

    @interface
    def decimals(self):
        pass

class OMMInterface(InterfaceScore):
    @interface
    def burn(self, _value: int):
        pass
        
    @interface
    def balanceOf(self, _owner: Address):
        pass

class CoreInterface(InterfaceScore):
    @interface
    def getReserves(self):
        pass