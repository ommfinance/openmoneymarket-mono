from iconservice import *


class RewardRecipientToken(InterfaceScore):
    @interface
    def getTotalStakedBalance(self, _asset: Address) -> int:
        pass
