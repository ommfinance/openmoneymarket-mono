from iconservice import *

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

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._rewards = VarDB('rewards', db, value_type = Address)
        self._snapshotAddress = VarDB('snapshotAddress', db, value_type = Address)


    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external
    def setSnapshot(self, _val: Address):
        self._snapshotAddress.set(_val)

    @external(readonly=True)
    def getSnapshot(self) -> Address:
        return self._snapshotAddress.get()

    @external
    def setRewards(self, _val: Address):
        self._rewards.set(_val)

    @external(readonly=True)
    def getRewards(self) -> Address:
        return self._rewards.get()

    
    @external
    def setStartTimestamp(self) -> None:
        snapshot = self.create_interface_score(self._snapshotAddress.get(), SnapshotInterface)
        rewards = self.create_interface_score(self._rewards.get(), RewardInterface)
        snapshot.setStartTimestamp(self.now())
        rewards.setStartTimestamp(self.now())


