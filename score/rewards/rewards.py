from iconservice import *
from .Math import *

TAG = 'Rewards'

BATCH_SIZE = 100
DAY_IN_MICROSECONDS = 86400 * 10**6

# An interface to LendingPool
class LendingPoolInterface(InterfaceScore):
    @interface
    def getDepositWallets(self, _index: int) -> list:
        pass

    @interface
    def getBorrowWallets(self, _index: int) -> list:
        pass

# An interface to LendingPoolCore
class CoreInterface(InterfaceScore):
    @interface
    def getReserves(self) -> list:
        pass

# An interface to Snapshot
class SnapshotInterface(InterfaceScore):
    @interface
    def userDataAt(self, _user: Address, _reserve: Address _day: int) -> dict:
        pass

    @interface
    def reserveDataAt(self, _reserve: Address, _day: int) -> dict:
        pass

    @interface
    def getStartTimestamp(self) -> int:
        pass

class Rewards(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._day = VarDB('day', db, value_type = int)
        self._tokenValue = DictDB('tokenValue', db, value_type = int)
        self._lendingPoolAddress = VarDB('lendingPoolAddress', db, value_type = Address)
        self._lendingPoolCoreAddress = VarDB('lendingPoolCoreAddress', db, value_type = Address)
        self._snapshotAddress = VarDB('snapshotAddress', db, value_type = Address)
        self._depositComp = DictDB('depositComp', db, value_type = bool)
        self._depositCompIndex = VarDB('depositCompIndex', db, value_type = int)
        self._depositMulApy = DictDB('depositMulApy', db, value_type = int, depth = 2)
        self._totalDepositMulApy = DictDB('totalDepositMulApy', db, value_type = int)
        self._borrowComp = DictDB('borrowComp', db, value_type = bool)
        self._borrowCompIndex = VarDB('borrowCompIndex', db, value_type = int)
        self._borrowMulApy = DictDB('borrowMulApy', db, value_type = int, depth = 2)
        self._totalBorrowMulApy = DictDB('totalBorrowMulApy', db, value_type = int)
        self._depositDist = DictDB('depositDist', db, value_type = bool)
        self._depositDistIndex = VarDB('depositDistIndex', db, value_type = int)
        self._borrowDist = DictDB('borrowDist', db, value_type = bool)
        self._borrowDistIndex = VarDB('borrowDistIndex', db, value_type = int)
        self._workerDist = DictDB('workerDist', db, value_type = bool)
        self._workerDistIndex = VarDB('workerDistIndex', db, value_type = int)
        self._timestampAtStart = VarDB('timestampAtStart', db, value_type = int)
        
    def on_install(self) -> None:
        super().on_install()
      

    def on_update(self) -> None:
        super().on_update()

    @external
    def setStartTimestamp(self, _timestamp: int):
        self._lendingPoolAddress.set(_timestamp)

    @external(readonly=True)
    def getStartTimestamp(self) -> Address:
        return self._timestampAtStart.get()
    
    @external
    def setLendingPool(self, _val: Address):
        self._lendingPoolAddress.set(_val)

    @external(readonly=True)
    def getLendingPool(self) -> Address:
        return self._lendingPoolAddress.get()

    @external
    def setLendingPoolCore(self, _val: Address):
        self._lendingPoolCoreAddress.set(_val)

    @external(readonly=True)
    def getLendingPoolCore(self) -> Address:
        return self._lendingPoolCoreAddress.get()

    @external
    def setSnapshot(self, _val: Address):
        self._snapshotAddress.set(_val)

    @external(readonly=True)
    def getSnapshot(self) -> Address:
        return self._snapshotAddress.get()

    @external
    def distribute(self) -> None:
        pool = self.create_interface_score(self._lendingPoolAddress.get(), LendingPoolInterface)
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        snapshot = self.create_interface_score(self._snapshotAddress.get(), SnapshotInterface)
        if self._day.get() >= self._getDay():
            return
        if not self._depositComp[self._day.get()]:
            for user in pool.getDepositWallets(self._depositCompIndex.get()):
                for reserve in core.getReserves()
                    deposit = self.depositBalance(reserve, user)
                    reserveData = snapshot.reserveDataAt(_reserve, self._day.get())
                    self._depositMulApy[user][self._day.get()] += exaMul(deposit, reserveData['liquidityRate'])
                    self._totalDepositMulApy[self._day.get()] += exaMul(deposit, reserveData['liquidityRate'])
            self._depositCompIndex.set(self._depositCompIndex.get() + 1)

            if len(pool.getDepositWallets(self._depositCompIndex.get())) < BATCH_SIZE:
                self._depositComp[self._day.get()] = True
                self._depositCompIndex.set(0)


        if not self._borrowComp[self._day.get()]:
            for user in pool.getBorrowWallets(self._borrowCompIndex.get()):
                for reserve in core.getReserves()
                    borrow = self.borrowBalance(reserve, user)
                    reserveData = snapshot.reserveDataAt(_reserve, self._day.get())
                    self._borrowMulApy[user][self._day.get()] += exaMul(deposit, reserveData['borrowRate'])
                    self._totalborrowMulApy[self._day.get()] += exaMul(deposit, reserveData['borrowRate'])
            self._borrowCompIndex.set(self._borrowCompIndex.get() + 1)

            if len(pool.getBorrowWallets(self._borrowCompIndex.get())) < BATCH_SIZE:
                self._borrowComp[self._day.get()] = True
                self._borrowCompIndex.set(0)

        if not self._depositDist[self._day.get()]:
            for user in pool.getDepositWallets(self._depositDistIndex.get()):
                self._tokenValue[user] += exaMul(exaDiv(self._depositMulApy[user][self._day.get()], self._totalDepositMulApy[self._day.get()]), self.tokenDistributionPerDay(self._day.get()))
            self._depositDistIndex.set(self._depositDistIndex.get() + 1)

            if len(pool.getDepositWallets(self._depositDistIndex.get())) < BATCH_SIZE:
                self._depositDist[self._day.get()] = True
                self._depositDistIndex.set(0)

        if not self._borrowDist[self._day.get()]:
            for user in pool.getBorrowWallets(self._borrowDistIndex.get()):
                self._tokenValue[user] += exaMul(exaDiv(self._borrowMulApy[user][self._day.get()], self._totalBorrowMulApy[self._day.get()]),self.tokenDistributionPerDay(self._day.get()))
            self._borrowDistIndex.set(self._borrowDistIndex.get() + 1)

            if len(pool.getBorrowWallets(self._borrowDistIndex.get())) < BATCH_SIZE:
                self._borrowDist[self._day.get()] = True
                self._borrowDistIndex.set(0)

        if not self._workerDist[self._day.get()]:
            for user in worker.getWallets(self._workerDistIndex.get()):
                self._tokenValue[user] += exaMul(exaDiv(worker.balanceOf(user), worker.totalSupply()), self.tokenDistributionPerDay(self._day.get()))
            self._workerDistIndex.set(self._workerDistIndex.get() + 1)

            if len(worker.getWallets(self._workerDistIndex.get())) < BATCH_SIZE:
                self._workerDist[self._day.get()] = True
                self._workerDistIndex.set(0) 

        if self._depositDist[self._day.get()] and self._borrowDist[self._day.get()] and self._workerDist[self._day.get()]:
            self._day.set(self._day.get() + 1)

    def _getDay(self) -> None:
        return (self.now() - self._timestampAtStart.get()) // DAY_IN_MICROSECONDS

   
    def depositBalance(self, _reserve: Address, _user: Address) -> int:
        snapshot = self.create_interface_score(self._snapshotAddress.get(), SnapshotInterface)
        userData = snapshot.userDataAt(_user, _reserve, self._day.get())
        balance = userData['principalOTokenBalance']
        if userData['userLiquidityCumulativeIndex'] == 0:
            return balance
        else:
            reserveData = snapshot.reserveDataAt(_reserve, self._day.get())
            interest = self.calculateLinearInterest(reserveData['liquidityRate'], reserveData['lastUpdateTimestamp'])
            cumulated = exaMul(interest, reserveData['liquidityCumulativeIndex'])
            balance = exaDiv(exaMul(balance, cumulated),
                             userData['userLiquidityCumulativeIndex'])
            return balance

    def borrowBalance(self, _reserve: Address, _user: Address) -> int:
        snapshot = self.create_interface_score(self._snapshotAddress.get(), SnapshotInterface)
        userData = snapshot.userDataAt(_user, _reserve, self._day.get())
        reserveData = snapshot.reserveDataAt(_reserve, self._day.get())
        if userData['principalBorrowBalance'] == 0:
            return 0

        cumulatedInterest = exaDiv(
            exaMul(self.calculateCompoundedInterest(reserveData['borrowRate'], reserveData['lastUpdateTimestamp']),
                   reserveData['borrowCumulativeIndex']), userData['userBorrowCumulativeIndex'])
        compoundedBalance = exaMul(userData['principalBorrowBalance'], cumulatedInterest)

        return compoundedBalance

   
    def calculateLinearInterest(self, _rate: int, _lastUpdateTimestamp: int) -> int:
        snapshot = self.create_interface_score(self._snapshotAddress.get(), SnapshotInterface)
        timeDifference = (snapshot.getStartTimestamp() + (self._day.get()+1) * TIMESTAMP - _lastUpdateTimestamp) // 10 ** 6
        timeDelta = exaDiv(timeDifference, SECONDS_PER_YEAR)
        return exaMul(_rate, timeDelta) + EXA
        
   
    def calculateCompoundedInterest(self, _rate: int, _lastUpdateTimestamp: int) -> int:
        snapshot = self.create_interface_score(self._snapshotAddress.get(), SnapshotInterface)
        timeDifference = (snapshot.getStartTimestamp() + (self._day.get()+1) * TIMESTAMP - _lastUpdateTimestamp) // 10 ** 6
        ratePerSecond = _rate // SECONDS_PER_YEAR
        return exaPow((ratePerSecond + EXA), timeDifference)

    def tokenDistributionPerDay(self, _day: int) -> int:
        if _day < 30:
            return 10**24
        elif _day < 365:
            return 4 * 10**23
        elif _day < 730:
            return 3 * 10**23
        elif _day < 1095:
            return 2 * 10**23
        elif _day < 1460:
            return 10**23
        else: 
            index = _day // 365 - 3
            return (97**index * (10**23)) // (100**index)


    