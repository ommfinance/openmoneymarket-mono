from iconservice import *


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


class AssetConfig(TypedDict):
    poolID: int
    asset: Address
    distPercentage: int
    assetName: str
    rewardEntity: str


class UserAssetInput(TypedDict):
    asset: Address
    userBalance: int
    totalBalance: int


class DistPercentage(TypedDict):
    recipient: str
    percentage: int
