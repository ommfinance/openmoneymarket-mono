from iconservice import *

TAG = "OmmRewards"
STAKED_LP = 'stakedLP'
LENDING_POOL_DATA_PROVIDER = 'lendingPoolDataProvider'
OMM_TOKEN = 'ommToken'
WORKER_TOKEN = 'workerToken'
DAO_FUND = 'daoFund'
GOVERNANCE = 'governance'
oICX = 'oICX'
oUSDs = 'oUSDS'
oIUSDC = 'oIUSDC'
dICX = 'dICX'
dUSDs = 'dUSDS'
dIUSDC = 'dIUSDC'

AUTHORIZED_ASSETS = [oICX, oUSDs, oIUSDC, dICX, dUSDs, dIUSDC, OMM_TOKEN]


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
        if self.msg.sender != addressProvider:
            revert(f"{TAG}: "f"SenderNotAuthorizedError: (sender){self.msg.sender} (stakedLP){stakedLP}")
        return func(self, *args, **kwargs)

    return __wrapper

def only_owner_or_contracts(func, contracts=[]):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        _user_list = [self.owner]
        for contract in contracts:
            _user_list.append(self._addresses[contract])
        if self.msg.sender not in _user_list:
            revert(
                f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} is not (owner or {contracts.join('or')}){_user_list.join('or')}")

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
