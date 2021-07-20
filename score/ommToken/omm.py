from ommToken.utils.RewardRecipientToken import RewardRecipientToken
from .tokens.IRC2mintable import IRC2Mintable
from iconservice import *

TOKEN_NAME = 'OmmToken'
SYMBOL_NAME = 'OMM'


class OmmToken(IRC2Mintable, RewardRecipientToken):

    def on_install(self) -> None:
        super().on_install(TOKEN_NAME, SYMBOL_NAME)

    @external(readonly=True)
    def getTotalStakedBalance(self, _asset: Address) -> int:
        return self._total_staked_balance.get()
