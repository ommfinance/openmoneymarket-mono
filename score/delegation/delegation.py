from .utils.enumerable_set import EnumerableSetDB
from .utils.math import *
from .addresses import *


class Delegation(Addresses):
    _PREPS = 'preps'
    _USER_PREPS = 'userPreps'
    _PERCENTAGE_DELEGATIONS = 'percentageDelegations'
    _PREP_VOTES = 'prepVotes'
    _USER_VOTES = 'userVotes'
    _TOTAL_VOTES = 'totalVotes'
    _EQUAL_DISTRIBUTION = 'equalDistribution'
    _CONTRIBUTORS = 'contributors'
    _VOTE_THRESHOLD = 'voteThreshold'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._preps = EnumerableSetDB(self._PREPS, db, value_type=Address)
        self._userPreps = DictDB(self._USER_PREPS, db, value_type=Address, depth=2)
        self._percentageDelegations = DictDB(self._PERCENTAGE_DELEGATIONS, db, value_type=int, depth=2)
        self._prepVotes = DictDB(self._PREP_VOTES, db, value_type=int)
        self._userVotes = DictDB(self._USER_VOTES, db, value_type=int)
        self._totalVotes = VarDB(self._TOTAL_VOTES, db, value_type=int)
        self._contributors = ArrayDB(self._CONTRIBUTORS, db, value_type=Address)
        self._voteThreshold = VarDB(self._VOTE_THRESHOLD, db, value_type=int)

    def on_install(self, _addressProvider: Address) -> None:
        super().on_install(_addressProvider)
        self._voteThreshold.set(1 * 10 ** 15)

    def on_update(self) -> None:
        super().on_update()

    @staticmethod
    def _require(_condition: bool, _message: str):
        if not _condition:
            revert(_message)

    @external(readonly=True)
    def name(self) -> str:
        return f"Omm {TAG}"

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
        if self.msg.sender == self._addresses[OMM_TOKEN] or self.msg.sender == _user:
            prepVotes = 0
            for index in range(5):

                # removing votes
                prep_vote = exaMul(self._percentageDelegations[_user][index], self._userVotes[_user])
                if prep_vote > 0:
                    self._prepVotes[self._userPreps[_user][index]] -= prep_vote

                # resetting the preferences
                self._userPreps[_user][index] = ZERO_SCORE_ADDRESS
                self._percentageDelegations[_user][index] = 0

                # calculating total user votes
                prepVotes += prep_vote

            self._totalVotes.set(self._totalVotes.get() - prepVotes)
            self._userVotes[_user] = 0

    def _validatePrep(self, _address):
        governance = self.create_interface_score(ZERO_SCORE_ADDRESS, GovernanceContractInterface)
        try:
            prep = governance.getPRep(_address)
            isActive = prep["status"] == 0
        except:
            isActive = False

        if not isActive:
            revert(f"{TAG}: Invalid prep: {_address}")

    @external(readonly=True)
    def getPrepList(self) -> List[Address]:
        return [prep for prep in self._preps.range(0, len(self._preps))]

    @external
    def updateDelegations(self, _delegations: List[PrepDelegations] = None, _user: Address = None):
        if _user is not None and self.msg.sender == self._addresses[OMM_TOKEN]:
            user = _user
        else:
            user = self.msg.sender

        if _delegations is None:
            delegations = self.getUserDelegationDetails(user)
        else:
            self._require(len(_delegations) <= 5, f'{TAG}: '
                                                  f'updating delegation unsuccessful,more than 5 preps provided by user'
                                                  f'delegations provided {_delegations}')
            delegations = _delegations

        # if user have not provided delegations or provided delegations is empty, delegate votes to contributors
        if not delegations:
            delegations = self._distributeVoteToContributors()

        self._handleCalculation(delegations, user)

    def _handleCalculation(self, delegations, user):
        total_percentage = 0
        omm_token = self.create_interface_score(self._addresses[OMM_TOKEN], OmmTokenInterface)
        user_staked_token = omm_token.details_balanceOf(user)['stakedBalance']
        prepVotes = 0
        # resetting previous delegation preferences
        self._resetUser(user)
        for index, delegation in enumerate(delegations):
            address: Address = delegation['_address']
            votes: int = delegation['_votes_in_per']

            # updating prep list
            if address not in self._preps:
                self._validatePrep(address)
                self._preps.add(address)

            # adding delegation to new preps
            prep_vote = exaMul(votes, user_staked_token)
            self._prepVotes[address] += prep_vote

            # updating the delegation preferences
            self._userPreps[user][index] = address
            self._percentageDelegations[user][index] = votes

            # adjusting total votes
            prepVotes += prep_vote
            total_percentage += votes
        self._require(total_percentage == EXA,
                      f'{TAG}: '
                      f'updating delegation unsuccessful,sum of percentages not equal to 100'
                      f'sum total of percentages {total_percentage}'
                      f'delegation preferences {delegations}'
                      )

        self._userVotes[user] = user_staked_token
        self._totalVotes.set(self._totalVotes.get() + prepVotes)

        # get updated prep percentages
        updated_delegation = self.computeDelegationPercentages()

        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], LendingPoolCoreInterface)
        core.updatePrepDelegations(updated_delegation)

    def _distributeVoteToContributors(self) -> List[PrepDelegations]:
        user_details = []
        totalContributors = len(self._contributors)
        prep_percentage = EXA // totalContributors
        total_percentage = 0
        for index, preps in enumerate(self._contributors):
            user_details.append(
                {
                    '_address': preps,
                    '_votes_in_per': prep_percentage
                }
            )
            total_percentage += prep_percentage

        dust_votes = EXA - total_percentage
        if dust_votes >= 0 and len(user_details) > 0:
            user_details[0]['_votes_in_per'] += dust_votes

        return user_details

    @external(readonly=True)
    def prepVotes(self, _prep: Address) -> int:
        return self._prepVotes[_prep]

    @external(readonly=True)
    def userPrepVotes(self, _user: Address) -> dict:
        response = {}
        omm_token = self.create_interface_score(self._addresses[OMM_TOKEN], OmmTokenInterface)
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
    def getUserICXDelegation(self, _user: Address) -> List[PrepICXDelegations]:
        user_details = []
        omm_token = self.create_interface_score(self._addresses[OMM_TOKEN], OmmTokenInterface)
        sicx = self.create_interface_score(self._addresses[SICX], TokenInterface)
        staking = self.create_interface_score(self._addresses[STAKING], StakingInterface)
        user_staked_token = omm_token.details_balanceOf(_user)['stakedBalance']
        total_staked_token = omm_token.getTotalStaked()['totalStaked']
        core_sicx_balance = sicx.balanceOf(self._addresses[LENDING_POOL_CORE])
        sicx_icx_rate = staking.getTodayRate()
        omm_icx_power = exaMul(sicx_icx_rate, exaDiv(core_sicx_balance, total_staked_token))
        
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
        total_votes = self._totalVotes.get()
        if total_votes == 0:
            default_preference = self._distributeVoteToContributors()
            for index in range(len(default_preference)):
                default_preference[index]['_votes_in_per'] = default_preference[index]['_votes_in_per'] * 100
            return default_preference

        prep_list = self.getPrepList()
        prep_delegations = []
        if prep_list:
            total_percentage = 0
            max_votes_prep_index = 0
            max_votes = 0
            _voting_threshold = self._voteThreshold.get()
            for prep in prep_list:
                votes: int = exaDivFloor(self._prepVotes[prep], total_votes) * 100
                if votes > _voting_threshold:
                    votes_percentage: PrepDelegations = {'_address': prep, '_votes_in_per': votes}
                    total_percentage += votes

                    prep_delegations.append(votes_percentage)
                    if votes > max_votes:
                        max_votes = votes
                        max_votes_prep_index = len(prep_delegations) - 1

            dust_votes = 100 * EXA - total_percentage
            if dust_votes >= 0:
                prep_delegations[max_votes_prep_index]['_votes_in_per'] += dust_votes
        return prep_delegations
