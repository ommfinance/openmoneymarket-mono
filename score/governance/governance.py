from .utils.checks import *


# An interface to Rewards
class RewardInterface(InterfaceScore):
    @interface
    def setStartTimestamp(self, _timestamp: int):
        pass

class Governance(IconScoreBase):
    REWARDS = 'rewards'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._rewards = VarDB(self.REWARDS, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "OmmGovernanceManager"

    @only_owner
    @external
    def setRewards(self, _address: Address):
        self._rewards.set(_address)

    @external(readonly=True)
    def getRewards(self) -> Address:
        return self._rewards.get()

    @only_owner
    @external
    def setStartTimestamp(self, _timestamp: int) -> None:
        rewards = self.create_interface_score(self._rewards.get(), RewardInterface)
        rewards.setStartTimestamp(_timestamp)
