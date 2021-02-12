from iconservice import *
from .IIRC2 import TokenStandard
from ..utils.checks import *
from ..utils.consts import *

TAG = 'IRC_2'
DAY_TO_MICROSECOND = 864 * 10 ** 8
MICROSECONDS = 10 ** 6


class InsufficientBalanceError(Exception):
    pass


class ZeroValueError(Exception):
    pass


class InvalidNameError(Exception):
    pass


# An interface of tokenFallback.
# Receiving SCORE that has implemented this interface can handle
# the receiving or further routine.
class TokenFallbackInterface(InterfaceScore):
    @interface
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        pass


class Status:
    AVAILABLE = 0
    STAKED = 1
    UNSTAKING = 2
    UNSTAKING_PERIOD = 3


class IRC2(TokenStandard, IconScoreBase):
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
        self._lock_list = ArrayDB(self._LOCK_LIST, db, value_type=Address)

        self._minimum_stake = VarDB(self._MINUMUM_STAKE, db, value_type=int)
        self._staked_balances = DictDB(self._STAKED_BALANCES, db, value_type=int, depth=2)
        self._total_staked_balance = VarDB(self._TOTAL_STAKED_BALANCE, db, value_type=int)
        self._unstaking_period = VarDB(self._UNSTAKING_PERIOD, db, value_type=int)

    def on_install(self, _tokenName: str,
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
            raise InvalidNameError("Invalid Symbol name")
            pass
        if len(_tokenName) <= 0:
            raise InvalidNameError("Invalid Token Name")
            pass
        if _initialSupply < 0:
            raise ZeroValueError("Initial Supply cannot be less than zero")
            pass
        if _decimals < 0:
            raise ZeroValueError("Decimals cannot be less than zero")
            pass

        super().on_install()

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
		Returns the amount of tokens owned by the account.

		:param _owner: The account whose balance is to be checked.
		:return Amount of tokens owned by the `account` with the given address.
		"""
        return self._balances[_owner]

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
    def set_unstaking_period(self, _time: int) -> None:
        """
        Set the minimum staking period
        :param _time: Staking time period in days.
        """
        if _time < 0:
            revert("Time cannot be negative.")
        # total_time = _time * DAY_TO_MICROSECOND  # convert days to microseconds
        total_time = _time  * MICROSECONDS
        self._unstaking_period.set(total_time)

    @external(readonly=True)
    def details_balanceOf(self, _owner: Address) -> dict:
        if self._staked_balances[_owner][Status.UNSTAKING_PERIOD] < self.now():
            curr_unstaked = self._staked_balances[_owner][Status.UNSTAKING]
        else:
            curr_unstaked = 0

        if self._first_time(_owner):
            available_balance = self.balanceOf(_owner)
        else:
            available_balance = self._staked_balances[_owner][Status.AVAILABLE]

        unstaking_amount = self._staked_balances[_owner][Status.UNSTAKING] - curr_unstaked
        unstaking_time = 0 if unstaking_amount == 0 else self._staked_balances[_owner][Status.UNSTAKING_PERIOD]
        return {
            "totalBalance": self._balances[_owner],
            "availableBalance": available_balance + curr_unstaked,
            "stakedBalance": self._staked_balances[_owner][Status.STAKED],
            "unstakingBalance": unstaking_amount,
            "unstakingTimeInMills": unstaking_time
        }

    @external(readonly=True)
    def total_staked_balance(self) -> int:
        return self._total_staked_balance.get()

    @only_owner
    @external
    def setAdmin(self, _admin: Address) -> None:
        """
		Sets the authorized address.

		:param _admin: The authorized admin address.
		"""
        return self._admin.set(_admin)

    @external(readonly=True)
    def getAdmin(self) -> Address:
        """
		Returns the authorized admin address.
		"""
        return self._admin.get()

    @only_owner
    @external
    def setMinumumStake(self, _min: int) -> None:
        """
        Sets the minimum stake.

        :param _min: The minimum stake value
        """
        return self._minimum_stake.set(_min)

    @external(readonly=True)
    def getMinimumStake(self) -> Address:
        """
        Returns the minimum stake value
        """
        return self._minimum_stake.get()

    @only_owner
    @external
    def add_to_lockList(self, _user: Address):
        if _user not in self._lock_list:
            self._lock_list.put(_user)
        # Unstake TAP of locklist address
        staked_balance = self._staked_balances[_user][Status.STAKED]
        if staked_balance > 0:
            # Check if the unstaking period has already been reached.
            self._makeAvailable(_user)
            self._staked_balances[_user][Status.STAKED] = 0
            self._staked_balances[_user][Status.UNSTAKING] += staked_balance
            self._staked_balances[_user][Status.UNSTAKING_PERIOD] = (self.now() + self._unstaking_period.get())
            self._total_staked_balance.set(self._total_staked_balance.get() - staked_balance)
            # stake_address_changes = self._stake_changes[self._stake_address_update_db.get()]
            # stake_address_changes.put(_user)

    @only_owner
    @external
    def remove_from_lockList(self, _user: Address):
        self._require(_user in self._lock_list, "Remove error: User not in locklist")
        top = self._lock_list.pop()
        if top != _user:
            for i in range(len(self._lock_list)):
                if self._lock_list[i] == _user:
                    self._lock_list[i] = top

    @external(readonly=True)
    def get_locklist_addresses(self) -> list:
        lockList = []
        for user in self._lock_list:
            lockList.append(user)
        return lockList

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        pass

    @eventlog(indexed=1)
    def Mint(self, account: Address, amount: int, _data: bytes):
        pass

    @eventlog(indexed=1)
    def Burn(self, account: Address, amount: int):
        pass

    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        self._require(self.msg.sender not in self._lock_list,"Transfer error:The address is locker")
        if _data is None:
            _data = b'None'
        self._transfer(self.msg.sender, _to, _value, _data)

    def _transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        """
		Transfers certain amount of tokens from sender to the recepient.
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
            raise ZeroValueError("Transferring value cannot be less than 0.")
            return

        if self._balances[_from] < _value:
            raise InsufficientBalanceError("Insufficient balance.")
            return

        self._check_first_time(_from)
        self._check_first_time(_to)
        self._makeAvailable(_to)
        self._makeAvailable(_from)
        if self._staked_balances[_from][Status.AVAILABLE] < _value:
            revert("OMM token transfer error:Out of available balance")

        self._balances[_from] -= _value
        self._balances[_to] += _value

        self._staked_balances[_from][Status.AVAILABLE] = (self._staked_balances[_from][Status.AVAILABLE] - _value)
        self._staked_balances[_to][Status.AVAILABLE] = (self._staked_balances[_to][Status.AVAILABLE] + _value)
        
        if _to.is_contract:
            """
			If the recipient is SCORE,
			then calls `tokenFallback` to hand over control.
			"""
            recipient_score = self.create_interface_score(_to, TokenFallbackInterface)
            recipient_score.tokenFallback(_from, _value, _data)

        # Emits an event log `Transfer`
        self.Transfer(_from, _to, _value, _data)

    def _require(self, _condition: bool, _message: str):
        if not _condition:
            revert(_message)

    def _first_time(self, _from: Address) -> bool:
        if (
                self._staked_balances[_from][Status.AVAILABLE] == 0
                and self._staked_balances[_from][Status.STAKED] == 0
                and self._staked_balances[_from][Status.UNSTAKING] == 0
                and self._balances[_from] != 0
        ):
            return True
        else:
            return False

    def _check_first_time(self, _from: Address):
        # If first time copy the balance to available staked balances
        if self._first_time(_from):
            self._staked_balances[_from][Status.AVAILABLE] = self._balances[_from]

    @external
    def stake(self, _value: int) -> None:
        _from = self.msg.sender
        self._require(_value > 0, "Stake error:cant stake less than zero")
        self._require(self._balances[_from] > _value, "Stake error:Out of balance")
        self._require(_value > self._minimum_stake.get(), "Stake error:Stake amount must be greater than minimum stake")
        self._check_first_time(_from)
        self._makeAvailable(_from)
        self._require(_from not in self._lock_list, "Stake error: The address is locked ")
        old_stake = self._staked_balances[_from][Status.STAKED] + self._staked_balances[_from][Status.UNSTAKING]
        new_stake = _value
        stake_increment = _value - self._staked_balances[_from][Status.STAKED]
        unstake_amount: int = 0
        if new_stake > old_stake:
            offset: int = new_stake - old_stake
            self._staked_balances[_from][Status.AVAILABLE] = self._staked_balances[_from][Status.AVAILABLE] - offset
        else:
            unstake_amount = old_stake - new_stake

        self._staked_balances[_from][Status.STAKED] = _value
        self._staked_balances[_from][Status.UNSTAKING] = unstake_amount
        self._staked_balances[_from][Status.UNSTAKING_PERIOD] = self.now() + self._unstaking_period.get()
        self._total_staked_balance.set(self._total_staked_balance.get() + stake_increment)

        
    @external
    def unstake(self,_value:int)-> None:
        _from = self.msg.sender
        self._require(_value > 0, "Unstake error:cant unstake less than zero")
        self._makeAvailable(_from)
        staked_balance=self.staked_balanceOf(_from)
        self._require(staked_balance >= _value,"Unstake error:not enough staked balance to unstake")
        self._require(_from not in self._lock_list, "Stake error: The address is locked ")      
        self._staked_balances[_from][Status.UNSTAKING]=_value
        self._staked_balances[_from][Status.UNSTAKING_PERIOD] = self.now()+self._unstaking_period.get()
        self._total_staked_balance.set(self._total_staked_balance.get()-value)




    def _makeAvailable(self, _from: Address):
        # Check if the unstaking period has already been reached.
        if self._staked_balances[_from][Status.UNSTAKING_PERIOD] <= self.now():
            curr_unstaked = self._staked_balances[_from][Status.UNSTAKING]
            self._staked_balances[_from][Status.UNSTAKING] = 0
            self._staked_balances[_from][Status.AVAILABLE] += curr_unstaked

    @only_admin
    def _mint(self, account: Address, amount: int, _data: bytes) -> None:
        """
		Creates amount number of tokens, and assigns to account
		Increases the balance of that account and total supply.
		This is an internal function

		:param account: The account at whhich token is to be created.
		:param amount: Number of tokens to be created at the `account`.
		:param _data: Any information or message

		Raises
		ZeroValueError
			if the `amount` is less than or equal to zero.
		"""

        if amount <= 0:
            raise ZeroValueError("Invalid Value")
            pass

        self._total_supply.set(self._total_supply.get() + amount)
        self._balances[self.address] += amount

        self._transfer(self.address, account, amount, _data)

        # Emits an event log Mint
        self.Mint(account, amount, _data)