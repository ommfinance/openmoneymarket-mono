from .rewardDistribution import *
from .utils.checks import *

DAY_IN_MICROSECONDS = 86400 * 10 ** 6

TAG = 'RewardDistributionController'


class SupplyDetails(TypedDict):
    principalUserBalance: int
    principalTotalSupply: int


class DataProviderInterface(InterfaceScore):
    @interface
    def getAssetPrincipalSupply(self, _asset: Address, _user: Address) -> SupplyDetails:
        pass


class TokenInterface(InterfaceScore):
    @interface
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass

    @interface
    def mint(self, _amount: int):
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

    @interface
    def getReserveConfiguration(self, _reserve: Address) -> dict:
        pass


class DexInterface(InterfaceScore):
    @interface
    def balanceOfAt(self, _account: Address, _id: int, _day: int, _twa: bool = False) -> int:
        pass

    @interface
    def totalSupplyAt(self, _id: int, _day: int, _twa: bool = False) -> int:
        pass


class RewardDistributionController(RewardDistributionManager):
    USERS_UNCLAIMED_REWARDS = 'usersUnclaimedRewards'
    DATA_PROVIDER = 'dataProvider'
    OMM_TOKEN_ADDRESS = 'ommTokenAddress'
    DAY = 'day'
    TOKEN_VALUE = 'tokenValue'
    DEX = "dex"
    POOL_ID = "pool_id"
    REWARDS_BATCH_SIZE = "rewardsBatchSize"
    CLAIMED_BIT_MAP = "claimedBitMap"
    REWARDS_ACTIVATE = "rewardsActivate"

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._day = VarDB(self.DAY, db, value_type=int)
        self._tokenValue = DictDB(self.TOKEN_VALUE, db, value_type=int, depth=2)
        self._usersUnclaimedRewards = DictDB(self.USERS_UNCLAIMED_REWARDS, db, value_type=int)
        self._dataProviderAddress = VarDB(self.DATA_PROVIDER, db, value_type=Address)
        self._ommTokenAddress = VarDB(self.OMM_TOKEN_ADDRESS, db, value_type=Address)
        self._workerTokenAddress = VarDB('workerTokenAddress', db, value_type=Address)
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
        self._dex = VarDB(self.DEX, db, value_type=Address)
        self._pool_id = DictDB(self.POOL_ID, db, value_type=int)
        self._rewardsBatchSize = VarDB(self.REWARDS_BATCH_SIZE, db, value_type=int)
        self._rewardsActivate = VarDB(self.REWARDS_ACTIVATE, db, value_type=int)

    def on_install(self) -> None:
        super().on_install()
        self._recipients.put('dex')
        self._recipients.put('daoFund')
        self._distComplete['daoFund'] = True
        self._rewardsBatchSize.set(50)

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=2)
    def Distribution(self, _recipient: str, _user: Address, _value: int):
        pass

    @eventlog(indexed=1)
    def State(self, _state: str):
        pass

    @eventlog
    def RewardsAccrued(self, _user: Address, _rewards: int) -> None:
        pass

    @eventlog
    def RewardsClaimed(self, _user: Address, _rewards: int, _msg: str) -> None:
        pass

    @external(readonly=True)
    def name(self) -> str:
        return "RewardDistributionController"

    @external
    def setLendingPoolDataProvider(self, _address: Address):
        self._dataProviderAddress.set(_address)

    @external(readonly=True)
    def getLendingPoolDataProvider(self) -> Address:
        return self._dataProviderAddress.get()

    @external
    def setOmm(self, _address: Address):
        self._ommTokenAddress.set(_address)

    @external(readonly=True)
    def getOmm(self) -> Address:
        return self._ommTokenAddress.get()

    @only_owner
    @external
    def setDistPercentage(self, _ommICX: int, _dex: int, _worker: int, _daoFund: int):
        self._distPercentage['ommICX'] = _ommICX
        self._distPercentage['dex'] = _dex
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

    @only_owner
    @external
    def setBatchSize(self, _size: int):
        self._rewardsBatchSize.set(_size)

    @external(readonly=True)
    def getBatchSize(self) -> int:
        return self._rewardsBatchSize.get()

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
    def setAdmin(self, _address: Address):
        self._admin.set(_address)

    @external(readonly=True)
    def getAdmin(self) -> Address:
        return self._admin.get()

    @only_owner
    @external
    def setDaoFund(self, _address: Address):
        self._daoFundAddress.set(_address)

    @external(readonly=True)
    def getDaoFund(self) -> Address:
        return self._daoFundAddress.get()

    @only_owner
    @external
    def setDex(self, _address: Address):
        self._dex.set(_address)

    @external(readonly=True)
    def getDex(self) -> Address:
        return self._dex.get()

    @only_owner
    @external
    def setWorkerToken(self, _address: Address):
        self._workerTokenAddress.set(_address)

    @external(readonly=True)
    def getWorkerToken(self) -> Address:
        return self._workerTokenAddress.get()

    @external(readonly=True)
    def readValues(self, _recipient: str) -> dict:
        response = {"precompute": self._precompute[_recipient], "distComplete": self._distComplete[_recipient],
                    "totalAmount": self._totalAmount[_recipient],
                    "tokenDistTracker": self._tokenDistTracker[_recipient], "distIndex": self._distIndex[_recipient]}

        return response

    @external
    def handleAction(self, _user: Address, _userBalance: int, _totalSupply: int) -> None:
        accruedRewards = self._updateUserReserveInternal(_user, self.msg.sender, _userBalance, _totalSupply)
        if accruedRewards != 0:
            self._usersUnclaimedRewards[_user] += accruedRewards
            self.RewardsAccrued(_user, accruedRewards)

    @external(readonly=True)
    def getRewards(self, _user: Address) -> dict:
        unclaimedRewards = self._usersUnclaimedRewards[_user]
        dataProvider = self.create_interface_score(self.getLendingPoolDataProvider(), DataProviderInterface)

        userAssetList = []
        for asset in self._assets:
            supply = dataProvider.getAssetPrincipalSupply(asset, _user)
            userAssetDetails: UserAssetInput = {'asset': asset, 'userBalance': supply['principalUserBalance'],
                                                'totalBalance': supply['principalTotalSupply']}
            userAssetList.append(userAssetDetails)

        unclaimedRewards += self._getUnclaimedRewards(_user, userAssetList)

        response = {}
        ommRewards = unclaimedRewards
        liquidityRewards = 0
        total = unclaimedRewards
        recipientSet = {"daoFund", "worker"}
        for recipient in self._recipients:
            tokenAmount = self._tokenValue[_user][recipient]
            response[recipient] = tokenAmount
            if recipient in recipientSet:
                ommRewards += tokenAmount
            else:
                liquidityRewards += tokenAmount
            total += tokenAmount

        response['depositBorrowRewards'] = unclaimedRewards
        response['ommRewards'] = ommRewards
        response['liquidityRewards'] = liquidityRewards
        response['total'] = total

        return response

    @external
    def claimRewards(self) -> int:
        user = self.msg.sender
        unclaimedRewards = self._usersUnclaimedRewards[user]
        dataProvider = self.create_interface_score(self.getLendingPoolDataProvider(), DataProviderInterface)

        userAssetList = []
        for asset in self._assets:
            supply = dataProvider.getAssetPrincipalSupply(asset, user)
            userAssetDetails: UserAssetInput = {'asset': asset, 'userBalance': supply['principalUserBalance'],
                                                'totalBalance': supply['principalTotalSupply']}
            userAssetList.append(userAssetDetails)

        accruedRewards = self._claimRewards(user, userAssetList)
        if accruedRewards != 0:
            unclaimedRewards += accruedRewards
            self.RewardsAccrued(user, accruedRewards)

        if unclaimedRewards == 0:
            return 0

        self._usersUnclaimedRewards[user] = 0
        ommToken = self.create_interface_score(self._ommTokenAddress.get(), TokenInterface)
        ommToken.transfer(user, unclaimedRewards)

        self.RewardsClaimed(user, unclaimedRewards, 'borrowDepositRewards')

    @external
    def distribute(self) -> None:
        worker = self.create_interface_score(self._workerTokenAddress.get(), WorkerTokenInterface)
        ommToken = self.create_interface_score(self._ommTokenAddress.get(), TokenInterface)
        day: int = self._day.get()

        if self._distComplete['daoFund']:
            self._initialize()

        if day >= self.getDay():
            return

        if not self._distComplete['worker']:
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
            self._day.set(day + 1)

    @external(readonly=True)
    def getDay(self) -> int:
        return (self.now() - self._timestampAtStart.get()) // DAY_IN_MICROSECONDS

    @external(readonly=True)
    def getDistributedDay(self) -> int:
        return self._day.get()

    def _initialize(self) -> None:
        day: int = self._day.get()
        tokenDistributionPerDay: int = self.tokenDistributionPerDay(day)
        ommToken = self.create_interface_score(self._ommTokenAddress.get(), TokenInterface)
        ommToken.mint(tokenDistributionPerDay)

        for value in ('worker', 'daoFund'):
            self._distComplete[value] = False
            self._tokenDistTracker[value] = exaMul(tokenDistributionPerDay, self._distPercentage[value])

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

    @external(readonly=True)
    def getDexRewards(self, _account: Address, _start: int = 0, _end: int = 0) -> int:
        start, end = self._checkStartEnd(_start, _end)
        rewards = 0
        for day in range(start, end):
            rewards += self._getRewardsForDay(_account, day)

        return rewards

    @external(readonly=True)
    def getDaoFundRewards(self, _start: int = 0, _end: int = 0) -> int:
        _start, _end = self._checkStartEnd(_start, _end)
        rewards = 0
        for day in range(_start, _end):
            if not self._is_claimed(self._daoFundAddress.get(), day):
                rewards += self._getRewardsForDaoFund(day)

        return rewards

    def _checkStartEnd(self, _start: int, _end: int) -> (int, int):
        if _start == 0 and _end == 0:
            _end = self._day.get()
            _start = max(0, _end - self._rewardsBatchSize.get())
        elif _end == 0:
            _end = min(self._day.get(), _start + self._rewardsBatchSize.get())
        elif _start == 0:
            _start = max(0, _end - self._rewardsBatchSize.get())

        if not (0 <= _start < self._day.get()):
            revert("Invalid value of start provided")
        if not (0 < _end < self._day.get()):
            revert("Invalid value of end provided")
        if _start >= _end:
            revert("Start must not be greater than or equal to end.")
        if _end - _start > self._rewardsBatchSize.get():
            revert(f"Maximum allowed range is {self._rewardsBatchSize.get()}")
        return _start, _end

    def _getRewardsForDay(self, _account: Address, _day: int) -> int:

        if self._is_claimed(_account, _day):
            return 0

        dex = self.create_interface_score(self._dex.get(), DexInterface)

        userLp = dex.balanceOfAt(_account, self._pool_id['OMM/sICX'], _day)
        totalLp = dex.totalSupplyAt(self._pool_id['OMM/sICX'], _day)

        tokenDistributionPerDay = self.tokenDistributionPerDay(_day)

        equivalentReward = 0
        if userLp > 0 and totalLp > 0:
            # TODO snapshot in dist percentage
            totalReward = exaMul(tokenDistributionPerDay, self._distPercentage['ommICX'])
            equivalentReward = exaDiv(exaMul(userLp, totalReward), totalLp)

        userLp1 = dex.balanceOfAt(_account, self._pool_id['OMM/USDS'], _day)
        totalLp1 = dex.totalSupplyAt(self._pool_id['OMM/USDS'], _day)
        userLp2 = convertToExa(dex.balanceOfAt(_account, self._pool_id['OMM/IUSDC'], _day), 12)
        totalLp2 = convertToExa(dex.totalSupplyAt(self._pool_id['OMM/IUSDC'], _day), 12)
        userLpSum = userLp1 + userLp2
        totalLpSum = totalLp1 + totalLp2

        if userLpSum > 0 and totalLpSum > 0:
            totalReward = exaMul(tokenDistributionPerDay, self._distPercentage['dex'])
            equivalentReward += exaDiv(exaMul(userLpSum, totalReward), totalLpSum)

        return equivalentReward

    def _getRewardsForDaoFund(self, _day: int) -> int:
        if self._is_claimed(self._daoFundAddress.get(), _day):
            return 0
        tokenDistributionPerDay = self.tokenDistributionPerDay(_day)
        totalReward = exaMul(tokenDistributionPerDay, self._distPercentage['daoFund'])
        return totalReward

    def _setClaimed(self, _account: Address, _day: int):
        claimed_bit_map = DictDB(self.CLAIMED_BIT_MAP + str(_account), self.db, value_type=int)
        claimed_word_index = _day // 256
        claimed_bit_index = _day % 256
        claimed_bit_map[claimed_word_index] = claimed_bit_map[claimed_word_index] | (1 << claimed_bit_index)

    def _is_claimed(self, _account: Address, _day: int) -> bool:
        claimed_bit_map = DictDB(self.CLAIMED_BIT_MAP + str(_account), self.db, value_type=int)
        claimed_word_index = _day // 256
        claimed_bit_index = _day % 256
        claimed_word = claimed_bit_map[claimed_word_index]
        mask = (1 << claimed_bit_index)
        return claimed_word & mask == mask

    @external
    def claimDexRewards(self, _start: int = 0, _end: int = 0) -> None:
        """
        Used to claim all fees generated by the Balanced system. _start and _end is used to take the range of rewards
        user wants to claim.
        """
        if not self._rewardsActivate.get():
            revert(f"Balanced Dividends: Claim has not been activated")

        start, end = self._checkStartEnd(_start, _end)
        account = self.msg.sender

        totalRewards = 0
        for day in range(start, end):
            rewards = self._getRewardsForDay(account, day)
            if rewards:
                self._setClaimed(account, day)
            totalRewards += rewards

        try:
            ommToken = self.create_interface_score(self._ommTokenAddress.get(), TokenInterface)
            ommToken.transfer(self.msg.sender, totalRewards)
            self.Claimed(account, start, end, totalRewards)
        except BaseException as e:
            revert(f"Error in claiming rewards. Error: {e}")

    @external
    def claimDaoFundRewards(self, _start: int = 0, _end: int = 0) -> None:
        """
        Used to claim all fees generated by the Balanced system. _start and _end is used to take the range of rewards
        user wants to claim.
        """
        if not self._rewardsActivate.get():
            revert(f"Balanced Dividends: Claim has not been activated")

        start, end = self._checkStartEnd(_start, _end)
        account = self._daoFundAddress.get()

        totalRewards = 0
        for day in range(start, end):
            rewards = self._getRewardsForDaoFund(day)
            if rewards:
                self._setClaimed(account, day)
            totalRewards += rewards

        try:
            ommToken = self.create_interface_score(self._ommTokenAddress.get(), TokenInterface)
            ommToken.transfer(self.msg.sender, totalRewards)
            self.Claimed(account, start, end, totalRewards)
        except BaseException as e:
            revert(f"Error in claiming rewards. Error: {e}")

    @eventlog(indexed=1)
    def Claimed(self, _address: Address, _start: int, _end: int, _rewards: int):
        pass
