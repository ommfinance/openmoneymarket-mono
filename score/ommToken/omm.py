from iconservice import *
from .tokens.IRC2mintable import IRC2Mintable

TAG = 'OMM'

TOKEN_NAME = 'OmmToken'
SYMBOL_NAME = 'OMM'


class OmmToken(IRC2Mintable):

    def on_install(self) -> None:
        super().on_install(TOKEN_NAME, SYMBOL_NAME)
