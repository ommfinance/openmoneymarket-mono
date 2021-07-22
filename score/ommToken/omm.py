from .tokens.IRC2mintable import IRC2Mintable
from iconservice import *

TOKEN_NAME = 'OmmToken'
SYMBOL_NAME = 'OMM'


class SupplyDetails(TypedDict):
    principalUserBalance: int
    principalTotalSupply: int


class OmmToken(IRC2Mintable):

    def on_install(self) -> None:
        super().on_install(TOKEN_NAME, SYMBOL_NAME)

    @external(readonly=True)
    def getPrincipalSupply(self, _user: Address) -> SupplyDetails:
        return {
            "principalUserBalance": self.staked_balanceOf(_user),
            "principalTotalSupply": self.total_staked_balance()
        }
