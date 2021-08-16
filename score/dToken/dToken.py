from .IIRC2 import TokenStandard
from .addresses import *
from .utils.math import *


class DToken(TokenStandard, Addresses):
    """
    Implementation of IRC2
    """
    _NAME = 'token_name'
    _SYMBOL = 'token_symbol'
    _DECIMALS = 'decimals'
    _TOTAL_SUPPLY = 'total_supply'
    _BALANCES = 'balances'
    _USER_INDEXES = 'user_indexes'

    def __init__(self, db: IconScoreDatabase) -> None:
        """
        Variable Definition
        """
        super().__init__(db)

        self._name = VarDB(self._NAME, db, value_type=str)
        self._symbol = VarDB(self._SYMBOL, db, value_type=str)
        self._decimals = VarDB(self._DECIMALS, db, value_type=int)
        self._totalSupply = VarDB(self._TOTAL_SUPPLY, db, value_type=int)
        self._balances = DictDB(self._BALANCES, db, value_type=int)
        self._userIndexes = DictDB(self._USER_INDEXES, db, value_type=int)

    def on_install(self, _addressProvider: Address, _name: str, _symbol: str, _decimals: int = 18) -> None:
        """
        Variable Initialization.
        :param _addressProvider: the address of addressProvider
        :param _name: The name of the token.
        :param _symbol: The symbol of the token.
        :param _decimals: The number of decimals. Set to 18 by default.

        """
        super().on_install(_addressProvider)

        if len(_symbol) <= 0:
            revert(f"Invalid Symbol name")

        if len(_name) <= 0:
            revert(f"Invalid Token Name")

        if _decimals < 0:
            revert(f"Decimals cannot be less than zero")

        self._name.set(_name)
        self._symbol.set(_symbol)
        self._decimals.set(_decimals)
        self._totalSupply.set(0)

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        pass

    @eventlog(indexed=3)
    def MintOnBorrow(self, _from: Address, _value: int, _fromBalanceIncrease: int, _fromIndex: int):
        pass

    @eventlog(indexed=3)
    def BurnOnRepay(self, _from: Address, _value: int, _fromBalanceIncrease: int, _fromIndex: int):
        pass

    @eventlog(indexed=3)
    def BurnOnLiquidation(self, _from: Address, _value: int, _fromBalanceIncrease: int, _fromIndex: int):
        pass

    @external(readonly=True)
    def name(self) -> str:
        """
        Returns the name of the token
        """
        return self._name.get()

    @external(readonly=True)
    def symbol(self) -> str:
        """
        Returns the symbol of the token
        """
        return self._symbol.get()

    @external(readonly=True)
    def decimals(self) -> int:
        """
        Returns the number of decimals
        For example, if the decimals = 2, a balance of 25 tokens
        should be displayed to the user as (25 * 10 ** 2)
        Tokens usually opt for value of 18. It is also the IRC2
        uses by default. It can be changed by passing required
        number of decimals during initialization.
        """
        return self._decimals.get()

    @external(readonly=True)
    def getUserBorrowCumulativeIndex(self, _user: Address) -> int:
        return self._userIndexes[_user]

    def _calculateCumulatedBalanceInternal(self, _user: Address, _balance: int) -> int:
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], LendingPoolCoreInterface)
        userIndex = self._userIndexes[_user]
        if userIndex == 0:
            return _balance
        else:
            decimals = self._decimals.get()
            balance = exaDiv(
                exaMul(convertToExa(_balance, decimals), core.getNormalizedDebt(self._addresses[RESERVE])),
                userIndex)
            return convertExaToOther(balance, decimals)

    # This will always include accrued interest as a computed value
    @external(readonly=True)
    def balanceOf(self, _owner: Address) -> int:
        currentPrincipalBalance = self.principalBalanceOf(_owner)

        balance = self._calculateCumulatedBalanceInternal(_owner, currentPrincipalBalance)
        return balance

    # This shows the state updated balance and includes the accrued interest upto the most recent computation initiated by the user transaction
    @external(readonly=True)
    def principalBalanceOf(self, _user: Address) -> int:
        return self._balances[_user]

    @external(readonly=True)
    def principalTotalSupply(self) -> int:
        return self._totalSupply.get()

    @external(readonly=True)
    def getPrincipalSupply(self, _user: Address) -> SupplyDetails:
        return {
            "decimals": self.decimals(),
            'principalUserBalance': self.principalBalanceOf(_user),
            'principalTotalSupply': self.principalTotalSupply()
        }

    @external(readonly=True)
    def totalSupply(self) -> int:
        """
        Returns the total number of tokens in existence

        """
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], LendingPoolCoreInterface)
        borrowIndex = core.getReserveBorrowCumulativeIndex(self._addresses[RESERVE])
        principalTotalSupply = self.principalTotalSupply()
        if borrowIndex == 0:
            return self._totalSupply.get()
        else:
            decimals = self._decimals.get()
            balance = exaDiv(
                exaMul(convertToExa(principalTotalSupply, decimals), core.getNormalizedDebt(self._addresses[RESERVE])),
                borrowIndex)
            return convertExaToOther(balance, decimals)

    def _resetDataOnZeroBalanceInternal(self, _user: Address) -> None:
        self._userIndexes[_user] = 0

    def _mintInterestAndUpdateIndex(self, _user: Address, _balanceIncrease: int):
        if _balanceIncrease > 0:
            self._mint(_user, _balanceIncrease)
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], LendingPoolCoreInterface)
        userIndex = core.getReserveBorrowCumulativeIndex(self._addresses[RESERVE])
        self._userIndexes[_user] = userIndex

    @only_lending_pool_core
    @external
    def mintOnBorrow(self, _user: Address, _amount: int, _balanceIncrease: int):
        beforeTotalSupply = self.principalTotalSupply()
        beforeUserSupply = self.principalBalanceOf(_user)
        self._mintInterestAndUpdateIndex(_user, _balanceIncrease)
        self._mint(_user, _amount)
        self._handleActions(_user, beforeUserSupply, beforeTotalSupply)
        self.MintOnBorrow(_user, _amount, _balanceIncrease, self._userIndexes[_user])

    def _handleActions(self, _user, _user_balance, _total_supply):
        _userDetails = {
            "_user": _user,
            "_userBalance": _user_balance,
            "_totalSupply": _total_supply,
            "_decimals": self.decimals(),
        }
        rewards = self.create_interface_score(self._addresses[REWARDS], DistributionManager)
        rewards.handleAction(_userDetails)

    @only_lending_pool_core
    @external
    def burnOnRepay(self, _user: Address, _amount: int, _balanceIncrease: int):
        beforeTotalSupply = self.principalTotalSupply()
        beforeUserSupply = self.principalBalanceOf(_user)
        self._mintInterestAndUpdateIndex(_user, _balanceIncrease)
        self._burn(_user, _amount, b'loanRepaid')

        self._handleActions(_user, beforeUserSupply, beforeTotalSupply)

        if self.principalBalanceOf(_user) == 0:
            self._resetDataOnZeroBalanceInternal(_user)
        self.BurnOnRepay(_user, _amount, _balanceIncrease, self._userIndexes[_user])

    @only_lending_pool_core
    @external
    def burnOnLiquidation(self, _user: Address, _amount: int, _balanceIncrease: int) -> None:
        beforeTotalSupply = self.principalTotalSupply()
        beforeUserSupply = self.principalBalanceOf(_user)
        self._mintInterestAndUpdateIndex(_user, _balanceIncrease)
        self._burn(_user, _amount, b'userLiquidated')

        self._handleActions(_user, beforeUserSupply, beforeTotalSupply)

        if self.principalBalanceOf(_user) == 0:
            self._resetDataOnZeroBalanceInternal(_user)
        self.BurnOnLiquidation(_user, _amount, _balanceIncrease, self._userIndexes[_user])

    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        """
        Transfers certain amount of tokens from sender to the receiver.

        :param _to: The account to which the token is to be transferred.
        :param _value: The no. of tokens to be transferred.
        :param _data: Any information or message
        """
        revert(f'{TAG}: Transfer not allowed in debt token ')

    def _mint(self, account: Address, amount: int, data: bytes = None) -> None:
        """
        Creates amount number of tokens, and assigns to account
        Increases the balance of that account and total supply.
        This is an internal function.
        :param account: The account at which token is to be created.
        :param amount: Number of tokens to be created at the `account`.

        """
        if data is None:
            data = b'mint'

        if amount < 0:
            revert(f'{TAG}: 'f'Invalid value: {amount} to mint')

        self._totalSupply.set(self._totalSupply.get() + amount)
        self._balances[account] += amount

        # Emits an event log Mint
        self.Transfer(ZERO_SCORE_ADDRESS, account, amount, data)

    def _burn(self, account: Address, amount: int, data: bytes = None) -> None:
        """
        Destroys `amount` number of tokens from `account`
        Decreases the balance of that `account` and total supply.
        This is an internal function.
        :param account: The account at which token is to be destroyed.
        :param amount: The `amount` of tokens of `account` to be destroyed.

        """
        if data is None:
            data = b'burn'
        totalSupply = self._totalSupply.get()
        userBalance = self._balances[account]
        if amount <= 0:
            revert(f'{TAG}: 'f'Invalid value: {amount} to burn')
        if amount > totalSupply:
            revert(f'{TAG}:'
                   f'{amount} is greater than total supply :{totalSupply}')
        if amount > userBalance:
            revert(f'{TAG}: Cannot burn more than user balance. Amount to burn: {amount} User Balance: {userBalance}')

        self._totalSupply.set(totalSupply - amount)
        self._balances[account] -= amount

        # Emits an event log Burn
        self.Transfer(account, ZERO_SCORE_ADDRESS, amount, data)

    @external(readonly=True)
    def getTotalStaked(self) -> TotalStaked:
        """
        return total supply for reward distribution
        :return: total supply
        """
        return {
            "decimals": self.decimals(),
            "totalStaked": self.totalSupply()
        }
