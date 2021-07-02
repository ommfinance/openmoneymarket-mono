from iconservice import *

TAG = "OmmRewards"


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
        if self.msg.sender != self._governanceAddress.get():
            revert(f"{TAG}: "f"SenderNotGovernanceError: (sender){self.msg.sender} (governance){self._governanceAddress.get()}")

        return func(self, *args, **kwargs)

    return __wrapper


def only_admin(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self._admin.get():
            revert(f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} (admin){self._admin.get()}")

        return func(self, *args, **kwargs)

    return __wrapper
