from iconservice import *

# ================================================
#  Exceptions
# ================================================


class SenderNotScoreOwnerError(Exception):
	pass


class SenderNotAuthorized(Exception):
	pass


class NotAFunctionError(Exception):
	pass


def only_lending_pool(func):
	if not isfunction(func):
		raise NotAFunctionError

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if self.msg.sender != self._lendingPool.get():
			raise SenderNotAuthorized(self.msg.sender)

		return func(self, *args, **kwargs)
	return __wrapper

def only_liquidation_manager(func):
	if not isfunction(func):
		raise NotAFunctionError

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if self.msg.sender != self._liquidation.get():
			raise SenderNotAuthorized(self.msg.sender)

		return func(self, *args, **kwargs)
	return __wrapper

def only_liquidation(func):
	if not isfunction(func):
		raise NotAFunctionError

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if self.msg.sender != self._liquidation.get():
			raise SenderNotAuthorized(self.msg.sender)

		return func(self, *args, **kwargs)
	return __wrapper

def only_delegation(func):
	if not isfunction(func):
		raise NotAFunctionError

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if self.msg.sender != self._delegation.get():
			raise SenderNotAuthorized(self.msg.sender)

		return func(self, *args, **kwargs)
	return __wrapper

def only_owner(func):
	if not isfunction(func):
		raise NotAFunctionError

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		if self.msg.sender != self.owner:
			raise SenderNotScoreOwnerError(self.owner)

		return func(self, *args, **kwargs)
	return __wrapper


def catch_error(func):
	if not isfunction(func):
		raise NotAFunctionError

	@wraps(func)
	def __wrapper(self: object, *args, **kwargs):
		try:
			return func(self, *args, **kwargs)
		except BaseException as e:
			Logger.error(repr(e), TAG)
			try:
				# readonly methods cannot emit eventlogs
				self.ShowException(repr(e))
			except:
				pass
			revert(repr(e))

	return __wrapper
