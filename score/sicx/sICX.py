from iconservice import *

TAG = 'SampleToken'


# An interface of ICON Token Standard, IRC-2
class TokenStandard(ABC):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def symbol(self) -> str:
        pass

    @abstractmethod
    def decimals(self) -> int:
        pass

    @abstractmethod
    def totalSupply(self) -> int:
        pass

    @abstractmethod
    def balanceOf(self, _owner: Address) -> int:
        pass

    @abstractmethod
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass


# An interface of tokenFallback.
# Receiving SCORE that has implemented this interface can handle
# the receiving or further routine.
class TokenFallbackInterface(InterfaceScore):
    @interface
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        pass


class Sicx(IconScoreBase, TokenStandard):
    _BALANCES = 'balances'
    _TOTAL_SUPPLY = 'total_supply'
    _DECIMALS = 'decimals'

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        pass

    @eventlog(indexed=2)
    def Mint(self, _account: Address, _amount: int):
        pass

    @eventlog(indexed=2)
    def Burn(self, _account: Address, _amount: int):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._total_supply = VarDB(self._TOTAL_SUPPLY, db, value_type=int)
        self._decimals = VarDB(self._DECIMALS, db, value_type=int)
        self._balances = DictDB(self._BALANCES, db, value_type=int)

    def on_install(self, _initialSupply: int, _decimals: int) -> None:
        super().on_install()

        if _initialSupply < 0:
            revert("Initial supply cannot be less than zero")

        if _decimals < 0:
            revert("Decimals cannot be less than zero")

        total_supply = _initialSupply * 10 ** _decimals
        Logger.debug(f'on_install: total_supply={total_supply}', TAG)

        self._total_supply.set(total_supply)
        self._decimals.set(_decimals)
        self._balances[self.msg.sender] = total_supply

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "StakedIcx"

    @external(readonly=True)
    def symbol(self) -> str:
        return "Sicx"

    @external(readonly=True)
    def decimals(self) -> int:
        return self._decimals.get()

    @external(readonly=True)
    def totalSupply(self) -> int:
        return self._total_supply.get()

    @external(readonly=True)
    def balanceOf(self, _owner: Address) -> int:
        return self._balances[_owner]

    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        if _data is None:
            _data = b'None'
        self._transfer(self.msg.sender, _to, _value, _data)

    def _transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        # Checks the sending value and balance.
        if _value < 0:
            revert("Transferring value cannot be less than zero")
        from_balance: int = self._balances[_from]
        if from_balance < _value:
            revert("SICX error :Out of balance")

        self._balances[_from] = from_balance - _value
        self._balances[_to] += _value

        if _to.is_contract:
            # If the recipient is SCORE,
            #   then calls `tokenFallback` to hand over control.
            recipient_score = self.create_interface_score(_to, TokenFallbackInterface)
            recipient_score.tokenFallback(_from, _value, _data)

        # Emits an event log `Transfer`
        self.Transfer(_from, _to, _value, _data)
        Logger.debug(f'Transfer({_from}, {_to}, {_value}, {_data})', TAG)

    @external
    @payable
    def add_collateral(self, _to: Address, _data: bytes = None) -> int:
        self._mint(_to, self.msg.value)
        return self.msg.value

    def _mint(self, account: Address, amount: int):
        """
        Creates amount number of tokens, and assigns to account
        Increases the balance of that account and total supply.
        This is an internal function.
        :param account: The account at which token is to be created.
        :param amount: Number of tokens to be created at the `account`.

        """

        if amount < 0:
            revert(f"Invalid Value")

        self._total_supply.set(self._total_supply.get() + amount)
        self._balances[account] += amount

        # Emits an event log Mint
        self.Mint(account, amount)

    def _burn(self, account: Address, amount: int):
        """
        Creates amount number of tokens, and assigns to account
        Increases the balance of that account and total supply.
        This is an internal function.
        :param account: The account at which token is to be created.
        :param amount: Number of tokens to be created at the `account`.

        """

        if amount < 0:
            revert(f"Invalid Value")

        self._total_supply.set(self._total_supply.get() - amount)
        self._balances[account] -= amount

        # Emits an event log Mint
        self.Burn(account, amount)
