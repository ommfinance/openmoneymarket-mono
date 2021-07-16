from .Math import *
from .utils.checks import *

class AddressDetails(TypedDict):
    name: str
    address: Address

class PrepDelegations(TypedDict):
    _address: Address
    _votes_in_per: int


class SystemInterface(InterfaceScore):
    @interface
    def getPRep(self, address: Address) -> dict:
        pass


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
    _EQUAL_DISTRIBUTION = 'equalDistribution'
    _CONTRIBUTORS = 'contributors'
    _VOTE_THRESHOLD = 'voteThreshold'
    _ADDRESSES = 'addresses'
    _CONTRACTS = 'contracts'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._preps = ArrayDB(self._PREPS, db, Address)
        self._addresses = DictDB(self._ADDRESSES, db, value_type=Address)
        self._contracts = ArrayDB(self._CONTRACTS, db, value_type=str)
        self._userPreps = DictDB(self._USER_PREPS, db, value_type=Address, depth=2)
        self._percentageDelegations = DictDB(self._PERCENTAGE_DELEGATIONS, db, value_type=int, depth=2)
        self._prepVotes = DictDB(self._PREP_VOTES, db, value_type=int)
        self._userVotes = DictDB(self._USER_VOTES, db, value_type=int)
        self._totalVotes = VarDB(self._TOTAL_VOTES, db, value_type=int)
        self._contributors = ArrayDB(self._CONTRIBUTORS, db, value_type=Address)
        self._voteThreshold = VarDB(self._VOTE_THRESHOLD, db, value_type=int)

    def on_install(self) -> None:
        super().on_install()
        self._voteThreshold.set(1 * 10 ** 15)

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

    @origin_owner
    @external
    def setAddresses(self, _addressDetails: List[AddressDetails]) -> None:
        for contracts in _addressDetails:
            if contracts['name'] not in self._contracts:
                self._contracts.put(contracts['name'])
            self._addresses[contracts['name']] = contracts['address']

    @external(readonly=True)
    def getAddresses(self) -> dict:
        return {item: self._addresses[item] for item in self._contracts}

    @only_owner
    @external
    def setVoteThreshold(self, _vote: int):
        self._voteThreshold.set(_vote)

    @external(readonly=True)
    def getVoteThreshold(self) -> int:
        return self._voteThreshold.get()


    @only_owner
    @external
    def addContributor(self, _prep: Address) -> None:
        if _prep not in self._contributors:
            self._contributors.put(_prep)

    @only_owner
    @external
    def removeContributor(self, _prep: Address) -> None:
        if _prep not in self._contributors:
            revert(f"{TAG}: {_prep} is not in contributor list")
        else:
            topPrep = self._contributors.pop()
            if topPrep != _prep:
                for i in range(len(self._contributors)):
                    if self._contributors[i] == _prep:
                        self._contributors[i] = topPrep

    @external(readonly=True)
    def getContributors(self) -> List[Address]:
        return [prep for prep in self._contributors]

    @only_owner
    @external
    def addAllContributors(self, _preps: List[Address]) -> None:
        for preps in _preps:
            self.addContributor(preps)

    @external
    def clearPrevious(self, _user: Address):
        if self.msg.sender != _user:
            revert(f'{TAG}: You are not authorized to clear others delegation preference')

        # if user wants to clear his delegation preference,votes are delegated to contributor preps
        defaultDelegation = self._distributeVoteToContributors()
        self.updateDelegations(defaultDelegation)

    @external(readonly=True)
    def userDefaultDelegation(self, _user: Address) -> bool:
        return self._distributeVoteToContributors() == self.getUserDelegationDetails(_user)

    def _resetUser(self, _user: Address):
        if self.msg.sender == self._addresses["ommToken"] or self.msg.sender == _user:
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
    def getPrepList(self) -> List[Address]:
        return [prep for prep in self._preps]

    @external
    def updateDelegations(self, _delegations: List[PrepDelegations] = None, _user: Address = None):
        if _user is not None and self.msg.sender == self._addresses["ommToken"]:
            user = _user
        else:
            user = self.msg.sender

        total_percentage = 0
        initialDelegation = self.computeDelegationPercentages()

        if _delegations is None:
            delegations = self.getUserDelegationDetails(user)
            if not delegations:
                delegations = self._distributeVoteToContributors()
        else:
            self._require(len(_delegations) <= 5, f'{TAG}: '
                                                  f'updating delegation unsuccessful,more than 5 preps provided by user'
                                                  f'delegations provided {_delegations}')
            delegations = _delegations

        omm_token = self.create_interface_score(self._addresses["ommToken"], OmmTokenInterface)
        user_staked_token = omm_token.details_balanceOf(user)['stakedBalance']
        if len(delegations) > 0:
            # resetting previous delegation preferences
            self._resetUser(user)

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
                          f'{TAG}: '
                          f'updating delegation unsuccessful,sum of percentages not equal to 100'
                          f'sum total of percentages {total_percentage}'
                          f'delegation preferences {delegations}'
                          )
            self._userVotes[user] = user_staked_token

            # get updated prep percentages 
            updated_delegation = self.computeDelegationPercentages()

            # updating the delegation if there is change in previous delegation
            if updated_delegation != initialDelegation:
                core = self.create_interface_score(self._addresses["lendingPoolCore"], LendingPoolCoreInterface)
                core.updatePrepDelegations(updated_delegation)
                self.DelegationUpdated(f'{initialDelegation}', f'{updated_delegation}')

    def _distributeVoteToContributors(self) -> List[PrepDelegations]:
        user_details = []
        totalContributors = len(self._contributors)
        prepPercentage = EXA // totalContributors
        for index, preps in enumerate(self._contributors):
            if index == totalContributors - 1:
                percent = EXA - prepPercentage * (totalContributors - 1)
            else:

                percent = prepPercentage
            user_details.append(
                {
                    '_address': preps,
                    '_votes_in_per': percent
                }
            )
        return user_details

    @external(readonly=True)
    def prepVotes(self, _prep: Address) -> int:
        return self._prepVotes[_prep]

    @external(readonly=True)
    def userPrepVotes(self, _user: Address) -> dict:
        response = {}
        omm_token = self.create_interface_score(self._addresses["ommToken"], OmmTokenInterface)
        user_staked_token = omm_token.details_balanceOf(_user)['stakedBalance']
        for index in range(5):
            prep: Address = self._userPreps[_user][index]
            if prep != ZERO_SCORE_ADDRESS and prep is not None:
                response[str(prep)] = exaMul(self._percentageDelegations[_user][index], user_staked_token)
        return response

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
        if prep_list:
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

                if votes < self._voteThreshold.get():
                    dust_votes += votes
                    below_threshold_prep_indexes.append(index)

                prep_delegations.append(votes_percentage)
            if dust_votes >= 0:
                prep_delegations[max_votes_prep_index]['_votes_in_per'] += dust_votes
                for items in sorted(below_threshold_prep_indexes, reverse=True):
                    del prep_delegations[items]
        return prep_delegations
