from iconservice import *


class UserReserveData(object):

    def __init__(self, db: IconScoreDatabase) -> None:
        self.reserveAddress = VarDB('id', db, Address)
        self.userAddress = VarDB('oToken', db, Address)
        self.principalBorrowBalance = VarDB('principalBorrowBalance', db, int)
        self.userBorrowCumulativeIndex = VarDB('userBorrowCumulativeIndex', db, int)
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


def addDataToUserReserve(prefix: bytes, userReserve: 'UserReserveDataDB', userReserveData: 'UserReserveDataObject'):
    userReserve[prefix].reserveAddress.set(userReserveData.reserveAddress)
    userReserve[prefix].userAddress.set(userReserveData.userAddress)
    userReserve[prefix].principalBorrowBalance.set(userReserveData.principalBorrowBalance)
    userReserve[prefix].userBorrowCumulativeIndex.set(userReserveData.userBorrowCumulativeIndex)
    userReserve[prefix].lastUpdateTimestamp.set(userReserveData.lastUpdateTimestamp)
    userReserve[prefix].originationFee.set(userReserveData.originationFee)
    userReserve[prefix].useAsCollateral.set(userReserveData.useAsCollateral)


def getDataFromUserReserve(prefix: bytes, userReserve: 'UserReserveDataDB') -> dict:
    reserveAddress = userReserve[prefix].reserveAddress.get()
    userAddress = userReserve[prefix].userAddress.get()
    principalBorrowBalance = userReserve[prefix].principalBorrowBalance.get()
    userBorrowCumulativeIndex = userReserve[prefix].userBorrowCumulativeIndex.get()
    lastUpdateTimestamp = userReserve[prefix].lastUpdateTimestamp.get()
    originationFee = userReserve[prefix].originationFee.get()
    useAsCollateral = userReserve[prefix].useAsCollateral.get()

    return {
        'reserveAddress': reserveAddress,
        'userAddress': userAddress,
        'principalBorrowBalance': principalBorrowBalance,
        'userBorrowCumulativeIndex': userBorrowCumulativeIndex,
        'lastUpdateTimestamp': lastUpdateTimestamp,
        'originationFee': originationFee,
        'useAsCollateral': useAsCollateral
    }


def createUserReserveDataObject(reserveData: dict) -> 'UserReserveDataObject':
    return UserReserveDataObject(
        reserveAddress=reserveData['reserveAddress'],
        userAddress=reserveData['userAddress'],
        principalBorrowBalance=reserveData['principalBorrowBalance'],
        userBorrowCumulativeIndex=reserveData['userBorrowCumulativeIndex'],
        lastUpdateTimestamp=reserveData['lastUpdateTimestamp'],
        originationFee=reserveData['originationFee'],
        useAsCollateral=reserveData['useAsCollateral']
    )


class UserReserveDataObject(object):

    def __init__(self, **kwargs) -> None:
        self.reserveAddress = kwargs.get('reserveAddress')
        self.userAddress = kwargs.get('userAddress')
        self.principalBorrowBalance = kwargs.get('principalBorrowBalance')
        self.userBorrowCumulativeIndex = kwargs.get('userBorrowCumulativeIndex')
        self.lastUpdateTimestamp = kwargs.get('lastUpdateTimestamp')
        self.originationFee = kwargs.get('originationFee')
        self.useAsCollateral = kwargs.get('useAsCollateral')
