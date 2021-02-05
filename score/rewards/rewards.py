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

# An interface to Worker Token
class WorkerTokenInterface(InterfaceScore):
    @interface
    def getWallets(self) -> list:
        pass

# An interface to LendingPoolCore
class CoreInterface(InterfaceScore):
    @interface
    def getReserves(self) -> list:
        pass

# An interface to Snapshot
class SnapshotInterface(InterfaceScore):
    @interface
    def userDataAt(self, _user: Address, _reserve: Address, _day: int) -> dict:
        pass

    @interface
    def reserveDataAt(self, _reserve: Address, _day: int) -> dict:
        pass

    @interface
    def getStartTimestamp(self) -> int:
        pass

class TokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass


class DataSourceInterface(InterfaceScore):
    @interface
    def precompute(self, _snapshot_id: int, batch_size: int) -> str:
        pass

    @interface
    def getTotalValue(self, _snapshot_id: int) -> int:
        pass

    @interface
    def getDataBatch(self, _name: str, _snapshot_id: int, _limit: int, _offset: int = 0) -> dict:
        pass

class Rewards(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._day = VarDB('day', db, value_type = int)
        self._tokenValue = DictDB('tokenValue', db, value_type = int)
        self._lendingPoolAddress = VarDB('lendingPoolAddress', db, value_type = Address)
        self._ommTokenAddress = VarDB('ommTokenAddress', db, value_type = Address)
        self._workerTokenAddress = VarDB('workerTokenAddress', db, value_type = Address)
        self._lendingPoolCoreAddress = VarDB('lendingPoolCoreAddress', db, value_type = Address)
        self._snapshotAddress = VarDB('snapshotAddress', db, value_type = Address)
        self._lpTokenAddress = VarDB('lpTokenAddress', db, value_type = Address)
        self._daoFundAddress = VarDB('daoFundAddress', db, value_type = Address)
        self._timestampAtStart = VarDB('timestampAtStart', db, value_type = int)

        self._precompute = DictDB('preCompute', db, value_type = bool)
        self._compIndex = DictDB('compIndex', db, value_type = int)
        self._amountMulApy = DictDB('amountMulApy', db, value_type = int)
        self._totalAmount = DictDB('totalAmount', db, value_type = int)
        self._distComplete =  DictDB('distComplete', db, value_type = bool)
        self._distIndex = DictDB('distIndex', db, value_type = int)
        self._tokenDistTracker = DictDB('tokenDistTracker', db, value_type = int)
        self._distPercentage = DictDB('distPercentage', db, value_type = int)
        self._offset = VarDB('offset', db, value_type = int)

        
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
    def setOmm(self, _val: Address):
        self._ommTokenAddress.set(_val)

    @external(readonly=True)
    def getOmm(self) -> Address:
        return self._ommTokenAddress.get()

    @external
    def setLendingPoolCore(self, _val: Address):
        self._lendingPoolCoreAddress.set(_val)

    @external(readonly=True)
    def getLendingPoolCore(self) -> Address:
        return self._lendingPoolCoreAddress.get()

    @external
    def setDaoFund(self, _val: Address):
        self._daoFundAddress.set(_val)

    @external(readonly=True)
    def getDaoFund(self) -> Address:
        return self._daoFundAddress.get()

    @external
    def setLpToken(self, _val: Address):
        self._lpTokenAddress.set(_val)

    @external(readonly=True)
    def getLpToken(self) -> Address:
        return self._lpTokenAddress.get()

    @external
    def setWorkerToken(self, _address: Address):
        self._workerTokenAddress.set(_address)

    @external(readonly=True)
    def getWorkerToken(self) -> Address:
        return self._workerTokenAddress.get()

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
        worker = self.create_interface_score(self._workerTokenAddress.get(), WorkerTokenInterface)
        snapshot = self.create_interface_score(self._snapshotAddress.get(), SnapshotInterface)
        if self._day.get() >= self._getDay():
            return
        if not self._precompute['deposit']:
            for user in pool.getDepositWallets(self._compIndex['deposit']):
                for reserve in core.getReserves():
                    deposit = self.depositBalance(reserve, user)
                    reserveData = snapshot.reserveDataAt(_reserve, self._day.get())
                    self._amountMulApy['deposit'][user][self._day.get()] += exaMul(deposit, reserveData['liquidityRate'])
                    self._totalAmount['deposit'] += exaMul(deposit, reserveData['liquidityRate'])
            self._compIndex['deposit'] += 1

            if len(pool.getDepositWallets(self._compIndex['deposit'])) < BATCH_SIZE:
                self._precompute['deposit'] = True
                self._compIndex['deposit'] = 0


        if not self._precompute['borrow']:
            for user in pool.getBorrowWallets(self._compIndex['borrow']):
                for reserve in core.getReserves():
                    borrow = self.borrowBalance(reserve, user)
                    reserveData = snapshot.reserveDataAt(_reserve, self._day.get())
                    self._amountMulApy['borrow'][user][self._day.get()] += exaMul(deposit, reserveData['borrowRate'])
                    self._totalAmount['borrow'] += exaMul(deposit, reserveData['borrowRate'])
            self._compIndex['borrow'] += 1

            if len(pool.getBorrowWallets(self._compIndex['borrow'])) < BATCH_SIZE:
                self._precompute['borrrow'] = True
                self._compIndex['borrow'] = 0

        if not self._distComplete['deposit']:
            for user in pool.getDepositWallets(self._distIndex['deposit']):
                tokenAmount = exaMul(exaDiv(self._amountMulApy['deposit'][user][self._day.get()], self._totalAmount['deposit']), self._tokenDistTracker['deposit'])
                self._tokenValue[user] += tokenAmount
                self._totalAmount['deposit'] -= self._amountMulApy['deposit'][user][self._day.get()]
                self._tokenDistTracker['deposit'] -= tokenAmount
            self._distIndex['deposit'] += 1

            if len(pool.getDepositWallets(self._distIndex['deposit'])) < BATCH_SIZE:
                self._distComplete['deposit'] = True
                self._distIndex['deposit'] = 0

        if not self._distComplete['borrow']:
            for user in pool.getDepositWallets(self._distIndex['borrow']):
                tokenAmount = exaMul(exaDiv(self._amountMulApy['borrow'][user][self._day.get()], self._totalAmount['borrow']), self._tokenDistTracker['borrow'])
                self._tokenValue[user] += tokenAmount
                self._totalAmount['borrow'] -= self._amountMulApy['borrow'][user][self._day.get()]
                self._tokenDistTracker['borrow'] -= tokenAmount
            self._distIndex['borrow'] += 1

            if len(pool.getDepositWallets(self._distIndex['borrow'])) < BATCH_SIZE:
                self._distComplete['borrow'] = True
                self._distIndex['borrow'] = 0

        if not self._distComplete['worker']:
            totalSupply = worker.totalSupply()
            for user in worker.getWallets():
                tokenAmount = exaMul(exaDiv(worker.balanceOf(user), totalSupply), self._tokenDistTracker['worker'])
                self._tokenValue[user] += tokenAmount
                totalSupply -= worker.balanceOf(user)
                self._tokenDistTracker['worker'] -= tokenAmount
            self._distComplete['worker'] = True

        if not self._distComplete['daoFund']:
            ommToken = self.create_interface_score(self._ommTokenAddress.get(), TokenInterface)
            ommToken.transfer(self._daoFundAddress.get(), self._tokenDistTracker['daoFund'])
            self._distComplete['daoFund'] = True

        if not self._precompute['lp']:
            data_source = self.create_interface_score(self._lpTokenAddress.get(), DataSourceInterface)
            self._totalAmount['lp'] = data_source.getTotalValue(self._day.get())
            self._precompute['lp'] = True
        
        if not self._distComplete['lp']:
            data_source = self.create_interface_score(self._lpTokenAddress.get(), DataSourceInterface)
            data_batch = data_source.getDataBatch(self._day.get(), self._offset.get(), BATCH_SIZE)
            self._offset.set(self._offset.get() + BATCH_SIZE)
            
            for address in data_batch:
                tokenAmount = exaMul(exaDiv(data_batch[address], self._totalAmount['lp']), self._tokenDistTracker['lp'])
                self._tokenValue[user] += tokenAmount
                self._totalAmount['lp'] -= data_batch[address]
                self._tokenDistTracker['lp'] -= tokenAmount

            if not data_batch:
                self._distComplete['lp'] = True
                self._offset.set(0)

        if self._distComplete['deposit'] and self._distComplete['borrow'] and self._distComplete['lp']:
            self._initialize()


    def _getDay(self) -> None:
        return (self.now() - self._timestampAtStart.get()) // DAY_IN_MICROSECONDS
    
    def _initialize(self) -> None:
        self._day.set(self._day.get() + 1)

        for value in ['deposit','borrow','lp']:
            self._precompute[value] = False
            self._distComplete[value] = False
            self._totalAmount[value] = 0
            self._tokenDistTracker[value] = exaMul(self.tokenDistributionPerDay(self._day.get()), self._distPercentage[value])
        
        for value in ['worker','daoFund']:
            self._tokenDistTracker[value] = exaMul(self.tokenDistributionPerDay(self._day.get()), self._distPercentage[value])

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


    