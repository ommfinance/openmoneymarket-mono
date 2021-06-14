from .IIRC2 import TokenStandard
from .Math import *
from .utils.checks import *


class SupplyDetails(TypedDict):
    principalUserBalance: int
    principalTotalSupply: int


class LendingPoolCoreInterface(InterfaceScore):
    @interface
    def getNormalizedIncome(self, _reserve: Address) -> int:
        pass

    @interface
    def getReserveLiquidityCumulativeIndex(self, _reserve: Address) -> int:
        pass


class DataProviderInterface(InterfaceScore):
    @interface
    def balanceDecreaseAllowed(self, _underlyingAssetAddress: Address, _user: Address, _amount: int):
        pass


class LendingPoolInterface(InterfaceScore):
    @interface
    def redeemUnderlying(self, _reserve: Address, _user: Address, _amount: int, _oTokenbalanceAfterRedeem: int):
        pass


# An interface of tokenFallback.
# Receiving SCORE that has implemented this interface can handle
# the receiving or further routine.
class TokenFallbackInterface(InterfaceScore):
    @interface
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        pass


class OToken(IconScoreBase, TokenStandard):
    """
    Implementation of IRC2
    """
    _NAME = 'token_name'
    _SYMBOL = 'token_symbol'
    _DECIMALS = 'decimals'
    _TOTAL_SUPPLY = 'total_supply'
    _BALANCES = 'balances'
    _CORE_ADDRESS = 'core_address'
    _RESERVE_ADDRESS = 'reserve_address'
    _DATA_PROVIDER = 'data_provider'
    _LENDING_POOL = 'lending_pool'
    _LIQUIDATION = 'liquidation'
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
        self._coreAddress = VarDB(self._CORE_ADDRESS, db, Address)
        self._reserveAddress = VarDB(self._RESERVE_ADDRESS, db, Address)
        self._dataProviderAddress = VarDB(self._DATA_PROVIDER, db, value_type=Address)
        self._lendingPoolAddress = VarDB(self._LENDING_POOL, db, value_type=Address)
        self._liquidation = VarDB(self._LIQUIDATION, db, value_type=Address)
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
    def Redeem(self, _from: Address, _value: int, _fromBalanceIncrease: int, _fromIndex: int):
        pass

    @eventlog(indexed=3)
    def MintOnDeposit(self, _from: Address, _value: int, _fromBalanceIncrease: int, _fromIndex: int):
        pass

    @eventlog(indexed=3)
    def BurnOnLiquidation(self, _from: Address, _value: int, _fromBalanceIncrease: int, _fromIndex: int):
        pass

    @eventlog(indexed=3)
    def BalanceTransfer(self, _from: Address, _to: Address, _value: int, _fromBalanceIncrease: int,
                        _toBalanceIncrease: int, _fromIndex: int, _toIndex: int):
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
    def principalTotalSupply(self) -> int:
        return self._totalSupply.get()

    @external(readonly=True)
    def totalSupply(self) -> int:
        """
        Returns the total number of tokens in existence

        """
        core = self.create_interface_score(self.getLendingPoolCore(), LendingPoolCoreInterface)
        borrowIndex = core.getReserveLiquidityCumulativeIndex(self._reserveAddress.get())
        principalTotalSupply = self.principalTotalSupply()
        if borrowIndex == 0:
            return self._totalSupply.get()
        else:
            decimals = self._decimals.get()
            balance = exaDiv(
                exaMul(convertToExa(principalTotalSupply, decimals), core.getNormalizedIncome(self.getReserve())),
                borrowIndex)
            return convertExaToOther(balance, decimals)

    @only_owner
    @external
    def setLendingPoolCore(self, _address: Address):
        self._coreAddress.set(_address)

    @external(readonly=True)
    def getLendingPoolCore(self) -> Address:
        return self._coreAddress.get()

    @only_owner
    @external
    def setLiquidation(self, _address: Address):
        self._liquidation.set(_address)

    @external(readonly=True)
    def getLiquidation(self) -> Address:
        return self._liquidation.get()

    @only_owner
    @external
    def setReserve(self, _address: Address):
        self._reserveAddress.set(_address)

    @external(readonly=True)
    def getReserve(self) -> Address:
        return self._reserveAddress.get()

    @only_owner
    @external
    def setLendingPoolDataProvider(self, _address: Address):
        self._dataProviderAddress.set(_address)

    @external(readonly=True)
    def getLendingPoolDataProvider(self) -> Address:
        return self._dataProviderAddress.get()

    @only_owner
    @external
    def setLendingPool(self, _address: Address):
        self._lendingPoolAddress.set(_address)

    @external(readonly=True)
    def getLendingPool(self) -> Address:
        return self._lendingPoolAddress.get()

    @external(readonly=True)
    def getUserLiquidityCumulativeIndex(self, _user: Address) -> int:
        return self._userIndexes[_user]

    def _calculateCumulatedBalanceInternal(self, _user: Address, _balance: int) -> int:
        core = self.create_interface_score(self.getLendingPoolCore(), LendingPoolCoreInterface)
        userIndex = self._userIndexes[_user]

        if userIndex == 0:
            return _balance
        else:
            decimals = self._decimals.get()
            balance = exaDiv(
                exaMul(convertToExa(_balance, decimals), core.getNormalizedIncome(self.getReserve())),
                userIndex)
            return convertExaToOther(balance, decimals)

    def _cumulateBalanceInternal(self, _user: Address) -> dict:
        previousPrincipalBalance = self.principalBalanceOf(_user)
        balanceIncrease = self.balanceOf(_user) - previousPrincipalBalance
        if balanceIncrease > 0:
            self._mint(_user, balanceIncrease)
        core = self.create_interface_score(self.getLendingPoolCore(), LendingPoolCoreInterface)
        userIndex = core.getNormalizedIncome(self.getReserve())
        self._userIndexes[_user] = userIndex
        # self._userIndexes[_user] = 1000000234 * 10 ** 10
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

    # The transfer is only allowed if transferring this amount of the underlying collateral doesn't bring the health factor below 1
    @external(readonly=True)
    def isTransferAllowed(self, _user: Address, _amount: int) -> bool:
        dataProvider = self.create_interface_score(self.getLendingPoolDataProvider(), DataProviderInterface)
        return dataProvider.balanceDecreaseAllowed(self.getReserve(), _user, _amount)

    @external(readonly=True)
    def getPrincipalSupply(self, _user: Address) -> SupplyDetails:
        return {
            'principalUserBalance': self.principalBalanceOf(_user),
            'principalTotalSupply': self.principalTotalSupply()
        }

    @external
    def redeem(self, _amount: int, _waitForUnstaking: bool = False) -> None:
        """
        Redeems certain amount of tokens to get the equivalent amount of underlying asset.

        :param _amount: The amount of oToken.

        """
        if _amount <= 0 and _amount != -1:
            revert(f'{TAG}: '
                   f'Amount: {_amount} to redeem needs to be greater than zero')

        cumulated = self._cumulateBalanceInternal(self.msg.sender)
        currentBalance = cumulated['principalBalance']
        balanceIncrease = cumulated['balanceIncrease']
        index = cumulated['index']
        amountToRedeem = _amount
        if _amount == -1:
            amountToRedeem = currentBalance
        if amountToRedeem > currentBalance:
            revert(f'{TAG}: '
                   f'Redeem amount: {amountToRedeem} is more than user balance {currentBalance} ')
        if not self.isTransferAllowed(self.msg.sender, amountToRedeem):
            revert(f'{TAG}: '
                   f'Transfer of amount {amountToRedeem} to the user is not allowed')
        self._burn(self.msg.sender, amountToRedeem)

        if currentBalance - amountToRedeem == 0:
            self._resetDataOnZeroBalanceInternal(self.msg.sender)
            index = 0

        pool = self.create_interface_score(self.getLendingPool(), LendingPoolInterface)
        pool.redeemUnderlying(self.getReserve(), self.msg.sender, amountToRedeem, currentBalance - amountToRedeem,
                              _waitForUnstaking)
        self.Redeem(self.msg.sender, amountToRedeem, balanceIncrease, index)

    def _resetDataOnZeroBalanceInternal(self, _user: Address) -> None:
        self._userIndexes[_user] = 0

    @only_lending_pool
    @external
    def mintOnDeposit(self, _user: Address, _amount: int) -> None:
        cumulated = self._cumulateBalanceInternal(_user)

        balanceIncrease = cumulated['balanceIncrease']
        index = cumulated['index']
        self._mint(_user, _amount)
        self.MintOnDeposit(_user, _amount, balanceIncrease, index)

    @only_liquidation
    @external
    def burnOnLiquidation(self, _user: Address, _value: int) -> None:
        cumulated = self._cumulateBalanceInternal(_user)
        currentBalance = cumulated['principalBalance']
        balanceIncrease = cumulated['balanceIncrease']
        index = cumulated['index']
        self._burn(_user, _value)
        if currentBalance - _value == 0:
            self._resetDataOnZeroBalanceInternal(_user)
            index = 0
        self.BurnOnLiquidation(_user, _value, balanceIncrease, index)

    def _executeTransfer(self, _from: Address, _to: Address, _value: int):
        fromCumulated = self._cumulateBalanceInternal(_from)
        toCumulated = self._cumulateBalanceInternal(_to)
        fromBalance = fromCumulated['principalBalance']
        fromBalanceIncrease = fromCumulated['balanceIncrease']
        fromIndex = fromCumulated['index']
        toBalanceIncrease = toCumulated['balanceIncrease']
        toIndex = toCumulated['index']

        if fromBalance - _value == 0:
            self._resetDataOnZeroBalanceInternal(_from)

        self.BalanceTransfer(_from, _to, _value, fromBalanceIncrease, toBalanceIncrease, fromIndex, toIndex)

    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        """
        Transfers certain amount of tokens from sender to the receiver.

        :param _to: The account to which the token is to be transferred.
        :param _value: The no. of tokens to be transferred.
        :param _data: Any information or message
        """
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
        """
        if _value < 0:
            revert(f"{TAG}: "
                   f"Transferring value:{_value} cannot be less than 0.")

        if self._balances[_from] < _value:
            revert(f"{TAG}: "
                   f"Token transfer error:Insufficient balance:{self._balances[_from]}")

        if not self.isTransferAllowed(self.msg.sender, _value):
            revert(f"{TAG}: "
                   f"Transfer error:Transfer cannot be allowed")

        self._executeTransfer(_from, _to, _value)
        self._balances[_from] -= _value
        self._balances[_to] += _value

        if _to.is_contract:
            '''
            If the recipient is SCORE,
            then calls `tokenFallback` to hand over control.
            '''
            recipient_score = self.create_interface_score(_to, TokenFallbackInterface)
            recipient_score.tokenFallback(_from, _value, _data)

        # Emits an event log `Transfer`
        self.Transfer(_from, _to, _value, _data)

    def _mint(self, account: Address, amount: int) -> None:
        """
        Creates amount number of tokens, and assigns to account
        Increases the balance of that account and total supply.
        This is an internal function.
        :param account: The account at which token is to be created.
        :param amount: Number of tokens to be created at the `account`.

        """

        if amount < 0:
            revert(f'{TAG}: ',
                   f'Invalid value: {amount} to mint')

        self._totalSupply.set(self._totalSupply.get() + amount)
        self._balances[account] += amount

        # Emits an event log Mint
        self.Transfer(ZERO_SCORE_ADDRESS, account, amount, b'mint')
        self.Mint(account, amount)

    def _burn(self, account: Address, amount: int) -> None:
        """
        Destroys `amount` number of tokens from `account`
        Decreases the balance of that `account` and total supply.
        This is an internal function.
        :param account: The account at which token is to be destroyed.
        :param amount: The `amount` of tokens of `account` to be destroyed.

        """

        if amount <= 0:
            revert(f'{TAG}: ',
                   f'Invalid value: {amount} to burn')

        self._totalSupply.set(self._totalSupply.get() - amount)
        self._balances[account] -= amount

        # Emits an event log Burn
        self.Transfer(account, ZERO_SCORE_ADDRESS, amount, b'burn')
        self.Burn(account, amount)
