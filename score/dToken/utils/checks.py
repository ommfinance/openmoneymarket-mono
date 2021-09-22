from iconservice import *

TAG = "Omm dToken"


def only_lending_pool_core(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self._addresses['lendingPoolCore']:
            revert(
                f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} (lending pool core){self._addresses['lendingPoolCore']}")
        return func(self, *args, **kwargs)

    return __wrapper


def only_address_provider(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        addressProvider = self._addressProvider.get()
        if self.msg.sender != addressProvider:
            revert(f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} (address provider){addressProvider}")
        return func(self, *args, **kwargs)

    return __wrapper
