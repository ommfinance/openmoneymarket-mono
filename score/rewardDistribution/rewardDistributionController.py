from .rewardDistribution import *
from .utils.checks import *

DAY_IN_MICROSECONDS = 86400 * 10 ** 6

TAG = 'RewardDistributionController'


class AddressDetails(TypedDict):
    name: str
    address: Address


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
    DAY = 'day'
    TOKEN_VALUE = 'tokenValue'
    DEX = "dex"
    POOL_ID = "pool_id"
    REWARDS_BATCH_SIZE = "rewardsBatchSize"
    CLAIMED_BIT_MAP = "claimedBitMap"
    REWARDS_ACTIVATE = "rewardsActivate"
    ASSET_NAME = "assetName"
    ADDRESSES = "addresses"
    CONTRACTS = "contracts"

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._day = VarDB(self.DAY, db, value_type=int)
        self._usersUnclaimedRewards = DictDB(self.USERS_UNCLAIMED_REWARDS, db, value_type=int, depth=2)
        self._assetName = DictDB(self.ASSET_NAME, db, value_type=str)
        self._recipients = ArrayDB('recipients', db, value_type=str)

        self._precompute = DictDB('preCompute', db, value_type=bool)
        self._compIndex = DictDB('compIndex', db, value_type=int)
        self._amountMulApy = DictDB('amountMulApy', db, value_type=int, depth=3)
        self._totalAmount = DictDB('totalAmount', db, value_type=int)
        self._distComplete = DictDB('distComplete', db, value_type=bool)
        self._distIndex = DictDB('distIndex', db, value_type=int)
        self._tokenDistTracker = DictDB('tokenDistTracker', db, value_type=int)
        self._distPercentage = DictDB('distPercentage', db, value_type=int, depth=2)
        self._offset = DictDB('offset', db, value_type=int)
        self._admin = VarDB('admin', db, value_type=Address)
        self._dex = VarDB(self.DEX, db, value_type=Address)
        self._pool_id = DictDB(self.POOL_ID, db, value_type=int)
        self._rewardsBatchSize = VarDB(self.REWARDS_BATCH_SIZE, db, value_type=int)
        self._rewardsActivate = VarDB(self.REWARDS_ACTIVATE, db, value_type=int)
        self._addresses = DictDB(self.ADDRESSES, db, value_type=Address)
        self._contracts = ArrayDB(self.CONTRACTS, db, value_type=str)

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

    @origin_owner
    @external
    def setAddresses(self, _addressDetails: List[AddressDetails]) -> None:
        for contracts in _addressDetails:
            if contracts['name'] not in self._contracts:
                self._contracts.put(contracts['name'])
            self._addresses[contracts['name']] = contracts['address']

    @external(readonly=True)
    def getAddresses(self) -> dict:
        return {item: self._addresses[item] for item in self._contracts}

    @only_owner
    @external
    def setAssetName(self, _asset: Address, _name: str):
        self._assetName[_asset] = _name

    @external(readonly=True)
    def getAssetName(self, _asset: Address) -> str:
        return self._assetName[_asset]

    @only_owner
    @external
    def setDistPercentage(self, _ommICX: int, _dex: int, _worker: int, _daoFund: int):
        currentDay = self.getDay()
        length = self._distPercentage["length"][0]
        if length == 0:
            self._distPercentage['ommICX'][length] = _ommICX
            self._distPercentage['dex'][length] = _dex
            self._distPercentage['worker'][length] = _worker
            self._distPercentage['daoFund'][length] = _daoFund
            self._distPercentage["ids"][length] = currentDay
            self._distPercentage["length"][0] += 1
            return
        else:
            lastDay = self._distPercentage["ids"][length - 1]

        if lastDay < currentDay:
            self._distPercentage["ids"][length] = currentDay
            self._distPercentage['ommICX'][length] = _ommICX
            self._distPercentage['dex'][length] = _dex
            self._distPercentage['worker'][length] = _worker
            self._distPercentage['daoFund'][length] = _daoFund
            self._distPercentage["length"][0] += 1
        else:
            self._distPercentage['ommICX'][length - 1] = _ommICX
            self._distPercentage['dex'][length - 1] = _dex
            self._distPercentage['worker'][length - 1] = _worker
            self._distPercentage['daoFund'][length - 1] = _daoFund

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
    def setPoolId(self, _pool: str, _id: int):
        self._pool_id[_pool] = _id

    @external(readonly=True)
    def getPoolId(self, _pool: str) -> int:
        return self._pool_id[_pool]

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
    def distPercentageAt(self, _recipient: str, _day: int) -> int:
        if _day < 0:
            revert(f"{TAG}: "f"IRC2Snapshot: day:{_day} must be equal to or greater then Zero")
        low = 0
        high = self._distPercentage["length"][0]

        while low < high:
            mid = (low + high) // 2
            if self._distPercentage["ids"][mid] > _day:
                high = mid
            else:
                low = mid + 1

        if self._distPercentage["ids"][0] == _day:
            return self._distPercentage[_recipient][0]
        elif low == 0:
            return 0
        else:
            return self._distPercentage[_recipient][low - 1]

    @only_owner
    @external
    def setAdmin(self, _address: Address):
        self._admin.set(_address)

    @external(readonly=True)
    def getAdmin(self) -> Address:
        return self._admin.get()

    @external
    def handleAction(self, _user: Address, _userBalance: int, _totalSupply: int, _asset: Address = None) -> None:
        if _asset is None:
            _asset = self.msg.sender
        accruedRewards = self._updateUserReserveInternal(_user, _asset, _userBalance, _totalSupply)
        if accruedRewards != 0:
            self._usersUnclaimedRewards[_user][_asset] += accruedRewards
            self.RewardsAccrued(_user, _asset, accruedRewards)

    @external(readonly=True)
    def getRewards(self, _user: Address) -> dict:
        dataProvider = self.create_interface_score(self._addresses['lendingPoolDataProvider'], DataProviderInterface)
        totalRewards = 0
        response = {}
        for asset in self._assets:
            supply = dataProvider.getAssetPrincipalSupply(asset, _user)
            userAssetDetails: UserAssetInput = {'asset': asset, 'userBalance': supply['principalUserBalance'],
                                                'totalBalance': supply['principalTotalSupply']}
            unclaimedRewards = self._usersUnclaimedRewards[_user][asset]
            unclaimedRewards += self._getUnclaimedRewards(_user, userAssetDetails)
            response[self._assetName[asset]] = unclaimedRewards
            totalRewards += unclaimedRewards

        response['totalRewards'] = totalRewards

        return response

    @only_lendingPool
    @external
    def claimRewards(self) -> int:
        user = self.msg.sender
        dataProvider = self.create_interface_score(self._addresses['lendingPoolDataProvider'], DataProviderInterface)

        userAssetList = []
        unclaimedRewards = 0
        for asset in self._assets:
            unclaimedRewards += self._usersUnclaimedRewards[user][asset]
            supply = dataProvider.getAssetPrincipalSupply(asset, user)
            userAssetDetails: UserAssetInput = {'asset': asset, 'userBalance': supply['principalUserBalance'],
                                                'totalBalance': supply['principalTotalSupply']}
            userAssetList.append(userAssetDetails)
            self._usersUnclaimedRewards[user][asset] = 0

        accruedRewards = self._claimRewards(user, userAssetList)
        if accruedRewards != 0:
            unclaimedRewards += accruedRewards
            self.RewardsAccrued(user, accruedRewards)

        if unclaimedRewards == 0:
            return 0

        ommToken = self.create_interface_score(self._addresses["ommToken"], TokenInterface)
        ommToken.transfer(user, unclaimedRewards)

        self.RewardsClaimed(user, unclaimedRewards, 'Asset rewards')

    @external
    def distribute(self) -> None:
        worker = self.create_interface_score(self._addresses['workerToken'], WorkerTokenInterface)
        ommToken = self.create_interface_score(self._addresses['ommToken'], TokenInterface)
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
                self.Distribution("worker", user, tokenAmount)
                ommToken.transfer(user, tokenAmount)
                totalSupply -= worker.balanceOf(user)
                tokenDistTracker -= tokenAmount

            self._distComplete['worker'] = True

        elif not self._distComplete['daoFund']:
            self.State("distribute daoFund")
            daoFundAddress = self._addresses['daoFund']
            tokenDistTrackerDaoFund: int = self._tokenDistTracker['daoFund']
            ommToken.transfer(daoFundAddress, tokenDistTrackerDaoFund)
            self._distComplete['daoFund'] = True
            self.Distribution("daoFund", daoFundAddress, tokenDistTrackerDaoFund)
            self._day.set(day + 1)

    @external(readonly=True)
    def getDistributedDay(self) -> int:
        return self._day.get()

    def _initialize(self) -> None:
        day: int = self._day.get()
        tokenDistributionPerDay: int = self.tokenDistributionPerDay(day)
        ommToken = self.create_interface_score(self._addresses['ommToken'], TokenInterface)
        ommToken.mint(tokenDistributionPerDay)

        for recipient in ('worker', 'daoFund'):
            self._distComplete[recipient] = False
            self._tokenDistTracker[recipient] = exaMul(tokenDistributionPerDay, self.distPercentageAt(recipient, day))

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        pass

    @eventlog(indexed=1)
    def Claimed(self, _address: Address, _start: int, _end: int, _rewards: int):
        pass
