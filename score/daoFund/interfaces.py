from iconservice import *


class AddressDetails(TypedDict):
    name: str
    address: Address


class TokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass



