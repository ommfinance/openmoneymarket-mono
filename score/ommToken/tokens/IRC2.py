from .IIRC2 import TokenStandard
from ..addresses import *
from ..interfaces import *
from ..utils.consts import *
from ..utils.enumerable_set import EnumerableSetDB
from ..utils.ommSnapshot import OMMSnapshot

TAG = 'Omm Token'
DAY_TO_MICROSECOND = 86400 * 10 ** 6
MICROSECONDS = 10 ** 6


class IRC2(TokenStandard, Addresses, OMMSnapshot):
    """
    Implementation of IRC2
    """
    _NAME = 'name'
    _SYMBOL = 'symbol'
    _DECIMALS = 'decimals'
    _TOTAL_SUPPLY = 'total_supply'
    _BALANCES = 'balances'
    _ADMIN = 'admin'
    _LOCK_LIST = 'lock_list'

    _MINUMUM_STAKE = 'minimum_stake'
    _STAKED_BALANCES = 'staked_balances'
    _TOTAL_STAKED_BALANCE = 'total_stake_balance'
    _UNSTAKING_PERIOD = 'unstaking_period'
    _SNAPSHOT_STARTED_AT = 'snapshot-started-at'
    _STAKERS = 'stakers'

    def __init__(self, db: IconScoreDatabase) -> None:
        """
        Variable Definition
        """
        super().__init__(db)
        self._name = VarDB(self._NAME, db, value_type=str)
        self._symbol = VarDB(self._SYMBOL, db, value_type=str)
        self._decimals = VarDB(self._DECIMALS, db, value_type=int)
        self._total_supply = VarDB(self._TOTAL_SUPPLY, db, value_type=int)
        self._balances = DictDB(self._BALANCES, db, value_type=int)
        self._admin = VarDB(self._ADMIN, db, value_type=Address)
        self._lock_list = EnumerableSetDB(self._LOCK_LIST, db, value_type=Address)

        self._minimum_stake = VarDB(self._MINUMUM_STAKE, db, value_type=int)
        self._staked_balances = DictDB(self._STAKED_BALANCES, db, value_type=int, depth=2)
        self._total_staked_balance = VarDB(self._TOTAL_STAKED_BALANCE, db, value_type=int)
        self._unstaking_period = VarDB(self._UNSTAKING_PERIOD, db, value_type=int)
        self._snapshot_started_at = VarDB(self._SNAPSHOT_STARTED_AT, db, value_type=int)
        self._stakers = EnumerableSetDB(self._STAKERS, db, value_type=Address)

    def on_install(
            self,
            _addressProvider: Address,
            _tokenName: str,
            _symbolName: str,
            _initialSupply: int = DEFAULT_INITIAL_SUPPLY,
            _decimals: int = DEFAULT_DECIMAL_VALUE) -> None:
        """
        Variable Initialization.

        :param _tokenName: The name of the token.
        :param _symbolName: The symbol of the token.
        :param _initialSupply: The total number of tokens to initialize with.
        It is set to total supply in the beginning, 0 by default.
        :param _decimals: The number of decimals. Set to 18 by default.

        total_supply is set to `_initialSupply`* 10 ^ decimals.

        Raise
        InvalidNameError
            If the length of strings `_symbolName` and `_tokenName` is 0 or less.
        ZeroValueError
            If `_initialSupply` is 0 or less.
            If `_decimals` value is 0 or less.
        """
        if len(_symbolName) <= 0:
            revert("Invalid Symbol name")
        if len(_tokenName) <= 0:
            revert("Invalid Token Name")
        if _initialSupply < 0:
            revert("Initial Supply cannot be less than zero")
        if _decimals < 0:
            revert("Decimals cannot be less than zero")

        super().on_install(_addressProvider)

        total_supply = _initialSupply * 10 ** _decimals

        Logger.debug(f'on_install: total_supply={total_supply}', TAG)

        self._name.set(_tokenName)
        self._symbol.set(_symbolName)
        self._total_supply.set(total_supply)
        self._decimals.set(_decimals)
        self._balances[self.msg.sender] = total_supply

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        """
        Returns the name of the token.
        """
        return self._name.get()

    @external(readonly=True)
    def symbol(self) -> str:
        """
        Returns the symbol of the token.
        """
        return self._symbol.get()

    @external(readonly=True)
    def decimals(self) -> int:
        """
        Returns the number of decimals.
        """
        return self._decimals.get()

    @external(readonly=True)
    def totalSupply(self) -> int:
        """
        Returns the total number of tokens in existence.
        """
        return self._total_supply.get()

    @external(readonly=True)
    def balanceOf(self, _owner: Address) -> int:
        """
        Returns the amount of transferable tokens owned by the account excluding staked tokens
        :param _owner: The account whose balance is to be checked.
        :return Amount of tokens owned by the `account` with the given address.
        """

        return self.available_balanceOf(_owner)

    @external(readonly=True)
    def available_balanceOf(self, _owner: Address) -> int:
        detail_balance = self.details_balanceOf(_owner)
        return detail_balance["availableBalance"]

    @external(readonly=True)
    def staked_balanceOf(self, _owner: Address) -> int:
        return self._staked_balances[_owner][Status.STAKED]

    @external(readonly=True)
    def unstaked_balanceOf(self, _owner: Address) -> int:
        detail_balance = self.details_balanceOf(_owner)
        return detail_balance["unstakingBalance"]

    @only_owner
    @external
    def setUnstakingPeriod(self, _timeInSeconds: int) -> None:
        """
        Set the minimum staking period
        :param _timeInSeconds: Staking time period in seconds.
        """
        if _timeInSeconds < 0:
            revert(f"{TAG}: ""Time cannot be negative.")
        total_time = _timeInSeconds * MICROSECONDS
        self._unstaking_period.set(total_time)

    @external(readonly=True)
    def getUnstakingPeriod(self) -> int:
        return self._unstaking_period.get()

    @only_owner
    @external
    def addStaker(self, _stakers: List[Address]):
        for items in _stakers:
            self._addStaker(items)

    @only_owner
    @external
    def removeStaker(self, _stakers: List[Address]):
        for items in _stakers:
            self._removeStaker(items)

    def _addStaker(self, _staker: Address):
        self._stakers.add(_staker)

    def _removeStaker(self, _staker: Address):
        self._stakers.remove(_staker)

    @external(readonly=True)
    def getStakersList(self, _start: int, _end: int) -> List[Address]:
        self._require(_end > _start, f'start index cannot be greater than end index')
        self._require(_end - _start <= 100, f'range cannot be greater than 100')
        return [addr for addr in self._stakers.range(_start, _end)]

    @external(readonly=True)
    def totalStakers(self) -> int:
        return len(self._stakers)

    @external(readonly=True)
    def inStakerList(self, _staker: Address) -> bool:
        return _staker in self._stakers

    @external(readonly=True)
    def details_balanceOf(self, _owner: Address) -> dict:
        userBalance = self._balances[_owner]
        stakedBalance = self._staked_balances[_owner][Status.STAKED]
        unstaking_amount = self._staked_balances[_owner][Status.UNSTAKING]

        if self._staked_balances[_owner][Status.UNSTAKING_PERIOD] < self.now():
            unstaking_amount = 0

        unstaking_time = 0 if unstaking_amount == 0 else self._staked_balances[_owner][Status.UNSTAKING_PERIOD]
        return {
            "totalBalance": userBalance,
            "availableBalance": userBalance - stakedBalance - unstaking_amount,
            "stakedBalance": stakedBalance,
            "unstakingBalance": unstaking_amount,
            "unstakingTimeInMicro": unstaking_time
        }

    @external(readonly=True)
    def total_staked_balance(self) -> int:
        return self._total_staked_balance.get()

    @only_owner
    @external
    def setMinimumStake(self, _min: int) -> None:
        """
        Sets the minimum stake.

        :param _min: The minimum stake value
        """
        return self._minimum_stake.set(_min)

    @external(readonly=True)
    def getMinimumStake(self) -> int:
        """
        Returns the minimum stake value
        """
        return self._minimum_stake.get()

    @only_owner
    @external
    def add_to_lockList(self, _user: Address):
        if _user not in self._lock_list:
            self._lock_list.add(_user)

        staked_balance = self._staked_balances[_user][Status.STAKED]
        if staked_balance > 0:
            # Check if the unstaking period has already been reached.
            self._makeAvailable(_user)
            self._staked_balances[_user][Status.STAKED] = 0
            self._staked_balances[_user][Status.UNSTAKING] += staked_balance
            self._staked_balances[_user][Status.UNSTAKING_PERIOD] = self.now() + self._unstaking_period.get()
            self._total_staked_balance.set(self._total_staked_balance.get() - staked_balance)

    @only_owner
    @external
    def remove_from_lockList(self, _user: Address):
        IRC2._require(_user in self._lock_list, f'Cannot remove, the user {_user} is not in lock list')
        self._lock_list.remove(_user)

    @external(readonly=True)
    def get_locklist_addresses(self, _start: int, _end: int) -> List[Address]:
        return [addr for addr in self._lock_list.range(_start, _end)]

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        pass

    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        IRC2._require(self.msg.sender not in self._lock_list,
                      f'Cannot transfer, the sender {self.msg.sender} is locked')
        IRC2._require(_to not in self._lock_list,
                      f'Cannot transfer, the receiver {_to} is locked')
        if _data is None:
            _data = b'None'
        self._transfer(self.msg.sender, _to, _value, _data)

    def _transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        """
        Transfers certain amount of tokens from sender to the recipient.
        This is an internal function.

        :param _from: The account from which the token is to be transferred.
        :param _to: The account to which the token is to be transferred.
        :param _value: The no. of tokens to be transferred.
        :param _data: Any information or message

        Raises
        ZeroValueError
            if the value to be transferred is less than 0
        InsufficientBalanceError
            if the sender has less balance than the value to be transferred
        """

        if _value < 0:
            revert(f"{TAG}: ""Transferring value cannot be less than 0.")

        if self._balances[_from] < _value:
            revert(f"{TAG}: ""Insufficient balance")
        lending_pool = self.create_interface_score(self.getAddresses()[LENDING_POOL], LendingPoolInterface)
        isFeeSharingEnabled = lending_pool.isFeeSharingEnable(_from)
        if isFeeSharingEnabled:
            self.set_fee_sharing_proportion(100)

        self._makeAvailable(_to)
        self._makeAvailable(_from)
        senderAvailableBalance = self.available_balanceOf(_from)
        if senderAvailableBalance < _value:
            revert(f'{TAG}: '
                   f'available balance of user {senderAvailableBalance}'
                   f'balance to transfer {_value}')

        self._balances[_from] -= _value
        self._balances[_to] += _value

        if _to.is_contract:
            """
            If the recipient is SCORE,
            then calls `tokenFallback` to hand over control.
            """
            recipient_score = self.create_interface_score(_to, TokenFallbackInterface)
            recipient_score.tokenFallback(_from, _value, _data)

        # Emits an event log `Transfer`
        self.Transfer(_from, _to, _value, _data)

    @staticmethod
    def _require(_condition: bool, _message: str):
        if not _condition:
            revert(f'{TAG}: {_message}')

    @only_lending_pool
    @external
    def stake(self, _value: int, _user: Address) -> None:
        revert(f"{TAG}: Staking no longer supported.")
        userBalance = self._balances[_user]
        IRC2._require(_value > 0, f'Cannot stake less than zero'f'value to stake {_value}')
        IRC2._require(_value >= self._minimum_stake.get(),
                      f'Amount to stake:{_value} is smaller the minimum stake:{self._minimum_stake.get()}')

        self._makeAvailable(_user)
        IRC2._require((userBalance - self._staked_balances[_user][Status.UNSTAKING]) >= _value,
                      f'Cannot stake,user dont have enough balance amount to stake {_value}'f'balance of user:{_user} is  {userBalance}')
        IRC2._require(_user not in self._lock_list, f'Cannot stake,the address {_user} is locked')
        old_total_supply = self._total_staked_balance.get()
        _user_old_stake = self._staked_balances[_user][Status.STAKED]
        new_stake = _value
        stake_increment = new_stake - _user_old_stake
        IRC2._require(stake_increment > 0, "Stake error: Stake amount less than previously staked value")
        self._staked_balances[_user][Status.STAKED] = _value
        self._addStaker(_user)
        _new_total_staked_balance = old_total_supply + stake_increment
        self.onStakeChanged({
            "_user": _user,
            "_new_total_staked_balance": _new_total_staked_balance,
            "_old_total_staked_balance": old_total_supply,
            "_user_new_staked_balance": new_stake,
            "_user_old_staked_balance": _user_old_stake
        })

    @external
    def cancelUnstake(self, _value: int):
        revert(f"{TAG}: Staking no longer supported. Lock your tokens.")
        IRC2._require(_value > 0, f'Cannot cancel negative unstake')

        _user = self.msg.sender

        IRC2._require(_user not in self._lock_list, f'Cannot cancel unstake,the address {_user} is locked')

        userBalances = self.details_balanceOf(_user)
        unstakingBalance = userBalances['unstakingBalance']
        _user_old_stake = userBalances['stakedBalance']

        IRC2._require(unstakingBalance >= _value,
                      f'Cannot cancel unstake,cancel value is more than the actual unstaking amount')

        old_total_supply = self._total_staked_balance.get()

        lending_pool = self.create_interface_score(self.getAddresses()[LENDING_POOL], LendingPoolInterface)
        isFeeSharingEnabled = lending_pool.isFeeSharingEnable(_user)
        if isFeeSharingEnabled:
            self.set_fee_sharing_proportion(100)
        _new_staked_balance = _user_old_stake + _value
        self._staked_balances[_user][Status.STAKED] = _new_staked_balance

        self._staked_balances[_user][Status.UNSTAKING] = unstakingBalance - _value
        self._addStaker(_user)
        _new_total_staked_balance = old_total_supply + _value
        self.onStakeChanged({
            "_user": _user,
            "_new_total_staked_balance": _new_total_staked_balance,
            "_old_total_staked_balance": old_total_supply,
            "_user_new_staked_balance": _new_staked_balance,
            "_user_old_staked_balance": _user_old_stake
        })

    def _handleAction(self, _user, _user_balance, _total_supply):
        _userDetails = {
            "_user": _user,
            "_userBalance": _user_balance,
            "_totalSupply": _total_supply,
            "_decimals": self.decimals(),
        }
        rewardDistribution = self.create_interface_score(self._addresses[REWARDS], RewardDistributionInterface)
        rewardDistribution.handleAction(_userDetails)

    @only_lending_pool
    @external
    def unstake(self, _value: int, _user: Address) -> None:
        IRC2._require(_value > 0, f'Cannot unstake less than zero'
                                  f'value to stake {_value}')
        self._makeAvailable(_user)
        staked_balance = self.staked_balanceOf(_user)
        before_total_staked_balance = self._total_staked_balance.get()
        IRC2._require(staked_balance >= _value, f'Cannot unstake,user dont have enough staked  balance'
                                                f'amount to unstake {_value}'
                                                f'staked balance of user:{_user} is  {staked_balance}')
        IRC2._require(_user not in self._lock_list, f'Cannot unstake,the address {_user} is locked')
        if self._staked_balances[_user][Status.UNSTAKING] > 0:
            revert("you already have a unstaking order,try after the amount is unstaked")

        _new_staked_balance = staked_balance - _value
        self._staked_balances[_user][Status.STAKED] = _new_staked_balance
        self._staked_balances[_user][Status.UNSTAKING] = _value
        self._staked_balances[_user][Status.UNSTAKING_PERIOD] = self.now() + self._unstaking_period.get()

        _new_total_staked_balance = before_total_staked_balance - _value
        if _new_staked_balance == 0:
            self._removeStaker(_user)

        self.onStakeChanged({
            "_user": _user,
            "_new_total_staked_balance": _new_total_staked_balance,
            "_old_total_staked_balance": before_total_staked_balance,
            "_user_new_staked_balance": _new_staked_balance,
            "_user_old_staked_balance": staked_balance
        })

    @external
    def lockStakedOMM(self, _amount: int, _lockPeriod: int):
        _user = self.msg.sender
        staked_balance = self.staked_balanceOf(_user)
        IRC2._require(staked_balance >= _amount, "Cannot lock more than staked.")
        ve_omm_addr = self._addresses[VE_OMM]
        ve_omm = self.create_interface_score(ve_omm_addr, VeOmmInterface)
        locked_balance = ve_omm.getLocked(_user)

        if locked_balance.get('amount') > 0 :
            # increaseAmount
            depositData = {'method': 'increaseAmount', 'params': {'unlockTime': _lockPeriod}}
            data = json.dumps(depositData).encode('utf-8')
        else:
            # createLock
            depositData = {'method': 'createLock', 'params': {'unlockTime': _lockPeriod}}
            data = json.dumps(depositData).encode('utf-8')

        self._staked_balances[_from][Status.STAKED] -= _amount

        self._transfer(_user, ve_omm_addr, _amount, _data)


    def onStakeChanged(self, params: OnStakeChangedParams):
        _user = params['_user']
        _new_total_staked_balance = params['_new_total_staked_balance']
        _old_total_staked_balance = params['_old_total_staked_balance']
        _user_new_staked_balance = params['_user_new_staked_balance']
        _user_old_staked_balance = params['_user_old_staked_balance']

        self._total_staked_balance.set(_new_total_staked_balance)
        delegation = self.create_interface_score(self._addresses[DELEGATION], DelegationInterface)
        delegation.updateDelegations(_user=_user)
        self._handleAction(_user, _user_old_staked_balance, _old_total_staked_balance)
        _initial_timestamp: int = self._snapshot_started_at.get()
        self._create_initial_snapshot(_user, _initial_timestamp, _user_old_staked_balance)
        self._createSnapshot(_user, _user_old_staked_balance, _user_new_staked_balance, _new_total_staked_balance)

    def _makeAvailable(self, _from: Address):
        # Check if the unstakin g period has already been reached.
        if self._staked_balances[_from][Status.UNSTAKING_PERIOD] <= self.now():
            self._staked_balances[_from][Status.UNSTAKING] = 0

    def _mint(self, _to: Address, _amount: int, _data: bytes = None) -> None:
        """
        Creates amount number of tokens, and assigns to account
        Increases the balance of that account and total supply.
        This is an internal function

        :param _amount: Number of tokens to be created at the `account`.
        :param _data: Any information or message

        Raises
        ZeroValueError
        if the `amount` is less than or equal to zero.
        """

        if _amount <= 0:
            revert(f"ZeroValueError: _amount: {_amount}")

        self._total_supply.set(self._total_supply.get() + _amount)
        self._balances[_to] += _amount

        self.Transfer(ZERO_SCORE_ADDRESS, _to, _amount, _data)
