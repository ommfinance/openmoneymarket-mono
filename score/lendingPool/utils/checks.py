from iconservice import *

TAG = 'Lending Pool'


def only_owner(func):
    if not isfunction(func):
        revert(f"{TAG}: NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.owner:
            revert(f"{TAG}: SenderNotScoreOwnerError: (sender){self.msg.sender} (owner){self.owner}")

        return func(self, *args, **kwargs)

    return __wrapper


def only_address_provider(func):
    if not isfunction(func):
        revert(f"{TAG}: ""NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        addressProvider = self._addressProvider.get()
        if self.msg.sender != addressProvider:
            revert(f"{TAG}: "f"SenderNotAuthorized: (sender){self.msg.sender} (address provider){addressProvider}")
        return func(self, *args, **kwargs)

    return __wrapper

def only_omm_token(func):
    if not isfunction(func):
        revert(f"{TAG}: NotAFunctionError")

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        _ommToken = self.getAddress('ommToken')
        if self.msg.sender != _ommToken:
            revert(f"{TAG}: SenderNotScoreOwnerError: (sender){self.msg.sender} (omm token){_ommToken}")

        return func(self, *args, **kwargs)

    return __wrapper
