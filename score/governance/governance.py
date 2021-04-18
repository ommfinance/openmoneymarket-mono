from iconservice import *
from .utils.checks import * 

TAG = 'Governance'

# An interface to Rewards
class RewardInterface(InterfaceScore):
    @interface
    def setStartTimestamp(self, _timestamp: int):
        pass

# An interface to Snapshot
class SnapshotInterface(InterfaceScore):
    @interface
    def setStartTimestamp(self, _timestamp: int):
        pass


class Governance(IconScoreBase):

    REWARDS = 'rewards'
    SNAPSHOT = 'snapshot'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._rewards = VarDB(self.REWARDS, db, value_type = Address)
        self._snapshot = VarDB(self.SNAPSHOT, db, value_type = Address)


    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str :
        return "OmmGovernanceManager" 
        
    @only_owner
    @external
    def setSnapshot(self, _address: Address):
        self._snapshot.set(_address)

    @external(readonly=True)
    def getSnapshot(self) -> Address:
        return self._snapshot.get()

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
        snapshot = self.create_interface_score(self._snapshot.get(), SnapshotInterface)
        rewards = self.create_interface_score(self._rewards.get(), RewardInterface)
        snapshot.setStartTimestamp(_timestamp)
        rewards.setStartTimestamp(_timestamp)


