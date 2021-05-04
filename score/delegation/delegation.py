from iconservice import *
from .Math import *
from .utils.checks import *

TAG = 'Delegation'


class PrepDelegations(TypedDict):
    _address: Address
    _votes_in_per: int


class OmmTokenInterface(InterfaceScore):
    @interface
    def details_balanceOf(self, _owner: Address) -> dict:
        pass


class LendingPoolCoreInterface(InterfaceScore):
    @interface
    def updatePrepDelegations(self, _delegations: List[PrepDelegations]):
        pass


class Delegation(IconScoreBase):
    _PREPS = 'preps'
    _USER_PREPS = 'userPreps'
    _PERCENTAGE_DELEGATIONS = 'percentageDelegations'
    _PREP_VOTES = 'prepVotes'
    _USER_VOTES = 'userVotes'
    _TOTAL_VOTES = 'totalVotes'
    _VOTED = 'voted'
    _EQUAL_DISTRIBUTION = 'equalDistribution'
    _OMM_TOKEN = 'ommToken'
    _LENDING_POOL_CORE = 'lendingPoolCore'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._preps = ArrayDB(self._PREPS, db, Address)
        self._userPreps = DictDB(self._USER_PREPS, db, value_type=Address, depth=2)
        self._percentageDelegations = DictDB(self._PERCENTAGE_DELEGATIONS, db, value_type=int, depth=2)
        self._prepVotes = DictDB(self._PREP_VOTES, db, value_type=int)
        self._userVotes = DictDB(self._USER_VOTES, db, value_type=int)
        self._totalVotes = VarDB(self._TOTAL_VOTES, db, value_type=int)
        self._ommToken = VarDB(self._OMM_TOKEN, db, value_type=Address)
        self._lendingPoolCore = VarDB(self._LENDING_POOL_CORE, db, value_type=Address)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @staticmethod
    def _require(_condition: bool, _message: str):
        if not _condition:
            revert(_message)

    @external(readonly=True)
    def name(self) -> str:
        return "OmmDelegation"

    @eventlog(indexed=2)
    def DelegationUpdated(self, _before: str, _after: str):
        pass

    @only_owner
    @external
    def setOmmToken(self, _address: Address):
        self._ommToken.set(_address)

    @external(readonly=True)
    def getOmmToken(self) -> Address:
        return self._ommToken.get()

    @only_owner
    @external
    def setLendingPoolCore(self, _address: Address):
        self._lendingPoolCore.set(_address)

    @external(readonly=True)
    def getLendingPoolCore(self) -> Address:
        return self._lendingPoolCore.get()

    @external
    def clearPrevious(self, _user: Address):
        if self.msg.sender == self._ommToken.get() or self.msg.sender == _user:
            for index in range(5):

                # removing votes
                prep_vote = exaMul(self._percentageDelegations[_user][index], self._userVotes[_user])
                if prep_vote > 0:
                    self._prepVotes[self._userPreps[_user][index]] -= prep_vote

                # resetting the preferences
                self._userPreps[_user][index] = ZERO_SCORE_ADDRESS
                self._percentageDelegations[_user][index] = 0

                # adjusting total votes
                self._totalVotes.set(self._totalVotes.get() - prep_vote)
            self._userVotes[_user] = 0

    @external(readonly=True)
    def getPrepList(self) -> list:
        return [prep for prep in self._preps]

    @external
    def updateDelegations(self, _delegations: List[PrepDelegations] = None, _user: Address = None):
        if _user is not None and self.msg.sender == self._ommToken.get():
            user = _user
        else:
            user = self.msg.sender

        total_percentage = 0
        initialDelegation = self.computeDelegationPercentages()
        delegationBefore = f'{initialDelegation}'
        if _delegations is None:
            delegations = self.getUserDelegationDetails(user)
        else:
            self._require(len(_delegations) <= 5,
                          "Delegation SCORE : Add error-Cant take more than 5 preps for a user ")
            delegations = _delegations

        omm_token = self.create_interface_score(self._ommToken.get(), OmmTokenInterface)
        user_staked_token = omm_token.details_balanceOf(user)['stakedBalance']
        if len(delegations) > 0:
            # resetting previous delegation preferences
            self.clearPrevious(user)

            for index, delegation in enumerate(delegations):
                address: Address = delegation['_address']
                votes: int = delegation['_votes_in_per']

                # adding delegation to new preps
                prep_vote = exaMul(votes, user_staked_token)
                self._prepVotes[address] += prep_vote

                # updating prep list
                if address not in self._preps:
                    self._preps.put(address)

                # updating the delegation preferences
                self._userPreps[user][index] = address
                self._percentageDelegations[user][index] = votes

                # adjusting total votes
                self._totalVotes.set(self._totalVotes.get() + prep_vote)
                total_percentage += votes

            self._require(total_percentage == EXA,
                          "Delegation SCORE :Update error- sum of percentages not equal to 100 ")
            self._userVotes[user] = user_staked_token

            # get updated prep percentages and updating the preference
            updated_delegation = self.computeDelegationPercentages()
            core = self.create_interface_score(self._lendingPoolCore.get(), LendingPoolCoreInterface)
            core.updatePrepDelegations(updated_delegation)
            self.DelegationUpdated(delegationBefore, f'{updated_delegation}')

    @external(readonly=True)
    def prepVotes(self, _prep: Address) -> int:
        return self._prepVotes[_prep]

    @external(readonly=True)
    def getUserDelegationDetails(self, _user: Address) -> List[PrepDelegations]:
        user_details = []

        for index in range(5):
            prep: Address = self._userPreps[_user][index]
            if prep != ZERO_SCORE_ADDRESS and prep is not None:
                user_details.append({
                    '_address': prep,
                    '_votes_in_per': self._percentageDelegations[_user][index]
                })

        return user_details

    @external(readonly=True)
    def computeDelegationPercentages(self) -> List[PrepDelegations]:
        prep_delegations = []
        prep_list = self.getPrepList()
        total_percentage = 0
        dust_votes = 0
        max_votes_prep_index = 0
        max_votes = 0
        below_threshold_prep_indexes = []
        for index, prep in enumerate(prep_list):
            votes: int = 0
            votes_percentage: PrepDelegations = {'_address': prep, '_votes_in_per': 0}
            if index == len(prep_list) - 1:
                votes = 100 * EXA - total_percentage
                votes_percentage['_votes_in_per'] = votes
                if votes > max_votes:
                    max_votes = votes
                    max_votes_prep_index = index
            else:
                votes = exaDiv(self._prepVotes[prep], self._totalVotes.get()) * 100
                votes_percentage['_votes_in_per'] = votes
                total_percentage += votes_percentage['_votes_in_per']
                if votes > max_votes:
                    max_votes = votes
                    max_votes_prep_index = index

            if votes < 1 * 10 ** 15:
                dust_votes += votes
                below_threshold_prep_indexes.append(index)
            prep_delegations.append(votes_percentage)
        prep_delegations[max_votes_prep_index]['_votes_in_per'] += dust_votes
        for items in below_threshold_prep_indexes:
            prep_delegations.pop(items)
        return prep_delegations
