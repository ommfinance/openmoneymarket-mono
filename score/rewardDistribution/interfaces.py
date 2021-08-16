from iconservice import *
from .utils.types import SupplyDetails, TotalStaked


class TokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

    @interface
    def mint(self, _amount: int):
        pass

    @interface
    def getTotalStaked(self) -> TotalStaked:
        pass

    @interface
    def getPrincipalSupply(self, _user: Address) -> SupplyDetails:
        pass


class LPInterface(InterfaceScore):

    @interface
    def getTotalStaked(self, _id: int) -> TotalStaked:
        pass

    @interface
    def getPoolById(self, _id: int) -> Address:
        pass

    @interface
    def getLPStakedSupply(self, _id: int, _user: Address) -> SupplyDetails:
        pass


# An interface to Worker Token
class WorkerTokenInterface(InterfaceScore):
    @interface
    def getWallets(self) -> list:
        pass

    @interface
    def totalSupply(self) -> int:
        pass

    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass


# An interface to LendingPoolCore
class CoreInterface(InterfaceScore):
    @interface
    def getReserves(self) -> list:
        pass

    @interface
    def getReserveConfiguration(self, _reserve: Address) -> dict:
        pass
