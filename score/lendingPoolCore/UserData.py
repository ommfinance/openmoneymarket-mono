from iconservice import *


class UserReserveData(object):

    def __init__(self, db: IconScoreDatabase) -> None:
        self.lastUpdateTimestamp = VarDB('lastUpdateTimestamp', db, int)
        self.originationFee = VarDB('originationFee', db, int)
        self.useAsCollateral = VarDB('usageAsCollateralEnabled', db, bool)


class UserReserveDataDB:

    def __init__(self, db: IconScoreDatabase):
        self._db = db
        self._items = {}

    def __getitem__(self, prefix: bytes) -> UserReserveData:
        if prefix not in self._items:
            sub_db = self._db.get_sub_db(prefix)
            self._items[prefix] = UserReserveData(sub_db)

        return self._items[prefix]

    def __setitem__(self, key, value):
        revert('illegal access')


def getDataFromUserReserve(prefix: bytes, userReserve: 'UserReserveDataDB') -> dict:
    lastUpdateTimestamp = userReserve[prefix].lastUpdateTimestamp.get()
    originationFee = userReserve[prefix].originationFee.get()
    useAsCollateral = userReserve[prefix].useAsCollateral.get()

    return {
        'lastUpdateTimestamp': lastUpdateTimestamp,
        'originationFee': originationFee,
        'useAsCollateral': useAsCollateral
    }


def createUserReserveDataObject(reserveData: dict) -> 'UserReserveDataObject':
    return UserReserveDataObject(
        lastUpdateTimestamp=reserveData['lastUpdateTimestamp'],
        originationFee=reserveData['originationFee'],
        useAsCollateral=reserveData['useAsCollateral']
    )


class UserReserveDataObject(object):

    def __init__(self, **kwargs) -> None:
        self.lastUpdateTimestamp = kwargs.get('lastUpdateTimestamp')
        self.originationFee = kwargs.get('originationFee')
        self.useAsCollateral = kwargs.get('useAsCollateral')
