from iconservice import *


class RewardPercentageConfig(TypedDict):
    _percentage: int
    _address: Address
    _asset: Address


class ItemNotFound(Exception):
    pass


class RewardPercentageDB(object):

    def __init__(self, _key: str, db: IconScoreDatabase):
        self._assets = ArrayDB(f'{_key}__assets__', db, value_type=Address)
        self._percentage = DictDB(f'{_key}__percentage__', db, value_type=int)
        self._addresses = DictDB(f'{_key}__address__', db, value_type=Address)
        self._indexes = DictDB(f'{_key}__indexes__', db, value_type=int)

    def __index_of(self, value) -> int:
        return self._indexes[value]

    def add(self, _config: RewardPercentageConfig):
        _asset = _config['_asset']
        _address = _config['_address']
        _percentage = _config['_percentage']
        index = self.__index_of(_asset)
        if index == 0:
            self._assets.put(_asset)
            self._indexes[_asset] = len(self._assets)
        self._percentage[_asset] = _percentage
        self._addresses[_asset] = _address

    def get(self, _asset: Address) -> dict:
        index = self.__index_of(_asset)
        if index == 0:
            raise ItemNotFound(f"{_asset} not found")
        _address = self._addresses['_address']
        _percentage = self._percentage['_percentage']
        return {
            "_address": _address,
            "_percentage": _percentage
        }

    def remove(self, _asset):
        value_index = self.__index_of(_asset)
        if value_index != 0:
            last_index = len(self._assets)
            last_entry = self._assets.pop()
            self._indexes.remove(_asset)
            self._percentage.remove(_asset)
            self._addresses.remove(_asset)
            if value_index != last_index:
                self._assets[value_index - 1] = last_entry
                self._indexes[last_entry] = value_index

    def getAssets(self) -> ArrayDB:
        return self._assets
