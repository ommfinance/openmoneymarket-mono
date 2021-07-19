from iconservice import *

TAG = "LiquidationManager"

# Addresses
LENDING_POOL_DATA_PROVIDER = "lendingPoolDataProvider"
STAKING = "staking"
PRICE_ORACLE = "priceOracle"
LENDING_POOL_CORE = "lendingPoolCore"
FEE_PROVIDER = "feeProvider"


def only_owner(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.owner:
            revert(f"{TAG}: "f"SenderNotScoreOwnerError: (sender){self.msg.sender} (owner){self.owner}")

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
