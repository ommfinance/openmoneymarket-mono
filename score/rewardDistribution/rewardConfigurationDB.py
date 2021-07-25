from iconservice import *

from .Math import exaMul
from .utils.types import AssetConfig

TAG = "Reward Distribution Storage"

SUPPORTED_RECIPIENTS = ["worker", "daoFund", "lendingBorrow", "liquidityProvider"]


class ItemNotFound(Exception):
    pass


class ItemNotSupported(Exception):
    pass


class RewardConfigurationDB(object):
    EMISSION_PER_SECOND = 'EmissionPerSecond'
    DISTRIBUTION_PERCENTAGE = 'DistributionPercentage'
    ASSET_LEVEL_PERCENTAGE = 'AssetLevelPercentage'
    ASSET_MAPPING = 'AssetMapping'
    POOL_ID_MAPPING = 'PoolIDMapping'
    ASSET_NAME = 'AssetName'
    ASSETS = 'Assets'
    ASSET_INDEXES = 'AssetINDEXES'

    def __init__(self, key: str, db: IconScoreDatabase) -> None:
        self._distributionPercentage = DictDB(f'{key}{self.DISTRIBUTION_PERCENTAGE}', db, value_type=int)
        self._emissionPerSecond = DictDB(f'{key}{self.EMISSION_PER_SECOND}', db, value_type=int)
        self._assetLevelPercentage = DictDB(f'{key}{self.ASSET_LEVEL_PERCENTAGE}', db, value_type=int)

        self._assetMapping = DictDB(f'{key}{self.ASSET_MAPPING}', db, value_type=str)
        self._poolIDMapping = DictDB(f'{key}{self.POOL_ID_MAPPING}', db, value_type=int)

        self._assetName = DictDB(f'{key}{self.ASSET_NAME}', db, value_type=str)

        self._assets = ArrayDB(f'{key}{self.ASSETS}', db, value_type=Address)
        self._indexes = DictDB(f'{key}{self.ASSET_INDEXES}', db, value_type=int)

    def __get_size(self) -> int:
        return len(self._assets)

    def __get_index(self, asset) -> int:
        return self._indexes[asset]

    def __len__(self) -> int:
        return self.__get_size()

    def __add_asset(self, asset) -> None:
        index = self.__get_index(asset)
        if index == 0:
            self._assets.put(asset)
            self._indexes[asset] = self.__len__()

    def setDistributionPercentage(self, recipient: str, percentage: int):
        if recipient not in SUPPORTED_RECIPIENTS:
            raise ItemNotSupported(f"{TAG}: unsupported recipient {recipient}")
        self._distributionPercentage[recipient] = percentage

    def getDistributionPercentage(self, recipient: str) -> int:
        return self._distributionPercentage[recipient]

    def getAllDistributionPercentage(self) -> dict:
        return {
            recipient: self._distributionPercentage[recipient]
            for recipient in SUPPORTED_RECIPIENTS
        }

    def getRecipients(self) -> list:
        return [item for item in SUPPORTED_RECIPIENTS]

    def removeAssetConfig(self, asset: Address) -> None:
        index = self.__get_index(asset)
        if index == 0:
            raise ItemNotFound(f"{TAG}: Asset not found {asset}")

        self._assetLevelPercentage[asset].remove(asset)
        self._assetMapping[asset].remove(asset)
        self._assetName[asset].remove(asset)
        self._poolIDMapping[asset].remove(asset)

        last_index = self.__len__()
        last_asset = self._assets.pop()
        self._indexes.remove(asset)
        if index != last_index:
            self._assets[index - 1] = last_asset
            self._indexes[last_asset] = index

    def setAssetConfig(self, config: AssetConfig) -> None:
        asset = config['asset']
        assetName = config['assetName']
        distPercentage = config['distPercentage']
        self._assetLevelPercentage[asset] = distPercentage
        self._assetMapping[asset] = config['mapping']
        self._poolIDMapping[asset] = config['_id']
        self._assetName[asset] = assetName

        self.__add_asset(asset)

    def getPoolID(self, asset: Address) -> int:
        return self._poolIDMapping[asset]

    def updateEmissionPerSecond(self, asset: Address, distributionPerDay: int) -> int:
        _percentage = self.getAssetPercentage(asset)
        _emissionPerSecond = exaMul(distributionPerDay // 86400, _percentage)
        self._emissionPerSecond[asset] = _emissionPerSecond
        return _emissionPerSecond

    def getAssetPercentage(self, asset: Address) -> int:
        _parentKey = self._assetMapping[asset]
        _distPercentage = self._distributionPercentage[_parentKey]
        _assetPercentage = self._assetLevelPercentage[asset]
        _actualPercentage = exaMul(_distPercentage, _assetPercentage)
        return _actualPercentage

    def getAssets(self):
        return self._assets

    def getEmissionPerSecond(self, asset: Address) -> int:
        return self._emissionPerSecond[asset]

    def getAllEmissionPerSecond(self) -> dict:
        return {
            str(asset): self._emissionPerSecond[asset]
            for asset in self._assets
        }

    def getAssetNames(self) -> dict:
        return {str(item): self._assetName[item] for item in self._assets}

    def setAssetName(self, asset: Address, name: str):
        if asset not in self._assets:
            raise ItemNotFound(f"{TAG}: Asset not found {asset}")
        self._assetName[asset] = name

    def getAssetName(self, asset: Address) -> str:
        return self._assetName[asset]
