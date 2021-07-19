from .IIRC2 import TokenStandard
from .Math import *
from .utils.checks import *

REWARDS = 'rewards'
LENDING_POOL_CORE = 'lendingPoolCore'
RESERVE = 'reserve'

class SupplyDetails(TypedDict):
    principalUserBalance: int
    principalTotalSupply: int
    decimals: int


class AddressDetails(TypedDict):
    name: str
    address: Address


class LendingPoolCoreInterface(InterfaceScore):
    @interface
    def getNormalizedDebt(self, _reserve: Address) -> int:
        pass

    @interface
    def getReserveBorrowCumulativeIndex(self, _reserve: int) -> int:
        pass


class DistributionManager(InterfaceScore):
    @interface
    def handleAction(self, _user: Address, _userBalance: int, _totalSupply: int, _asset: Address = None) -> None:
        pass


class TokenFallbackInterface(InterfaceScore):
    @interface
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        pass


class DToken(IconScoreBase, TokenStandard):
    """
    Implementation of IRC2
    """
    _NAME = 'token_name'
    _SYMBOL = 'token_symbol'
    _DECIMALS = 'decimals'
    _TOTAL_SUPPLY = 'total_supply'
    _BALANCES = 'balances'
    _CONTRACTS = 'contracts'
    _ADDRESSES = 'addresses'
    _USER_INDEXES = 'user_indexes'

    def __init__(self, db: IconScoreDatabase) -> None:
        """
        Variable Definition
        """
        super().__init__(db)

        self._name = VarDB(self._NAME, db, value_type=str)
        self._addresses = DictDB(self._ADDRESSES, db, value_type=Address)
        self._contracts = ArrayDB(self._CONTRACTS, db, value_type=str)
        self._symbol = VarDB(self._SYMBOL, db, value_type=str)
        self._decimals = VarDB(self._DECIMALS, db, value_type=int)
        self._totalSupply = VarDB(self._TOTAL_SUPPLY, db, value_type=int)
        self._balances = DictDB(self._BALANCES, db, value_type=int)
        self._userIndexes = DictDB(self._USER_INDEXES, db, value_type=int)

    def on_install(self, _name: str, _symbol: str, _decimals: int = 18) -> None:
        """
        Variable Initialization.
        :param _name: The name of the token.
        :param _symbol: The symbol of the token.
        :param _decimals: The number of decimals. Set to 18 by default.

        """
        super().on_install()

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

    @eventlog(indexed=1)
    def Mint(self, account: Address, amount: int):
        pass

    @eventlog(indexed=1)
    def Burn(self, account: Address, amount: int):
        pass

    @eventlog(indexed=3)
    def MintOnBorrow(self, _from: Address, _value: int, _fromBalanceIncrease: int, _fromIndex: int):
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
                exaMul(convertToExa(_balance, decimals), core.getNormalizedDebt(self.getReserve())),
                userIndex)
            return convertExaToOther(balance, decimals)

    def _cumulateBalanceInternal(self, _user: Address) -> dict:
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], LendingPoolCoreInterface)
        previousUserIndex = self._userIndexes[_user]
        decimals = self._decimals.get()
        previousPrincipalBalance = self.principalBalanceOf(_user)
        if previousUserIndex != 0:
            balanceInExa = exaDiv(
                exaMul(convertToExa(previousPrincipalBalance, decimals),
                       core.getReserveBorrowCumulativeIndex(self.getReserve())), previousUserIndex)
            balance = convertExaToOther(balanceInExa, decimals)
        else:
            balance = previousPrincipalBalance
        balanceIncrease = balance - previousPrincipalBalance
        if balanceIncrease > 0:
            self._mint(_user, balanceIncrease)

        userIndex = core.getReserveBorrowCumulativeIndex(self.getReserve())
        self._userIndexes[_user] = userIndex

        return {
            'previousPrincipalBalance': previousPrincipalBalance,
            'principalBalance': previousPrincipalBalance + balanceIncrease,
            'balanceIncrease': balanceIncrease,
            'index': userIndex
        }

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
            'principalUserBalance': self.principalBalanceOf(_user),
            'principalTotalSupply': self.principalTotalSupply(),
            'decimals': self.decimals()
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
                exaMul(convertToExa(principalTotalSupply, decimals), core.getNormalizedDebt(self.getReserve())),
                borrowIndex)
            return convertExaToOther(balance, decimals)

    def _resetDataOnZeroBalanceInternal(self, _user: Address) -> None:
        self._userIndexes[_user] = 0

    def _mintInterestAndUpdateIndex(self, _user: Address, _balanceIncrease: int):
        if _balanceIncrease > 0:
            self._mint(_user, _balanceIncrease)
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], LendingPoolCoreInterface)
        userIndex = core.getReserveBorrowCumulativeIndex(self.getReserve())
        self._userIndexes[_user] = userIndex

    @only_lending_pool_core
    @external
    def mintOnBorrow(self, _user: Address, _amount: int, _balanceIncrease: int):
        beforeTotalSupply = self.principalTotalSupply()
        beforeUserSupply = self.principalBalanceOf(_user)
        self._mintInterestAndUpdateIndex(_user, _balanceIncrease)
        self._mint(_user, _amount)
        rewards = self.create_interface_score(self._addresses[REWARDS], DistributionManager)
        decimals = self.decimals()
        rewards.handleAction(_user, convertToExa(beforeUserSupply, decimals), convertToExa(beforeTotalSupply, decimals))
        self.MintOnBorrow(_user, _amount, _balanceIncrease, self._userIndexes[_user])

    @only_lending_pool_core
    @external
    def burnOnRepay(self, _user: Address, _amount: int, _balanceIncrease: int):
        beforeTotalSupply = self.principalTotalSupply()
        beforeUserSupply = self.principalBalanceOf(_user)
        self._mintInterestAndUpdateIndex(_user, _balanceIncrease)
        self._burn(_user, _amount, b'loanRepaid')
        rewards = self.create_interface_score(self._addresses[REWARDS], DistributionManager)
        decimals = self.decimals()
        rewards.handleAction(_user, convertToExa(beforeUserSupply, decimals), convertToExa(beforeTotalSupply, decimals))
        if self.principalBalanceOf(_user) == 0:
            self._resetDataOnZeroBalanceInternal(_user)

    @only_lending_pool_core
    @external
    def burnOnLiquidation(self, _user: Address, _amount: int, _balanceIncrease: int) -> None:
        beforeTotalSupply = self.principalTotalSupply()
        beforeUserSupply = self.principalBalanceOf(_user)
        self._mintInterestAndUpdateIndex(_user, _balanceIncrease)
        self._burn(_user, _amount, b'userLiquidated')
        rewards = self.create_interface_score(self._addresses[REWARDS], DistributionManager)
        decimals = self.decimals()
        rewards.handleAction(_user, convertToExa(beforeUserSupply, decimals), convertToExa(beforeTotalSupply, decimals))
        if self.principalBalanceOf(_user) == 0:
            self._resetDataOnZeroBalanceInternal(_user)

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
            revert(f'{TAG}: ',
                   f'Invalid value: {amount} to mint')

        self._totalSupply.set(self._totalSupply.get() + amount)
        self._balances[account] += amount

        # Emits an event log Mint
        self.Transfer(ZERO_SCORE_ADDRESS, account, amount, data)
        self.Mint(account, amount)

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
        if amount <= 0:
            revert(f'{TAG}: ',
                   f'Invalid value: {amount} to burn')
        if amount > totalSupply:
            revert(f'{TAG}:'
                   f'{amount} is greater than total supply :{totalSupply}')

        self._totalSupply.set(self._totalSupply.get() - amount)
        self._balances[account] -= amount

        # Emits an event log Burn
        self.Transfer(account, ZERO_SCORE_ADDRESS, amount, data)
        self.Burn(account, amount)
