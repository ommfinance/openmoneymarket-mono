from iconservice import *

TAG = "OmmRewards"
STAKED_LP = 'stakedLp'
LENDING_POOL_DATA_PROVIDER = 'lendingPoolDataProvider'
OMM_TOKEN = 'ommToken'
WORKER_TOKEN = 'workerToken'
DAO_FUND = 'daoFund'


def only_owner(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.owner:
            revert(f"{TAG}: "f"SenderNotScoreOwnerError: (sender){self.msg.sender} (owner){self.owner}")

        return func(self, *args, **kwargs)

    return __wrapper


def only_governance(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self._addresses['governance']:
            revert(f"{TAG}: "f"SenderNotGovernanceError: (sender){self.msg.sender} (governance){self._governanceAddress.get()}")

        return func(self, *args, **kwargs)

    return __wrapper


def only_lending_pool(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self._lendingPool.get():
            revert(
                f"{TAG}: "f"SenderNotLendingPoolError: (sender){self.msg.sender} (lendingPool){self._lendingPool.get()}")

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