from iconservice import *
from .IRC2 import IRC2
from ..utils.checks import *


class IRC2Mintable(IRC2):
	"""
	Implementation of IRC2Mintable
	"""

	@external
	@only_rewards
	def mint(self, _amount: int, _data: bytes = None) -> None:
		"""
		Creates `_amount` number of tokens, and assigns to caller account.
		Increases the balance of that account and total supply.
		See {IRC2-_mint}

		:param _amount: Number of tokens to be created at the account.
		:param _data:
		"""
		if _data is None:
			_data = b'minted by reward'
		self._mint(self.msg.sender, _amount, _data)

