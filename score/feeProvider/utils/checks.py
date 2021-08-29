from iconservice import *

TAG = 'Fee Provider'


def only_owner(func):
    if not isfunction(func):
        revert(f"{TAG}: NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.owner:
            revert(f"{TAG}:" f"SenderNotScoreOwnerError: (sender){self.msg.sender} (owner){self.owner}")

        return func(self, *args, **kwargs)

    return __wrapper


def only_address_provider(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        addressProvider = self._addressProvider.get()
        if self.msg.sender != addressProvider:
            revert(
                f"{TAG}: "f"SenderNotAddressProviderError: (sender){self.msg.sender} (address provider){addressProvider}")
        return func(self, *args, **kwargs)

    return __wrapper


def only_governance(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        governance = self._addresses['governance']
        if self.msg.sender != governance:
            revert(
                f"{TAG}: "f"SenderNotGovernanceError: (sender){self.msg.sender} (governance){governance}")
        return func(self, *args, **kwargs)

    return __wrapper
