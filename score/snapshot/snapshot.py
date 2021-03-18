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
        self._userData = DictDB(self.USER_DATA, db, value_type = int, depth = 4)
        self._reserveData = DictDB(self.RESERVE_DATA, db, value_type = int, depth = 3)
        self._timestampAtStart = VarDB(self.TIMESTAMP_AT_START, db, value_type = int)
        self._admin = VarDB(self.ADMIN, db, value_type = Address)
        self._governance = VarDB(self.GOVERNANCE, db , value_type = Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    
    @only_governance
    @external
    def setStartTimestamp(self, _timestamp: int):
        self._timestampAtStart.set(_timestamp)

    @external(readonly=True)
    def getStartTimestamp(self) -> int:
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
        response = {}
        if _day < 0:
            revert(f'IRC2Snapshot: day must be equal to or greater then Zero')
        low = 0
        high = self._userData[_user][_reserve]['length'][0]

        while (low < high):
            mid = (low + high) // 2
            if self._userData[_user][_reserve]['ids'][mid] > _day:
                high = mid
            else:
                low = mid + 1 
        if self._userData[_user][_reserve]['ids'][0] ==  _day:
            response = {
                'principalOTokenBalance' : self._userData[_user][_reserve]['principalOTokenBalance'][0],
                'principalBorrowBalance' : self._userData[_user][_reserve]['principalBorrowBalance'][0],
                'userLiquidityCumulativeIndex' : self._userData[_user][_reserve]['userLiquidityCumulativeIndex'][0],
                'userBorrowCumulativeIndex' : self._userData[_user][_reserve]['userBorrowCumulativeIndex'][0]
            }

        elif low == 0:
            response = {
                'principalOTokenBalance' : 0,
                'principalBorrowBalance' : 0,
                'userLiquidityCumulativeIndex' : 10**18,
                'userBorrowCumulativeIndex' : 10**18
            }
        else:
            response = {
                'principalOTokenBalance' : self._userData[_user][_reserve]['principalOTokenBalance'][low - 1],
                'principalBorrowBalance' : self._userData[_user][_reserve]['principalBorrowBalance'][low - 1],
                'userLiquidityCumulativeIndex' : self._userData[_user][_reserve]['userLiquidityCumulativeIndex'][low - 1],
                'userBorrowCumulativeIndex' : self._userData[_user][_reserve]['userBorrowCumulativeIndex'][low - 1]
            }

        return response

    @external(readonly=True)
    def reserveDataAt(self, _reserve: Address, _day: int) -> dict:
        if _day < 0:
            revert(f'IRC2Snapshot: day must be equal to or greater then Zero')
        low = 0
        high = self._reserveData[_reserve]['length'][0]

        while (low < high):
            mid = (low + high) // 2
            if self._reserveData[_reserve]['ids'][mid] > _day:
                high = mid
            else:
                low = mid + 1 
        if self._reserveData[_reserve]['ids'][0] ==  _day:
            response = {
                'liquidityRate' : self._reserveData[_reserve]['liquidityRate'][0],
                'borrowRate' : self._reserveData[_reserve]['borrowRate'][0],
                'liquidityCumulativeIndex' : self._reserveData[_reserve]['liquidityCumulativeIndex'][0],
                'borrowCumulativeIndex' : self._reserveData[_reserve]['borrowCumulativeIndex'][0],
                'lastUpdateTimestamp' : self._reserveData[_reserve]['lastUpdateTimestamp'][0],
                'price' : self._reserveData[_reserve]['price'][0]
            }

        elif low == 0:
            response = {
                'liquidityRate' : 0,
                'borrowRate' : 0,
                'liquidityCumulativeIndex' : 10**18,
                'borrowCumulativeIndex' : 10**18,
                'lastUpdateTimestamp' : self._reserveData[_reserve]['lastUpdateTimestamp'][0],
                'price' : self._reserveData[_reserve]['price'][0]
            }
        else:
            response = {
                'liquidityRate' : self._reserveData[_reserve]['liquidityRate'][low - 1],
                'borrowRate' : self._reserveData[_reserve]['borrowRate'][low - 1],
                'liquidityCumulativeIndex' : self._reserveData[_reserve]['liquidityCumulativeIndex'][low - 1],
                'borrowCumulativeIndex' : self._reserveData[_reserve]['borrowCumulativeIndex'][low - 1],
                'lastUpdateTimestamp' : self._reserveData[_reserve]['lastUpdateTimestamp'][low - 1],
                'price' : self._reserveData[_reserve]['price'][low - 1]
            }

        return response

    @only_admin
    @external
    def updateUserSnapshot(self,_user: Address, _reserve: Address, _userData: UserSnapshotData) -> None:
        currentDay = self._getDay()
        length = self._userData[_user][_reserve]['length'][0]
        if length == 0:
            self._userData[_user][_reserve]['principalOTokenBalance'][length] = _userData['principalOTokenBalance']
            self._userData[_user][_reserve]['principalBorrowBalance'][length] = _userData['principalBorrowBalance']
            self._userData[_user][_reserve]['userLiquidityCumulativeIndex'][length] = _userData['userLiquidityCumulativeIndex']
            self._userData[_user][_reserve]['userBorrowCumulativeIndex'][length] = _userData['userBorrowCumulativeIndex']
            self._userData[_user][_reserve]['length'][0] += 1 
            return
        else:
            lastDay = self._userData[_user][_reserve]['ids'][length - 1]

        if lastDay< currentDay :
            self._userData[_user][_reserve]['ids'][length] = currentDay 
            self._userData[_user][_reserve]['principalOTokenBalance'][length] = _userData['principalOTokenBalance']
            self._userData[_user][_reserve]['principalBorrowBalance'][length] = _userData['principalBorrowBalance']
            self._userData[_user][_reserve]['userLiquidityCumulativeIndex'][length] = _userData['userLiquidityCumulativeIndex']
            self._userData[_user][_reserve]['userBorrowCumulativeIndex'][length] = _userData['userBorrowCumulativeIndex']
            self._userData[_user][_reserve]['length'][0] += 1 
            
        else:
            self._userData[_user][_reserve]['principalOTokenBalance'][length - 1] = _userData['principalOTokenBalance']
            self._userData[_user][_reserve]['principalBorrowBalance'][length - 1] = _userData['principalBorrowBalance']
            self._userData[_user][_reserve]['userLiquidityCumulativeIndex'][length - 1] = _userData['userLiquidityCumulativeIndex']
            self._userData[_user][_reserve]['userBorrowCumulativeIndex'][length - 1] = _userData['userBorrowCumulativeIndex']

    @only_admin
    @external
    def updateReserveSnapshot(self, _reserve: Address, _reserveData: ReserveSnapshotData) -> None:
        currentDay = self._getDay()
        length = self._reserveData[_reserve]['length'][0]
        if length == 0:
            self._reserveData[_reserve]['liquidityRate'][length] = _reserveData['liquidityRate']
            self._reserveData[_reserve]['borrowRate'][length] = _reserveData['borrowRate']
            self._reserveData[_reserve]['liquidityCumulativeIndex'][length] = _reserveData['liquidityCumulativeIndex']
            self._reserveData[_reserve]['borrowCumulativeIndex'][length] = _reserveData['borrowCumulativeIndex']
            self._reserveData[_reserve]['lastUpdateTimestamp'][length] = _reserveData['lastUpdateTimestamp']
            self._reserveData[_reserve]['price'][length] = _reserveData['price']
            self._reserveData[_reserve]['length'][0] += 1 
            return
        else:
            lastDay = self._reserveData[_reserve]['ids'][length - 1]

        if lastDay< currentDay :
            self._reserveData[_reserve]['ids'][length] = currentDay 
            self._reserveData[_reserve]['liquidityRate'][length] = _reserveData['liquidityRate']
            self._reserveData[_reserve]['borrowRate'][length] = _reserveData['borrowRate']
            self._reserveData[_reserve]['liquidityCumulativeIndex'][length] = _reserveData['liquidityCumulativeIndex']
            self._reserveData[_reserve]['borrowCumulativeIndex'][length] = _reserveData['borrowCumulativeIndex']
            self._reserveData[_reserve]['lastUpdateTimestamp'][length] = _reserveData['lastUpdateTimestamp']
            self._reserveData[_reserve]['price'][length] = _reserveData['price']
            self._reserveData[_reserve]['length'][0] += 1  
            
        else:
            self._reserveData[_reserve]['liquidityRate'][length - 1] = _reserveData['liquidityRate']
            self._reserveData[_reserve]['borrowRate'][length - 1] = _reserveData['borrowRate']
            self._reserveData[_reserve]['liquidityCumulativeIndex'][length - 1] = _reserveData['liquidityCumulativeIndex']
            self._reserveData[_reserve]['borrowCumulativeIndex'][length - 1] = _reserveData['borrowCumulativeIndex']
            self._reserveData[_reserve]['lastUpdateTimestamp'][length - 1] = _reserveData['lastUpdateTimestamp']
            self._reserveData[_reserve]['price'][length] = _reserveData['price']

    @external(readonly = True)
    def _getDay(self) -> int:
        return (self.now() - self._timestampAtStart.get()) // DAY_IN_MICROSECONDS

