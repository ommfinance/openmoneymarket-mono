from iconservice import *


class SupplyDetails(TypedDict):
    decimals: int
    principalUserBalance: int
    principalTotalSupply: int


class TotalStaked(TypedDict):
    decimals: int
    totalStaked: int


class UserDetails(TypedDict):
    _user: Address
    _userBalance: int
    _totalSupply: int
    _decimals: int


class AddressDetails(TypedDict):
    name: str
    address: Address


class LendingPoolCoreInterface(InterfaceScore):
    @interface
    def getNormalizedDebt(self, _reserve: Address) -> int:
        pass

    @interface
    def getReserveBorrowCumulativeIndex(self, _reserve: int) -> int:
        pass


class DistributionManager(InterfaceScore):
    @interface
    def handleAction(self, _userDetails: UserDetails) -> None:
        pass


class TokenFallbackInterface(InterfaceScore):
    @interface
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        pass
