from iconservice import *

TAG = "OmmToken"


def only_owner(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.owner:
            revert(f"{TAG}: "f"SenderNotScoreOwnerError: (sender){self.msg.sender} (owner){self.owner}")

        return func(self, *args, **kwargs)

    return __wrapper


def only_admin(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self._admin.get():
            revert(f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} (admin){self._admin.get()}")

        return func(self, *args, **kwargs)

    return __wrapper


def only_lending_pool(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        _lendingPool=self._addresses["lendingPool"]
        if self.msg.sender != _lendingPool:
            revert(f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} (lendingPool){_lendingPool}")

        return func(self, *args, **kwargs)

    return __wrapper

def origin_owner(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.tx.origin != self.owner:
            revert(f"{TAG}: "f"SenderNotScoreOwnerError: (sender){self.txn.origin} (owner){self.owner}")
        return func(self, *args, **kwargs)

    return __wrapper