from iconservice import *

TAG = 'Omm Staked Lp'


def only_owner(func):
    if not isfunction(func):
        revert(f'{TAG}'
               'NotAFunctionError')

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.owner:
            revert(f"{TAG}: "f"SenderNotScoreOwnerError: (sender){self.msg.sender} (owner){self.owner}")
        return func(self, *args, **kwargs)

    return __wrapper


def only_dex(func):
    if not isfunction(func):
        revert(f'{TAG}'
               'NotAFunctionError')

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self._addresses['dex']:
            revert(f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} (dex){self._dex.get()}")
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