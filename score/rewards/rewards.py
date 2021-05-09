from iconservice import *
from .Math import *
from .utils.checks import *

TAG = 'Rewards'

BATCH_SIZE = 100
DAY_IN_MICROSECONDS = 86400 * 10 ** 6


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

    @interface
    def totalSupply(self) -> int:
        pass

    @interface
    def balanceOf(self, _owner: Address) -> int:
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


class TokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

    @interface
    def mint(self, _amount: int):
        pass


class DataSourceInterface(InterfaceScore):
    @interface
    def precompute(self, _snapshot_id: int, batch_size: int) -> str:
        pass

    @interface
    def getTotalValue(self, _name: str, _snapshot_id: int) -> int:
        pass

    @interface
    def getDataBatch(self, _name: str, _snapshot_id: int, _limit: int, _offset: int = 0) -> dict:
        pass


class Rewards(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._day = VarDB('day', db, value_type=int)
        self._tokenValue = DictDB('tokenValue', db, value_type=int, depth=2)
        self._lendingPoolAddress = VarDB('lendingPoolAddress', db, value_type=Address)
        self._ommTokenAddress = VarDB('ommTokenAddress', db, value_type=Address)
        self._workerTokenAddress = VarDB('workerTokenAddress', db, value_type=Address)
        self._lendingPoolCoreAddress = VarDB('lendingPoolCoreAddress', db, value_type=Address)
        self._snapshotAddress = VarDB('snapshotAddress', db, value_type=Address)
        self._lpTokenAddress = VarDB('lpTokenAddress', db, value_type=Address)
        self._daoFundAddress = VarDB('daoFundAddress', db, value_type=Address)
        self._timestampAtStart = VarDB('timestampAtStart', db, value_type=int)
        self._recipients = ArrayDB('recipients', db, value_type=str)

        self._precompute = DictDB('preCompute', db, value_type=bool)
        self._compIndex = DictDB('compIndex', db, value_type=int)
        self._amountMulApy = DictDB('amountMulApy', db, value_type=int, depth=3)
        self._totalAmount = DictDB('totalAmount', db, value_type=int)
        self._distComplete = DictDB('distComplete', db, value_type=bool)
        self._distIndex = DictDB('distIndex', db, value_type=int)
        self._tokenDistTracker = DictDB('tokenDistTracker', db, value_type=int)
        self._distPercentage = DictDB('distPercentage', db, value_type=int)
        self._offset = DictDB('offset', db, value_type=int)
        self._admin = VarDB('admin', db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()
        self._recipients.put('deposit')
        self._recipients.put('borrow')
        self._recipients.put('worker')
        self._recipients.put('ommICX')
        self._recipients.put('ommUSDb')
        self._recipients.put('daoFund')
        self._distComplete['daoFund'] = True

    def on_update(self) -> None:
        super().on_update()
        self._distComplete['daoFund'] = True

    @eventlog(indexed=2)
    def Distribution(self, _recipient: str, _user: Address, _value: int):
        pass

    @eventlog(indexed=1)
    def State(self, _state: str):
        pass

    @external(readonly=True)
    def name(self) -> str:
        return "OmmRewardsManager"

    @only_owner
    @external
    def setDistPercentage(self, _deposit: int, _borrow: int, _ommICX: int, _ommUSDb: int, _worker: int, _daoFund: int):
        if (_deposit + _borrow + _ommICX + _ommUSDb + _worker + _daoFund) != EXA:
            revert(f"Sum of distribution percentage doesn't match to 100")
        self._distPercentage['deposit'] = _deposit
        self._distPercentage['borrow'] = _borrow
        self._distPercentage['ommICX'] = _ommICX
        self._distPercentage['ommUSDb'] = _ommUSDb
        self._distPercentage['worker'] = _worker
        self._distPercentage['daoFund'] = _daoFund

    @only_owner
    @external
    def setRecipients(self, _recipient: str):
        if _recipient not in self._recipients:
            self._recipients.put(_recipient)

    @external(readonly=True)
    def getRecipients(self) -> list:
        return [item for item in self._recipients]

    @external(readonly=True)
    def getDistPercentage(self) -> dict:
        return {
            recipient: self._distPercentage[recipient]
            for recipient in self._recipients
        }

    @only_admin
    @external
    def setStartTimestamp(self, _timestamp: int):
        self._timestampAtStart.set(_timestamp)

    @external(readonly=True)
    def getStartTimestamp(self) -> int:
        return self._timestampAtStart.get()

    @only_owner
    @external
    def setLendingPool(self, _address: Address):
        self._lendingPoolAddress.set(_address)

    @external(readonly=True)
    def getLendingPool(self) -> Address:
        return self._lendingPoolAddress.get()

    @only_owner
    @external
    def setOmm(self, _address: Address):
        self._ommTokenAddress.set(_address)

    @external(readonly=True)
    def getOmm(self) -> Address:
        return self._ommTokenAddress.get()

    @only_owner
    @external
    def setAdmin(self, _address: Address):
        self._admin.set(_address)

    @external(readonly=True)
    def getAdmin(self) -> Address:
        return self._admin.get()

    @only_owner
    @external
    def setLendingPoolCore(self, _address: Address):
        self._lendingPoolCoreAddress.set(_address)

    @external(readonly=True)
    def getLendingPoolCore(self) -> Address:
        return self._lendingPoolCoreAddress.get()

    @only_owner
    @external
    def setDaoFund(self, _address: Address):
        self._daoFundAddress.set(_address)

    @external(readonly=True)
    def getDaoFund(self) -> Address:
        return self._daoFundAddress.get()

    @only_owner
    @external
    def setLpToken(self, _address: Address):
        self._lpTokenAddress.set(_address)

    @external(readonly=True)
    def getLpToken(self) -> Address:
        return self._lpTokenAddress.get()

    @only_owner
    @external
    def setWorkerToken(self, _address: Address):
        self._workerTokenAddress.set(_address)

    @external(readonly=True)
    def getWorkerToken(self) -> Address:
        return self._workerTokenAddress.get()

    @only_owner
    @external
    def setSnapshot(self, _address: Address):
        self._snapshotAddress.set(_address)

    @external(readonly=True)
    def getSnapshot(self) -> Address:
        return self._snapshotAddress.get()

    def _check(self, _recipient: str) -> bool:
        tokenDistTracker = self._tokenDistTracker[_recipient]
        if not self._totalAmount[_recipient] and tokenDistTracker:
            ommToken = self.create_interface_score(self._ommTokenAddress.get(), TokenInterface)
            ommToken.transfer(self._daoFundAddress.get(), tokenDistTracker)
            self._distComplete[_recipient] = True
            self._tokenDistTracker[_recipient] = 0
            return False

        return True

    @external
    def distribute(self) -> None:
        pool = self.create_interface_score(self._lendingPoolAddress.get(), LendingPoolInterface)
        core = self.create_interface_score(self._lendingPoolCoreAddress.get(), CoreInterface)
        worker = self.create_interface_score(self._workerTokenAddress.get(), WorkerTokenInterface)
        snapshot = self.create_interface_score(self._snapshotAddress.get(), SnapshotInterface)
        ommToken = self.create_interface_score(self._ommTokenAddress.get(), TokenInterface)
        day: int = self._day.get()
        if day >= self._getDay():
            return

        if self._distComplete['daoFund']:
            self._initialize()
            day = self._day.get()

        if not self._precompute['deposit']:
            self.State("precompute deposit")
            totalAmount = 0
            depositWalletList = pool.getDepositWallets(self._compIndex['deposit'])
            for user in depositWalletList:
                amountMulApy = 0
                for reserve in core.getReserves():
                    deposit = self._depositBalance(reserve, user)
                    reserveData = snapshot.reserveDataAt(reserve, day)
                    deposit = exaMul(deposit, reserveData['price'])
                    amountMulApy += exaMul(deposit, reserveData['liquidityRate'])
                    totalAmount += exaMul(deposit, reserveData['liquidityRate'])

                self._amountMulApy['deposit'][user][day] += amountMulApy

            self._totalAmount['deposit'] += totalAmount

            if len(depositWalletList) < BATCH_SIZE:
                self._precompute['deposit'] = True
                self._compIndex['deposit'] = 0
            else:
                self._compIndex['deposit'] += 1

        elif not self._distComplete['deposit'] and self._check('deposit'):
            self.State("distribute deposit")
            totalAmount = self._totalAmount['deposit']
            tokenDistTracker = self._tokenDistTracker['deposit']
            distIndexDeposit: int = self._distIndex['deposit']
            depositWalletList = pool.getDepositWallets(distIndexDeposit)

            for user in depositWalletList:
                if tokenDistTracker <= 0:
                    break
                tokenAmount = exaMul(exaDiv(self._amountMulApy['deposit'][user][day], totalAmount),
                                     tokenDistTracker)
                self._tokenValue[user]['deposit'] += tokenAmount
                self.Distribution("deposit", user, tokenAmount)
                totalAmount -= self._amountMulApy['deposit'][user][day]
                tokenDistTracker -= tokenAmount

            self._totalAmount['deposit'] = totalAmount
            self._tokenDistTracker['deposit'] = tokenDistTracker

            if len(depositWalletList) < BATCH_SIZE:
                self._distComplete['deposit'] = True
                self._distIndex['deposit'] = 0
            else:
                self._distIndex['deposit'] = distIndexDeposit + 1

        elif not self._precompute['borrow']:
            self.State("precompute borrow")
            totalAmount = 0
            compIndexBorrow: int = self._compIndex['borrow']
            borrowWalletList = pool.getBorrowWallets(compIndexBorrow)
            for user in borrowWalletList:
                amountMulApy = 0
                for reserve in core.getReserves():
                    borrow = self._borrowBalance(reserve, user)
                    reserveData = snapshot.reserveDataAt(reserve, day)
                    borrow = exaMul(borrow, reserveData['price'])
                    amountMulApy += exaMul(borrow, reserveData['borrowRate'])
                    totalAmount += exaMul(borrow, reserveData['borrowRate'])

                self._amountMulApy['borrow'][user][day] += amountMulApy

            self._totalAmount['borrow'] += totalAmount

            if len(borrowWalletList) < BATCH_SIZE:
                self._precompute['borrow'] = True
                self._compIndex['borrow'] = 0
            else:
                self._compIndex['borrow'] = compIndexBorrow + 1

        elif not self._distComplete['borrow'] and self._check('borrow'):
            self.State("distribute borrow")
            totalAmount = self._totalAmount['borrow']
            tokenDistTracker = self._tokenDistTracker['borrow']
            distIndexBorrow: int = self._distIndex['borrow']
            borrowWalletList = pool.getBorrowWallets(distIndexBorrow)

            for user in borrowWalletList:
                if tokenDistTracker <= 0:
                    break
                tokenAmount = exaMul(exaDiv(self._amountMulApy['borrow'][user][day], totalAmount),
                                     tokenDistTracker)
                self._tokenValue[user]['borrow'] += tokenAmount
                self.Distribution("borrow", user, tokenAmount)
                totalAmount -= self._amountMulApy['borrow'][user][day]
                tokenDistTracker -= tokenAmount

            self._totalAmount['borrow'] = totalAmount
            self._tokenDistTracker['borrow'] = tokenDistTracker

            if len(borrowWalletList) < BATCH_SIZE:
                self._distComplete['borrow'] = True
                self._distIndex['borrow'] = 0
            else:
                self._distIndex['borrow'] = distIndexBorrow + 1

        elif not self._precompute['ommICX']:
            self.State("precompute ommICX")
            data_source = self.create_interface_score(self._lpTokenAddress.get(), DataSourceInterface)
            self._totalAmount['ommICX'] = data_source.getTotalValue("OMMSICX", day)
            self._precompute['ommICX'] = True

        elif not self._distComplete['ommICX'] and self._check('ommICX'):
            self.State("distribute ommICX")
            data_source = self.create_interface_score(self._lpTokenAddress.get(), DataSourceInterface)
            data_batch = data_source.getDataBatch("OMMSICX", day, BATCH_SIZE, self._offset["OMMSICX"])
            self._offset["OMMSICX"] += BATCH_SIZE

            if data_batch:
                totalAmount = self._totalAmount['ommICX']
                tokenDistTracker = self._tokenDistTracker['ommICX']

                for user in data_batch:
                    if tokenDistTracker <= 0:
                        break
                    tokenAmount = exaMul(exaDiv(data_batch[user], totalAmount), tokenDistTracker)
                    self._tokenValue[Address.from_string(user)]['ommICX'] += tokenAmount
                    self.Distribution("ommICX", Address.from_string(user), tokenAmount)
                    totalAmount -= data_batch[user]
                    tokenDistTracker -= tokenAmount

                self._totalAmount['ommICX'] = totalAmount
                self._tokenDistTracker['ommICX'] = tokenDistTracker

            else:
                self._distComplete['ommICX'] = True
                self._offset["OMMSICX"] = 0

        elif not self._precompute['ommUSDb']:
            self.State("precompute ommUSDb")
            data_source = self.create_interface_score(self._lpTokenAddress.get(), DataSourceInterface)
            self._totalAmount['ommUSDb'] = data_source.getTotalValue("OMMIUSDC", day)
            self._totalAmount['ommUSDb'] += data_source.getTotalValue("OMMUSDB", day)
            self._precompute['ommUSDb'] = True

        elif not self._distComplete['ommUSDb'] and self._check('ommUSDb'):
            self.State("distribute ommUSDb")
            data_source = self.create_interface_score(self._lpTokenAddress.get(), DataSourceInterface)
            data_batch1 = data_source.getDataBatch("OMMIUSDC", day, BATCH_SIZE, self._offset["OMMUSDB"])
            data_batch2 = data_source.getDataBatch("OMMUSDB", day, BATCH_SIZE, self._offset["OMMUSDB"])
            self._offset["OMMUSDB"] += BATCH_SIZE

            if data_batch1 or data_batch2:
                totalAmount = self._totalAmount['ommUSDb']
                tokenDistTracker = self._tokenDistTracker['ommUSDb']

                for user in data_batch1:
                    if tokenDistTracker <= 0:
                        break
                    tokenAmount = exaMul(exaDiv(data_batch1[user], totalAmount), tokenDistTracker)
                    self._tokenValue[Address.from_string(user)]['ommUSDb'] += tokenAmount
                    self.Distribution("ommIUSDC", Address.from_string(user), tokenAmount)
                    totalAmount -= data_batch1[user]
                    tokenDistTracker -= tokenAmount

                for user in data_batch2:
                    if tokenDistTracker <= 0:
                        break
                    tokenAmount = exaMul(exaDiv(data_batch2[user], totalAmount), tokenDistTracker)
                    self._tokenValue[Address.from_string(user)]['ommUSDb'] += tokenAmount
                    self.Distribution("ommUSDb", Address.from_string(user), tokenAmount)
                    totalAmount -= data_batch2[user]
                    tokenDistTracker -= tokenAmount

                self._totalAmount['ommUSDb'] = totalAmount
                self._tokenDistTracker['ommUSDb'] = tokenDistTracker

            else:
                self._distComplete['ommUSDb'] = True
                self._offset["OMMUSDB"] = 0

        elif not self._distComplete['worker']:
            self.State("distribute worker")
            totalSupply = worker.totalSupply()
            tokenDistTracker = self._tokenDistTracker['worker']
            for user in worker.getWallets():
                if tokenDistTracker <= 0:
                    break
                tokenAmount = exaMul(exaDiv(worker.balanceOf(user), totalSupply), tokenDistTracker)
                self._tokenValue[user]['worker'] += tokenAmount
                self.Distribution("worker", user, tokenAmount)
                totalSupply -= worker.balanceOf(user)
                tokenDistTracker -= tokenAmount

            self._distComplete['worker'] = True

        elif not self._distComplete['daoFund']:
            self.State("distribute daoFund")
            daoFundAddress = self._daoFundAddress.get()
            tokenDistTrackerDaoFund: int = self._tokenDistTracker['daoFund']
            ommToken.transfer(daoFundAddress, tokenDistTrackerDaoFund)
            self._distComplete['daoFund'] = True
            self.Distribution("daoFund", daoFundAddress, tokenDistTrackerDaoFund)

    @external
    def claimRewards(self):
        total_token = 0
        for recipient in self._recipients:
            total_token += self._tokenValue[self.msg.sender][recipient]
            self._tokenValue[self.msg.sender][recipient] = 0

        if total_token:
            ommToken = self.create_interface_score(self._ommTokenAddress.get(), TokenInterface)
            ommToken.transfer(self.msg.sender, total_token)

    @external(readonly=True)
    def getRewards(self, _user: Address):
        response = {}
        ommRewards = 0
        liquidityRewards = 0
        total = 0
        recipientSet = {"deposit", "borrow", "daoFund", "worker"}
        for recipient in self._recipients:
            tokenAmount = self._tokenValue[_user][recipient]
            response[recipient] = tokenAmount
            if recipient in recipientSet:
                ommRewards += tokenAmount
            else:
                liquidityRewards += tokenAmount
            total += tokenAmount

        response['ommRewards'] = ommRewards
        response['liquidityRewards'] = liquidityRewards
        response['total'] = total

        return response

    @external(readonly=True)
    def _getDay(self) -> int:
        return (self.now() - self._timestampAtStart.get()) // DAY_IN_MICROSECONDS

    def _initialize(self) -> None:
        day: int = self._day.get()
        tokenDistributionPerDay: int = self.tokenDistributionPerDay(day)
        ommToken = self.create_interface_score(self._ommTokenAddress.get(), TokenInterface)
        ommToken.mint(tokenDistributionPerDay)

        for value in ('deposit', 'borrow', 'ommICX', 'ommUSDb'):
            self._precompute[value] = False
            self._totalAmount[value] = 0
            self._distComplete[value] = False
            self._tokenDistTracker[value] = exaMul(tokenDistributionPerDay, self._distPercentage[value])

        for value in ('worker', 'daoFund'):
            self._distComplete[value] = False
            self._tokenDistTracker[value] = exaMul(tokenDistributionPerDay, self._distPercentage[value])

        self._day.set(day + 1)

    def _depositBalance(self, _reserve: Address, _user: Address) -> int:
        day: int = self._day.get()
        snapshot = self.create_interface_score(self._snapshotAddress.get(), SnapshotInterface)
        userData = snapshot.userDataAt(_user, _reserve, day)
        balance = userData['principalOTokenBalance']

        if userData['userLiquidityCumulativeIndex'] != 0:
            reserveData = snapshot.reserveDataAt(_reserve, day)
            interest = self._calculateLinearInterest(reserveData['liquidityRate'], reserveData['lastUpdateTimestamp'])
            cumulated = exaMul(interest, reserveData['liquidityCumulativeIndex'])
            balance = exaDiv(exaMul(balance, cumulated), userData['userLiquidityCumulativeIndex'])

        return balance

    def _borrowBalance(self, _reserve: Address, _user: Address) -> int:
        day: int = self._day.get()
        snapshot = self.create_interface_score(self._snapshotAddress.get(), SnapshotInterface)
        userData = snapshot.userDataAt(_user, _reserve, day)
        reserveData = snapshot.reserveDataAt(_reserve, day)
        if userData['principalBorrowBalance'] == 0:
            return 0

        cumulatedInterest = exaDiv(
            exaMul(self._calculateCompoundedInterest(reserveData['borrowRate'], reserveData['lastUpdateTimestamp']),
                   reserveData['borrowCumulativeIndex']), userData['userBorrowCumulativeIndex'])
        compoundedBalance = exaMul(userData['principalBorrowBalance'], cumulatedInterest)

        return compoundedBalance

    def _calculateLinearInterest(self, _rate: int, _lastUpdateTimestamp: int) -> int:
        timeDifference = (self.getStartTimestamp() + (
                    self._day.get() + 1) * DAY_IN_MICROSECONDS - _lastUpdateTimestamp) // 10 ** 6
        timeDelta = exaDiv(timeDifference, SECONDS_PER_YEAR)
        return exaMul(_rate, timeDelta) + EXA

    def _calculateCompoundedInterest(self, _rate: int, _lastUpdateTimestamp: int) -> int:
        timeDifference = (self.getStartTimestamp() + (
                    self._day.get() + 1) * DAY_IN_MICROSECONDS - _lastUpdateTimestamp) // 10 ** 6
        ratePerSecond = _rate // SECONDS_PER_YEAR
        return exaPow((ratePerSecond + EXA), timeDifference)

    @external(readonly=True)
    def tokenDistributionPerDay(self, _day: int) -> int:
        DAYS_PER_YEAR = 365

        if _day < 30:
            return 10 ** 24
        elif _day < DAYS_PER_YEAR:
            return 4 * 10 ** 23
        elif _day < (DAYS_PER_YEAR * 2):
            return 3 * 10 ** 23
        elif _day < (DAYS_PER_YEAR * 3):
            return 2 * 10 ** 23
        elif _day < (DAYS_PER_YEAR * 4):
            return 10 ** 23
        else:
            index = _day // 365 - 4
            return ((103 ** index * 3 * (383 * 10 ** 24)) // DAYS_PER_YEAR) // (100 ** (index + 1))

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        pass
