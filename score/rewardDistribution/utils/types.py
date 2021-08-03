from iconservice import *


class SupplyDetails(TypedDict):
    principalUserBalance: int
    principalTotalSupply: int


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
