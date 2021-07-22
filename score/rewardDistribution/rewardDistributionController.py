from .rewardDistribution import *
from .utils.checks import *

DAY_IN_MICROSECONDS = 86400 * 10 ** 6

TAG = 'RewardDistributionController'


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

    @interface
    def getPrincipalSupply(self, _asset: Address, _user: Address) -> SupplyDetails:
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


class RewardDistributionController(RewardDistributionManager):
    USERS_UNCLAIMED_REWARDS = 'usersUnclaimedRewards'
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
        self._usersUnclaimedRewards = DictDB(self.USERS_UNCLAIMED_REWARDS, db, value_type=int, depth=2)
        self._recipients = ArrayDB('recipients', db, value_type=str)
        self._dailyDistributionPercentage = DictDB('dailyDistributionPercentage', db, value_type=int)

        self._precompute = DictDB('preCompute', db, value_type=bool)
        self._compIndex = DictDB('compIndex', db, value_type=int)
        self._amountMulApy = DictDB('amountMulApy', db, value_type=int, depth=3)
        self._totalAmount = DictDB('totalAmount', db, value_type=int)
        self._distComplete = DictDB('distComplete', db, value_type=bool)
        self._distIndex = DictDB('distIndex', db, value_type=int)
        self._tokenDistTracker = DictDB('tokenDistTracker', db, value_type=int)
        self._offset = DictDB('offset', db, value_type=int)
        self._pool_id = DictDB(self.POOL_ID, db, value_type=int)
        self._rewardsBatchSize = VarDB(self.REWARDS_BATCH_SIZE, db, value_type=int)
        self._rewardsActivate = VarDB(self.REWARDS_ACTIVATE, db, value_type=int)

    def on_install(self) -> None:
        super().on_install()
        self._recipients.put('worker')
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
    def RewardsAccrued(self, _user: Address, _asset: Address, _rewards: int) -> None:
        pass

    @eventlog
    def RewardsClaimed(self, _user: Address, _rewards: int, _msg: str) -> None:
        pass

    @external(readonly=True)
    def name(self) -> str:
        return "RewardDistributionController"

    @only_owner
    @external
    def setAssetName(self, _asset: Address, _name: str):
        self._assetName[_asset] = _name

    @only_owner
    @external
    def setDailyDistributionPercentage(self, _recipient: str, _percentage: int):
        self._dailyDistributionPercentage[_recipient] = _percentage

    @external(readonly=True)
    def getDailyDistributionPercentage(self, _recipient: str) -> int:
        return self._dailyDistributionPercentage[_recipient]

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
        totalRewards = 0
        response = {}

        for asset in self._reserveAssets:
            token = self.create_interface_score(asset, TokenInterface)
            supply = token.getPrincipalSupply(_user)
            userAssetDetails: UserAssetInput = {'asset': asset, 'userBalance': supply['principalUserBalance'],
                                                'totalBalance': supply['principalTotalSupply']}
            unclaimedRewards = self._usersUnclaimedRewards[_user][asset]
            unclaimedRewards += self._getUnclaimedRewards(_user, userAssetDetails)
            response[self._assetName[asset]] = unclaimedRewards
            totalRewards += unclaimedRewards

        for lpId in self._lpIds:
            lp = self.create_interface_score(self._addresses[STAKED_LP], LPInterface)
            asset = lp.getPoolById(lpId)
            supply = lp.getLPStakedSupply(lpId, _user)

            userAssetDetails: UserAssetInput = {'asset': asset, 'userBalance': supply['principalUserBalance'],
                                                'totalBalance': supply['principalTotalSupply']}
            unclaimedRewards = self._usersUnclaimedRewards[_user][asset]
            unclaimedRewards += self._getUnclaimedRewards(_user, userAssetDetails)
            response[self._assetName[asset]] = unclaimedRewards
            totalRewards += unclaimedRewards

        _asset = self._addresses[OMM_TOKEN]
        ommToken = self.create_interface_score(_asset, TokenInterface)
        supply = ommToken.getPrincipalSupply(_user)
        userAssetDetails: UserAssetInput = {'asset': _asset,
                                            'userBalance': supply['principalUserBalance'],
                                            'totalBalance': supply['principalTotalSupply']}
        unclaimedRewards = self._usersUnclaimedRewards[_user][_asset]
        unclaimedRewards += self._getUnclaimedRewards(_user, userAssetDetails)
        response[self._assetName[_asset]] = unclaimedRewards
        totalRewards += unclaimedRewards

        response['total'] = totalRewards

        return response

    @only_lending_pool
    @external
    def claimRewards(self, _user: Address) -> int:

        userAssetList = []
        unclaimedRewards = 0

        for asset in self._reserveAssets:
            token = self.create_interface_score(asset, TokenInterface)
            unclaimedRewards += self._usersUnclaimedRewards[_user][asset]
            supply = token.getPrincipalSupply(_user)
            userAssetDetails: UserAssetInput = {'asset': asset, 'userBalance': supply['principalUserBalance'],
                                                'totalBalance': supply['principalTotalSupply']}
            userAssetList.append(userAssetDetails)
            self._usersUnclaimedRewards[_user][asset] = 0

        for lpId in self._lpIds:
            lp = self.create_interface_score(self._addresses[STAKED_LP], LPInterface)
            asset = lp.getPoolById(lpId)
            unclaimedRewards += self._usersUnclaimedRewards[_user][asset]
            supply = lp.getLPStakedSupply(lpId, _user)
            userAssetDetails: UserAssetInput = {'asset': asset, 'userBalance': supply['principalUserBalance'],
                                                'totalBalance': supply['principalTotalSupply']}
            userAssetList.append(userAssetDetails)
            self._usersUnclaimedRewards[_user][asset] = 0

        _asset = self._addresses[OMM_TOKEN]
        ommToken = self.create_interface_score(_asset, TokenInterface)
        supply = ommToken.getPrincipalSupply(_user)
        unclaimedRewards += self._usersUnclaimedRewards[_user][_asset]
        userAssetDetails: UserAssetInput = {'asset': _asset, 'userBalance': supply['principalUserBalance'],
                                            'totalBalance': supply['principalTotalSupply']}
        userAssetList.append(userAssetDetails)
        self._usersUnclaimedRewards[_user][_asset] = 0

        accruedRewards = self._claimRewards(_user, userAssetList)
        if accruedRewards != 0:
            unclaimedRewards += accruedRewards
            self.RewardsAccrued(_user, self.address, accruedRewards)

        if unclaimedRewards == 0:
            return 0

        ommToken = self.create_interface_score(self._addresses[OMM_TOKEN], TokenInterface)
        ommToken.transfer(_user, unclaimedRewards)

        self.RewardsClaimed(_user, unclaimedRewards, 'Asset rewards')

    @external
    def distribute(self) -> None:
        worker = self.create_interface_score(self._addresses[WORKER_TOKEN], WorkerTokenInterface)
        ommToken = self.create_interface_score(self._addresses[OMM_TOKEN], TokenInterface)
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
            daoFundAddress = self._addresses[DAO_FUND]
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
        ommToken = self.create_interface_score(self._addresses[OMM_TOKEN], TokenInterface)
        ommToken.mint(tokenDistributionPerDay)

        for recipient in ('worker', 'daoFund'):
            self._distComplete[recipient] = False
            self._tokenDistTracker[recipient] = exaMul(tokenDistributionPerDay,
                                                       self._dailyDistributionPercentage[recipient])

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        pass

    @eventlog(indexed=1)
    def Claimed(self, _address: Address, _start: int, _end: int, _rewards: int):
        pass
