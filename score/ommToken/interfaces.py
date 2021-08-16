from iconservice import *


class Status:
    STAKED = 1
    UNSTAKING = 2
    UNSTAKING_PERIOD = 3


class AddressDetails(TypedDict):
    name: str
    address: Address


class PrepDelegationDetails(TypedDict):
    prepAddress: Address
    prepPercentage: int


class SupplyDetails(TypedDict):
    decimals: int
    principalUserBalance: int
    principalTotalSupply: int


class TotalStaked(TypedDict):
    decimals: int
    totalStaked: int
    

class TokenFallbackInterface(InterfaceScore):
    @interface
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        pass


class DelegationInterface(InterfaceScore):
    @interface
    def updateDelegations(self, _delegations: List[PrepDelegationDetails] = None, _user: Address = None):
        pass


class RewardDistributionInterface(InterfaceScore):
    @interface
    def handleAction(self, _user: Address, _userBalance: int, _totalSupply: int) -> None:
        pass


class LendingPoolInterface(InterfaceScore):
    @interface
    def isFeeSharingEnable(self, _user: Address) -> bool:
        pass
