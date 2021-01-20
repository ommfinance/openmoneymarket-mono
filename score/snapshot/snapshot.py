from iconservice import *

TAG = 'Snapshot'

class UserData(TypedDict):
    principalOTokenBalance: int
    principalBorrowBalance: int
    userLiquidityCumulativeIndex: int
    userBorrowCumulativeIndex: int

class ReserveData(TypedDict):
    liquidityRate: int
    borrowRate: int
    liquidityCumulativeIndex: int
    borrowCumulativeIndex: int
    lastUpdateTimestamp: int
    


class Snapshot(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._userData = DictDB("userData", db, value_type = int, depth = 3)
        self._reserveData = DictDB("reserveData", db, value_type = int, depth = 2)
        self._blockHeightAtStart = VarDB('blockHeightAtStart', db, value_type = int)
        self._timestampAtStart = VarDB('timestampAtStart', db, value_type = int)


    def on_install(self) -> None:
        super().on_install()
        self._blockHeightAtStart.set(self.block.height)
        self._timestampAtStart.set(self.now())

    def on_update(self) -> None:
        super().on_update()
    
    @external(readonly=True)
    def hello(self) -> str:
        Logger.debug(f'Hello, world!', TAG)
        return "Hello"

    @external(readonly=True)
	def userDataAt(self, _user: Address, _reserve: Address _day: int) -> dict:
		if _snapshot_id < 0:
			revert(f'IRC2Snapshot: snapshot id is equal to or greater then Zero')
		low = 0
		high = self._userData[_user]['length'][0]
		
		while (low < high):
			mid = (low + high) // 2
			if self._userData[_user]['ids'][mid] > _day:
				high = mid
			else:
				low = mid + 1 
		if self._userData[_user]['ids'][0] ==  _day:
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
		if _snapshot_id < 0:
			revert(f'IRC2Snapshot: snapshot id is equal to or greater then Zero')
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
                'lastUpdateTimestamp' : self._reserveData[_reserve]['lastUpdateTimestamp'][0]
            }

		elif low == 0:
			response = {
                'liquidityRate' : 0,
                'borrowRate' : 0,
                'liquidityCumulativeIndex' : 10**18,
                'borrowCumulativeIndex' : 10**18,
                'lastUpdateTimestamp' : self._reserveData[_reserve]['lastUpdateTimestamp'][0]
            }
		else:
			response = {
                'liquidityRate' : self._reserveData[_reserve]['liquidityRate'][low - 1],
                'borrowRate' : self._reserveData[_reserve]['borrowRate'][low - 1],
                'liquidityCumulativeIndex' : self._reserveData[_reserve]['liquidityCumulativeIndex'][low - 1],
                'borrowCumulativeIndex' : self._reserveData[_reserve]['borrowCumulativeIndex'][low - 1],
                'lastUpdateTimestamp' : self._reserveData[_reserve]['lastUpdateTimestamp'][low - 1]
            }

        return response

    @external
    def updateUserSnapshot(self, _user: Address, _reserve: Address, _userData: UserData) -> None:
		currentDay = self._getDay()
		length = self._userData[_user][_reserve]['length'][0]
		if length == 0:
			self._userData[_user][_reserve]['principalOToken'][length] = _userData['principalOToken']
            self._userData[_user][_reserve]['principalBorrowBalance'][length] = _userData['principalBorrowBalance']
            self._userData[_user][_reserve]['userLiquidityCumulativeIndex'][length] = _userData['userLiquidityCumulativeIndex']
            self._userData[_user][_reserve]['userBorrowCumulativeIndex'][length] = _userData['userBorrowCumulativeIndex']
			self._userData[_user][_reserve]['length'][0] += 1 
			return
		else:
			lastDay = self._userData[_user][_reserve]['ids'][length - 1]

		if lastDay< currentDay :
			self._userData[_user][_reserve]['ids'][length] = currentDay 
			self._userData[_user][_reserve]['principalOToken'][length] = _userData['principalOToken']
            self._userData[_user][_reserve]['principalBorrowBalance'][length] = _userData['principalBorrowBalance']
            self._userData[_user][_reserve]['userLiquidityCumulativeIndex'][length] = _userData['userLiquidityCumulativeIndex']
            self._userData[_user][_reserve]['userBorrowCumulativeIndex'][length] = _userData['userBorrowCumulativeIndex']
			self._userData[_user][_reserve]['length'][0] += 1 
			
		else:
			self._userData[_user][_reserve]['principalOToken'][length - 1] = _userData['principalOToken']
            self._userData[_user][_reserve]['principalBorrowBalance'][length - 1] = _userData['principalBorrowBalance']
            self._userData[_user][_reserve]['userLiquidityCumulativeIndex'][length - 1] = _userData['userLiquidityCumulativeIndex']
            self._userData[_user][_reserve]['userBorrowCumulativeIndex'][length - 1] = _userData['userBorrowCumulativeIndex']

    @external
    def updateReserveSnapshot(self, _reserve: Address, _reserveData: ReserveData) -> None:
		currentDay = self._getDay()
		length = self._reserveData[_reserve]['length'][0]
		if length == 0:
			self._reserveData[_reserve]['liquidityRate'][length] = _reserveData['liquidityRate']
            self._reserveData[_reserve]['borrowRate'][length] = _reserveData['borrowRate']
            self._reserveData[_reserve]['liquidityCumulativeIndex'][length] = _reserveData['liquidityCumulativeIndex']
            self._reserveData[_reserve]['borrowCumulativeIndex'][length] = _reserveData['borrowCumulativeIndex']
            self._reserveData[_reserve]['lastUpdateTimestamp'][length] = _reserveData['lastUpdateTimestamp']
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
			self._reserveData[_reserve]['length'][0] += 1  
			
		else:
			self._reserveData[_reserve]['liquidityRate'][length - 1] = _reserveData['liquidityRate']
            self._reserveData[_reserve]['borrowRate'][length - 1] = _reserveData['borrowRate']
            self._reserveData[_reserve]['liquidityCumulativeIndex'][length - 1] = _reserveData['liquidityCumulativeIndex']
            self._reserveData[_reserve]['borrowCumulativeIndex'][length - 1] = _reserveData['borrowCumulativeIndex']
            self._reserveData[_reserve]['lastUpdateTimestamp'][length - 1] = _reserveData['lastUpdateTimestamp']

    def _getDay(self) -> None:
        return (self.block.height - self._blockHeightAtStart.get()) // TERM

    @external(readonly = True):
    def getStartTimestamp(self) -> int:
        self._timestampAtStart.get()