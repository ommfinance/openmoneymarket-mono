from iconservice import *
from .utils.checks import *

TAG = 'Snapshot'

DAY_IN_MICROSECONDS = 86400 * 10**6


class UserSnapshotData(TypedDict):
    principalOTokenBalance: int
    principalBorrowBalance: int
    userLiquidityCumulativeIndex: int
    userBorrowCumulativeIndex: int


class ReserveSnapshotData(TypedDict):
    liquidityRate: int
    borrowRate: int
    liquidityCumulativeIndex: int
    borrowCumulativeIndex: int
    lastUpdateTimestamp: int
    price: int
    

class Snapshot(IconScoreBase):

    USER_DATA = 'userData'
    RESERVE_DATA = 'reserveData'
    TIMESTAMP_AT_START = 'timestampAtStart'
    ADMIN = 'admin'
    GOVERNANCE = 'governance'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._userData = DictDB(self.USER_DATA, db, value_type=int, depth=4)
        self._reserveData = DictDB(self.RESERVE_DATA, db, value_type=int, depth=3)
        self._timestampAtStart = VarDB(self.TIMESTAMP_AT_START, db, value_type=int)
        self._admin = VarDB(self.ADMIN, db, value_type=Address)
        self._governance = VarDB(self.GOVERNANCE, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "OmmSnapshotManager"  

    @only_governance
    @external
    def setStartTimestamp(self, _timestamp: int):
        self._timestampAtStart.set(_timestamp)

    @external(readonly=True)
    def getStartTimestamp(self) -> Address:
        return self._timestampAtStart.get()

    @only_owner
    @external
    def setAdmin(self, _address: Address):
        self._admin.set(_address)

    @external(readonly=True)
    def getAdmin(self) -> Address:
        return self._admin.get()

    @only_owner
    @external
    def setGovernance(self, _address: Address):
        self._governance.set(_address)

    @external(readonly=True)
    def getGovernance(self) -> Address:
        return self._governance.get()

    @external(readonly=True)
    def userDataAt(self, _user: Address, _reserve: Address, _day: int) -> dict:
        if _day < 0:
            revert(f'IRC2Snapshot: day must be equal to or greater then Zero')
        userReserve = self._userData[_user][_reserve]
        low = 0
        high = userReserve['length'][0]

        while low < high:
            mid = (low + high) // 2
            if userReserve['ids'][mid] > _day:
                high = mid
            else:
                low = mid + 1

        keys = (
            "principalOTokenBalance",
            "principalBorrowBalance",
            "userLiquidityCumulativeIndex",
            "userBorrowCumulativeIndex"
        )

        if userReserve['ids'][0] == _day:
            response = {key: userReserve[key][0] for key in keys}
        elif low == 0:
            response = {
                keys[0]: 0,
                keys[1]: 0,
                keys[2]: 10 ** 18,
                keys[3]: 10 ** 18
            }
        else:
            response = {key: userReserve[key][low - 1] for key in keys}

        return response

    @external(readonly=True)
    def reserveDataAt(self, _reserve: Address, _day: int) -> dict:
        if _day < 0:
            revert(f'IRC2Snapshot: day must be equal to or greater then Zero')
        reserveData = self._reserveData[_reserve]
        low = 0
        high = reserveData['length'][0]

        while low < high:
            mid = (low + high) // 2
            if reserveData['ids'][mid] > _day:
                high = mid
            else:
                low = mid + 1

        keys = (
            "liquidityRate",
            "borrowRate",
            "liquidityCumulativeIndex",
            "borrowCumulativeIndex",
            "lastUpdateTimestamp",
            "price"
        )

        if reserveData['ids'][0] == _day:
            response = {key: reserveData[key][0] for key in keys}
        elif low == 0:
            response = {
                keys[0]: 0,
                keys[1]: 0,
                keys[2]: 10 ** 18,
                keys[3]: 10 ** 18,
                keys[4]: reserveData[keys[4]][0],
                keys[5]: reserveData[keys[5]][0]
            }
        else:
            response = {key: reserveData[key][low - 1] for key in keys}

        return response

    @only_admin
    @external
    def updateUserSnapshot(self, _user: Address, _reserve: Address, _userData: UserSnapshotData) -> None:
        currentDay = self._getDay()
        userReserve = self._userData[_user][_reserve]
        length = userReserve['length'][0]

        keys = (
            "principalOTokenBalance",
            "principalBorrowBalance",
            "userLiquidityCumulativeIndex",
            "userBorrowCumulativeIndex"
        )

        if length == 0:
            for key in keys:
                userReserve[key][length] = _userData[key]
            userReserve['length'][0] += 1
            return
        else:
            lastDay = userReserve['ids'][length - 1]

        if lastDay < currentDay:
            userReserve['ids'][length] = currentDay
            for key in keys:
                userReserve[key][length] = _userData[key]
            userReserve['length'][0] += 1
        else:
            for key in keys:
                userReserve[key][length - 1] = _userData[key]

    @only_admin
    @external
    def updateReserveSnapshot(self, _reserve: Address, _reserveData: ReserveSnapshotData) -> None:
        currentDay = self._getDay()
        reserveData = self._reserveData[_reserve]
        length = reserveData['length'][0]

        keys = (
            "liquidityRate",
            "borrowRate",
            "liquidityCumulativeIndex",
            "borrowCumulativeIndex",
            "lastUpdateTimestamp",
        )

        if length == 0:
            for key in keys:
                reserveData[key][length] = _reserveData[key]
            reserveData['price'][length] = _reserveData['price']
            reserveData['length'][0] += 1
            return
        else:
            lastDay = reserveData['ids'][length - 1]

        if lastDay < currentDay:
            reserveData['ids'][length] = currentDay
            for key in keys:
                reserveData[key][length] = _reserveData[key]
            reserveData['price'][length] = _reserveData['price']
            reserveData['length'][0] += 1
        else:
            for key in keys:
                reserveData[key][length - 1] = _reserveData[key]
            # TODO check why length is not "length - 1"
            reserveData['price'][length] = _reserveData['price']

    @external(readonly=True)
    def _getDay(self) -> int:
        return (self.now() - self._timestampAtStart.get()) // DAY_IN_MICROSECONDS

    @external(readonly=True)
    def getStartTimestamp(self) -> int:
        return self._timestampAtStart.get()
