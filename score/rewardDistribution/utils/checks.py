from iconservice import *

TAG = "OmmRewards"
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


def origin_owner(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.tx.origin != self.owner:
            revert(f"{TAG}: "f"SenderNotScoreOwnerError: (sender){self.tx.origin} (owner){self.owner}")
        return func(self, *args, **kwargs)

    return __wrapper


def only_stake_lp_or_omm(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        _stakedLp = self._addresses[STAKED_LP]
        _omm = self._addresses["ommToken"]
        if self.msg.sender not in [_stakedLp, _omm]:
            revert(
                f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} is not (stakedLp or ommToken){_stakedLp} or {_omm}")

        return func(self, *args, **kwargs)

    return __wrapper
