from iconservice import *

TAG = "LendingPoolCore"

# Address
LENDING_POOL = "lendingPool"
LENDING_POOL_DATA_PROVIDER = "lendingPoolDataProvider"
STAKING = "staking"
DELEGATION = "delegation"
LIQUIDATION_MANAGER = "liquidationManager"
FEE_PROVIDER = "feeProvider"
GOVERNANCE = "governance"


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


def only_delegation(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        _delegation = self.getAddress(DELEGATION)
        if self.msg.sender != _delegation:
            revert(f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} (delegation){_delegation}")

        return func(self, *args, **kwargs)

    return __wrapper


def only_liquidation_manager(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        _liquidation = self.getAddress(LIQUIDATION_MANAGER)
        if self.msg.sender != _liquidation:
            revert(f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} (liquidation){_liquidation}")

        return func(self, *args, **kwargs)

    return __wrapper


def only_lending_pool(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        _lendingPool = self.getAddress(LENDING_POOL)
        if self.msg.sender != _lendingPool:
            revert(f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} (lendingPool){_lendingPool}")

        return func(self, *args, **kwargs)

    return __wrapper


def only_governance(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        _governance = self.getAddress(GOVERNANCE)
        if self.msg.sender != _governance:
            revert(f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} (governance){_governance}")

        return func(self, *args, **kwargs)

    return __wrapper
