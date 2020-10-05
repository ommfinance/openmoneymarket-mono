from iconservice import *
from .IIRC2 import TokenStandard

TAG = 'OToken'

# An interface of tokenFallback.
# Receiving SCORE that has implemented this interface can handle
# the receiving or further routine.
class TokenFallbackInterface(InterfaceScore):
    @interface
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        pass


class OToken(IconScoreBase, TokenStandard):
    '''
    Implementation of IRC2
    '''
    _NAME = 'token_name'
    _SYMBOL = 'token_symbol'
    _DECIMALS = 'decimals'
    _TOTAL_SUPPLY = 'total_supply'
    _BALANCES = 'balances'

    def __init__(self, db: IconScoreDatabase) -> None:
        '''
        Varible Definition
        '''
        super().__init__(db)

        self._name = VarDB(self._NAME, db, value_type=str)
        self._symbol = VarDB(self._SYMBOL, db, value_type=str)
        self._decimals = VarDB(self._DECIMALS, db, value_type=int)
        self._total_supply = VarDB(self._TOTAL_SUPPLY, db, value_type=int)
        self._balances = DictDB(self._BALANCES, db, value_type=int)
        self._allowances = DictDB(self._ALLOWANCES,db,value_type=int,depth=2)

    def on_install(self, _name:str, _symbol:str, _decimals:int = 18) -> None:
        '''
        Variable Initialization.
        :param _tokenName: The name of the token.
        :param _symbolName: The symbol of the token.
        :param _decimals: The number of decimals. Set to 18 by default.
    
        '''
        super().on_install()

        if (len(_symbol) <= 0):
            revert(f"Invalid Symbol name")
            
        if (len(_name) <= 0):
            revert(f"Invalid Token Name")
        
            
        if _decimals < 0:
            revert(f"Decimals cannot be less than zero")

        self._name.set(_name)
        self._symbol.set(_symbol)
        self._decimals.set(_decimals)
        self._total_supply.set(0)

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to:  Address, _value:  int, _data:  bytes): 
        pass

    @eventlog(indexed=1)
    def Mint(self, account:Address, amount: int):
        pass

    @eventlog(indexed=1)
    def Burn(self, account: Address, amount: int):
        pass

    @external(readonly=True)
    def name(self) -> str:
        '''
        Returns the name of the token 
        '''
        return self._name.get()

    @external(readonly=True)
    def symbol(self) -> str:
        '''
        Returns the symbol of the token 
        '''
        return self._symbol.get()

    @external(readonly=True)
    def decimals(self) -> int:
        '''
        Returns the number of decimals
        For example, if the decimals = 2, a balance of 25 tokens 
        should be displayed to the user as (25 * 10 ** 2)
        Tokens usually opt for value of 18. It is also the IRC2 
        uses by default. It can be changed by passing required 
        number of decimals during initialization. 
        '''
        return self._decimals.get()

    @external(readonly=True)
    def totalSupply(self) -> int:
        '''
        Returns the total number of tokens in existence
        '''
        return self._total_supply.get()

    # This will always include accured interest as a computated value
    @external(readonly = True)
    def balanceOf(self, _account: Address) -> int:
        pass

    # This shows the state updated balance and includes the accured interest upto the most recent computation initiated by the user transaction
    @external(readonly = True)
    def principalBalanceOf(self, _account: Address) -> int:
        pass


    # The transfer is only allowed if transferring this amount of the underlying collateral doesn't bring the health factor below 1
    @external(readonly = True)
    def isTransferAllowed(self, _account: Address, _amount: int) -> bool:
        pass

    # This returns the most recent cummulative index for the user
    @external(readonly = True)
    def getUserIndex(self, _account: Address) -> int:
        pass

    @external
    def redeem(self, _amount: int ) -> None:
        '''
        Redeems certain amount of tokens to get the equivalent amount of underlying asset.
        
        :param _amount: The amount of oToken.
    
        '''
        pass
    
    @external
    def mintOnDeposit(self, _account: Address, _amount: int) -> None:
        pass

    @external
    def burnOnLiquidation(self, _account: Address, _value: int) -> None:
        pass
    
    # This may not be required as we only allow collateral as an asset that can be received on liquidation
    @external
    def transferOnLiquidation(self, _from: Address, _to: Address, _value: int) -> None:
        pass
    
    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        '''
        Transfers certain amount of tokens from sender to the reciever.
        
        :param _to: The account to which the token is to be transferred.
        :param _value: The no. of tokens to be transferred.
        :param _data: Any information or message 
        '''
        if _data is None:
            _data = b'None'
        self._transfer(self.msg.sender, _to, _value, _data)    

    def _transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        '''
        Transfers certain amount of tokens from sender to the recepient.
        This is an internal function.
        :param _from: The account from which the token is to be transferred.
        :param _to: The account to which the token is to be transferred.
        :param _value: The no. of tokens to be transferred.
        :param _data: Any information or message 
        '''
        if _value < 0 :
            revert(f"Transferring value cannot be less than 0.")
            
        if self._balances[_from] < _value :
            revert(f"Insufficient balance.")

        self._balances[_from] -=  _value
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
       
    def _mint(self, account:Address, amount:int) -> bool:
        '''
        Creates amount number of tokens, and assigns to account
        Increases the balance of that account and total supply.
        This is an internal function.
        :param account: The account at which token is to be created.
        :param amount: Number of tokens to be created at the `account`.
       
        '''

        if amount <= 0:
            revert(f"Invalid Value")

        self._total_supply.set(self._total_supply.get() + amount)
        self._balances[account] +=  amount      

        # Emits an event log Mint
        self.Mint(account, amount)
        
    def _burn(self, account: Address, amount: int) -> None:
        '''
        Destroys `amount` number of tokens from `account`
        Decreases the balance of that `account` and total supply.
        This is an internal function.
        :param account: The account at which token is to be destroyed.
        :param amount: The `amount` of tokens of `account` to be destroyed.
       
        '''

        if amount <= 0:
            revert(f"Invalid Value")
            
        self._total_supply.set(self._total_supply.get() - amount)
        self._balances[account] -= amount
        
        # Emits an event log Burn
        self.Burn(account, amount)