from iconservice import *

TAG = "oToken"


def only_lending_pool(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.getLendingPool():
            revert(f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} (liquidation){self.getLendingPool()}")
        return func(self, *args, **kwargs)

    return __wrapper


def only_liquidation(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.getLiquidation():
            revert(f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} (liquidation){self.getLiquidation()}")
        return func(self, *args, **kwargs)

    return __wrapper


def only_owner(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.owner:
            revert(f"{TAG}: "f"SenderNotScoreOwnerError: (sender){self.msg.sender} (owner){self.owner}")
        return func(self, *args, **kwargs)

    return __wrapper
