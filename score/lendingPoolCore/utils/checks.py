from iconservice import *


def only_owner(func):
	if not isfunction(func):
		revert("NotAFunctionError")

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if self.msg.sender != self.owner:
			revert(f"SenderNotScoreOwnerError: (sender){self.msg.sender} (owner){self.owner}")

		return func(self, *args, **kwargs)
	return __wrapper


def only_delegation(func):
	if not isfunction(func):
		revert("NotAFunctionError")

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if self.msg.sender != self._delegation.get():
			revert(f"SenderNotAuthorized: (sender){self.msg.sender} (delegation){self._delegation.get()}")

		return func(self, *args, **kwargs)
	return __wrapper


def only_liquidation_manager(func):
	if not isfunction(func):
		revert("NotAFunctionError")

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if self.msg.sender != self._liquidation.get():
			revert(f"SenderNotAuthorized: (sender){self.msg.sender} (liquidation){self._liquidation.get()}")

		return func(self, *args, **kwargs)
	return __wrapper


def only_lending_pool(func):
	if not isfunction(func):
		revert("NotAFunctionError")

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if self.msg.sender != self._lendingPool.get():
			revert(f"SenderNotAuthorized: (sender){self.msg.sender} (lendingPool){self._lendingPool.get()}")

		return func(self, *args, **kwargs)
	return __wrapper