from iconservice import *

TAG = 'PriceOracle'

#Address
BAND_ORACLE = "bandOracle"
LENDING_POOL_DATA_PROVIDER = "lendingPoolDataProvider"
ADDRESS_PROVIDER = "addressProvider"

def only_owner(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.owner:
            revert(f"{TAG}: SenderNotScoreOwnerError: (sender){self.msg.sender} (owner){self.owner}")

        return func(self, *args, **kwargs)

    return __wrapper

def origin_owner(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.tx.origin != self.owner:
            revert(f"{TAG}: "f"SenderNotScoreOwnerError: (sender){self.tx.origin} (owner){self.owner}")
        return func(self, *args, **kwargs)

    return __wrapper
