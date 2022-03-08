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


class UserDetails(TypedDict):
    _user: Address
    _userBalance: int
    _totalSupply: int
    _decimals: int


class OnStakeChangedParams(TypedDict):
    _user: Address
    _new_total_staked_balance: int
    _old_total_staked_balance: int
    _user_new_staked_balance: int
    _user_old_staked_balance: int


class TokenFallbackInterface(InterfaceScore):
    @interface
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        pass

class BoostedOmmInterface(InterfaceScore):
    @interface
    def getLocked(self, _user: Address):
        pass

class RewardDistributionInterface(InterfaceScore):
    @interface
    def handleAction(self, _userDetails: UserDetails) -> None:
        pass


class LendingPoolInterface(InterfaceScore):
    @interface
    def isFeeSharingEnable(self, _user: Address) -> bool:
        pass
