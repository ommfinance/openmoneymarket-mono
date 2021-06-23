from .rewardDistribution import *
from .utils.checks import *

BATCH_SIZE = 100
DAY_IN_MICROSECONDS = 86400 * 10 ** 6
IUSDC_PRECISION = 6

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


class RewardDistributionController(RewardDistributionManager):
    USERS_UNCLAIMED_REWARDS = 'usersUnclaimedRewards'
    DATA_PROVIDER = 'data_provider'
    OMM_TOKEN_ADDRESS = 'ommTokenAddress'
    DAY = 'day'
    TOKEN_VALUE = 'tokenValue'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._day = VarDB(self.DAY, db, value_type=int)
        self._tokenValue = DictDB(self.TOKEN_VALUE, db, value_type=int, depth=2)
        self._usersUnclaimedRewards = DictDB(self.USERS_UNCLAIMED_REWARDS, db, value_type=int)
        self._dataProviderAddress = VarDB(self.DATA_PROVIDER, db, value_type=Address)
        self._ommTokenAddress = VarDB(self.OMM_TOKEN_ADDRESS, db, value_type=Address)
        self._workerTokenAddress = VarDB('workerTokenAddress', db, value_type=Address)
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
        self._recipients.put('worker')
        self._recipients.put('ommICX')
        self._recipients.put('dex')
        self._recipients.put('daoFund')
        self._distComplete['daoFund'] = True

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
    def RewardsClaimed(self, _user: Address, _rewards: int) -> None:
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

    def _check(self, _recipient: str) -> bool:
        tokenDistTracker = self._tokenDistTracker[_recipient]
        if not self._totalAmount[_recipient] and tokenDistTracker:
            daoFundAddress = self._daoFundAddress.get()
            ommToken = self.create_interface_score(self._ommTokenAddress.get(), TokenInterface)
            ommToken.transfer(daoFundAddress, tokenDistTracker)
            self.Distribution("daoFund", daoFundAddress, tokenDistTracker)
            self._distComplete[_recipient] = True
            self._tokenDistTracker[_recipient] = 0
            return False

        return True

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
    def getRewardsBalance(self, _user: Address) -> dict:
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
        ommRewards = 0
        liquidityRewards = 0
        total = 0
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
    def claimRewards(self, _amount: int) -> int:
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

        amountToClaim = unclaimedRewards if (_amount > unclaimedRewards) else _amount
        self._usersUnclaimedRewards[user] -= unclaimedRewards - amountToClaim
        ommToken = self.create_interface_score(self._ommTokenAddress.get(), TokenInterface)
        ommToken.transfer(user, amountToClaim)

        self.RewardsClaimed(user, amountToClaim)

        total_token = 0
        for recipient in self._recipients:
            total_token += self._tokenValue[user][recipient]
            self._tokenValue[user][recipient] = 0

        if total_token:
            ommToken = self.create_interface_score(self._ommTokenAddress.get(), TokenInterface)
            ommToken.transfer(user, total_token)
            self.RewardsClaimed(user, amountToClaim)

    @external
    def distribute(self) -> None:
        worker = self.create_interface_score(self._workerTokenAddress.get(), WorkerTokenInterface)
        ommToken = self.create_interface_score(self._ommTokenAddress.get(), TokenInterface)
        day: int = self._day.get()

        if self._distComplete['daoFund']:
            self._initialize()
        
        if day >= self.getDay():
            return

        if not self._precompute['ommICX']:
            self.State("precompute ommICX")
            data_source = self.create_interface_score(self._lpTokenAddress.get(), DataSourceInterface)
            self._totalAmount['ommICX'] = data_source.getTotalValue("OMM2/sICX", day)
            self._precompute['ommICX'] = True

        elif not self._distComplete['ommICX'] and self._check('ommICX'):
            self.State("distribute ommICX")
            data_source = self.create_interface_score(self._lpTokenAddress.get(), DataSourceInterface)
            data_batch = data_source.getDataBatch("OMM2/sICX", day, BATCH_SIZE, self._offset["OMMSICX"])
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

        elif not self._precompute['dex']:
            self.State("precompute dex")
            data_source = self.create_interface_score(self._lpTokenAddress.get(), DataSourceInterface)
            self._totalAmount['dex'] = convertToExa(data_source.getTotalValue("OMM2/IUSDC", day), IUSDC_PRECISION)
            self._totalAmount['dex'] += data_source.getTotalValue("OMM2/USDS", day)
            self._precompute['dex'] = True

        elif not self._distComplete['dex'] and self._check('dex'):
            self.State("distribute dex")
            data_source = self.create_interface_score(self._lpTokenAddress.get(), DataSourceInterface)
            data_batch1 = data_source.getDataBatch("OMM2/IUSDC", day, BATCH_SIZE, self._offset["dex"])
            data_batch2 = data_source.getDataBatch("OMM2/USDS", day, BATCH_SIZE, self._offset["dex"])
            self._offset["dex"] += BATCH_SIZE

            if data_batch1 or data_batch2:
                totalAmount = self._totalAmount['dex']
                tokenDistTracker = self._tokenDistTracker['dex']

                for user in data_batch1:
                    if tokenDistTracker <= 0:
                        break
                    tokenAmount = exaMul(exaDiv(convertToExa(data_batch1[user], IUSDC_PRECISION), totalAmount),
                                         tokenDistTracker)
                    self._tokenValue[Address.from_string(user)]['dex'] += tokenAmount
                    self.Distribution("ommIUSDC", Address.from_string(user), tokenAmount)
                    totalAmount -= convertToExa(data_batch1[user], IUSDC_PRECISION)
                    tokenDistTracker -= tokenAmount

                for user in data_batch2:
                    if tokenDistTracker <= 0:
                        break
                    tokenAmount = exaMul(exaDiv(data_batch2[user], totalAmount), tokenDistTracker)
                    self._tokenValue[Address.from_string(user)]['ommUSDS'] += tokenAmount
                    self.Distribution("ommUSDS", Address.from_string(user), tokenAmount)
                    totalAmount -= data_batch2[user]
                    tokenDistTracker -= tokenAmount

                self._totalAmount['ommUSDS'] = totalAmount
                self._tokenDistTracker['ommUSDS'] = tokenDistTracker

            else:
                self._distComplete['ommUSDS'] = True
                self._offset["OMMUSDS"] = 0

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

        for value in ('ommICX', 'ommUSDS'):
            self._precompute[value] = False
            self._totalAmount[value] = 0
            self._distComplete[value] = False
            self._tokenDistTracker[value] = exaMul(tokenDistributionPerDay, self._distPercentage[value])

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
