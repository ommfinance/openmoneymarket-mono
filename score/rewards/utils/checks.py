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


def only_admin(func):
	if not isfunction(func):
		revert("NotAFunctionError")

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if self.msg.sender != self._admin.get():
			revert(f"SenderNotAuthorized: (sender){self.msg.sender} (admin){self._admin.get()}")

		return func(self, *args, **kwargs)
	return __wrapper
