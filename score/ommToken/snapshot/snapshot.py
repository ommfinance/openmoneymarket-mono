from iconservice import *

from .snapshot_db import SnapshotDB


class StakedDetail(TypedDict):
    total_staked_balance: int
    user_staked_balanced: int


class Snapshot(IconScoreBase):

    @abstractmethod
    def on_install(self, **kwargs) -> None:
        super().on_install(**kwargs)

    @abstractmethod
    def on_update(self, **kwargs) -> None:
        super().on_update(**kwargs)
        self._snapshot.set_address(self.address)

    @abstractmethod
    def __init__(self, _name: str, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._snapshot = SnapshotDB(_name, db)

    @eventlog
    def SnapshotCreated(self, _owner: Address, _user_before_staked: int, _user_after_staked: int):
        pass

    def _is_snapshot_exists(self, _owner: Address) -> bool:
        return self._snapshot.is_snapshot_exists(_owner)

    def _create_initial_snapshot(self, _owner: Address, _timestamp: int, _user_staked_balance: int) -> None:
        """
        create initial snapshot if not exists
        :param _owner:
        :param _timestamp:
        :param _user_staked_balance:
        :return: None
        """
        if not self._is_snapshot_exists(_owner) and _user_staked_balance > 0:
            self._snapshot.create_checkpoints(_owner, _timestamp, _user_staked_balance)

    def _createSnapshot(self, _owner: Address, _user_old_staked_balance: int, _user_new_staked_balance: int,
                        _total_staked_balance: int) -> None:
        """
        Create snapshot for _owner with curren staked
        :param _owner: The address of the account to set
        :return: None
        """
        _now = self.now()
        self._snapshot.create_checkpoints(_owner, _now, _user_new_staked_balance)
        self._snapshot.create_total_checkpoints(_now, _total_staked_balance)

        self.SnapshotCreated(_owner, _user_old_staked_balance, _user_new_staked_balance)

    @abstractmethod
    def stakedBalanceOfAt(self, _owner: Address, _timestamp: int) -> int:
        return self._snapshot.get_staked_at(_owner, _timestamp)

    @external(readonly=True)
    def totalStakedBalanceOfAt(self, _timestamp: int) -> int:
        return self._snapshot.get_total_staked(_timestamp)
