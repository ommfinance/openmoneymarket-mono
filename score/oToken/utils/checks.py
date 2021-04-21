from iconservice import *


def only_lending_pool(func):
    if not isfunction(func):
        revert('NotAFunctionError')

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.getLendingPool():
            revert('SenderNotAuthorized')
        return func(self, *args, **kwargs)

    return __wrapper


def only_liquidation(func):
    if not isfunction(func):
        revert('NotAFunctionError')

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.getLiquidation():
            revert('SenderNotAuthorized')
        return func(self, *args, **kwargs)

    return __wrapper


def only_owner(func):
    if not isfunction(func):
        revert('NotAFunctionError')

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.owner:
            revert('SenderNotScoreOwnerError')
        return func(self, *args, **kwargs)

    return __wrapper
