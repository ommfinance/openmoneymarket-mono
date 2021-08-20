from .utils.checks import *
from .utils.math import *
from .interfaces import *
from .addresses import *

MICROSECONDS = 10 ** 6


class StakedLp(Addresses):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._supportedPools = ArrayDB('supportedPools', db, int)
        self._poolStakeDetails = DictDB('poolStakeDetails', db, value_type=int, depth=3)
        self._totalStaked = DictDB('totalStaked', db, value_type=int)
        self._addressMap = DictDB('addressMap', db, value_type=Address)
        self._minimumStake = VarDB('minimumStake', db, value_type=int)

    def on_install(self, _addressProvider: Address) -> None:
        super().on_install(_addressProvider)
        self._minimumStake.set(0)

    def on_update(self) -> None:
        super().on_update()

    @staticmethod
    def _require(_condition: bool, _message: str):
        if not _condition:
            revert(f'{TAG}: {_message}')

    @external(readonly=True)
    def name(self) -> str:
        return f'Omm {TAG}'

    @only_owner
    @external
    def setMinimumStake(self, _value: int):
        self._minimumStake.set(_value)

    @external(readonly=True)
    def getMinimumStake(self) -> int:
        return self._minimumStake.get()

    @external(readonly=True)
    def getTotalStaked(self, _id: int) -> TotalStaked:
        decimals = self._getAverageDecimals(_id)
        return {
            "decimals": decimals,
            "totalStaked": self._totalStaked[_id]
        }

    @external(readonly=True)
    def balanceOf(self, _owner: Address, _id: int) -> dict:
        lp = self.create_interface_score(self._addresses[DEX], LiquidityPoolInterface)
        userBalance = lp.balanceOf(_owner, _id)

        return {
            "poolID": _id,
            "userTotalBalance": userBalance + self._poolStakeDetails[_owner][_id][Status.STAKED],
            "userAvailableBalance": userBalance,
            "userStakedBalance": self._poolStakeDetails[_owner][_id][Status.STAKED],
            "totalStakedBalance": self._totalStaked[_id]
        }

    @external(readonly=True)
    def getBalanceByPool(self) -> List[dict]:
        result = []
        for _id in self._supportedPools:
            lp = self.create_interface_score(self._addresses[DEX], LiquidityPoolInterface)
            totalBalance = lp.balanceOf(self.address, _id)
            pool_details = {
                "poolID": _id,
                "totalStakedBalance": totalBalance
            }
            result.append(pool_details)
        return result

    @external(readonly=True)
    def getPoolBalanceByUser(self, _owner: Address) -> List[dict]:
        result = []
        for _id in self._supportedPools:
            user_balance = self.balanceOf(_owner, _id)
            result.append(user_balance)
        return result

    @only_governance
    @external
    def addPool(self, _id: int, _pool: Address) -> None:
        self._addressMap[_id] = _pool
        if _id not in self._supportedPools:
            self._supportedPools.put(_id)

    @external(readonly=True)
    def getPoolById(self, _id: int) -> Address:
        return self._addressMap[_id]

    @only_governance
    @external
    def removePool(self, _poolID: int) -> None:
        pool = self._addressMap[_poolID]
        if pool is None:
            revert(f"{TAG}: {_poolID} is not in address map")
        self._addressMap.remove(pool)

        top = self._supportedPools.pop()
        _is_removed = top == _poolID
        if _is_removed is False:
            for i in range(len(self._supportedPools)):
                if self._supportedPools[i] == _poolID:
                    self._supportedPools[i] = top
                    _is_removed = True

        if _is_removed is False:
            revert(f"{TAG}: {_poolID} is not in supported pool list")

    @external(readonly=True)
    def getSupportedPools(self) -> dict:
        return {pool: self._addressMap[pool] for pool in self._supportedPools}

    def _stake(self, _user: Address, _id: int, _value: int) -> None:
        StakedLp._require(_id in self._supportedPools, f'pool with id:{_id} is not supported')
        StakedLp._require(_value > 0, f'Cannot stake less than zero ,value to stake {_value}')
        StakedLp._require(_value > self._minimumStake.get(),
                          f'Amount to stake:{_value} is smaller the minimum stake:{self._minimumStake.get()}')

        previousUserStaked = self._poolStakeDetails[_user][_id][Status.STAKED]
        previousTotalStaked = self._totalStaked[_id]
        self._poolStakeDetails[_user][_id][Status.STAKED] = previousUserStaked + _value
        self._totalStaked[_id] = self._totalStaked[_id] + _value
        reward = self.create_interface_score(self._addresses[REWARDS], RewardInterface)
        decimals = self._getAverageDecimals(_id)
        _userDetails = {
            "_user": _user,
            "_userBalance": previousUserStaked,
            "_totalSupply": previousTotalStaked,
            "_decimals": decimals,
        }
        reward.handleLPAction(self._addressMap[_id], _userDetails)

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
        self._totalStaked[_id] = self._totalStaked[_id] - _value
        reward = self.create_interface_score(self._addresses[REWARDS], RewardInterface)
        decimals = self._getAverageDecimals(_id)
        _userDetails = {
            "_user": _user,
            "_userBalance": previousUserStaked,
            "_totalSupply": previousTotalStaked,
            "_decimals": decimals,
        }
        reward.handleLPAction(self._addressMap[_id], _userDetails)
        
        lpToken = self.create_interface_score(self._addresses[DEX], LiquidityPoolInterface)
        lpToken.transfer(_user, _value, _id, b'transferBackToUser')

    @only_dex
    @external
    def onIRC31Received(self, _operator: Address, _from: Address, _id: int, _value: int, _data: bytes):
        d = None
        try:
            d = json_loads(_data.decode("utf-8"))
        except IconScoreException:
            revert(f'{TAG}: Invalid data: {_data}.')
        if set(d.keys()) != {"method"}:
            revert(f'{TAG}: Invalid parameters.')
        if d["method"] == "stake":
            self._stake(_from, _id, _value)
        else:
            revert(f'{TAG}: No valid method called, data: {_data}')

    @external(readonly=True)
    def getLPStakedSupply(self, _id: int, _user: Address) -> SupplyDetails:
        balance = self.balanceOf(_user, _id)
        return {
            "decimals": self._getAverageDecimals(_id),
            "principalUserBalance": balance["userStakedBalance"],
            "principalTotalSupply": balance["totalStakedBalance"]
        }

    def _getAverageDecimals(self, _id: int) -> int:
        dex = self.create_interface_score(self.getAddress(DEX), LiquidityPoolInterface)
        pool_stats = dex.getPoolStats(_id)
        quote_decimals = pool_stats['quote_decimals']
        base_decimals = pool_stats['base_decimals']
        average_decimals = (quote_decimals + base_decimals) // 2
        return average_decimals
