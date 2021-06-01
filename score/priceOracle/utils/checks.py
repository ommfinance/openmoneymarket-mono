from iconservice import *

TAG = 'PriceOracle'


def only_owner(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.owner:
            revert(f"{TAG}: SenderNotScoreOwnerError: (sender){self.msg.sender} (owner){self.owner}")

        return func(self, *args, **kwargs)

    return __wrapper
