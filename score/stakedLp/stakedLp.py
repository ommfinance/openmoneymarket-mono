from .utils.RewardRecipientToken import RewardRecipientToken
from .utils.checks import *

MICROSECONDS = 10 ** 6
REWARDS = 'rewards'
DEX = 'dex'


class AddressDetails(TypedDict):
    name: str
    address: Address


class RewardInterface(InterfaceScore):
    @interface
    def handleAction(self, _user: Address, _userBalance: int, _totalSupply: int, _asset: Address = None) -> None:
        pass


class LiquidityPoolInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address, _id: int) -> int:
        pass

    @interface
    def transfer(self, _to: Address, _value: int, _id: int, _data: bytes = None):
        pass


class Status:
    AVAILABLE = 0
    STAKED = 1


class StakedLp(IconScoreBase, RewardRecipientToken):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._supportedPools = ArrayDB('supportedPools', db, int)
        self._poolStakeDetails = DictDB('poolStakeDetails', db, value_type=int, depth=3)
        self._totalStaked = DictDB('totalStaked', db, value_type=int)
        self._addressMap = DictDB('addressMap', db, value_type=Address)
        self._poolIDMap = DictDB('poolIDMap', db, value_type=int)
        self._minimumStake = VarDB('minimumStake', db, value_type=int)
        self._unstakingTime = VarDB('unstakingTime', db, value_type=int)
        self._addresses = DictDB('addresses', db, value_type=Address)
        self._contracts = ArrayDB('contracts', db, value_type=str)

    def on_install(self) -> None:
        super().on_install()
        self._minimumStake.set(0)
        self._unstakingTime.set(0)

    def on_update(self) -> None:
        super().on_update()

    @staticmethod
    def _require(_condition: bool, _message: str):
        if not _condition:
            revert(f'{TAG}: {_message}')

    @external(readonly=True)
    def name(self) -> str:
        return "Omm Stake Lp"

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
    def setMinimumStake(self, _value: int):
        self._minimumStake.set(_value)

    @external(readonly=True)
    def getMinimumStake(self) -> int:
        return self._minimumStake.get()

    @external(readonly=True)
    def getTotalStaked(self, _id: int) -> int:
        return self._totalStaked[_id]

    @only_owner
    @external
    def setUnstakingPeriod(self, _time: int) -> None:
        """
        Set the minimum staking period
        :param _time: Staking time period in days.
        """
        StakedLp._require(_time >= 0, "Time cannot be negative.")
        # total_time = _time * DAY_TO_MICROSECOND  # convert days to microseconds
        total_time = _time * MICROSECONDS
        self._unstakingTime.set(total_time)

    @external(readonly=True)
    def getUnstakingPeriod(self) -> int:
        return self._unstakingTime.get()

    @external(readonly=True)
    def balanceOf(self, _owner: Address, _id: int) -> dict:
        lp = self.create_interface_score(self._addresses[DEX], LiquidityPoolInterface)
        userBalance = lp.balanceOf(_owner, _id)

        return {
            "userTotalBalance": userBalance + self._poolStakeDetails[_owner][_id][Status.STAKED],
            "userAvailableBalance": userBalance,
            "userStakedBalance": self._poolStakeDetails[_owner][_id][Status.STAKED],
            "totalStakedBalance": self._totalStaked[_id]
        }

    @external(readonly=True)
    def detailsBalanceOf(self, _owner: Address) -> dict:
        return {_id: self.balanceOf(_owner, _id) for _id in self._supportedPools}

    @only_owner
    @external
    def addPool(self, _pool: Address, _id: int) -> None:
        self._addressMap[_id] = _pool
        self._poolIDMap[_pool] = _id
        if _id not in self._supportedPools:
            self._supportedPools.put(_id)

    @external(readonly=True)
    def getPoolById(self, _id: int) -> Address:
        return self._addressMap[_id]

    @only_owner
    @external
    def removePool(self, _pool: Address) -> None:
        if _pool not in self._supportedPools:
            revert(f"{TAG}: {_pool} is not in contributor list")
        else:
            top = self._supportedPools.pop()
            if top != _pool:
                for i in range(len(self._supportedPools)):
                    if self._supportedPools[i] == _pool:
                        self._supportedPools[i] = top

    @external(readonly=True)
    def getSupportedPools(self) -> dict:
        return {pool: self._addressMap[pool] for pool in self._supportedPools}

    def _first_time(self, _from: Address, _id: int, _userBalance: int) -> bool:
        if (
                self._poolStakeDetails[_from][_id][Status.AVAILABLE] == 0
                and self._poolStakeDetails[_from][_id][Status.STAKED] == 0
                and _userBalance != 0
        ):
            return True
        else:
            return False

    def _check_first_time(self, _from: Address, _id: int, _userBalance: int):
        # If first time copy the balance to available staked balances
        if self._first_time(_from, _id, _userBalance):
            self._poolStakeDetails[_from][_id][Status.AVAILABLE] = _userBalance

    def _stake(self, _user: Address, _id: int, _value: int) -> None:
        StakedLp._require(_id in self._supportedPools, f'pool with id:{_id} is not supported')
        StakedLp._require(_value > 0, f'Cannot stake less than zero'f'value to stake {_value}')
        StakedLp._require(_value > self._minimumStake.get(),
                          f'Amount to stake:{_value} is smaller the minimum stake:{self._minimumStake.get()}')

        lp = self.create_interface_score(self._addresses[DEX], LiquidityPoolInterface)
        userBalance = lp.balanceOf(_user, _id)
        previousUserStaked = self._poolStakeDetails[_user][_id][Status.STAKED]
        previousTotalStaked = self._totalStaked[_id]

        self._check_first_time(_user, _id, userBalance)
        StakedLp._require(userBalance >= _value,
                          f'Cannot stake,user dont have enough balance'f'amount to stake {_value}'f'balance of user:{_user} is  {userBalance}')
        new_stake = _value
        stake_increment = new_stake - previousUserStaked
        StakedLp._require(stake_increment > 0, "Stake error: Stake amount less than previously staked value")
        self._poolStakeDetails[_user][_id][Status.AVAILABLE] = self._poolStakeDetails[_user][_id][
                                                                   Status.AVAILABLE] - stake_increment
        self._poolStakeDetails[_user][_id][Status.STAKED] = _value
        self._totalStaked[_id] = self._totalStaked[_id] + stake_increment
        reward = self.create_interface_score(self._addresses[REWARDS], RewardInterface)
        reward.handleAction(_user, previousUserStaked, previousTotalStaked, self._addressMap[_id])

    @external
    def unstake(self, _id: int, _value: int) -> None:
        StakedLp._require(_id in self._supportedPools, f'pool with id:{_id} is not supported')
        _user = self.msg.sender
        StakedLp._require(_value > 0, f'Cannot unstake less than zero'
                                      f'value to stake {_value}')

        previousUserStaked = self._poolStakeDetails[_user][_id][Status.STAKED]
        previousTotalStaked = self._totalStaked[_id]
        StakedLp._require(previousUserStaked >= _value, f'Cannot unstake,user dont have enough staked balance '
                                                        f'amount to unstake {_value} '
                                                        f'staked balance of user: {_user} is  {previousUserStaked}')
        self._poolStakeDetails[_user][_id][Status.STAKED] -= _value
        self._poolStakeDetails[_user][_id][Status.AVAILABLE] += _value
        self._totalStaked[_id] = self._totalStaked[_id] - _value
        reward = self.create_interface_score(self._addresses[REWARDS], RewardInterface)
        reward.handleAction(_user, previousUserStaked, previousTotalStaked, self._addressMap[_id])
        lpToken = self.create_interface_score(self._addresses[DEX], LiquidityPoolInterface)
        lpToken.transfer(_user, _value, _id, b'transferBackToUser')

    @only_dex
    @external
    def onIRC31Received(self, _operator: Address, _from: Address, _id: int, _value: int, _data: bytes):
        d = None
        try:
            d = json_loads(_data.decode("utf-8"))
        except BaseException as e:
            revert(f'{TAG}: Invalid data: {_data}. Exception: {e}')
        if set(d.keys()) != {"method"}:
            revert(f'{TAG}: Invalid parameters.')
        if d["method"] == "stake":
            self._stake(_from, _id, _value)
        else:
            revert(f'{TAG}: No valid method called, data: {_data}')

    @external(readonly=True)
    def getTotalStakedBalance(self, _asset: Address) -> int:
        pool_id = self._poolIDMap[_asset]
        return self._totalStaked[pool_id]
