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

class AddressProviderInterface(InterfaceScore):
    @interface
    def getReserveAddresses(self):
        pass


