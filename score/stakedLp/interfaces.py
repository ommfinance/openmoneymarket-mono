from iconservice import *


class Status:
    STAKED = 1


class SupplyDetails(TypedDict):
    decimals: int
    principalUserBalance: int
    principalTotalSupply: int


class TotalStaked(TypedDict):
    decimals: int
    totalStaked: int


class AddressDetails(TypedDict):
    name: str
    address: Address


class UserDetails(TypedDict):
    _user: Address
    _userBalance: int
    _totalSupply: int
    _decimals: int


class AssetConfig(TypedDict):
    _id: int
    asset: Address
    distPercentage: int
    assetName: str
    rewardEntity: str


class RewardInterface(InterfaceScore):
    @interface
    def handleLPAction(self, _asset: Address, _userDetails: UserDetails) -> None:
        pass


class LiquidityPoolInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address, _id: int) -> int:
        pass

    @interface
    def transfer(self, _to: Address, _value: int, _id: int, _data: bytes = None):
        pass

    @interface
    def getPoolStats(self, _id: int) -> dict:
        pass
