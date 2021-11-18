from iconservice import *
from .IRC2 import IRC2


class IRC2Burnable(IRC2):
	"""
	Implementation of IRC2Burnable
	"""

	@external
	def burn(self, _amount: int, _data: bytes = None) -> None:
		"""
		Burns `_amount` number of tokens.
		Decreases the balance of that account and total supply.
		See {IRC2-_burn}

		:param _amount: Number of tokens to be burned from this account.
		:param _data:
		"""
		if _data is None:
			_data = b'Omm token burnt'
		self._burn(self.msg.sender, _amount, _data)

