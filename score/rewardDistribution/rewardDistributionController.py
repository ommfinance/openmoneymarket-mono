from iconservice import *
from .rewardDistribution import *

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


class RewardDistributionController(IconScoreBase, RewardDistributionManager):
    USERS_UNCLAIMED_REWARDS = 'usersUnclaimedRewards'
    DATA_PROVIDER = 'data_provider'
    OMM_TOKEN_ADDRESS = 'ommTokenAddress'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._usersUnclaimedRewards = DictDB(self.USERS_UNCLAIMED_REWARDS, db, value_type=int)
        self._dataProviderAddress = VarDB(self.DATA_PROVIDER, db, value_type=Address)
        self._ommTokenAddress = VarDB(self.OMM_TOKEN_ADDRESS, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @eventlog
    def RewardsAccrued(self, _user: Address, _rewards: int) -> None:
        pass

    @eventlog
    def RewardsClaimed(self, _user: Address, _rewards: int) -> None:
        pass

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

    @external
    def handleAction(self, _user: Address, _userBalance: int, _totalSupply: int) -> None:
        accruedRewards = self._updateUserReserveInternal(_user, self.msg.sender, _userBalance, _totalSupply)
        if accruedRewards != 0:
            self._usersUnclaimedRewards[_user] += accruedRewards
            self.RewardsAccrued(_user, accruedRewards)

    @external(readonly=True)
    def getRewardsBalance(self, _user: Address) -> int:
        unclaimedRewards = self._usersUnclaimedRewards[_user]
        dataProvider = self.create_interface_score(self.getLendingPoolDataProvider(), DataProviderInterface)

        userAssetList = []
        for asset in self._assets:
            supply = dataProvider.getAssetPrincipalSupply(asset, _user)
            userAssetDetails: UserAssetInput = {'asset': asset, 'userBalance': supply['userPrincipalBalance'],
                                                'totalBalance': supply['totalBalance']}
            userAssetList.append(userAssetDetails)

        unclaimedRewards += self._getUnclaimedRewards(_user, userAssetList)
        return unclaimedRewards

    @external
    def claimRewards(self, _amount: int, to: Address) -> int:
        user = self.msg.sender
        unclaimedRewards = self._usersUnclaimedRewards[user]
        dataProvider = self.create_interface_score(self.getLendingPoolDataProvider(), DataProviderInterface)

        userAssetList = []
        for asset in self._assets:
            supply = dataProvider.getAssetPrincipalSupply(asset, user)
            userAssetDetails: UserAssetInput = {'asset': asset, 'userBalance': supply['userPrincipalBalance'],
                                                'totalBalance': supply['totalBalance']}
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
        ommToken.transfer(to, amountToClaim)

        self.RewardsClaimed(user, to, amountToClaim)
