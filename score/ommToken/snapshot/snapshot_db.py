from iconservice import *

TAG = "SnapshotDB"


class SnapshotDB(object):
    _PREFIX = "SnapshotDB_"

    def __init__(self, _key: str, _contract: Address, db: IconScoreDatabase):
        # number of checkpoint for each address (address > checkpoint_count)
        self._checkpoint_count = DictDB(f'{self._PREFIX}{_key}_checkpoint_count', db, value_type=int)
        # checkpoints for marking number of timestamp (address > checkpoint_counter > timestamp)
        self._timestamp_checkpoints = DictDB(f'{self._PREFIX}{_key}_timestamp_checkpoints', db, value_type=int, depth=2)
        # checkpoints for marking number of votes (address > checkpoint_counter > staked)
        self._staked_checkpoints = DictDB(f'{self._PREFIX}{_key}_staked_checkpoints', db, value_type=int, depth=2)

        # checkpoints for marking number of total staked from a given timestamp (timestamp > total_staked)
        self._total_staked_checkpoints = DictDB(f'{self._PREFIX}{_key}_total_staked_checkpoints', db, value_type=int)

        self._contract = _contract

    def is_snapshot_exists(self, _owner: Address) -> bool:
        nCheckpoints = self._checkpoint_count[_owner]
        return nCheckpoints > 0

    def create_total_checkpoints(self, _timestamp: int, _staked: int):
        self.create_checkpoints(self._contract, _timestamp, _staked)

    def create_checkpoints(self, _owner: Address, _timestamp: int, _staked: int):
        """
         Create checkpoint for `_owner` at `_timestamp`
        :param _owner: The address of the account to set
        :param _timestamp: The timestamp number to set the vote balance at
        :param _staked: The staked to set  at
        :return: None
        """
        nCheckpoints = self._checkpoint_count[_owner]
        if nCheckpoints > 0 and self._timestamp_checkpoints[_owner][nCheckpoints - 1] == _timestamp:
            self._staked_checkpoints[_owner][nCheckpoints - 1] = _staked
        else:
            self._checkpoint_count[_owner] = nCheckpoints + 1
            self._timestamp_checkpoints[_owner][nCheckpoints] = _timestamp
            self._staked_checkpoints[_owner][nCheckpoints] = _staked

    def get_current_staked(self, _owner: Address) -> int:
        """
        Gets the current staked balance for `_owner`
        :param _owner: The address to get staked balance
        :return: The number of current staked for `_owner`
        """
        nCheckpoints = self._checkpoint_count[_owner]
        if nCheckpoints > 0:
            return self._staked_checkpoints[_owner][nCheckpoints - 1]
        return 0

    def get_staked_at(self, _owner: Address, _timestamp: int) -> int:
        """
        Determine the prior number of staked for an account as of a timestamp number
        :param _owner: The address of the account to check
        :param _timestamp: The timestamp number to get the vote balance at
        :return: The number of staked the account had as of the given timestamp
        """
        nCheckpoints = self._checkpoint_count[_owner]
        if nCheckpoints == 0:
            return 0
        _latest_timestamp = self._timestamp_checkpoints[_owner][nCheckpoints - 1]
        if _latest_timestamp <= _timestamp:
            return self._staked_checkpoints[_owner][nCheckpoints - 1]
        _initial_timestamp = self._timestamp_checkpoints[_owner][0]
        # if _timestamp is less than _initial_timestamp, there is now staking for user
        if _initial_timestamp > _timestamp:
            return 0

        if _initial_timestamp == _timestamp:
            return self._staked_checkpoints[_owner][0]

        return self._search_for_staked(nCheckpoints, _owner, _timestamp)

    def _search_for_staked(self, _nCheckpoints: int, _owner: Address, _timestamp: int) -> int:
        """
        Binary search for staked
        :param _nCheckpoints: Number of total checkpoints for `_owner`
        :param _owner: The address of the account to check
        :param _timestamp: The timestamp number to get the vote balance at
        :return: The number of staked the account had as of the given timestamp or lower timestamp
        """
        _lower = 0
        _mid = 0
        _upper = _nCheckpoints - 1
        while _upper > _lower:
            _mid = -((_upper + _lower) // -2)  # ceil
            _mid_timestamp = self._timestamp_checkpoints[_owner][_mid]
            if _mid_timestamp == _timestamp:
                return self._staked_checkpoints[_owner][_mid]
            elif _mid_timestamp < _timestamp:
                _lower = _mid
            else:
                _upper = _mid - 1
        return self._staked_checkpoints[_owner][_lower]

    def get_total_staked(self, _timestamp: int) -> int:
        _staked = self._total_staked_checkpoints[_timestamp]
        if _staked:
            return _staked
        return self.get_staked_at(self._contract, _timestamp)

    def set_total_staked(self, _timestamp: int) -> None:
        """
        Determine the prior number of total staked for an account as of a timestamp number
        :param _timestamp: The timestamp number to set the total staked balance at
        """
        if not self._total_staked_checkpoints[_timestamp]:
            _total_staked_on_timestamp = self.get_staked_at(self._contract, _timestamp)
            self._total_staked_checkpoints[_timestamp] = _total_staked_on_timestamp
