from iconservice import *

class AddressDetails(TypedDict):
    name: str
    address: Address


class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> dict:
        pass


class DataSourceInterface(InterfaceScore):
    @interface
    def lookupPid(self, _name: str) -> int:
        pass

    @interface
    def getPoolStats(self, _id: int) -> dict:
        pass

    @interface
    def getPriceByName(self, _name: str) -> int:
        pass

    @interface
    def getBalnPrice(self) -> int:
        pass


class TokenInterface(InterfaceScore):
    @interface
    def decimals(self) -> int:
        pass

