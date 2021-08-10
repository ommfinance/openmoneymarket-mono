from iconservice import *


class AddressDetails(TypedDict):
    name: str
    address: Address


class TokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass


class DaoFundInterface(interfaceScore):
    @interface
    def transferOmmToWallet(self, _value: int, _address: Address):
        pass
