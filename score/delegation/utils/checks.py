from iconservice import *

TAG = 'Delegation'


def only_owner(func):
    if not isfunction(func):
        revert(f'{TAG}'
               'NotAFunctionError')

    @wraps(func)
    def __wrapper(self: object, *args, **kwargs):
        if self.msg.sender != self.owner:
            revert(f'{TAG}: '
                   'SenderNotScoreOwnerError')
        return func(self, *args, **kwargs)

    return __wrapper
