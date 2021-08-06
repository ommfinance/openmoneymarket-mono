from iconservice import *

TAG = "Omm Rewards"
STAKED_LP = 'stakedLP'
LENDING_POOL_DATA_PROVIDER = 'lendingPoolDataProvider'
OMM_TOKEN = 'ommToken'
WORKER_TOKEN = 'workerToken'
DAO_FUND = 'daoFund'
GOVERNANCE = 'governance'


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
        _governance=self._addresses[GOVERNANCE]
        if self.msg.sender != _governance:
            revert(
                f"{TAG}: "f"SenderNotGovernanceError: (sender){self.msg.sender} (governance){_governance}")

        return func(self, *args, **kwargs)

    return __wrapper


def only_lending_pool(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        _lendingPool = self._addresses["lendingPool"]
        if self.msg.sender != _lendingPool:
            revert(
                f"{TAG}: "f"SenderNotLendingPoolError: (sender){self.msg.sender} (lendingPool){_lendingPool}")

        return func(self, *args, **kwargs)

    return __wrapper


def only_address_provider(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        addressProvider = self._addressProvider.get()
        if self.msg.sender != addressProvider:
            revert(f"{TAG}: "f"SenderNotAddressProviderError: (sender){self.msg.sender} (address provider){addressProvider}")
        return func(self, *args, **kwargs)

    return __wrapper

def only_staked_lp(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        stakedLP = self._addresses[STAKED_LP]
        if self.msg.sender != stakedLP:
            revert(f"{TAG}: "f"SenderNotAuthorizedError: (sender){self.msg.sender} (stakedLP){stakedLP}")
        return func(self, *args, **kwargs)

    return __wrapper
