from iconservice import *


class ReserveData(object):
    

    def __init__(self, db: IconScoreDatabase) -> None:
        self.reserveAddress = VarDB('id', db, Address)
        self.oTokenAddress = VarDB('oToken', db, Address)
        self.totalBorrows = VarDB('totalBorrow', db, int)
        self.lastUpdateTimestamp = VarDB('lastUpdateTimestamp', db, int)
        self.liquidityRate = VarDB('liquidityRate', db, int)
        self.borrowRate = VarDB('borrowRate', db, int)
        self.liquidityCumulativeIndex = VarDB('liquidityCumulativeIndex', db, int)
        self.borrowCumulativeIndex= VarDB('borrowCumulativeIndex',db,int)
        self.baseLTVasCollateral = VarDB('baseLTLasCollateral', db, int)
        self.liquidationThreshold = VarDB('liquidationThreshold', db, int)
        self.liquidationBonus = VarDB('liquidationBonus', db, int)
        self.decimals = VarDB('decimals', db, int)
        self.borrowingEnabled = VarDB('borrowingEnabled', db, bool)
        self.usageAsCollateralEnabled = VarDB('usageAsCollateralEnabled', db, bool)
        self.isFreezed = VarDB('isFreezed', db, bool)
        self.isActive = VarDB('Active', db, bool)
        

class ReserveDataDB:

    def __init__(self, db: IconScoreDatabase):
        self._db = db
        self._items = {}

    def __getitem__(self, prefix: bytes) -> ReserveData:
        if prefix not in self._items:
            sub_db = self._db.get_sub_db(prefix)
            self._items[prefix] = ReserveData(sub_db)

        return self._items[prefix]

    def __setitem__(self, key, value):
        revert('illegal access')

    # def addToReserve(self,_prefix:bytes,reserveData:'ReserveDataObject'):
    #     self._items[_prefix].totalBorrows.set(reserveData.totalBorrows)
    #     # _reserve[_prefix].totalBorrows.set(reserveData.totalBorrows)
    #     # _reserve[prefix].reserveAddress.set(reserveData.reserveAddress)
    #     # _reserve[prefix].oTokenAddress.set(reserveData.oTokenAddress)
    #     # _reserve[prefix].totalBorrows.set(reserveData.totalBorrows)
    #     # _reserve[prefix].lastUpdateTimestamp.set(reserveData.lastUpdateTimestamp)
    #     # _reserve[prefix].liquidityRate.set(reserveData.liquidityRate)
    #     # _reserve[prefix].borrowRate.set(reserveData.borrowRate)
    #     # _reserve[prefix].liquidityCumulativeIndex.set(reserveData.liquidityCumulativeIndex)
    #     # _reserve[prefix].baseLTVasCollateral.set(reserveData.baseLTVasCollateral)
    #     # _reserve[prefix].liquidationThreshold.set(reserveData.liquidationThreshold)
    #     # _reserve[prefix].liquidationBonus.set(reserveData.liquidationBonus)
    #     # _reserve[prefix].decimals.set(reserveData.decimals)
    #     # _reserve[prefix].borrowingEnabled.set(reserveData.borrowingEnabled)
    #     # _reserve[prefix].usageAsCollateralEnabled.set(reserveData.usageAsCollateralEnabled),
    #     # _reserve[prefix].isFreezed.set(reserveData.isFreezed)
    #     # _reserve[prefix].isActive.set(reserveData.isActive)


def addDataToReserve(prefix: bytes, _reserve: 'ReserveDataDB', reserveData: 'ReserveDataObject'):
    _reserve[prefix].totalBorrows.set(reserveData.totalBorrows)
    _reserve[prefix].reserveAddress.set(reserveData.reserveAddress)
    _reserve[prefix].oTokenAddress.set(reserveData.oTokenAddress)
    _reserve[prefix].totalBorrows.set(reserveData.totalBorrows)
    _reserve[prefix].lastUpdateTimestamp.set(reserveData.lastUpdateTimestamp)
    _reserve[prefix].liquidityRate.set(reserveData.liquidityRate)
    _reserve[prefix].borrowRate.set(reserveData.borrowRate)
    _reserve[prefix].liquidityCumulativeIndex.set(reserveData.liquidityCumulativeIndex)
    _reserve[prefix].borrowCumulativeIndex.set(reserveData.borrowCumulativeIndex)
    _reserve[prefix].baseLTVasCollateral.set(reserveData.baseLTVasCollateral)
    _reserve[prefix].liquidationThreshold.set(reserveData.liquidationThreshold)
    _reserve[prefix].liquidationBonus.set(reserveData.liquidationBonus)
    _reserve[prefix].decimals.set(reserveData.decimals)
    _reserve[prefix].borrowingEnabled.set(reserveData.borrowingEnabled)
    _reserve[prefix].usageAsCollateralEnabled.set(reserveData.usageAsCollateralEnabled),
    _reserve[prefix].isFreezed.set(reserveData.isFreezed)
    _reserve[prefix].isActive.set(reserveData.isActive)


def getDataFromReserve(prefix: bytes, _reserve: 'ReserveDataDB') -> dict:
    reserveAddress = _reserve[prefix].reserveAddress.get()
    oTokenAddress = _reserve[prefix].oTokenAddress.get()
    totalBorrows = _reserve[prefix].totalBorrows.get()
    lastUpdateTimestamp = _reserve[prefix].lastUpdateTimestamp.get()
    liquidityRate = _reserve[prefix].liquidityRate.get()
    borrowRate = _reserve[prefix].borrowRate.get()
    liquidityCumulativeIndex = _reserve[prefix].liquidityCumulativeIndex.get()
    borrowCumulativeIndex=_reserve[prefix].borrowCumulativeIndex.get()
    baseLTVasCollateral = _reserve[prefix].baseLTVasCollateral.get()
    liquidationThreshold = _reserve[prefix].liquidationThreshold.get()
    liquidationBonus = _reserve[prefix].liquidationBonus.get()
    decimals = _reserve[prefix].decimals.get()
    borrowingEnabled = _reserve[prefix].borrowingEnabled.get()
    usageAsCollateralEnabled = _reserve[prefix].usageAsCollateralEnabled.get(),
    isFreezed = _reserve[prefix].isFreezed.get()
    isActive = _reserve[prefix].isActive.get()
    return {
        'reserveAddress': reserveAddress,
        'oTokenAddress': oTokenAddress,
        'totalBorrows': totalBorrows,
        'lastUpdateTimestamp': lastUpdateTimestamp,
        'liquidityRate': liquidityRate,
        'borrowRate': borrowRate,
        'liquidityCumulativeIndex': liquidityCumulativeIndex,
        'borrowCumulativeIndex':borrowCumulativeIndex,
        'baseLTVasCollateral': baseLTVasCollateral,
        'liquidationThreshold': liquidationThreshold,
        'liquidationBonus': liquidationBonus,
        'decimals': decimals,
        'borrowingEnabled': borrowingEnabled,
        'usageAsCollateralEnabled': usageAsCollateralEnabled,
        'isFreezed': isFreezed,
        'isActive': isActive
    }


def createReserveDataObject(reserveData: dict) -> 'ReserveDataObject':
    return ReserveDataObject(reserveAddress=reserveData['reserveAddress'],
                             oTokenAddress=reserveData['oTokenAddress'],
                             totalBorrows=reserveData['totalBorrows'],
                             lastUpdateTimestamp=reserveData['lastUpdateTimestamp'],
                             liquidityRate=reserveData['liquidityRate'],
                             borrowRate=reserveData['borrowRate'],
                             liquidityCumulativeIndex=reserveData['liquidityCumulativeIndex'],
                             borrowCumulativeIndex=reserveData['borrowCumulativeIndex'],
                             baseLTVasCollateral=reserveData['baseLTVasCollateral'],
                             liquidationThreshold=reserveData['liquidationThreshold'],
                             liquidationBonus=reserveData['liquidationBonus'],
                             decimals=reserveData['decimals'],
                             borrowingEnabled=reserveData['borrowingEnabled'],
                             usageAsCollateralEnabled=reserveData['usageAsCollateralEnabled'],
                             isFreezed=reserveData['isFreezed'],
                             isActive=reserveData['isActive']
                             )


class ReserveDataObject(object):

    def __init__(self, **kwargs) -> None:
        self.reserveAddress = kwargs.get('reserveAddress')
        self.oTokenAddress = kwargs.get('oTokenAddress')
        self.totalBorrows = kwargs.get('totalBorrows')
        self.lastUpdateTimestamp = kwargs.get('lastUpdateTimestamp')
        self.liquidityRate = kwargs.get('liquidityRate')
        self.borrowRate = kwargs.get('borrowRate')
        self.liquidityCumulativeIndex = kwargs.get('liquidityCumulativeIndex')
        self.borrowCumulativeIndex=kwargs.get('borrowCumulativeIndex')
        self.baseLTVasCollateral = kwargs.get('baseLTVasCollateral')
        self.liquidationThreshold = kwargs.get('liquidationThreshold')
        self.liquidationBonus = kwargs.get('liquidationBonus')
        self.decimals = kwargs.get('decimals')
        self.borrowingEnabled = kwargs.get('borrowingEnabled')
        self.usageAsCollateralEnabled = kwargs.get('usageAsCollateralEnabled')
        self.isFreezed = kwargs.get('isFreezed')
        self.isActive = kwargs.get('isActive')
